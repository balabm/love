"""
Patch core/living_substrate.py to boot the IgnitionDaemon alongside the
other substrate systems.

Safe to re-run: checks for the sentinel comment before inserting.
Works with both LF and CRLF line endings (reads/writes in binary mode).

What it adds
------------
  In start_living_substrate():
    # 8. GWT Ignition daemon
    try:
        from core.ignition_daemon import start_ignition_daemon
        start_ignition_daemon()
        status["ignition_daemon"] = "ok"
    except Exception as e:
        status["ignition_daemon"] = f"err:{e}"

  In substrate_snapshot():
    try:
        from core.global_workspace import get_global_workspace
        snap["global_workspace"] = get_global_workspace().snapshot()
    except Exception as e:
        snap["global_workspace"] = {"err": str(e)}
"""
from pathlib import Path

SUBSTRATE = Path(__file__).parent.parent / "core" / "living_substrate.py"

# ── sentinels (checked before inserting to make patch idempotent) ─────────────
SENTINEL_START    = "# 8. GWT Ignition daemon"
SENTINEL_SNAPSHOT = "# global_workspace snapshot"

# ── block to inject into start_living_substrate() ────────────────────────────
START_BLOCK = """\

    # 8. GWT Ignition daemon
    try:
        from core.ignition_daemon import start_ignition_daemon
        start_ignition_daemon()
        status["ignition_daemon"] = "ok"
    except Exception as e:
        status["ignition_daemon"] = f"err:{e}"
"""

# ── block to inject into substrate_snapshot() ────────────────────────────────
SNAPSHOT_BLOCK = """\
    # global_workspace snapshot
    try:
        from core.global_workspace import get_global_workspace
        snap["global_workspace"] = get_global_workspace().snapshot()
    except Exception as e:
        snap["global_workspace"] = {"err": str(e)}
"""

# ── read ──────────────────────────────────────────────────────────────────────
raw = SUBSTRATE.read_bytes()
# Normalise to LF for manipulation; restore original ending style on write.
uses_crlf = b"\r\n" in raw
text = raw.replace(b"\r\n", b"\n").decode("utf-8")

changed = False

# ── inject into start_living_substrate() ─────────────────────────────────────
if SENTINEL_START not in text:
    # Insert just before the final print(...startup status...) line
    anchor = '    print(f"[LivingSubstrate] startup status: {status}")\n    return status'
    if anchor in text:
        text = text.replace(anchor, START_BLOCK + anchor)
        changed = True
        print("[patch] Inserted ignition_daemon start block into start_living_substrate()")
    else:
        print("[patch] WARNING: could not find insertion anchor in start_living_substrate()")
else:
    print("[patch] start block already present — skipping")

# ── inject into substrate_snapshot() ─────────────────────────────────────────
if SENTINEL_SNAPSHOT not in text:
    # Insert just before `return snap`
    snap_anchor = "    return snap\n"
    if snap_anchor in text:
        text = text.replace(
            snap_anchor,
            SNAPSHOT_BLOCK + snap_anchor,
            1,   # only replace the first occurrence (inside substrate_snapshot)
        )
        changed = True
        print("[patch] Inserted global_workspace snapshot block into substrate_snapshot()")
    else:
        print("[patch] WARNING: could not find 'return snap' anchor in substrate_snapshot()")
else:
    print("[patch] snapshot block already present — skipping")

# ── write back ────────────────────────────────────────────────────────────────
if changed:
    out = text.encode("utf-8")
    if uses_crlf:
        out = out.replace(b"\n", b"\r\n")
    SUBSTRATE.write_bytes(out)
    print(f"[patch] Written: {SUBSTRATE}")
else:
    print("[patch] No changes needed.")
