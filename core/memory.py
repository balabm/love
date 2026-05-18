import chromadb
from datetime import datetime
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
    # Save to local ChromaDB
    collection.add(
        documents=[f"User: {user_input}\nLove: {response}"],
        metadatas=[{"mode": mode, "timestamp": datetime.now().isoformat()}],
        ids=[datetime.now().isoformat()],
    )
    
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
