"""
LOVE Knowledge Graph

Memory isn't a flat list — it's a network.
People are connected to projects. Projects have moods. Events have outcomes.

This is what makes Jarvis feel like he KNOWS Karthi:
"How's that thing you were stressed about with Rahul last week?"
"Remember when you were excited about the side project? You haven't touched it in 12 days."
"Your brother called. Last 3 times he called were after work events."

Graph: SQLite + simple traversal queries. No external deps.
"""

import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GRAPH_DB = DATA_DIR / "knowledge_graph.db"


# ── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    attributes TEXT DEFAULT '{}',
    first_seen TEXT,
    last_seen TEXT,
    mention_count INTEGER DEFAULT 1,
    UNIQUE(name, type)
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    relation TEXT NOT NULL,
    strength REAL DEFAULT 1.0,
    context TEXT,
    created_at TEXT,
    last_reinforced TEXT,
    FOREIGN KEY(from_id) REFERENCES entities(id),
    FOREIGN KEY(to_id) REFERENCES entities(id),
    UNIQUE(from_id, to_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_relation_from ON relations(from_id);
CREATE INDEX IF NOT EXISTS idx_relation_to ON relations(to_id);
CREATE INDEX IF NOT EXISTS idx_relation_type ON relations(relation);
"""

ENTITY_TYPES = {"person", "project", "company", "topic", "emotion", "event",
                "location", "tool", "skill", "goal", "habit"}

RELATION_TYPES = {
    "knows", "works_with", "works_on", "uses", "feels", "located_at",
    "mentioned_with", "caused_by", "led_to", "blocks", "enables",
    "discusses", "owns", "wants", "avoids",
}

# AI response artifacts that should NEVER become entities
NOISE_WORDS = {
    "summarize", "summary", "breakdown", "overview", "detail", "status",
    "battery", "usage", "cpu", "ram", "memory", "usage", "charging",
    "attention", "enquiry", "alert", "notification", "message",
    "email", "event", "calendar", "task", "meeting",
    "great", "good", "nice", "perfect", "thanks", "thank",
    "here", "this", "that", "what", "how", "when", "where",
    "your", "you", "have", "from", "about", "with", "for",
}


@contextmanager
def _db():
    conn = sqlite3.connect(str(GRAPH_DB))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _init():
    with _db() as conn:
        conn.executescript(SCHEMA)


_init()


# ── Entity ops ──────────────────────────────────────────────────────────────

def add_entity(name: str, etype: str, attributes: Dict[str, Any] = None) -> int:
    """Create or update an entity. Returns its ID."""
    if etype not in ENTITY_TYPES:
        # Allow but log
        pass

    name = name.strip()
    if not name:
        return -1

    # Reject AI noise and generic words
    name_lower = name.lower()
    if name_lower in NOISE_WORDS or name_lower in EXCLUDE_WORDS or len(name) < 3:
        return -1
    # Reject multi-word noise combos (e.g., "Battery Status")
    parts = name_lower.split()
    if len(parts) <= 2 and any(p in NOISE_WORDS or p in EXCLUDE_WORDS for p in parts):
        return -1

    now = datetime.now().isoformat()
    attrs_json = json.dumps(attributes or {})

    with _db() as conn:
        cur = conn.execute("SELECT id, mention_count, attributes FROM entities WHERE name = ? AND type = ?",
                           (name, etype))
        row = cur.fetchone()
        if row:
            # Merge attributes
            existing_attrs = json.loads(row["attributes"] or "{}")
            existing_attrs.update(attributes or {})
            conn.execute(
                "UPDATE entities SET mention_count = mention_count + 1, last_seen = ?, attributes = ? WHERE id = ?",
                (now, json.dumps(existing_attrs), row["id"])
            )
            return row["id"]
        else:
            cur = conn.execute(
                "INSERT INTO entities (name, type, attributes, first_seen, last_seen) VALUES (?, ?, ?, ?, ?)",
                (name, etype, attrs_json, now, now)
            )
            return cur.lastrowid


def get_entity(name: str, etype: Optional[str] = None) -> Optional[Dict]:
    with _db() as conn:
        if etype:
            row = conn.execute("SELECT * FROM entities WHERE name = ? AND type = ?", (name, etype)).fetchone()
        else:
            row = conn.execute("SELECT * FROM entities WHERE name = ?", (name,)).fetchone()
        if row:
            d = dict(row)
            d["attributes"] = json.loads(d.get("attributes", "{}") or "{}")
            return d
    return None


def find_entities(query: str, etype: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Fuzzy search entities by name."""
    with _db() as conn:
        if etype:
            rows = conn.execute(
                "SELECT * FROM entities WHERE name LIKE ? AND type = ? ORDER BY mention_count DESC LIMIT ?",
                (f"%{query}%", etype, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM entities WHERE name LIKE ? ORDER BY mention_count DESC LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()
        return [dict(r) for r in rows]


# ── Relations ───────────────────────────────────────────────────────────────

def add_relation(from_name: str, from_type: str, to_name: str, to_type: str,
                 relation: str, context: str = "", strength: float = 1.0) -> Optional[int]:
    """Create or reinforce a relation between two entities."""
    from_id = add_entity(from_name, from_type)
    to_id = add_entity(to_name, to_type)
    if from_id < 0 or to_id < 0:
        return None

    now = datetime.now().isoformat()

    with _db() as conn:
        cur = conn.execute(
            "SELECT id, strength FROM relations WHERE from_id = ? AND to_id = ? AND relation = ?",
            (from_id, to_id, relation)
        )
        row = cur.fetchone()
        if row:
            new_strength = min(row["strength"] + strength * 0.5, 10.0)
            conn.execute(
                "UPDATE relations SET strength = ?, last_reinforced = ?, context = ? WHERE id = ?",
                (new_strength, now, context or "", row["id"])
            )
            return row["id"]
        else:
            cur = conn.execute(
                """INSERT INTO relations (from_id, to_id, relation, strength, context, created_at, last_reinforced)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (from_id, to_id, relation, strength, context, now, now)
            )
            return cur.lastrowid


def get_relations(name: str, etype: str = None,
                   direction: str = "both", limit: int = 20) -> List[Dict]:
    """
    Get all relations involving an entity.
    direction: 'out', 'in', or 'both'
    """
    entity = get_entity(name, etype)
    if not entity:
        return []
    eid = entity["id"]

    results = []
    with _db() as conn:
        if direction in ("out", "both"):
            rows = conn.execute("""
                SELECT r.*, e.name as to_name, e.type as to_type
                FROM relations r JOIN entities e ON r.to_id = e.id
                WHERE r.from_id = ?
                ORDER BY r.strength DESC LIMIT ?
            """, (eid, limit)).fetchall()
            for r in rows:
                results.append({
                    "from": entity["name"],
                    "from_type": entity["type"],
                    "to": r["to_name"],
                    "to_type": r["to_type"],
                    "relation": r["relation"],
                    "strength": r["strength"],
                    "context": r["context"],
                    "direction": "out",
                })

        if direction in ("in", "both"):
            rows = conn.execute("""
                SELECT r.*, e.name as from_name, e.type as from_type
                FROM relations r JOIN entities e ON r.from_id = e.id
                WHERE r.to_id = ?
                ORDER BY r.strength DESC LIMIT ?
            """, (eid, limit)).fetchall()
            for r in rows:
                results.append({
                    "from": r["from_name"],
                    "from_type": r["from_type"],
                    "to": entity["name"],
                    "to_type": entity["type"],
                    "relation": r["relation"],
                    "strength": r["strength"],
                    "context": r["context"],
                    "direction": "in",
                })

    return results


# ── Auto-extraction from text ──────────────────────────────────────────────

# Names: capitalized words, conservative — only proper names (first+last or known patterns)
# Only matches names that look like real people names
NAME_PATTERN = re.compile(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b')

# Common emotion words
EMOTION_KEYWORDS = {
    "stressed", "anxious", "happy", "excited", "tired", "exhausted", "frustrated",
    "angry", "sad", "depressed", "motivated", "confident", "worried", "scared",
    "proud", "grateful", "lonely", "overwhelmed", "calm", "focused", "energetic",
}

# Words that should NEVER be extracted as entities
EXCLUDE_WORDS = {
    # Days
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    # Months
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    # Common words
    "google", "github", "windows", "mac", "linux", "python", "javascript",
    "typescript", "flutter", "dart", "react", "angular", "vue", "docker",
    "kubernetes", "aws", "azure", "gcp", "firebase", "mongodb", "postgres",
    "mysql", "sqlite", "redis", "nginx", "apache", "git", "npm", "yarn",
    # Pronouns / articles
    "love", "karthi", "i", "you", "we", "they", "he", "she", "it", "this",
    "that", "these", "those", "the", "a", "an", "and", "or", "but", "so",
    "because", "if", "then", "than", "when", "where", "what", "how", "why",
    "who", "which", "whose", "whom", "here", "there", "every", "each",
    # Generic AI words
    "let", "their", "here", "additionally", "moreover", "furthermore",
    "however", "therefore", "thus", "hence", "consequently",
    "summarize", "summary", "breakdown", "overview", "detail",
    "status", "battery", "usage", "charging", "attention", "enquiry",
    # Tech brands that are topics not people
    "microsoft", "apple", "amazon", "facebook", "meta", "netflix", "spotify",
    "twitter", "x", "linkedin", "instagram", "tiktok", "youtube",
}

# Project signals
PROJECT_PATTERNS = [
    r"(?:my|our|the)\s+(\w+)\s+(?:project|app|tool|service|product|feature)",
    r"working on\s+([A-Z]\w+)",
    r"building\s+([A-Z]\w+)",
]

# Work verbs as topics for now
WORK_VERBS = {"work", "code", "build", "deploy", "ship", "fix", "debug", "review", "design", "test"}


def extract_entities(text: str, context_id: str = "") -> Dict[str, List[str]]:
    """
    Auto-extract entities from a chat message or memory.
    Returns dict by type.
    """
    extracted = {"person": [], "project": [], "emotion": [], "topic": []}

    # Only extract from user text, not from LOVE's generic responses
    # Split on "Love:" or "LOVE:" and only take user part
    user_text = text
    for sep in ["Love:", "LOVE:", "love:", "Assistant:", "AI:"]:
        if sep in text:
            parts = text.split(sep)
            if len(parts) > 1:
                # Keep everything before LOVE's response
                user_text = parts[0]
                break

    # People: capitalized names — be VERY conservative
    for m in NAME_PATTERN.finditer(user_text):
        name = m.group(1).strip()
        name_lower = name.lower()

        # Skip excluded or noise words
        if name_lower in EXCLUDE_WORDS or name_lower in NOISE_WORDS or len(name) < 3:
            continue
        # Skip sentence-start words (likely not a name)
        # Simple heuristic: if it's at start of sentence and alone
        if user_text.startswith(name):
            continue
        # Skip if it's clearly a tech term (all caps or camelCase)
        if re.match(r'^[A-Z][a-z]+[A-Z]', name):
            continue

        if name not in extracted["person"]:
            extracted["person"].append(name)

    # Emotions
    words = set(re.findall(r'\b\w+\b', user_text.lower()))
    for w in words:
        if w in EMOTION_KEYWORDS:
            extracted["emotion"].append(w)

    # Projects
    for pat in PROJECT_PATTERNS:
        for m in re.finditer(pat, user_text, re.IGNORECASE):
            proj = m.group(1).strip()
            if proj not in extracted["project"]:
                extracted["project"].append(proj)

    # Topics: work verbs as topics for now
    for w in words:
        if w in WORK_VERBS:
            extracted["topic"].append(w)

    return extracted


def ingest_text(text: str, source: str = "chat") -> Dict[str, Any]:
    """
    Process a chunk of text: extract entities, infer relations, save them.
    """
    extracted = extract_entities(text, context_id=source)
    added_relations = 0

    # Add all extracted entities
    for etype, names in extracted.items():
        for name in names:
            add_entity(name, etype, {"source": source})

    # Co-occurrence relations: if a person and a project appear together, link them
    for person in extracted["person"]:
        for project in extracted["project"]:
            add_relation(person, "person", project, "project", "works_on",
                         context=text[:200])
            added_relations += 1
        for emotion in extracted["emotion"]:
            add_relation(person, "person", emotion, "emotion", "mentioned_with",
                         context=text[:200])
            added_relations += 1

    # Karthi-centric relations (assume "I" / first person)
    if re.search(r'\b(?:I|my|me|i\'m|im)\b', text, re.IGNORECASE):
        for emotion in extracted["emotion"]:
            add_relation("Karthi", "person", emotion, "emotion", "feels",
                         context=text[:200])
            added_relations += 1
        for project in extracted["project"]:
            add_relation("Karthi", "person", project, "project", "works_on",
                         context=text[:200])
            added_relations += 1
        for person in extracted["person"]:
            add_relation("Karthi", "person", person, "person", "knows",
                         context=text[:200])
            added_relations += 1

    return {
        "extracted": extracted,
        "relations_added": added_relations,
    }


# ── Queries — make LOVE feel like she remembers ─────────────────────────────

def how_is(name: str) -> Dict[str, Any]:
    """
    'How is X?' — pull recent emotional/project/event signals about an entity.
    """
    entity = get_entity(name)
    if not entity:
        # Try fuzzy match
        candidates = find_entities(name, limit=3)
        if not candidates:
            return {"found": False, "name": name}
        entity = candidates[0]

    relations = get_relations(entity["name"], entity["type"], direction="out", limit=20)

    # Recent emotions tied to this entity (or by them)
    emotions = [r for r in relations if r["to_type"] == "emotion"]
    projects = [r for r in relations if r["to_type"] == "project"]

    # When was last mention?
    last_seen = entity.get("last_seen", "")
    days_since = None
    if last_seen:
        try:
            d = datetime.fromisoformat(last_seen)
            days_since = (datetime.now() - d).days
        except Exception:
            pass

    return {
        "found": True,
        "name": entity["name"],
        "type": entity["type"],
        "mentions": entity["mention_count"],
        "days_since_mention": days_since,
        "emotions": [e["to"] for e in emotions[:5]],
        "projects": [p["to"] for p in projects[:5]],
        "all_relations": relations[:10],
    }


def stale_things(days: int = 14) -> List[Dict[str, Any]]:
    """
    Find projects/people/goals not mentioned in N+ days — for proactive checkin.
    'You haven't talked about X in 12 days.'
    """
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with _db() as conn:
        rows = conn.execute("""
            SELECT name, type, last_seen, mention_count
            FROM entities
            WHERE last_seen < ? AND mention_count >= 3
            AND type IN ('project', 'goal', 'person', 'habit')
            ORDER BY mention_count DESC LIMIT 10
        """, (cutoff,)).fetchall()
        return [dict(r) for r in rows]


def graph_summary() -> Dict[str, Any]:
    """Top-level stats about the graph."""
    with _db() as conn:
        total_entities = conn.execute("SELECT COUNT(*) as n FROM entities").fetchone()["n"]
        total_relations = conn.execute("SELECT COUNT(*) as n FROM relations").fetchone()["n"]

        by_type = conn.execute("""
            SELECT type, COUNT(*) as n FROM entities GROUP BY type ORDER BY n DESC
        """).fetchall()

        top_people = conn.execute("""
            SELECT name, mention_count FROM entities WHERE type='person' ORDER BY mention_count DESC LIMIT 5
        """).fetchall()

        top_projects = conn.execute("""
            SELECT name, mention_count FROM entities WHERE type='project' ORDER BY mention_count DESC LIMIT 5
        """).fetchall()

    return {
        "total_entities": total_entities,
        "total_relations": total_relations,
        "by_type": [dict(r) for r in by_type],
        "top_people": [dict(r) for r in top_people],
        "top_projects": [dict(r) for r in top_projects],
    }


def context_for_chat(user_input: str) -> str:
    """
    Pull relevant graph context to inject into a chat prompt.
    """
    extracted = extract_entities(user_input)

    lines = []
    for etype, names in extracted.items():
        for name in names[:2]:  # Top 2 per type
            info = how_is(name)
            if info.get("found"):
                bits = []
                if info["days_since_mention"]:
                    bits.append(f"last mentioned {info['days_since_mention']}d ago")
                if info["emotions"]:
                    bits.append(f"emotions: {', '.join(info['emotions'][:3])}")
                if info["projects"]:
                    bits.append(f"projects: {', '.join(info['projects'][:3])}")
                if bits:
                    lines.append(f"  {name} ({info['type']}): {' | '.join(bits)}")

    if not lines:
        return ""
    return "KNOWLEDGE GRAPH CONTEXT:\n" + "\n".join(lines)


def query_knowledge(query: str, limit: int = 20) -> List[Dict]:
    """
    Query the knowledge graph for entities matching the query.
    Returns a list of relevant entities with their info.
    """
    # Extract potential entity names from query
    extracted = extract_entities(query)
    all_entities = []
    
    for etype, names in extracted.items():
        for name in names:
            info = how_is(name)
            if info.get("found"):
                all_entities.append(info)
    
    # Also search for partial matches in all entities
    query_lower = query.lower()
    try:
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM entities WHERE name LIKE ? OR LOWER(type) LIKE ? ORDER BY mention_count DESC LIMIT ?",
                (f"%{query}%", f"%{query_lower}%", limit)
            ).fetchall()
            for r in rows:
                info = how_is(r["name"])
                if info.get("found") and info not in all_entities:
                    all_entities.append(info)
    except Exception:
        pass
    
    return all_entities[:limit]
