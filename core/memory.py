import chromadb
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

load_dotenv()

client = chromadb.PersistentClient(path="./data/memory")
collection = client.get_or_create_collection("love_memory")

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
    except Exception:
        pass
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
    except Exception:
        pass
    # [FEEDBACK-PATCH] implicit feedback detection
    try:
        from core.feedback_collector import get_feedback_collector
        _fc = get_feedback_collector()
        _prev = getattr(_fc, '_last_user_text', '')
        _sig = _fc.detect_implicit(user_input, _prev, response, 0)
        _fc._last_user_text = user_input
    except Exception:
        pass
    # Save to local ChromaDB
    collection.add(
        documents=[f"User: {user_input}\nLove: {response}"],
        metadatas=[{"mode": mode, "timestamp": datetime.now().isoformat()}],
        ids=[datetime.now().isoformat()],
    )
    
    # Also write to local structured log for memory consolidation
    import json
    from pathlib import Path
    try:
        log_file = Path(__file__).parent.parent / "data" / "conversations.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "love": response,
            "mode": mode
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
    
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
        except Exception:
            pass  # Fail silently if sync fails

def recall_memory(query: str, n: int = 5, mode: str = None):
    """Recall relevant past memories."""
    where = {"mode": mode} if mode else None
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n,
            where=where
        )
        if results["documents"][0]:
            return "\n".join(results["documents"][0])
    except Exception:
        pass
    return ""

def save_log(category: str, data: dict):
    """Save structured life logs — mood, fitness, finance etc. Syncs across devices."""
    # Save to local ChromaDB
    log_collection = client.get_or_create_collection(f"love_{category}")
    log_collection.add(
        documents=[str(data)],
        metadatas=[{"timestamp": datetime.now().isoformat()}],
        ids=[datetime.now().isoformat()],
    )
    
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
        except Exception:
            pass  # Fail silently if sync fails

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
        results = collection.get(include=["metadatas"])
        
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
            collection.delete(ids=ids_to_delete)
            logging.info(f"Pruned {len(ids_to_delete)} old memory entries (older than {days_to_keep} days)")
        
    except Exception as e:
        logging.error(f"Failed to prune short-term memory: {e}")