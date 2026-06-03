"""
LOVE File Inspector

Proactively scans Karthi's project directories, detects interesting files,
and generates personalized questions about them.

This is how LOVE learns "inspect folder and asked me file to refer for info."
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INSPECTION_LOG = DATA_DIR / "file_inspections.jsonl"
INTERESTING_FILE = DATA_DIR / "interesting_files.json"

# File types LOVE should notice
INTERESTING_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt", ".json", ".yaml", ".yml",
    ".sql", ".sh", ".bat", ".ps1", ".html", ".css", ".scss", ".less",
    ".ipynb", ".csv", ".log", ".env", ".cfg", ".ini", ".toml",
}

# Files that are always worth asking about
SIGNAL_FILES = {
    "README", "TODO", "CHANGELOG", "CONTRIBUTING", "LICENSE",
    "requirements", "package", "Dockerfile", "docker-compose",
    "Makefile", "setup", "config", ".env", ".gitignore",
}

# Recent files threshold
RECENT_HOURS = 24


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(INSPECTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.file_inspector")


def _load_interesting() -> Dict[str, Any]:
    if INTERESTING_FILE.exists():
        try:
            return json.loads(INTERESTING_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.file_inspector")
    return {"files": {}, "last_asked": {}, "patterns": {}}


def _save_interesting(data: Dict[str, Any]):
    try:
        INTERESTING_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.file_inspector")


def get_watch_paths() -> List[Path]:
    """Load configured dev folders from settings or fallback."""
    try:
        from core.settings import get_settings
        settings = get_settings()
        folders = getattr(settings.work, 'dev_folders', [])
        if folders:
            return [Path(f) for f in folders if Path(f).exists()]
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.file_inspector")

    # Fallback: common dev locations
    home = Path.home()
    candidates = [
        home / "Projects", home / "projects", home / "Dev", home / "dev",
        home / "Documents" / "Projects", home / "workspace",
        PROJECT_ROOT.parent,  # sibling of LOVE
    ]
    return [c for c in candidates if c.exists()]


def scan_directory(path: Path, max_depth: int = 2, max_files: int = 50) -> List[Dict[str, Any]]:
    """
    Scan a directory for interesting files.
    Returns list of file metadata dicts.
    """
    results = []
    try:
        for root, dirs, files in os.walk(str(path)):
            depth = len(Path(root).relative_to(path).parts)
            if depth > max_depth:
                del dirs[:]
                continue

            # Skip common junk
            dirs[:] = [d for d in dirs if d not in {
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "dist", "build", ".next", ".expo", ".idea", ".vscode",
                "target", "bin", "obj", "vendor", "coverage"
            }]

            for filename in files:
                if len(results) >= max_files:
                    break

                file_path = Path(root) / filename
                stem = file_path.stem
                ext = file_path.suffix.lower()

                # Skip very small or very large files
                try:
                    size = file_path.stat().st_size
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                except Exception:
                    continue

                if size < 10 or size > 5_000_000:  # < 10 bytes or > 5MB
                    continue

                is_signal = any(s.lower() in stem.lower() for s in SIGNAL_FILES)
                is_interesting_ext = ext in INTERESTING_EXTENSIONS
                is_recent = (datetime.now() - mtime) < timedelta(hours=RECENT_HOURS)

                if not (is_signal or is_interesting_ext or is_recent):
                    continue

                # Quick content peek for TODOs, FIXMEs, or interesting lines
                content_hint = ""
                if size < 50_000 and ext in {".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".txt"}:
                    try:
                        text = file_path.read_text(encoding="utf-8", errors="ignore")[:2000]
                        todos = re.findall(r'(TODO|FIXME|HACK|BUG|NOTE|IDEA|XXX)[\s:]*(.{0,80})', text, re.IGNORECASE)
                        if todos:
                            content_hint = ", ".join(f"{t[0]}: {t[1].strip()}" for t in todos[:3])
                    except Exception as e:
                        from core.execution_guard import log_error
                        log_error(e, module="core.file_inspector")

                score = 0
                if is_signal: score += 3
                if is_recent: score += 2
                if is_interesting_ext: score += 1
                if content_hint: score += 2
                if size > 100_000: score += 1  # Substantial file

                results.append({
                    "path": str(file_path),
                    "name": filename,
                    "stem": stem,
                    "ext": ext,
                    "size": size,
                    "mtime": mtime.isoformat(),
                    "is_recent": is_recent,
                    "is_signal": is_signal,
                    "content_hint": content_hint,
                    "score": score,
                })

    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.file_inspector")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.file_inspector")

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def rank_files_for_user(files: List[Dict[str, Any]], known_patterns: Dict) -> List[Dict[str, Any]]:
    """Use LLM to identify which files would be most interesting to ask about."""
    if not files:
        return []

    # Filter to top candidates
    candidates = files[:10]

    # Build prompt for LLM
    lines = []
    for f in candidates:
        hint = f" | hint: {f['content_hint']}" if f['content_hint'] else ""
        recent = " | RECENTLY MODIFIED" if f['is_recent'] else ""
        lines.append(f"- {f['name']} ({f['ext']}, {f['size']} bytes){hint}{recent}")

    prompt = f"""You are LOVE, scanning a user's project directories. You found these files:

{chr(10).join(lines)}

Which 2-3 files would be MOST interesting to ask the user about? Consider:
- Recently modified files suggest active work
- Files with TODO/FIXME suggest something in progress
- README/config files suggest new projects
- Large files suggest important codebases

Return ONLY the file names, one per line. No explanation."""

    try:
        from core.llm import get_reasoning_llm
        llm = get_reasoning_llm(temperature=0.3, max_tokens=100)
        response = llm.invoke(prompt).strip()
        selected = [line.strip("-\n ") for line in response.split("\n") if line.strip()]

        # Reorder candidates based on LLM selection
        ranked = []
        for s in selected:
            for c in candidates:
                if s in c["name"] or c["name"] in s:
                    ranked.append(c)
                    break
        # Append remaining
        for c in candidates:
            if c not in ranked:
                ranked.append(c)
        return ranked

    except Exception:
        return candidates


def generate_question_about_file(file_info: Dict[str, Any], user_name: str = "Karthi") -> str:
    """Generate a natural, curious question about a file."""
    name = file_info["name"]
    hint = file_info.get("content_hint", "")
    is_recent = file_info.get("is_recent", False)

    if "TODO" in hint or "FIXME" in hint:
        task = re.search(r'(TODO|FIXME)[\s:]*(.{0,60})', hint, re.IGNORECASE)
        task_text = task.group(2).strip() if task else "something"
        return f"I noticed you have a TODO in `{name}` — '{task_text}'. Want me to track that for you?"

    if name.lower().startswith("readme"):
        return f"I see a README in `{name}`. Is this a new project you're working on? Should I remember the details?"

    if is_recent:
        return f"I noticed `{name}` was modified recently. What are you working on there? Anything I should keep tabs on?"

    if file_info.get("is_signal"):
        return f"I spotted `{name}` in your project folder. Is this something I should know about for context?"

    return f"I came across `{name}` while looking through your files. What's this one about? Should I remember it?"


def inspect_and_ask() -> Optional[Dict[str, Any]]:
    """
    Main entry: scan directories, find interesting files, decide if worth asking.
    Returns question dict or None if nothing interesting found.
    """
    state = _load_interesting()
    watch_paths = get_watch_paths()

    if not watch_paths:
        return None

    all_files = []
    for path in watch_paths:
        files = scan_directory(path, max_depth=2, max_files=30)
        all_files.extend(files)

    if not all_files:
        return None

    # Filter out files we've already asked about recently (< 7 days)
    last_asked = state.get("last_asked", {})
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    new_files = [f for f in all_files if last_asked.get(f["path"], "") < cutoff]

    if not new_files:
        return None

    # Rank by interest
    ranked = rank_files_for_user(new_files, state.get("patterns", {}))
    if not ranked:
        return None

    top = ranked[0]

    # Check if score is high enough to be worth asking
    if top["score"] < 2:
        return None

    # Generate question
    try:
        from core.settings import get_settings
        settings = get_settings()
        user_name = settings.user.name
    except Exception:
        user_name = "Karthi"

    question = generate_question_about_file(top, user_name)

    # Record that we asked
    last_asked[top["path"]] = datetime.now().isoformat()
    state["last_asked"] = last_asked
    state["files"][top["path"]] = top
    _save_interesting(state)

    _log({
        "event": "file_inspection",
        "file": top["path"],
        "question": question,
        "score": top["score"],
    })

    return {
        "file": top["name"],
        "path": top["path"],
        "question": question,
        "score": top["score"],
        "content_hint": top.get("content_hint", ""),
    }


def get_inspection_summary() -> Dict[str, Any]:
    """Return current inspection state for dashboard."""
    state = _load_interesting()
    watch_paths = [str(p) for p in get_watch_paths()]
    recent_files = list(state.get("files", {}).values())[:10]
    return {
        "watch_paths": watch_paths,
        "files_discovered": len(state.get("files", {})),
        "files_asked_about": len(state.get("last_asked", {})),
        "recent_files": recent_files,
    }
