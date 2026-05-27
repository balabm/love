"""
LOVE Long-Term Memory System

Companion for life means remembering everything that matters.
Not just chat logs — LIFE.

Three memory types:
- Episodic: specific events with timestamp, emotion, people, location
  "June 2026: Karthi launched Project LOVE after a 3-month burnout"
- Semantic: facts, preferences, knowledge about Karthi
  "Karthi hates meetings before 10am", "Brother: Arjun, lives in Chennai"
- Procedural: what LOVE learned about HOW to help
  "When stress >70, don't suggest new tasks — just listen"

Built on SQLite (structured) + ChromaDB (embeddings for similarity search).
Consolidation runs nightly: compresses old conversations into life memories.
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from contextlib import contextmanager

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LTM_DB = DATA_DIR / "long_term_memory.db"


# ── Schema ──────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS episodic (
    id INTEGER PRIMARY KEY,
    memory_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT,
    emotion TEXT,
    intensity REAL DEFAULT 0.5,
    people TEXT,          -- JSON array
    location TEXT,
    tags TEXT,            -- JSON array
    source TEXT,          -- 'conversation', 'observation', 'milestone', 'dream'
    embedding_id TEXT,    -- ChromaDB reference
    created_at TEXT,
    last_accessed TEXT,
    access_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS semantic (
    id INTEGER PRIMARY KEY,
    memory_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,   -- 'preference', 'person', 'fact', 'goal', 'fear', 'joy'
    subject TEXT NOT NULL,    -- 'Karthi', 'work', 'family', 'health'
    predicate TEXT NOT NULL,  -- 'prefers', 'has', 'wants', 'avoids'
    object TEXT NOT NULL,     -- the value
    confidence REAL DEFAULT 1.0,
    first_seen TEXT,
    last_confirmed TEXT,
    evidence_count INTEGER DEFAULT 1,
    sources TEXT              -- JSON array of source IDs
);

CREATE TABLE IF NOT EXISTS procedural (
    id INTEGER PRIMARY KEY,
    memory_id TEXT UNIQUE NOT NULL,
    situation TEXT NOT NULL,   -- "when Karthi is stressed"
    action TEXT NOT NULL,      -- "don't suggest new tasks"
    outcome TEXT,              -- "Karthi felt supported"
    success_rate REAL DEFAULT 0.5,
    usage_count INTEGER DEFAULT 1,
    created_at TEXT,
    last_used TEXT
);

CREATE TABLE IF NOT EXISTS consolidation_log (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    conversations_processed INTEGER,
    memories_created INTEGER,
    types_breakdown TEXT       -- JSON
);

CREATE INDEX IF NOT EXISTS idx_episodic_time ON episodic(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodic_emotion ON episodic(emotion);
CREATE INDEX IF NOT EXISTS idx_episodic_people ON episodic(people);
CREATE INDEX IF NOT EXISTS idx_semantic_cat ON semantic(category);
CREATE INDEX IF NOT EXISTS idx_semantic_subj ON semantic(subject);
CREATE INDEX IF NOT EXISTS idx_procedural_sit ON procedural(situation);
"""


@contextmanager
def _db():
    conn = sqlite3.connect(str(LTM_DB))
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


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _now() -> str:
    return datetime.now().isoformat()


# -- Lazy shared ChromaDB client (avoids creating a new PersistentClient per call) --
_ltm_chroma_client = None
_ltm_chroma_collections: dict = {}

def _ltm_get_collection(collection_name: str):
    """Return a cached ChromaDB collection, opening the client once."""
    global _ltm_chroma_client, _ltm_chroma_collections
    import chromadb
    if _ltm_chroma_client is None:
        _ltm_chroma_client = chromadb.PersistentClient(path=str(DATA_DIR / "memory"))
    key = f"love_{collection_name}"
    if key not in _ltm_chroma_collections:
        _ltm_chroma_collections[key] = _ltm_chroma_client.get_or_create_collection(name=key)
    return _ltm_chroma_collections[key]


def _chroma_store(text: str, metadata: Dict, collection_name: str = "episodic") -> str:
    """Store embedding in ChromaDB, return embedding ID."""
    try:
        collection = _ltm_get_collection(collection_name)
        doc_id = _make_id(text + json.dumps(metadata, sort_keys=True))
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return doc_id
    except Exception:
        return None


def _chroma_query(query: str, n: int = 5, collection_name: str = "episodic") -> List[Dict]:
    """Semantic search via ChromaDB."""
    try:
        collection = _ltm_get_collection(collection_name)
        results = collection.query(query_texts=[query], n_results=n)
        out = []
        for i, doc in enumerate(results["documents"][0]):
            out.append({
                "text": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return out
    except Exception:
        return []


# ── Episodic Memory ────────────────────────────────────────────────────────

def add_episodic(summary: str, detail: str = None, timestamp: str = None,
                 emotion: str = None, intensity: float = 0.5,
                 people: List[str] = None, location: str = None,
                 tags: List[str] = None, source: str = "conversation", **kwargs) -> Dict[str, Any]:
    """Add a life event memory."""
    ts = timestamp or _now()
    mem_id = _make_id(summary + ts)
    people_json = json.dumps(people or [])
    tags_json = json.dumps(tags or [])

    # Store in ChromaDB for semantic retrieval
    embedding_id = _chroma_store(summary, {
        "type": "episodic", "timestamp": ts, "emotion": emotion or "",
        "people": people_json, "tags": tags_json
    })

    with _db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO episodic
            (memory_id, timestamp, summary, detail, emotion, intensity, people, location, tags, source, embedding_id, created_at, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (mem_id, ts, summary, detail or "", emotion, intensity, people_json, location or "", tags_json, source, embedding_id, _now(), _now(), 0))

    return {"success": True, "memory_id": mem_id, "type": "episodic"}


def query_episodic(query: str = None, start_date: str = None, end_date: str = None,
                   emotion: str = None, person: str = None, tag: str = None,
                   limit: int = 20) -> List[Dict[str, Any]]:
    """Query episodic memories. Supports semantic + structured filters."""
    results = []

    # Semantic search if query provided
    if query:
        semantic_results = _chroma_query(query, n=min(limit, 10), collection_name="episodic")
        for r in semantic_results:
            meta = r.get("metadata", {})
            results.append({
                "summary": r["text"],
                "timestamp": meta.get("timestamp", ""),
                "emotion": meta.get("emotion", ""),
                "semantic_match": True,
                "distance": r.get("distance"),
            })

    # Structured query
    with _db() as conn:
        sql = "SELECT * FROM episodic WHERE 1=1"
        params = []
        if start_date:
            sql += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND timestamp <= ?"
            params.append(end_date)
        if emotion:
            sql += " AND emotion = ?"
            params.append(emotion)
        if person:
            sql += " AND people LIKE ?"
            params.append(f'%"{person}"%')
        if tag:
            sql += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        for row in rows:
            d = dict(row)
            d["people"] = json.loads(d.get("people") or "[]")
            d["tags"] = json.loads(d.get("tags") or "[]")
            results.append(d)

    return results[:limit]


def get_life_timeline(year: int = None, month: int = None) -> List[Dict]:
    """Get memories as a life timeline."""
    start = None
    end = None
    if year:
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        if month:
            start = f"{year}-{month:02d}-01"
            # approximate end
            if month == 12:
                end = f"{year}-12-31"
            else:
                end = f"{year}-{month+1:02d}-01"
    return query_episodic(start_date=start, end_date=end, limit=50)


# ── Semantic Memory ────────────────────────────────────────────────────────

def add_semantic(category: str, subject: str, predicate: str, obj: str,
                 confidence: float = 1.0, source: str = None, metadata: Dict = None, **kwargs) -> Dict[str, Any]:
    """
    Add a fact about Karthi's world.
    Examples:
      add_semantic("preference", "Karthi", "prefers", "dark mode", 0.9)
      add_semantic("person", "Karthi", "has_brother", "Arjun", 1.0)
      add_semantic("goal", "Karthi", "wants_to", "ship LOVE v1 by June", 0.8)
    """
    mem_id = _make_id(f"{category}:{subject}:{predicate}:{obj}")

    with _db() as conn:
        cur = conn.execute(
            "SELECT * FROM semantic WHERE memory_id = ?", (mem_id,)
        ).fetchone()
        if cur:
            # Reinforce existing memory
            new_conf = (cur["confidence"] * cur["evidence_count"] + confidence) / (cur["evidence_count"] + 1)
            sources = json.loads(cur["sources"] or "[]")
            if source:
                sources.append(source)
            conn.execute("""
                UPDATE semantic SET
                confidence = ?, last_confirmed = ?, evidence_count = evidence_count + 1, sources = ?
                WHERE memory_id = ?
            """, (round(new_conf, 3), _now(), json.dumps(sources[-10:]), mem_id))
            return {"success": True, "memory_id": mem_id, "action": "reinforced", "confidence": new_conf}
        else:
            conn.execute("""
                INSERT INTO semantic (memory_id, category, subject, predicate, object, confidence, first_seen, last_confirmed, evidence_count, sources)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (mem_id, category, subject, predicate, obj, confidence, _now(), _now(), json.dumps([source] if source else [])))
            return {"success": True, "memory_id": mem_id, "action": "created"}


def query_semantic(category: str = None, subject: str = None,
                   predicate: str = None, limit: int = 20) -> List[Dict]:
    """Query semantic facts."""
    with _db() as conn:
        sql = "SELECT * FROM semantic WHERE 1=1"
        params = []
        if category:
            sql += " AND category = ?"
            params.append(category)
        if subject:
            sql += " AND subject LIKE ?"
            params.append(f"%{subject}%")
        if predicate:
            sql += " AND predicate = ?"
            params.append(predicate)
        sql += " ORDER BY confidence DESC, last_confirmed DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_karthi_profile() -> Dict[str, Any]:
    """Build a comprehensive profile of Karthi from semantic memory."""
    categories = ["preference", "person", "goal", "fear", "joy", "fact"]
    profile = {}
    for cat in categories:
        facts = query_semantic(category=cat, subject="Karthi", limit=20)
        profile[cat] = [{"predicate": f["predicate"], "object": f["object"],
                         "confidence": f["confidence"]} for f in facts]
    return profile


# ── Procedural Memory ──────────────────────────────────────────────────────

def add_procedural(situation: str, action: str, outcome: str = None,
                   success: bool = True, metadata: Dict = None, **kwargs) -> Dict[str, Any]:
    """
    Record what LOVE learned about helping Karthi.
    Example:
      add_procedural("Karthi is stressed and mentions burnout",
                     "Ask what one thing would help most, don't add tasks",
                     "Karthi said 'that actually helped'")
    """
    mem_id = _make_id(situation + action)

    with _db() as conn:
        cur = conn.execute("SELECT * FROM procedural WHERE memory_id = ?", (mem_id,)).fetchone()
        if cur:
            # Update success rate
            old_rate = cur["success_rate"]
            old_count = cur["usage_count"]
            new_count = old_count + 1
            new_rate = (old_rate * old_count + (1.0 if success else 0.0)) / new_count
            conn.execute("""
                UPDATE procedural SET success_rate = ?, usage_count = ?, last_used = ?
                WHERE memory_id = ?
            """, (round(new_rate, 3), new_count, _now(), mem_id))
            return {"success": True, "memory_id": mem_id, "action": "updated", "success_rate": new_rate}
        else:
            rate = 1.0 if success else 0.0
            conn.execute("""
                INSERT INTO procedural (memory_id, situation, action, outcome, success_rate, usage_count, created_at, last_used)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (mem_id, situation, action, outcome or "", rate, _now(), _now()))
            return {"success": True, "memory_id": mem_id, "action": "created", "success_rate": rate}


def query_procedural(situation: str = None, limit: int = 10) -> List[Dict]:
    """Find learned procedures. Can do semantic match on situation."""
    with _db() as conn:
        if situation:
            rows = conn.execute(
                "SELECT * FROM procedural WHERE situation LIKE ? ORDER BY success_rate DESC, usage_count DESC LIMIT ?",
                (f"%{situation}%", limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM procedural ORDER BY success_rate DESC, usage_count DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def get_best_response_for(mood: str, context: str = None) -> Optional[str]:
    """Find the most successful learned response for a situation."""
    procs = query_procedural(situation=mood, limit=5)
    if not procs:
        return None
    best = max(procs, key=lambda p: p.get("success_rate", 0) * p.get("usage_count", 1))
    return best.get("action")


# ── Unified Query ─────────────────────────────────────────────────────────

def remember(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    The main memory query — searches all memory types and returns unified results.
    This is what LOVE uses when she 'remembers' something about Karthi.
    """
    episodic = query_episodic(query=query, limit=limit)
    semantic = query_semantic(subject=query, limit=limit)
    procedural = query_procedural(situation=query, limit=limit)

    # Also try semantic search on semantic memories via ChromaDB
    semantic_texts = _chroma_query(query, n=min(limit, 5), collection_name="semantic")

    return {
        "query": query,
        "episodic": episodic[:5],
        "semantic": semantic[:5],
        "procedural": procedural[:3],
        "semantic_similar": semantic_texts[:3],
        "total_found": len(episodic) + len(semantic) + len(procedural),
    }


# ── Life Summary ──────────────────────────────────────────────────────────

def get_life_summary(period: str = "all") -> Dict[str, Any]:
    """
    Generate a life summary for a period.
    period: 'today', 'week', 'month', 'year', 'all'
    """
    now = datetime.now()
    if period == "today":
        start = now.strftime("%Y-%m-%d")
    elif period == "week":
        start = (now - timedelta(days=7)).isoformat()
    elif period == "month":
        start = (now - timedelta(days=30)).isoformat()
    elif period == "year":
        start = (now - timedelta(days=365)).isoformat()
    else:
        start = None

    events = query_episodic(start_date=start, limit=100) if start else query_episodic(limit=100)

    # Count emotions
    emotions = {}
    people_seen = set()
    milestones = []
    for e in events:
        emo = e.get("emotion")
        if emo:
            emotions[emo] = emotions.get(emo, 0) + 1
        for p in e.get("people", []):
            people_seen.add(p)
        if e.get("source") == "milestone":
            milestones.append(e.get("summary", ""))

    profile = get_karthi_profile()

    return {
        "period": period,
        "events_count": len(events),
        "emotional_summary": emotions,
        "people_involved": list(people_seen),
        "milestones": milestones[:10],
        "top_memories": [e.get("summary", "") for e in events[:5]],
        "profile_snapshot": profile,
    }


def format_memory_for_chat(memory_result: Dict[str, Any]) -> str:
    """Convert memory query result into natural text for LLM prompt."""
    lines = []
    if memory_result.get("episodic"):
        lines.append("LIFE MEMORIES:")
        for e in memory_result["episodic"][:3]:
            ts = e.get("timestamp", "")[:10] if isinstance(e, dict) else ""
            summary = e.get("summary", "") if isinstance(e, dict) else str(e)
            lines.append(f"  [{ts}] {summary}")

    if memory_result.get("semantic"):
        lines.append("WHAT I KNOW:")
        for s in memory_result["semantic"][:3]:
            obj = s.get("object", "")
            pred = s.get("predicate", "")
            conf = s.get("confidence", 1.0)
            lines.append(f"  {pred} {obj} (confidence: {conf:.0%})")

    if memory_result.get("procedural"):
        lines.append("WHAT WORKS:")
        for p in memory_result["procedural"][:2]:
            sit = p.get("situation", "")
            act = p.get("action", "")
            rate = p.get("success_rate", 0.5)
            lines.append(f"  When {sit}: {act} (works {rate:.0%} of the time)")

    return "\n".join(lines) if lines else ""
