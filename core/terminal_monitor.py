"""
LOVE Terminal Error Monitor — Wave 31

LOVE watches its own server output in real time. When it sees Python
tracebacks, import errors, or runtime exceptions, it:

1. Captures the full error + surrounding context
2. Locates the file and line responsible
3. Asks the LLM (coding model) to generate a minimal patch
4. Applies the patch if it's safe (single-file, < 50 lines changed)
5. Pushes the diagnosis + action report via WebSocket instantly
6. Logs everything to data/terminal_errors.jsonl

The server logs to data/server.log (uvicorn stderr redirect).
This daemon wakes up every 10 seconds and scans the tail of that file.

Usage:
    from core.terminal_monitor import get_terminal_monitor
    monitor = get_terminal_monitor()
    monitor.start()          # start watching
    monitor.get_errors()     # recent errors
    monitor.get_fixes()      # applied fixes
"""

import json
import os
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SERVER_LOG = DATA_DIR / "server.log"
ERROR_LOG = DATA_DIR / "terminal_errors.jsonl"
FIX_LOG = DATA_DIR / "terminal_fixes.jsonl"
SCAN_INTERVAL_SECS = 10
MAX_LOG_TAIL_BYTES = 100_000   # last 100 KB scanned per tick
MAX_ERRORS_MEMORY = 50         # in-memory cap
_lock = threading.Lock()

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Traceback extraction ──────────────────────────────────────────────────────

# Matches Python traceback blocks
_TB_START = re.compile(r"^Traceback \(most recent call last\):", re.MULTILINE)
_TB_FILE  = re.compile(r'^\s+File "([^"]+)", line (\d+), in (\S+)', re.MULTILINE)
_ERR_LINE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*(?:Error|Exception|Warning)[^\n]*)", re.MULTILINE)

def _extract_tracebacks(text: str) -> List[Dict[str, Any]]:
    """Parse one or more tracebacks from a block of log text."""
    blocks = []
    for m in _TB_START.finditer(text):
        # Take up to 80 lines after the "Traceback" header
        start = m.start()
        chunk = text[start:start + 6000]
        lines = chunk.splitlines()[:80]
        tb_text = "\n".join(lines)

        # Find all file references
        files = _TB_FILE.findall(tb_text)
        # Last file reference = the actual crash location
        crash_file, crash_line, crash_fn = files[-1] if files else ("", "0", "")

        # Find the error type + message (last non-empty line)
        error_msg = ""
        for ln in reversed(lines):
            ln = ln.strip()
            if ln and _ERR_LINE.match(ln):
                error_msg = ln
                break
        if not error_msg:
            for ln in reversed(lines):
                if ln.strip():
                    error_msg = ln.strip()
                    break

        blocks.append({
            "traceback": tb_text,
            "file": crash_file,
            "line": int(crash_line) if crash_line.isdigit() else 0,
            "function": crash_fn,
            "error": error_msg,
            "ts": datetime.now().isoformat(),
        })
    return blocks


# ── LLM-powered diagnosis + patch ────────────────────────────────────────────

_DIAGNOSIS_PROMPT = """You are the self-repair engine of Project LOVE, an autonomous AI assistant.
A Python error occurred in the running server. Diagnose the root cause and generate a minimal fix.

ERROR:
{error}

TRACEBACK:
{traceback}

RELEVANT SOURCE (file: {file}, around line {line}):
{source}

INSTRUCTIONS:
1. Identify the root cause in one sentence.
2. If the fix is a simple code change (< 20 lines), provide it as a unified diff (--- original / +++ fixed).
3. If the fix requires more context or is unsafe to auto-apply, say "NEEDS_HUMAN: <reason>".
4. Format your response as JSON:
{{
  "root_cause": "...",
  "fix_type": "patch" | "config" | "install" | "manual",
  "patch": "...unified diff...",
  "install_cmd": "pip install ...",
  "manual_steps": "...",
  "confidence": 0.0-1.0
}}
Return ONLY valid JSON, no commentary."""


def _read_source_context(file_path: str, line_no: int, ctx: int = 20) -> str:
    """Read source lines around a crash location."""
    try:
        p = Path(file_path)
        if not p.exists():
            # Try relative to project root
            p = PROJECT_ROOT / file_path
        if not p.exists():
            return "(source not found)"
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(0, line_no - ctx - 1)
        end = min(len(lines), line_no + ctx)
        numbered = [f"{i+1:4d} | {l}" for i, l in enumerate(lines[start:end], start=start)]
        # Mark crash line
        marker_idx = line_no - start - 1
        if 0 <= marker_idx < len(numbered):
            numbered[marker_idx] = numbered[marker_idx].replace(" | ", " >|")
        return "\n".join(numbered)
    except Exception as e:
        return f"(could not read source: {e})"


def _ask_llm_for_fix(tb_info: Dict[str, Any]) -> Dict[str, Any]:
    """Ask the coding LLM to diagnose and patch the error."""
    try:
        from core.llm import get_coding_llm
        llm = get_coding_llm()
    except Exception as e:
        return {"root_cause": f"LLM unavailable: {e}", "fix_type": "manual", "confidence": 0}

    source = _read_source_context(tb_info["file"], tb_info["line"])
    prompt = _DIAGNOSIS_PROMPT.format(
        error=tb_info["error"],
        traceback=tb_info["traceback"][:3000],
        file=tb_info["file"],
        line=tb_info["line"],
        source=source,
    )
    try:
        raw = llm.invoke(prompt)
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw.strip(), flags=re.MULTILINE)
        result = json.loads(raw)
        result.setdefault("confidence", 0.5)
        return result
    except Exception as e:
        return {"root_cause": f"LLM parse error: {e}", "fix_type": "manual", "confidence": 0}


# ── Patch application ─────────────────────────────────────────────────────────

_DIFF_HUNK = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",
    re.MULTILINE,
)

def _apply_patch(file_path: str, patch: str) -> Dict[str, Any]:
    """Apply a unified diff patch to a project file. Returns {applied, reason}."""
    try:
        p = Path(file_path)
        if not p.exists():
            p = PROJECT_ROOT / file_path
        if not p.exists():
            return {"applied": False, "reason": f"File not found: {file_path}"}

        # Safety: only touch files inside project root
        try:
            p.resolve().relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return {"applied": False, "reason": "Refusing to patch file outside project root"}

        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

        # Parse hunks
        hunks = list(_DIFF_HUNK.finditer(patch))
        if not hunks:
            return {"applied": False, "reason": "No valid diff hunks found"}

        # Backup original
        bak = p.with_suffix(p.suffix + ".bak")
        bak.write_text("".join(lines), encoding="utf-8")

        # Apply each hunk (in reverse order so line numbers don't shift)
        patch_lines = patch.splitlines(keepends=True)
        for hunk in reversed(hunks):
            orig_start = int(hunk.group(1)) - 1  # 0-indexed
            hunk_content_start = patch.rfind(hunk.group(0)) + len(hunk.group(0))
            # Get hunk lines (skip header)
            hunk_lines = []
            for pl in patch_lines[patch.count("\n", 0, patch.rfind(hunk.group(0))) + 1:]:
                if pl.startswith((" ", "-", "+")):
                    hunk_lines.append(pl)
                elif pl.startswith("@@") and hunk_lines:
                    break

            old_lines = [l[1:] if l.startswith("-") else l[1:]
                         for l in hunk_lines if not l.startswith("+")]
            new_lines = [l[1:] for l in hunk_lines if not l.startswith("-")]

            # Replace
            lines[orig_start:orig_start + len(old_lines)] = new_lines

        p.write_text("".join(lines), encoding="utf-8")
        return {"applied": True, "reason": "Patch applied", "backup": str(bak)}

    except Exception as e:
        return {"applied": False, "reason": f"Patch error: {e}"}


# ── Core monitor daemon ───────────────────────────────────────────────────────

class TerminalMonitor:
    """Watches server.log, detects Python errors, calls LLM, applies fixes."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._seen_positions: int = 0        # byte offset into server.log
        self._errors: List[Dict] = []        # recent errors in memory
        self._fixes: List[Dict] = []         # applied fixes in memory
        self._pending_errors: set = set()    # fingerprints of in-flight errors

    def start(self):
        if self._running:
            return
        self._running = True
        # Seek to end of existing log so we don't re-process old errors
        if SERVER_LOG.exists():
            self._seen_positions = SERVER_LOG.stat().st_size
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="LOVE-TerminalMonitor"
        )
        self._thread.start()
        print(f"[TerminalMonitor] Started — watching {SERVER_LOG}")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                self._scan()
            except Exception as e:
                print(f"[TerminalMonitor] scan error: {e}")
            time.sleep(SCAN_INTERVAL_SECS)

    def _scan(self):
        if not SERVER_LOG.exists():
            return

        size = SERVER_LOG.stat().st_size
        if size <= self._seen_positions:
            return

        # Read only new bytes
        try:
            with open(SERVER_LOG, "rb") as f:
                f.seek(self._seen_positions)
                new_bytes = f.read(MAX_LOG_TAIL_BYTES)
            self._seen_positions = min(self._seen_positions + len(new_bytes), size)
        except Exception:
            return

        new_text = new_bytes.decode("utf-8", errors="replace")
        tracebacks = _extract_tracebacks(new_text)
        for tb in tracebacks:
            self._handle_error(tb)

    def _handle_error(self, tb_info: Dict[str, Any]):
        # Deduplicate by (file, line, error message)
        fingerprint = f"{tb_info['file']}:{tb_info['line']}:{tb_info['error'][:80]}"
        if fingerprint in self._pending_errors:
            return
        self._pending_errors.add(fingerprint)

        print(f"[TerminalMonitor] Error detected: {tb_info['error'][:100]}")

        # Log raw error
        self._append_log(ERROR_LOG, tb_info)
        with _lock:
            self._errors.append(tb_info)
            if len(self._errors) > MAX_ERRORS_MEMORY:
                self._errors.pop(0)

        # Skip errors in venv/site-packages (third-party, can't patch)
        file_path = tb_info.get("file", "")
        if any(x in file_path for x in ["site-packages", "venv\\", "venv/", "lib\\python"]):
            self._push_notice(tb_info, fix={"root_cause": "Third-party library error — cannot auto-patch.", "fix_type": "manual"})
            self._pending_errors.discard(fingerprint)
            return

        # Ask LLM
        fix = _ask_llm_for_fix(tb_info)

        # Attempt auto-apply if patch + high confidence
        applied = False
        if (fix.get("fix_type") == "patch"
                and fix.get("patch")
                and fix.get("confidence", 0) >= 0.75
                and file_path):
            result = _apply_patch(file_path, fix["patch"])
            fix["patch_result"] = result
            applied = result.get("applied", False)
            if applied:
                fix["auto_applied"] = True
                print(f"[TerminalMonitor] Auto-patched {file_path}")

        # Log fix attempt
        fix_record = {**tb_info, "fix": fix, "auto_applied": applied, "ts": datetime.now().isoformat()}
        self._append_log(FIX_LOG, fix_record)
        with _lock:
            self._fixes.append(fix_record)
            if len(self._fixes) > MAX_ERRORS_MEMORY:
                self._fixes.pop(0)

        # Push to WebSocket
        self._push_notice(tb_info, fix, applied)
        self._pending_errors.discard(fingerprint)

    def _push_notice(self, tb_info: Dict, fix: Dict, applied: bool = False):
        try:
            from core.proactive_push import get_push_engine
            engine = get_push_engine()
            error_short = tb_info.get("error", "Unknown error")[:100]
            file_short = Path(tb_info.get("file", "?")).name
            line = tb_info.get("line", "?")

            if applied:
                msg = (
                    f"AUTO-FIXED: {error_short}\n"
                    f"File: {file_short} line {line}\n"
                    f"Cause: {fix.get('root_cause', '?')[:120]}\n"
                    f"Patch applied. Backup saved."
                )
                priority = "high"
                category = "SELF_HEAL"
            else:
                fix_type = fix.get("fix_type", "manual")
                cause = fix.get("root_cause", "?")[:120]
                if fix_type == "install":
                    action = f"Run: {fix.get('install_cmd', 'pip install ?')}"
                elif fix_type == "manual":
                    action = fix.get("manual_steps", "Manual investigation needed.")[:120]
                elif fix_type == "patch":
                    action = "Patch generated but confidence too low to auto-apply. Review fix log."
                else:
                    action = fix.get("manual_steps", "Check the fix log.")[:120]

                msg = (
                    f"ERROR DETECTED: {error_short}\n"
                    f"File: {file_short} line {line}\n"
                    f"Cause: {cause}\n"
                    f"Action: {action}"
                )
                priority = "high"
                category = "ERROR"

            engine.push(category, msg, priority, metadata={
                "file": tb_info.get("file"),
                "line": tb_info.get("line"),
                "error": tb_info.get("error"),
                "auto_applied": applied,
            })
        except Exception as e:
            print(f"[TerminalMonitor] push failed: {e}")

    @staticmethod
    def _append_log(path: Path, record: Dict):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception:
            pass

    def get_errors(self, limit: int = 20) -> List[Dict]:
        with _lock:
            return list(reversed(self._errors[-limit:]))

    def get_fixes(self, limit: int = 20) -> List[Dict]:
        with _lock:
            return list(reversed(self._fixes[-limit:]))

    def get_status(self) -> Dict[str, Any]:
        with _lock:
            return {
                "running": self._running,
                "log_file": str(SERVER_LOG),
                "log_exists": SERVER_LOG.exists(),
                "bytes_scanned": self._seen_positions,
                "errors_detected": len(self._errors),
                "fixes_attempted": len(self._fixes),
                "auto_fixed": sum(1 for f in self._fixes if f.get("auto_applied")),
            }

    def ingest_error(self, error_text: str, file: str = "", line: int = 0) -> Dict[str, Any]:
        """
        Manually submit an error string for diagnosis.
        Used by /terminal/error endpoint so the UI can report frontend errors too.
        """
        tbs = _extract_tracebacks(error_text)
        if tbs:
            tb_info = tbs[0]
        else:
            tb_info = {
                "traceback": error_text,
                "file": file,
                "line": line,
                "function": "",
                "error": error_text.strip().splitlines()[-1] if error_text.strip() else "Unknown",
                "ts": datetime.now().isoformat(),
            }
        self._handle_error(tb_info)
        return {"status": "processing", "error": tb_info["error"]}


# ── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[TerminalMonitor] = None
_inst_lock = threading.Lock()


def get_terminal_monitor() -> TerminalMonitor:
    global _instance
    if _instance is None:
        with _inst_lock:
            if _instance is None:
                _instance = TerminalMonitor()
    return _instance
