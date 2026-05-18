"""
LOVE Curiosity Engine — actively fills knowledge gaps.
"""
import json, re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
GAPS_FILE = DATA_DIR / "knowledge_gaps.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_gaps() -> List[Dict]: 
    return json.loads(GAPS_FILE.read_text()) if GAPS_FILE.exists() else []

def _save_gaps(gaps: List[Dict]):
    GAPS_FILE.write_text(json.dumps(gaps, indent=2))

def detect_gaps_from_conversation(user_input: str, love_response: str) -> List[Dict]:
    gaps = _load_gaps()
    new_gaps = []
    text = f"{user_input} {love_response}".lower()
    names = re.findall(r'\b[A-Z][a-z]{2,}\b', user_input)
    known = set()
    try:
        from core.dream_engine import get_world_model
        known = set(get_world_model().get("people", {}).keys())
    except Exception:
        pass
    for name in names:
        if name in ("I","The","You","This","That","What","How") or len(name) < 4:
            continue
        if name not in known and not any(g["subject"]==name for g in gaps):
            new_gaps.append({"id":f"gap_{name.lower()}","type":"unknown_person","subject":name,"context":user_input[:100],"status":"open","priority":"medium","discovered_at":datetime.now().isoformat()})
    if any(p in text for p in ["i want to","i need to","planning to"]):
        m = re.search(r'(?:want to|need to|planning to)\s+(.{10,80})', user_input, re.IGNORECASE)
        if m:
            goal = m.group(1).strip()
            new_gaps.append({"id":f"gap_goal_{int(datetime.now().timestamp())}","type":"unclear_goal","subject":goal,"context":user_input[:100],"status":"open","priority":"high","discovered_at":datetime.now().isoformat()})
    gaps.extend(new_gaps)
    _save_gaps(gaps)
    return new_gaps

def get_top_gaps_for_prompt() -> str:
    gaps = [g for g in _load_gaps() if g.get("status")=="open"]
    if not gaps: return ""
    gaps.sort(key=lambda g:{"high":0,"medium":1,"low":2}.get(g.get("priority","low"),2))
    lines = ["[THINGS I'M CURIOUS ABOUT — knowledge gaps I'm working to fill]"]
    for g in gaps[:3]: lines.append(f"- {g['subject']} ({g['type']})")
    return "\n".join(lines)

def enrich_prompt() -> str: 
    return get_top_gaps_for_prompt()


def get_open_gaps() -> List[Dict]:
    """Get all open knowledge gaps sorted by priority."""
    gaps = _load_gaps()
    open_gaps = [g for g in gaps if g.get("status") == "open"]
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    open_gaps.sort(key=lambda g: priority_order.get(g.get("priority", "low"), 2))
    return open_gaps
