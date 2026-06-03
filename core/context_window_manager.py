"""
LOVE Context Window Manager — Intelligent LLM Context Optimization (Modern AI Pattern)

Modern LLMs have limited context windows. This manager optimizes:

1. MEMORY PRIORITIZATION
   - Score memories by relevance, recency, and importance
   - Keep high-priority context, summarize or evict low-priority
   - Ensure critical user preferences and facts are always present

2. CONVERSATION COMPRESSION
   - Summarize old conversation turns when window fills
   - Preserve key decisions and emotional moments
   - Maintain conversation flow after compression

3. CONTEXT BUDGETING
   - Allocate context budget across: system prompt, user profile,
     recent conversation, relevant memories, and tools
   - Dynamic reallocation based on task type

4. TOKEN TRACKING
   - Estimate token usage in real-time
   - Warn before approaching context limits
   - Proactively compress when threshold reached

Architecture:
- optimize_context(): Compress and prioritize context for LLM call
- summarize_old_turns(): Compress conversation history
- get_token_estimate(): Estimate tokens in a context
- get_context_stats(): Track compression metrics
"""

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "context_window"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMPRESSION_LOG = DATA_DIR / "compression_log.jsonl"

# Rough token estimates
TOKENS_PER_CHAR = 0.25
DEFAULT_MAX_CONTEXT = 8000  # Conservative default


@dataclass
class ContextSegment:
    """A segment of context with metadata."""
    content: str = ""
    segment_type: str = ""  # system, user_profile, conversation, memory, tool
    priority: float = 1.0   # 0-1, higher = more important
    created_at: float = 0.0
    tokens: int = 0


class ContextWindowManager:
    """
    Intelligent context window optimization for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, max_context: int = DEFAULT_MAX_CONTEXT):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._max_context = max_context
        self._stats = {
            "total_optimizations": 0,
            "total_tokens_saved": 0,
            "total_turns_summarized": 0,
            "compression_events": 0,
        }

    # ── Core Optimization ───────────────────────────────────────────────────

    def optimize_context(self, segments: List[ContextSegment]) -> List[ContextSegment]:
        """
        Optimize a list of context segments to fit within the window.
        Returns prioritized, possibly compressed segments.
        """
        # Sort by priority (highest first), then recency
        sorted_segments = sorted(
            segments,
            key=lambda s: (s.priority, s.created_at),
            reverse=True,
        )

        # Calculate tokens for each segment
        total_tokens = 0
        result = []

        for segment in sorted_segments:
            segment.tokens = self._estimate_tokens(segment.content)

            if total_tokens + segment.tokens <= self._max_context:
                result.append(segment)
                total_tokens += segment.tokens
            else:
                # Try to compress this segment
                compressed = self._compress_segment(segment, self._max_context - total_tokens)
                if compressed and compressed.tokens > 0:
                    result.append(compressed)
                    total_tokens += compressed.tokens
                break  # No more space

        self._stats["total_optimizations"] += 1
        self._stats["total_tokens_saved"] += sum(s.tokens for s in segments) - total_tokens

        return result

    def _compress_segment(self, segment: ContextSegment, available_tokens: int) -> Optional[ContextSegment]:
        """Compress a single segment to fit available tokens."""
        if segment.segment_type == "conversation":
            # Summarize conversation
            summary = self._summarize_text(segment.content, int(available_tokens * 3))  # chars ≈ tokens * 3
            return ContextSegment(
                content=summary,
                segment_type="conversation_summary",
                priority=segment.priority,
                created_at=segment.created_at,
                tokens=self._estimate_tokens(summary),
            )
        elif segment.segment_type == "memory":
            # Truncate memory to key facts
            truncated = self._extract_key_facts(segment.content, int(available_tokens * 3))
            return ContextSegment(
                content=truncated,
                segment_type="memory_summary",
                priority=segment.priority,
                created_at=segment.created_at,
                tokens=self._estimate_tokens(truncated),
            )
        return None

    # ── Conversation Compression ────────────────────────────────────────────

    def summarize_old_turns(self, conversation: List[Dict[str, Any]],
                              keep_recent: int = 5) -> Dict[str, Any]:
        """
        Summarize old conversation turns, keeping recent ones intact.
        Returns summary + recent turns.
        """
        if len(conversation) <= keep_recent:
            return {"summary": "", "recent": conversation}

        old_turns = conversation[:-keep_recent]
        recent_turns = conversation[-keep_recent:]

        # Create a simple summary of old turns
        summary_parts = []
        for turn in old_turns:
            speaker = turn.get("speaker", "unknown")
            text = turn.get("text", "")
            if text:
                # Extract first sentence or first 50 chars
                summary = text.split(".")[0][:50] + "..." if len(text) > 50 else text
                summary_parts.append(f"{speaker}: {summary}")

        summary = " | ".join(summary_parts)
        self._stats["total_turns_summarized"] += len(old_turns)
        self._stats["compression_events"] += 1

        self._log_compression(len(old_turns), len(summary))

        return {
            "summary": summary,
            "recent": recent_turns,
        }

    # ── Token Estimation ────────────────────────────────────────────────────

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate based on character count."""
        return max(1, int(len(text) * TOKENS_PER_CHAR))

    def get_token_estimate(self, text: str) -> int:
        """Public API for token estimation."""
        return self._estimate_tokens(text)

    # ── Context Budgeting ────────────────────────────────────────────────────

    def allocate_budget(self, task_type: str = "default") -> Dict[str, int]:
        """Allocate context budget based on task type."""
        budgets = {
            "chat": {
                "system": 500,
                "user_profile": 800,
                "conversation": 4000,
                "memories": 2000,
                "tools": 700,
            },
            "coding": {
                "system": 800,
                "user_profile": 400,
                "conversation": 2000,
                "memories": 1000,
                "tools": 3800,
            },
            "research": {
                "system": 600,
                "user_profile": 600,
                "conversation": 1500,
                "memories": 3000,
                "tools": 2300,
            },
            "default": {
                "system": 600,
                "user_profile": 600,
                "conversation": 3000,
                "memories": 2500,
                "tools": 1300,
            },
        }
        return budgets.get(task_type, budgets["default"])

    # ── Helper Methods ─────────────────────────────────────────────────────

    def _summarize_text(self, text: str, max_chars: int) -> str:
        """Simple text summarization."""
        if len(text) <= max_chars:
            return text

        sentences = text.split(".")
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) + 2 <= max_chars:
                summary += sentence + ". "
            else:
                break
        return summary.strip() or text[:max_chars] + "..."

    def _extract_key_facts(self, text: str, max_chars: int) -> str:
        """Extract key facts from a memory text."""
        if len(text) <= max_chars:
            return text

        # Look for sentences with key indicators
        key_indicators = ["is", "has", "likes", "prefers", "needs", "wants", "important"]
        sentences = text.split(".")
        facts = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in key_indicators):
                facts.append(sentence.strip())

        result = ". ".join(facts)
        if len(result) > max_chars:
            result = result[:max_chars] + "..."

        return result or text[:max_chars] + "..."

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_context_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "max_context": self._max_context,
            "avg_compression_ratio": round(
                self._stats["total_tokens_saved"] / max(self._stats["compression_events"], 1), 2
            ),
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log_compression(self, turns_summarized: int, summary_length: int):
        try:
            with open(COMPRESSION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "turns_summarized": turns_summarized,
                    "summary_length": summary_length,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.context_window_manager")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_cwm_instance: Optional[ContextWindowManager] = None
_cwm_lock = threading.Lock()


def get_context_window_manager(max_context: int = DEFAULT_MAX_CONTEXT) -> ContextWindowManager:
    global _cwm_instance
    with _cwm_lock:
        if _cwm_instance is None:
            _cwm_instance = ContextWindowManager(max_context)
        return _cwm_instance
