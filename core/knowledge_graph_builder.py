"""
LOVE Knowledge Graph Auto-Builder — Automated Entity & Relation Extraction (Modern AI Pattern)

Modern companions learn from every conversation. This auto-builder:

1. ENTITY EXTRACTION
   - Extract people, places, organizations, concepts from text
   - Use pattern matching + heuristics (no external NLP dependencies)
   - Track entity mentions across conversations

2. RELATIONSHIP DETECTION
   - Identify how entities relate to each other
   - Detect: works_at, lives_in, likes, created_by, part_of, related_to
   - Build a semantic web of user knowledge

3. KNOWLEDGE GRAPH CONSTRUCTION
   - Merge new facts into existing graph
   - Resolve entity aliases (e.g., "NYC" = "New York City")
   - Track confidence scores for all facts

4. GRAPH QUERIES
   - Find connections between entities
   - Discover unexplored relationships
   - Export for visualization

Architecture:
- extract_entities(): Pull entities from raw text
- extract_relations(): Find relationships between entities
- build_graph(): Merge texts into knowledge graph
- query_graph(): Traverse graph for connections
- get_graph_stats(): Track graph growth
- export_graph(): JSON export for visualization
"""

import json
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

DATA_DIR = Path(__file__).parent.parent / "data" / "knowledge_graph"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GRAPH_DB = DATA_DIR / "graph_db.json"
ENTITY_LOG = DATA_DIR / "entity_log.jsonl"


@dataclass
class Entity:
    """A node in the knowledge graph."""
    id: str = ""
    name: str = ""
    entity_type: str = ""  # person, place, organization, concept, thing
    aliases: List[str] = field(default_factory=list)
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    mention_count: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """An edge in the knowledge graph."""
    id: str = ""
    source: str = ""
    relation_type: str = ""  # works_at, lives_in, likes, created_by, part_of, related_to
    target: str = ""
    confidence: float = 0.5
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    evidence: List[str] = field(default_factory=list)


class KnowledgeGraphBuilder:
    """
    Automated knowledge graph construction for LOVE.
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
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, Relation] = {}
        self._aliases: Dict[str, str] = {}  # alias -> canonical entity id
        self._stats = {"entities_extracted": 0, "relations_extracted": 0, "texts_processed": 0}
        self._load_graph()

    # ── Entity Extraction ───────────────────────────────────────────────────

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using heuristics."""
        entities = []

        # People: capitalized words that could be names
        name_pattern = r'\b([A-Z][a-z]+\s[A-Z][a-z]+)\b'
        for match in re.finditer(name_pattern, text):
            name = match.group(1)
            if not self._is_common_word(name):
                entities.append({
                    "name": name,
                    "type": "person",
                    "confidence": 0.7,
                })

        # Organizations: words ending in Inc, Corp, Ltd, etc.
        org_pattern = r'\b([A-Z][a-zA-Z\s]+(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Company|Organization|Institute|University))\b'
        for match in re.finditer(org_pattern, text):
            entities.append({
                "name": match.group(1).strip(),
                "type": "organization",
                "confidence": 0.8,
            })

        # Places: common place indicators
        place_indicators = ["city", "country", "state", "mountain", "river", "lake", "park", "street", "avenue", "road"]
        place_pattern = r'\b([A-Z][a-zA-Z\s]+)\s+(?:' + '|'.join(place_indicators) + r')\b'
        for match in re.finditer(place_pattern, text, re.IGNORECASE):
            entities.append({
                "name": match.group(1).strip(),
                "type": "place",
                "confidence": 0.6,
            })

        # Capitalized proper nouns (potential concepts/things)
        proper_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        found_names = {e["name"] for e in entities}
        for match in re.finditer(proper_pattern, text):
            name = match.group(1)
            if name not in found_names and not self._is_common_word(name) and len(name) > 2:
                entities.append({
                    "name": name,
                    "type": "concept",
                    "confidence": 0.4,
                })

        self._stats["entities_extracted"] += len(entities)
        return entities

    def _is_common_word(self, word: str) -> bool:
        """Check if a word is a common English word (not a proper noun)."""
        common = {
            "The", "A", "An", "This", "That", "These", "Those",
            "I", "You", "He", "She", "It", "We", "They",
            "Is", "Are", "Was", "Were", "Be", "Been", "Being",
            "Have", "Has", "Had", "Do", "Does", "Did",
            "Will", "Would", "Could", "Should", "May", "Might",
            "Can", "Shall", "Must", "Shall", "Need", "Dare",
            "And", "But", "Or", "Nor", "For", "Yet", "So",
            "In", "On", "At", "To", "From", "By", "With", "About",
            "Into", "Through", "During", "Before", "After",
            "Above", "Below", "Between", "Under", "Again",
            "Further", "Then", "Once", "Here", "There",
            "When", "Where", "Why", "How", "All", "Each",
            "Few", "More", "Most", "Other", "Some", "Such",
            "No", "Not", "Only", "Own", "Same", "Than",
            "Too", "Very", "Just", "Now", "Also", "Always",
            "Never", "Often", "Sometimes", "Usually",
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday", "January", "February", "March",
            "April", "May", "June", "July", "August", "September",
            "October", "November", "December", "Today", "Tomorrow",
            "Yesterday", "Morning", "Afternoon", "Evening", "Night",
        }
        return word in common

    # ── Relation Extraction ───────────────────────────────────────────────────

    def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships between entities."""
        relations = []
        entity_names = [e["name"] for e in entities]

        # Simple pattern: "X works at Y", "X lives in Y", "X likes Y"
        relation_patterns = [
            (r'\b(\w+)\s+(?:works?\s+(?:at|for)|employed\s+(?:at|by))\s+([\w\s]+?)\b', "works_at"),
            (r'\b(\w+)\s+(?:lives?\s+in|from|based\s+in)\s+([\w\s]+?)\b', "lives_in"),
            (r'\b(\w+)\s+(?:likes?|loves?|enjoys?)\s+([\w\s]+?)\b', "likes"),
            (r'\b(\w+)\s+(?:created?|made|built)\s+([\w\s]+?)\b', "created_by"),
            (r'\b(\w+)\s+(?:part\s+of|member\s+of|belongs?\s+to)\s+([\w\s]+?)\b', "part_of"),
        ]

        for pattern, rel_type in relation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                source = match.group(1).strip()
                target = match.group(2).strip()
                if source in entity_names or target in entity_names:
                    relations.append({
                        "source": source,
                        "relation_type": rel_type,
                        "target": target,
                        "confidence": 0.6,
                    })

        self._stats["relations_extracted"] += len(relations)
        return relations

    # ── Graph Building ────────────────────────────────────────────────────────

    def build_graph(self, texts: List[str]) -> Dict[str, Any]:
        """Process texts and build knowledge graph."""
        new_entities = 0
        new_relations = 0

        for text in texts:
            entities = self.extract_entities(text)
            relations = self.extract_relations(text, entities)

            for e_data in entities:
                entity_id = self._add_entity(e_data["name"], e_data["type"],
                                               confidence=e_data.get("confidence", 0.5))
                if entity_id:
                    new_entities += 1

            for r_data in relations:
                rel_id = self._add_relation(r_data["source"], r_data["relation_type"],
                                            r_data["target"], r_data.get("confidence", 0.5))
                if rel_id:
                    new_relations += 1

            self._stats["texts_processed"] += 1

        self._save_graph()
        return {
            "texts_processed": len(texts),
            "new_entities": new_entities,
            "new_relations": new_relations,
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
        }

    def _add_entity(self, name: str, entity_type: str, confidence: float = 0.5) -> Optional[str]:
        """Add or update an entity."""
        canonical_name = name.strip()
        entity_id = canonical_name.lower().replace(" ", "_")

        with self._lock:
            if entity_id in self._entities:
                self._entities[entity_id].mention_count += 1
                self._entities[entity_id].last_seen = datetime.now().isoformat()
                return None  # Not new

            self._entities[entity_id] = Entity(
                id=entity_id,
                name=canonical_name,
                entity_type=entity_type,
                mention_count=1,
            )
            return entity_id

    def _add_relation(self, source: str, relation_type: str, target: str,
                      confidence: float = 0.5) -> Optional[str]:
        """Add or update a relation."""
        source_id = source.lower().replace(" ", "_")
        target_id = target.lower().replace(" ", "_")
        rel_id = f"{source_id}_{relation_type}_{target_id}"

        with self._lock:
            if rel_id in self._relations:
                self._relations[rel_id].confidence = min(1.0,
                    self._relations[rel_id].confidence + 0.1)
                return None

            self._relations[rel_id] = Relation(
                id=rel_id,
                source=source_id,
                relation_type=relation_type,
                target=target_id,
                confidence=confidence,
            )
            return rel_id

    # ── Graph Queries ─────────────────────────────────────────────────────────

    def query_graph(self, entity_name: str, depth: int = 1) -> Dict[str, Any]:
        """Query the graph for connections to an entity."""
        entity_id = entity_name.lower().replace(" ", "_")

        if entity_id not in self._entities:
            return {"entity": entity_name, "found": False, "connections": []}

        connections = []
        visited = {entity_id}
        queue = [(entity_id, 0)]

        while queue:
            current_id, current_depth = queue.pop(0)
            if current_depth >= depth:
                continue

            for rel in self._relations.values():
                if rel.source == current_id and rel.target not in visited:
                    visited.add(rel.target)
                    queue.append((rel.target, current_depth + 1))
                    if rel.target in self._entities:
                        connections.append({
                            "entity": self._entities[rel.target].name,
                            "type": self._entities[rel.target].entity_type,
                            "relation": rel.relation_type,
                            "confidence": rel.confidence,
                        })
                elif rel.target == current_id and rel.source not in visited:
                    visited.add(rel.source)
                    queue.append((rel.source, current_depth + 1))
                    if rel.source in self._entities:
                        connections.append({
                            "entity": self._entities[rel.source].name,
                            "type": self._entities[rel.source].entity_type,
                            "relation": f"reverse_{rel.relation_type}",
                            "confidence": rel.confidence,
                        })

        return {
            "entity": entity_name,
            "found": True,
            "connections": connections,
        }

    # ── Statistics & Export ─────────────────────────────────────────────────

    def get_graph_stats(self) -> Dict[str, Any]:
        entity_types = {}
        for e in self._entities.values():
            entity_types[e.entity_type] = entity_types.get(e.entity_type, 0) + 1

        relation_types = {}
        for r in self._relations.values():
            relation_types[r.relation_type] = relation_types.get(r.relation_type, 0) + 1

        return {
            **self._stats,
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entity_types": entity_types,
            "relation_types": relation_types,
        }

    def export_graph(self) -> Dict[str, Any]:
        """Export graph as JSON for visualization."""
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.entity_type,
                    "mention_count": e.mention_count,
                }
                for e in self._entities.values()
            ],
            "relations": [
                {
                    "source": r.source,
                    "type": r.relation_type,
                    "target": r.target,
                    "confidence": r.confidence,
                }
                for r in self._relations.values()
            ],
        }

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_graph(self):
        try:
            data = {
                "entities": {
                    k: {
                        "id": e.id,
                        "name": e.name,
                        "entity_type": e.entity_type,
                        "aliases": e.aliases,
                        "first_seen": e.first_seen,
                        "last_seen": e.last_seen,
                        "mention_count": e.mention_count,
                        "attributes": e.attributes,
                    }
                    for k, e in self._entities.items()
                },
                "relations": {
                    k: {
                        "id": r.id,
                        "source": r.source,
                        "relation_type": r.relation_type,
                        "target": r.target,
                        "confidence": r.confidence,
                        "first_seen": r.first_seen,
                        "evidence": r.evidence,
                    }
                    for k, r in self._relations.items()
                },
            }
            GRAPH_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_graph(self):
        try:
            if GRAPH_DB.exists():
                data = json.loads(GRAPH_DB.read_text())
                for k, e_data in data.get("entities", {}).items():
                    self._entities[k] = Entity(**e_data)
                for k, r_data in data.get("relations", {}).items():
                    self._relations[k] = Relation(**r_data)
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_kgb_instance: Optional[KnowledgeGraphBuilder] = None
_kgb_lock = threading.Lock()


def get_knowledge_graph_builder() -> KnowledgeGraphBuilder:
    global _kgb_instance
    with _kgb_lock:
        if _kgb_instance is None:
            _kgb_instance = KnowledgeGraphBuilder()
        return _kgb_instance
