"""
Patch core/agent.py to use GlobalWorkspace GWT gating instead of raw substrate
injection in the WAVE 16 NEURAL MESH block.

The patch:
  1. Reads core/agent.py in binary mode (preserves CRLF)
  2. Locates the WAVE 16 NEURAL MESH block (lines ~998-1006 as of this writing)
  3. Prepends a GWT-gated substrate context block just before that section
  4. Writes back in binary mode

If the patch is already applied, or the needle is not found, the script reports
cleanly without touching the file.

Run from the project root:
    python scripts/patch_agent_global_workspace.py
"""
from pathlib import Path
import sys

AGENT = Path(__file__).parent.parent / "core" / "agent.py"

# ── the exact block we're adding right before the WAVE 16 neural mesh section ──
PATCH_MARKER = b"# [GW-PATCH]"   # idempotency sentinel

# We insert immediately before the "# \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90 WAVE 16: NEURAL MESH CONTEXT"
# line, which starts with these bytes in both LF and CRLF files.
NEEDLE_CANDIDATES = [
    b"    # \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90 WAVE 16: NEURAL MESH CONTEXT \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\r\n",
    b"    # \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90 WAVE 16: NEURAL MESH CONTEXT \xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\n",
]

INJECT = b"""\
    # [GW-PATCH] GLOBAL WORKSPACE THEORY -- GWT-gated substrate context\r
    # Replaces raw substrate dump with attention-filtered broadcast signals.\r
    # Only the highest-surprise / most-attention-worthy substrate signals\r
    # enter the LLM prompt.  Everything else stays pre-conscious.\r
    _substrate_context_block = ""\r
    try:\r
        from core.living_substrate import substrate_snapshot as _sub_snap\r
        from core.hierarchical_predictive_coding import get_hpc as _get_hpc\r
        from core.global_workspace import get_global_workspace as _get_gw\r
        _substrate_snap = _sub_snap()\r
        _hpc_snap = _get_hpc().snapshot()\r
        _hpc_attn = _hpc_snap.get("attention", {})\r
        _moe_winner = (\r
            _substrate_snap.get("moe_router", {}).get("last_winner", "")\r
            if isinstance(_substrate_snap, dict) else ""\r
        )\r
        _gw = _get_gw()\r
        _gated = _gw.gate_substrate_for_prompt(_substrate_snap, _hpc_attn, _moe_winner)\r
        if _gw.should_inject(_gated):\r
            _substrate_context_block = ("\\n\\n=== SUBSTRATE (global workspace broadcast) ===\\n"\r
                                        + _gw.format_for_prompt(_gated))\r
    except Exception:\r
        pass\r
\r
"""


def _find_needle(data: bytes):
    for n in NEEDLE_CANDIDATES:
        idx = data.find(n)
        if idx != -1:
            return idx, n
    return -1, None


def main():
    if not AGENT.exists():
        print(f"[GW-PATCH] ERROR: {AGENT} not found.")
        sys.exit(1)

    data = AGENT.read_bytes()

    # Idempotency check
    if PATCH_MARKER in data:
        print("[GW-PATCH] Already patched — nothing to do.")
        return

    idx, needle = _find_needle(data)

    if idx == -1:
        # Print diagnostic context so the human can see what's around "WAVE 16"
        wave16_idx = data.find(b"WAVE 16")
        if wave16_idx != -1:
            ctx_start = max(0, wave16_idx - 100)
            ctx_end   = min(len(data), wave16_idx + 400)
            print("[GW-PATCH] Could not find exact needle, but found 'WAVE 16' at byte",
                  wave16_idx)
            print("[GW-PATCH] Context (500 bytes):")
            print(repr(data[ctx_start:ctx_end]))
        else:
            print("[GW-PATCH] WAVE 16 not found in agent.py.")
            print("[GW-PATCH] Searching for 'neural_block'...")
            nb_idx = data.find(b"neural_block")
            if nb_idx != -1:
                ctx = data[max(0, nb_idx - 80): nb_idx + 400]
                print("[GW-PATCH] Context around 'neural_block':")
                print(repr(ctx))
        print()
        print("[GW-PATCH] Patch NOT applied.  Please add the GWT block manually "
              "just before the WAVE 16 NEURAL MESH section (around line 998).")
        sys.exit(2)

    # Also update the prompt f-string to include _substrate_context_block.
    # The f-string ends with {neural_block} — we add {_substrate_context_block}
    # right after it so it appears as a distinct section.
    FSTR_NEEDLE   = b"{neural_block}"
    FSTR_REPLACE  = b"{neural_block}{_substrate_context_block}"

    patched = data[:idx] + INJECT + data[idx:]

    if FSTR_NEEDLE in patched and FSTR_REPLACE not in patched:
        patched = patched.replace(FSTR_NEEDLE, FSTR_REPLACE, 1)
        fstr_patched = True
    else:
        fstr_patched = False

    AGENT.write_bytes(patched)

    added_bytes = len(patched) - len(data)
    print(f"[GW-PATCH] Patch applied successfully (+{added_bytes} bytes).")
    if fstr_patched:
        print("[GW-PATCH] Also patched prompt f-string: {neural_block} -> "
              "{neural_block}{_substrate_context_block}")
    else:
        print("[GW-PATCH] WARNING: Could not patch prompt f-string automatically.")
        print("           Add {_substrate_context_block} to the prompt= f-string "
              "in agent.py's chat() function manually.")


if __name__ == "__main__":
    main()
