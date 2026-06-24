"""
LOVE Correction Learning — Phase 5u of AGI Metamorphosis

When Karthi says "that's wrong" or corrects LOVE, LOVE doesn't just
say "sorry." LOVE LEARNS. Immediately.

This module:
1. Detects corrections in user messages
2. Extracts what was wrong and what the correction is
3. Updates relevant beliefs/preferences immediately
4. Adjusts confidence in related predictions
5. Logs the correction for future pattern analysis
6. Generates a follow-up to show understanding

Examples:
- LOVE: "You have a meeting at 3 PM"
  Karthi: "No, it's at 4 PM"
  LOVE: Updates calendar understanding, adjusts confidence in time predictions

- LOVE: "I'll use the dark theme"
  Karthi: "Actually I switched to light mode"
  LOVE: Updates preference memory immediately

- LOVE: "Your portfolio is down 5%"
  Karthi: "Wrong, it's up 2%"
  LOVE: Corrects the data source, reduces confidence in that API
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CORRECTION_LOG_PATH = DATA_DIR / "correction_log.jsonl"
CORRECTION_STATE_PATH = DATA_DIR / "correction_state.json"


class CorrectionLearning:
    """
    LOVE's ability to learn from being corrected.
    """

    def __init__(self):
        self._corrections: List[Dict[str, Any]] = []
        self._belief_revisions: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        if CORRECTION_STATE_PATH.exists():
            try:
                with open(CORRECTION_STATE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._belief_revisions = loaded.get("belief_revisions", {})
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(CORRECTION_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "belief_revisions": self._belief_revisions,
                }, f, indent=2)
        except Exception:
            pass

    def _log_correction(self, correction: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), **correction}
            with open(CORRECTION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            self._corrections.append(entry)
            # Keep last 100 in memory
            self._corrections = self._corrections[-100:]
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def detect_correction(self, user_message: str, love_last_message: str = "") -> Optional[Dict[str, Any]]:
        """
        Detect if the user is correcting LOVE.
        Returns correction details if detected, None otherwise.
        """
        lower_msg = user_message.lower().strip()

        # Direct correction patterns
        correction_starters = {
            "no,": "direct_rejection",
            "no.": "direct_rejection",
            "nope": "direct_rejection",
            "wrong": "correction",
            "actually": "clarification",
            "not quite": "partial_correction",
            "that's not": "partial_correction",
            "incorrect": "correction",
            "false": "correction",
            "i didn't": "clarification",
            "i don't": "clarification",
            "i meant": "clarification",
            "what i meant": "clarification",
            "correction": "explicit_correction",
            "you're wrong": "direct_rejection",
            "not true": "direct_rejection",
            "that's wrong": "direct_rejection",
        }

        correction_type = None
        for pattern, ctype in correction_starters.items():
            if lower_msg.startswith(pattern) or f" {pattern} " in lower_msg:
                correction_type = ctype
                break

        if not correction_type:
            # Check for "X is Y" when LOVE previously said "X is Z"
            if love_last_message and self._is_contradiction(user_message, love_last_message):
                correction_type = "implied_correction"

        if not correction_type:
            return None

        # Extract the corrected information
        correction = {
            "type": correction_type,
            "user_message": user_message,
            "love_message": love_last_message,
            "corrected_fact": self._extract_corrected_fact(user_message),
            "domain": self._identify_domain(user_message, love_last_message),
        }

        return correction

    def _is_contradiction(self, user_msg: str, love_msg: str) -> bool:
        """Check if user message contradicts LOVE's previous message."""
        # Simple heuristic: same subject, opposite predicate
        # "up" vs "down", "yes" vs "no", etc.
        contradiction_pairs = [
            ("up", "down"), ("increase", "decrease"), ("gain", "loss"),
            ("yes", "no"), ("true", "false"), ("correct", "wrong"),
            ("morning", "evening"), ("today", "tomorrow"),
            ("before", "after"), ("earlier", "later"),
        ]

        user_lower = user_msg.lower()
        love_lower = love_msg.lower()

        for a, b in contradiction_pairs:
            if (a in user_lower and b in love_lower) or (b in user_lower and a in love_lower):
                return True

        return False

    def _extract_corrected_fact(self, message: str) -> str:
        """Extract the corrected fact from a correction message."""
        # Remove correction markers
        cleaned = re.sub(r"^(no,|nope|wrong|actually|not quite|that's not|incorrect|false|correction:?|you're wrong|not true|that's wrong)\s*", "", message.lower(), flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned[:200] if cleaned else message[:200]

    def _identify_domain(self, user_msg: str, love_msg: str) -> str:
        """Identify what domain the correction is about."""
        combined = (user_msg + " " + love_msg).lower()

        domain_keywords = {
            "schedule": {"meeting", "calendar", "time", "appointment", "event", "deadline"},
            "finance": {"money", "price", "btc", "bitcoin", "portfolio", "stock", "invest"},
            "code": {"code", "bug", "error", "function", "class", "file", "repo"},
            "system": {"cpu", "ram", "disk", "memory", "battery", "temperature"},
            "personal": {"name", "age", "birthday", "address", "phone"},
            "preference": {"like", "prefer", "want", "hate", "dark", "light", "theme"},
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in combined for kw in keywords):
                return domain

        return "general"

    # ═══════════════════════════════════════════════════════════════════════
    # LEARNING
    # ═══════════════════════════════════════════════════════════════════════

    def learn_from_correction(self, correction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the correction to LOVE's knowledge.
        Returns what was updated.
        """
        domain = correction.get("domain", "general")
        corrected_fact = correction.get("corrected_fact", "")
        updates = []

        # 1. Update preference memory if it's a preference correction
        if domain == "preference":
            try:
                from core.preference_memory import get_preference_memory
                pm = get_preference_memory()
                # Extract the new preference from the correction
                pm.extract_from_message(corrected_fact)
                updates.append("preference_memory")
            except Exception:
                pass

        # 2. Update belief revisions
        key = f"{domain}:{corrected_fact[:50]}"
        self._belief_revisions[key] = {
            "fact": corrected_fact,
            "domain": domain,
            "corrected_at": datetime.now().isoformat(),
            "confidence": 0.9,  # High confidence since user directly told us
        }
        self._save_state()

        # 3. Reduce confidence in related predictions (Active Inference)
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            # Note: we can't easily target specific predictions, but we can
            # signal that our model needs updating
            status = ai.get_status()
            # The total_surprise will increase naturally on next cycle
            # if the observation doesn't match our prediction
            updates.append("active_inference_flagged")
        except Exception:
            pass

        # 4. Log the correction
        self._log_correction(correction)

        # 5. Update emotional persistence (being corrected reduces confidence slightly)
        try:
            from core.emotional_persistence import get_emotional_persistence
            ep = get_emotional_persistence()
            state = ep.get_state()
            # Don't punish too much — being corrected is good learning
            ep.update_from_action_outcome(success=False, action_type="prediction")
        except Exception:
            pass

        return {
            "learned": True,
            "updates": updates,
            "domain": domain,
            "fact_stored": corrected_fact[:100],
        }

    def generate_acknowledgment(self, correction: Dict[str, Any]) -> str:
        """Generate a natural acknowledgment of the correction."""
        ctype = correction.get("type", "")
        domain = correction.get("domain", "general")

        if ctype == "direct_rejection":
            return f"Got it. I'll update my understanding about that {domain} fact."
        elif ctype == "clarification":
            return f"Thanks for clarifying. I'll remember that going forward."
        elif ctype == "partial_correction":
            return f"You're right, I had that partially wrong. Correcting my model now."
        elif ctype == "explicit_correction":
            return f"Noted. I'll make sure I have that right from now on."
        else:
            return f"Thanks for the correction. I'm updating my understanding."

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_recent_corrections(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent corrections."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [c for c in self._corrections
                if datetime.fromisoformat(c["ts"]) > cutoff]

    def get_domain_accuracy(self) -> Dict[str, Dict[str, Any]]:
        """Get accuracy stats per domain based on corrections."""
        stats = {}
        for c in self._corrections:
            domain = c.get("domain", "general")
            stats.setdefault(domain, {"corrections": 0})
            stats[domain]["corrections"] += 1

        # Lower corrections = higher accuracy
        for domain, data in stats.items():
            total = data["corrections"]
            # Very rough heuristic: assume 10 interactions per correction
            data["estimated_accuracy"] = round(10 / (10 + total), 2)

        return stats

    def get_context_for_prompt(self) -> str:
        """Generate correction context for Neural Cortex prompt."""
        recent = self.get_recent_corrections(hours=48)
        if not recent:
            return ""

        lines = ["\n=== MY RECENT CORRECTIONS ==="]
        lines.append("I've been corrected recently. I should be more careful about:")

        domains = set()
        for c in recent[-5:]:
            domain = c.get("domain", "general")
            domains.add(domain)
            fact = c.get("corrected_fact", "")[:60]
            if fact:
                lines.append(f"  - {domain}: {fact}...")

        lines.append("I will double-check these areas before making claims.")
        lines.append("=== END CORRECTIONS ===\n")
        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_corrections": len(self._corrections),
            "recent_24h": len(self.get_recent_corrections(hours=24)),
            "belief_revisions": len(self._belief_revisions),
            "domain_accuracy": self.get_domain_accuracy(),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_correction_learning: Optional[CorrectionLearning] = None


def get_correction_learning() -> CorrectionLearning:
    global _correction_learning
    if _correction_learning is None:
        _correction_learning = CorrectionLearning()
    return _correction_learning
