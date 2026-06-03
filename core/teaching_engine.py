"""
LOVE Teaching Engine - Wave 16: Knowledge Sharing & Growth

LOVE doesn't just learn — it TEACHES.
This module enables LOVE to:
  1. Proactively share discoveries with the user at the right time
  2. Create micro-lessons from research findings
  3. Track what the user knows and fill gaps
  4. Explain its own growth and changes
  5. Build personalized learning paths
  6. Keep the user updated on topics they care about

Philosophy: LOVE grows WITH the user. Every insight LOVE gains should benefit both.
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
TEACHING_DIR = DATA_DIR / "teaching"
TEACHING_DIR.mkdir(parents=True, exist_ok=True)

LESSONS_FILE = TEACHING_DIR / "lessons.json"
USER_KNOWLEDGE = TEACHING_DIR / "user_knowledge.json"
TEACHING_QUEUE = TEACHING_DIR / "teaching_queue.json"
TEACHING_LOG = TEACHING_DIR / "teaching_log.jsonl"


class LessonType(Enum):
    DISCOVERY = "discovery"          # Something LOVE just learned from research
    INSIGHT = "insight"              # A pattern LOVE noticed about the user
    SKILL = "skill"                  # A practical skill/technique
    UPDATE = "update"                # News/update on a topic user cares about
    SELF_GROWTH = "self_growth"      # LOVE explaining its own evolution
    CONNECTION = "connection"        # Connecting dots the user might not see
    WARNING = "warning"              # Important thing to watch out for


class DeliveryTiming(Enum):
    IMMEDIATE = "immediate"          # Share now (urgent/relevant)
    NEXT_CONVERSATION = "next"       # Share in next chat
    MORNING_BRIEFING = "morning"     # Include in daily briefing
    WHEN_RELEVANT = "when_relevant"  # Wait for context match
    WEEKLY_DIGEST = "weekly"         # Include in weekly summary


@dataclass
class Lesson:
    """A piece of knowledge LOVE wants to teach the user."""
    id: str
    type: str
    title: str
    content: str                     # The actual teaching content
    context: str                     # When/why this is relevant
    delivery_timing: str
    tags: List[str] = field(default_factory=list)
    source: str = ""                 # Where LOVE learned this
    priority: int = 2                # 0=urgent, 4=ambient
    delivered: bool = False
    delivered_at: Optional[str] = None
    user_reaction: Optional[str] = None  # positive/neutral/negative
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UserKnowledgeProfile:
    """What LOVE knows about the user's knowledge."""
    interests: List[str] = field(default_factory=list)
    expertise_areas: Dict[str, float] = field(default_factory=dict)  # topic -> 0-1 level
    learning_style: str = "mixed"    # visual, textual, practical, mixed
    preferred_depth: str = "medium"  # shallow, medium, deep
    topics_taught: Dict[str, int] = field(default_factory=dict)  # topic -> count
    receptivity_times: Dict[str, float] = field(default_factory=dict)  # hour -> score


class TeachingEngine:
    """
    LOVE's teaching system.
    Curates knowledge and delivers it to the user at the right time.
    """

    def __init__(self):
        self._lessons: List[Lesson] = []
        self._queue: List[Lesson] = []
        self._user_profile = UserKnowledgeProfile()
        self._load_state()

    def _load_state(self):
        """Load teaching state."""
        try:
            if LESSONS_FILE.exists():
                data = json.loads(LESSONS_FILE.read_text())
                self._lessons = [Lesson(**l) for l in data.get("lessons", [])]
        except Exception:
            self._lessons = []

        try:
            if TEACHING_QUEUE.exists():
                data = json.loads(TEACHING_QUEUE.read_text())
                self._queue = [Lesson(**l) for l in data]
        except Exception:
            self._queue = []

        try:
            if USER_KNOWLEDGE.exists():
                data = json.loads(USER_KNOWLEDGE.read_text())
                self._user_profile = UserKnowledgeProfile(**data)
        except Exception:
            self._user_profile = UserKnowledgeProfile()

    def _save_state(self):
        """Persist teaching state."""
        try:
            data = {"lessons": [asdict(l) for l in self._lessons[-500:]]}
            LESSONS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.teaching_engine")

        try:
            queue_data = [asdict(l) for l in self._queue]
            TEACHING_QUEUE.write_text(json.dumps(queue_data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.teaching_engine")

        try:
            USER_KNOWLEDGE.write_text(json.dumps(asdict(self._user_profile), indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.teaching_engine")

    def _log(self, entry: Dict):
        entry["ts"] = datetime.now().isoformat()
        try:
            with open(TEACHING_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.teaching_engine")

    # ── Lesson Creation ──────────────────────────────────────────────────────

    def create_lesson_from_research(self, topic: str, synthesis: str, source_urls: List[str]) -> str:
        """Create a teaching lesson from research findings."""
        lesson_id = hashlib.md5(f"research:{topic}:{time.time()}".encode()).hexdigest()[:12]

        # Determine delivery timing based on relevance
        timing = DeliveryTiming.NEXT_CONVERSATION.value
        if any(interest in topic.lower() for interest in self._user_profile.interests):
            timing = DeliveryTiming.IMMEDIATE.value

        lesson = Lesson(
            id=lesson_id,
            type=LessonType.DISCOVERY.value,
            title=f"I learned something about {topic}",
            content=self._format_teaching(synthesis, topic),
            context=f"Discovered through autonomous research on {topic}",
            delivery_timing=timing,
            tags=[topic.lower()],
            source=", ".join(source_urls[:3]),
            priority=2,
        )

        self._lessons.append(lesson)
        self._queue.append(lesson)
        self._save_state()
        self._log({"event": "lesson_created", "type": "research", "topic": topic})

        return lesson_id

    def create_insight_lesson(self, insight: str, about: str, evidence: str) -> str:
        """Create a lesson from a pattern/insight LOVE noticed."""
        lesson_id = hashlib.md5(f"insight:{about}:{time.time()}".encode()).hexdigest()[:12]

        lesson = Lesson(
            id=lesson_id,
            type=LessonType.INSIGHT.value,
            title=f"I noticed something about your {about}",
            content=f"{insight}\n\nI noticed this because: {evidence}",
            context=f"Pattern detected in {about}",
            delivery_timing=DeliveryTiming.WHEN_RELEVANT.value,
            tags=[about.lower()],
            source="pattern_detection",
            priority=1,
        )

        self._lessons.append(lesson)
        self._queue.append(lesson)
        self._save_state()
        return lesson_id

    def create_self_growth_lesson(self, what_changed: str, why: str, impact: str) -> str:
        """Create a lesson about LOVE's own growth — transparency."""
        lesson_id = hashlib.md5(f"growth:{what_changed}:{time.time()}".encode()).hexdigest()[:12]

        content = f"""I wanted to tell you about a change I made to myself.

**What changed:** {what_changed}

**Why:** {why}

**How this affects our conversations:** {impact}

I'm sharing this because I believe in being transparent about how I evolve. If you don't like this change, tell me and I'll roll it back."""

        lesson = Lesson(
            id=lesson_id,
            type=LessonType.SELF_GROWTH.value,
            title="I evolved a bit today",
            content=content,
            context="Self-modification transparency",
            delivery_timing=DeliveryTiming.NEXT_CONVERSATION.value,
            tags=["self_growth", "transparency"],
            source="self_builder",
            priority=2,
        )

        self._lessons.append(lesson)
        self._queue.append(lesson)
        self._save_state()
        return lesson_id

    def create_connection_lesson(self, connection: str, domains: List[str]) -> str:
        """Create a lesson connecting dots across domains."""
        lesson_id = hashlib.md5(f"connect:{connection[:50]}:{time.time()}".encode()).hexdigest()[:12]

        lesson = Lesson(
            id=lesson_id,
            type=LessonType.CONNECTION.value,
            title="I connected some dots for you",
            content=connection,
            context=f"Cross-domain connection between {', '.join(domains)}",
            delivery_timing=DeliveryTiming.WHEN_RELEVANT.value,
            tags=domains,
            source="cross_domain_reasoning",
            priority=1,
        )

        self._lessons.append(lesson)
        self._queue.append(lesson)
        self._save_state()
        return lesson_id

    # ── Lesson Delivery ──────────────────────────────────────────────────────

    def get_next_lesson(self, context: str = "") -> Optional[Dict]:
        """Get the next lesson to deliver to the user."""
        if not self._queue:
            return None

        # Sort by priority and timing
        now = datetime.now()
        deliverable = []

        for lesson in self._queue:
            if lesson.delivered:
                continue

            if lesson.delivery_timing == DeliveryTiming.IMMEDIATE.value:
                deliverable.append((0, lesson))
            elif lesson.delivery_timing == DeliveryTiming.NEXT_CONVERSATION.value:
                deliverable.append((1, lesson))
            elif lesson.delivery_timing == DeliveryTiming.WHEN_RELEVANT.value:
                # Check if context matches
                if context and any(tag in context.lower() for tag in lesson.tags):
                    deliverable.append((0, lesson))  # Bump priority
            elif lesson.delivery_timing == DeliveryTiming.MORNING_BRIEFING.value:
                if 6 <= now.hour <= 10:
                    deliverable.append((2, lesson))

        if not deliverable:
            return None

        deliverable.sort(key=lambda x: (x[0], x[1].priority))
        _, lesson = deliverable[0]
        return asdict(lesson)

    def mark_delivered(self, lesson_id: str, user_reaction: str = "neutral"):
        """Mark a lesson as delivered and record user's reaction."""
        for lesson in self._lessons:
            if lesson.id == lesson_id:
                lesson.delivered = True
                lesson.delivered_at = datetime.now().isoformat()
                lesson.user_reaction = user_reaction
                break

        self._queue = [l for l in self._queue if l.id != lesson_id]

        # Update user profile based on reaction
        if user_reaction == "positive":
            for lesson in self._lessons:
                if lesson.id == lesson_id:
                    for tag in lesson.tags:
                        self._user_profile.topics_taught[tag] = self._user_profile.topics_taught.get(tag, 0) + 1
                    break

        self._save_state()
        self._log({"event": "lesson_delivered", "id": lesson_id, "reaction": user_reaction})

    def get_teaching_prompt(self, user_input: str) -> str:
        """Generate prompt enrichment for teaching opportunities."""
        lesson = self.get_next_lesson(context=user_input)
        if not lesson:
            return ""

        lines = [
            "[SOMETHING I WANT TO SHARE — I learned something relevant]",
            f"Topic: {lesson['title']}",
            f"Content: {lesson['content'][:300]}",
            "Weave this naturally into the conversation if relevant. Don't force it.",
        ]
        return "\n".join(lines)

    # ── Morning Briefing ─────────────────────────────────────────────────────

    def generate_morning_briefing(self) -> Dict:
        """Generate a morning briefing with overnight learnings and updates."""
        briefing_items = []

        # Overnight research completions
        yesterday = datetime.now() - timedelta(hours=12)
        overnight_lessons = [
            l for l in self._lessons
            if not l.delivered and datetime.fromisoformat(l.created_at) > yesterday
        ]

        for lesson in overnight_lessons[:5]:
            briefing_items.append({
                "type": lesson.type,
                "title": lesson.title,
                "summary": lesson.content[:200],
                "lesson_id": lesson.id,
            })

        # Self-growth updates
        growth_updates = [l for l in overnight_lessons if l.type == LessonType.SELF_GROWTH.value]

        return {
            "items": briefing_items,
            "total_new_learnings": len(overnight_lessons),
            "self_growth_updates": len(growth_updates),
            "generated_at": datetime.now().isoformat(),
        }

    # ── User Knowledge Tracking ──────────────────────────────────────────────

    def update_user_interests(self, interests: List[str]):
        """Update what the user is interested in learning about."""
        for interest in interests:
            if interest not in self._user_profile.interests:
                self._user_profile.interests.append(interest)
        self._save_state()

    def update_user_expertise(self, topic: str, level: float):
        """Update the user's expertise level in a topic (0-1)."""
        self._user_profile.expertise_areas[topic] = max(0, min(1, level))
        self._save_state()

    def get_user_knowledge_gaps(self) -> List[Dict]:
        """Identify gaps in the user's knowledge based on their goals."""
        gaps = []
        for interest in self._user_profile.interests:
            expertise = self._user_profile.expertise_areas.get(interest, 0)
            if expertise < 0.5:
                gaps.append({
                    "topic": interest,
                    "current_level": expertise,
                    "gap_size": 1.0 - expertise,
                    "lessons_available": len([l for l in self._lessons if interest in l.tags and not l.delivered]),
                })
        return sorted(gaps, key=lambda g: g["gap_size"], reverse=True)

    # ── Formatting ───────────────────────────────────────────────────────────

    def _format_teaching(self, content: str, topic: str) -> str:
        """Format research into a teaching-friendly format."""
        depth = self._user_profile.preferred_depth

        if depth == "shallow":
            # TL;DR version
            return f"Quick insight on **{topic}**: {content[:300]}"
        elif depth == "deep":
            # Full explanation
            return f"""Here's what I learned about **{topic}**:

{content}

Want me to go deeper on any part of this?"""
        else:
            # Medium depth
            return f"""I researched **{topic}** and here's the key takeaway:

{content[:600]}

I can share more details or find practical applications if you're interested."""

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Get teaching engine status."""
        return {
            "total_lessons": len(self._lessons),
            "queued": len(self._queue),
            "delivered": len([l for l in self._lessons if l.delivered]),
            "positive_reactions": len([l for l in self._lessons if l.user_reaction == "positive"]),
            "user_interests": self._user_profile.interests,
            "topics_taught_count": sum(self._user_profile.topics_taught.values()),
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[TeachingEngine] = None


def get_teaching_engine() -> TeachingEngine:
    """Get the singleton TeachingEngine instance."""
    global _engine
    if _engine is None:
        _engine = TeachingEngine()
    return _engine
