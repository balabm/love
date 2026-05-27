"""
Patch core/agent.py to inject the RolloutPlanner context block immediately
after the [GW-PATCH] global workspace block, and add {_plan_ctx} to the
prompt f-string right after {_substrate_context_block}.

Safe to re-run: checks for [PLANNER-PATCH] sentinel before inserting.
Works with both LF and CRLF line endings (reads/writes in binary mode).

What it does
------------
1. Finds the closing `except Exception: / pass` of the [GW-PATCH] block.
2. Injects the [PLANNER-PATCH] block immediately after it.
3. Appends {_plan_ctx} to the prompt f-string right after
   {_substrate_context_block}.
4. Verifies syntax with py_compile.

Usage
-----
    python scripts/patch_agent_planner.py
"""
import py_compile
import sys
from pathlib import Path

AGENT = Path(__file__).parent.parent / "core" / "agent.py"

PATCH_MARKER = b"# [PLANNER-PATCH]"

# ── The block we inject ───────────────────────────────────────────────────────
# Written with CRLF line endings because agent.py uses CRLF.

INJECT_CRLF = (
    b"\r\n"
    b"    # [PLANNER-PATCH]\r\n"
    b"    _plan_ctx = \"\"\r\n"
    b"    try:\r\n"
    b"        from core.rollout_planner import get_rollout_planner\r\n"
    b"        _planner = get_rollout_planner()\r\n"
    b"        _plan_ctx = _planner.get_planning_context("
    b"user_input if 'user_input' in dir() else message)\r\n"
    b"    except Exception:\r\n"
    b"        _plan_ctx = \"\"\r\n"
)

# Same block in LF for files that don't use CRLF
INJECT_LF = INJECT_CRLF.replace(b"\r\n", b"\n")

# ── The needle: closing except/pass of the GW-PATCH block ────────────────────
# We anchor on the bytes that immediately follow the GW except block — the
# \r\n\r\n    # ═══ WAVE 16 line.  This guarantees we insert in the right spot.

# CRLF variant
NEEDLE_CRLF = (
    b"    except Exception:\r\n"
    b"        pass\r\n"
    b"\r\n"
    b"    # \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90 WAVE 16: NEURAL MESH CONTEXT \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\r\n"
)
# LF variant
NEEDLE_LF = NEEDLE_CRLF.replace(b"\r\n", b"\n")

# ── f-string targets ──────────────────────────────────────────────────────────

FSTR_NEEDLE_CRLF  = b"{_substrate_context_block}"
FSTR_REPLACE_CRLF = b"{_substrate_context_block}{_plan_ctx}"
FSTR_NEEDLE_LF    = FSTR_NEEDLE_CRLF
FSTR_REPLACE_LF   = FSTR_REPLACE_CRLF


def main():
    if not AGENT.exists():
        print(f"[PLANNER-PATCH] ERROR: {AGENT} not found.")
        sys.exit(1)

    data = AGENT.read_bytes()
    uses_crlf = b"\r\n" in data

    print(f"[PLANNER-PATCH] Read {len(data)} bytes from {AGENT}")
    print(f"[PLANNER-PATCH] Line endings: {'CRLF' if uses_crlf else 'LF'}")

    # ── Idempotency check ─────────────────────────────────────────────────────

    if PATCH_MARKER in data:
        print("[PLANNER-PATCH] Already patched — nothing to do.")
        _verify(AGENT)
        return

    # ── Find anchor ───────────────────────────────────────────────────────────

    gw_idx = data.find(b"# [GW-PATCH]")
    if gw_idx == -1:
        print("[PLANNER-PATCH] ERROR: [GW-PATCH] block not found in agent.py.")
        print("                Run scripts/patch_agent_global_workspace.py first.")
        sys.exit(2)
    print(f"[PLANNER-PATCH] Found [GW-PATCH] at byte {gw_idx}")

    needle = NEEDLE_CRLF if uses_crlf else NEEDLE_LF
    inject = INJECT_CRLF if uses_crlf else INJECT_LF

    # Search for the needle *after* the GW-PATCH block
    needle_idx = data.find(needle, gw_idx)

    if needle_idx == -1:
        # Diagnostic output
        print("[PLANNER-PATCH] Could not find WAVE 16 anchor needle.")
        wave16_idx = data.find(b"WAVE 16", gw_idx)
        if wave16_idx != -1:
            ctx = data[max(0, wave16_idx - 80): wave16_idx + 200]
            print("[PLANNER-PATCH] Context around 'WAVE 16':")
            print(repr(ctx))
        else:
            print("[PLANNER-PATCH] 'WAVE 16' not found after GW-PATCH.")
        print("[PLANNER-PATCH] Patch NOT applied.")
        sys.exit(3)

    print(f"[PLANNER-PATCH] Found WAVE 16 anchor needle at byte {needle_idx}")

    # Insert inject BEFORE the WAVE 16 line (after the preceding blank line)
    # i.e. we splice: ...pass\r\n  <-- INJECT_BLOCK here --> \r\n    # ═══ WAVE 16
    # The needle includes the closing except/pass so we split there:
    #   needle  =  "    except Exception:\r\n        pass\r\n\r\n    # ═══ WAVE 16..."
    # We want to insert INJECT between `pass\r\n` and `\r\n    # ═══ WAVE 16`.

    if uses_crlf:
        split_after = b"        pass\r\n"
    else:
        split_after = b"        pass\n"

    split_point = data.find(split_after, needle_idx)
    assert split_point != -1, "split_after not found after needle_idx — logic error"
    insert_at = split_point + len(split_after)

    patched = data[:insert_at] + inject + data[insert_at:]

    # ── Patch f-string ────────────────────────────────────────────────────────

    fstr_needle  = FSTR_NEEDLE_CRLF  if uses_crlf else FSTR_NEEDLE_LF
    fstr_replace = FSTR_REPLACE_CRLF if uses_crlf else FSTR_REPLACE_LF

    if fstr_needle in patched and fstr_replace not in patched:
        patched = patched.replace(fstr_needle, fstr_replace, 1)
        print("[PLANNER-PATCH] Patched prompt f-string: "
              "{_substrate_context_block} -> {_substrate_context_block}{_plan_ctx}")
    else:
        print("[PLANNER-PATCH] WARNING: could not patch f-string automatically "
              "(already patched or needle not found).")

    # ── Write ─────────────────────────────────────────────────────────────────

    AGENT.write_bytes(patched)
    added = len(patched) - len(data)
    print(f"[PLANNER-PATCH] Written {len(patched)} bytes (+{added}) -> {AGENT}")

    _verify(AGENT)


def _safe_print(msg: str):
    """Print safely even on Windows consoles with restricted codepages."""
    try:
        print(msg)
    except (UnicodeEncodeError, OSError):
        sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()


def _verify(path: Path):
    _safe_print("[PLANNER-PATCH] Verifying syntax with py_compile ...")
    try:
        py_compile.compile(str(path), doraise=True)
        _safe_print("[PLANNER-PATCH] OK  agent.py compiles cleanly.")
    except py_compile.PyCompileError as err:
        _safe_print(f"[PLANNER-PATCH] ERROR  Compile error after patching: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
