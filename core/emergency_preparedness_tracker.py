"""
LOVE Emergency Preparedness Tracker — Safety Intelligence (Modern AI Pattern)

Most emergency prep is a one-time checklist. This tracker:

1. PREPAREDNESS TRACKING
   - Track emergency kit inventory (food, water, medical, tools, documents)
   - Record emergency plan status (meeting points, contacts, routes)
   - Log drills and their effectiveness

2. READINESS SCORING
   - Calculate readiness score across categories (food, water, medical, communication, shelter)
   - Identify critical gaps in preparedness
   - Track expiration dates of supplies

3. MAINTENANCE REMINDERS
   - Alert when supplies need rotation or replacement
   - Suggest drill scheduling
   - Remind about seasonal prep updates

4. SCENARIO PLANNING
   - Track preparation for specific scenarios (power outage, natural disaster, etc.)
   - Suggest scenario-specific additions to kit
   - Monitor regional risk factors

Architecture:
- record_supply(category, item, quantity, expiry): Log supply
- record_drill(scenario, effectiveness): Log emergency drill
- get_readiness_score(): Get overall readiness score
- get_preparation_gaps(): Identify missing supplies
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "emergency_preparedness_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SUPPLY_LOG = DATA_DIR / "supplies.jsonl"
DRILL_LOG = DATA_DIR / "drills.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class EmergencySupply:
    """An emergency supply item."""
    category: str = ""  # food, water, medical, tools, communication, shelter, documents, power
    item: str = ""
    quantity: int = 0
    unit: str = ""
    expiry_date: Optional[str] = None
    last_checked: str = field(default_factory=lambda: datetime.now().isoformat())
    condition: str = "good"  # good, fair, poor, expired
    notes: str = ""


@dataclass
class EmergencyDrill:
    """An emergency drill record."""
    scenario: str = ""  # fire, earthquake, flood, power_outage, evacuation, lockdown
    duration_minutes: float = 0.0
    effectiveness: float = 0.5
    issues_found: List[str] = field(default_factory=list)
    improvements_made: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    participants: int = 1


class EmergencyPreparednessTracker:
    """
    Track emergency preparedness with intelligent gap detection.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._supplies: Dict[str, EmergencySupply] = {}
        self._drills: deque = deque(maxlen=100)
        self._stats = {
            "total_supplies": 0,
            "total_drills": 0,
            "avg_drill_effectiveness": 0.5,
            "last_full_check": None,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_supply(self, category: str, item: str, quantity: int = 0, unit: str = "", expiry_date: Optional[str] = None, condition: str = "good", notes: str = "") -> EmergencySupply:
        """Record or update an emergency supply."""
        supply_id = f"{category}_{item.replace(' ', '_').lower()}"
        supply = EmergencySupply(
            category=category or "general",
            item=item,
            quantity=quantity,
            unit=unit or "item",
            expiry_date=expiry_date,
            condition=condition,
            notes=notes,
        )

        with self._lock:
            self._supplies[supply_id] = supply
            self._stats["total_supplies"] = len(self._supplies)

        self._save_stats()
        self._log_supply(supply)

        return supply

    def record_drill(self, scenario: str, duration: float = 0, effectiveness: float = 0.5, issues: Optional[List[str]] = None, improvements: Optional[List[str]] = None, participants: int = 1) -> EmergencyDrill:
        """Record an emergency drill."""
        drill = EmergencyDrill(
            scenario=scenario or "general",
            duration_minutes=duration,
            effectiveness=effectiveness,
            issues_found=issues or [],
            improvements_made=improvements or [],
            participants=participants,
        )

        with self._lock:
            self._drills.append(drill)
            self._stats["total_drills"] += 1
            self._update_stats(drill)

        self._save_stats()
        self._log_drill(drill)

        return drill

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_readiness_score(self) -> Dict[str, Any]:
        """Get overall readiness score by category."""
        # Define target quantities for each category
        targets = {
            "water": 14,  # gallons per person (1 gal/day for 2 weeks)
            "food": 42,   # meals per person (3 meals/day for 2 weeks)
            "medical": 1, # first aid kit per household
            "tools": 3,   # flashlight, radio, multi-tool
            "communication": 2, # phone + backup power
            "shelter": 1, # emergency blanket/tent
            "documents": 1, # document copies
            "power": 2,   # power banks + solar
        }

        category_scores = {}
        category_items = defaultdict(list)

        for supply in self._supplies.values():
            category_items[supply.category].append(supply)

        for category, target in targets.items():
            items = category_items.get(category, [])
            if items:
                total_quantity = sum(s.quantity for s in items)
                # Check expiry for food/water/medical
                expired = sum(1 for s in items if s.condition == "expired")
                score = min(100, (total_quantity / max(1, target)) * 100)
                if expired > 0:
                    score *= 0.8  # Penalty for expired items
                category_scores[category] = {
                    "score": round(score, 1),
                    "current": total_quantity,
                    "target": target,
                    "expired": expired,
                    "status": "ready" if score >= 80 else "adequate" if score >= 50 else "insufficient",
                }
            else:
                category_scores[category] = {
                    "score": 0,
                    "current": 0,
                    "target": target,
                    "expired": 0,
                    "status": "missing",
                }

        overall = sum(c["score"] for c in category_scores.values()) / len(category_scores) if category_scores else 0

        return {
            "overall_score": round(overall, 1),
            "categories": category_scores,
            "total_items": len(self._supplies),
            "last_drill": self._drills[-1].timestamp if self._drills else None,
            "drills_count": len(self._drills),
        }

    def get_preparation_gaps(self) -> List[Dict[str, Any]]:
        """Identify critical preparedness gaps."""
        gaps = []
        readiness = self.get_readiness_score()
        categories = readiness.get("categories", {})

        for category, data in categories.items():
            if data["status"] == "missing":
                gaps.append({
                    "category": category,
                    "severity": "critical",
                    "gap": f"No {category} supplies recorded",
                    "action": f"Add {category} items to your emergency kit immediately.",
                })
            elif data["status"] == "insufficient":
                gaps.append({
                    "category": category,
                    "severity": "high",
                    "gap": f"Only {data['current']} {category} items (target: {data['target']})",
                    "action": f"Add {data['target'] - data['current']} more {category} items.",
                })

        # Check expired items
        expired_items = [s for s in self._supplies.values() if s.condition == "expired"]
        if expired_items:
            gaps.append({
                "category": "expired",
                "severity": "medium",
                "gap": f"{len(expired_items)} items have expired",
                "action": "Replace expired supplies and check dates quarterly.",
            })

        # Check drill recency
        if not self._drills:
            gaps.append({
                "category": "drills",
                "severity": "medium",
                "gap": "No emergency drills recorded",
                "action": "Schedule a fire drill or evacuation practice this month.",
            })
        else:
            last_drill = datetime.fromisoformat(self._drills[-1].timestamp)
            months_since = (datetime.now() - last_drill).days / 30
            if months_since > 3:
                gaps.append({
                    "category": "drills",
                    "severity": "medium",
                    "gap": f"Last drill was {months_since:.0f} months ago",
                    "action": "Schedule a drill soon. Skills fade without practice.",
                })

        return sorted(gaps, key=lambda x: {"critical": 0, "high": 1, "medium": 2}[x["severity"]])

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, drill: EmergencyDrill):
        """Update running statistics."""
        n = self._stats["total_drills"]
        self._stats["avg_drill_effectiveness"] = round((self._stats["avg_drill_effectiveness"] * (n - 1) + drill.effectiveness) / n, 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "supplies": {k: {
                    "category": v.category,
                    "item": v.item,
                    "quantity": v.quantity,
                    "unit": v.unit,
                    "expiry_date": v.expiry_date,
                    "condition": v.condition,
                } for k, v in self._supplies.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emergency_preparedness_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("supplies", {}).items():
                    self._supplies[k] = EmergencySupply(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emergency_preparedness_tracker")

    def _log_supply(self, supply: EmergencySupply):
        try:
            with open(SUPPLY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": supply.last_checked,
                    "category": supply.category,
                    "item": supply.item,
                    "quantity": supply.quantity,
                    "condition": supply.condition,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emergency_preparedness_tracker")

    def _log_drill(self, drill: EmergencyDrill):
        try:
            with open(DRILL_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": drill.timestamp,
                    "scenario": drill.scenario,
                    "duration": drill.duration_minutes,
                    "effectiveness": drill.effectiveness,
                    "issues": drill.issues_found,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.emergency_preparedness_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_ept_instance: Optional[EmergencyPreparednessTracker] = None
_ept_lock = threading.Lock()


def get_emergency_preparedness_tracker() -> EmergencyPreparednessTracker:
    global _ept_instance
    with _ept_lock:
        if _ept_instance is None:
            _ept_instance = EmergencyPreparednessTracker()
        return _ept_instance
