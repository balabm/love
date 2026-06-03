"""
LOVE Reading Tracker — Knowledge Intelligence (Modern AI Pattern)

Most reading lists are forgotten. This tracker:

1. READING LOGGING
   - Record books, articles, papers, and other content
   - Track reading speed, comprehension, and engagement
   - Log notes, highlights, and key takeaways

2. READING ANALYTICS
   - Calculate reading velocity (pages/hour, words/minute)
   - Identify optimal reading times and conditions
   - Track reading streaks and consistency

3. KNOWLEDGE INTEGRATION
   - Suggest connections between current reading and past knowledge
   - Recommend follow-up reading based on interests
   - Track concept mastery from reading

4. PROACTIVE READING
   - Suggest reading based on current goals and gaps
   - Recommend reading breaks to maintain comprehension
   - Alert when a book has been idle too long

Architecture:
- record_reading(title, type, pages, duration): Log reading session
- get_reading_stats(): Get reading analytics
- get_recommendation(): Suggest next reading
- get_comprehension_score(): Get reading comprehension metric
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

DATA_DIR = Path(__file__).parent.parent / "data" / "reading_tracker"
DATA_DIR.mkdir(parents=True, exist_ok=True)

READING_LOG = DATA_DIR / "readings.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class ReadingSession:
    """A reading session."""
    title: str = ""
    content_type: str = ""  # book, article, paper, newsletter, documentation
    pages_read: float = 0.0
    words_read: float = 0.0
    duration_minutes: float = 0.0
    comprehension_score: float = 0.5  # 0-1
    engagement_score: float = 0.5
    notes: str = ""
    key_takeaways: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    topic_tags: List[str] = field(default_factory=list)


@dataclass
class Book:
    """A book being tracked."""
    title: str = ""
    author: str = ""
    total_pages: float = 0.0
    pages_read: float = 0.0
    status: str = "reading"  # to_read, reading, completed, abandoned
    start_date: Optional[str] = None
    completed_date: Optional[str] = None
    rating: float = 0.0
    topic_tags: List[str] = field(default_factory=list)


class ReadingTracker:
    """
    Track reading habits and provide reading intelligence.
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
        self._sessions: deque = deque(maxlen=500)
        self._books: Dict[str, Book] = {}
        self._stats = {
            "total_sessions": 0,
            "total_pages": 0,
            "total_words": 0,
            "total_minutes": 0,
            "avg_speed_wpm": 0.0,
            "current_streak": 0,
            "books_completed": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_reading(self, title: str, content_type: str = "", pages: float = 0, words: float = 0, duration: float = 0, comprehension: float = 0.5, engagement: float = 0.5, notes: str = "", takeaways: Optional[List[str]] = None, topic_tags: Optional[List[str]] = None) -> ReadingSession:
        """Record a reading session."""
        session = ReadingSession(
            title=title,
            content_type=content_type or "article",
            pages_read=pages,
            words_read=words,
            duration_minutes=duration,
            comprehension_score=comprehension,
            engagement_score=engagement,
            notes=notes,
            key_takeaways=takeaways or [],
            topic_tags=topic_tags or [],
        )

        with self._lock:
            self._sessions.append(session)
            self._stats["total_sessions"] += 1
            self._stats["total_pages"] += pages
            self._stats["total_words"] += words
            self._stats["total_minutes"] += duration
            self._update_streak(session)
            self._update_stats(session)

            # Update book progress
            if title in self._books:
                self._books[title].pages_read += pages
                if self._books[title].pages_read >= self._books[title].total_pages:
                    self._books[title].status = "completed"
                    self._books[title].completed_date = session.timestamp
                    self._stats["books_completed"] += 1

        self._save_stats()
        self._log_session(session)

        return session

    def add_book(self, title: str, author: str = "", total_pages: float = 0, topic_tags: Optional[List[str]] = None) -> Book:
        """Add a book to track."""
        book = Book(
            title=title,
            author=author,
            total_pages=total_pages,
            topic_tags=topic_tags or [],
            start_date=datetime.now().isoformat(),
        )
        with self._lock:
            self._books[title] = book
        self._save_stats()
        return book

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_reading_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get reading analytics."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        recent = [s for s in self._sessions if s.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # Speed analysis
        total_words = sum(s.words_read for s in recent)
        total_minutes = sum(s.duration_minutes for s in recent)
        avg_wpm = total_words / max(1, total_minutes)

        # Type breakdown
        by_type = defaultdict(lambda: {"count": 0, "pages": 0, "minutes": 0})
        for s in recent:
            t = s.content_type
            by_type[t]["count"] += 1
            by_type[t]["pages"] += s.pages_read
            by_type[t]["minutes"] += s.duration_minutes

        # Topic interests
        topic_counts = defaultdict(float)
        for s in recent:
            for tag in s.topic_tags:
                topic_counts[tag] += s.engagement_score

        # Daily reading
        daily = defaultdict(float)
        for s in recent:
            day = s.timestamp[:10]
            daily[day] += s.duration_minutes

        # Comprehension trend
        comprehension_trend = sorted(
            [(s.timestamp[:10], s.comprehension_score) for s in recent],
            key=lambda x: x[0],
        )

        return {
            "days_analyzed": len(set(s.timestamp[:10] for s in recent)),
            "total_sessions": len(recent),
            "total_pages": round(sum(s.pages_read for s in recent), 1),
            "total_minutes": round(sum(s.duration_minutes for s in recent), 1),
            "avg_speed_wpm": round(avg_wpm, 1),
            "avg_comprehension": round(sum(s.comprehension_score for s in recent) / len(recent), 2),
            "avg_engagement": round(sum(s.engagement_score for s in recent) / len(recent), 2),
            "current_streak": self._stats["current_streak"],
            "type_breakdown": {k: dict(v) for k, v in by_type.items()},
            "top_topics": sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "comprehension_trend": comprehension_trend[-7:],
            "books_in_progress": [b.title for b in self._books.values() if b.status == "reading"],
            "books_completed": self._stats["books_completed"],
        }

    def get_recommendation(self) -> Dict[str, Any]:
        """Suggest next reading based on patterns."""
        # Analyze topic interests
        topic_counts = defaultdict(float)
        for s in self._sessions:
            for tag in s.topic_tags:
                topic_counts[tag] += s.engagement_score

        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        # Find books that match interests
        suggestions = []
        for book in self._books.values():
            if book.status == "to_read":
                match_score = sum(1 for t in book.topic_tags if any(t == top[0] for top in top_topics))
                if match_score > 0:
                    suggestions.append({
                        "title": book.title,
                        "author": book.author,
                        "reason": f"Matches your interest in {', '.join(book.topic_tags[:2])}",
                        "match_score": match_score,
                    })

        # If no matching books, suggest continuing current book
        in_progress = [b for b in self._books.values() if b.status == "reading"]
        if in_progress:
            for book in in_progress:
                days_idle = 0
                try:
                    last_session = [s for s in self._sessions if s.title == book.title]
                    if last_session:
                        last_date = datetime.fromisoformat(last_session[-1].timestamp)
                        days_idle = (datetime.now() - last_date).days
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.reading_tracker")

                if days_idle > 3:
                    suggestions.append({
                        "title": book.title,
                        "author": book.author,
                        "reason": f"You haven't read this in {days_idle} days. Pick it up again!",
                        "priority": "high",
                    })

        # Default suggestion
        if not suggestions:
            suggestions.append({
                "title": "Explore new topics",
                "reason": "Try reading something outside your usual interests to broaden your perspective.",
            })

        return {
            "suggestions": sorted(suggestions, key=lambda x: x.get("match_score", 0), reverse=True)[:3],
            "top_interests": [t[0] for t in top_topics],
            "reading_tip": "Read for comprehension, not speed. Take notes on key ideas.",
        }

    def get_comprehension_score(self) -> int:
        """Calculate overall reading comprehension score (0-100)."""
        if not self._sessions:
            return 0

        recent = list(self._sessions)[-20:]
        n = len(recent)

        # Comprehension quality
        avg_comprehension = sum(s.comprehension_score for s in recent) / n
        comprehension_score = avg_comprehension * 100

        # Note-taking habit
        notes_pct = sum(1 for s in recent if s.notes or s.key_takeaways) / n * 100
        notes_score = notes_pct

        # Consistency
        days_with_reading = len(set(s.timestamp[:10] for s in recent))
        consistency_score = min(100, days_with_reading * 14)  # 7 days = 100

        overall = round(comprehension_score * 0.5 + notes_score * 0.2 + consistency_score * 0.3)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_streak(self, session: ReadingSession):
        """Update reading streak."""
        today = datetime.now().date()
        try:
            session_date = datetime.fromisoformat(session.timestamp).date()
        except Exception:
            session_date = today

        if self._sessions and len(self._sessions) > 1:
            try:
                last_session = list(self._sessions)[-2]
                last_date = datetime.fromisoformat(last_session.timestamp).date()
                if (session_date - last_date).days == 1:
                    self._stats["current_streak"] += 1
                elif (session_date - last_date).days > 1:
                    self._stats["current_streak"] = 1
            except Exception:
                self._stats["current_streak"] = 1
        else:
            self._stats["current_streak"] = 1

    def _update_stats(self, session: ReadingSession):
        """Update running statistics."""
        n = self._stats["total_sessions"]
        # Update average reading speed
        if session.duration_minutes > 0 and session.words_read > 0:
            wpm = session.words_read / session.duration_minutes
            self._stats["avg_speed_wpm"] = round((self._stats["avg_speed_wpm"] * (n - 1) + wpm) / n, 1)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "books": {k: {
                    "title": v.title,
                    "author": v.author,
                    "total_pages": v.total_pages,
                    "pages_read": v.pages_read,
                    "status": v.status,
                    "topic_tags": v.topic_tags,
                } for k, v in self._books.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.reading_tracker")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("books", {}).items():
                    self._books[k] = Book(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.reading_tracker")

    def _log_session(self, session: ReadingSession):
        try:
            with open(READING_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": session.timestamp,
                    "title": session.title,
                    "type": session.content_type,
                    "pages": session.pages_read,
                    "words": session.words_read,
                    "minutes": session.duration_minutes,
                    "comprehension": session.comprehension_score,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.reading_tracker")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rt_instance: Optional[ReadingTracker] = None
_rt_lock = threading.Lock()


def get_reading_tracker() -> ReadingTracker:
    global _rt_instance
    with _rt_lock:
        if _rt_instance is None:
            _rt_instance = ReadingTracker()
        return _rt_instance
