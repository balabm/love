"""
Sanitize LOVE data: quarantine corrupted LoRA adapters and normalize numeric fields
in evolution metrics/genome files.
Run: python tools/sanitize_love_data.py
"""
import json
import shutil
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
LORA_DIR = ROOT / "data" / "lora_evolution" / "adapters"
CORRUPT_DIR = ROOT / "data" / "lora_evolution" / "corrupted_adapters"
METRICS_FILE = ROOT / "data" / "evolution" / "metrics.json"
GENOME_FILE = ROOT / "data" / "evolution" / "genome.json"

CORRUPT_DIR.mkdir(parents=True, exist_ok=True)

def quarantine_adapters():
    moved = []
    for p in LORA_DIR.glob("*.npz"):
        try:
            # attempt to open
            with np.load(str(p), allow_pickle=False) as data:
                pass
        except Exception as e:
            ts = int(time.time())
            target = CORRUPT_DIR / f"{p.stem}.{ts}.npz.corrupt"
            try:
                shutil.move(str(p), str(target))
                moved.append((str(p), str(target), str(e)))
            except Exception as e2:
                print(f"Failed to move {p}: {e2}")
    return moved


def _try_convert_scalar(s):
    from fractions import Fraction
    if not isinstance(s, str):
        return s
    s_strip = s.strip()
    if s_strip.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
        return s_strip.lower() in ('true', '1', 'yes')
    if '/' in s_strip:
        try:
            return float(Fraction(s_strip))
        except Exception:
            pass
    try:
        if '.' in s_strip or 'e' in s_strip.lower():
            return float(s_strip)
        return int(s_strip)
    except Exception:
        try:
            return float(s_strip)
        except Exception:
            return s


def sanitize_metrics():
    changed = False
    if METRICS_FILE.exists():
        try:
            data = json.loads(METRICS_FILE.read_text(encoding='utf-8'))
            inter = data.get('interactions', [])
            for r in inter:
                for k in ['response_quality','user_satisfaction','latency_ms','tokens_used','context_relevance']:
                    if k in r and isinstance(r[k], str):
                        r[k] = _try_convert_scalar(r[k])
                        changed = True
            if changed:
                METRICS_FILE.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')
        except Exception as e:
            print('Failed to sanitize metrics:', e)
    return changed


if __name__ == '__main__':
    print('Quarantining corrupted adapters...')
    moved = quarantine_adapters()
    for src,tgt,err in moved:
        print('Moved', src, '->', tgt, 'reason:', err)
    print('Sanitizing metrics...')
    changed = sanitize_metrics()
    print('Metrics changed:', changed)
    print('Done')
