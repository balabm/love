"""
World Model for LOVE
Models the world beyond user data - general knowledge, relationships, and how things work.
This enables LOVE to reason about the world, not just about Karthi.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque

from core.settings import get_settings

SETTINGS = get_settings()


class KnowledgeType(Enum):
    """Types of knowledge in the world model"""
    FACT = "fact"  # Objective facts
    CONCEPT = "concept"  # Abstract concepts
    RELATIONSHIP = "relationship"  # Relationships between entities
    PROCEDURE = "procedure"  # How to do things
    PRINCIPLE = "principle"  # General principles
    PATTERN = "pattern"  # Repeating patterns
    CAUSAL = "causal"  # Cause-effect relationships


class Confidence(Enum):
    """Confidence levels for knowledge"""
    CERTAIN = 1.0
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4
    SPECULATIVE = 0.2


@dataclass
class Knowledge:
    """A piece of knowledge about the world"""
    id: str
    type: KnowledgeType
    subject: str
    predicate: str  # What is being said about the subject
    object: Optional[str] = None  # Object of the relationship
    confidence: float = 0.5
    source: str = "general"  # Where this knowledge came from
    evidence: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0


@dataclass
class ConceptNode:
    """A node in the knowledge graph representing a concept"""
    name: str
    category: str  # technology, science, art, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    related: Dict[str, float] = field(default_factory=dict)  # Related concepts and strength
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class CausalLink:
    """A causal relationship between events/states"""
    cause: str
    effect: str
    strength: float  # 0-1, how strong the causal link is
    conditions: List[str] = field(default_factory=list)  # Conditions for this link to hold
    confidence: float = 0.5
    examples: List[str] = field(default_factory=list)


class WorldModel:
    """
    World model that stores general knowledge about the world.
    Enables LOVE to reason beyond just Karthi's data.
    """
    
    def __init__(self):
        self.knowledge: Dict[str, Knowledge] = {}
        self.concepts: Dict[str, ConceptNode] = {}
        self.causal_links: List[CausalLink] = []
        self.lock = threading.Lock()
        self._load_knowledge()
        self._initialize_base_knowledge()
    
    def _load_knowledge(self):
        """Load world knowledge from storage"""
        try:
            world_file = SETTINGS.data_dir / "world_model.json"
            if world_file.exists():
                with open(world_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load knowledge
                    for k_id, k_data in data.get("knowledge", {}).items():
                        self.knowledge[k_id] = Knowledge(
                            id=k_id,
                            type=KnowledgeType(k_data["type"]),
                            subject=k_data["subject"],
                            predicate=k_data["predicate"],
                            object=k_data.get("object"),
                            confidence=k_data["confidence"],
                            source=k_data.get("source", "general"),
                            evidence=k_data.get("evidence", []),
                            related_concepts=k_data.get("related_concepts", []),
                            created_at=k_data["created_at"],
                            last_accessed=k_data.get("last_accessed"),
                            access_count=k_data.get("access_count", 0)
                        )
                    
                    # Load concepts
                    for c_name, c_data in data.get("concepts", {}).items():
                        self.concepts[c_name] = ConceptNode(
                            name=c_name,
                            category=c_data["category"],
                            properties=c_data.get("properties", {}),
                            related=c_data.get("related", {}),
                            last_updated=c_data.get("last_updated")
                        )
                    
                    # Load causal links
                    for cl_data in data.get("causal_links", []):
                        self.causal_links.append(CausalLink(
                            cause=cl_data["cause"],
                            effect=cl_data["effect"],
                            strength=cl_data["strength"],
                            conditions=cl_data.get("conditions", []),
                            confidence=cl_data["confidence"],
                            examples=cl_data.get("examples", [])
                        ))
                    
        except Exception as e:
            print(f"[WorldModel] Error loading knowledge: {e}")
    
    def _save_knowledge(self):
        """Save world knowledge to storage"""
        try:
            world_file = SETTINGS.data_dir / "world_model.json"
            with self.lock:
                data = {
                    "knowledge": {
                        k_id: {
                            "type": k.type.value,
                            "subject": k.subject,
                            "predicate": k.predicate,
                            "object": k.object,
                            "confidence": k.confidence,
                            "source": k.source,
                            "evidence": k.evidence,
                            "related_concepts": k.related_concepts,
                            "created_at": k.created_at,
                            "last_accessed": k.last_accessed,
                            "access_count": k.access_count
                        }
                        for k_id, k in self.knowledge.items()
                    },
                    "concepts": {
                        c_name: {
                            "category": c.category,
                            "properties": c.properties,
                            "related": c.related,
                            "last_updated": c.last_updated
                        }
                        for c_name, c in self.concepts.items()
                    },
                    "causal_links": [
                        {
                            "cause": cl.cause,
                            "effect": cl.effect,
                            "strength": cl.strength,
                            "conditions": cl.conditions,
                            "confidence": cl.confidence,
                            "examples": cl.examples
                        }
                        for cl in self.causal_links
                    ]
                }
                with open(world_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WorldModel] Error saving knowledge: {e}")
    
    def _initialize_base_knowledge(self):
        """Initialize base knowledge about the world"""
        if not self.knowledge:
            # Technology knowledge
            self._add_knowledge(
                KnowledgeType.FACT,
                subject="AI",
                predicate="is a field of computer science",
                object="artificial intelligence",
                confidence=1.0,
                source="general"
            )
            
            self._add_knowledge(
                KnowledgeType.FACT,
                subject="Python",
                predicate="is a programming language",
                object="high-level",
                confidence=1.0,
                source="general"
            )
            
            self._add_knowledge(
                KnowledgeType.FACT,
                subject="React",
                predicate="is a JavaScript library",
                object="UI framework",
                confidence=1.0,
                source="general"
            )
            
            self._add_knowledge(
                KnowledgeType.FACT,
                subject="TypeScript",
                predicate="is a superset of JavaScript",
                object="typed",
                confidence=1.0,
                source="general"
            )
            
            # Causal relationships
            self.causal_links.append(CausalLink(
                cause="lack of sleep",
                effect="decreased cognitive performance",
                strength=0.8,
                confidence=0.9,
                examples=["Sleep deprivation leads to slower thinking", "Tired people make more errors"]
            ))
            
            self.causal_links.append(CausalLink(
                cause="high stress",
                effect="reduced creativity",
                strength=0.6,
                confidence=0.7,
                examples=["Stress blocks creative thinking", "Anxiety inhibits innovation"]
            ))
            
            self.causal_links.append(CausalLink(
                cause="regular exercise",
                effect="improved mental clarity",
                strength=0.7,
                confidence=0.8,
                examples=["Exercise boosts brain function", "Physical activity improves focus"]
            ))
            
            self.causal_links.append(CausalLink(
                cause="continuous learning",
                effect="career advancement",
                strength=0.8,
                confidence=0.85,
                examples=["Learning new skills leads to opportunities", "Knowledge workers advance through expertise"]
            ))
            
            self.causal_links.append(CausalLink(
                cause="poor work-life balance",
                effect="burnout",
                strength=0.9,
                confidence=0.9,
                examples=["Overworking leads to exhaustion", "No recovery time causes burnout"]
            ))
            
            # Initialize concepts
            self._add_concept("programming", "technology", {
                "description": "The process of creating computer programs",
                "skills": ["problem solving", "logic", "attention to detail"]
            })
            
            self._add_concept("software development", "technology", {
                "description": "The process of designing, coding, testing, and maintaining software",
                "phases": ["design", "implementation", "testing", "deployment", "maintenance"]
            })
            
            self._add_concept("AGI", "technology", {
                "description": "Artificial General Intelligence - AI that can perform any intellectual task",
                "characteristics": ["autonomy", "generalization", "learning", "reasoning"]
            })
            
            self._add_concept("productivity", "general", {
                "description": "The effectiveness of productive effort",
                "factors": ["focus", "energy", "motivation", "tools", "environment"]
            })
            
            self._add_concept("stress", "psychology", {
                "description": "The body's response to pressure or challenge",
                "types": ["acute", "chronic"],
                "effects": ["physical", "mental", "emotional"]
            })
            
            self._save_knowledge()
    
    def _add_knowledge(self, k_type: KnowledgeType, subject: str, predicate: str,
                      object: str = None, confidence: float = 0.5, source: str = "general",
                      evidence: List[str] = None, related_concepts: List[str] = None):
        """Add a piece of knowledge"""
        k_id = f"{k_type.value}_{subject}_{predicate}_{object or 'none'}"
        knowledge = Knowledge(
            id=k_id,
            type=k_type,
            subject=subject,
            predicate=predicate,
            object=object,
            confidence=confidence,
            source=source,
            evidence=evidence or [],
            related_concepts=related_concepts or []
        )
        self.knowledge[k_id] = knowledge
    
    def _add_concept(self, name: str, category: str, properties: Dict[str, Any]):
        """Add a concept to the knowledge graph"""
        concept = ConceptNode(
            name=name,
            category=category,
            properties=properties
        )
        self.concepts[name] = concept
    
    def query_knowledge(self, subject: str = None, predicate: str = None, 
                       object: str = None, k_type: KnowledgeType = None,
                       min_confidence: float = 0.0) -> List[Knowledge]:
        """
        Query the knowledge base.
        Returns knowledge matching the criteria.
        """
        results = []
        
        for k in self.knowledge.values():
            # Update access stats
            k.last_accessed = datetime.utcnow().isoformat()
            k.access_count += 1
            
            # Filter by criteria
            if subject and k.subject.lower() != subject.lower():
                continue
            if predicate and predicate.lower() not in k.predicate.lower():
                continue
            if object and k.object and object.lower() != k.object.lower():
                continue
            if k_type and k.type != k_type:
                continue
            if k.confidence < min_confidence:
                continue
            
            results.append(k)
        
        self._save_knowledge()
        return results
    
    def get_related_concepts(self, concept: str, max_distance: int = 2) -> Dict[str, float]:
        """
        Get concepts related to the given concept.
        Uses the knowledge graph to find relationships.
        """
        if concept not in self.concepts:
            return {}
        
        related = {}
        visited = set()
        queue = deque([(concept, 0)])
        
        while queue:
            current, distance = queue.popleft()
            
            if distance > max_distance:
                continue
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in self.concepts:
                for related_concept, strength in self.concepts[current].related.items():
                    if related_concept not in visited:
                        related[related_concept] = max(
                            related.get(related_concept, 0),
                            strength * (1 - distance * 0.3)  # Decay with distance
                        )
                        queue.append((related_concept, distance + 1))
        
        return related
    
    def infer(self, subject: str, predicate: str) -> List[Tuple[str, float]]:
        """
        Infer the object for a subject-predicate pair using reasoning.
        Returns possible objects with confidence scores.
        """
        inferences = []
        
        # Direct knowledge lookup
        for k in self.query_knowledge(subject=subject, predicate=predicate):
            if k.object:
                inferences.append((k.object, k.confidence))
        
        # Reasoning through causal links
        for cl in self.causal_links:
            if cl.cause.lower() in subject.lower():
                if predicate.lower() == "leads to" or predicate.lower() == "causes":
                    inferences.append((cl.effect, cl.strength * cl.confidence))
        
        # Reasoning through related concepts
        related = self.get_related_concepts(subject)
        for related_concept, strength in related.items():
            for k in self.query_knowledge(subject=related_concept, predicate=predicate):
                if k.object:
                    inferences.append((k.object, strength * k.confidence * 0.5))  # Discount indirect inferences
        
        # Sort by confidence and deduplicate
        seen = set()
        unique_inferences = []
        for obj, conf in sorted(inferences, key=lambda x: x[1], reverse=True):
            if obj not in seen:
                seen.add(obj)
                unique_inferences.append((obj, conf))
        
        return unique_inferences
    
    def explain(self, phenomenon: str) -> Dict:
        """
        Explain a phenomenon using world knowledge.
        Returns explanation with supporting evidence.
        """
        explanation = {
            "phenomenon": phenomenon,
            "direct_knowledge": [],
            "causal_explanations": [],
            "related_concepts": [],
            "confidence": 0.0
        }
        
        # Direct knowledge
        direct_knowledge = self.query_knowledge(subject=phenomenon)
        explanation["direct_knowledge"] = [
            {
                "predicate": k.predicate,
                "object": k.object,
                "confidence": k.confidence,
                "source": k.source
            }
            for k in direct_knowledge
        ]
        
        # Causal explanations
        for cl in self.causal_links:
            if cl.cause.lower() in phenomenon.lower():
                explanation["causal_explanations"].append({
                    "type": "effect",
                    "description": f"{phenomenon} causes {cl.effect}",
                    "strength": cl.strength,
                    "confidence": cl.confidence,
                    "examples": cl.examples
                })
            elif cl.effect.lower() in phenomenon.lower():
                explanation["causal_explanations"].append({
                    "type": "cause",
                    "description": f"{cl.cause} causes {phenomenon}",
                    "strength": cl.strength,
                    "confidence": cl.confidence,
                    "examples": cl.examples
                })
        
        # Related concepts
        related = self.get_related_concepts(phenomenon)
        explanation["related_concepts"] = [
            {"concept": c, "strength": s}
            for c, s in sorted(related.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Calculate overall confidence
        if explanation["direct_knowledge"]:
            explanation["confidence"] = max(k["confidence"] for k in explanation["direct_knowledge"])
        elif explanation["causal_explanations"]:
            explanation["confidence"] = max(e["confidence"] for e in explanation["causal_explanations"])
        
        return explanation
    
    def learn_from_interaction(self, subject: str, predicate: str, object: str = None,
                            confidence: float = 0.5, source: str = "interaction"):
        """
        Learn new knowledge from user interactions.
        This is how LOVE builds its world model over time.
        """
        # Check if this knowledge already exists
        existing = self.query_knowledge(subject=subject, predicate=predicate, object=object)
        
        if existing:
            # Update confidence if it exists
            for k in existing:
                k.confidence = min(1.0, k.confidence + 0.1)
                k.last_accessed = datetime.utcnow().isoformat()
        else:
            # Add new knowledge
            self._add_knowledge(
                KnowledgeType.FACT,
                subject=subject,
                predicate=predicate,
                object=object,
                confidence=confidence,
                source=source
            )
        
        self._save_knowledge()
    
    def get_knowledge_summary(self) -> Dict:
        """Get summary of world model knowledge"""
        by_type = defaultdict(int)
        for k in self.knowledge.values():
            by_type[k.type.value] += 1
        
        return {
            "total_knowledge": len(self.knowledge),
            "total_concepts": len(self.concepts),
            "total_causal_links": len(self.causal_links),
            "knowledge_by_type": dict(by_type),
            "most_accessed": sorted(
                self.knowledge.values(),
                key=lambda k: k.access_count,
                reverse=True
            )[:10]
        }


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_world_model() -> WorldModel:
    """Get the singleton world model instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = WorldModel()
    return _instance
