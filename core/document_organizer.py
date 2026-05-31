"""
LOVE Document Organizer — Document Intelligence (Modern AI Pattern)

Most document tools are folders. This organizer:

1. DOCUMENT TRACKING
   - Record documents with type, tags, importance, and location
   - Track document access patterns (frequently used, forgotten)
   - Log document creation, updates, and archival

2. SMART CATEGORIZATION
   - Auto-suggest tags based on document name and type
   - Identify duplicate or near-duplicate documents
   - Detect documents that haven't been accessed in a long time

3. RETRIEVAL INTELLIGENCE
   - Surface documents needed for upcoming events/tasks
   - Suggest documents to archive or delete
   - Find related documents based on tags and content

4. PROACTIVE MANAGEMENT
   - Alert about expiring documents (contracts, warranties, subscriptions)
   - Suggest document cleanup when storage is cluttered
   - Recommend document organization improvements

Architecture:
- record_document(name, type, tags, importance): Log document
- get_document_stats(): Get access and organization insights
- get_retrieval_suggestions(context): Suggest relevant documents
- get_organization_score(): Calculate document health score
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "document_organizer"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DOC_LOG = DATA_DIR / "documents.jsonl"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class Document:
    """A tracked document."""
    doc_id: str = ""
    name: str = ""
    doc_type: str = ""  # contract, receipt, manual, certificate, report, note, image, pdf
    tags: List[str] = field(default_factory=list)
    importance: str = "medium"  # low, medium, high, critical
    location: str = ""  # filepath or url
    size_kb: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    expiry_date: Optional[str] = None
    related_docs: List[str] = field(default_factory=list)
    notes: str = ""


class DocumentOrganizer:
    """
    Intelligent document organizer with proactive management.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._documents: Dict[str, Document] = {}
        self._stats = {
            "total_documents": 0,
            "total_size_mb": 0.0,
            "avg_access_count": 0.0,
            "organization_score": 0,
        }
        self._load_stats()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_document(self, name: str = "", doc_type: str = "", tags: Optional[List[str]] = None, importance: str = "medium", location: str = "", size_kb: float = 0, expiry_date: Optional[str] = None, related_docs: Optional[List[str]] = None, notes: str = "") -> Document:
        """Record or update a document."""
        doc_id = f"doc_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Auto-suggest tags if none provided
        suggested_tags = tags or []
        if not suggested_tags and name:
            type_tags = {
                "contract": ["legal", "agreement"],
                "receipt": ["finance", "purchase"],
                "manual": ["reference", "guide"],
                "certificate": ["credential", "proof"],
                "report": ["work", "analysis"],
                "note": ["personal", "idea"],
                "image": ["media", "visual"],
                "pdf": ["document", "archive"],
            }
            suggested_tags = type_tags.get(doc_type, ["general"])

        doc = Document(
            doc_id=doc_id,
            name=name or "untitled",
            doc_type=doc_type or "document",
            tags=suggested_tags,
            importance=importance,
            location=location,
            size_kb=size_kb,
            expiry_date=expiry_date,
            related_docs=related_docs or [],
            notes=notes,
        )

        with self._lock:
            self._documents[doc_id] = doc
            self._stats["total_documents"] = len(self._documents)
            self._stats["total_size_mb"] += size_kb / 1024
            self._update_stats()

        self._save_stats()
        self._log_document(doc)

        return doc

    def access_document(self, doc_id: str) -> Optional[Document]:
        """Record access to a document."""
        if doc_id not in self._documents:
            return None

        with self._lock:
            self._documents[doc_id].access_count += 1
            self._documents[doc_id].last_accessed = datetime.now().isoformat()

        self._save_stats()
        return self._documents[doc_id]

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_document_stats(self) -> Dict[str, Any]:
        """Get access and organization insights."""
        if not self._documents:
            return {"status": "no_documents"}

        # Type breakdown
        by_type = defaultdict(int)
        for doc in self._documents.values():
            by_type[doc.doc_type] += 1

        # Importance breakdown
        by_importance = defaultdict(int)
        for doc in self._documents.values():
            by_importance[doc.importance] += 1

        # Access patterns
        total_access = sum(d.access_count for d in self._documents.values())
        avg_access = total_access / len(self._documents)

        # Find hot documents (frequently accessed)
        hot_docs = sorted(
            [(d.doc_id, d.name, d.access_count) for d in self._documents.values()],
            key=lambda x: x[2],
            reverse=True,
        )[:5]

        # Find cold documents (not accessed in 6 months)
        six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()
        cold_docs = [(d.doc_id, d.name, d.last_accessed) for d in self._documents.values() if d.last_accessed < six_months_ago]

        # Expiring documents
        now = datetime.now().isoformat()
        expiring = [(d.doc_id, d.name, d.expiry_date) for d in self._documents.values() if d.expiry_date and d.expiry_date > now and d.expiry_date < (datetime.now() + timedelta(days=30)).isoformat()]

        # Duplicate detection (same name, different id)
        name_counts = defaultdict(list)
        for doc_id, doc in self._documents.items():
            name_counts[doc.name].append(doc_id)
        duplicates = {name: ids for name, ids in name_counts.items() if len(ids) > 1}

        return {
            "total_documents": len(self._documents),
            "total_size_mb": round(self._stats["total_size_mb"], 2),
            "by_type": dict(by_type),
            "by_importance": dict(by_importance),
            "avg_access_count": round(avg_access, 1),
            "hot_documents": hot_docs,
            "cold_documents": cold_docs[:5],
            "expiring_soon": expiring[:5],
            "duplicates": list(duplicates.keys())[:5],
            "organization_score": self._stats["organization_score"],
        }

    def get_retrieval_suggestions(self, context: str = "") -> List[Dict[str, Any]]:
        """Suggest relevant documents based on context."""
        suggestions = []
        
        # Context-based matching
        context_keywords = context.lower().split()
        for doc in self._documents.values():
            score = 0
            # Tag matching
            for tag in doc.tags:
                if any(kw in tag.lower() for kw in context_keywords):
                    score += 2
            # Name matching
            if any(kw in doc.name.lower() for kw in context_keywords):
                score += 3
            # Type matching
            if doc.doc_type in context_keywords:
                score += 1
            # Recent access bonus
            if doc.last_accessed > (datetime.now() - timedelta(days=7)).isoformat():
                score += 1

            if score > 0:
                suggestions.append({
                    "doc_id": doc.doc_id,
                    "name": doc.name,
                    "type": doc.doc_type,
                    "relevance": score,
                    "last_accessed": doc.last_accessed[:10],
                })

        return sorted(suggestions, key=lambda x: x["relevance"], reverse=True)[:10]

    def get_organization_score(self) -> int:
        """Calculate document organization health (0-100)."""
        if not self._documents:
            return 0

        # Tag coverage (documents should have tags)
        tagged = sum(1 for d in self._documents.values() if d.tags)
        tag_score = (tagged / len(self._documents)) * 100

        # Importance distribution (should have some high importance)
        high_importance = sum(1 for d in self._documents.values() if d.importance in ["high", "critical"])
        importance_score = min(100, high_importance * 10)

        # Access recency
        recent = sum(1 for d in self._documents.values() if d.last_accessed > (datetime.now() - timedelta(days=90)).isoformat())
        recency_score = (recent / len(self._documents)) * 100

        # No duplicates bonus
        name_counts = defaultdict(int)
        for doc in self._documents.values():
            name_counts[doc.name] += 1
        duplicates = sum(1 for count in name_counts.values() if count > 1)
        duplicate_score = max(0, 100 - duplicates * 10)

        overall = round(tag_score * 0.3 + importance_score * 0.2 + recency_score * 0.3 + duplicate_score * 0.2)
        return min(100, overall)

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self):
        """Update running statistics."""
        if self._documents:
            self._stats["avg_access_count"] = round(sum(d.access_count for d in self._documents.values()) / len(self._documents), 1)
            self._stats["organization_score"] = self.get_organization_score()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            data = {
                **self._stats,
                "documents": {k: {
                    "doc_id": v.doc_id,
                    "name": v.name,
                    "doc_type": v.doc_type,
                    "tags": v.tags,
                    "importance": v.importance,
                    "location": v.location,
                    "size_kb": v.size_kb,
                    "created_at": v.created_at,
                    "last_accessed": v.last_accessed,
                    "access_count": v.access_count,
                    "expiry_date": v.expiry_date,
                    "related_docs": v.related_docs,
                    "notes": v.notes,
                } for k, v in self._documents.items()},
            }
            STATS_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                data = json.loads(STATS_DB.read_text())
                self._stats.update({k: v for k, v in data.items() if k in self._stats})
                for k, v in data.get("documents", {}).items():
                    self._documents[k] = Document(**v)
        except Exception:
            pass

    def _log_document(self, doc: Document):
        try:
            with open(DOC_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": doc.created_at,
                    "doc_id": doc.doc_id,
                    "name": doc.name,
                    "type": doc.doc_type,
                    "importance": doc.importance,
                    "size_kb": doc.size_kb,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_do_instance: Optional[DocumentOrganizer] = None
_do_lock = threading.Lock()


def get_document_organizer() -> DocumentOrganizer:
    global _do_instance
    with _do_lock:
        if _do_instance is None:
            _do_instance = DocumentOrganizer()
        return _do_instance
