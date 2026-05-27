"""
Patch core/living_substrate.py to boot the RolloutPlanner and surface it
in substrate_snapshot().

Safe to re-run: checks for sentinel comments before inserting.
Works with both LF and CRLF line endings (reads/writes in binary mode).

What it does
------------
1. Appends a "# 9. Rollout planner" entry to start_living_substrate()
   just before the print/return lines.
2. Adds a rollout_planner try/except block to substrate_snapshot() so
   snap["rollout_planner"] is populated.

Usage
-----
    python scripts/patch_living_substrate_planner.py
"""
import py_compile
import sys
from pathlib import Path

SUBSTRATE = Path(__file__).parent.parent / "core" / "living_substrate.py"

# ── Sentinels (text must be ABSENT for the patch to apply) ───────────────────

SENTINEL_START    = "# 9. Rollout planner"
SENTINEL_SNAPSHOT = "# rollout_planner snapshot"

# ── Code blocks to inject ─────────────────────────────────────────────────────

START_BLOCK = """\

    # 9. Rollout planner
    try:
        from core.rollout_planner import get_rollout_planner
        get_rollout_planner()
        status["rollout_planner"] = "ok"
    except Exception as e:
        status["rollout_planner"] = f"err:{e}"
"""

SNAPSHOT_BLOCK = """\
    # rollout_planner snapshot
    try:
        from core.rollout_planner import get_rollout_planner
        snap["rollout_planner"] = get_rollout_planner().snapshot()
    except Exception as e:
        snap["rollout_planner"] = {"err": str(e)}
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
    # Anchor: the print/return tail of start_living_substrate().
    anchor = '    print(f"[LivingSubstrate] startup status: {status}")\n    return status'
    if anchor in text:
        text = text.replace(anchor, START_BLOCK + anchor, 1)
        changed = True
        print("[patch] Inserted rollout_planner boot block into start_living_substrate()")
    else:
        print("[patch] WARNING: could not find print/return anchor in start_living_substrate() — skipping")

# ── Inject into substrate_snapshot() ─────────────────────────────────────────

if SENTINEL_SNAPSHOT in text:
    print("[patch] snapshot block already present - skipping substrate_snapshot() patch")
else:
    snap_anchor = "    return snap\n"
    if snap_anchor in text:
        # Insert just before the final `return snap`
        last_idx = text.rfind(snap_anchor)
        text = text[:last_idx] + SNAPSHOT_BLOCK + text[last_idx:]
        changed = True
        print("[patch] Inserted rollout_planner snapshot block into substrate_snapshot()")
    else:
        print("[patch] WARNING: could not find 'return snap' anchor in substrate_snapshot() — skipping")

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
