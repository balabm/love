"""
LOVE Feedback Collector — Real user satisfaction as fitness signal.

Captures explicit and implicit feedback from every interaction and feeds it
into lora_evolution.score_adapter() and evolution_engine.record_interaction().

Explicit:
  - /feedback endpoint (thumbs up/down from UI, 1-5 star rating)
  - In-conversation signals: "that was helpful", "you're wrong", "perfect"

Implicit:
  - Session continuation (user keeps talking = positive)
  - Session length vs baseline
  - Response followed by user action (positive)
  - User repeating the same question (negative — LOVE failed to answer)
  - User correction ("no, I meant...") = negative signal

Output:
  - satisfaction_score: float [-1.0, 1.0] per interaction
  - confidence: float [0, 1] (how sure we are of the signal)
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "feedback"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SIGNALS_FILE = DATA_DIR / "signals.jsonl"

# ── Signal vocabulary ─────────────────────────────────────────────────────────

_CORRECTION_PREFIXES = ("no ", "wait ", "actually ", "no,", "wait,", "actually,")
_CORRECTION_PHRASES = ("that's wrong", "you're wrong", "incorrect", "that is wrong",
                       "that's incorrect", "you are wrong", "not right", "that's not right")
_POSITIVE_PHRASES = ("perfect", "exactly", "great", "thanks", "that helps",
                     "brilliant", "yes!", "awesome", "helpful", "love it",
                     "well done", "nice", "spot on", "that's right", "correct",
                     "thank you", "excellent", "wonderful", "amazing")

# Cosine-similarity threshold for repeat-question detection
_REPEAT_SIM_THRESHOLD = 0.85


# ── FeedbackSignal dataclass ──────────────────────────────────────────────────

@dataclass
class FeedbackSignal:
    """A single user-satisfaction signal tied to one interaction."""
    interaction_id: str
    timestamp: float
    satisfaction: float        # -1.0 to 1.0
    confidence: float          # 0.0 to 1.0
    source: str                # "explicit_thumbs", "explicit_rating",
                               # "implicit_continue", "implicit_correction",
                               # "implicit_repeat"
    raw_value: Any             # the raw signal (e.g. "thumbs_up", 4.0, True)

    def to_dict(self) -> dict:
        return {
            "interaction_id": self.interaction_id,
            "timestamp": self.timestamp,
            "satisfaction": self.satisfaction,
            "confidence": self.confidence,
            "source": self.source,
            "raw_value": self.raw_value,
        }


# ── EpisodeRecord dataclass ──────────────────────────────────────────────────

@dataclass
class EpisodeRecord:
    """Aggregated satisfaction record for one session (episode)."""
    episode_id: str                    # uuid
    start_time: float
    end_time: float
    turn_count: int
    satisfaction_arc: List[float]      # per-turn satisfaction values in order
    arc_slope: float                   # linear regression slope (positive = improving)
    peak_satisfaction: float
    valley_satisfaction: float
    net_satisfaction: float            # mean of last 25% of turns (recency-weighted)
    returned_next_session: bool = False  # filled in when next session starts
    episode_fitness: float = 0.0      # computed composite score

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "turn_count": self.turn_count,
            "satisfaction_arc": self.satisfaction_arc,
            "arc_slope": self.arc_slope,
            "peak_satisfaction": self.peak_satisfaction,
            "valley_satisfaction": self.valley_satisfaction,
            "net_satisfaction": self.net_satisfaction,
            "returned_next_session": self.returned_next_session,
            "episode_fitness": self.episode_fitness,
        }


EPISODES_FILE = DATA_DIR / "episodes.jsonl"


# ── Embedding helpers ─────────────────────────────────────────────────────────

def _word_set(text: str) -> set:
    """Simple tokenisation: lowercase words."""
    return set(text.lower().split())


def _word_overlap_sim(a: str, b: str) -> float:
    """Jaccard-like word overlap as fallback similarity in [0, 1]."""
    sa, sb = _word_set(a), _word_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _bow_embed(text: str, dim: int = 256) -> np.ndarray:
    """
    Ultra-lightweight bag-of-chars hashing into a fixed-dim float32 vector.
    Deterministic, no external deps. Good enough for repeat-question detection.
    """
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    for word in words:
        h = hash(word) % dim
        vec[abs(h)] += 1.0
    n = np.linalg.norm(vec)
    return vec / n if n > 1e-8 else vec


def _cosine_sim(a: str, b: str) -> float:
    """Cosine similarity between two texts using BoW hash embedding."""
    try:
        va = _bow_embed(a)
        vb = _bow_embed(b)
        # Both are already L2-normalised by _bow_embed
        return float(np.dot(va, vb))
    except Exception:
        return _word_overlap_sim(a, b)


# ── FeedbackCollector ─────────────────────────────────────────────────────────

class FeedbackCollector:
    """
    Singleton that collects explicit and implicit feedback signals and
    propagates them into the LoRA evolution and autonomous self-improvement
    pipelines as real user-satisfaction fitness signals.
    """

    _instance: Optional["FeedbackCollector"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "FeedbackCollector":
        with cls._instance_lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._initialized = False
                cls._instance = obj
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._lock = threading.Lock()
        self._signals: List[FeedbackSignal] = []   # in-memory ring (last 200)
        self._explicit_count: int = 0
        self._implicit_count: int = 0
        self._last_user_text: str = ""             # for repeat-detection

        # Episode-level tracking
        self._episode_start: float = time.time()
        self._episodes: List[EpisodeRecord] = []

        self._load_recent_signals()
        self._start_episode_watcher()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_recent_signals(self) -> None:
        """Load the last 200 signals from disk for warm-start."""
        try:
            if not SIGNALS_FILE.exists():
                return
            lines = SIGNALS_FILE.read_text(encoding="utf-8").strip().splitlines()
            loaded: List[FeedbackSignal] = []
            for line in lines[-200:]:
                try:
                    d = json.loads(line)
                    loaded.append(FeedbackSignal(**d))
                except Exception:
                    pass
            self._signals = loaded
            self._explicit_count = sum(
                1 for s in loaded if s.source.startswith("explicit"))
            self._implicit_count = sum(
                1 for s in loaded if s.source.startswith("implicit"))
        except Exception:
            pass

    def _persist_signal(self, sig: FeedbackSignal) -> None:
        """Append one signal to signals.jsonl."""
        try:
            with SIGNALS_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(sig.to_dict()) + "\n")
        except Exception:
            pass

    # ── Episode watcher ────────────────────────────────────────────────────────

    def _start_episode_watcher(self) -> None:
        """Background daemon that auto-closes episodes after silence."""
        def _watch():
            while True:
                time.sleep(300)  # check every 5 min
                try:
                    self.maybe_close_episode(silence_minutes=30)
                except Exception:
                    pass
        t = threading.Thread(target=_watch, daemon=True)
        t.start()

    # ── Episode-level satisfaction ────────────────────────────────────────────

    def compute_episode_fitness(self, arc: List[float]) -> float:
        """Composite fitness from a session arc."""
        if len(arc) < 2:
            return arc[0] if arc else 0.0

        # 1. Arc slope (improving = positive) — via linear regression
        n = len(arc)
        xs = np.arange(n, dtype=float)
        slope = float(np.polyfit(xs, arc, 1)[0])

        # 2. Recency-weighted mean (last 25% of session)
        tail_n = max(1, n // 4)
        tail_mean = float(np.mean(arc[-tail_n:]))

        # 3. Peak (best moment in session)
        peak = float(max(arc))

        # 4. Composite: arc trajectory matters most (50%), recency next (30%), peak last (20%)
        fitness = 0.50 * np.clip(slope * 5, -1, 1) + 0.30 * tail_mean + 0.20 * peak
        return float(np.clip(fitness, -1, 1))

    def close_episode(self, session_id: str = None) -> Optional[EpisodeRecord]:
        """
        Called when a session ends (or after N minutes of silence).
        Aggregates all signals since _episode_start into an EpisodeRecord,
        computes episode_fitness, updates LoRA, and resets the episode buffer.
        """
        with self._lock:
            episode_signals = [
                s for s in self._signals if s.timestamp >= self._episode_start
            ]
            # Fallback: if no signals pass timestamp filter (e.g. historical
            # timestamps loaded from disk), use all un-episodized signals
            if not episode_signals and self._signals:
                episode_signals = list(self._signals)

        if not episode_signals:
            return None

        # Build satisfaction arc (satisfaction * confidence per turn)
        satisfaction_arc = [
            s.satisfaction * s.confidence for s in episode_signals
        ]

        n = len(satisfaction_arc)

        # Arc slope via linear regression
        if n >= 2:
            xs = np.arange(n, dtype=float)
            arc_slope = float(np.polyfit(xs, satisfaction_arc, 1)[0])
        else:
            arc_slope = 0.0

        # Peak and valley
        peak_satisfaction = float(max(satisfaction_arc))
        valley_satisfaction = float(min(satisfaction_arc))

        # Net satisfaction: mean of last 25% of turns
        tail_n = max(1, n // 4)
        net_satisfaction = float(np.mean(satisfaction_arc[-tail_n:]))

        # Episode fitness
        episode_fitness = self.compute_episode_fitness(satisfaction_arc)

        # Mark returned_next_session on previous episode if it exists
        if self._episodes:
            self._episodes[-1].returned_next_session = True

        # Create the episode record
        record = EpisodeRecord(
            episode_id=str(uuid.uuid4()),
            start_time=self._episode_start,
            end_time=time.time(),
            turn_count=n,
            satisfaction_arc=satisfaction_arc,
            arc_slope=round(arc_slope, 6),
            peak_satisfaction=round(peak_satisfaction, 4),
            valley_satisfaction=round(valley_satisfaction, 4),
            net_satisfaction=round(net_satisfaction, 4),
            returned_next_session=False,
            episode_fitness=round(episode_fitness, 4),
        )

        self._episodes.append(record)

        # Persist to episodes.jsonl
        try:
            with EPISODES_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict()) + "\n")
        except Exception:
            pass

        # Propagate episode-level signal to LoRA evolution (higher confidence)
        try:
            from core.lora_evolution import get_lora_evolution
            get_lora_evolution().receive_feedback(episode_fitness, confidence=0.85)
        except Exception:
            pass

        # Reset episode buffer
        self._episode_start = time.time()

        return record

    def maybe_close_episode(self, silence_minutes: float = 30.0) -> None:
        """Auto-close if last signal was > silence_minutes ago."""
        if not self._signals:
            return
        last_ts = max(s.timestamp for s in self._signals[-20:])
        if time.time() - last_ts > silence_minutes * 60:
            self.close_episode()

    # ── Public API ────────────────────────────────────────────────────────────

    def record_explicit(
        self,
        interaction_id: str,
        rating: float,
        source: str = "explicit",
    ) -> FeedbackSignal:
        """
        Record an explicit satisfaction signal.

        Args:
            interaction_id: Unique ID for the interaction being rated.
            rating: Float in [0, 1] — 1.0 = fully positive, 0.0 = fully negative.
                    Also accepts 1-5 star scale if value > 1 (auto-normalised).
            source: One of "explicit_thumbs", "explicit_rating", or "explicit".

        Returns:
            The resulting FeedbackSignal.
        """
        # Normalise 1-5 star → [0, 1]
        if rating > 1.0:
            rating = (rating - 1.0) / 4.0  # maps 1→0, 5→1

        rating = float(np.clip(rating, 0.0, 1.0))
        satisfaction = 2.0 * rating - 1.0   # maps [0,1] → [-1,1]

        sig = FeedbackSignal(
            interaction_id=interaction_id,
            timestamp=time.time(),
            satisfaction=round(satisfaction, 4),
            confidence=0.95,
            source=source if source.startswith("explicit") else f"explicit_{source}",
            raw_value=rating,
        )

        with self._lock:
            self._signals.append(sig)
            if len(self._signals) > 200:
                self._signals = self._signals[-200:]
            self._explicit_count += 1

        self._persist_signal(sig)
        self._propagate(sig)
        return sig

    def detect_implicit(
        self,
        user_text: str,
        prev_user_text: str,
        response_text: str,
        session_turn: int,
    ) -> Optional[FeedbackSignal]:
        """
        Detect an implicit satisfaction signal from the conversation context.

        Detection priority (first match wins):
          1. Correction signal  → satisfaction = -0.7, confidence = 0.8
          2. Positive signal    → satisfaction = +0.6, confidence = 0.6
          3. Repeat question    → satisfaction = -0.5, confidence = 0.7
          4. Continuation       → satisfaction = +0.2, confidence = 0.4

        Returns:
            FeedbackSignal or None if no signal detected.
        """
        if not user_text:
            return None

        ul = user_text.lower().strip()
        interaction_id = str(uuid.uuid4())
        sig: Optional[FeedbackSignal] = None

        # ── 1. Correction ─────────────────────────────────────────────────────
        is_correction = any(ul.startswith(pfx) for pfx in _CORRECTION_PREFIXES)
        if not is_correction:
            is_correction = any(phrase in ul for phrase in _CORRECTION_PHRASES)

        if is_correction:
            sig = FeedbackSignal(
                interaction_id=interaction_id,
                timestamp=time.time(),
                satisfaction=-0.7,
                confidence=0.8,
                source="implicit_correction",
                raw_value=user_text[:120],
            )

        # ── 2. Positive signal ────────────────────────────────────────────────
        elif any(phrase in ul for phrase in _POSITIVE_PHRASES):
            sig = FeedbackSignal(
                interaction_id=interaction_id,
                timestamp=time.time(),
                satisfaction=0.6,
                confidence=0.6,
                source="implicit_positive",
                raw_value=user_text[:120],
            )

        # ── 3. Repeat question (semantic similarity to prev message) ──────────
        elif (
            prev_user_text
            and session_turn > 1
            and _cosine_sim(user_text, prev_user_text) > _REPEAT_SIM_THRESHOLD
        ):
            sig = FeedbackSignal(
                interaction_id=interaction_id,
                timestamp=time.time(),
                satisfaction=-0.5,
                confidence=0.7,
                source="implicit_repeat",
                raw_value={"current": user_text[:80], "prev": prev_user_text[:80]},
            )

        # ── 4. Continuation (weak positive: user is still engaged) ────────────
        elif len(user_text) > 20 and session_turn > 3:
            sig = FeedbackSignal(
                interaction_id=interaction_id,
                timestamp=time.time(),
                satisfaction=0.2,
                confidence=0.4,
                source="implicit_continue",
                raw_value=session_turn,
            )

        if sig is not None:
            with self._lock:
                self._signals.append(sig)
                if len(self._signals) > 200:
                    self._signals = self._signals[-200:]
                self._implicit_count += 1
            self._persist_signal(sig)
            self._propagate(sig)

        return sig

    # ── Propagation ───────────────────────────────────────────────────────────

    def _propagate(self, signal: FeedbackSignal) -> None:
        """
        Push the satisfaction signal into all downstream fitness systems:
          - EvolutionEngine.record_interaction()
          - LoRAEvolution.receive_feedback()
          - AutonomousSelfImprovement.receive_feedback()
        All failures are silently swallowed — never crash a conversation.
        """
        # 1. Evolution engine — existing user_satisfaction param
        try:
            from core.evolution_engine import get_evolution_engine
            get_evolution_engine().record_interaction(
                user_satisfaction=signal.satisfaction,
            )
        except Exception:
            pass

        # 2. LoRA evolution — new receive_feedback hook
        try:
            from core.lora_evolution import get_lora_evolution
            get_lora_evolution().receive_feedback(signal.satisfaction, signal.confidence)
        except Exception:
            pass

        # 3. Autonomous self-improvement — new receive_feedback hook
        try:
            from core.autonomous_self_improvement import get_autonomous_self_improvement
            get_autonomous_self_improvement().receive_feedback(signal)
        except Exception:
            pass

    # ── Query helpers ─────────────────────────────────────────────────────────

    def get_recent_satisfaction(self, n: int = 20) -> float:
        """
        Average satisfaction of the last N signals.
        Returns 0.0 if no signals have been recorded yet.
        """
        with self._lock:
            recent = list(self._signals[-n:])
        if not recent:
            return 0.0
        return float(np.mean([s.satisfaction for s in recent]))

    def snapshot(self) -> dict:
        """
        Summary of current feedback state — suitable for dashboards.
        """
        with self._lock:
            total = len(self._signals)
            explicit = self._explicit_count
            implicit = self._implicit_count
            last_ts = self._signals[-1].timestamp if self._signals else None
            current_episode_turns = len(
                [s for s in self._signals if s.timestamp >= self._episode_start]
            )

        return {
            "total_signals": total,
            "recent_satisfaction": round(self.get_recent_satisfaction(), 4),
            "explicit_count": explicit,
            "implicit_count": implicit,
            "last_signal_timestamp": last_ts,
            "episodes_total": len(self._episodes),
            "last_episode_fitness": self._episodes[-1].episode_fitness if self._episodes else None,
            "current_episode_turns": current_episode_turns,
        }


# ── Singleton accessor ────────────────────────────────────────────────────────

_fc_instance: Optional[FeedbackCollector] = None
_fc_lock = threading.Lock()


def get_feedback_collector() -> FeedbackCollector:
    """Return the process-wide FeedbackCollector singleton."""
    global _fc_instance
    if _fc_instance is None:
        with _fc_lock:
            if _fc_instance is None:
                _fc_instance = FeedbackCollector()
    return _fc_instance
