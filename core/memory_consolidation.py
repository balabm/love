"""
LOVE Memory Consolidation

Every night, LOVE dreams.
She reviews the day's conversations and compresses them into long-term memories.

- Clusters conversations by topic/emotion
- Extracts semantic facts ("Karthi prefers X", "Karthi was stressed about Y")
- Creates episodic events ("May 14: all-day coding session on LOVE, hit 80% stress")
- Learns procedural rules ("when I suggested breaks during stress, Karthi said it helped")

Runs automatically via idle_mind or cron.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def _get_recent_conversations(hours: int = 24) -> List[Dict[str, Any]]:
    """Pull recent conversation turns from memory log or ChromaDB."""
    try:
        from core.memory import recall_memory
        # Try to get recent turns
        results = recall_memory("recent conversations", mode="general", n=50)
        if results:
            # Parse results — they may be structured
            return results if isinstance(results, list) else [results]
    except Exception:
        pass

    # Fallback: read conversation log file
    log_file = DATA_DIR / "conversations.jsonl"
    if not log_file.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours)
    conversations = []
    try:
        with open(log_file, "r") as f:
            for line in f:
                entry = json.loads(line)
                ts = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts)
                    if dt >= cutoff:
                        conversations.append(entry)
                except Exception:
                    pass
    except Exception:
        pass
    return conversations


def _extract_events_from_conversations(conversations: List[Dict]) -> List[Dict[str, Any]]:
    """Cluster conversations into meaningful events."""
    if not conversations:
        return []

    events = []
    current_event = None

    for conv in conversations:
        user_text = conv.get("user", "")
        love_text = conv.get("love", "")
        ts = conv.get("timestamp", "")

        # Detect major themes
        themes = []
        if any(w in user_text.lower() for w in ["stressed", "overwhelmed", "anxious", "burnout"]):
            themes.append("stress")
        if any(w in user_text.lower() for w in ["excited", "pumped", "great", "amazing", "launched"]):
            themes.append("excitement")
        if any(w in user_text.lower() for w in ["meeting", "standup", "call", "interview"]):
            themes.append("meeting")
        if any(w in user_text.lower() for w in ["shipped", "deployed", "released", "launched", "done"]):
            themes.append("milestone")
        if any(w in user_text.lower() for w in ["sick", "tired", "headache", "sleep", "health"]):
            themes.append("health")

        # Check if this continues current event or starts new one
        if current_event and themes and any(t in current_event["themes"] for t in themes):
            current_event["entries"].append(conv)
            current_event["themes"] = list(set(current_event["themes"] + themes))
        else:
            if current_event and len(current_event["entries"]) >= 2:
                events.append(current_event)
            current_event = {
                "start_time": ts,
                "entries": [conv],
                "themes": themes or ["general"],
            }

    if current_event and len(current_event["entries"]) >= 1:
        events.append(current_event)

    return events


def _summarize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to summarize a cluster of conversations into an episodic memory."""
    try:
        from core.llm import get_reasoning_llm
        from core.context_engine import get_live_context
        llm = get_reasoning_llm(temperature=0.3, max_tokens=300)

        entries_text = "\n".join([
            f"Karthi: {e.get('user', '')[:200]}\nLOVE: {e.get('love', '')[:200]}"
            for e in event["entries"][:10]
        ])

        # Add context to prompt for richer summaries
        try:
            ctx = get_live_context()
            context_str = f"\nContext: Working on {ctx.active_project or 'unknown'}, mood: {ctx.mood_score or 'unknown'}, activity: {ctx.activity or 'unknown'}"
        except Exception:
            context_str = ""

        prompt = f"""Summarize this conversation cluster into ONE concise episodic memory.
Include: what happened, Karthi's emotional state, any key people mentioned, and significance.
{context_str}

Conversations:
{entries_text}

Format: One paragraph, past tense, specific."""

        summary = llm.invoke(prompt).strip()

        # Extract emotion with enhanced detection
        emotion = "neutral"
        emotion_scores = {"stressed": 0, "excited": 0, "proud": 0, "concerned": 0, "sad": 0, "content": 0}
        
        for theme in event["themes"]:
            if theme == "stress":
                emotion_scores["stressed"] += 1
            elif theme == "excitement":
                emotion_scores["excited"] += 1
            elif theme == "milestone":
                emotion_scores["proud"] += 1
            elif theme == "health":
                emotion_scores["concerned"] += 1
        
        # Check text for emotional indicators
        text_lower = entries_text.lower()
        if any(w in text_lower for w in ["happy", "great", "awesome", "love", "excited"]):
            emotion_scores["content"] += 1
        if any(w in text_lower for w in ["sad", "down", "depressed", "lonely"]):
            emotion_scores["sad"] += 1
        
        # Get highest scoring emotion
        emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if any(emotion_scores.values()) else "neutral"

        # Extract people with better filtering
        people = set()
        import re
        for m in re.finditer(r'\b([A-Z][a-z]{2,})\b', entries_text):
            name = m.group(1)
            if name not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                            "Saturday", "Sunday", "January", "February", "March",
                            "April", "May", "June", "July", "August", "September",
                            "October", "November", "December", "Love", "Karthi",
                            "I", "You", "We", "They", "He", "She", "It", "The", "This", "That"}:
                people.add(name)

        # Calculate importance based on multiple factors
        importance = 0.5
        if len(event["entries"]) > 5:
            importance += 0.2
        if "milestone" in event["themes"]:
            importance += 0.3
        if emotion in {"stressed", "excited", "proud"}:
            importance += 0.1
        if len(people) > 0:
            importance += 0.1

        return {
            "summary": summary,
            "emotion": emotion,
            "intensity": importance,
            "people": list(people),
            "tags": event["themes"],
            "source": "milestone" if "milestone" in event["themes"] else "conversation",
            "timestamp": event["start_time"],
            "importance": min(importance, 1.0),
        }

    except Exception:
        # Fallback: simple concatenation
        themes = ", ".join(event["themes"])
        return {
            "summary": f"Conversations about {themes} ({len(event['entries'])} turns)",
            "emotion": "neutral",
            "intensity": 0.3,
            "people": [],
            "tags": event["themes"],
            "source": "conversation",
            "timestamp": event["start_time"],
            "importance": 0.3,
        }


def _extract_semantic_facts(conversations: List[Dict]) -> List[Dict[str, Any]]:
    """Extract declarative facts from conversations with richer patterns."""
    facts = []
    text = " ".join([c.get("user", "") for c in conversations])

    # Enhanced pattern-based extraction
    patterns = [
        # Family/people relationships
        (r"\b(my (?:brother|sister|dad|mom|friend|colleague|boss|team|manager))\s+(?:is\s+|name\s+is\s+)?([A-Z][a-z]+)",
         lambda m: ("person", "Karthi", f"has_{m.group(1).split()[1]}", m.group(2))),
        (r"\b([A-Z][a-z]+)\s+is\s+(?:my|a)\s+(?:brother|sister|dad|mom|friend|colleague|boss)",
         lambda m: ("person", "Karthi", f"has_relation", f"{m.group(1)} is family/colleague")),

        # Preferences with intensity
        (r"\b(i (?:really|absolutely|definitely)\s+(?:love|hate|like|dislike|prefer|enjoy))\s+(.+?)(?:\.|$|,)",
         lambda m: ("preference", "Karthi", f"strongly_{m.group(2)}", m.group(3).strip())),
        (r"\b(i (?:love|hate|like|dislike|prefer|enjoy))\s+(.+?)(?:\.|$|,)",
         lambda m: ("preference", "Karthi", m.group(1).replace("i ", ""), m.group(2).strip())),

        # Goals with timeframe
        (r"\b(i\s+(?:want to|need to|plan to|goal is to|trying to|working on))\s+(.+?)(?:\.|$|,)",
         lambda m: ("goal", "Karthi", "wants_to", m.group(2).strip())),
        (r"\b(by (?:next week|tomorrow|tonight|end of day|this month))\s+(?:i need to|i want to|i will)\s+(.+?)(?:\.|$|,)",
         lambda m: ("goal", "Karthi", f"deadline_{m.group(1)}", m.group(2).strip())),

        # Fears and anxieties
        (r"\b(i am (?:scared of|afraid of|worried about|anxious about|stressed about))\s+(.+?)(?:\.|$|,)",
         lambda m: ("fear", "Karthi", "fears", m.group(2).strip())),
        (r"\b(what if)\s+(.+?)(?:\.|$|,)",
         lambda m: ("fear", "Karthi", "anxious_about", f"what if {m.group(2)}")),

        # Skills and expertise
        (r"\b(i am (?:really|very|quite)\s+(?:good at|skilled at|expert in))\s+(.+?)(?:\.|$|,)",
         lambda m: ("skill", "Karthi", f"strong_at", m.group(2).strip())),
        (r"\b(i am (?:good at|skilled at|expert in))\s+(.+?)(?:\.|$|,)",
         lambda m: ("skill", "Karthi", "is_skilled_at", m.group(2).strip())),

        # Work/career facts
        (r"\b(at (?:work|my job|the office))\s+(?:i am|i'm)\s+(?:working on|doing|building|developing)\s+(.+?)(?:\.|$|,)",
         lambda m: ("work", "Karthi", "working_on", m.group(2).strip())),
        (r"\b(my (?:project|task|assignment))\s+(?:is|involves)\s+(.+?)(?:\.|$|,)",
         lambda m: ("work", "Karthi", "project_is", m.group(2).strip())),

        # Health and wellness
        (r"\b(i (?:feel|am feeling)\s+(?:sick|tired|exhausted|energetic|great|good|bad|stressed))\s+(?:today|right now|this week)",
         lambda m: ("health", "Karthi", "feels", m.group(2))),
        (r"\b(i (?:didn't|haven't)\s+slept\s+(?:well|good|enough))\s+(?:last night|recently)",
         lambda m: ("health", "Karthi", "sleep_quality", "poor")),

        # Location and environment
        (r"\b(i am|i'm)\s+(?:at|in)\s+(?:the|my)\s+(home|office|gym|cafe|car|desk)",
         lambda m: ("location", "Karthi", "at", m.group(2))),
        (r"\b(we are going to|i'm going to|i am going to)\s+(.+?)(?:\.|$|,)",
         lambda m: ("location", "Karthi", "going_to", m.group(2).strip())),

        # Time patterns
        (r"\b(yesterday|last night|this morning|today|tonight|tomorrow)\s+(?:i was|i was feeling|i did)\s+(.+?)(?:\.|$|,)",
         lambda m: ("time_event", "Karthi", f"on_{m.group(1)}", m.group(2).strip())),
    ]

    import re
    for pattern, extractor in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                cat, subj, pred, obj = extractor(m)
                # Filter out generic objects
                if len(obj) < 3 or obj.lower() in {"it", "that", "this", "them", "they", "something", "anything"}:
                    continue
                facts.append({
                    "category": cat,
                    "subject": subj,
                    "predicate": pred,
                    "object": obj,
                    "confidence": 0.7,
                })
            except Exception:
                pass

    # Relationship inference from co-mentions
    people = set()
    for conv in conversations:
        user = conv.get("user", "")
        # Find capitalized names
        for m in re.finditer(r'\b([A-Z][a-z]{2,})\b', user):
            name = m.group(1)
            if name not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                            "Saturday", "Sunday", "January", "February", "March",
                            "April", "May", "June", "July", "August", "September",
                            "October", "November", "December", "Love", "Karthi",
                            "I", "You", "We", "They", "He", "She", "It"}:
                people.add(name)

    # Infer relationships from context
    for person in people:
        if any(f"my {person}" in text.lower() for f in ["friend", "colleague", "boss", "team"]):
            facts.append({
                "category": "relationship",
                "subject": "Karthi",
                "predicate": "knows",
                "object": person,
                "confidence": 0.6,
            })

    return facts


def _learn_procedures(conversations: List[Dict]) -> List[Dict[str, Any]]:
    """Learn what responses work for what situations."""
    procedures = []

    for i, conv in enumerate(conversations[:-1]):
        user_text = conv.get("user", "").lower()
        love_response = conv.get("love", "")
        next_user = conversations[i + 1].get("user", "").lower() if i + 1 < len(conversations) else ""

        # Detect situation
        situation = None
        if any(w in user_text for w in ["stressed", "overwhelmed", "burnout"]):
            situation = "Karthi is stressed"
        elif any(w in user_text for w in ["tired", "exhausted", "sleepy", "no energy"]):
            situation = "Karthi is tired"
        elif any(w in user_text for w in ["excited", "pumped", "great news"]):
            situation = "Karthi is excited"
        elif any(w in user_text for w in ["stuck", "frustrated", "blocked", "not working"]):
            situation = "Karthi is stuck/frustrated"
        elif any(w in user_text for w in ["sad", "down", "depressed", "lonely"]):
            situation = "Karthi is sad"

        if situation and len(love_response) > 10:
            # Determine success from next response
            success = False
            positive = ["thanks", "helped", "better", "yes", "good point", "that works",
                        "appreciate", "feel better", "makes sense"]
            negative = ["no", "not really", "doesn't help", "wrong", "annoying", "stop"]

            if any(p in next_user for p in positive):
                success = True
            elif any(n in next_user for n in negative):
                success = False
            else:
                success = None  # Ambiguous

            if success is not None:
                action = love_response[:200]  # Truncate
                procedures.append({
                    "situation": situation,
                    "action": action,
                    "success": success,
                })

    return procedures


# ── Main consolidation routine ──────────────────────────────────────────────

def consolidate_period(hours: int = 24) -> Dict[str, Any]:
    """
    Run memory consolidation for the last N hours.
    Returns summary of what was learned.
    """
    conversations = _get_recent_conversations(hours)
    if not conversations:
        return {"processed": 0, "created": 0, "message": "No conversations to consolidate"}

    events = _extract_events_from_conversations(conversations)
    created_memories = 0
    types_breakdown = {"episodic": 0, "semantic": 0, "procedural": 0}

    # 1. Create episodic memories with importance scoring
    try:
        from core.long_term_memory import add_episodic
        for event in events:
            summary = _summarize_event(event)
            add_episodic(
                summary=summary["summary"],
                detail=f"Consolidated from {len(event['entries'])} conversation turns",
                timestamp=summary["timestamp"],
                emotion=summary["emotion"],
                intensity=summary["intensity"],
                people=summary["people"],
                tags=summary["tags"],
                source=summary["source"],
                importance=summary.get("importance", 0.5),
            )
            created_memories += 1
            types_breakdown["episodic"] += 1
    except Exception as e:
        print(f"[Consolidation] Episodic error: {e}")

    # 2. Extract semantic facts with cross-referencing
    try:
        from core.long_term_memory import add_semantic
        from core.doc_analyst import get_analyst
        facts = _extract_semantic_facts(conversations)
        
        # Cross-reference with project context
        try:
            analyst = get_analyst()
            project = analyst.get_active_project()
            if project:
                # Add project context to work-related facts
                for fact in facts:
                    if fact["category"] == "work":
                        fact["project_context"] = project
        except Exception:
            pass
        
        for fact in facts:
            add_semantic(
                category=fact["category"],
                subject=fact["subject"],
                predicate=fact["predicate"],
                obj=fact["object"],
                confidence=fact["confidence"],
                source="consolidation",
                metadata={"project_context": fact.get("project_context")} if fact.get("project_context") else None,
            )
            created_memories += 1
            types_breakdown["semantic"] += 1
    except Exception as e:
        print(f"[Consolidation] Semantic error: {e}")

    # 3. Learn procedures with success rate tracking
    try:
        from core.long_term_memory import add_procedural
        procedures = _learn_procedures(conversations)
        
        # Calculate success rates per situation
        success_rates = {}
        for proc in procedures:
            situation = proc["situation"]
            if situation not in success_rates:
                success_rates[situation] = {"success": 0, "total": 0}
            success_rates[situation]["total"] += 1
            if proc["success"]:
                success_rates[situation]["success"] += 1
        
        for proc in procedures:
            situation = proc["situation"]
            success_rate = success_rates[situation]["success"] / success_rates[situation]["total"] if success_rates[situation]["total"] > 0 else 0
            add_procedural(
                situation=proc["situation"],
                action=proc["action"],
                success=proc["success"],
                metadata={"success_rate": success_rate, "total_attempts": success_rates[situation]["total"]},
            )
            created_memories += 1
            types_breakdown["procedural"] += 1
    except Exception as e:
        print(f"[Consolidation] Procedural error: {e}")

    # Log consolidation
    try:
        from core.long_term_memory import _db
        with _db() as conn:
            conn.execute("""
                INSERT INTO consolidation_log (date, conversations_processed, memories_created, types_breakdown)
                VALUES (?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                len(conversations),
                created_memories,
                json.dumps(types_breakdown),
            ))
    except Exception:
        pass

    return {
        "processed": len(conversations),
        "events": len(events),
        "created": created_memories,
        "types_breakdown": types_breakdown,
        "message": f"Consolidated {len(conversations)} conversations into {created_memories} memories",
    }


def should_run_consolidation() -> bool:
    """Run once per day, ideally at night (10 PM - 6 AM)."""
    LAST_RUN_FILE = DATA_DIR / "last_consolidation.txt"
    try:
        if LAST_RUN_FILE.exists():
            last = datetime.fromisoformat(LAST_RUN_FILE.read_text().strip())
            hours_since = (datetime.now() - last).total_seconds() / 3600
            if hours_since < 20:
                return False
    except Exception:
        pass
    hour = datetime.now().hour
    if 6 <= hour < 22:
        return False  # Only run 10 PM - 6 AM
    LAST_RUN_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_RUN_FILE.write_text(datetime.now().isoformat())
    return True


def get_consolidation_history(days: int = 7) -> List[Dict]:
    """Show what LOVE has been learning."""
    try:
        from core.long_term_memory import _db
        with _db() as conn:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            rows = conn.execute(
                "SELECT * FROM consolidation_log WHERE date > ? ORDER BY date DESC",
                (cutoff,)
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []
