"""
LOVE Cross-Modal Fusion Engine — Unified Multi-Modal Understanding

Combines insights from text, visual, and voice modalities into a single
 coherent understanding. Detects conflicts, weights by confidence, and
 generates proactive summaries that help LOVE notice what matters.

Capabilities:
1. MODALITY FUSION
   - Merge insights from any combination of text, visual, and voice
   - Weight contributions by per-modality confidence
   - Extract common themes across modalities

2. CONFLICT DETECTION
   - Spot when different modalities send contradictory emotional signals
   - Surface the same entity described differently across channels
   - Flag low-confidence modalities for re-check

3. CROSS-MODAL SUMMARY
   - Generate a weighted narrative that prioritizes high-confidence signals
   - Proactively suggest what LOVE should notice or do next
   - Maintain timestamps for temporal reasoning

4. STATISTICS & PERSISTENCE
   - Log every fusion, conflict, and summary to JSONL
   - Track per-modality hit rates and conflict frequencies
   - Enable future pattern detection across fusion history
"""

import json
import re
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).parent.parent / "data" / "cross_modal_fusion"
DATA_DIR.mkdir(parents=True, exist_ok=True)

FUSION_LOG = DATA_DIR / "fusion_log.jsonl"
CONFLICT_LOG = DATA_DIR / "conflict_log.jsonl"
SUMMARY_LOG = DATA_DIR / "summary_log.jsonl"
STATS_FILE = DATA_DIR / "fusion_stats.json"


@dataclass
class ModalInsight:
    """Normalized insight from a single modality."""
    source: str = ""          # text | visual | voice
    content: str = ""
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    entities: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModalInsight":
        return cls(
            source=d.get("source", ""),
            content=d.get("content", ""),
            confidence=float(d.get("confidence", 0.5)),
            timestamp=d.get("timestamp", datetime.now().isoformat()),
            entities=d.get("entities", []),
            emotions=d.get("emotions", []),
            tags=d.get("tags", []),
        )


@dataclass
class FusionResult:
    """Result of fusing multiple insights."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    unified_themes: List[str] = field(default_factory=list)
    dominant_emotion: str = ""
    dominant_entities: List[str] = field(default_factory=list)
    confidence: float = 0.0
    modality_weights: Dict[str, float] = field(default_factory=dict)
    resolved_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    proactive_suggestion: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConflictReport:
    """Detected conflict across modalities."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    entity: str = ""
    conflict_type: str = ""   # emotion | description | intent
    modalities_involved: List[str] = field(default_factory=list)
    signals: Dict[str, str] = field(default_factory=dict)
    severity: float = 0.5     # 0-1, higher = more severe
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CrossModalSummary:
    """A generated summary across modalities."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    sources: List[str] = field(default_factory=list)
    summary_text: str = ""
    key_themes: List[str] = field(default_factory=list)
    emotional_tone: str = ""
    confidence: float = 0.0
    suggested_action: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CrossModalFusionEngine:
    """
    Central engine for combining multi-modal insights into unified understanding.
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
        self._stats = {
            "total_fusions": 0,
            "total_conflicts_detected": 0,
            "total_summaries": 0,
            "text_insights_processed": 0,
            "visual_insights_processed": 0,
            "voice_insights_processed": 0,
            "last_fusion_at": None,
        }
        self._load_stats()

    # ── Core Fusion ────────────────────────────────────────────────────────────

    def fuse_insights(
        self,
        text_insights: Optional[List[Dict[str, Any]]] = None,
        visual_insights: Optional[List[Dict[str, Any]]] = None,
        voice_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> FusionResult:
        """
        Combine insights from multiple modalities into unified understanding.

        Each insight dict must contain at minimum:
            {source: "text|visual|voice", content: str, confidence: float, timestamp: str}
        """
        all_insights: List[ModalInsight] = []
        if text_insights:
            all_insights.extend([ModalInsight.from_dict(i) for i in text_insights])
        if visual_insights:
            all_insights.extend([ModalInsight.from_dict(i) for i in visual_insights])
        if voice_insights:
            all_insights.extend([ModalInsight.from_dict(i) for i in voice_insights])

        if not all_insights:
            return FusionResult(
                unified_themes=[],
                dominant_emotion="",
                dominant_entities=[],
                confidence=0.0,
                modality_weights={},
                proactive_suggestion="No insights provided.",
            )

        # Enrich with entity / emotion extraction if not provided
        for insight in all_insights:
            if not insight.entities:
                insight.entities = self._extract_entities(insight.content)
            if not insight.emotions:
                insight.emotions = self._extract_emotions(insight.content)

        # Weight by confidence
        total_confidence = sum(i.confidence for i in all_insights) or 1.0
        modality_weights: Dict[str, float] = defaultdict(float)
        for insight in all_insights:
            modality_weights[insight.source] += insight.confidence / total_confidence

        # Extract common themes
        unified_themes = self._extract_common_themes(all_insights)
        dominant_emotion = self._resolve_dominant_emotion(all_insights)
        dominant_entities = self._resolve_dominant_entities(all_insights)

        # Resolve conflicts
        conflicts = self._detect_conflicts_raw(all_insights)
        resolved = []
        for c in conflicts:
            # Simple resolution: pick the signal from the highest-confidence modality
            best_modality = max(
                c["modalities_involved"],
                key=lambda m: next(
                    (i.confidence for i in all_insights if i.source == m), 0.0
                ),
            )
            resolved.append(
                {
                    "entity": c["entity"],
                    "conflict_type": c["conflict_type"],
                    "resolved_to": c["signals"].get(best_modality, "unknown"),
                    "resolution_basis": f"highest_confidence_modality: {best_modality}",
                }
            )

        # Proactive suggestion
        suggestion = self._generate_proactive_suggestion(all_insights, unified_themes, conflicts)

        result = FusionResult(
            unified_themes=unified_themes,
            dominant_emotion=dominant_emotion,
            dominant_entities=dominant_entities,
            confidence=min(1.0, total_confidence / len(all_insights)),
            modality_weights=dict(modality_weights),
            resolved_conflicts=resolved,
            proactive_suggestion=suggestion,
        )

        with self._lock:
            self._stats["total_fusions"] += 1
            self._stats["last_fusion_at"] = datetime.now().isoformat()
            if text_insights:
                self._stats["text_insights_processed"] += len(text_insights)
            if visual_insights:
                self._stats["visual_insights_processed"] += len(visual_insights)
            if voice_insights:
                self._stats["voice_insights_processed"] += len(voice_insights)
            self._save_stats()

        self._append_jsonl(FUSION_LOG, asdict(result))
        return result

    # ── Conflict Detection ───────────────────────────────────────────────────

    def detect_modal_conflicts(
        self, modalities: List[Dict[str, Any]]
    ) -> List[ConflictReport]:
        """
        Detect when different modalities report conflicting information.

        Each modality dict should contain:
            {source: "text|visual|voice", content: str, confidence: float, timestamp: str}
        """
        insights = [ModalInsight.from_dict(m) for m in modalities]
        for insight in insights:
            if not insight.entities:
                insight.entities = self._extract_entities(insight.content)
            if not insight.emotions:
                insight.emotions = self._extract_emotions(insight.content)

        raw_conflicts = self._detect_conflicts_raw(insights)
        reports = []
        for rc in raw_conflicts:
            report = ConflictReport(
                entity=rc["entity"],
                conflict_type=rc["conflict_type"],
                modalities_involved=rc["modalities_involved"],
                signals=rc["signals"],
                severity=rc["severity"],
                recommendation=rc["recommendation"],
            )
            reports.append(report)

        with self._lock:
            self._stats["total_conflicts_detected"] += len(reports)
            self._save_stats()

        for report in reports:
            self._append_jsonl(CONFLICT_LOG, asdict(report))

        return reports

    # ── Summary Generation ─────────────────────────────────────────────────────

    def get_cross_modal_summary(
        self, sources: List[Dict[str, Any]]
    ) -> CrossModalSummary:
        """
        Generate a cross-modal summary that weights each modality by confidence.

        Sources are insight dicts with:
            {source: "text|visual|voice", content: str, confidence: float, timestamp: str}
        """
        insights = [ModalInsight.from_dict(s) for s in sources]
        for insight in insights:
            if not insight.entities:
                insight.entities = self._extract_entities(insight.content)
            if not insight.emotions:
                insight.emotions = self._extract_emotions(insight.content)

        if not insights:
            return CrossModalSummary(
                summary_text="No sources provided.",
                confidence=0.0,
                suggested_action="Wait for more input.",
            )

        # Weighted confidence
        total_conf = sum(i.confidence for i in insights) or 1.0
        weighted_text_parts = []
        for i in insights:
            weight = i.confidence / total_conf
            weighted_text_parts.append(f"[{i.source.upper()} w={weight:.2f}] {i.content}")

        themes = self._extract_common_themes(insights)
        emotional_tone = self._resolve_dominant_emotion(insights)
        dominant_entities = self._resolve_dominant_entities(insights)

        summary_text = (
            f"Cross-modal summary: "
            f"{' / '.join(themes[:3]) if themes else 'No clear theme'}. "
            f"Dominant emotional tone: {emotional_tone or 'neutral'}. "
            f"Key focus: {', '.join(dominant_entities[:3]) if dominant_entities else 'none'}."
        )

        suggested_action = self._generate_proactive_suggestion(insights, themes, [])

        result = CrossModalSummary(
            sources=list({i.source for i in insights}),
            summary_text=summary_text,
            key_themes=themes,
            emotional_tone=emotional_tone,
            confidence=min(1.0, total_conf / len(insights)),
            suggested_action=suggested_action,
        )

        with self._lock:
            self._stats["total_summaries"] += 1
            self._save_stats()

        self._append_jsonl(SUMMARY_LOG, asdict(result))
        return result

    # ── Statistics ─────────────────────────────────────────────────────────────

    def get_fusion_stats(self) -> Dict[str, Any]:
        """Return engine statistics."""
        with self._lock:
            stats = dict(self._stats)
        stats["fusion_log_entries"] = self._count_lines(FUSION_LOG)
        stats["conflict_log_entries"] = self._count_lines(CONFLICT_LOG)
        stats["summary_log_entries"] = self._count_lines(SUMMARY_LOG)
        stats["engine_status"] = "active"
        return stats

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction: capitalize word sequences, names, pronouns."""
        # Look for capitalized phrases (naive but fast)
        entities = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", text)
        # Add first-person references
        for pronoun in ("i", "me", "my", "myself", "we", "us", "our"):
            if re.search(rf"\b{pronoun}\b", text, re.IGNORECASE):
                entities.append("user")
                break
        # Deduplicate and lowercase
        seen = set()
        clean = []
        for e in entities:
            key = e.lower()
            if key not in seen and len(key) > 2:
                seen.add(key)
                clean.append(key)
        return clean

    def _extract_emotions(self, text: str) -> List[str]:
        """Extract emotional signals from text."""
        emotion_lexicon = {
            "happy": ["happy", "joy", "excited", "cheerful", "glad", "delighted"],
            "sad": ["sad", "down", "depressed", "unhappy", "melancholy", "gloomy"],
            "angry": ["angry", "mad", "furious", "irritated", "annoyed", "frustrated"],
            "anxious": ["anxious", "worried", "nervous", "stressed", "tense", "uneasy"],
            "calm": ["calm", "relaxed", "peaceful", "serene", "tranquil", "content"],
            "tired": ["tired", "exhausted", "fatigued", "sleepy", "drained", "weary"],
            "energetic": ["energetic", "active", "lively", "vigorous", "dynamic"],
            "confused": ["confused", "uncertain", "puzzled", "lost", "perplexed"],
            "loved": ["loved", "appreciated", "cared", "cherished", "supported"],
            "lonely": ["lonely", "isolated", "alone", "abandoned", "neglected"],
        }
        found = []
        text_lower = text.lower()
        for emotion, keywords in emotion_lexicon.items():
            if any(kw in text_lower for kw in keywords):
                found.append(emotion)
        return found

    def _extract_common_themes(self, insights: List[ModalInsight]) -> List[str]:
        """Extract themes that appear across modalities."""
        # Collect all words, weighted by confidence
        word_scores: Dict[str, float] = defaultdict(float)
        for i in insights:
            words = re.findall(r"\b[a-z]{4,}\b", i.content.lower())
            for w in words:
                word_scores[w] += i.confidence

        # Filter for words appearing in multiple modalities
        modality_presence: Dict[str, set] = defaultdict(set)
        for i in insights:
            words = set(re.findall(r"\b[a-z]{4,}\b", i.content.lower()))
            for w in words:
                modality_presence[w].add(i.source)

        # Keep words present in 2+ modalities or with high score
        themes = []
        for word, score in sorted(word_scores.items(), key=lambda x: x[1], reverse=True):
            if len(modality_presence.get(word, set())) >= 2 or score > 1.5:
                themes.append(word)
        return themes[:5]

    def _resolve_dominant_emotion(self, insights: List[ModalInsight]) -> str:
        """Pick the emotion with highest aggregated confidence."""
        emotion_scores: Dict[str, float] = defaultdict(float)
        for i in insights:
            for e in i.emotions:
                emotion_scores[e] += i.confidence
        if not emotion_scores:
            return ""
        return max(emotion_scores.items(), key=lambda x: x[1])[0]

    def _resolve_dominant_entities(self, insights: List[ModalInsight]) -> List[str]:
        """Pick entities that appear most often, weighted by confidence."""
        entity_scores: Dict[str, float] = defaultdict(float)
        for i in insights:
            for e in i.entities:
                entity_scores[e] += i.confidence
        sorted_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)
        return [e for e, _ in sorted_entities[:5]]

    def _detect_conflicts_raw(self, insights: List[ModalInsight]) -> List[Dict[str, Any]]:
        """Internal conflict detection."""
        conflicts = []
        # Group by entity
        by_entity: Dict[str, List[ModalInsight]] = defaultdict(list)
        for i in insights:
            for e in i.entities:
                by_entity[e].append(i)

        for entity, entity_insights in by_entity.items():
            if len(entity_insights) < 2:
                continue
            modalities = list({i.source for i in entity_insights})
            if len(modalities) < 2:
                continue

            # Check emotion conflicts
            emotions_by_modality: Dict[str, set] = defaultdict(set)
            for i in entity_insights:
                emotions_by_modality[i.source].update(i.emotions)

            all_emotions = set()
            for s in emotions_by_modality.values():
                all_emotions.update(s)

            if len(all_emotions) > 1:
                # Determine severity: higher when confidences are similar (harder to resolve)
                confs = [i.confidence for i in entity_insights]
                avg_conf = sum(confs) / len(confs)
                min_conf = min(confs)
                max_conf = max(confs)
                severity = 0.5 + 0.3 * (1.0 - (max_conf - min_conf)) + 0.2 * avg_conf
                severity = min(1.0, severity)

                signals = {}
                for mod, emos in emotions_by_modality.items():
                    signals[mod] = ", ".join(emos) if emos else "neutral"

                conflicts.append(
                    {
                        "entity": entity,
                        "conflict_type": "emotion",
                        "modalities_involved": modalities,
                        "signals": signals,
                        "severity": round(severity, 3),
                        "recommendation": (
                            f"Entity '{entity}' shows mixed emotions across modalities. "
                            f"Verify with the highest-confidence source or ask the user directly."
                        ),
                    }
                )

        return conflicts

    def _generate_proactive_suggestion(
        self,
        insights: List[ModalInsight],
        themes: List[str],
        conflicts: List[Dict[str, Any]],
    ) -> str:
        """Generate a proactive suggestion based on fused understanding."""
        dominant_emotion = self._resolve_dominant_emotion(insights)
        dominant_entities = self._resolve_dominant_entities(insights)

        suggestions = []
        if conflicts:
            suggestions.append(
                f"Detected conflicting signals for {conflicts[0]['entity']}. "
                f"Consider clarifying before acting."
            )
        if dominant_emotion in {"sad", "anxious", "lonely"}:
            suggestions.append(
                "User may need emotional support or a gentle check-in."
            )
        if dominant_emotion in {"tired", "exhausted"}:
            suggestions.append(
                "User energy is low — suggest a break or recovery activity."
            )
        if "work" in themes or "busy" in themes:
            suggestions.append(
                "User context suggests workload. Proactively surface the day's work limit status."
            )
        if not suggestions:
            if dominant_entities:
                suggestions.append(
                    f"User attention is on {dominant_entities[0]}. "
                    f"Be ready to assist with related tasks."
                )
            else:
                suggestions.append(
                    "Insights aligned across modalities. Maintain current supportive stance."
                )

        return " ".join(suggestions)

    # ── Persistence Helpers ──────────────────────────────────────────────────

    def _append_jsonl(self, path: Path, obj: Dict[str, Any]):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _count_lines(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _save_stats(self):
        try:
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2)
        except Exception:
            pass

    def _load_stats(self):
        if not STATS_FILE.exists():
            return
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self._stats.update(loaded)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def get_cross_modal_fusion_engine() -> CrossModalFusionEngine:
    return CrossModalFusionEngine()
