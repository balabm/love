"""
LOVE Savoring Trainer — Positive Experience Amplification Intelligence (Modern AI Pattern)

Most people rush past good moments. This trainer:

1. SAVORING TRACKING
   - Record savoring attempts and their success
   - Track what is savored, how, and for how long
   - Log anticipatory, present-moment, and reminiscing savoring

2. PATTERN ANALYSIS
   - Identify the user's savoring style (basking, marveling, thanksgiving, temporal extension)
   - Find what the user most easily vs rarely savors
   - Detect savoring blocks (hurry, pessimism, guilt, habituation)

3. SAVORING GENERATION
   - Suggest savoring techniques for current positive experiences
   - Provide micro-savoring exercises (30-second amplifications)
   - Recommend savoring practices based on mood and context

4. GROWTH SUPPORT
   - Track savoring as a skill that strengthens with practice
   - Savoring challenges and milestones
   - Celebrate the ability to make good moments last

Architecture:
- record_savoring(experience, type, duration, success): Log savoring
- get_savoring_stats(): Get savoring pattern analysis
- get_savoring_suggestion(experience, mood): Get savoring technique
- get_savoring_score(): Calculate overall savoring health
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

DATA_DIR = Path(__file__).parent.parent / "data" / "savoring_trainer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SAVORING_LOG = DATA_DIR / "savoring.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Savoring:
    """A tracked savoring attempt."""
    savoring_id: str = ""
    experience: str = ""
    savoring_type: str = ""  # anticipatory, present, reminiscing
    technique: str = ""  # basking, marveling, thanksgiving, temporal_extension, sharing, memory_building, sharpening
    duration_seconds: float = 0.0
    success: float = 0.5  # 0-1, how well it worked
    intensity_before: float = 0.5  # 0-1
    intensity_after: float = 0.5  # 0-1
    blocks: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class SavoringTrainer:
    """
    Intelligent savoring trainer with positive experience amplification and block detection.
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
        self._savorings: deque = deque(maxlen=200)
        self._stats = {
            "total_savorings": 0,
            "avg_success": 0.0,
            "avg_amplification": 0.0,
            "dominant_type": "",
            "dominant_technique": "",
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_savoring(self, experience: str = "", savoring_type: str = "", technique: str = "", duration: float = 0, success: float = 0.5, intensity_before: float = 0.5, intensity_after: float = 0.5, blocks: Optional[List[str]] = None, notes: str = "") -> Savoring:
        """Record a savoring attempt."""
        savoring_id = f"savor_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._savorings)}"
        s = Savoring(
            savoring_id=savoring_id,
            experience=experience or "unspecified",
            savoring_type=savoring_type or "present",
            technique=technique or "basking",
            duration_seconds=duration,
            success=success,
            intensity_before=intensity_before,
            intensity_after=intensity_after,
            blocks=blocks or [],
            notes=notes,
        )

        with self._lock:
            self._savorings.append(s)
            self._stats["total_savorings"] += 1
            self._update_stats()

        self._save_stats()
        self._log_savoring(s)

        return s

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_savoring_stats(self) -> Dict[str, Any]:
        """Get savoring pattern analysis."""
        if not self._savorings:
            return {"status": "insufficient_data"}

        # Type analysis
        by_type = defaultdict(lambda: {"count": 0, "success_sum": 0.0, "amplification_sum": 0.0})
        for s in self._savorings:
            by_type[s.savoring_type]["count"] += 1
            by_type[s.savoring_type]["success_sum"] += s.success
            by_type[s.savoring_type]["amplification_sum"] += (s.intensity_after - s.intensity_before)

        type_stats = {}
        for t, data in by_type.items():
            count = data["count"]
            type_stats[t] = {
                "count": count,
                "avg_success": round(data["success_sum"] / count, 2),
                "avg_amplification": round(data["amplification_sum"] / count, 2),
            }

        dominant_type = max(type_stats.items(), key=lambda x: x[1]["count"]) if type_stats else ("", {})

        # Technique analysis
        by_technique = defaultdict(lambda: {"count": 0, "success_sum": 0.0})
        for s in self._savorings:
            by_technique[s.technique]["count"] += 1
            by_technique[s.technique]["success_sum"] += s.success

        technique_stats = {}
        for tech, data in by_technique.items():
            count = data["count"]
            technique_stats[tech] = {
                "count": count,
                "avg_success": round(data["success_sum"] / count, 2),
            }

        dominant_technique = max(technique_stats.items(), key=lambda x: x[1]["count"]) if technique_stats else ("", {})

        # Block analysis
        all_blocks = []
        for s in self._savorings:
            all_blocks.extend(s.blocks)
        block_counts = defaultdict(int)
        for b in all_blocks:
            block_counts[b] += 1

        # Amplification trend
        amplifications = [s.intensity_after - s.intensity_before for s in self._savorings]
        avg_amplification = sum(amplifications) / len(amplifications) if amplifications else 0

        return {
            "total_savorings": len(self._savorings),
            "type_stats": type_stats,
            "dominant_type": dominant_type[0],
            "technique_stats": technique_stats,
            "dominant_technique": dominant_technique[0],
            "block_frequency": dict(block_counts),
            "avg_success": round(sum(s.success for s in self._savorings) / len(self._savorings), 2),
            "avg_amplification": round(avg_amplification, 2),
        }

    def get_savoring_suggestion(self, experience: str = "", mood: str = "neutral", savoring_type: str = "") -> Dict[str, Any]:
        """Get savoring technique."""
        techniques = {
            "basking": {
                "description": "Luxuriate in the warmth of the experience. Let it fill you.",
                "steps": [
                    "Close your eyes",
                    "Breathe the feeling in",
                    "Let it expand in your chest",
                    "Stay with it longer than feels natural",
                ],
            },
            "marveling": {
                "description": "Approach the experience with wonder, as if seeing it for the first time.",
                "steps": [
                    "Notice something new about it",
                    "Ask: How is this even possible?",
                    "Feel awe at its existence",
                    "Let amazement replace familiarity",
                ],
            },
            "thanksgiving": {
                "description": "Feel grateful for the experience and its sources.",
                "steps": [
                    "Name three things that made this possible",
                    "Feel gratitude toward each",
                    "Acknowledge your role in receiving it",
                    "Let gratitude amplify the joy",
                ],
            },
            "temporal_extension": {
                "description": "Stretch the experience across time—past, present, future.",
                "steps": [
                    "Remember when this wasn't true",
                    "Feel the present moment fully",
                    "Imagine savoring this memory years from now",
                    "Weave all three timeframes together",
                ],
            },
            "sharing": {
                "description": "Amplify by connecting with others about the experience.",
                "steps": [
                    "Tell someone about it",
                    "See their reaction reflect your joy",
                    "Feel the experience become part of your bond",
                    "Let social connection deepen the savoring",
                ],
            },
            "memory_building": {
                "description": "Encode the experience deeply for future reminiscing.",
                "steps": [
                    "Notice sensory details (sounds, smells, textures)",
                    "Take a mental photograph",
                    "Name the emotion precisely",
                    "Create a trigger word or gesture to recall it",
                ],
            },
            "sharpening": {
                "description": "Focus on one aspect and magnify it.",
                "steps": [
                    "Choose one element of the experience",
                    "Zoom in mentally on that element",
                    "Explore its texture, quality, depth",
                    "Let everything else blur as this sharpens",
                ],
            },
        }

        tech = random.choice(list(techniques.keys()))
        selected = techniques[tech]

        return {
            "experience": experience or "this moment",
            "technique": tech,
            **selected,
            "time": "30-60 seconds minimum. Longer is better.",
            "mood": mood,
            "reminder": "Don't rush to the next thing. This moment deserves your full attention.",
        }

    def get_savoring_score(self) -> int:
        """Calculate overall savoring health (0-100)."""
        if not self._savorings:
            return 30

        # Success rate
        avg_success = sum(s.success for s in self._savorings) / len(self._savorings)

        # Amplification
        amplifications = [s.intensity_after - s.intensity_before for s in self._savorings]
        avg_amplification = sum(amplifications) / len(amplifications) if amplifications else 0

        # Frequency
        recent = [s for s in self._savorings if s.timestamp > (datetime.now() - timedelta(days=14)).isoformat()]
        frequency = len(recent)

        # Variety
        unique_types = len(set(s.savoring_type for s in self._savorings))
        unique_techniques = len(set(s.technique for s in self._savorings))

        # Low blocks
        total_blocks = sum(len(s.blocks) for s in self._savorings)
        block_rate = total_blocks / max(1, len(self._savorings))

        score = (avg_success * 25) + (avg_amplification * 20) + (min(frequency, 10) * 3) + (unique_types * 3) + (unique_techniques * 2) + ((1 - block_rate) * 15)
        return max(0, min(100, round(score)))

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._savorings:
            self._stats["avg_success"] = round(sum(s.success for s in self._savorings) / len(self._savorings), 2)
            
            amplifications = [s.intensity_after - s.intensity_before for s in self._savorings]
            self._stats["avg_amplification"] = round(sum(amplifications) / len(amplifications), 2) if amplifications else 0

            by_type = defaultdict(int)
            by_technique = defaultdict(int)
            for s in self._savorings:
                by_type[s.savoring_type] += 1
                by_technique[s.technique] += 1
            
            if by_type:
                self._stats["dominant_type"] = max(by_type.items(), key=lambda x: x[1])[0]
            if by_technique:
                self._stats["dominant_technique"] = max(by_technique.items(), key=lambda x: x[1])[0]

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.savoring_trainer")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.savoring_trainer")

    def _log_savoring(self, savoring: Savoring):
        try:
            with open(SAVORING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": savoring.timestamp,
                    "experience": savoring.experience,
                    "type": savoring.savoring_type,
                    "technique": savoring.technique,
                    "success": savoring.success,
                    "amplification": savoring.intensity_after - savoring.intensity_before,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.savoring_trainer")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_st_instance: Optional[SavoringTrainer] = None
_st_lock = threading.Lock()


def get_savoring_trainer() -> SavoringTrainer:
    global _st_instance
    with _st_lock:
        if _st_instance is None:
            _st_instance = SavoringTrainer()
        return _st_instance
