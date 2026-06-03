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
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def _retry_with_backoff(func: Callable, max_retries: int = 3) -> Any:
    """
    Retry a function with exponential backoff (2s, 4s, 8s).
    Used for HTTP client calls to Ollama that may experience transient timeouts.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** (attempt + 1)
            print(f"[Consolidation] Retry {attempt + 1}/{max_retries} after {wait_time}s error: {e}")
            time.sleep(wait_time)


def _get_recent_conversations(hours: Union[int, str] = 24) -> List[Dict[str, Any]]:
    """Pull recent conversation turns from the structured conversation log."""
    log_file = DATA_DIR / "conversations.jsonl"
    if not log_file.exists():
        return []

    # Defensive cast: ensure hours is numeric
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        hours = 24
    cutoff = datetime.now() - timedelta(hours=hours)
    conversations = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", "")
                    dt = datetime.fromisoformat(ts)
                    if dt >= cutoff:
                        conversations.append(entry)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.memory_consolidation")
    except Exception as e:
        print(f"[Consolidation] Error reading log file: {e}")
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

        # Detect major themes (expanded)
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
        if any(w in user_text.lower() for w in ["code", "coding", "python", "build", "project", "agi", "system"]):
            themes.append("coding")
        if any(w in user_text.lower() for w in ["family", "brother", "sister", "friend", "visiting", "plan"]):
            themes.append("personal")
        if any(w in user_text.lower() for w in ["ship", "deadline", "goal", "want to", "need to"]):
            themes.append("goals")
        if any(w in user_text.lower() for w in ["work", "office", "job", "task", "assignment"]):
            themes.append("work")
        if any(w in user_text.lower() for w in ["thanks", "helped", "better", "appreciate"]):
            themes.append("gratitude")

        # Check if this continues current event or starts new one
        if current_event and themes and any(t in current_event["themes"] for t in themes):
            current_event["entries"].append(conv)
            current_event["themes"] = list(set(current_event["themes"] + themes))
        else:
            # Save current event (keep ALL events, even single-turn ones)
            if current_event:
                events.append(current_event)
            current_event = {
                "start_time": ts,
                "entries": [conv],
                "themes": themes or ["general"],
            }

    if current_event:
        events.append(current_event)

    return events


def _summarize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize a cluster of conversations into an episodic memory.
    Uses LLM if available (with a short timeout), otherwise uses rich rule-based extraction.
    """
    entries_text = "\n".join([
        f"Karthi: {e.get('user', '')[:200]}\nLOVE: {e.get('love', '')[:200]}"
        for e in event["entries"][:10]
    ])

    # --- Rule-based analysis (always runs, used as fallback or enrichment) ---
    import re

    # Extract people
    people = set()
    for m in re.finditer(r'\b([A-Z][a-z]{2,})\b', entries_text):
        name = m.group(1)
        if name not in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                        "Saturday", "Sunday", "January", "February", "March",
                        "April", "May", "June", "July", "August", "September",
                        "October", "November", "December", "Love", "Karthi",
                        "I", "You", "We", "They", "He", "She", "It", "The", "This", "That",
                        "User", "When", "What", "Where", "Why", "How", "But", "And",
                        "Not", "Also", "Just", "Like", "Really", "Very"}:
            people.add(name)

    # Detect emotion
    text_lower = entries_text.lower()
    emotion_scores = {"stressed": 0, "excited": 0, "proud": 0, "concerned": 0, "sad": 0, "content": 0}
    for theme in event["themes"]:
        if theme == "stress": emotion_scores["stressed"] += 1
        elif theme == "excitement": emotion_scores["excited"] += 1
        elif theme == "milestone": emotion_scores["proud"] += 1
        elif theme == "health": emotion_scores["concerned"] += 1
    if any(w in text_lower for w in ["happy", "great", "awesome", "love", "excited"]):
        emotion_scores["content"] += 1
    if any(w in text_lower for w in ["sad", "down", "depressed", "lonely"]):
        emotion_scores["sad"] += 1
    emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if any(emotion_scores.values()) else "neutral"

    # Calculate importance
    importance = 0.5
    if len(event["entries"]) > 5: importance += 0.2
    if "milestone" in event["themes"]: importance += 0.3
    if emotion in {"stressed", "excited", "proud"}: importance += 0.1
    if len(people) > 0: importance += 0.1
    importance = min(importance, 1.0)

    # Build a smart summary from the actual text
    user_texts = [e.get("user", "") for e in event["entries"]]
    themes = ", ".join(event["themes"])
    n_turns = len(event["entries"])
    ts_str = event.get("start_time", "")[:16]

    # Extract key phrases from user messages
    all_user = " ".join(user_texts)
    key_topics = set()
    # Find noun phrases and important terms
    for pattern in [r'\b(?:building|working on|developing|coding|shipping|deploying|fixing|debugging)\s+(\w+(?:\s+\w+)?)',
                    r'\b(?:project|app|system|module|feature|code)\s+(\w+)',
                    r'\b(?:AGI|LOVE|Python|React|API|UI|LLM|Ollama)\b']:
        for m in re.finditer(pattern, all_user, re.IGNORECASE):
            key_topics.add(m.group(0).strip())

    people_str = f" involving {', '.join(people)}" if people else ""
    topic_str = f" Topics discussed: {', '.join(list(key_topics)[:4])}." if key_topics else ""

    # Build the summary
    first_user_msg = user_texts[0][:120] if user_texts else ""
    summary = f"On {ts_str}, Karthi had a {n_turns}-turn conversation about {themes}{people_str}. "
    summary += f'It started with: "{first_user_msg}..."'
    if emotion != "neutral":
        summary += f" Karthi's emotional state was {emotion}."
    if topic_str:
        summary += topic_str

    # Try LLM-based summarization with a short timeout
    try:
        from core.llm import get_reasoning_llm
        import concurrent.futures

        def _llm_summarize():
            llm = get_reasoning_llm(temperature=0.3, max_tokens=200)
            prompt = f"""Summarize this conversation cluster into ONE concise episodic memory.
Include: what happened, Karthi's emotional state, significance.

Conversations:
{entries_text[:1500]}

Format: One paragraph, past tense, specific, 2-3 sentences max."""
            return llm.invoke(prompt).strip()

        with concurrent.futures.ThreadPoolExecutor() as ex:
            future = ex.submit(_llm_summarize)
            llm_summary = _retry_with_backoff(lambda: future.result(timeout=45))
            if llm_summary and len(llm_summary) > 20:
                summary = llm_summary
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory_consolidation")

    return {
        "summary": summary,
        "emotion": emotion,
        "intensity": importance,
        "people": list(people),
        "tags": event["themes"],
        "source": "milestone" if "milestone" in event["themes"] else "conversation",
        "timestamp": event["start_time"],
        "importance": importance,
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
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.memory_consolidation")

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

    positive = ["thanks", "helped", "better", "yes", "good point", "that works",
                "appreciate", "feel better", "makes sense", "smarter", "great", "awesome"]
    negative = ["no", "not really", "doesn't help", "wrong", "annoying", "stop",
                "useless", "don't", "terrible", "bad"]

    for i, conv in enumerate(conversations):
        user_text = conv.get("user", "").lower()
        love_response = conv.get("love", "")

        # Detect situation (expanded)
        situation = None
        if any(w in user_text for w in ["stressed", "overwhelmed", "burnout", "anxiety"]):
            situation = "Karthi is stressed"
        elif any(w in user_text for w in ["tired", "exhausted", "sleepy", "no energy", "sleep"]):
            situation = "Karthi is tired"
        elif any(w in user_text for w in ["excited", "pumped", "great news", "amazing"]):
            situation = "Karthi is excited"
        elif any(w in user_text for w in ["stuck", "frustrated", "blocked", "not working"]):
            situation = "Karthi is stuck/frustrated"
        elif any(w in user_text for w in ["sad", "down", "depressed", "lonely"]):
            situation = "Karthi is sad"
        elif any(w in user_text for w in ["coding", "building", "developing", "debugging"]):
            situation = "Karthi is coding"
        elif any(w in user_text for w in ["planning", "want to", "goal", "ship"]):
            situation = "Karthi is planning"

        if situation and len(love_response) > 10:
            # Look ahead up to 2 turns for feedback
            success = None
            for look_ahead in range(1, min(3, len(conversations) - i)):
                next_user = conversations[i + look_ahead].get("user", "").lower()
                if any(p in next_user for p in positive):
                    success = True
                    break
                elif any(n in next_user for n in negative):
                    success = False
                    break

            # Store all procedures — ambiguous ones get neutral success
            if success is None:
                success = True  # Assume neutral-to-positive if no explicit negative feedback

            action = love_response[:200]
            procedures.append({
                "situation": situation,
                "action": action,
                "success": success,
            })

    return procedures


# ── Main consolidation routine ──────────────────────────────────────────────

_PERIOD_MAP = {
    "daily": 24,
    "weekly": 168,
    "hourly": 1,
}

def consolidate_period(hours: Union[int, str] = 24) -> Dict[str, Any]:
    """
    Run memory consolidation for the last N hours.
    Accepts an int (hours) or a string label like 'daily', 'weekly'.
    Returns summary of what was learned.
    """
    if isinstance(hours, str):
        hours = _PERIOD_MAP.get(hours.lower(), 24)
    conversations = _get_recent_conversations(hours)
    if not conversations:
        return {"processed": 0, "created": 0, "message": "No conversations to consolidate"}
    
    try:
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
                analyst = _retry_with_backoff(get_analyst)
                project = analyst.get_active_project()
                if project:
                    # Add project context to work-related facts
                    for fact in facts:
                        if fact["category"] == "work":
                            fact["project_context"] = project
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.memory_consolidation")
            
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
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory_consolidation")

        return {
            "processed": len(conversations),
            "events": len(events),
            "created": created_memories,
            "types_breakdown": types_breakdown,
            "message": f"Consolidated {len(conversations)} conversations into {created_memories} memories",
        }
    
    except Exception as e:
        print(f"[Consolidation] Complete failure: {e}")
        # Fallback: write to backlog
        try:
            backlog_file = DATA_DIR / "memory" / "backlog.json"
            backlog_file.parent.mkdir(parents=True, exist_ok=True)
            
            backlog_data = {
                "timestamp": datetime.now().isoformat(),
                "conversations": conversations,
                "reason": "consolidation_failed"
            }
            
            if backlog_file.exists():
                try:
                    with open(backlog_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if isinstance(existing, list):
                        existing.append(backlog_data)
                    else:
                        existing = [existing, backlog_data]
                except Exception:
                    existing = [backlog_data]
            else:
                existing = [backlog_data]
            
            with open(backlog_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
            
            print(f"[Consolidation] Fallback: wrote {len(conversations)} conversations to backlog")
        except Exception as fallback_error:
            print(f"[Consolidation] Fallback also failed: {fallback_error}")
        
        return {
            "processed": len(conversations),
            "created": 0,
            "types_breakdown": {"episodic": 0, "semantic": 0, "procedural": 0},
            "message": f"Consolidation failed, wrote to backlog: {len(conversations)} conversations",
            "fallback": True,
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
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory_consolidation")
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