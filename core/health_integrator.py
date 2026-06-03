"""
LOVE Health Integrator — Holistic Health Intelligence (Modern AI Pattern)

Most health tracking is siloed and reactive. This integrator:

1. HEALTH INTEGRATION
   - Pull data from sleep, nutrition, movement, and other health engines
   - Track correlations between health domains
   - Log overall wellbeing snapshots

2. PATTERN ANALYSIS
   - Identify health leverage points (small changes with big effects)
   - Find vicious cycles (poor sleep -> poor eating -> poor movement)
   - Detect virtuous cycles (good sleep -> good choices -> more energy)

3. HOLISTIC GUIDANCE
   - Suggest the one health change with highest impact
   - Provide daily health priorities based on current state
   - Recommend integration practices (meal timing with sleep, movement with energy)

4. PREVENTION
   - Track early warning signs of burnout, illness, or decline
   - Alert when multiple health domains are deteriorating
   - Celebrate holistic health wins

Architecture:
- record_wellbeing_snapshot(sleep, nutrition, movement, mood, energy): Log snapshot
- get_health_stats(): Get holistic health analysis
- get_health_priority(current_state): Get priority
- get_health_score(): Calculate overall holistic health
"""

import json
import math
import random
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "health_integrator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WELLBEING_LOG = DATA_DIR / "wellbeing.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class WellbeingSnapshot:
    """A holistic wellbeing snapshot."""
    snapshot_id: str = ""
    sleep_hours: float = 0.0
    sleep_quality: float = 0.5  # 0-1
    nutrition_quality: float = 0.5  # 0-1
    movement_minutes: float = 0.0
    movement_satisfaction: float = 0.5
    mood: float = 0.5  # 0-1
    energy: float = 0.5  # 0-1
    stress: float = 0.5  # 0-1
    social_connection: float = 0.5  # 0-1
    focus_quality: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class HealthIntegrator:
    """
    Intelligent health integrator with correlation analysis and leverage point detection.
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
        self._snapshots: deque = deque(maxlen=200)
        self._stats = {
            "total_snapshots": 0,
            "avg_wellbeing": 0.0,
            "weakest_domain": "",
            "strongest_domain": "",
            "vicious_cycle_risk": False,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_wellbeing_snapshot(self, sleep_hours: float = 0.0, sleep_quality: float = 0.5, nutrition_quality: float = 0.5, movement_minutes: float = 0.0, movement_satisfaction: float = 0.5, mood: float = 0.5, energy: float = 0.5, stress: float = 0.5, social_connection: float = 0.5, focus_quality: float = 0.5, notes: str = "") -> WellbeingSnapshot:
        """Record a wellbeing snapshot."""
        snapshot_id = f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._snapshots)}"
        snapshot = WellbeingSnapshot(
            snapshot_id=snapshot_id,
            sleep_hours=sleep_hours,
            sleep_quality=sleep_quality,
            nutrition_quality=nutrition_quality,
            movement_minutes=movement_minutes,
            movement_satisfaction=movement_satisfaction,
            mood=mood,
            energy=energy,
            stress=stress,
            social_connection=social_connection,
            focus_quality=focus_quality,
            notes=notes,
        )

        with self._lock:
            self._snapshots.append(snapshot)
            self._stats["total_snapshots"] += 1
            self._update_stats()

        self._save_stats()
        self._log_snapshot(snapshot)

        return snapshot

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_health_stats(self) -> Dict[str, Any]:
        """Get holistic health analysis."""
        if not self._snapshots:
            return {"status": "insufficient_data"}

        # Domain analysis
        domains = {
            "sleep": [s.sleep_quality for s in self._snapshots],
            "nutrition": [s.nutrition_quality for s in self._snapshots],
            "movement": [s.movement_satisfaction for s in self._snapshots],
            "mood": [s.mood for s in self._snapshots],
            "energy": [s.energy for s in self._snapshots],
            "social": [s.social_connection for s in self._snapshots],
            "focus": [s.focus_quality for s in self._snapshots],
        }

        domain_stats = {}
        for name, values in domains.items():
            domain_stats[name] = {
                "avg": round(sum(values) / len(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
            }

        weakest = min(domain_stats.items(), key=lambda x: x[1]["avg"])
        strongest = max(domain_stats.items(), key=lambda x: x[1]["avg"])

        # Correlation analysis
        # Sleep -> Energy correlation
        sleep_energy_corr = self._correlation(
            [s.sleep_quality for s in self._snapshots],
            [s.energy for s in self._snapshots]
        )

        # Movement -> Mood correlation
        movement_mood_corr = self._correlation(
            [s.movement_minutes for s in self._snapshots],
            [s.mood for s in self._snapshots]
        )

        # Nutrition -> Focus correlation
        nutrition_focus_corr = self._correlation(
            [s.nutrition_quality for s in self._snapshots],
            [s.focus_quality for s in self._snapshots]
        )

        # Stress -> Sleep correlation (negative)
        stress_sleep_corr = self._correlation(
            [s.stress for s in self._snapshots],
            [s.sleep_quality for s in self._snapshots]
        )

        # Vicious cycle detection
        recent = list(self._snapshots)[-7:]
        if recent:
            low_sleep = sum(1 for s in recent if s.sleep_quality < 0.4) / len(recent)
            low_energy = sum(1 for s in recent if s.energy < 0.4) / len(recent)
            high_stress = sum(1 for s in recent if s.stress > 0.7) / len(recent)
            vicious_cycle_risk = low_sleep > 0.4 and low_energy > 0.4 and high_stress > 0.4
        else:
            vicious_cycle_risk = False

        # Recent trend
        recent_avg = sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction for s in recent) / (len(recent) * 5)
        older = list(self._snapshots)[:-7] if len(self._snapshots) > 7 else []
        if older:
            older_avg = sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction for s in older) / (len(older) * 5)
            trend = recent_avg - older_avg
        else:
            trend = 0

        return {
            "total_snapshots": len(self._snapshots),
            "domain_stats": domain_stats,
            "weakest_domain": weakest[0],
            "strongest_domain": strongest[0],
            "correlations": {
                "sleep_energy": round(sleep_energy_corr, 2),
                "movement_mood": round(movement_mood_corr, 2),
                "nutrition_focus": round(nutrition_focus_corr, 2),
                "stress_sleep": round(stress_sleep_corr, 2),
            },
            "vicious_cycle_risk": vicious_cycle_risk,
            "trend": round(trend, 2),
            "avg_wellbeing": round(sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction for s in self._snapshots) / (len(self._snapshots) * 5), 2),
        }

    def get_health_priority(self, current_state: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Get priority."""
        if current_state is None:
            current_state = {}

        sleep = current_state.get("sleep", 0.5)
        nutrition = current_state.get("nutrition", 0.5)
        movement = current_state.get("movement", 0.5)
        mood = current_state.get("mood", 0.5)
        energy = current_state.get("energy", 0.5)
        stress = current_state.get("stress", 0.5)

        # Find the weakest domain that's also a leverage point
        domains = {
            "sleep": sleep,
            "nutrition": nutrition,
            "movement": movement,
            "mood": mood,
            "energy": energy,
        }

        # Priority logic: lowest score gets priority, but sleep is weighted higher
        weighted = {
            "sleep": sleep * 1.2,  # Sleep has outsized impact
            "nutrition": nutrition * 1.0,
            "movement": movement * 0.9,
            "mood": mood * 0.9,
            "energy": energy * 1.0,
        }

        priority_domain = min(weighted.items(), key=lambda x: x[1])[0]

        actions = {
            "sleep": [
                "Tonight: Set a bedtime alarm. Treat it like a meeting you can't miss.",
                "Create a 30-minute wind-down routine. Same time, every night.",
                "Eliminate screens 1 hour before bed. Read a paper book instead.",
            ],
            "nutrition": [
                "Next meal: Add one vegetable. Half plate rule.",
                "Drink a full glass of water before every meal.",
                "Eat without screens. Notice flavors, textures, fullness.",
            ],
            "movement": [
                "Take a 10-minute walk today. Fresh air + light movement.",
                "Do 5 minutes of stretching before bed. Release the day.",
                "Dance to one song. Joy is movement too.",
            ],
            "mood": [
                "Text one person you care about. Connection lifts mood.",
                "Write 3 things you're grateful for. Specific, not generic.",
                "Spend 10 minutes in nature. Green spaces reduce rumination.",
            ],
            "energy": [
                "Take a 20-minute nap. Not a weakness, a strategy.",
                "Eat a protein + complex carb snack. Sustained energy.",
                "Do 2 minutes of box breathing. Oxygen is energy.",
            ],
        }

        if stress > 0.7:
            stress_note = "High stress detected. This affects everything. Prioritize one stress-reduction practice today."
        else:
            stress_note = "Stress is manageable. Maintain your practices."

        return {
            "priority_domain": priority_domain,
            "current_scores": domains,
            "action": random.choice(actions.get(priority_domain, actions["sleep"])),
            "stress_note": stress_note,
            "principle": "Health is not the absence of illness. It's the presence of vitality in every domain. Focus on the weakest link first.",
        }

    def get_health_score(self) -> int:
        """Calculate overall holistic health (0-100)."""
        if not self._snapshots:
            return 30

        # Average across all domains
        avg_wellbeing = sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction + s.social_connection + s.focus_quality for s in self._snapshots) / (len(self._snapshots) * 7)

        # Balance (lowest domain pulls score down)
        domain_avgs = [
            sum(s.sleep_quality for s in self._snapshots) / len(self._snapshots),
            sum(s.nutrition_quality for s in self._snapshots) / len(self._snapshots),
            sum(s.movement_satisfaction for s in self._snapshots) / len(self._snapshots),
            sum(s.mood for s in self._snapshots) / len(self._snapshots),
            sum(s.energy for s in self._snapshots) / len(self._snapshots),
            sum(s.social_connection for s in self._snapshots) / len(self._snapshots),
            sum(s.focus_quality for s in self._snapshots) / len(self._snapshots),
        ]
        balance = min(domain_avgs)

        # Recent trend
        recent = list(self._snapshots)[-7:]
        if recent:
            recent_avg = sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction for s in recent) / (len(recent) * 5)
        else:
            recent_avg = 0

        # Vicious cycle penalty
        recent_low = [s for s in recent if s.sleep_quality < 0.4 and s.energy < 0.4 and s.stress > 0.7]
        cycle_penalty = min(15, len(recent_low) * 5)

        score = (avg_wellbeing * 40) + (balance * 30) + (recent_avg * 20) - cycle_penalty
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 3:
            return 0.0
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
        denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5
        
        if denom_x == 0 or denom_y == 0:
            return 0.0
        return numerator / (denom_x * denom_y)

    def _update_stats(self):
        """Update running statistics."""
        if self._snapshots:
            self._stats["avg_wellbeing"] = round(sum(s.mood + s.energy + s.sleep_quality + s.nutrition_quality + s.movement_satisfaction for s in self._snapshots) / (len(self._snapshots) * 5), 2)

            domains = {
                "sleep": sum(s.sleep_quality for s in self._snapshots) / len(self._snapshots),
                "nutrition": sum(s.nutrition_quality for s in self._snapshots) / len(self._snapshots),
                "movement": sum(s.movement_satisfaction for s in self._snapshots) / len(self._snapshots),
                "mood": sum(s.mood for s in self._snapshots) / len(self._snapshots),
                "energy": sum(s.energy for s in self._snapshots) / len(self._snapshots),
            }
            if domains:
                weakest = min(domains.items(), key=lambda x: x[1])
                strongest = max(domains.items(), key=lambda x: x[1])
                self._stats["weakest_domain"] = weakest[0]
                self._stats["strongest_domain"] = strongest[0]

            recent = [s for s in self._snapshots if s.timestamp > (datetime.now() - timedelta(days=7)).isoformat()]
            if recent:
                low_sleep = sum(1 for s in recent if s.sleep_quality < 0.4) / len(recent)
                low_energy = sum(1 for s in recent if s.energy < 0.4) / len(recent)
                high_stress = sum(1 for s in recent if s.stress > 0.7) / len(recent)
                self._stats["vicious_cycle_risk"] = low_sleep > 0.4 and low_energy > 0.4 and high_stress > 0.4

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.health_integrator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.health_integrator")

    def _log_snapshot(self, snapshot: WellbeingSnapshot):
        try:
            with open(WELLBEING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": snapshot.timestamp,
                    "sleep_hours": snapshot.sleep_hours,
                    "sleep_quality": snapshot.sleep_quality,
                    "nutrition": snapshot.nutrition_quality,
                    "movement_minutes": snapshot.movement_minutes,
                    "mood": snapshot.mood,
                    "energy": snapshot.energy,
                    "stress": snapshot.stress,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.health_integrator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hi_instance: Optional[HealthIntegrator] = None
_hi_lock = threading.Lock()


    
def get_health_integrator() -> HealthIntegrator:
    global _hi_instance
    with _hi_lock:
        if _hi_instance is None:
            _hi_instance = HealthIntegrator()
        return _hi_instance
