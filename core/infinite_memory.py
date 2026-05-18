"""
LOVE Infinite Memory Cortex — Wave 12
Utilizes ChromaDB to store and retrieve long-term episodic memory, context, and knowledge.
Provides LOVE with permanent, vectorized recall.
"""

import os
import time
import uuid
import json
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

class InfiniteMemory:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chromadb")
        os.makedirs(self.db_path, exist_ok=True)
        
        if CHROMA_AVAILABLE:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            # Create or get collections
            self.episodic_collection = self.client.get_or_create_collection(
                name="episodic_memory",
                metadata={"hnsw:space": "cosine"}
            )
            self.knowledge_collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.client = None
            
    def store_memory(self, content: str, memory_type: str = "episodic", metadata: Dict[str, Any] = None):
        """Stores a memory string into the vector DB."""
        if not CHROMA_AVAILABLE:
            return "ChromaDB not installed."
            
        metadata = metadata or {}
        metadata["timestamp"] = time.time()
        
        collection = self.episodic_collection if memory_type == "episodic" else self.knowledge_collection
        
        doc_id = str(uuid.uuid4())
        
        try:
            collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            return f"Memory stored successfully with ID {doc_id}."
        except Exception as e:
            return f"Failed to store memory: {str(e)}"
            
    def recall(self, query: str, memory_type: str = "episodic", n_results: int = 5) -> List[Dict[str, Any]]:
        """Recalls relevant memories based on a semantic query."""
        if not CHROMA_AVAILABLE:
            return [{"error": "ChromaDB not installed."}]
            
        collection = self.episodic_collection if memory_type == "episodic" else self.knowledge_collection
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            recalled = []
            if results and 'documents' in results and results['documents']:
                for i in range(len(results['documents'][0])):
                    recalled.append({
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {},
                        "distance": results['distances'][0][i] if 'distances' in results else 0
                    })
            return recalled
        except Exception as e:
            return [{"error": f"Failed to recall: {str(e)}"}]

_memory = None

def get_infinite_memory() -> InfiniteMemory:
    global _memory
    if _memory is None:
        _memory = InfiniteMemory()
    return _memory

def register_memory_tools(registry):
    """Register infinite memory tools into the LOVE Tool Registry."""
    memory = get_infinite_memory()
    
    def recall_memory_tool(query: str, type: str = "episodic"):
        results = memory.recall(query, type)
        return json.dumps(results, indent=2)
        
    def store_memory_tool(content: str, type: str = "episodic", tags: str = ""):
        meta = {"tags": tags} if tags else {}
        return memory.store_memory(content, type, meta)
        
    registry.register_tool(
        name="recall_memory",
        func=recall_memory_tool,
        description="Search LOVE's infinite vector memory for past events, conversations, or facts. Type can be 'episodic' or 'knowledge'.",
        parameters={
            "query": "The semantic search query.",
            "type": "'episodic' for events, 'knowledge' for facts."
        }
    )
    
    registry.register_tool(
        name="store_memory",
        func=store_memory_tool,
        description="Save an important fact or event permanently to LOVE's infinite vector memory.",
        parameters={
            "content": "The information to store.",
            "type": "'episodic' or 'knowledge'.",
            "tags": "Optional comma-separated tags."
        }
    )
