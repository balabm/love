"""
LOVE Preference Memory — Phase 5t of AGI Metamorphosis

LOVE doesn't just remember that Karthi likes code. LOVE remembers:
- Karthi likes his coffee black, no sugar
- Karthi prefers dark mode in everything
- Karthi hates notifications before 9 AM
- Karthi works best in 90-minute focused blocks
- Karthi prefers Python over JavaScript for backends
- Karthi gets annoyed by TTS after 10 PM

These are SPECIFIC, ACTIONABLE preferences that LOVE uses
to make better decisions every single time.

The preference memory:
1. Extracts preferences from every conversation
2. Assigns confidence scores based on repetition
3. Categorizes by domain (tech, lifestyle, communication, schedule)
4. Flags high-confidence preferences for automatic action
5. Tracks preference changes over time
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREFERENCE_DB_PATH = DATA_DIR / "preference_memory.json"
PREFERENCE_LOG_PATH = DATA_DIR / "preference_log.jsonl"


class PreferenceMemory:
    """
    LOVE's memory of Karthi's specific, actionable preferences.
    """

    # Preference categories
    CATEGORIES = {
        "tech": "Technology preferences (languages, tools, IDEs, themes)",
        "lifestyle": "Daily habits (food, sleep, exercise, environment)",
        "communication": "How Karthi wants to be spoken to (tone, timing, channel)",
        "schedule": "Work patterns (hours, breaks, focus blocks, deadlines)",
        "social": "People preferences (who to notify, group dynamics)",
        "aesthetic": "Visual/audio preferences (colors, fonts, sounds)",
        "privacy": "What Karthi wants kept private vs. shared",
    }

    def __init__(self):
        self._preferences: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in self.CATEGORIES}
        self._load()

    def _load(self):
        if PREFERENCE_DB_PATH.exists():
            try:
                with open(PREFERENCE_DB_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for cat in self.CATEGORIES:
                        if cat in loaded:
                            self._preferences[cat] = loaded[cat]
            except Exception:
                pass

    def _save(self):
        try:
            with open(PREFERENCE_DB_PATH, "w", encoding="utf-8") as f:
                json.dump(self._preferences, f, indent=2)
        except Exception as e:
            log_error(e, module="core.preference_memory", context={"phase": "save"})

    def _log(self, event: str, details: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), "event": event, **details}
            with open(PREFERENCE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════

    def extract_from_message(self, message: str) -> List[Dict[str, Any]]:
        """
        Extract preferences from a user message.
        Returns list of extracted preferences.
        """
        extracted = []
        lower_msg = message.lower()

        # Pattern 1: "I like/prefer/love/hate [X]"
        like_patterns = [
            (r"i (?:like|love|enjoy|prefer) ([^,.;!?]{3,80})", "positive"),
            (r"i (?:hate|dislike|can't stand|detest) ([^,.;!?]{3,80})", "negative"),
            (r"i (?:don't like|don't want|don't need) ([^,.;!?]{3,80})", "negative"),
            (r"i (?:always|usually) ([^,.;!?]{3,80})", "habit"),
            (r"i (?:never|rarely) ([^,.;!?]{3,80})", "avoidance"),
            (r"my favorite [\w ]+ is ([^,.;!?]{3,80})", "positive"),
            (r"i wish ([^,.;!?]{3,80})", "desire"),
        ]

        for pattern, sentiment in like_patterns:
            matches = re.findall(pattern, lower_msg)
            for match in matches:
                pref_text = match.strip()
                if len(pref_text) < 3:
                    continue

                category = self._categorize_preference(pref_text)
                extracted.append({
                    "text": pref_text,
                    "sentiment": sentiment,
                    "category": category,
                    "source": message[:200],
                })

        # Pattern 2: "Don't [do X]" or "Stop [doing X]"
        stop_patterns = re.findall(r"(?:don't|stop|quit|avoid) ([^,.;!?]{3,80})", lower_msg)
        for match in stop_patterns:
            pref_text = match.strip()
            category = self._categorize_preference(pref_text)
            extracted.append({
                "text": pref_text,
                "sentiment": "negative",
                "category": category,
                "source": message[:200],
            })

        # Store all extracted
        for pref in extracted:
            self._store_preference(pref)

        return extracted

    def _categorize_preference(self, text: str) -> str:
        """Categorize a preference text into a domain."""
        text_lower = text.lower()

        category_keywords = {
            "tech": {"python", "javascript", "code", "ide", "editor", "theme", "dark mode",
                     "light mode", "font", "terminal", "api", "framework", "library"},
            "lifestyle": {"coffee", "tea", "food", "sleep", "bed", "exercise", "gym",
                        "walk", "music", "podcast", "temperature", "light"},
            "communication": {"tts", "voice", "speak", "notify", "notification", "push",
                            "alert", "quiet", "loud", "message", "email", "text"},
            "schedule": {"morning", "evening", "night", "hour", "break", "focus",
                       "deadline", "schedule", "plan", "routine", "block", "session"},
            "social": {"friend", "family", "team", "colleague", "group", "meet",
                     "call", "video", "chat"},
            "aesthetic": {"color", "dark", "light", "theme", "font", "size", "sound",
                        "music", "quiet", "minimal", "clutter"},
            "privacy": {"private", "secret", "don't share", "confidential", "personal",
                      "hide", "nobody", "only me"},
        }

        best_category = "general"
        best_score = 0
        for cat, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_category = cat

        return best_category

    def _store_preference(self, pref: Dict[str, Any]):
        """Store a preference, updating confidence if it already exists."""
        category = pref["category"]
        text = pref["text"]

        # Check if similar preference already exists
        for existing in self._preferences.get(category, []):
            if self._is_similar(existing["text"], text):
                existing["mentions"] = existing.get("mentions", 1) + 1
                existing["last_mentioned"] = datetime.now().isoformat()
                existing["confidence"] = min(1.0, existing["mentions"] * 0.2 + 0.3)
                self._save()
                self._log("updated", {"text": text, "category": category, "confidence": existing["confidence"]})
                return

        # New preference
        new_pref = {
            "text": text,
            "sentiment": pref.get("sentiment", "neutral"),
            "mentions": 1,
            "confidence": 0.3,
            "first_mentioned": datetime.now().isoformat(),
            "last_mentioned": datetime.now().isoformat(),
            "source": pref.get("source", ""),
            "auto_apply": False,
        }
        self._preferences.setdefault(category, []).append(new_pref)
        self._save()
        self._log("added", {"text": text, "category": category})

    def _is_similar(self, a: str, b: str) -> bool:
        """Check if two preference texts are similar."""
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return False
        overlap = len(a_words & b_words)
        return overlap / max(len(a_words), len(b_words)) > 0.6

    # ═══════════════════════════════════════════════════════════════════════
    # QUERYING
    # ═══════════════════════════════════════════════════════════════════════

    def get_preferences(self, category: Optional[str] = None,
                        min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Get preferences, optionally filtered by category and confidence."""
        results = []
        categories = [category] if category else list(self.CATEGORIES.keys())
        for cat in categories:
            for pref in self._preferences.get(cat, []):
                if pref.get("confidence", 0) >= min_confidence:
                    results.append({**pref, "category": cat})
        return sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)

    def get_context_for_prompt(self) -> str:
        """Generate preference context for Neural Cortex prompt injection."""
        high_conf = self.get_preferences(min_confidence=0.7)
        if not high_conf:
            return ""

        lines = ["\n=== WHAT I KNOW ABOUT KARTHI'S PREFERENCES ==="]

        # Group by category
        by_category: Dict[str, List[str]] = {}
        for pref in high_conf[:15]:  # Top 15
            cat = pref.get("category", "general")
            text = pref["text"]
            sentiment = pref.get("sentiment", "neutral")
            mentions = pref.get("mentions", 1)

            marker = {"positive": "likes", "negative": "dislikes", "habit": "usually",
                     "avoidance": "avoids", "desire": "wants"}.get(sentiment, "prefers")

            entry = f"  - Karthi {marker}: {text}"
            if mentions > 1:
                entry += f" (mentioned {mentions} times)"
            by_category.setdefault(cat, []).append(entry)

        for cat, entries in by_category.items():
            cat_name = self.CATEGORIES.get(cat, cat)
            lines.append(f"\n{cat_name}:")
            lines.extend(entries[:5])

        lines.append("\n=== END PREFERENCES ===\n")
        return "\n".join(lines)

    def should_auto_apply(self, action_type: str) -> Optional[str]:
        """
        Check if there's a high-confidence preference that should auto-apply.
        Returns the preference text if one matches, None otherwise.
        """
        action_lower = action_type.lower()
        for cat, prefs in self._preferences.items():
            for pref in prefs:
                if pref.get("confidence", 0) >= 0.8 and pref.get("auto_apply", False):
                    pref_text = pref["text"].lower()
                    # Check if action matches preference domain
                    if any(word in action_lower for word in pref_text.split()[:3]):
                        return pref["text"]
        return None

    def set_auto_apply(self, preference_text: str, auto_apply: bool = True):
        """Mark a preference for automatic application."""
        for cat, prefs in self._preferences.items():
            for pref in prefs:
                if pref["text"] == preference_text:
                    pref["auto_apply"] = auto_apply
                    self._save()
                    return

    def get_status(self) -> Dict[str, Any]:
        total = sum(len(prefs) for prefs in self._preferences.values())
        high_conf = len(self.get_preferences(min_confidence=0.7))
        return {
            "total_preferences": total,
            "high_confidence": high_conf,
            "categories_with_prefs": sum(1 for cat, prefs in self._preferences.items() if prefs),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_preference_memory: Optional[PreferenceMemory] = None


def get_preference_memory() -> PreferenceMemory:
    global _preference_memory
    if _preference_memory is None:
        _preference_memory = PreferenceMemory()
    return _preference_memory
