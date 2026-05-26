"""One-shot patch: inject living-substrate hooks into core/agent.py (CRLF-safe)."""
from pathlib import Path

p = Path(__file__).parent.parent / "core" / "agent.py"
b = p.read_bytes()

needle = b"    # Ping idle mind \xe2\x80\x94 user is active\r\n    ping_active()\r\n"

inject = (
    b"\r\n"
    b"    # \xe2\x94\x80\xe2\x94\x80 LIVING SUBSTRATE: feed every turn into the predictive hierarchy \xe2\x94\x80\xe2\x94\x80\r\n"
    b"    try:\r\n"
    b"        from core.hierarchical_predictive_coding import get_hpc\r\n"
    b"        get_hpc().feed(user_input, source=\"user\")\r\n"
    b"    except Exception:\r\n"
    b"        pass\r\n"
    b"    try:\r\n"
    b"        from core.world_model_latent import get_world_model_latent\r\n"
    b"        from core.state_space_memory import get_ssm_memory\r\n"
    b"        _wm = get_world_model_latent()\r\n"
    b"        if _wm._recent_obs:\r\n"
    b"            get_ssm_memory().step(_wm._recent_obs[-1].state)\r\n"
    b"    except Exception:\r\n"
    b"        pass\r\n"
)

if b"LIVING SUBSTRATE" in b:
    print("already patched")
elif needle not in b:
    print("needle missing; aborting")
else:
    new = b.replace(needle, needle + inject, 1)
    p.write_bytes(new)
    print(f"patched: +{len(new)-len(b)} bytes")
