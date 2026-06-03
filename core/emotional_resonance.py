"""
LOVE Emotional Resonance Engine — Deep Emotional Pattern Analysis

This isn't surface-level sentiment scoring. LOVE reads between the lines:
sarcasm that sounds cheerful but stings, the quiet flattening before burnout,
the barely-contained excitement the user hasn't admitted to themselves yet.

Capabilities:
- analyze_emotional_depth(): Detect subtle emotional cues beyond obvious sentiment
- detect_emotional_shifts(): Spot sudden changes in the user's emotional baseline
- measure_resonance(): Score how well LOVE's response actually landed emotionally
- get_emotional_forecast(): Predict where the user's emotional trajectory is heading
- get_resonance_stats(): Engine usage and accuracy statistics

All data stored in data/emotional_resonance/ for proactive recall and alerts.
"""

import json
import math
import re
import threading
import time
import uuid
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "emotional_resonance"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DB = DATA_DIR / "emotional_history.json"
STATS_DB = DATA_DIR / "resonance_stats.json"


@dataclass
class EmotionalState:
    """A snapshot of the user's emotional state at a point in time."""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_text: str = ""

    # Surface dimensions
    valence: float = 0.0  # -1 (negative) to +1 (positive)
    arousal: float = 0.0  # 0 (flat) to 1 (activated)
    dominance: float = 0.5  # 0 (submissive/helpless) to 1 (in control)

    # Deep dimensions
    sarcasm: float = 0.0
    suppressed_frustration: float = 0.0
    growing_anxiety: float = 0.0
    hidden_excitement: float = 0.0
    emotional_numbness: float = 0.0
    defensiveness: float = 0.0
    vulnerability: float = 0.0
    masked_distress: float = 0.0

    # Computed
    primary_emotion: str = "neutral"
    depth_score: float = 0.0  # How much is unsaid
    transparency: float = 1.0  # 1 = what you see is what you get, 0 = heavily masked


@dataclass
class ResonanceReading:
    """How well a LOVE response resonated with the user."""
    reading_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_text: str = ""
    love_response: str = ""
    emotional_match: float = 0.0  # Did LOVE match the user's emotional register
    validation_felt: float = 0.0  # Did the user feel seen
    tone_alignment: float = 0.0  # Was LOVE's tone appropriate
    depth_reciprocity: float = 0.0  # Did LOVE meet the depth of the moment
    overall_resonance: float = 0.0
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ShiftAlert:
    """An alert about a meaningful emotional shift."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    shift_type: str = ""  # e.g., "energy_drop", "irritability_spike", "withdrawal"
    severity: float = 0.5  # 0-1
    description: str = ""
    previous_state_id: str = ""
    current_state_id: str = ""
    recommendation: str = ""


class EmotionalResonanceEngine:
    """
    Deep emotional analysis engine for LOVE.
    Reads what the user says, what they don't say, and how they change over time.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._history: deque = deque(maxlen=500)
        self._readings: deque = deque(maxlen=500)
        self._alerts: deque = deque(maxlen=100)
        self._stats = {
            "analyses_run": 0,
            "shifts_detected": 0,
            "readings_taken": 0,
            "forecasts_made": 0,
            "alerts_issued": 0,
            "created_at": datetime.now().isoformat(),
        }
        self._load_data()

    # ── Core Analysis ──────────────────────────────────────────────────────────

    def analyze_emotional_depth(self, text: str) -> EmotionalState:
        """
        Deep emotional analysis beyond surface sentiment.
        Detects sarcasm, suppressed frustration, growing anxiety,
        hidden excitement, and other masked emotions.
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)

        state = EmotionalState(raw_text=text[:500])

        # ── Surface valence ──
        positive_words = {
            "good", "great", "awesome", "love", "happy", "excited", "amazing",
            "wonderful", "best", "fantastic", "brilliant", "perfect", "yes",
            "thanks", "thank", "appreciate", "nice", "cool", "solid",
        }
        negative_words = {
            "bad", "terrible", "awful", "hate", "sad", "angry", "frustrated",
            "annoying", "worst", "horrible", "disappointing", "no", "never",
            "stupid", "ridiculous", "pathetic", "useless", "broken", "fail",
        }
        pos_count = sum(1 for w in words if w.strip(".,!?;:") in positive_words)
        neg_count = sum(1 for w in words if w.strip(".,!?;:") in negative_words)

        state.valence = self._clamp((pos_count - neg_count) / max(word_count, 1) * 3, -1.0, 1.0)
        if pos_count == 0 and neg_count == 0:
            state.valence = 0.0

        # ── Arousal (energy level) ──
        high_arousal = {"!", "wow", "omg", "incredible", "shocking", "furious", "ecstatic"}
        low_arousal = {"tired", "exhausted", "numb", "flat", "whatever", "meh", "fine"}
        arousal_score = 0.5
        if any(w in text_lower for w in high_arousal):
            arousal_score = 0.8
        if any(w in text_lower for w in low_arousal):
            arousal_score = 0.2
        # Punctuation density as arousal signal
        excl_ratio = text.count("!") / max(word_count, 1)
        arousal_score += excl_ratio * 0.3
        state.arousal = self._clamp(arousal_score, 0.0, 1.0)

        # ── Sarcasm detection ──
        state.sarcasm = self._detect_sarcasm(text, state.valence)

        # ── Suppressed frustration ──
        state.suppressed_frustration = self._detect_suppressed_frustration(text)

        # ── Growing anxiety ──
        state.growing_anxiety = self._detect_growing_anxiety(text)

        # ── Hidden excitement ──
        state.hidden_excitement = self._detect_hidden_excitement(text, state.valence)

        # ── Emotional numbness ──
        state.emotional_numbness = self._detect_numbness(text, state.arousal)

        # ── Defensiveness ──
        state.defensiveness = self._detect_defensiveness(text)

        # ── Vulnerability ──
        state.vulnerability = self._detect_vulnerability(text)

        # ── Masked distress ──
        state.masked_distress = self._detect_masked_distress(text, state.valence, state.arousal)

        # ── Dominance (sense of control) ──
        control_words = {"can", "will", "going to", "plan", "handle", "manage"}
        helpless_words = {"can't", "cannot", "won't", "impossible", "stuck", "trapped"}
        ctrl = sum(1 for w in control_words if w in text_lower)
        hlp = sum(1 for w in helpless_words if w in text_lower)
        state.dominance = self._clamp(0.5 + (ctrl - hlp) * 0.15, 0.0, 1.0)

        # ── Compute aggregate scores ──
        deep_signals = [
            state.sarcasm, state.suppressed_frustration, state.growing_anxiety,
            state.hidden_excitement, state.emotional_numbness, state.defensiveness,
            state.vulnerability, state.masked_distress,
        ]
        state.depth_score = round(sum(deep_signals) / len(deep_signals), 3)
        # Transparency: high if surface valence matches deep signals
        # Low transparency = surface says one thing, depth says another
        surface_positive = state.valence > 0.2
        surface_negative = state.valence < -0.2
        deep_negative = any(s > 0.5 for s in [state.suppressed_frustration, state.growing_anxiety, state.masked_distress])
        deep_positive = state.hidden_excitement > 0.5
        mismatch = (surface_positive and deep_negative) or (surface_negative and deep_positive)
        state.transparency = round(0.2 if mismatch else 0.8, 3)

        # Primary emotion label
        state.primary_emotion = self._label_primary_emotion(state)

        with self._lock:
            self._history.append(state)
        self._stats["analyses_run"] += 1
        self._save_data()

        return state

    def detect_emotional_shifts(self, history: Optional[List[EmotionalState]] = None) -> List[ShiftAlert]:
        """
        Compare recent emotional states to detect meaningful shifts.
        E.g., sudden drop in energy, unusual irritability, withdrawal patterns.
        """
        if history is None:
            with self._lock:
                states = list(self._history)
        else:
            states = history

        if len(states) < 2:
            return []

        alerts = []
        # Compare last state with the window before it
        recent_window = states[-5:-1] if len(states) >= 5 else states[:-1]
        current = states[-1]

        if not recent_window:
            return []

        avg_valence = sum(s.valence for s in recent_window) / len(recent_window)
        avg_arousal = sum(s.arousal for s in recent_window) / len(recent_window)
        avg_frustration = sum(s.suppressed_frustration for s in recent_window) / len(recent_window)
        avg_anxiety = sum(s.growing_anxiety for s in recent_window) / len(recent_window)

        # Shift 1: Sudden energy drop
        if avg_arousal - current.arousal > 0.3 and current.arousal < 0.4:
            severity = self._clamp((avg_arousal - current.arousal) * 2, 0.0, 1.0)
            alert = ShiftAlert(
                shift_type="energy_drop",
                severity=round(severity, 3),
                description="User's energy dropped noticeably compared to recent baseline.",
                previous_state_id=recent_window[-1].state_id,
                current_state_id=current.state_id,
                recommendation="Check in gently. Ask if something drained them, or if they need a break.",
            )
            alerts.append(alert)

        # Shift 2: Irritability spike
        if current.suppressed_frustration - avg_frustration > 0.25 and current.suppressed_frustration > 0.5:
            severity = self._clamp((current.suppressed_frustration - avg_frustration) * 3, 0.0, 1.0)
            alert = ShiftAlert(
                shift_type="irritability_spike",
                severity=round(severity, 3),
                description="Frustration signals are elevated above the user's recent baseline.",
                previous_state_id=recent_window[-1].state_id,
                current_state_id=current.state_id,
                recommendation="Give space. Don't push for productivity. Acknowledge if they vent.",
            )
            alerts.append(alert)

        # Shift 3: Withdrawal / numbness
        if current.emotional_numbness > 0.5 and avg_arousal > 0.4:
            alert = ShiftAlert(
                shift_type="withdrawal",
                severity=round(current.emotional_numbness, 3),
                description="User seems emotionally withdrawn or numb despite previous engagement.",
                previous_state_id=recent_window[-1].state_id,
                current_state_id=current.state_id,
                recommendation="This is often a protective response. Keep it light. Offer a low-stakes check-in.",
            )
            alerts.append(alert)

        # Shift 4: Anxiety surge
        if current.growing_anxiety - avg_anxiety > 0.25 and current.growing_anxiety > 0.5:
            alert = ShiftAlert(
                shift_type="anxiety_surge",
                severity=round(current.growing_anxiety, 3),
                description="Anxiety markers have climbed above the recent baseline.",
                previous_state_id=recent_window[-1].state_id,
                current_state_id=current.state_id,
                recommendation="Name it softly if appropriate. Offer grounding or practical next-step clarity.",
            )
            alerts.append(alert)

        # Shift 5: Sudden positivity spike (might be masking)
        if current.valence - avg_valence > 0.4 and current.transparency < 0.5:
            alert = ShiftAlert(
                shift_type="masked_positivity",
                severity=round(1.0 - current.transparency, 3),
                description="Sharp positive shift, but low transparency suggests it may be performative.",
                previous_state_id=recent_window[-1].state_id,
                current_state_id=current.state_id,
                recommendation="Don't challenge it directly. Stay available. They may reveal more when ready.",
            )
            alerts.append(alert)

        with self._lock:
            for a in alerts:
                self._alerts.append(a)
        self._stats["shifts_detected"] += len(alerts)
        self._stats["alerts_issued"] += len(alerts)
        self._save_data()

        return alerts

    def measure_resonance(self, user_text: str, love_response: str) -> ResonanceReading:
        """
        Measure how well LOVE's response resonated emotionally with the user.
        This is LOVE's emotional mirror: did we meet them where they were?
        """
        user_state = self.analyze_emotional_depth(user_text)
        response_lower = love_response.lower()
        response_words = set(response_lower.split())

        reading = ResonanceReading(user_text=user_text[:500], love_response=love_response[:500])

        # Emotional match: did LOVE's tone align with user's valence?
        positive_response = {"good", "great", "happy", "excited", "love", "awesome", "nice"}
        negative_response = {"sorry", "hard", "tough", "difficult", "sad", "frustrating", "bad"}
        neutral_response = {"understand", "see", "hear", "okay", "sure"}

        pos_r = sum(1 for w in positive_response if w in response_lower)
        neg_r = sum(1 for w in negative_response if w in response_lower)
        neu_r = sum(1 for w in neutral_response if w in response_lower)

        response_valence = self._clamp((pos_r - neg_r) / max(pos_r + neg_r + neu_r, 1), -1.0, 1.0)

        # Match: closer valence = better match, but with nuance
        if user_state.valence < -0.3 and response_valence > 0.3:
            # User negative, LOVE overly positive = toxic positivity
            reading.emotional_match = 0.2
        elif user_state.valence < -0.3 and response_valence < 0.0:
            # User negative, LOVE acknowledges = good match
            reading.emotional_match = 0.8
        elif user_state.valence > 0.3 and response_valence > 0.0:
            # Both positive = good
            reading.emotional_match = 0.85
        elif abs(user_state.valence - response_valence) < 0.3:
            reading.emotional_match = 0.75
        else:
            reading.emotional_match = 0.45

        # Validation: did LOVE acknowledge the user's specific emotional state?
        validation_cues = {
            "sounds like", "seems like", "you seem", "you sound", "i can tell",
            "you're feeling", "that sounds", "that must", "i hear that",
        }
        validated = any(cue in response_lower for cue in validation_cues)
        reading.validation_felt = 0.85 if validated else 0.4

        # Depth reciprocity: did LOVE match the depth of the user's emotional moment?
        user_depth = user_state.depth_score
        response_depth = self._score_response_depth(love_response)
        reading.depth_reciprocity = 1.0 - abs(user_depth - response_depth)

        # Tone alignment: was the tone appropriate to the context?
        if user_state.sarcasm > 0.5 and "sure" in response_lower and "great" in response_lower:
            # LOVE might be missing the sarcasm
            reading.tone_alignment = 0.3
        elif user_state.growing_anxiety > 0.5 and any(w in response_lower for w in {"relax", "calm down", "chill"}):
            # Dismissive response to anxiety
            reading.tone_alignment = 0.25
        elif user_state.suppressed_frustration > 0.5 and any(w in response_lower for w in {"help", "let's", "together"}):
            reading.tone_alignment = 0.85
        else:
            reading.tone_alignment = 0.7

        # Overall resonance: weighted composite
        reading.overall_resonance = round(
            reading.emotional_match * 0.25 +
            reading.validation_felt * 0.30 +
            reading.tone_alignment * 0.25 +
            reading.depth_reciprocity * 0.20,
            3
        )

        # Suggestions for improvement
        suggestions = []
        if reading.emotional_match < 0.5:
            suggestions.append("Tone mismatch: match the user's emotional register more closely.")
        if reading.validation_felt < 0.5:
            suggestions.append("Validation missing: explicitly acknowledge what the user is feeling.")
        if reading.depth_reciprocity < 0.5:
            suggestions.append("Depth gap: the user's emotional moment was deeper than the response.")
        if reading.tone_alignment < 0.5:
            suggestions.append("Tone risk: the response could feel dismissive or inappropriate.")
        reading.suggestions = suggestions

        with self._lock:
            self._readings.append(reading)
        self._stats["readings_taken"] += 1
        self._save_data()

        return reading

    def get_emotional_forecast(self, lookback_turns: int = 10) -> Dict[str, Any]:
        """
        Predict emotional trajectory based on recent patterns.
        Returns forecast with confidence and recommended proactive action.
        """
        with self._lock:
            states = list(self._history)[-lookback_turns:]

        if len(states) < 3:
            return {
                "forecast": "insufficient_data",
                "confidence": 0.0,
                "message": "Not enough history for a reliable forecast.",
                "recommended_action": "Keep observing. No pattern yet.",
                "trend": "flat",
            }

        # Simple linear trend on valence and arousal
        valences = [s.valence for s in states]
        arousals = [s.arousal for s in states]
        anxieties = [s.growing_anxiety for s in states]
        frustrations = [s.suppressed_frustration for s in states]

        valence_trend = valences[-1] - valences[0]
        arousal_trend = arousals[-1] - arousals[0]
        anxiety_trend = anxieties[-1] - anxieties[0]
        frustration_trend = frustrations[-1] - frustrations[0]

        # Volatility
        valence_volatility = sum(abs(valences[i] - valences[i - 1]) for i in range(1, len(valences))) / max(len(valences) - 1, 1)

        forecast = {
            "valence_trend": round(valence_trend, 3),
            "arousal_trend": round(arousal_trend, 3),
            "anxiety_trend": round(anxiety_trend, 3),
            "frustration_trend": round(frustration_trend, 3),
            "volatility": round(valence_volatility, 3),
        }

        # Determine trajectory label
        if valence_trend < -0.3 and anxiety_trend > 0.2:
            trajectory = "declining_mood_rising_stress"
            confidence = min(0.9, 0.6 + abs(valence_trend))
            message = "User's mood is trending down while stress markers rise."
            action = "Proactively suggest a break, a small win, or ask what's weighing on them."
        elif valence_trend > 0.3 and arousal_trend > 0.1:
            trajectory = "improving_mood"
            confidence = min(0.85, 0.6 + valence_trend)
            message = "User's emotional state is improving. Good time to build momentum."
            action = "Encourage and reinforce. This is a window for tackling harder tasks."
        elif valence_volatility > 0.3:
            trajectory = "unstable"
            confidence = min(0.8, 0.5 + valence_volatility)
            message = "Emotional state is volatile — rapid shifts between tones."
            action = "Stay consistent and grounding. Don't overreact to any single turn."
        elif abs(valence_trend) < 0.15 and abs(arousal_trend) < 0.15:
            trajectory = "stable"
            confidence = 0.7
            message = "Emotional baseline is steady."
            action = "Maintain current approach. Watch for any early shift signals."
        elif arousal_trend < -0.3:
            trajectory = "energy_depletion"
            confidence = min(0.85, 0.6 + abs(arousal_trend))
            message = "Energy is draining. User may be approaching a limit."
            action = "Suggest winding down, food, movement, or sleep prep."
        else:
            trajectory = "mixed_signals"
            confidence = 0.5
            message = "Signals are mixed. No clear trajectory yet."
            action = "Stay attentive. No major intervention needed, but keep observing."

        self._stats["forecasts_made"] += 1
        self._save_data()

        return {
            "forecast": trajectory,
            "confidence": round(confidence, 3),
            "message": message,
            "recommended_action": action,
            "trend": "down" if valence_trend < -0.15 else "up" if valence_trend > 0.15 else "flat",
            "details": forecast,
            "based_on_n_turns": len(states),
        }

    def get_resonance_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        with self._lock:
            avg_resonance = 0.0
            if self._readings:
                avg_resonance = sum(r.overall_resonance for r in self._readings) / len(self._readings)

            recent_alerts = list(self._alerts)[-10:]

            return {
                "engine": "emotional_resonance",
                "version": "1.0",
                "stats": self._stats.copy(),
                "history_size": len(self._history),
                "readings_count": len(self._readings),
                "alerts_count": len(self._alerts),
                "average_resonance_score": round(avg_resonance, 3),
                "recent_alerts": [
                    {
                        "type": a.shift_type,
                        "severity": a.severity,
                        "description": a.description,
                        "timestamp": a.timestamp,
                    }
                    for a in recent_alerts
                ],
                "last_updated": datetime.now().isoformat(),
            }

    # ── Internal Detectors ───────────────────────────────────────────────────

    def _detect_sarcasm(self, text: str, surface_valence: float) -> float:
        """Detect sarcastic tone — positive words with negative context."""
        text_lower = text.lower()
        score = 0.0

        # Classic sarcasm markers
        sarcasm_phrases = [
            "great", "awesome", "perfect", "wonderful", "fantastic",
            "just what i needed", "oh joy", "sure thing", "lovely",
        ]
        for phrase in sarcasm_phrases:
            if phrase in text_lower:
                score += 0.25

        # Excessive positivity after a negative statement
        if surface_valence > 0.3 and any(w in text_lower for w in {"but", "except", "however", "although"}):
            score += 0.2

        # Over-punctuation can signal sarcasm
        if text.count("!") > 2 and surface_valence > 0.3:
            score += 0.15

        # Specific dismissive patterns
        dismissive = {"yeah right", "sure sure", "of course", "obviously", "tell me about it"}
        for d in dismissive:
            if d in text_lower:
                score += 0.35

        return self._clamp(score, 0.0, 1.0)

    def _detect_suppressed_frustration(self, text: str) -> float:
        """Detect frustration being held back."""
        text_lower = text.lower()
        score = 0.0

        frustration_markers = {
            "whatever", "it is what it is", "not a big deal", "fine",
            "i guess", "supposed to", "should have", "doesn't matter",
            "kind of", "sort of", "maybe", "probably",
        }
        for marker in frustration_markers:
            if marker in text_lower:
                score += 0.2

        # Over-politeness can mask anger
        polite = {"with all due respect", "no offense", "i'm not mad",
                  "i don't mean to", "but i appreciate"}
        for p in polite:
            if p in text_lower:
                score += 0.3

        # Short replies after context suggesting more to say
        word_count = len(text_lower.split())
        if word_count < 5 and any(w in text_lower for w in {"fine", "ok", "okay", "sure"}):
            score += 0.25

        # Passive voice often masks agency/frustration
        passive = {"was done", "was made", "was given", "got told", "was asked"}
        for p in passive:
            if p in text_lower:
                score += 0.15

        return self._clamp(score, 0.0, 1.0)

    def _detect_growing_anxiety(self, text: str) -> float:
        """Detect anxiety building beneath the surface."""
        text_lower = text.lower()
        score = 0.0

        anxiety_markers = {
            "can't stop", "keep thinking", "worried about", "what if",
            "not sure if", "feeling off", "something wrong", "on edge",
            "restless", "can't sit", "racing", "overwhelmed", "too much",
            "drowning", "suffocating", "tight chest", "nervous", "uneasy",
        }
        for marker in anxiety_markers:
            if marker in text_lower:
                score += 0.25

        # Repetitive questioning
        question_count = text.count("?")
        if question_count >= 3:
            score += 0.2

        # Urgency words without clear action
        urgency = {"need to", "have to", "must", "urgent", "asap", "quickly"}
        urgent_count = sum(1 for u in urgency if u in text_lower)
        if urgent_count >= 2:
            score += 0.15

        # Over-explaining (a common anxiety behavior)
        word_count = len(text_lower.split())
        if word_count > 80 and any(m in text_lower for m in {"just", "actually", "basically", "like"}):
            score += 0.1

        return self._clamp(score, 0.0, 1.0)

    def _detect_hidden_excitement(self, text: str, surface_valence: float) -> float:
        """Detect excitement the user hasn't fully expressed."""
        text_lower = text.lower()
        score = 0.0

        # Downplayed positivity
        downplay = {"might be", "could be", "kind of cool", "not bad",
                    "pretty good", "i think", "maybe", "possibly"}
        for d in downplay:
            if d in text_lower:
                score += 0.15

        # Physical excitement cues
        physical = {"can't wait", "butterflies", "heart racing", "so ready",
                    "pumped", "fired up", "buzzing", "itching to"}
        for p in physical:
            if p in text_lower:
                score += 0.4

        # Looking forward language
        forward = {"looking forward", "counting down", "almost time",
                   "soon", "next week", "this weekend", "big day"}
        for f in forward:
            if f in text_lower:
                score += 0.2

        # If surface valence is low but there are excitement markers, it's hidden
        if surface_valence < 0.2 and score > 0.3:
            score += 0.2

        return self._clamp(score, 0.0, 1.0)

    def _detect_numbness(self, text: str, arousal: float) -> float:
        """Detect emotional numbness or disconnection."""
        text_lower = text.lower()
        score = 0.0

        numb_markers = {"numb", "empty", "hollow", "nothing", "don't feel",
                        "can't feel", "just going", "going through", "auto-pilot",
                        "robot", "detached", "disconnected", "far away",
                        "not real", "watching myself", "gray", "flat"}
        for m in numb_markers:
            if m in text_lower:
                score += 0.35

        # Very short responses with low arousal
        word_count = len(text_lower.split())
        if word_count < 5 and arousal < 0.3:
            score += 0.2

        # Absence of emotional vocabulary
        emotional_words = {"happy", "sad", "angry", "excited", "worried", "love", "hate"}
        has_emotion = any(w in text_lower for w in emotional_words)
        if not has_emotion and word_count > 15 and arousal < 0.4:
            score += 0.15

        return self._clamp(score, 0.0, 1.0)

    def _detect_defensiveness(self, text: str) -> float:
        """Detect defensive posture."""
        text_lower = text.lower()
        score = 0.0

        def_markers = {"actually", "to be fair", "in my defense", "i did",
                       "i already", "you don't understand", "not my fault",
                       "i was going to", "i meant to", "but i", "however i"}
        for m in def_markers:
            if m in text_lower:
                score += 0.25

        # Justification chains
        if text_lower.count("because") >= 2:
            score += 0.2

        # Counter-attack language
        counter = {"well you", "what about", "at least i", "unlike"}
        for c in counter:
            if c in text_lower:
                score += 0.3

        return self._clamp(score, 0.0, 1.0)

    def _detect_vulnerability(self, text: str) -> float:
        """Detect emotional openness and vulnerability."""
        text_lower = text.lower()
        score = 0.0

        vuln_markers = {"i don't know what to do", "i feel lost", "scared",
                        "i'm struggling", "hard for me", "i need help",
                        "i can't handle", "breaking down", "not okay",
                        "don't tell anyone", "never told", "embarrassed",
                        "ashamed", "i'm afraid that", "vulnerable"}
        for m in vuln_markers:
            if m in text_lower:
                score += 0.35

        # Self-disclosure of weakness
        if any(w in text_lower for w in {"i'm not good at", "i fail", "i always mess"}):
            score += 0.3

        # Trust language
        trust = {"i trust you", "only you", "you're the only", "i can tell you"}
        for t in trust:
            if t in text_lower:
                score += 0.25

        return self._clamp(score, 0.0, 1.0)

    def _detect_masked_distress(self, text: str, valence: float, arousal: float) -> float:
        """Detect distress hidden behind a facade."""
        text_lower = text.lower()
        score = 0.0

        # High arousal + negative valence but softened language = masked distress
        distress_markers = {"i'm fine", "it's fine", "everything's fine",
                            "no worries", "all good", "not a problem",
                            "i'll manage", "i'll be okay", "just tired",
                            "just stressed", "just a lot"}
        for m in distress_markers:
            if m in text_lower:
                score += 0.3

        # Minimizers
        minimizers = {"just", "only", "merely", "simply", "a little"}
        min_count = sum(1 for m in minimizers if f" {m} " in text_lower or text_lower.startswith(m + " "))
        if min_count >= 2:
            score += 0.2

        # Contradiction: says fine but uses negative words
        negative_words = {"bad", "terrible", "awful", "hate", "sad", "angry",
                          "frustrated", "annoying", "worst", "horrible"}
        neg_count = sum(1 for w in negative_words if w in text_lower)
        if neg_count > 0 and "fine" in text_lower:
            score += 0.25

        # Physical symptoms without emotional naming
        physical = {"can't sleep", "no appetite", "headache", "tense",
                    "stomach", "chest", "breathing", "exhausted"}
        for p in physical:
            if p in text_lower:
                score += 0.15

        return self._clamp(score, 0.0, 1.0)

    def _label_primary_emotion(self, state: EmotionalState) -> str:
        """Assign a primary emotion label based on the full state."""
        scores = [
            ("sarcasm", state.sarcasm),
            ("suppressed_frustration", state.suppressed_frustration),
            ("growing_anxiety", state.growing_anxiety),
            ("hidden_excitement", state.hidden_excitement),
            ("emotional_numbness", state.emotional_numbness),
            ("defensiveness", state.defensiveness),
            ("vulnerability", state.vulnerability),
            ("masked_distress", state.masked_distress),
        ]
        # If any deep signal is strong, use it
        deep = max(scores, key=lambda x: x[1])
        if deep[1] > 0.4:
            return deep[0]

        # Otherwise fall back to surface valence/arousal
        if state.valence > 0.3:
            return "positive" if state.arousal > 0.5 else "content"
        if state.valence < -0.3:
            return "distressed" if state.arousal > 0.5 else "low"
        return "neutral"

    def _score_response_depth(self, response: str) -> float:
        """Score how emotionally deep a response is."""
        score = 0.3  # baseline
        response_lower = response.lower()

        # Emotional vocabulary
        emotional = {"feel", "feeling", "emotion", "heart", "soul", "care",
                     "matters", "important", "means", "deep", "raw"}
        score += sum(0.05 for w in emotional if w in response_lower)

        # Specificity (names, details)
        if any(w in response_lower for w in {"you", "your", "you're", "you've"}):
            score += 0.1

        # Acknowledgment depth
        if any(w in response_lower for w in {"sounds like", "seems like", "i can see"}):
            score += 0.15

        # Presence of questions that invite more depth
        if "?" in response:
            score += 0.05

        return self._clamp(score, 0.0, 1.0)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_data(self):
        """Load history and stats from disk."""
        if HISTORY_DB.exists():
            try:
                with open(HISTORY_DB, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for s in data.get("history", []):
                    self._history.append(EmotionalState(**s))
                for r in data.get("readings", []):
                    self._readings.append(ResonanceReading(**r))
                for a in data.get("alerts", []):
                    self._alerts.append(ShiftAlert(**a))
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.emotional_resonance")

        if STATS_DB.exists():
            try:
                with open(STATS_DB, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._stats.update(loaded)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.emotional_resonance")

    def _save_data(self):
        """Persist history and stats."""
        try:
            with self._lock:
                data = {
                    "history": [self._state_to_dict(s) for s in self._history],
                    "readings": [self._reading_to_dict(r) for r in self._readings],
                    "alerts": [self._alert_to_dict(a) for a in self._alerts],
                }
            with open(HISTORY_DB, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            with open(STATS_DB, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            print(f"[EmotionalResonance] Save error: {e}")

    def _state_to_dict(self, s: EmotionalState) -> Dict[str, Any]:
        return {
            "state_id": s.state_id,
            "timestamp": s.timestamp,
            "raw_text": s.raw_text,
            "valence": s.valence,
            "arousal": s.arousal,
            "dominance": s.dominance,
            "sarcasm": s.sarcasm,
            "suppressed_frustration": s.suppressed_frustration,
            "growing_anxiety": s.growing_anxiety,
            "hidden_excitement": s.hidden_excitement,
            "emotional_numbness": s.emotional_numbness,
            "defensiveness": s.defensiveness,
            "vulnerability": s.vulnerability,
            "masked_distress": s.masked_distress,
            "primary_emotion": s.primary_emotion,
            "depth_score": s.depth_score,
            "transparency": s.transparency,
        }

    def _reading_to_dict(self, r: ResonanceReading) -> Dict[str, Any]:
        return {
            "reading_id": r.reading_id,
            "timestamp": r.timestamp,
            "user_text": r.user_text,
            "love_response": r.love_response,
            "emotional_match": r.emotional_match,
            "validation_felt": r.validation_felt,
            "tone_alignment": r.tone_alignment,
            "depth_reciprocity": r.depth_reciprocity,
            "overall_resonance": r.overall_resonance,
            "suggestions": r.suggestions,
        }

    def _alert_to_dict(self, a: ShiftAlert) -> Dict[str, Any]:
        return {
            "alert_id": a.alert_id,
            "timestamp": a.timestamp,
            "shift_type": a.shift_type,
            "severity": a.severity,
            "description": a.description,
            "previous_state_id": a.previous_state_id,
            "current_state_id": a.current_state_id,
            "recommendation": a.recommendation,
        }

    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level accessor
# ═══════════════════════════════════════════════════════════════════════════════

_engine: Optional[EmotionalResonanceEngine] = None
_engine_lock = threading.Lock()


def get_emotional_resonance_engine() -> EmotionalResonanceEngine:
    """Get the singleton EmotionalResonanceEngine instance."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = EmotionalResonanceEngine()
    return _engine