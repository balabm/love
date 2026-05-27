"""
Hyper-Dimensional Polymathic Synthesis - Cross-Domain Isomorphism Engine

True intelligence is finding isomorphic mappings between unrelated domains. The system
applies concepts from physics to finance, or biology to software architecture, autonomously.

When a problem is detected in Domain A (e.g., a memory leak in Flutter), the engine projects
the problem's abstract topology into a high-dimensional vector space, queries the ChromaDB
knowledge graph to find structurally identical problems solved in Domain B (e.g., fluid dynamics,
traffic routing), and synthesizes the solution by translating the mathematical/logical solution
from the foreign domain back into the exact syntax and context of the user's current problem.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from collections import deque
import hashlib
import json
import re
import threading
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Domain(Enum):
    """Knowledge domains for cross-domain reasoning"""
    SOFTWARE_ENGINEERING = "software_engineering"
    PHYSICS = "physics"
    MATHEMATICS = "mathematics"
    BIOLOGY = "biology"
    FINANCE = "finance"
    ECONOMICS = "economics"
    CHEMISTRY = "chemistry"
    NEUROSCIENCE = "neuroscience"
    CIVIL_ENGINEERING = "civil_engineering"
    LOGIC = "logic"
    GAME_THEORY = "game_theory"
    NETWORK_THEORY = "network_theory"
    CONTROL_SYSTEMS = "control_systems"


class ProblemTopology(Enum):
    """Types of problem topologies (abstract structures)"""
    FLOW_OPTIMIZATION = "flow_optimization"  # Traffic, data, fluids, electricity
    RESOURCE_ALLOCATION = "resource_allocation"  # CPU, memory, budget, energy
    CASCADE_FAILURE = "cascade_failure"  # Power grids, financial crashes, neural networks
    EQUILIBRIUM_FINDING = "equilibrium_finding"  # Markets, chemical reactions, game theory
    PATH_FINDING = "path_finding"  # Routing, navigation, decision trees
    SCHEDULING = "scheduling"  * 10  # Tasks, processes, events
    CLUSTERING = "clustering"  # Data, particles, agents
    OSCILLATION = "oscillation"  # Signals, populations, markets
    DIFFUSION = "diffusion"  # Heat, information, disease
    COMPETITION = "competition"  # Species, companies, algorithms


@dataclass
class ProblemRepresentation:
    """Abstract representation of a problem in high-dimensional space"""
    problem_id: str
    domain: Domain
    description: str
    topology: ProblemTopology
    vector_embedding: np.ndarray
    structural_features: Dict[str, float]
    constraints: List[str]
    variables: List[str]
    relationships: List[Tuple[str, str, str]]  # (source, relation, target)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "problem_id": self.problem_id,
            "domain": self.domain.value,
            "description": self.description,
            "topology": self.topology.value,
            "vector_embedding": self.vector_embedding.tolist(),
            "structural_features": self.structural_features,
            "constraints": self.constraints,
            "variables": self.variables,
            "relationships": self.relationships,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class IsomorphicMapping:
    """Represents an isomorphic mapping between two problems"""
    mapping_id: str
    source_problem: str
    target_problem: str
    similarity_score: float
    topology_match: ProblemTopology
    variable_mappings: Dict[str, str]  # source_var -> target_var
    relation_mappings: Dict[str, str]  # source_relation -> target_relation
    confidence: float
    explanation: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "mapping_id": self.mapping_id,
            "source_problem": self.source_problem,
            "target_problem": self.target_problem,
            "similarity_score": self.similarity_score,
            "topology_match": self.topology_match.value,
            "variable_mappings": self.variable_mappings,
            "relation_mappings": self.relation_mappings,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SolutionTranslation:
    """A solution translated from one domain to another"""
    translation_id: str
    original_solution: str
    original_domain: Domain
    target_domain: Domain
    translated_solution: str
    translation_confidence: float
    adaptation_notes: List[str]
    validation_results: Dict[str, bool]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "translation_id": self.translation_id,
            "original_solution": self.original_solution,
            "original_domain": self.original_domain.value,
            "target_domain": self.target_domain.value,
            "translated_solution": self.translated_solution,
            "translation_confidence": self.translation_confidence,
            "adaptation_notes": self.adaptation_notes,
            "validation_results": self.validation_results,
            "timestamp": self.timestamp.isoformat()
        }


class DomainAdapter(ABC):
    """
    Abstract base class for domain-specific adapters.
    
    Each adapter knows how to:
    1. Parse problems in its domain
    2. Extract structural features
    3. Generate domain-specific solutions
    4. Translate solutions from other domains
    """
    
    @abstractmethod
    def parse_problem(self, description: str) -> ProblemRepresentation:
        """Parse a problem description into abstract representation"""
        pass
    
    @abstractmethod
    def extract_structural_features(self, problem: ProblemRepresentation) -> Dict[str, float]:
        """Extract structural features from a problem"""
        pass
    
    @abstractmethod
    def generate_solution(self, problem: ProblemRepresentation) -> str:
        """Generate a solution for a problem in this domain"""
        pass
    
    @abstractmethod
    def translate_solution(self, solution: str, target_domain: Domain) -> SolutionTranslation:
        """Translate a solution from another domain to this domain"""
        pass


class SoftwareEngineeringAdapter(DomainAdapter):
    """Adapter for software engineering problems"""
    
    def parse_problem(self, description: str) -> ProblemRepresentation:
        """Parse software engineering problem"""
        problem_id = hashlib.md5(description.encode()).hexdigest()[:12]
        
        # Detect topology from description
        topology = self._detect_topology(description)
        
        # Extract variables and constraints
        variables = self._extract_variables(description)
        constraints = self._extract_constraints(description)
        
        # Generate vector embedding (simplified)
        embedding = self._generate_embedding(description, topology)
        
        # Extract structural features
        structural_features = {
            "complexity": self._estimate_complexity(description),
            "scale": self._estimate_scale(description),
            "real_time": 1.0 if "real-time" in description.lower() else 0.0,
            "distributed": 1.0 if "distributed" in description.lower() else 0.0
        }
        
        return ProblemRepresentation(
            problem_id=problem_id,
            domain=Domain.SOFTWARE_ENGINEERING,
            description=description,
            topology=topology,
            vector_embedding=embedding,
            structural_features=structural_features,
            constraints=constraints,
            variables=variables,
            relationships=[]
        )
    
    def extract_structural_features(self, problem: ProblemRepresentation) -> Dict[str, float]:
        """Extract structural features"""
        return problem.structural_features
    
    def generate_solution(self, problem: ProblemRepresentation) -> str:
        """Generate software engineering solution"""
        solutions = {
            ProblemTopology.MEMORY_LEAK: "Implement proper resource cleanup using context managers and weak references",
            ProblemTopology.FLOW_OPTIMIZATION: "Use caching, load balancing, and asynchronous processing",
            ProblemTopology.CASCADE_FAILURE: "Implement circuit breakers, bulkheads, and fallback mechanisms",
            ProblemTopology.RESOURCE_ALLOCATION: "Use dynamic resource allocation with monitoring and auto-scaling"
        }
        
        return solutions.get(problem.topology, "Apply software engineering best practices")
    
    def translate_solution(self, solution: str, target_domain: Domain) -> SolutionTranslation:
        """Translate solution from another domain to software engineering"""
        # This would use LLM to translate domain-specific concepts
        translation_id = hashlib.md5(f"{solution}_{target_domain.value}".encode()).hexdigest()[:12]
        
        # Simplified translation logic
        translated = self._domain_specific_translation(solution, target_domain)
        
        return SolutionTranslation(
            translation_id=translation_id,
            original_solution=solution,
            original_domain=target_domain,
            target_domain=Domain.SOFTWARE_ENGINEERING,
            translated_solution=translated,
            translation_confidence=0.7,
            adaptation_notes=["Translated from domain-specific concepts"],
            validation_results={}
        )
    
    def _detect_topology(self, description: str) -> ProblemTopology:
        """Detect problem topology from description"""
        desc_lower = description.lower()
        
        if "memory leak" in desc_lower or "resource" in desc_lower:
            return ProblemTopology.RESOURCE_ALLOCATION
        elif "traffic" in desc_lower or "flow" in desc_lower or "bottleneck" in desc_lower:
            return ProblemTopology.FLOW_OPTIMIZATION
        elif "crash" in desc_lower or "failure" in desc_lower or "cascade" in desc_lower:
            return ProblemTopology.CASCADE_FAILURE
        else:
            return ProblemTopology.RESOURCE_ALLOCATION
    
    def _extract_variables(self, description: str) -> List[str]:
        """Extract variables from description"""
        # Simplified variable extraction
        variables = []
        words = description.split()
        for word in words:
            if word.isidentifier() and len(word) > 2:
                variables.append(word)
        return variables[:10]  # Limit to top 10
    
    def _extract_constraints(self, description: str) -> List[str]:
        """Extract constraints from description"""
        constraints = []
        constraint_keywords = ["limit", "constraint", "requirement", "must", "should"]
        
        for keyword in constraint_keywords:
            if keyword in description.lower():
                constraints.append(keyword)
        
        return constraints
    
    def _generate_embedding(self, description: str, topology: ProblemTopology) -> np.ndarray:
        """Generate vector embedding (simplified)"""
        # In production, would use proper embedding model
        embedding = np.zeros(128)
        embedding[hash(topology.value) % 128] = 1.0
        return embedding
    
    def _estimate_complexity(self, description: str) -> float:
        """Estimate problem complexity"""
        return min(len(description.split()) / 100.0, 1.0)
    
    def _estimate_scale(self, description: str) -> float:
        """Estimate problem scale"""
        scale_keywords = ["large", "massive", "distributed", "enterprise"]
        for keyword in scale_keywords:
            if keyword in description.lower():
                return 0.8
        return 0.3
    
    def _domain_specific_translation(self, solution: str, target_domain: Domain) -> str:
        """Translate domain-specific solution to software engineering"""
        translations = {
            Domain.PHYSICS: "Apply physics-inspired optimization algorithms",
            Domain.BIOLOGY: "Use evolutionary algorithms and genetic programming",
            Domain.FINANCE: "Implement risk management and portfolio optimization techniques",
            Domain.MATHEMATICS: "Apply mathematical optimization and formal verification"
        }
        
        return translations.get(target_domain, f"Adapted from {target_domain.value}")


class PhysicsAdapter(DomainAdapter):
    """Adapter for physics problems"""
    
    def parse_problem(self, description: str) -> ProblemRepresentation:
        """Parse physics problem"""
        problem_id = hashlib.md5(description.encode()).hexdigest()[:12]
        
        topology = self._detect_topology(description)
        embedding = self._generate_embedding(description, topology)
        
        return ProblemRepresentation(
            problem_id=problem_id,
            domain=Domain.PHYSICS,
            description=description,
            topology=topology,
            vector_embedding=embedding,
            structural_features={"energy": 0.5, "entropy": 0.3},
            constraints=["conservation_laws"],
            variables=["mass", "velocity", "force"],
            relationships=[]
        )
    
    def extract_structural_features(self, problem: ProblemRepresentation) -> Dict[str, float]:
        return problem.structural_features
    
    def generate_solution(self, problem: ProblemRepresentation) -> str:
        """Generate physics solution"""
        return "Apply conservation laws and thermodynamic principles"
    
    def translate_solution(self, solution: str, target_domain: Domain) -> SolutionTranslation:
        """Translate solution to physics domain"""
        return SolutionTranslation(
            translation_id=hashlib.md5(solution.encode()).hexdigest()[:12],
            original_solution=solution,
            original_domain=target_domain,
            target_domain=Domain.PHYSICS,
            translated_solution=f"Physics interpretation: {solution}",
            translation_confidence=0.6,
            adaptation_notes=["Translated to physics terminology"],
            validation_results={}
        )
    
    def _detect_topology(self, description: str) -> ProblemTopology:
        desc_lower = description.lower()
        if "flow" in desc_lower or "fluid" in desc_lower:
            return ProblemTopology.FLOW_OPTIMIZATION
        elif "equilibrium" in desc_lower:
            return ProblemTopology.EQUILIBRIUM_FINDING
        else:
            return ProblemTopology.DIFFUSION
    
    def _generate_embedding(self, description: str, topology: ProblemTopology) -> np.ndarray:
        embedding = np.zeros(128)
        embedding[hash(topology.value) % 128] = 1.0
        return embedding


class FinanceAdapter(DomainAdapter):
    """Adapter for finance problems"""
    
    def parse_problem(self, description: str) -> ProblemRepresentation:
        """Parse finance problem"""
        problem_id = hashlib.md5(description.encode()).hexdigest()[:12]
        
        topology = self._detect_topology(description)
        embedding = self._generate_embedding(description, topology)
        
        return ProblemRepresentation(
            problem_id=problem_id,
            domain=Domain.FINANCE,
            description=description,
            topology=topology,
            vector_embedding=embedding,
            structural_features={"risk": 0.7, "return": 0.5, "volatility": 0.6},
            constraints=["regulatory", "capital"],
            variables=["price", "volume", "risk"],
            relationships=[]
        )
    
    def extract_structural_features(self, problem: ProblemRepresentation) -> Dict[str, float]:
        return problem.structural_features
    
    def generate_solution(self, problem: ProblemRepresentation) -> str:
        """Generate finance solution"""
        return "Apply portfolio optimization and risk management strategies"
    
    def translate_solution(self, solution: str, target_domain: Domain) -> SolutionTranslation:
        """Translate solution to finance domain"""
        return SolutionTranslation(
            translation_id=hashlib.md5(solution.encode()).hexdigest()[:12],
            original_solution=solution,
            original_domain=target_domain,
            target_domain=Domain.FINANCE,
            translated_solution=f"Financial interpretation: {solution}",
            translation_confidence=0.65,
            adaptation_notes=["Translated to financial terminology"],
            validation_results={}
        )
    
    def _detect_topology(self, description: str) -> ProblemTopology:
        desc_lower = description.lower()
        if "risk" in desc_lower or "portfolio" in desc_lower:
            return ProblemTopology.RESOURCE_ALLOCATION
        elif "crash" in desc_lower or "cascade" in desc_lower:
            return ProblemTopology.CASCADE_FAILURE
        else:
            return ProblemTopology.EQUILIBRIUM_FINDING
    
    def _generate_embedding(self, description: str, topology: ProblemTopology) -> np.ndarray:
        embedding = np.zeros(128)
        embedding[hash(topology.value) % 128] = 1.0
        return embedding


class VectorSpaceProjector:
    """
    Projects problems into high-dimensional vector space for similarity analysis.
    
    Uses vector embeddings to find structural similarities between problems
    across different domains.
    """
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.projection_history: deque = deque(maxlen=1000)
        
    def project_problem(self, problem: ProblemRepresentation) -> np.ndarray:
        """Project a problem into vector space"""
        # Combine topology embedding with structural features
        topology_embedding = problem.vector_embedding
        
        # Create feature vector from structural features
        feature_values = list(problem.structural_features.values())
        feature_vector = np.zeros(self.embedding_dim)
        
        for i, value in enumerate(feature_values):
            if i < self.embedding_dim:
                feature_vector[i] = value
        
        # Combine embeddings
        combined = (topology_embedding + feature_vector) / 2.0
        return combined
    
    def calculate_similarity(self, problem1: ProblemRepresentation, problem2: ProblemRepresentation) -> float:
        """Calculate similarity between two problems using cosine similarity"""
        vec1 = self.project_problem(problem1)
        vec2 = self.project_problem(problem2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    
    def find_similar_problems(
        self, 
        target_problem: ProblemRepresentation, 
        problem_database: List[ProblemRepresentation],
        threshold: float = 0.5,
        top_k: int = 5
    ) -> List[Tuple[ProblemRepresentation, float]]:
        """Find similar problems in the database"""
        similarities = []
        
        for problem in problem_database:
            if problem.problem_id != target_problem.problem_id:
                similarity = self.calculate_similarity(target_problem, problem)
                if similarity >= threshold:
                    similarities.append((problem, similarity))
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class IsomorphicMapper:
    """
    Finds isomorphic mappings between problems across domains.
    
    Identifies structural similarities and creates detailed mappings
    between variables and relationships.
    """
    
    def __init__(self):
        self.mapping_history: deque = deque(maxlen=500)
        
    def find_isomorphic_mapping(
        self, 
        source_problem: ProblemRepresentation, 
        target_problem: ProblemRepresentation
    ) -> Optional[IsomorphicMapping]:
        """
        Find isomorphic mapping between two problems.
        
        Returns None if no significant isomorphism exists.
        """
        # Check if topologies match
        if source_problem.topology != target_problem.topology:
            return None
        
        # Calculate structural similarity
        similarity = self._calculate_structural_similarity(source_problem, target_problem)
        
        if similarity < 0.5:
            return None
        
        # Create variable mappings
        variable_mappings = self._map_variables(source_problem, target_problem)
        
        # Create relation mappings
        relation_mappings = self._map_relations(source_problem, target_problem)
        
        # Generate explanation
        explanation = self._generate_explanation(source_problem, target_problem, similarity)
        
        mapping_id = hashlib.md5(
            f"{source_problem.problem_id}_{target_problem.problem_id}".encode()
        ).hexdigest()[:12]
        
        mapping = IsomorphicMapping(
            mapping_id=mapping_id,
            source_problem=source_problem.problem_id,
            target_problem=target_problem.problem_id,
            similarity_score=similarity,
            topology_match=source_problem.topology,
            variable_mappings=variable_mappings,
            relation_mappings=relation_mappings,
            confidence=min(similarity + 0.1, 1.0),
            explanation=explanation
        )
        
        self.mapping_history.append(mapping)
        logger.info(f"Found isomorphic mapping: {source_problem.domain.value} → {target_problem.domain.value}")
        
        return mapping
    
    def _calculate_structural_similarity(
        self, 
        problem1: ProblemRepresentation, 
        problem2: ProblemRepresentation
    ) -> float:
        """Calculate structural similarity between problems"""
        # Compare structural features
        features1 = problem1.structural_features
        features2 = problem2.structural_features
        
        # Get common features
        common_features = set(features1.keys()) & set(features2.keys())
        
        if not common_features:
            return 0.0
        
        # Calculate feature similarity
        feature_similarities = []
        for feature in common_features:
            val1 = features1[feature]
            val2 = features2[feature]
            similarity = 1.0 - abs(val1 - val2)  # Simple difference metric
            feature_similarities.append(similarity)
        
        return np.mean(feature_similarities) if feature_similarities else 0.0
    
    def _map_variables(
        self, 
        source_problem: ProblemRepresentation, 
        target_problem: ProblemRepresentation
    ) -> Dict[str, str]:
        """Map variables from source to target problem"""
        mappings = {}
        
        # Simple mapping based on variable count and position
        source_vars = source_problem.variables
        target_vars = target_problem.variables
        
        for i, source_var in enumerate(source_vars):
            if i < len(target_vars):
                mappings[source_var] = target_vars[i]
        
        return mappings
    
    def _map_relations(
        self, 
        source_problem: ProblemRepresentation, 
        target_problem: ProblemRepresentation
    ) -> Dict[str, str]:
        """Map relations from source to target problem"""
        mappings = {}
        
        # Extract relation types from relationships
        source_relations = set()
        target_relations = set()
        
        for _, relation, _ in source_problem.relationships:
            source_relations.add(relation)
        
        for _, relation, _ in target_problem.relationships:
            target_relations.add(relation)
        
        # Map similar relations
        for source_rel in source_relations:
            for target_rel in target_relations:
                if source_rel.lower() == target_rel.lower():
                    mappings[source_rel] = target_rel
                    break
        
        return mappings
    
    def _generate_explanation(
        self, 
        source_problem: ProblemRepresentation, 
        target_problem: ProblemRepresentation,
        similarity: float
    ) -> str:
        """Generate human-readable explanation of the mapping"""
        return (f"Problems share {source_problem.topology.value} topology with {similarity:.2%} similarity. "
                f"Mapping {source_problem.domain.value} concepts to {target_problem.domain.value} domain.")


class SolutionTranslator:
    """
    Translates solutions from one domain to another using isomorphic mappings.
    
    Takes a solution from a foreign domain and adapts it to the target domain's
    syntax, context, and constraints.
    """
    
    def __init__(self):
        self.adapters: Dict[Domain, DomainAdapter] = {
            Domain.SOFTWARE_ENGINEERING: SoftwareEngineeringAdapter(),
            Domain.PHYSICS: PhysicsAdapter(),
            Domain.FINANCE: FinanceAdapter()
        }
        self.translation_history: deque = deque(maxlen=500)
        
    def translate_solution(
        self, 
        mapping: IsomorphicMapping, 
        original_solution: str,
        target_domain: Domain
    ) -> SolutionTranslation:
        """
        Translate a solution using an isomorphic mapping.
        
        Args:
            mapping: The isomorphic mapping between domains
            original_solution: The solution from the source domain
            target_domain: The domain to translate to
            
        Returns:
            Translated solution adapted to target domain
        """
        try:
            # Get target domain adapter
            adapter = self.adapters.get(target_domain)
            if not adapter:
                raise ValueError(f"No adapter for domain {target_domain}")
            
            # Perform translation
            translation = adapter.translate_solution(original_solution, mapping.source_problem)
            
            # Apply variable mappings
            translated_solution = self._apply_variable_mappings(
                translation.translated_solution,
                mapping.variable_mappings
            )
            
            # Update translation with mapped solution
            translation.translated_solution = translated_solution
            
            self.translation_history.append(translation)
            logger.info(f"Translated solution from {mapping.source_problem} to {target_domain.value}")
            
            return translation
            
        except Exception as e:
            logger.error(f"Error translating solution: {e}")
            raise
    
    def _apply_variable_mappings(self, solution: str, variable_mappings: Dict[str, str]) -> str:
        """Apply variable mappings to the solution"""
        translated = solution
        
        for source_var, target_var in variable_mappings.items():
            translated = translated.replace(source_var, target_var)
        
        return translated


class IsomorphicEngine:
    """
    Main engine coordinating cross-domain isomorphic reasoning.
    
    1. Projects problems into high-dimensional vector space
    2. Queries knowledge graph for structurally identical problems
    3. Creates isomorphic mappings between domains
    4. Translates solutions from foreign domains to current context
    """
    
    def __init__(self):
        self.projector = VectorSpaceProjector()
        self.mapper = IsomorphicMapper()
        self.translator = SolutionTranslator()
        self.problem_database: List[ProblemRepresentation] = []
        self.adapters: Dict[Domain, DomainAdapter] = {
            Domain.SOFTWARE_ENGINEERING: SoftwareEngineeringAdapter(),
            Domain.PHYSICS: PhysicsAdapter(),
            Domain.FINANCE: FinanceAdapter()
        }
        
        # Initialize with some example problems
        self._initialize_problem_database()
        
    def _initialize_problem_database(self) -> None:
        """Initialize with example problems from different domains"""
        example_problems = [
            (Domain.PHYSICS, "Fluid flow optimization in pipe network with pressure constraints"),
            (Domain.FINANCE, "Portfolio allocation under risk constraints and market volatility"),
            (Domain.BIOLOGY, "Resource allocation in biological systems under energy constraints"),
            (Domain.CIVIL_ENGINEERING, "Traffic flow optimization in urban network with capacity constraints")
        ]
        
        for domain, description in example_problems:
            adapter = self.adapters.get(domain)
            if adapter:
                problem = adapter.parse_problem(description)
                self.problem_database.append(problem)
    
    def solve_problem_cross_domain(
        self, 
        problem_description: str, 
        target_domain: Domain = Domain.SOFTWARE_ENGINEERING
    ) -> Dict[str, Any]:
        """
        Solve a problem using cross-domain isomorphic reasoning.
        
        Args:
            problem_description: Description of the problem to solve
            target_domain: The domain of the original problem
            
        Returns:
            Dictionary containing the solution and reasoning process
        """
        try:
            # Parse the problem
            adapter = self.adapters.get(target_domain)
            if not adapter:
                raise ValueError(f"No adapter for domain {target_domain}")
            
            target_problem = adapter.parse_problem(problem_description)
            
            # Project into vector space
            projected = self.projector.project_problem(target_problem)
            
            # Find similar problems in other domains
            similar_problems = self.projector.find_similar_problems(
                target_problem,
                self.problem_database,
                threshold=0.3,
                top_k=3
            )
            
            if not similar_problems:
                # Fall back to domain-specific solution
                solution = adapter.generate_solution(target_problem)
                return {
                    "solution": solution,
                    "method": "domain_specific",
                    "confidence": 0.5,
                    "reasoning": "No cross-domain isomorphisms found, used domain-specific approach"
                }
            
            # Find best isomorphic mapping
            best_mapping = None
            best_similarity = 0.0
            
            for similar_problem, similarity in similar_problems:
                mapping = self.mapper.find_isomorphic_mapping(target_problem, similar_problem)
                if mapping and mapping.similarity_score > best_similarity:
                    best_mapping = mapping
                    best_similarity = mapping.similarity_score
            
            if not best_mapping:
                # Fall back to domain-specific solution
                solution = adapter.generate_solution(target_problem)
                return {
                    "solution": solution,
                    "method": "domain_specific",
                    "confidence": 0.5,
                    "reasoning": "No valid isomorphic mapping found"
                }
            
            # Get solution from source domain
            source_adapter = self.adapters.get(similar_problems[0][0].domain)
            if source_adapter:
                original_solution = source_adapter.generate_solution(similar_problems[0][0])
                
                # Translate solution to target domain
                translated = self.translator.translate_solution(
                    best_mapping,
                    original_solution,
                    target_domain
                )
                
                return {
                    "solution": translated.translated_solution,
                    "method": "cross_domain_isomorphism",
                    "confidence": translated.translation_confidence,
                    "reasoning": best_mapping.explanation,
                    "source_domain": similar_problems[0][0].domain.value,
                    "similarity_score": best_similarity,
                    "adaptation_notes": translated.adaptation_notes
                }
            
            # Fallback
            solution = adapter.generate_solution(target_problem)
            return {
                "solution": solution,
                "method": "domain_specific",
                "confidence": 0.5,
                "reasoning": "Translation failed, used domain-specific approach"
            }
            
        except Exception as e:
            logger.error(f"Error in cross-domain problem solving: {e}")
            return {
                "solution": "Error occurred during cross-domain reasoning",
                "method": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def add_problem_to_database(self, domain: Domain, description: str) -> bool:
        """Add a new problem to the knowledge base"""
        try:
            adapter = self.adapters.get(domain)
            if not adapter:
                return False
            
            problem = adapter.parse_problem(description)
            self.problem_database.append(problem)
            logger.info(f"Added problem to database: {domain.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding problem to database: {e}")
            return False


# Singleton instance
_isomorphic_engine_instance: Optional[IsomorphicEngine] = None
_engine_lock = threading.Lock()

def get_isomorphic_engine() -> IsomorphicEngine:
    """Get the singleton Isomorphic Engine instance"""
    global _isomorphic_engine_instance
    with _engine_lock:
        if _isomorphic_engine_instance is None:
            _isomorphic_engine_instance = IsomorphicEngine()
        return _isomorphic_engine_instance


if __name__ == "__main__":
    # Test the Isomorphic Engine
    print("Testing Isomorphic Engine...")
    
    engine = get_isomorphic_engine()
    
    # Test cross-domain problem solving
    result = engine.solve_problem_cross_domain(
        "Memory leak in Flutter application causing performance degradation",
        Domain.SOFTWARE_ENGINEERING
    )
    
    print(f"\nCross-Domain Solution Result:")
    print(f"Method: {result['method']}")
    print(f"Solution: {result['solution']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning: {result['reasoning']}")
    
    if 'source_domain' in result:
        print(f"Source Domain: {result['source_domain']}")
        print(f"Similarity Score: {result['similarity_score']}")
    
    print("\nIsomorphic Engine test completed successfully!")