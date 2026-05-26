"""
Patch core/memory.py: wire FeedbackCollector implicit detection into save_memory().

Inspects the actual save_memory signature first. If the parameters needed for
implicit feedback (user_input / response) are not present, the script skips the
patch and explains why.

The injected block is guarded by try/except so it can never crash a save_memory
call — it is purely additive and observational.
"""
from pathlib import Path
import re

SENTINEL = b"[FEEDBACK-PATCH]"

memory_path = Path(__file__).parent.parent / "core" / "memory.py"
b = memory_path.read_bytes()

# ── Guard: already patched? ────────────────────────────────────────────────────
if SENTINEL in b:
    print("core/memory.py: already patched with FEEDBACK-PATCH — nothing to do.")
    raise SystemExit(0)

# ── Inspect save_memory signature ─────────────────────────────────────────────
sig_match = re.search(rb"def save_memory\(([^)]+)\)", b)
if not sig_match:
    print("SKIP: could not locate save_memory() in core/memory.py.")
    print("      Patch not applied.")
    raise SystemExit(0)

sig_text = sig_match.group(1).decode("utf-8", errors="replace")
print(f"Found save_memory signature: ({sig_text})")

has_user_input = "user_input" in sig_text
has_response   = "response"   in sig_text

if not has_user_input or not has_response:
    print("SKIP: save_memory() does not expose user_input / response params.")
    print(f"      Signature found: ({sig_text})")
    print("      Patch not applied — no suitable injection point.")
    raise SystemExit(0)

print("Parameters available. Proceeding with patch…")

# ── Detect line-ending style ───────────────────────────────────────────────────
nl = b"\r\n" if b"\r\n" in b else b"\n"

# ── Build the injection block ─────────────────────────────────────────────────
#
# We attach it right after the first try/except block that already lives inside
# save_memory (the HPC / MoE block).  The simplest reliable anchor is the last
# line of that block: the "pass" that closes the second except.  We find the
# body of save_memory and insert AFTER the existing reward-signal block.
#
# Anchor: the existing MoE try/except ends with:
#       except Exception:
#           pass
# followed by the ChromaDB collection.add() call.
# We'll inject our block just before collection.add() so it runs in the same
# function scope and has access to user_input / response.
#
# Anchor needle: the line "    # Save to local ChromaDB\n"
anchor_lf   = b"    # Save to local ChromaDB" + b"\n"
anchor_crlf = b"    # Save to local ChromaDB" + b"\r\n"
anchor = anchor_crlf if anchor_crlf in b else anchor_lf

if anchor not in b:
    print("SKIP: could not find '# Save to local ChromaDB' anchor in save_memory().")
    print("      The file may have been restructured. Patch not applied.")
    raise SystemExit(0)

inject = (
    b"    # [FEEDBACK-PATCH] implicit feedback detection" + nl
    + b"    try:" + nl
    + b"        from core.feedback_collector import get_feedback_collector" + nl
    + b"        _fc = get_feedback_collector()" + nl
    + b"        _prev = getattr(_fc, '_last_user_text', '')" + nl
    + b"        _sig = _fc.detect_implicit(user_input, _prev, response, 0)" + nl
    + b"        _fc._last_user_text = user_input" + nl
    + b"    except Exception:" + nl
    + b"        pass" + nl
    + anchor
)

new_b = b.replace(anchor, inject, 1)

if new_b == b:
    print("ERROR: replacement produced identical bytes — patch not written.")
    raise SystemExit(1)

memory_path.write_bytes(new_b)
delta = len(new_b) - len(b)
print(f"core/memory.py patched: +{delta} bytes injected at '# Save to local ChromaDB'.")
print("Implicit FeedbackCollector detection is now wired into save_memory().")
