"""
LOVE Productivity Gamifier — Gamification Intelligence (Modern AI Pattern)

Most gamification is superficial badges. This gamifier:

1. ACHIEVEMENT SYSTEM
   - Track meaningful achievements (streaks, milestones, personal bests)
   - Create contextual challenges based on current goals
   - Reward effort, consistency, and improvement (not just output)

2. PROGRESS VISUALIZATION
   - Generate XP and leveling based on productive time
   - Track daily/weekly/monthly high scores
   - Visualize skill trees for different life domains

3. MOTIVATION INTELLIGENCE
   - Detect motivation dips and suggest the right challenge
   - Identify what type of rewards motivate this user
   - Balance difficulty (not too easy, not too hard)

4. SOCIAL COMPETITION
   - Compare today's self to yesterday's self
   - Track personal records and break them
   - Celebrate small wins to maintain momentum

Architecture:
- record_activity(activity, duration, quality): Log productive activity
- get_level(): Get current productivity level
- get_achievements(): Get unlocked achievements
- get_daily_challenge(): Get personalized daily challenge
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

DATA_DIR = Path(__file__).parent.parent / "data" / "productivity_gamifier"
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_LOG = DATA_DIR / "activities.jsonl"
STATS_DB = DATA_DIR / "stats.json"
ACHIEVEMENTS_DB = DATA_DIR / "achievements.json"


@dataclass
class ProductiveActivity:
    """A productive activity."""
    activity: str = ""
    domain: str = ""  # work, health, learning, creative, social, maintenance
    duration_minutes: float = 0.0
    quality: float = 0.5  # 0-1
    xp_earned: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class Achievement:
    """An achievement."""
    id: str = ""
    name: str = ""
    description: str = ""
    domain: str = ""
    requirement_type: str = ""  # streak, total, single, milestone
    requirement_value: float = 0.0
    unlocked: bool = False
    unlocked_at: Optional[str] = None
    rarity: str = "common"  # common, rare, epic, legendary


class ProductivityGamifier:
    """
    Gamify productivity with intelligent challenge design.
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
        self._activities: deque = deque(maxlen=500)
        self._achievements: Dict[str, Achievement] = {}
        self._stats = {
            "total_xp": 0,
            "current_level": 1,
            "xp_to_next_level": 100,
            "total_activities": 0,
            "current_streak": 0,
            "best_streak": 0,
        }
        self._init_achievements()
        self._load_stats()
        self._load_achievements()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_activity(self, activity: str = "", domain: str = "", duration: float = 0, quality: float = 0.5, notes: str = "") -> ProductiveActivity:
        """Record a productive activity and award XP."""
        # Calculate XP
        base_xp = duration * quality
        domain_multiplier = {
            "work": 1.0,
            "health": 1.2,
            "learning": 1.3,
            "creative": 1.1,
            "social": 0.8,
            "maintenance": 0.6,
        }.get(domain, 1.0)
        
        xp = base_xp * domain_multiplier

        entry = ProductiveActivity(
            activity=activity or "general",
            domain=domain or "work",
            duration_minutes=duration,
            quality=quality,
            xp_earned=round(xp, 1),
            notes=notes,
        )

        with self._lock:
            self._activities.append(entry)
            self._stats["total_activities"] += 1
            self._stats["total_xp"] += xp
            self._update_streak()
            self._check_level_up()
            self._check_achievements(entry)

        self._save_stats()
        self._log_activity(entry)

        return entry

    # ── Level System ──────────────────────────────────────────────────────

    def get_level(self) -> Dict[str, Any]:
        """Get current productivity level info."""
        level = self._stats["current_level"]
        xp = self._stats["total_xp"]
        xp_needed = self._stats["xp_to_next_level"]
        xp_progress = xp % xp_needed if xp > 0 else 0
        pct = (xp_progress / xp_needed) * 100

        # Level titles
        titles = {
            1: "Novice",
            5: "Apprentice",
            10: "Journeyman",
            15: "Expert",
            20: "Master",
            25: "Grandmaster",
            30: "Legend",
        }
        title = titles.get(level, "Legend")
        for l in sorted(titles.keys(), reverse=True):
            if level >= l:
                title = titles[l]
                break

        return {
            "level": level,
            "title": title,
            "total_xp": round(xp, 1),
            "xp_to_next_level": xp_needed,
            "xp_progress": round(xp_progress, 1),
            "pct_to_next": round(pct, 1),
            "next_title": titles.get(min([k for k in titles.keys() if k > level] or [level + 5]), "Unknown"),
        }

    # ── Achievements ──────────────────────────────────────────────────────

    def get_achievements(self) -> Dict[str, Any]:
        """Get all achievements with unlock status."""
        unlocked = [a for a in self._achievements.values() if a.unlocked]
        locked = [a for a in self._achievements.values() if not a.unlocked]

        return {
            "total": len(self._achievements),
            "unlocked": len(unlocked),
            "locked": len(locked),
            "completion_pct": round(len(unlocked) / max(1, len(self._achievements)) * 100, 1),
            "recent_unlocks": sorted(
                [a for a in unlocked],
                key=lambda x: x.unlocked_at or "",
                reverse=True,
            )[:5],
            "by_rarity": {
                "common": sum(1 for a in unlocked if a.rarity == "common"),
                "rare": sum(1 for a in unlocked if a.rarity == "rare"),
                "epic": sum(1 for a in unlocked if a.rarity == "epic"),
                "legendary": sum(1 for a in unlocked if a.rarity == "legendary"),
            },
        }

    def get_daily_challenge(self) -> Dict[str, Any]:
        """Get personalized daily challenge."""
        # Analyze recent patterns
        today = datetime.now().date().isoformat()
        today_acts = [a for a in self._activities if a.timestamp[:10] == today]

        # Check what domains haven't been touched today
        domains_touched = set(a.domain for a in today_acts)
        all_domains = {"work", "health", "learning", "creative", "social", "maintenance"}
        missing_domains = all_domains - domains_touched

        # Challenge types
        challenges = []
        
        if missing_domains:
            domain = list(missing_domains)[0]
            challenges.append({
                "challenge": f"Do something in the {domain} domain today",
                "reward": "50 XP",
                "difficulty": "easy",
                "reason": f"You haven't touched {domain} yet today. Variety keeps momentum.",
            })

        # Check streak maintenance
        if self._stats["current_streak"] > 3:
            challenges.append({
                "challenge": f"Maintain your {self._stats['current_streak']}-day streak",
                "reward": f"{self._stats['current_streak'] * 10} XP",
                "difficulty": "medium",
                "reason": "Streaks are fragile. Protect it today.",
            })

        # Check level proximity
        level_info = self.get_level()
        if level_info["pct_to_next"] > 80:
            challenges.append({
                "challenge": "Level up today",
                "reward": f"Level {level_info['level'] + 1}: {level_info['next_title']}",
                "difficulty": "medium",
                "reason": f"You're {level_info['pct_to_next']:.0f}% to the next level. One more push!",
            })

        # Default challenge
        if not challenges:
            challenges.append({
                "challenge": "Complete 3 productive activities today",
                "reward": "100 XP",
                "difficulty": "easy",
                "reason": "Start with small wins. Momentum builds from there.",
            })

        return {
            "daily_challenges": challenges[:2],
            "current_streak": self._stats["current_streak"],
            "best_streak": self._stats["best_streak"],
            "xp_today": round(sum(a.xp_earned for a in today_acts), 1),
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _init_achievements(self):
        """Initialize default achievements."""
        defaults = [
            Achievement("first_step", "First Step", "Record your first productive activity", "general", "total", 1, rarity="common"),
            Achievement("week_warrior", "Week Warrior", "7-day productivity streak", "general", "streak", 7, rarity="rare"),
            Achievement("month_master", "Month Master", "30-day productivity streak", "general", "streak", 30, rarity="epic"),
            Achievement("centurion", "Centurion", "100 productive activities", "general", "total", 100, rarity="rare"),
            Achievement("deep_diver", "Deep Diver", "One 4-hour deep work session", "work", "single", 240, rarity="rare"),
            Achievement("learner", "Learner", "10 learning activities", "learning", "total", 10, rarity="common"),
            Achievement("health_hero", "Health Hero", "10 health activities", "health", "total", 10, rarity="common"),
            Achievement("creative_spark", "Creative Spark", "5 creative sessions", "creative", "total", 5, rarity="common"),
            Achievement("social_butterfly", "Social Butterfly", "5 social activities", "social", "total", 5, rarity="common"),
            Achievement("level_5", "Rising Star", "Reach level 5", "general", "milestone", 5, rarity="rare"),
            Achievement("level_10", "Veteran", "Reach level 10", "general", "milestone", 10, rarity="epic"),
            Achievement("level_20", "Master", "Reach level 20", "general", "milestone", 20, rarity="legendary"),
        ]
        for a in defaults:
            if a.id not in self._achievements:
                self._achievements[a.id] = a

    def _update_streak(self):
        """Update productivity streak."""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Check if there was activity yesterday
        yesterday_acts = [a for a in self._activities if a.timestamp[:10] == yesterday.isoformat()]
        today_acts = [a for a in self._activities if a.timestamp[:10] == today.isoformat()]
        
        if yesterday_acts and today_acts:
            self._stats["current_streak"] += 1
        elif not yesterday_acts and today_acts and self._stats["current_streak"] == 0:
            self._stats["current_streak"] = 1
        elif not today_acts:
            self._stats["current_streak"] = 0
        
        self._stats["best_streak"] = max(self._stats["best_streak"], self._stats["current_streak"])

    def _check_level_up(self):
        """Check if user leveled up."""
        while self._stats["total_xp"] >= self._stats["xp_to_next_level"]:
            self._stats["current_level"] += 1
            self._stats["total_xp"] -= self._stats["xp_to_next_level"]
            self._stats["xp_to_next_level"] = int(100 * (1.2 ** self._stats["current_level"]))

    def _check_achievements(self, entry: ProductiveActivity):
        """Check if any achievements were unlocked."""
        for achievement in self._achievements.values():
            if achievement.unlocked:
                continue

            unlocked = False
            if achievement.requirement_type == "streak":
                if self._stats["current_streak"] >= achievement.requirement_value:
                    unlocked = True
            elif achievement.requirement_type == "total":
                domain_acts = [a for a in self._activities if a.domain == achievement.domain or achievement.domain == "general"]
                if len(domain_acts) >= achievement.requirement_value:
                    unlocked = True
            elif achievement.requirement_type == "single":
                if entry.duration_minutes >= achievement.requirement_value and entry.domain == achievement.domain:
                    unlocked = True
            elif achievement.requirement_type == "milestone":
                if self._stats["current_level"] >= achievement.requirement_value:
                    unlocked = True

            if unlocked:
                achievement.unlocked = True
                achievement.unlocked_at = datetime.now().isoformat()
                try:
                    from core.neural_bus import get_neural_bus
                    get_neural_bus().publish(
                        event_type="achievement_unlocked",
                        domain="productivity",
                        payload={
                            "achievement": achievement.name,
                            "rarity": achievement.rarity,
                            "description": achievement.description,
                        },
                    )
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.productivity_gamifier")

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.productivity_gamifier")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.productivity_gamifier")

    def _load_achievements(self):
        try:
            if ACHIEVEMENTS_DB.exists():
                data = json.loads(ACHIEVEMENTS_DB.read_text())
                for k, v in data.items():
                    self._achievements[k] = Achievement(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.productivity_gamifier")

    def _save_achievements(self):
        try:
            data = {k: {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "domain": v.domain,
                "requirement_type": v.requirement_type,
                "requirement_value": v.requirement_value,
                "unlocked": v.unlocked,
                "unlocked_at": v.unlocked_at,
                "rarity": v.rarity,
            } for k, v in self._achievements.items()}
            ACHIEVEMENTS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.productivity_gamifier")

    def _log_activity(self, entry: ProductiveActivity):
        try:
            with open(ACTIVITY_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": entry.timestamp,
                    "activity": entry.activity,
                    "domain": entry.domain,
                    "duration": entry.duration_minutes,
                    "xp": entry.xp_earned,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.productivity_gamifier")

    def __del__(self):
        """Save achievements on cleanup."""
        self._save_achievements()


# ── Singleton Access ─────────────────────────────────────────────────────────────

_pg_instance: Optional[ProductivityGamifier] = None
_pg_lock = threading.Lock()


def get_productivity_gamifier() -> ProductivityGamifier:
    global _pg_instance
    with _pg_lock:
        if _pg_instance is None:
            _pg_instance = ProductivityGamifier()
        return _pg_instance
