import chromadb
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from core.execution_guard import log_error

load_dotenv()

# -- Lazy ChromaDB initialisation --
# Opening a PersistentClient at module-import time blocks startup on network/
# cloud-synced paths (OneDrive, Dropbox) because SQLite migrations run
# synchronously. Defer the connection until first actual use.
_client = None
_collection = None

def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path="./data/memory")
    return _client

def _get_collection():
    global _collection
    if _collection is None:
        _collection = _get_client().get_or_create_collection("love_memory")
    return _collection

# Shims for any code that imported these names directly
client = None
collection = None

# Neural Sync integration (optional)
try:
    from core.sync import get_sync_memory, get_user_state
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False


def _get_device_id() -> str:
    """Get current device ID from environment or default."""
    import os
    import socket
    device_id = os.getenv("LOVE_DEVICE_ID")
    if not device_id:
        # Generate from hostname
        device_id = socket.gethostname().replace('.', '_')
    return device_id


def _get_device_type() -> str:
    """Get device type from environment."""
    import os
    return os.getenv("LOVE_DEVICE_TYPE", "unknown")

def save_memory(user_input: str, response: str, mode: str = "general"):
    """Save a conversation turn to memory and sync across devices."""

    # -- LIVING SUBSTRATE feedback: response goes back through predictive layers --
    try:
        from core.hierarchical_predictive_coding import get_hpc
        get_hpc().feed(response, source="love")
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")
    try:
        # Implicit reward: short user follow-ups w/ thanks => positive, corrections => negative
        from core.moe_router import get_moe_router
        r_signal = 0.0
        ul = user_input.lower()
        if any(w in ul for w in ["thanks", "perfect", "great", "exactly", "helpful"]):
            r_signal = 0.6
        elif any(w in ul for w in ["wrong", "no that", "not quite", "actually,", "i meant"]):
            r_signal = -0.6
        if r_signal != 0.0:
            get_moe_router().reinforce("core_agent_chat", user_input, r_signal)
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")
    # [FEEDBACK-PATCH] implicit feedback detection
    try:
        from core.feedback_collector import get_feedback_collector
        _fc = get_feedback_collector()
        _prev = getattr(_fc, '_last_user_text', '')
        _sig = _fc.detect_implicit(user_input, _prev, response, 0)
        _fc._last_user_text = user_input
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")
    # Save to local ChromaDB
    _get_collection().add(
        documents=[f"User: {user_input}\nLove: {response}"],
        metadatas=[{"mode": mode, "timestamp": datetime.now().isoformat()}],
        ids=[datetime.now().isoformat()],
    )

    # Also write to Consolidated Memory for unified persistence and learning
    try:
        from core.consolidated_memory import get_consolidated_memory
        get_consolidated_memory().write(
            domain="chat",
            event_type=mode,
            payload={
                "user": user_input,
                "love": response,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
            },
            text_for_search=f"User: {user_input}\nLove: {response}",
        )
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")
    
    # Sync to Neural Sync if available
    if SYNC_AVAILABLE:
        try:
            device_id = _get_device_id()
            sync_mem = get_sync_memory()
            sync_mem.sync_entry(
                device_id=device_id,
                category=f"chat_{mode}",
                content=f"User: {user_input}\nLove: {response}",
                metadata={"mode": mode, "user_input": user_input[:100]}
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory")

def recall_memory(query: str, n: int = 5, mode: str = None):
    """Recall relevant past memories."""
    where = {"mode": mode} if mode else None
    try:
        results = _get_collection().query(
            query_texts=[query],
            n_results=n,
            where=where
        )
        if results["documents"][0]:
            return "\n".join(results["documents"][0])
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")
    return ""

def save_log(category: str, data: dict):
    """Save structured life logs — mood, fitness, finance etc. Syncs across devices."""
    # Save to local ChromaDB
    log_collection = _get_client().get_or_create_collection(f"love_{category}")
    log_collection.add(
        documents=[str(data)],
        metadatas=[{"timestamp": datetime.now().isoformat()}],
        ids=[datetime.now().isoformat()],
    )

    # Also write to Consolidated Memory for unified persistence
    try:
        from core.consolidated_memory import get_consolidated_memory
        get_consolidated_memory().write(
            domain=category,
            event_type="log",
            payload={**data, "timestamp": datetime.now().isoformat()},
            text_for_search=str(data),
        )
    except Exception as e:
        from core.execution_guard import log_error
        log_error(e, module="core.memory")

    # Sync to Neural Sync if available
    if SYNC_AVAILABLE:
        try:
            device_id = _get_device_id()
            sync_mem = get_sync_memory()
            user_state = get_user_state()
            
            # Push to synced memory
            sync_mem.sync_entry(
                device_id=device_id,
                category=category,
                content=str(data),
                metadata={"category": category, **data}
            )
            
            # Update user state for cross-device consistency
            user_state.set_state(
                f"last_{category}",
                data,
                device_id=device_id,
                priority=8 if category in ['work_status', 'portfolio_update'] else 5
            )
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.memory")

def prune_short_term_memory(days_to_keep: int = 7):
    """Prune old entries from the love_memory collection to prevent unbounded memory growth.
    
    Args:
        days_to_keep: Number of days to retain. Entries older than this will be deleted.
    """
    try:
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_iso = cutoff_date.isoformat()
        
        # Query for all entries to find old ones
        # Note: ChromaDB doesn't support direct timestamp filtering in where clause,
        # so we need to get all entries and filter manually
        results = _get_collection().get(include=["metadatas"])
        
        if not results or not results["ids"]:
            return
        
        # Find IDs of entries older than cutoff
        ids_to_delete = []
        for entry_id, metadata in zip(results["ids"], results["metadatas"]):
            timestamp = metadata.get("timestamp")
            if timestamp and timestamp < cutoff_iso:
                ids_to_delete.append(entry_id)
        
        # Delete old entries if any found
        if ids_to_delete:
            _get_collection().delete(ids=ids_to_delete)
            logging.info(f"Pruned {len(ids_to_delete)} old memory entries (older than {days_to_keep} days)")
        
    except Exception as e:
        logging.error(f"Failed to prune short-term memory: {e}")


def get_memory_stats() -> dict:
    """Return basic memory statistics for health dashboards."""
    try:
        collection = _get_collection()
        count = collection.count()
        return {"total_memories": count, "status": "ready"}
    except Exception:
        return {"total_memories": 0, "status": "unavailable"}