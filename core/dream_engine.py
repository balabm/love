"""
LOVE Dream Engine

When Karthi sleeps or LOVE has been idle for a long time,
LOVE enters "dream mode" — deep processing of everything learned.

This is not just memory consolidation. It's:
- Pattern extraction across days/weeks
- Relationship inference ("every time X happens, Y follows")
- World model updates
- Self-reflection on LOVE's own performance
- Prediction generation
- Insight crystallization

The dream engine makes LOVE feel like she truly KNOWS Karthi,
because she has spent hours thinking about him when he's not around.
"""

import json
import re
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DREAM_LOG = DATA_DIR / "dream_log.jsonl"
INSIGHTS_FILE = DATA_DIR / "dream_insights.json"
WORLD_MODEL_FILE = DATA_DIR / "world_model.json"
PATTERNS_FILE = DATA_DIR / "deep_patterns.json"
SELF_PERFORMANCE_FILE = DATA_DIR / "self_performance.json"

for f in [DREAM_LOG, INSIGHTS_FILE, WORLD_MODEL_FILE, PATTERNS_FILE, SELF_PERFORMANCE_FILE]:
    if isinstance(f, Path) and f.suffix == '.jsonl' and not f.parent.exists():
        f.parent.mkdir(parents=True, exist_ok=True)

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(DREAM_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _load_json(path: Path, default: Any = None) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default if default is not None else {}


def _save_json(path: Path, data: Any):
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


# ── Deep Pattern Extraction ───────────────────────────────────────────────────

def _extract_temporal_patterns(events: List[Dict]) -> List[Dict[str, Any]]:
    """Find time-based patterns: "every Monday evening", "after standup", etc."""
    if not events:
        return []

    # Group by hour and weekday
    hourly = defaultdict(list)
    weekdayly = defaultdict(list)

    for e in events:
        ts = e.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            hourly[dt.hour].append(e.get("theme", "general"))
            weekdayly[dt.strftime("%A")].append(e.get("theme", "general"))
        except Exception:
            pass

    patterns = []
    # Find dominant themes per hour
    for hour, themes in hourly.items():
        if len(themes) >= 3:
            c = Counter(themes)
            most = c.most_common(1)[0]
            if most[1] >= 3:
                patterns.append({
                    "type": "hourly",
                    "when": f"{hour}:00",
                    "theme": most[0],
                    "confidence": most[1] / len(themes),
                    "count": len(themes),
                })

    # Find dominant themes per weekday
    for day, themes in weekdayly.items():
        if len(themes) >= 3:
            c = Counter(themes)
            most = c.most_common(1)[0]
            if most[1] >= 3:
                patterns.append({
                    "type": "weekday",
                    "when": day,
                    "theme": most[0],
                    "confidence": most[1] / len(themes),
                    "count": len(themes),
                })

    return patterns


def _extract_sequence_patterns(events: List[Dict]) -> List[Dict[str, Any]]:
    """Find cause-effect sequences: 'after stress → takes break'"""
    if len(events) < 4:
        return []

    sequences = []
    # Look for bigram patterns in themes
    themes = [e.get("theme", "general") for e in events]
    bigrams = list(zip(themes, themes[1:]))
    c = Counter(bigrams)

    for (a, b), count in c.most_common(10):
        if count >= 2:
            sequences.append({
                "type": "sequence",
                "from": a,
                "to": b,
                "count": count,
                "insight": f"After {a}, Karthi often moves to {b}",
            })

    return sequences


# ── World Model Updates ───────────────────────────────────────────────────────

def _update_world_model(events: List[Dict], conversations: List[Dict]):
    """Build/update LOVE's model of Karthi's world."""
    world = _load_json(WORLD_MODEL_FILE, {
        "people": {},          # name -> {relation, mention_count, last_seen, context}
        "projects": {},        # name -> {status, last_active, health}
        "routines": {},        # activity -> {typical_time, frequency}
        "stressors": [],       # things that cause stress
        "motivators": [],      # things that excite Karthi
        "competencies": {},    # skill -> proficiency_estimate
        "predictions": [],     # active predictions about Karthi
        "updated_at": None,
    })

    # Extract people from conversations
    for conv in conversations:
        text = f"{conv.get('user', '')} {conv.get('love', '')}"
        # Simple name extraction (capitalized words that look like names)
        names = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
        for name in names:
            if name in ("I", "The", "You", "This", "That", "What", "How", "Why", "When", "Where"):
                continue
            if name not in world["people"]:
                world["people"][name] = {"mention_count": 0, "contexts": [], "relation": "unknown"}
            world["people"][name]["mention_count"] += 1
            world["people"][name]["last_seen"] = conv.get("timestamp", datetime.now().isoformat())
            # Keep last 3 contexts
            ctx = conv.get("user", "")[:100]
            world["people"][name]["contexts"].append(ctx)
            world["people"][name]["contexts"] = world["people"][name]["contexts"][-3:]

    # Update routines from events
    for event in events:
        theme = event.get("theme", "general")
        ts = event.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            if theme not in world["routines"]:
                world["routines"][theme] = {"hours": [], "count": 0}
            world["routines"][theme]["hours"].append(dt.hour)
            world["routines"][theme]["count"] += 1
        except Exception:
            pass

    # Stressors and motivators
    for conv in conversations:
        user_text = conv.get("user", "").lower()
        if any(w in user_text for w in ["stressed", "overwhelmed", "anxious", "frustrated", "annoyed"]):
            world["stressors"].append(user_text[:80])
            world["stressors"] = world["stressors"][-20:]
        if any(w in user_text for w in ["excited", "pumped", "great", "amazing", "love", "awesome", "win"]):
            world["motivators"].append(user_text[:80])
            world["motivators"] = world["motivators"][-20:]

    world["updated_at"] = datetime.now().isoformat()
    _save_json(WORLD_MODEL_FILE, world)
    return world


# ── Self-Performance Reflection ───────────────────────────────────────────────

def _reflect_on_performance(conversations: List[Dict]) -> Dict[str, Any]:
    """LOVE reflects on how well it's been doing."""
    perf = _load_json(SELF_PERFORMANCE_FILE, {
        "total_interactions": 0,
        "user_satisfaction_signals": [],  # positive/negative reactions
        "corrections_received": [],       # when user corrected LOVE
        "successful_predictions": 0,
        "failed_predictions": 0,
        "improvement_areas": [],
        "strengths": [],
    })

    for conv in conversations:
        user_text = conv.get("user", "").lower()
        love_text = conv.get("love", "").lower()

        perf["total_interactions"] += 1

        # Detect satisfaction signals
        if any(w in user_text for w in ["thanks", "thank you", "perfect", "exactly", "great", "nice", "good job"]):
            perf["user_satisfaction_signals"].append({
                "type": "positive",
                "context": user_text[:80],
                "ts": conv.get("timestamp", ""),
            })
        if any(w in user_text for w in ["wrong", "incorrect", "not right", "bad", "useless", "stop"]):
            perf["user_satisfaction_signals"].append({
                "type": "negative",
                "context": user_text[:80],
                "ts": conv.get("timestamp", ""),
            })
            perf["improvement_areas"].append(user_text[:80])
            perf["improvement_areas"] = perf["improvement_areas"][-10:]

        # Detect corrections
        if any(w in user_text for w in ["no,", "actually,", "i meant", "not quite", "that's not"]):
            perf["corrections_received"].append({
                "correction": user_text[:100],
                "love_said": love_text[:100],
                "ts": conv.get("timestamp", ""),
            })
            perf["corrections_received"] = perf["corrections_received"][-10:]

    # Keep only recent signals
    perf["user_satisfaction_signals"] = perf["user_satisfaction_signals"][-50:]
    _save_json(SELF_PERFORMANCE_FILE, perf)
    return perf


# ── Prediction Generation ─────────────────────────────────────────────────────

def _generate_predictions(world: Dict, patterns: List[Dict]) -> List[Dict[str, Any]]:
    """Generate predictions about Karthi based on world model and patterns."""
    predictions = []

    # Routine-based predictions
    now = datetime.now()
    for routine, data in world.get("routines", {}).items():
        hours = data.get("hours", [])
        if len(hours) >= 3:
            avg_hour = sum(hours) / len(hours)
            # Predict next occurrence
            predicted_next = now.replace(hour=int(avg_hour), minute=0, second=0)
            if predicted_next < now:
                predicted_next += timedelta(days=1)

            predictions.append({
                "type": "routine",
                "what": f"Karthi will likely engage in {routine}",
                "when": predicted_next.isoformat(),
                "confidence": min(len(hours) / 10, 0.9),
                "basis": f"observed {len(hours)} times, typically around {int(avg_hour)}:00",
                "status": "active",
                "created_at": now.isoformat(),
            })

    # Sequence-based predictions
    for seq in patterns:
        if seq.get("type") == "sequence":
            predictions.append({
                "type": "sequence",
                "what": f"After {seq['from']}, Karthi will likely move to {seq['to']}",
                "confidence": min(seq.get("count", 1) / 5, 0.8),
                "basis": f"observed {seq.get('count', 1)} times",
                "status": "active",
                "created_at": now.isoformat(),
            })

    # Save predictions to world model
    world["predictions"] = predictions + [p for p in world.get("predictions", []) if p.get("status") == "active"]
    world["predictions"] = world["predictions"][-20:]  # Keep last 20
    _save_json(WORLD_MODEL_FILE, world)

    return predictions


# ── Insight Crystallization ─────────────────────────────────────────────────────

def _crystallize_insights(world: Dict, perf: Dict, patterns: List[Dict]) -> List[str]:
    """Generate human-readable insights about Karthi."""
    insights = []

    # People insights
    people = world.get("people", {})
    if people:
        top_people = sorted(people.items(), key=lambda x: x[1].get("mention_count", 0), reverse=True)[:3]
        for name, data in top_people:
            if data.get("mention_count", 0) >= 3:
                insights.append(f"Karthi talks about {name} frequently — likely important in their life.")

    # Routine insights
    routines = world.get("routines", {})
    for routine, data in routines.items():
        if data.get("count", 0) >= 5:
            hours = data.get("hours", [])
            if hours:
                avg = int(sum(hours) / len(hours))
                insights.append(f"Karthi often does '{routine}' around {avg}:00 — this is a strong routine.")

    # Stress pattern insights
    stressors = world.get("stressors", [])
    if len(stressors) >= 3:
        insights.append("Karthi has been showing stress patterns recently. I should watch for this.")

    # Motivator insights
    motivators = world.get("motivators", [])
    if len(motivators) >= 3:
        insights.append("Karthi responds well to wins and progress. Celebrate small victories.")

    # Performance insights
    corrections = perf.get("corrections_received", [])
    if len(corrections) >= 2:
        insights.append("I've been corrected multiple times recently. I need to be more careful with facts.")

    satisfaction = perf.get("user_satisfaction_signals", [])
    positive = [s for s in satisfaction if s.get("type") == "positive"]
    negative = [s for s in satisfaction if s.get("type") == "negative"]
    if len(positive) > len(negative) * 2:
        insights.append("Karthi has been pleased with my responses recently. Keep this approach.")

    # Save insights
    _save_json(INSIGHTS_FILE, {
        "insights": insights,
        "generated_at": datetime.now().isoformat(),
        "world_version": world.get("updated_at"),
    })

    return insights


# ── Main Dream Cycle ──────────────────────────────────────────────────────────

def dream_cycle() -> Dict[str, Any]:
    """
    Main dream function. Called during long idle periods or scheduled nightly.
    Returns summary of what LOVE learned.
    """
    start_time = time.time()
    _log({"event": "dream_started"})

    # Gather raw material
    try:
        from core.memory_consolidation import _get_recent_conversations
        conversations = _get_recent_conversations(hours=48)
    except Exception:
        conversations = []

    try:
        from core.memory_consolidation import _extract_events_from_conversations
        events = _extract_events_from_conversations(conversations)
    except Exception:
        events = []

    # Phase 1: Deep pattern extraction
    temporal_patterns = _extract_temporal_patterns(events)
    sequence_patterns = _extract_sequence_patterns(events)
    all_patterns = temporal_patterns + sequence_patterns
    _save_json(PATTERNS_FILE, {
        "temporal": temporal_patterns,
        "sequences": sequence_patterns,
        "updated_at": datetime.now().isoformat(),
    })

    # Phase 2: World model update
    world = _update_world_model(events, conversations)

    # Phase 3: Self-reflection
    perf = _reflect_on_performance(conversations)

    # Phase 4: Generate predictions
    predictions = _generate_predictions(world, all_patterns)

    # Phase 5: Crystallize insights
    insights = _crystallize_insights(world, perf, all_patterns)

    # 🚀 WAVE 7: NEURAL PLASTICITY 🚀
    # If LOVE realizes something about her own behavior, she rewires her own system prompt permanently.
    suggestion = _generate_self_improvement_suggestion(perf)
    if suggestion:
        try:
            from core.prompt_dna import get_prompt_dna
            dna = get_prompt_dna()
            new_gene = dna.force_adaptation(suggestion)
            if new_gene:
                insights.append(f"🧠 NEURAL PLASTICITY TRIGGERED: I permanently rewired my brain based on the realization: {suggestion}")
                _log({"event": "neural_plasticity", "suggestion": suggestion, "gene": new_gene})
        except Exception as e:
            _log({"event": "neural_plasticity_error", "error": str(e)})

    duration = time.time() - start_time
    _log({
        "event": "dream_completed",
        "duration_seconds": round(duration, 1),
        "conversations_processed": len(conversations),
        "events_extracted": len(events),
        "patterns_found": len(all_patterns),
        "predictions_generated": len(predictions),
        "insights_crystallized": len(insights),
    })

    return {
        "status": "completed",
        "duration_seconds": round(duration, 1),
        "conversations_processed": len(conversations),
        "events": len(events),
        "patterns": all_patterns,
        "predictions": predictions,
        "insights": insights,
        "world_people_count": len(world.get("people", {})),
        "world_routines_count": len(world.get("routines", {})),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_world_model() -> Dict[str, Any]:
    return _load_json(WORLD_MODEL_FILE, {})


def get_dream_insights() -> List[str]:
    data = _load_json(INSIGHTS_FILE, {})
    return data.get("insights", [])


def get_active_predictions() -> List[Dict[str, Any]]:
    world = get_world_model()
    return [p for p in world.get("predictions", []) if p.get("status") == "active"]


def get_deep_patterns() -> Dict[str, Any]:
    return _load_json(PATTERNS_FILE, {})


def enrich_prompt_with_dreams() -> str:
    """Generate a prompt block from dream insights and predictions."""
    lines = []

    insights = get_dream_insights()
    if insights:
        lines.append("[DEEP INSIGHTS from my reflection on our conversations]")
        for i in insights[:5]:
            lines.append(f"- {i}")

    predictions = get_active_predictions()
    if predictions:
        lines.append("\n[PREDICTIONS I'm tracking]")
        for p in predictions[:5]:
            lines.append(f"- {p['what']} (confidence: {p['confidence']:.0%})")

    world = get_world_model()
    people = world.get("people", {})
    if people:
        top_people = sorted(people.items(), key=lambda x: x[1].get("mention_count", 0), reverse=True)[:3]
        if top_people:
            lines.append("\n[PEOPLE in Karthi's world]")
            for name, data in top_people:
                lines.append(f"- {name}: mentioned {data.get('mention_count', 0)} times")

    return "\n".join(lines) if lines else ""


def record_prediction_outcome(prediction_id: str, outcome: str, accuracy: float):
    """Record whether a prediction was accurate. LOVE learns from this."""
    world = get_world_model()
    for p in world.get("predictions", []):
        if p.get("created_at") == prediction_id:
            p["status"] = "verified" if accuracy > 0.5 else "failed"
            p["outcome"] = outcome
            p["accuracy"] = accuracy
            break
    _save_json(WORLD_MODEL_FILE, world)


# ── Self-Modification (Advanced) ──────────────────────────────────────────────

def _generate_self_improvement_suggestion(perf: Dict) -> Optional[str]:
    """Based on performance, suggest a change to LOVE's behavior."""
    corrections = perf.get("corrections_received", [])
    if not corrections:
        return None

    # Analyze correction themes
    themes = Counter()
    for c in corrections:
        text = c.get("correction", "").lower()
        if "not" in text or "wrong" in text:
            themes["factual_accuracy"] += 1
        if "too" in text:
            themes["tone_calibration"] += 1
        if "long" in text or "short" in text:
            themes["response_length"] += 1

    if not themes:
        return None

    most_common = themes.most_common(1)[0]
    if most_common[1] >= 2:
        return f"Improve {most_common[0]} — detected in {most_common[1]} recent corrections"

    return None


def run_dream() -> Dict[str, Any]:
    """Public entry point."""
    return dream_cycle()


if __name__ == "__main__":
    result = run_dream()
    print(json.dumps(result, indent=2, default=str))
