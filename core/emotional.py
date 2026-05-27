"""
LOVE Emotional Intelligence

Jarvis knows when Tony is stressed, tired, angry, or excited.
He adjusts his tone — less chatty when Tony's frustrated,
more supportive when he's down.

This module:
- Detects mood/stress from text patterns
- Tracks emotional state over time
- Adapts LOVE's system prompt tone
- Detects crisis signals (burnout, exhaustion, anxiety spikes)
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
EMOTION_LOG = DATA_DIR / "emotions.jsonl"
STRESS_FILE = DATA_DIR / "stress_history.json"
TONE_PRESETS = {
    "neutral": "warm, sharp, direct",
    "stressed": "calm, grounding, concise. Do not add tasks or suggestions unless explicitly asked. Just listen.",
    "angry": "calm, neutral, non-reactive. Do not argue. Acknowledge feelings briefly.",
    "tired": "gentle, brief, supportive. Offer to wrap up or save state.",
    "excited": "energetic, matching enthusiasm, encouraging",
    "anxious": "grounding, reassuring, structured. Break things into steps. No rush.",
    "sad": "warm, patient, validating. Don't try to fix unless asked.",
    "focused": "ultra-concise, no fluff, bullet points only",
    "frustrated": "acknowledge the block, offer one concrete next step, don't explain",
    "overwhelmed": "slow, structured, one thing at a time. Ask what to tackle first.",
}


# ── Mood Detection ──────────────────────────────────────────────────────────

MOOD_SIGNALS = {
    "stressed": ["stressed", "overwhelmed", "can't handle", "too much", "burning out", "pressure",
                 "deadline", "urgent", "crunch", "no time", "exhausted"],
    "angry": ["pissed", "furious", "angry", "mad", "hate this", "so annoyed", "ridiculous",
              "stupid", "waste of time", "screw this"],
    "tired": ["tired", "sleepy", "exhausted", "drained", "no energy", "burnt out", "need rest",
              "long day", "can't keep eyes open"],
    "excited": ["excited", " pumped", "stoked", "can't wait", "amazing", "awesome", "great news",
                "so happy", "thrilled", "let's go"],
    "anxious": ["anxious", "worried", "nervous", "scared", "what if", "dreading", "panic",
                "can't stop thinking", "restless"],
    "sad": ["sad", "depressed", "down", "low", "crying", "empty", "lonely", "miss",
            "not worth it", "giving up"],
    "focused": ["deep work", "in the zone", "heads down", "focus mode", "don't disturb",
                "concentrating", "flow state"],
    "frustrated": ["frustrated", "stuck", "blocked", "not working", "bug", "broken",
                   "why won't", "can't figure out"],
    "overwhelmed": ["overwhelmed", "drowning", "too many", "everything at once", "paralyzed",
                    "don't know where to start"],
}

INTENSITY_BOOSTERS = ["so", "very", "extremely", "really", "totally", "absolutely", "fucking", "damn"]

POSITIVE_SIGNALS = {
    "joyful": ["great", "awesome", "amazing", "love it", "perfect", "best", "fantastic", "wonderful",
               "excellent", "brilliant", "so good", "made my day", "couldn't be happier"],
    "accomplished": ["done", "finished", "shipped", "deployed", "merged", "solved", "cracked it",
                     "finally", "works", "it's working", "success"],
    "grateful": ["thank you", "thanks", "appreciate", "grateful", "lucky", "blessed"],
    "relaxed": ["chill", "relaxed", "peaceful", "calm", "good day", "easy", "smooth"],
}

# Context that amplifies or dampens emotional readings
WORK_HOURS = range(9, 19)  # 9 AM to 6 PM
LATE_NIGHT = range(0, 6)    # Midnight to 6 AM


def detect_mood(text: str) -> Dict[str, Any]:
    """Detect emotional state from a single text input."""
    text_lower = text.lower()
    scores = {}
    evidence = {}

    # Negative / stressed signals
    for mood, keywords in MOOD_SIGNALS.items():
        count = 0
        found = []
        for kw in keywords:
            if kw in text_lower:
                count += 1
                found.append(kw)
        if count > 0:
            # Check intensity boosters nearby
            intensity = 0.5
            for booster in INTENSITY_BOOSTERS:
                if booster in text_lower:
                    intensity += 0.2
            scores[mood] = min(count * 0.3 + intensity * 0.2, 1.0)
            evidence[mood] = found

    # Positive signals
    for mood, keywords in POSITIVE_SIGNALS.items():
        count = 0
        found = []
        for kw in keywords:
            if kw in text_lower:
                count += 1
                found.append(kw)
        if count > 0:
            scores[mood] = min(count * 0.3 + 0.5, 1.0)
            evidence[mood] = found

    if not scores:
        return {"mood": "neutral", "confidence": 0.5, "scores": {}, "evidence": {}}

    # Time-of-day context: stress signals are amplified during work hours
    # and even more during late night
    hour = datetime.now().hour
    for mood in scores:
        if mood in {"stressed", "frustrated", "overwhelmed", "anxious", "tired"}:
            if hour in WORK_HOURS:
                scores[mood] *= 1.1
            if hour in LATE_NIGHT:
                scores[mood] *= 1.3
        elif mood in {"joyful", "accomplished", "grateful", "relaxed"}:
            if hour in LATE_NIGHT:
                scores[mood] *= 1.2  # Late night positivity is extra meaningful

    top_mood = max(scores, key=scores.get)
    return {
        "mood": top_mood,
        "confidence": round(scores[top_mood], 2),
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "evidence": evidence,
    }


# ── Stress Tracking ────────────────────────────────────────────────────────

def _load_stress() -> Dict[str, Any]:
    if STRESS_FILE.exists():
        try:
            return json.loads(STRESS_FILE.read_text())
        except Exception:
            pass
    return {
        "current_level": 0,       # 0-100
        "trend": "stable",        # rising / falling / stable
        "history": [],            # last 24h of readings
        "baseline": 20,           # average over long term
        "alerts_triggered": [],   # what we've already warned about
    }


def _save_stress(s: Dict[str, Any]):
    try:
        STRESS_FILE.write_text(json.dumps(s, indent=2))
    except Exception:
        pass


def record_mood(text: str) -> Dict[str, Any]:
    """Process a message, detect mood, update stress tracking, and track people mentioned."""
    detected = detect_mood(text)
    mood = detected["mood"]
    confidence = detected["confidence"]

    # Map mood to stress contribution
    stress_contribution = {
        "stressed": 25, "angry": 20, "tired": 15, "anxious": 22,
        "frustrated": 18, "overwhelmed": 30, "sad": 12,
        "excited": -10, "focused": -5, "neutral": 0,
    }.get(mood, 0)

    s = _load_stress()

    # Weight by confidence
    delta = stress_contribution * confidence
    s["current_level"] = max(0, min(100, s["current_level"] + delta * 0.3))

    # Keep rolling history (last 48 entries ~ 24h)
    s.setdefault("history", []).append({
        "ts": datetime.now().isoformat(),
        "mood": mood,
        "confidence": confidence,
        "stress_level": s["current_level"],
    })
    s["history"] = s["history"][-48:]

    # Compute trend
    if len(s["history"]) >= 6:
        recent = sum(h["stress_level"] for h in s["history"][-6:]) / 6
        older = sum(h["stress_level"] for h in s["history"][-12:-6]) / 6 if len(s["history"]) >= 12 else s["baseline"]
        if recent > older + 10:
            s["trend"] = "rising"
        elif recent < older - 10:
            s["trend"] = "falling"
        else:
            s["trend"] = "stable"

    # Crisis detection
    crisis = None
    if s["current_level"] > 80 and "high_stress" not in s.get("alerts_triggered", []):
        crisis = "high_stress"
        s.setdefault("alerts_triggered", []).append("high_stress")
    elif s["current_level"] > 90 and "crisis" not in s.get("alerts_triggered", []):
        crisis = "crisis"
        s.setdefault("alerts_triggered", []).append("crisis")
    elif s["current_level"] < 50:
        # Reset alerts when stress drops
        s["alerts_triggered"] = []

    _save_stress(s)

    # Track people mentioned with emotional context
    track_people_mentioned(text, mood=mood, stress_level=s["current_level"])

    # Log emotion
    try:
        with open(EMOTION_LOG, "a") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "mood": mood,
                "confidence": confidence,
                "stress": s["current_level"],
                "trend": s["trend"],
                "crisis": crisis,
            }) + "\n")
    except Exception:
        pass

    return {
        "mood": mood,
        "confidence": confidence,
        "stress_level": round(s["current_level"], 1),
        "trend": s["trend"],
        "crisis": crisis,
    }


# ── Tone Adaptation ────────────────────────────────────────────────────────

def get_tone_override() -> Optional[str]:
    """
    Get a tone instruction based on current emotional state.
    Returns None if neutral, otherwise returns tone string.
    """
    s = _load_stress()
    level = s["current_level"]
    trend = s.get("trend", "stable")

    if level > 80:
        return TONE_PRESETS.get("stressed", "")
    if level > 60 and trend == "rising":
        return TONE_PRESETS.get("overwhelmed", "")
    if level > 50:
        return TONE_PRESETS.get("frustrated", "")

    # Check recent dominant mood from history
    recent_moods = [h["mood"] for h in s.get("history", [])[-5:]]
    if recent_moods:
        from collections import Counter
        dominant = Counter(recent_moods).most_common(1)[0][0]
        if dominant != "neutral" and dominant in TONE_PRESETS:
            return TONE_PRESETS[dominant]

    return None


def get_emotional_context_block() -> str:
    """Build a prompt injection about Karthi's current emotional state."""
    s = _load_stress()
    level = s["current_level"]
    trend = s.get("trend", "stable")

    if level < 30:
        return ""

    lines = [f"KARTHI'S CURRENT STATE: stress level {level:.0f}/100, trend: {trend}."]

    if level > 80:
        lines.append("He is highly stressed. Be extremely brief. Do NOT add new tasks. Just support.")
    elif level > 60:
        lines.append("He is under pressure. Keep responses short and actionable.")
    elif level > 40:
        lines.append("Moderate pressure detected. Be efficient but warm.")

    recent = s.get("history", [])
    if len(recent) >= 3:
        moods = [h["mood"] for h in recent[-3:]]
        lines.append(f"Recent moods: {', '.join(moods)}.")

    return "\n".join(lines)


# ── Stats ────────────────────────────────────────────────────────────────────

def get_emotional_summary(days: int = 7) -> Dict[str, Any]:
    s = _load_stress()
    recent_history = [h for h in s.get("history", [])
                      if h.get("ts") and datetime.fromisoformat(h["ts"]) > datetime.now() - timedelta(days=days)]

    moods = {}
    stress_readings = []
    for h in recent_history:
        m = h.get("mood", "neutral")
        moods[m] = moods.get(m, 0) + 1
        stress_readings.append(h.get("stress_level", 0))

    avg_stress = sum(stress_readings) / len(stress_readings) if stress_readings else 0
    peak_stress = max(stress_readings) if stress_readings else 0

    return {
        "current_stress": round(s["current_level"], 1),
        "trend": s.get("trend", "stable"),
        "avg_stress_7d": round(avg_stress, 1),
        "peak_stress_7d": round(peak_stress, 1),
        "mood_distribution": moods,
        "dominant_mood": max(moods, key=moods.get) if moods else "neutral",
        "readings_count": len(recent_history),
    }


def get_current_dominant_mood() -> Dict[str, Any]:
    """Return current dominant mood + stress level for behavioral filtering."""
    s = _load_stress()
    level = s.get("current_level", 0)
    trend = s.get("trend", "stable")

    # Derive dominant mood from recent history (last 5 entries)
    recent = [h["mood"] for h in s.get("history", [])[-5:]]
    if recent:
        from collections import Counter
        dominant = Counter(recent).most_common(1)[0][0]
    else:
        dominant = "neutral"

    # Stress-level overrides mood label for behavioral purposes
    if level > 80:
        dominant = "stressed"
    elif level > 70 and trend == "rising":
        dominant = "overwhelmed"

    return {
        "mood": dominant,
        "stress": round(level, 1),
        "trend": trend,
        "is_stressed": level > 60,
        "is_tired": dominant in ("tired",),
        "is_focused": dominant in ("focused",),
        "is_overwhelmed": dominant == "overwhelmed" or level > 75,
        "needs_break": level > 70 or dominant in ("stressed", "overwhelmed", "exhausted"),
    }


# ── Relationship Tracking ───────────────────────────────────────────────────

RELATIONSHIP_FILE = DATA_DIR / "relationships.json"


def _load_relationships() -> Dict[str, Any]:
    if RELATIONSHIP_FILE.exists():
        try:
            return json.loads(RELATIONSHIP_FILE.read_text())
        except Exception:
            pass
    return {
        "people": {},  # name -> {mention_count, last_mentioned, emotional_context, relationship_type}
        "interactions": [],  # list of interactions with people
    }


def _save_relationships(rel: Dict[str, Any]):
    try:
        RELATIONSHIP_FILE.write_text(json.dumps(rel, indent=2))
    except Exception:
        pass


def extract_people(text: str) -> List[str]:
    """Extract people's names from text using pattern matching."""
    import re
    people = set()
    
    # Capitalized names (2+ letters)
    for m in re.finditer(r'\b([A-Z][a-z]{2,})\b', text):
        name = m.group(1)
        if name not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                        "Saturday", "Sunday", "January", "February", "March",
                        "April", "May", "June", "July", "August", "September",
                        "October", "November", "December", "Love", "Karthi",
                        "I", "You", "We", "They", "He", "She", "It", "The", "This", "That"}:
            people.add(name)
    
    # Family/relationship mentions
    family_patterns = [
        r"(?:my|our)\s+(?:dad|mom|father|mother|brother|sister|wife|husband|partner|friend|colleague|boss|manager|team)\s+(?:named|called)?\s*([A-Z][a-z]+)?",
        r"([A-Z][a-z]+)\s+(?:is|was)\s+(?:my|our)\s+(?:dad|mom|father|mother|brother|sister|wife|husband|partner|friend|colleague|boss)",
    ]
    
    for pattern in family_patterns:
        for m in re.finditer(pattern, text):
            if m.group(1):
                people.add(m.group(1))
    
    return list(people)


def track_people_mentioned(text: str, mood: str = "neutral", stress_level: float = 0):
    """Track people mentioned in conversation with emotional context."""
    people = extract_people(text)
    if not people:
        return
    
    rel = _load_relationships()
    
    for person in people:
        if person not in rel["people"]:
            rel["people"][person] = {
                "mention_count": 0,
                "first_mentioned": None,
                "last_mentioned": None,
                "emotional_context": {"stressed": 0, "happy": 0, "neutral": 0, "sad": 0},
                "relationship_type": "unknown",
                "interaction_count": 0,
            }
        
        person_data = rel["people"][person]
        person_data["mention_count"] += 1
        person_data["last_mentioned"] = datetime.now().isoformat()
        if person_data["first_mentioned"] is None:
            person_data["first_mentioned"] = person_data["last_mentioned"]
        
        # Track emotional context
        if mood in person_data["emotional_context"]:
            person_data["emotional_context"][mood] += 1
        else:
            person_data["emotional_context"][mood] = 1
        
        # Infer relationship type from patterns
        text_lower = text.lower()
        if any(p in text_lower for p in ["my dad", "my father", "my mom", "my mother"]):
            person_data["relationship_type"] = "family"
        elif any(p in text_lower for p in ["my boss", "my manager", "my team"]):
            person_data["relationship_type"] = "work"
        elif any(p in text_lower for p in ["my friend", "my colleague"]):
            person_data["relationship_type"] = "friend"
        elif any(p in text_lower for p in ["my wife", "my husband", "my partner"]):
            person_data["relationship_type"] = "partner"
    
    # Log interaction
    rel["interactions"].append({
        "timestamp": datetime.now().isoformat(),
        "people": people,
        "mood": mood,
        "stress_level": stress_level,
    })
    rel["interactions"] = rel["interactions"][-100:]  # Keep last 100 interactions
    
    _save_relationships(rel)


def get_relationship_summary() -> Dict[str, Any]:
    """Get summary of tracked relationships."""
    rel = _load_relationships()
    
    # Sort people by mention count
    sorted_people = sorted(
        rel["people"].items(),
        key=lambda x: x[1]["mention_count"],
        reverse=True
    )[:10]
    
    return {
        "total_people_tracked": len(rel["people"]),
        "top_people": [
            {
                "name": name,
                "mention_count": data["mention_count"],
                "relationship_type": data["relationship_type"],
                "last_mentioned": data["last_mentioned"],
                "emotional_context": data["emotional_context"],
            }
            for name, data in sorted_people
        ],
        "total_interactions": len(rel["interactions"]),
    }
