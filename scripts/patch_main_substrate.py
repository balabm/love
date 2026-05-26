"""Patch api/main.py: start living substrate + expose /substrate endpoint."""
from pathlib import Path

p = Path(__file__).parent.parent / "api" / "main.py"
b = p.read_bytes()

if b"LIVING SUBSTRATE BOOT" in b:
    print("already patched")
    raise SystemExit(0)

nl = b"\r\n" if b"\r\n" in b[:4000] else b"\n"

# Pick a stable anchor: the existing Wave 17 evolution-routes block we know is present.
needle_options = [
    b"# Wave 17: Evolution Dashboard Routes",
]
needle = next((n for n in needle_options if n in b), None)
if needle is None:
    print("no anchor found")
    raise SystemExit(1)

block_lines = [
    "",
    "# ── LIVING SUBSTRATE BOOT (world model + SSM + MoE + homeostasis + body + HPC) ──",
    "try:",
    "    from core.living_substrate import start_living_substrate, substrate_snapshot",
    "    _LS_STATUS = start_living_substrate()",
    "    print(f'[API] Living Substrate online: {_LS_STATUS}')",
    "",
    "    @app.get('/substrate')",
    "    async def get_substrate():",
    "        return substrate_snapshot()",
    "",
    "    @app.get('/substrate/attention')",
    "    async def get_substrate_attention():",
    "        from core.hierarchical_predictive_coding import get_hpc",
    "        from core.world_model_latent import get_world_model_latent",
    "        return {",
    "            'level_attention': get_hpc().attention(),",
    "            'channel_attention': get_world_model_latent().attention_distribution(),",
    "            'inferred_activity': get_hpc().current_inferred_activity(),",
    "        }",
    "except Exception as e:",
    "    print(f'[API] Living Substrate boot error: {e}')",
    "",
]
inject = nl.join(s.encode("utf-8") for s in block_lines) + nl

new = b.replace(needle, inject + needle, 1)
p.write_bytes(new)
print(f"patched: +{len(new)-len(b)} bytes")
