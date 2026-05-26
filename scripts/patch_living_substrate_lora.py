"""
Patch core/living_substrate.py to boot LoRAEvolution daemon
and surface it in substrate_snapshot().

Safe to re-run: checks for the sentinel comment before inserting.
Works with both LF and CRLF line endings.
"""
from pathlib import Path

SUBSTRATE = Path(__file__).parent.parent / "core" / "living_substrate.py"

SENTINEL_START = "# 8. LoRA evolution daemon"

START_BLOCK = """\

    # 8. LoRA evolution daemon
    try:
        from core.lora_evolution import get_lora_evolution
        get_lora_evolution().start_daemon(interval_hours=6)
        status["lora_evolution"] = "ok"
    except Exception as e:
        status["lora_evolution"] = f"err:{e}"
"""

SNAPSHOT_SENTINEL = "# lora_evolution snapshot"

SNAPSHOT_BLOCK = """\
    try:
        from core.lora_evolution import get_lora_evolution
        snap["lora_evolution"] = get_lora_evolution().snapshot()
    except Exception as e:
        snap["lora_evolution"] = {"err": str(e)}
"""

# ── read ──────────────────────────────────────────────────────────────────────
raw = SUBSTRATE.read_bytes()
# Normalise to LF for manipulation; we'll restore the original ending style.
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
        print("[patch] Inserted lora_evolution start block into start_living_substrate()")
    else:
        print("[patch] WARNING: could not find insertion anchor in start_living_substrate()")
else:
    print("[patch] start block already present — skipping")

# ── inject into substrate_snapshot() ─────────────────────────────────────────
if SNAPSHOT_SENTINEL not in text:
    # Insert just before `return snap`
    snap_anchor = "    return snap\n"
    if snap_anchor in text:
        text = text.replace(
            snap_anchor,
            "    " + SNAPSHOT_SENTINEL + "\n" + SNAPSHOT_BLOCK + snap_anchor,
            1,
        )
        changed = True
        print("[patch] Inserted lora_evolution snapshot block into substrate_snapshot()")
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
