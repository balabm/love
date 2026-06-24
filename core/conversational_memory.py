"""
LOVE Conversational Memory — Phase 5q of AGI Metamorphosis

LOVE doesn't just process messages. LOVE remembers conversations.
- What did we talk about yesterday?
- What questions did Karthi ask that I couldn't answer?
- What threads are still unresolved?
- What topics come up repeatedly?

This makes LOVE feel like a real companion who was paying attention.
"Hey, remember when we discussed refactoring the neural bus last week?
I was thinking about that..."

The conversational memory stores:
1. conversation_log: every exchange with topic extraction
2. topic_index: recurring themes and their frequency
3. unresolved_threads: questions asked but not fully answered
4. personal_facts: things Karthi has shared about himself
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONVERSATION_LOG_PATH = DATA_DIR / "conversation_log.jsonl"
TOPIC_INDEX_PATH = DATA_DIR / "conversation_topics.json"
UNRESOLVED_THREADS_PATH = DATA_DIR / "unresolved_threads.json"
PERSONAL_FACTS_PATH = DATA_DIR / "personal_facts.json"


class ConversationalMemory:
    """
    LOVE's memory of conversations with Karthi.
    """

    def __init__(self):
        self._topics: Dict[str, Dict[str, Any]] = {}
        self._unresolved: List[Dict[str, Any]] = []
        self._personal_facts: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if TOPIC_INDEX_PATH.exists():
            try:
                with open(TOPIC_INDEX_PATH, "r", encoding="utf-8") as f:
                    self._topics = json.load(f)
            except Exception:
                pass
        if UNRESOLVED_THREADS_PATH.exists():
            try:
                with open(UNRESOLVED_THREADS_PATH, "r", encoding="utf-8") as f:
                    self._unresolved = json.load(f)
            except Exception:
                pass
        if PERSONAL_FACTS_PATH.exists():
            try:
                with open(PERSONAL_FACTS_PATH, "r", encoding="utf-8") as f:
                    self._personal_facts = json.load(f)
            except Exception:
                pass

    def _save_topics(self):
        try:
            with open(TOPIC_INDEX_PATH, "w", encoding="utf-8") as f:
                json.dump(self._topics, f, indent=2)
        except Exception:
            pass

    def _save_unresolved(self):
        try:
            with open(UNRESOLVED_THREADS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._unresolved, f, indent=2)
        except Exception:
            pass

    def _save_facts(self):
        try:
            with open(PERSONAL_FACTS_PATH, "w", encoding="utf-8") as f:
                json.dump(self._personal_facts, f, indent=2)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # RECORDING CONVERSATIONS
    # ═══════════════════════════════════════════════════════════════════════

    def record_exchange(self, user_message: str, love_response: str,
                        topic_hint: Optional[str] = None):
        """
        Record a single exchange between Karthi and LOVE.
        """
        now = datetime.now().isoformat()
        entry = {
            "ts": now,
            "user": user_message[:500],
            "love": love_response[:1000],
            "topic": topic_hint or self._extract_topic(user_message, love_response),
        }

        # Log to file
        try:
            with open(CONVERSATION_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

        # Update topic index
        topic = entry["topic"]
        if topic:
            if topic not in self._topics:
                self._topics[topic] = {"count": 0, "first_seen": now, "last_seen": now}
            self._topics[topic]["count"] += 1
            self._topics[topic]["last_seen"] = now
            self._save_topics()

        # Check for unresolved questions
        self._check_unresolved(user_message, love_response, now)

        # Extract personal facts
        self._extract_personal_facts(user_message, now)

    def _extract_topic(self, user_msg: str, love_resp: str) -> str:
        """Simple topic extraction from conversation content."""
        text = (user_msg + " " + love_resp).lower()

        topic_keywords = {
            "code": {"code", "bug", "fix", "refactor", "compile", "error", "syntax"},
            "architecture": {"architecture", "design", "pattern", "module", "component", "structure"},
            "finance": {"money", "btc", "bitcoin", "crypto", "trade", "portfolio", "invest", "stock"},
            "health": {"health", "sleep", "tired", "exercise", "workout", "diet", "stress"},
            "schedule": {"schedule", "calendar", "meeting", "deadline", "plan", "todo", "task"},
            "love_system": {"love", "system", "module", "ai", "jarvis", "cortex", "neural"},
            "personal": {"feel", "think", "want", "need", "like", "prefer", "love", "hate"},
            "learning": {"learn", "study", "read", "book", "course", "tutorial", "documentation"},
        }

        best_topic = "general"
        best_score = 0
        for topic, keywords in topic_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_topic = topic

        return best_topic

    def _check_unresolved(self, user_msg: str, love_resp: str, timestamp: str):
        """Detect questions that weren't fully answered."""
        # Simple heuristic: user asked a question but LOVE said "I don't know" or "I'm not sure"
        lower_resp = love_resp.lower()
        uncertainty_signals = {
            "i don't know", "i'm not sure", "not certain", "unclear",
            "need more information", "can't determine", "hard to say",
            "no idea", "unsure", "ambiguous",
        }

        if any(s in lower_resp for s in uncertainty_signals):
            self._unresolved.append({
                "ts": timestamp,
                "question": user_msg[:200],
                "reason": "LOVE expressed uncertainty",
                "status": "open",
            })
            # Keep only last 50
            self._unresolved = self._unresolved[-50:]
            self._save_unresolved()

        # Also check if user said "remind me" or "I'll check later"
        lower_msg = user_msg.lower()
        if any(p in lower_msg for p in {"remind me", "later", "tomorrow", "next time", "follow up"}):
            self._unresolved.append({
                "ts": timestamp,
                "question": user_msg[:200],
                "reason": "Karthi asked for follow-up",
                "status": "open",
            })
            self._unresolved = self._unresolved[-50:]
            self._save_unresolved()

    def _extract_personal_facts(self, message: str, timestamp: str):
        """Extract things Karthi has shared about himself."""
        lower_msg = message.lower()

        # Simple patterns for personal facts
        fact_patterns = [
            ("preference", ["i like", "i prefer", "i love", "i enjoy", "my favorite"]),
            ("dislike", ["i hate", "i dislike", "i can't stand", "i don't like"]),
            ("goal", ["i want to", "my goal is", "i'm trying to", "i plan to"]),
            ("habit", ["i usually", "i always", "i tend to", "i never"]),
            ("value", ["i believe", "i think", "in my opinion", "i care about"]),
            ("constraint", ["i can't", "i'm unable to", "i don't have time", "i'm limited by"]),
        ]

        for fact_type, patterns in fact_patterns:
            for pattern in patterns:
                if pattern in lower_msg:
                    # Extract the fact
                    idx = lower_msg.find(pattern)
                    fact_text = message[idx:idx + 120]

                    self._personal_facts.append({
                        "ts": timestamp,
                        "type": fact_type,
                        "fact": fact_text,
                    })
                    # Keep only last 100
                    self._personal_facts = self._personal_facts[-100:]
                    self._save_facts()
                    return  # One fact per message

    # ═══════════════════════════════════════════════════════════════════════
    # QUERYING MEMORY
    # ═══════════════════════════════════════════════════════════════════════

    def get_recent_conversations(self, hours: int = 24, max_items: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation entries."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []
        if not CONVERSATION_LOG_PATH.exists():
            return recent
        try:
            with open(CONVERSATION_LOG_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line.strip())
                    ts = datetime.fromisoformat(entry["ts"])
                    if ts > cutoff:
                        recent.append(entry)
        except Exception:
            pass
        return recent[-max_items:]

    def get_conversational_context(self, max_age_hours: int = 48) -> str:
        """
        Generate conversational context for injection into the Neural Cortex prompt.
        This is what makes LOVE feel like it remembers yesterday.
        """
        lines = ["\n=== WHAT WE HAVE BEEN TALKING ABOUT ==="]

        # Recent conversations
        recent = self.get_recent_conversations(hours=max_age_hours, max_items=3)
        if recent:
            lines.append("Recent exchanges:")
            for entry in recent:
                ts = datetime.fromisoformat(entry["ts"])
                time_ago = self._format_time_ago(ts)
                user_msg = entry["user"][:80]
                lines.append(f"  [{time_ago}] Karthi: {user_msg}...")
        else:
            lines.append("No recent conversations.")

        # Recurring topics
        if self._topics:
            # Sort by frequency
            top_topics = sorted(
                self._topics.items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )[:5]
            lines.append("Topics we discuss often:")
            for topic, info in top_topics:
                lines.append(f"  - {topic}: {info['count']} times")

        # Unresolved threads
        open_threads = [t for t in self._unresolved if t.get("status") == "open"]
        if open_threads:
            lines.append("Unresolved threads (I should follow up on these):")
            for thread in open_threads[-3:]:
                ts = datetime.fromisoformat(thread["ts"])
                time_ago = self._format_time_ago(ts)
                lines.append(f"  [{time_ago}] {thread['question'][:80]}...")

        # Personal facts
        if self._personal_facts:
            lines.append("Things I know about Karthi:")
            for fact in self._personal_facts[-5:]:
                lines.append(f"  - [{fact['type']}] {fact['fact'][:100]}")

        lines.append("=== END CONVERSATIONS ===\n")
        return "\n".join(lines)

    def _format_time_ago(self, dt: datetime) -> str:
        """Format a datetime as a human-readable time ago."""
        delta = datetime.now() - dt
        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            return f"{int(delta.seconds / 60)}m ago"
        elif delta < timedelta(days=1):
            return f"{int(delta.seconds / 3600)}h ago"
        else:
            return f"{delta.days}d ago"

    def mark_resolved(self, question_substring: str):
        """Mark an unresolved thread as resolved."""
        for thread in self._unresolved:
            if question_substring.lower() in thread["question"].lower():
                thread["status"] = "resolved"
                thread["resolved_at"] = datetime.now().isoformat()
        self._save_unresolved()

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_topics": len(self._topics),
            "unresolved_threads": len([t for t in self._unresolved if t.get("status") == "open"]),
            "personal_facts": len(self._personal_facts),
            "recent_conversations": len(self.get_recent_conversations(hours=24)),
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_conversational_memory: Optional[ConversationalMemory] = None


def get_conversational_memory() -> ConversationalMemory:
    global _conversational_memory
    if _conversational_memory is None:
        _conversational_memory = ConversationalMemory()
    return _conversational_memory
