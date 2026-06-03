"""
LOVE Consolidated Memory — Unified Persistence & Semantic Recall

All modules write events through this single interface.
Every event is stored in two places:
  1. ChromaDB (semantic search / recall)
  2. JSONL log (raw replay, fast recent access)

On startup the last N hours are replayed to warm in-memory caches.
The notification-learning engine subscribes to all domains.

Usage:
    from core.consolidated_memory import get_consolidated_memory
    cm = get_consolidated_memory()
    cm.write(domain="notification", event_type="urgent", payload={...})
    recent = cm.get_recent(domain="notification", hours=24)
    results = cm.recall("bank transactions today", n=5)
"""

import json
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.execution_guard import log_error

# Reuse existing ChromaDB lazy init
from core.memory import _get_client

DATA_DIR = Path(__file__).parent.parent / "data" / "consolidated"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Domain-scoped JSONL files
LOG_FILES: Dict[str, Path] = {}

def _get_log_file(domain: str) -> Path:
    if domain not in LOG_FILES:
        LOG_FILES[domain] = DATA_DIR / f"{domain}.jsonl"
    return LOG_FILES[domain]


def _now_iso() -> str:
    return datetime.now().isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


class ConsolidatedMemory:
    """
    Singleton unified memory service.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._initialized = False
        self._write_lock = threading.Lock()
        self._batch: List[Dict] = []
        self._batch_lock = threading.Lock()
        self._recent_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self._learn_callbacks: List[callable] = []
        self._running = False
        self._flush_thread: Optional[threading.Thread] = None
        self._chroma_collection = None

    @classmethod
    def get_instance(cls) -> "ConsolidatedMemory":
        with cls._lock:
            if cls._instance is None:
                cls._instance = ConsolidatedMemory()
            return cls._instance

    def _ensure_chroma(self):
        if self._chroma_collection is None:
            self._chroma_collection = _get_client().get_or_create_collection("consolidated_memory")
        return self._chroma_collection

    def start(self):
        """Start the background flush loop and replay recent history."""
        if self._running:
            return
        self._running = True
        self._initialized = True

        # Replay last 24h from JSONL logs to warm in-memory caches
        self._replay_history(hours=24)

        # Start periodic ChromaDB flush
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True, name="LOVE-MemFlush")
        self._flush_thread.start()
        print("[ConsolidatedMemory] Started — replayed last 24h, flush loop active.")

    def stop(self):
        self._running = False
        self._flush_batch()  # Flush remaining items

    # ── Public API ────────────────────────────────────────────────────────

    def write(self, domain: str, event_type: str, payload: Dict[str, Any], text_for_search: str = ""):
        """
        Write an event to consolidated memory.

        Args:
            domain: e.g. "notification", "chat", "finance", "device"
            event_type: e.g. "urgent", "transaction", "message"
            payload: arbitrary JSON-serialisable dict
            text_for_search: the text that will be embedded for semantic search.
                              If empty, falls back to json.dumps(payload).
        """
        # Use nanosecond + atomic counter to guarantee unique IDs even at burst rates
        _id_counter = getattr(self, "_id_counter", 0)
        _id_counter = (_id_counter + 1) % 1_000_000
        self._id_counter = _id_counter
        entry = {
            "id": f"{domain}_{event_type}_{int(time.time() * 1_000_000)}_{_id_counter:06d}",
            "domain": domain,
            "event_type": event_type,
            "timestamp": _now_iso(),
            "payload": payload,
        }

        # 1. Append to JSONL log
        with self._write_lock:
            try:
                with open(_get_log_file(domain), "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, default=str) + "\n")
            except Exception as e:
                log_error(e, module="core.consolidated_memory")

        # 2. Add to in-memory cache for fast recent queries
        self._recent_cache[domain].append(entry)

        # 3. Queue for ChromaDB batch insert
        search_text = text_for_search or json.dumps(payload, default=str)
        with self._batch_lock:
            self._batch.append({
                "id": entry["id"],
                "document": search_text,
                "metadata": {
                    "domain": domain,
                    "event_type": event_type,
                    "timestamp": entry["timestamp"],
                }
            })

        # 4. Notify learners (fire-and-forget)
        self._notify_learners(entry)

    def query(self, domain: str, event_type: str = None, limit: int = 50) -> List[Dict]:
        """Query ChromaDB for events in a domain."""
        try:
            coll = self._ensure_chroma()
            where = {"domain": domain}
            if event_type:
                where["event_type"] = event_type
            results = coll.query(
                query_texts=[""],
                n_results=limit,
                where=where,
                include=["metadatas", "documents"]
            )
            out = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            for doc, meta in zip(docs, metas):
                out.append({
                    "text": doc,
                    "domain": meta.get("domain"),
                    "event_type": meta.get("event_type"),
                    "timestamp": meta.get("timestamp"),
                })
            return out
        except Exception as e:
            log_error(e, module="core.consolidated_memory")
            return []

    def recall(self, query_string: str, n: int = 5, domain: str = None) -> List[Dict]:
        """Semantic search across all (or a specific) domain(s)."""
        try:
            coll = self._ensure_chroma()
            where = {"domain": domain} if domain else None
            results = coll.query(
                query_texts=[query_string],
                n_results=n,
                where=where,
                include=["metadatas", "documents", "distances"]
            )
            out = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            for doc, meta, dist in zip(docs, metas, dists):
                out.append({
                    "text": doc,
                    "domain": meta.get("domain"),
                    "event_type": meta.get("event_type"),
                    "timestamp": meta.get("timestamp"),
                    "distance": dist,
                })
            return out
        except Exception as e:
            log_error(e, module="core.consolidated_memory")
            return []

    def get_recent(self, domain: str = None, hours: int = 24, limit: int = 200) -> List[Dict]:
        """
        Get recent events from JSONL logs (fast, no embedding needed).
        If domain is None, returns all domains.
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        out = []

        domains = [domain] if domain else self._list_domains()
        for dom in domains:
            # 1. Check in-memory cache first
            for entry in reversed(list(self._recent_cache.get(dom, []))):
                ts = _parse_iso(entry.get("timestamp", ""))
                if ts and ts >= cutoff:
                    out.append(entry)
                else:
                    break  # deque is ordered by time

            # 2. Read from disk if cache is small
            if len(out) < limit:
                log_file = _get_log_file(dom)
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    entry = json.loads(line)
                                    ts = _parse_iso(entry.get("timestamp", ""))
                                    if ts and ts >= cutoff:
                                        out.append(entry)
                                except json.JSONDecodeError:
                                    continue
                    except Exception as e:
                        log_error(e, module="core.consolidated_memory")

        # Deduplicate by id (cache + disk may overlap)
        seen_ids = set()
        deduped = []
        for entry in out:
            eid = entry.get("id")
            if eid and eid in seen_ids:
                continue
            if eid:
                seen_ids.add(eid)
            deduped.append(entry)

        # Sort by timestamp descending, limit
        deduped.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return deduped[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Return memory stats per domain."""
        stats = {"total_events": 0, "domains": {}}
        for domain in self._list_domains():
            log_file = _get_log_file(domain)
            count = 0
            if log_file.exists():
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                count += 1
                except Exception:
                    pass
            stats["domains"][domain] = count
            stats["total_events"] += count
        try:
            stats["chroma_count"] = self._ensure_chroma().count()
        except Exception:
            stats["chroma_count"] = 0
        return stats

    def register_learner(self, callback: callable):
        """Register a callback that receives every new entry for autonomous learning."""
        self._learn_callbacks.append(callback)

    def learn_from_history(self, hours: int = 168, domain: str = "notification"):
        """
        Replay historical events to all registered learners.
        Useful for re-training after code updates.
        """
        events = self.get_recent(domain=domain, hours=hours)
        print(f"[ConsolidatedMemory] Replaying {len(events)} {domain} events to learners...")
        for entry in events:
            self._notify_learners(entry)
        print(f"[ConsolidatedMemory] Replay complete.")

    # ── Internal ────────────────────────────────────────────────────────

    def _notify_learners(self, entry: Dict):
        for cb in self._learn_callbacks:
            try:
                cb(entry)
            except Exception as e:
                log_error(e, module="core.consolidated_memory")

    def _flush_loop(self):
        """Flush queued items to ChromaDB every 10 seconds."""
        while self._running:
            time.sleep(10)
            self._flush_batch()

    def _flush_batch(self):
        with self._batch_lock:
            if not self._batch:
                return
            batch = self._batch[:]
            self._batch.clear()

        # Deduplicate by ID — keep first occurrence
        seen_ids = set()
        deduped = []
        for b in batch:
            if b["id"] not in seen_ids:
                seen_ids.add(b["id"])
                deduped.append(b)

        try:
            coll = self._ensure_chroma()
            coll.add(
                documents=[b["document"] for b in deduped],
                metadatas=[b["metadata"] for b in deduped],
                ids=[b["id"] for b in deduped],
            )
        except Exception as e:
            log_error(e, module="core.consolidated_memory")
            # Put back only items whose IDs aren't already queued
            with self._batch_lock:
                existing_ids = {x["id"] for x in self._batch}
                for b in deduped:
                    if b["id"] not in existing_ids:
                        self._batch.append(b)

    def _replay_history(self, hours: int = 24):
        """Load recent events from JSONL into in-memory caches."""
        for domain in self._list_domains():
            events = self._read_log_recent(domain, hours=hours)
            for entry in events:
                self._recent_cache[domain].append(entry)
                # Also notify learners so they catch up
                self._notify_learners(entry)
        print(f"[ConsolidatedMemory] Replayed {sum(len(v) for v in self._recent_cache.values())} events into cache.")

    def _read_log_recent(self, domain: str, hours: int) -> List[Dict]:
        cutoff = datetime.now() - timedelta(hours=hours)
        log_file = _get_log_file(domain)
        if not log_file.exists():
            return []
        out = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = _parse_iso(entry.get("timestamp", ""))
                        if ts and ts >= cutoff:
                            out.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log_error(e, module="core.consolidated_memory")
        return out

    def _list_domains(self) -> List[str]:
        """List all domain JSONL files in the consolidated directory."""
        domains = []
        if DATA_DIR.exists():
            for p in DATA_DIR.glob("*.jsonl"):
                domains.append(p.stem)
        return domains


# ── Singleton accessor ────────────────────────────────────────────────

def get_consolidated_memory() -> ConsolidatedMemory:
    return ConsolidatedMemory.get_instance()


def start_consolidated_memory():
    cm = get_consolidated_memory()
    cm.start()
    return cm
