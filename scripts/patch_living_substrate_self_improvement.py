"""
Patch core/living_substrate.py to boot AutonomousSelfImprovement daemon
and surface it in substrate_snapshot().

Safe to re-run: checks for sentinel comments before inserting.
Works with both LF and CRLF line endings (reads/writes in binary mode).

What it does
------------
1. Appends an entry to start_living_substrate() directly after the
   replay_consolidation block (item 7), registering a new item 8.
2. Adds a try/except block for self_improvement to substrate_snapshot().

Usage
-----
    python scripts/patch_living_substrate_self_improvement.py
"""
import py_compile
import sys
from pathlib import Path

SUBSTRATE = Path(__file__).parent.parent / "core" / "living_substrate.py"

# ── Sentinels (text must be ABSENT for the patch to apply) ───────────────────

SENTINEL_START    = "# 8. Autonomous self-improvement daemon"
SENTINEL_SNAPSHOT = "# self_improvement snapshot"

# ── Code blocks to inject ─────────────────────────────────────────────────────

START_BLOCK = """\

    # 8. Autonomous self-improvement daemon
    try:
        from core.autonomous_self_improvement import get_autonomous_self_improvement
        get_autonomous_self_improvement().start_daemon()
        status["self_improvement"] = "ok"
    except Exception as e:
        status["self_improvement"] = f"err:{e}"
"""

SNAPSHOT_BLOCK = """\
    # self_improvement snapshot
    try:
        from core.autonomous_self_improvement import get_autonomous_self_improvement
        snap["self_improvement"] = get_autonomous_self_improvement().snapshot()
    except Exception as e:
        snap["self_improvement"] = {"err": str(e)}
"""

# ── Read ──────────────────────────────────────────────────────────────────────

if not SUBSTRATE.exists():
    print(f"[patch] ERROR: {SUBSTRATE} not found.")
    sys.exit(1)

raw = SUBSTRATE.read_bytes()
print(f"[patch] Read {len(raw)} bytes from {SUBSTRATE}")

# Normalise to LF for string manipulation; restore original ending on write.
uses_crlf = b"\r\n" in raw
text = raw.replace(b"\r\n", b"\n").decode("utf-8")

changed = False

# ── Inject into start_living_substrate() ─────────────────────────────────────

if SENTINEL_START in text:
    print("[patch] start block already present - skipping start_living_substrate() patch")
else:
    # Anchor: the replay_consolidation block we know exists (added by the previous patch).
    # We insert the new block right before the existing print/return lines.
    anchor = '    print(f"[LivingSubstrate] startup status: {status}")\n    return status'
    if anchor in text:
        text = text.replace(anchor, START_BLOCK + anchor)
        changed = True
        print("[patch] Inserted self_improvement start_daemon() block into start_living_substrate()")
    else:
        # Fallback: try to find the replay_consolidation block and insert after its except line
        replay_anchor = '        status["replay_consolidation"] = f"err:{e}"\n'
        if replay_anchor in text:
            text = text.replace(replay_anchor, replay_anchor + START_BLOCK, 1)
            changed = True
            print("[patch] Inserted self_improvement start block after replay_consolidation (fallback anchor)")
        else:
            print("[patch] WARNING: could not find insertion anchor in start_living_substrate() - skipping")

# ── Inject into substrate_snapshot() ─────────────────────────────────────────

if SENTINEL_SNAPSHOT in text:
    print("[patch] snapshot block already present - skipping substrate_snapshot() patch")
else:
    # Insert just before `return snap`
    snap_anchor = "    return snap\n"
    if snap_anchor in text:
        text = text.replace(snap_anchor, SNAPSHOT_BLOCK + snap_anchor, 1)
        changed = True
        print("[patch] Inserted self_improvement snapshot block into substrate_snapshot()")
    else:
        print("[patch] WARNING: could not find 'return snap' anchor in substrate_snapshot() - skipping")

# ── Write back (preserving original line endings) ─────────────────────────────

if changed:
    out = text.encode("utf-8")
    if uses_crlf:
        out = out.replace(b"\n", b"\r\n")
    SUBSTRATE.write_bytes(out)
    print(f"[patch] Written {len(out)} bytes -> {SUBSTRATE}")
else:
    print("[patch] No changes needed.")

# ── Verify syntax ─────────────────────────────────────────────────────────────

print("[patch] Verifying syntax with py_compile ...")
try:
    py_compile.compile(str(SUBSTRATE), doraise=True)
    print("[patch] OK  living_substrate.py compiles cleanly.")
except py_compile.PyCompileError as err:
    print(f"[patch] ERROR  Compile error after patching: {err}")
    sys.exit(1)
