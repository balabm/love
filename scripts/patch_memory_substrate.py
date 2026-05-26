"""Patch core/memory.py: feed LOVE's responses into the substrate + emit MoE reward."""
from pathlib import Path

p = Path(__file__).parent.parent / "core" / "memory.py"
b = p.read_bytes()

if b"LIVING SUBSTRATE feedback" in b:
    print("already patched")
    raise SystemExit(0)

# Find end of save_memory by looking for its def line, then insert hook at top of body.
needle_lf = b'def save_memory(user_input: str, response: str, mode: str = "general"):\n    """Save a conversation turn to memory and sync across devices."""\n'
needle_crlf = needle_lf.replace(b"\n", b"\r\n")
needle = needle_crlf if needle_crlf in b else needle_lf
if needle not in b:
    print("needle not found")
    raise SystemExit(1)
nl = b"\r\n" if needle is needle_crlf else b"\n"

inject = (
    nl
    + b"    # -- LIVING SUBSTRATE feedback: response goes back through predictive layers --" + nl
    + b"    try:" + nl
    + b"        from core.hierarchical_predictive_coding import get_hpc" + nl
    + b"        get_hpc().feed(response, source=\"love\")" + nl
    + b"    except Exception:" + nl
    + b"        pass" + nl
    + b"    try:" + nl
    + b"        # Implicit reward: short user follow-ups w/ thanks => positive, corrections => negative" + nl
    + b"        from core.moe_router import get_moe_router" + nl
    + b"        r_signal = 0.0" + nl
    + b"        ul = user_input.lower()" + nl
    + b"        if any(w in ul for w in [\"thanks\", \"perfect\", \"great\", \"exactly\", \"helpful\"]):" + nl
    + b"            r_signal = 0.6" + nl
    + b"        elif any(w in ul for w in [\"wrong\", \"no that\", \"not quite\", \"actually,\", \"i meant\"]):" + nl
    + b"            r_signal = -0.6" + nl
    + b"        if r_signal != 0.0:" + nl
    + b"            get_moe_router().reinforce(\"core_agent_chat\", user_input, r_signal)" + nl
    + b"    except Exception:" + nl
    + b"        pass" + nl
)

new = b.replace(needle, needle + inject, 1)
p.write_bytes(new)
print(f"patched: +{len(new)-len(b)} bytes")
