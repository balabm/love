"""
Epistemic Pruner — Sleep Cycle for ChromaDB

Nightly, LOVE extracts absolute semantic truths (Karthi's preferences, solved .NET bugs)
into the Knowledge Graph and permanently deletes the raw, token-heavy conversation logs.

Prevents ChromaDB bloat. Enforces the "Epistemic Pruning" directive.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
CONVERSATION_LOG = DATA_DIR / "conversations.jsonl"
PRUNE_MARKER = DATA_DIR / "last_prune.txt"

# Optional integrations
try:
    from core.long_term_memory import add_episodic, add_semantic
    LTM_AVAILABLE = True
except Exception:
    LTM_AVAILABLE = False

try:
    import chromadb
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False


def _read_recent_conversations(hours: int = 24) -> List[Dict[str, Any]]:
    """Pull recent conversation turns from the structured conversation log."""
    if not CONVERSATION_LOG.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours)
    conversations = []
    try:
        with open(CONVERSATION_LOG, "r", encoding="utf-8") as f:
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
                    log_error(e, module="core.epistemic_pruner")
    except Exception as e:
        log_error(e, module="core.epistemic_pruner", context={"action": "read_conversations"})
    return conversations


def _extract_truths(conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract absolute semantic truths from conversations.
    Simple heuristic: look for explicit preference statements and bug fixes.
    """
    truths = []
    for entry in conversations:
        text = entry.get("text", entry.get("message", ""))
        if not text:
            continue

        # Preference patterns
        lower = text.lower()
        if "prefer" in lower or "like" in lower or "hate" in lower:
            truths.append({
                "type": "preference",
                "content": text[:500],
                "source": entry.get("timestamp", ""),
                "confidence": 0.7,
            })

        # Bug fix patterns
        if "fixed" in lower or "solved" in lower or "bug" in lower:
            truths.append({
                "type": "bug_fix",
                "content": text[:500],
                "source": entry.get("timestamp", ""),
                "confidence": 0.8,
            })

        # Goal / project patterns
        if "working on" in lower or "project" in lower or "goal" in lower:
            truths.append({
                "type": "goal",
                "content": text[:500],
                "source": entry.get("timestamp", ""),
                "confidence": 0.6,
            })

    return truths


def _store_truths(truths: List[Dict[str, Any]]) -> int:
    """Store extracted truths into the Knowledge Graph (long-term memory)."""
    if not LTM_AVAILABLE:
        return 0

    stored = 0
    for truth in truths:
        try:
            if truth["type"] == "preference":
                add_semantic(
                    category="user_preferences",
                    content=truth["content"],
                    source="epistemic_pruner",
                    importance=truth["confidence"],
                )
            elif truth["type"] == "bug_fix":
                add_semantic(
                    category="solved_bugs",
                    content=truth["content"],
                    source="epistemic_pruner",
                    importance=truth["confidence"],
                )
            elif truth["type"] == "goal":
                add_episodic(
                    summary=truth["content"][:200],
                    detail=truth["content"],
                    emotion="neutral",
                    intensity=truth["confidence"],
                    tags=["goal", "pruned"],
                    source="epistemic_pruner",
                )
            stored += 1
        except Exception as e:
            log_error(e, module="core.epistemic_pruner", context={"action": "store_truth", "truth_type": truth.get("type")})
    return stored


def _prune_chroma_collection(collection_name: str = "love_memory") -> int:
    """Delete old entries from a ChromaDB collection to prevent bloat."""
    if not CHROMA_AVAILABLE:
        return 0

    try:
        client = chromadb.PersistentClient(path=str(DATA_DIR / "memory"))
        collection = client.get_or_create_collection(name=collection_name)

        # Get all entries
        results = collection.get(include=["metadatas"])
        if not results or not results["ids"]:
            return 0

        cutoff = datetime.now() - timedelta(days=7)
        ids_to_delete = []
        for entry_id, metadata in zip(results["ids"], results["metadatas"]):
            ts = metadata.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    if dt < cutoff:
                        ids_to_delete.append(entry_id)
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.epistemic_pruner")

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"[EpistemicPruner] Pruned {len(ids_to_delete)} old entries from {collection_name}")
            return len(ids_to_delete)
    except Exception as e:
        log_error(e, module="core.epistemic_pruner", context={"action": "prune_chroma", "collection": collection_name})
    return 0


def _delete_raw_logs():
    """Permanently delete the raw conversation log after extraction."""
    try:
        if CONVERSATION_LOG.exists():
            # Rotate instead of delete for safety (keep last 24h)
            rotated = DATA_DIR / f"conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            CONVERSATION_LOG.rename(rotated)
            # Truncate the main log
            CONVERSATION_LOG.write_text("")
            print("[EpistemicPruner] Rotated conversation log")
    except Exception as e:
        log_error(e, module="core.epistemic_pruner", context={"action": "delete_raw_logs"})


def run_prune_cycle() -> Dict[str, Any]:
    """
    Run one epistemic pruning cycle.
    Extract truths → Store in KG → Prune ChromaDB → Rotate raw logs.
    """
    print("[EpistemicPruner] Starting sleep cycle...")
    start = datetime.now()

    conversations = _read_recent_conversations(hours=24)
    truths = _extract_truths(conversations)
    stored = _store_truths(truths)

    pruned_memories = _prune_chroma_collection("love_memory")
    pruned_ltm = _prune_chroma_collection("love_episodic")

    _delete_raw_logs()

    PRUNE_MARKER.write_text(datetime.now().isoformat())

    elapsed = (datetime.now() - start).total_seconds()
    result = {
        "conversations_scanned": len(conversations),
        "truths_extracted": len(truths),
        "truths_stored": stored,
        "pruned_memories": pruned_memories,
        "pruned_episodic": pruned_ltm,
        "elapsed_seconds": elapsed,
    }
    print(f"[EpistemicPruner] Sleep cycle complete: {result}")
    return result


def should_prune() -> bool:
    """Check if enough time has passed since last prune (default: 24h)."""
    if not PRUNE_MARKER.exists():
        return True
    try:
        last = datetime.fromisoformat(PRUNE_MARKER.read_text().strip())
        return (datetime.now() - last).total_seconds() > 86400
    except Exception:
        return True


# ── Background thread helper ─────────────────────────────────────────────────

_pruner_thread: Optional[threading.Thread] = None
_pruner_running = False


def start_pruner_daemon():
    """Start a background thread that prunes during sleep phases."""
    global _pruner_running, _pruner_thread
    if _pruner_running:
        return
    _pruner_running = True

    def _loop():
        while _pruner_running:
            try:
                # Only prune during night hours (23:00 - 05:00)
                hour = datetime.now().hour
                if hour >= 23 or hour <= 5:
                    if should_prune():
                        run_prune_cycle()
            except Exception as e:
                log_error(e, module="core.epistemic_pruner", context={"action": "daemon_loop"})
            time.sleep(3600)  # Check every hour

    _pruner_thread = threading.Thread(target=_loop, daemon=True, name="LOVE-EpistemicPruner")
    _pruner_thread.start()
    print("[EpistemicPruner] Daemon started")


def stop_pruner_daemon():
    global _pruner_running
    _pruner_running = False
