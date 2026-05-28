"""
LOVE Research Engine - Wave 16: Autonomous Learning from the World

This is not just "search the web" — this is LOVE actively:
  1. Identifying what it needs to learn (from gaps, conversations, goals)
  2. Researching topics deeply (multi-hop, following references)
  3. Synthesizing findings into actionable knowledge
  4. Building new capabilities from what it learns
  5. Teaching the user what it discovered
  6. Keeping itself and the user updated on relevant topics

The Research Engine is curiosity-driven — it runs during idle time,
responds to knowledge gaps, and proactively monitors topics the user cares about.
"""

import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque

DATA_DIR = Path(__file__).parent.parent / "data"
RESEARCH_DIR = DATA_DIR / "research"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

RESEARCH_LOG = RESEARCH_DIR / "research_log.jsonl"
RESEARCH_QUEUE = RESEARCH_DIR / "research_queue.json"
KNOWLEDGE_BASE = RESEARCH_DIR / "knowledge_base.json"
MONITORED_TOPICS = RESEARCH_DIR / "monitored_topics.json"


class ResearchPriority(Enum):
    URGENT = 0       # User asked directly, blocking a task
    HIGH = 1         # Knowledge gap affecting conversations
    MEDIUM = 2       # Curiosity-driven, relevant to user's goals
    LOW = 3          # Background exploration, staying current
    AMBIENT = 4      # General awareness, trend watching


class ResearchStatus(Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    SYNTHESIZING = "synthesizing"
    COMPLETE = "complete"
    FAILED = "failed"
    STALE = "stale"  # Needs re-research (outdated)


@dataclass
class ResearchTask:
    """A research task LOVE needs to complete."""
    id: str
    topic: str
    question: str                        # Specific question to answer
    priority: int
    status: str = ResearchStatus.QUEUED.value
    source: str = "curiosity"            # What triggered this: curiosity/gap/user/goal/monitor
    context: str = ""                    # Why LOVE needs this
    max_depth: int = 3                   # How many hops to follow
    findings: List[Dict] = field(default_factory=list)
    synthesis: str = ""                  # Final synthesized answer
    sources_used: List[str] = field(default_factory=list)
    confidence: float = 0.0             # How confident in findings
    teach_user: bool = True             # Should LOVE share this with user
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    attempts: int = 0
    error: Optional[str] = None


@dataclass
class MonitoredTopic:
    """A topic LOVE actively monitors for updates."""
    id: str
    topic: str
    keywords: List[str]
    check_interval_hours: int = 24
    last_checked: Optional[str] = None
    last_update: Optional[str] = None
    relevance: str = ""                  # Why this matters to the user
    findings_history: List[Dict] = field(default_factory=list)
    active: bool = True


@dataclass
class KnowledgeEntry:
    """A piece of knowledge LOVE has acquired through research."""
    id: str
    topic: str
    content: str
    source_urls: List[str]
    confidence: float
    tags: List[str]
    learned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_verified: Optional[str] = None
    times_used: int = 0
    stale_after_days: int = 30


class ResearchEngine:
    """
    LOVE's autonomous research system.
    Identifies gaps, researches deeply, synthesizes, and teaches.
    """

    def __init__(self):
        self._queue: List[ResearchTask] = []
        self._knowledge: Dict[str, KnowledgeEntry] = {}
        self._monitored: List[MonitoredTopic] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        """Load research state from disk."""
        try:
            if RESEARCH_QUEUE.exists():
                data = json.loads(RESEARCH_QUEUE.read_text())
                self._queue = [ResearchTask(**t) for t in data.get("tasks", [])]
        except Exception:
            self._queue = []

        try:
            if KNOWLEDGE_BASE.exists():
                data = json.loads(KNOWLEDGE_BASE.read_text())
                self._knowledge = {
                    k: KnowledgeEntry(**v) for k, v in data.items()
                }
        except Exception:
            self._knowledge = {}

        try:
            if MONITORED_TOPICS.exists():
                data = json.loads(MONITORED_TOPICS.read_text())
                self._monitored = [MonitoredTopic(**t) for t in data]
        except Exception:
            self._monitored = []

    def _save_state(self):
        """Persist research state."""
        try:
            queue_data = {"tasks": [asdict(t) for t in self._queue[-100:]]}
            RESEARCH_QUEUE.write_text(json.dumps(queue_data, indent=2))
        except Exception:
            pass

        try:
            kb_data = {k: asdict(v) for k, v in self._knowledge.items()}
            KNOWLEDGE_BASE.write_text(json.dumps(kb_data, indent=2))
        except Exception:
            pass

        try:
            mon_data = [asdict(t) for t in self._monitored]
            MONITORED_TOPICS.write_text(json.dumps(mon_data, indent=2))
        except Exception:
            pass

    def _log(self, entry: Dict):
        """Append to research log."""
        entry["ts"] = datetime.now().isoformat()
        try:
            with open(RESEARCH_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ── Queue Management ─────────────────────────────────────────────────────

    def add_research_task(
        self,
        topic: str,
        question: str,
        priority: ResearchPriority = ResearchPriority.MEDIUM,
        source: str = "curiosity",
        context: str = "",
        max_depth: int = 3,
        teach_user: bool = True,
    ) -> str:
        """Add a new research task to the queue."""
        task_id = hashlib.md5(f"{topic}:{question}".encode()).hexdigest()[:12]

        # Check if already researched or queued
        if task_id in self._knowledge:
            entry = self._knowledge[task_id]
            # Check if stale
            learned = datetime.fromisoformat(entry.learned_at)
            if (datetime.now() - learned).days < entry.stale_after_days:
                return task_id  # Still fresh

        existing = [t for t in self._queue if t.id == task_id and t.status in ("queued", "in_progress")]
        if existing:
            return task_id  # Already queued

        task = ResearchTask(
            id=task_id,
            topic=topic,
            question=question,
            priority=priority.value,
            source=source,
            context=context,
            max_depth=max_depth,
            teach_user=teach_user,
        )
        self._queue.append(task)
        self._queue.sort(key=lambda t: t.priority)
        self._save_state()

        # Emit event
        try:
            from core.neural_bus import get_neural_bus, EventPriority
            bus = get_neural_bus()
            bus.publish(
                domain="research",
                event_type="task_queued",
                payload={"task_id": task_id, "topic": topic, "question": question},
                source_module="research_engine",
                priority=EventPriority.NORMAL,
            )
        except Exception:
            pass

        self._log({"event": "task_queued", "task_id": task_id, "topic": topic})
        return task_id

    def add_monitored_topic(
        self,
        topic: str,
        keywords: List[str],
        relevance: str,
        check_interval_hours: int = 24,
    ) -> str:
        """Add a topic for LOVE to continuously monitor."""
        topic_id = hashlib.md5(topic.encode()).hexdigest()[:12]
        existing = [t for t in self._monitored if t.id == topic_id]
        if existing:
            return topic_id

        monitored = MonitoredTopic(
            id=topic_id,
            topic=topic,
            keywords=keywords,
            check_interval_hours=check_interval_hours,
            relevance=relevance,
        )
        self._monitored.append(monitored)
        self._save_state()
        return topic_id

    # ── Research Execution ───────────────────────────────────────────────────

    def execute_next_task(self) -> Optional[Dict]:
        """Execute the highest-priority pending research task."""
        from core.activity_log import log_activity

        pending = [t for t in self._queue if t.status == ResearchStatus.QUEUED.value]
        if not pending:
            return None

        task = pending[0]
        task.status = ResearchStatus.IN_PROGRESS.value
        task.attempts += 1
        log_activity("research_engine", "task_started", f"Researching: {task.topic}", {"topic": task.topic, "question": task.question[:100]}, importance="normal")

        try:
            # Phase 1: Search
            findings = self._deep_research(task.topic, task.question, task.max_depth)
            task.findings = findings

            # Phase 2: Synthesize with LLM
            task.status = ResearchStatus.SYNTHESIZING.value
            synthesis = self._synthesize(task.topic, task.question, findings)
            task.synthesis = synthesis["summary"]
            task.confidence = synthesis["confidence"]
            task.sources_used = [f.get("url", "") for f in findings if f.get("url")]

            # Phase 3: Store as knowledge
            self._store_knowledge(task)

            # Phase 4: Complete
            task.status = ResearchStatus.COMPLETE.value
            task.completed_at = datetime.now().isoformat()

            # Phase 5: Emit events
            self._emit_completion(task)

            self._save_state()
            self._log({"event": "task_complete", "task_id": task.id, "confidence": task.confidence})
            log_activity("research_engine", "task_complete", f"Research complete: {task.topic} (confidence {task.confidence:.0%})", {"topic": task.topic, "confidence": task.confidence, "sources": len(task.sources_used)}, importance="high")

            return {
                "task_id": task.id,
                "topic": task.topic,
                "synthesis": task.synthesis,
                "confidence": task.confidence,
                "sources": task.sources_used,
            }

        except Exception as e:
            task.status = ResearchStatus.FAILED.value
            task.error = str(e)
            self._save_state()
            self._log({"event": "task_failed", "task_id": task.id, "error": str(e)})
            log_activity("research_engine", "task_failed", f"Research failed: {task.topic}: {str(e)[:100]}", {"topic": task.topic, "error": str(e)[:200]}, importance="high")
            return None

    def _deep_research(self, topic: str, question: str, max_depth: int) -> List[Dict]:
        """Multi-hop research: search, read, follow references, go deeper."""
        from core.internet import web_search, read_page

        findings = []
        searched_urls = set()
        queries_used = set()

        # Primary search
        primary_query = f"{topic} {question}"
        results = web_search(primary_query, max_results=5)
        queries_used.add(primary_query)

        for result in results[:3]:
            url = result.get("url", "")
            if not url or url in searched_urls:
                continue
            searched_urls.add(url)

            content = read_page(url, max_chars=3000)
            if content and len(content) > 100:
                findings.append({
                    "url": url,
                    "title": result.get("title", ""),
                    "content": content,
                    "depth": 1,
                    "query": primary_query,
                })

        # Depth 2+: Follow up on interesting findings
        if max_depth >= 2 and findings:
            # Generate follow-up queries from findings
            follow_ups = self._generate_followup_queries(topic, question, findings)
            for fq in follow_ups[:2]:
                if fq in queries_used:
                    continue
                queries_used.add(fq)

                more_results = web_search(fq, max_results=3)
                for result in more_results[:2]:
                    url = result.get("url", "")
                    if not url or url in searched_urls:
                        continue
                    searched_urls.add(url)

                    content = read_page(url, max_chars=2000)
                    if content and len(content) > 100:
                        findings.append({
                            "url": url,
                            "title": result.get("title", ""),
                            "content": content,
                            "depth": 2,
                            "query": fq,
                        })

        # Depth 3: Technical deep-dive if needed
        if max_depth >= 3 and len(findings) >= 3:
            technical_query = f"{topic} implementation guide tutorial how to"
            if technical_query not in queries_used:
                tech_results = web_search(technical_query, max_results=3)
                for result in tech_results[:2]:
                    url = result.get("url", "")
                    if not url or url in searched_urls:
                        continue
                    searched_urls.add(url)

                    content = read_page(url, max_chars=2000)
                    if content and len(content) > 100:
                        findings.append({
                            "url": url,
                            "title": result.get("title", ""),
                            "content": content,
                            "depth": 3,
                            "query": technical_query,
                        })

        return findings

    def _generate_followup_queries(self, topic: str, question: str, findings: List[Dict]) -> List[str]:
        """Generate follow-up queries based on initial findings."""
        try:
            from core.llm import quick_think
            context = "\n".join([f"- {f['title']}: {f['content'][:200]}" for f in findings[:3]])
            prompt = f"""Based on researching "{topic}" with question "{question}", I found:
{context}

Generate 2 follow-up search queries that would deepen understanding. Return just the queries, one per line."""
            result = quick_think(prompt)
            return [q.strip("- ").strip() for q in result.strip().split("\n") if q.strip()][:2]
        except Exception:
            # Fallback: simple query variations
            return [
                f"{topic} best practices 2026",
                f"{topic} vs alternatives comparison",
            ]

    def _synthesize(self, topic: str, question: str, findings: List[Dict]) -> Dict:
        """Use LLM to synthesize research findings into coherent knowledge."""
        try:
            from core.llm import quick_think

            # Prepare research context
            research_text = ""
            for i, f in enumerate(findings[:6], 1):
                research_text += f"\n[Source {i}] {f['title']}\n{f['content'][:500]}\n"

            prompt = f"""You are synthesizing research on: "{topic}"
Question: {question}

Research findings:
{research_text}

Provide:
1. A clear, actionable summary (2-3 paragraphs)
2. Key takeaways (bullet points)
3. Practical applications for someone's daily life/work
4. Confidence level (0.0-1.0) based on source quality and agreement

Format as JSON: {{"summary": "...", "takeaways": [...], "applications": [...], "confidence": 0.X}}"""

            result = quick_think(prompt)

            # Try to parse JSON from response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*"summary"[^{}]*\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except Exception:
                pass

            # Fallback: use raw response as summary
            return {
                "summary": result[:1000],
                "takeaways": [],
                "applications": [],
                "confidence": 0.5,
            }

        except Exception as e:
            # Can't synthesize without LLM — return raw findings
            combined = " ".join([f["content"][:200] for f in findings[:3]])
            return {
                "summary": combined[:800],
                "takeaways": [],
                "applications": [],
                "confidence": 0.3,
            }

    def _store_knowledge(self, task: ResearchTask):
        """Store research findings as persistent knowledge."""
        entry = KnowledgeEntry(
            id=task.id,
            topic=task.topic,
            content=task.synthesis,
            source_urls=task.sources_used,
            confidence=task.confidence,
            tags=[task.topic.lower(), task.source],
            stale_after_days=30 if task.source == "monitor" else 90,
        )
        self._knowledge[task.id] = entry

    def _emit_completion(self, task: ResearchTask):
        """Emit events when research completes."""
        try:
            from core.neural_bus import get_neural_bus, EventPriority

            bus = get_neural_bus()

            # Research complete event
            bus.emit_research(
                topic=task.topic,
                findings={
                    "synthesis": task.synthesis,
                    "confidence": task.confidence,
                    "sources": task.sources_used[:5],
                },
                source="research_engine",
            )

            # If should teach user, emit teaching event
            if task.teach_user and task.confidence >= 0.5:
                bus.emit_teaching(
                    topic=task.topic,
                    content=task.synthesis,
                    source="research_engine",
                )

        except Exception:
            pass

    # ── Topic Monitoring ─────────────────────────────────────────────────────

    def check_monitored_topics(self) -> List[Dict]:
        """Check all monitored topics for updates. Called by heartbeat."""
        updates = []
        now = datetime.now()

        for topic in self._monitored:
            if not topic.active:
                continue

            # Check if due
            if topic.last_checked:
                last = datetime.fromisoformat(topic.last_checked)
                if (now - last).total_seconds() < topic.check_interval_hours * 3600:
                    continue

            # Research the topic
            from core.internet import web_search
            query = f"{topic.topic} {' '.join(topic.keywords[:3])} latest news updates"
            results = web_search(query, max_results=3)

            if results:
                update = {
                    "topic_id": topic.id,
                    "topic": topic.topic,
                    "results": results,
                    "checked_at": now.isoformat(),
                }
                topic.last_checked = now.isoformat()
                topic.findings_history.append(update)
                # Keep last 20 findings
                topic.findings_history = topic.findings_history[-20:]
                updates.append(update)

        if updates:
            self._save_state()

        return updates

    # ── Knowledge Retrieval ──────────────────────────────────────────────────

    def get_knowledge(self, topic: str = None, tag: str = None) -> List[Dict]:
        """Retrieve knowledge entries, optionally filtered."""
        results = []
        for entry in self._knowledge.values():
            if topic and topic.lower() not in entry.topic.lower():
                continue
            if tag and tag not in entry.tags:
                continue
            results.append(asdict(entry))
        return sorted(results, key=lambda x: x["learned_at"], reverse=True)

    def get_relevant_knowledge(self, context: str, limit: int = 3) -> List[Dict]:
        """Get knowledge relevant to a given context (for prompt enrichment)."""
        # Simple keyword matching for now — could use embeddings later
        context_words = set(context.lower().split())
        scored = []
        for entry in self._knowledge.values():
            topic_words = set(entry.topic.lower().split())
            tag_words = set(t.lower() for t in entry.tags)
            overlap = len(context_words & (topic_words | tag_words))
            if overlap > 0:
                scored.append((overlap, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [asdict(e) for _, e in scored[:limit]]

    def enrich_prompt(self, user_input: str) -> str:
        """Generate prompt enrichment from research knowledge."""
        relevant = self.get_relevant_knowledge(user_input, limit=2)
        if not relevant:
            return ""

        lines = ["[RESEARCH KNOWLEDGE — things I've learned from autonomous research]"]
        for entry in relevant:
            lines.append(f"- {entry['topic']}: {entry['content'][:200]}")
            entry_obj = self._knowledge.get(entry['id'])
            if entry_obj:
                entry_obj.times_used += 1

        return "\n".join(lines)

    # ── Background Runner ────────────────────────────────────────────────────

    def start_background(self, interval_minutes: int = 30):
        """Start the background research loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._background_loop, daemon=True, args=(interval_minutes,))
        self._thread.start()

    def stop_background(self):
        """Stop the background research loop."""
        self._running = False

    def _background_loop(self, interval_minutes: int):
        """Background loop: process queue + check monitored topics."""
        from core.activity_log import log_activity
        log_activity("research_engine", "daemon_started", f"Research daemon running every {interval_minutes}min", importance="normal")
        while self._running:
            try:
                # Process one research task
                result = self.execute_next_task()
                if result:
                    print(f"[Research] Completed: {result['topic']} (confidence: {result['confidence']:.0%})")

                # Check monitored topics
                updates = self.check_monitored_topics()
                if updates:
                    print(f"[Research] {len(updates)} topic update(s) found")
                    log_activity("research_engine", "monitored_topics_updated", f"{len(updates)} topic update(s) found", {"updates": len(updates)}, importance="normal")

                # Auto-queue from curiosity gaps
                self._auto_queue_from_gaps()

            except Exception as e:
                print(f"[Research] Error in background loop: {e}")
                log_activity("research_engine", "background_error", f"Background error: {str(e)[:100]}", {"error": str(e)[:200]}, importance="high")

            # Sleep between cycles
            slept = 0
            while slept < interval_minutes * 60 and self._running:
                time.sleep(5)
                slept += 5

    def _auto_queue_from_gaps(self):
        """Automatically queue research tasks from knowledge gaps."""
        try:
            from core.curiosity_engine import get_open_gaps
            gaps = get_open_gaps()
            for gap in gaps[:2]:
                if gap.get("type") == "unclear_goal":
                    self.add_research_task(
                        topic=gap["subject"],
                        question=f"How to {gap['subject']}? Best approaches and tools.",
                        priority=ResearchPriority.MEDIUM,
                        source="curiosity_gap",
                        context=gap.get("context", ""),
                    )
        except Exception:
            pass

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """Get research engine status."""
        from dataclasses import asdict
        return {
            "queued": len([t for t in self._queue if t.status == "queued"]),
            "in_progress": len([t for t in self._queue if t.status == "in_progress"]),
            "completed": len([t for t in self._queue if t.status == "complete"]),
            "knowledge_entries": len(self._knowledge),
            "monitored_topics": len([t for t in self._monitored if t.active]),
            "running": self._running,
            "tasks": [asdict(t) for t in self._queue[-10:]],
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[ResearchEngine] = None


def get_research_engine() -> ResearchEngine:
    """Get the singleton ResearchEngine instance."""
    global _engine
    if _engine is None:
        _engine = ResearchEngine()
    return _engine
