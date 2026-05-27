"""
Meta-Learning System - Principle Extraction & Cognitive Elevation

The system logs how it successfully solved problems, extracts abstract principles,
and writes new core cognitive functions based on those principles to permanently
elevate its baseline intelligence.

This is the foundation of recursive self-improvement and knowledge crystallization.
"""

import logging
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from collections import deque
import ast
import inspect
import importlib
import os
import tempfile
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SolutionType(Enum):
    """Types of solutions the system can learn from"""
    ALGORITHMIC = "algorithmic"
    HEURISTIC = "heuristic"
    PATTERN_MATCHING = "pattern_matching"
    OPTIMIZATION = "optimization"
    DEBUGGING = "debugging"
    ARCHITECTURAL = "architectural"
    COMMUNICATION = "communication"
    PLANNING = "planning"


class PrincipleCategory(Enum):
    """Categories of abstract principles"""
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    CLARITY = "clarity"
    SCALABILITY = "scalability"
    SECURITY = "security"
    USABILITY = "usability"
    MAINTAINABILITY = "maintainability"
    GENERALIZATION = "generalization"


@dataclass
class SolutionLog:
    """A record of how the system solved a problem"""
    solution_id: str
    problem_description: str
    solution_type: SolutionType
    original_approach: str
    refined_approach: str
    success_metrics: Dict[str, float]
    context: Dict[str, Any]
    timestamp: datetime
    execution_time: float
    iterations: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "solution_id": self.solution_id,
            "problem_description": self.problem_description,
            "solution_type": self.solution_type.value,
            "original_approach": self.original_approach,
            "refined_approach": self.refined_approach,
            "success_metrics": self.success_metrics,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "iterations": self.iterations
        }


@dataclass
class AbstractPrinciple:
    """An abstract principle extracted from successful solutions"""
    principle_id: str
    name: str
    category: PrincipleCategory
    description: str
    formal_statement: str
    applicability_conditions: List[str]
    implementation_pattern: str
    confidence: float
    source_solutions: List[str]  # IDs of solutions this principle came from
    usage_count: int = 0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "principle_id": self.principle_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "formal_statement": self.formal_statement,
            "applicability_conditions": self.applicability_conditions,
            "implementation_pattern": self.implementation_pattern,
            "confidence": self.confidence,
            "source_solutions": self.source_solutions,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CognitiveFunction:
    """A new cognitive function generated from principles"""
    function_id: str
    name: str
    purpose: str
    source_principles: List[str]  # IDs of principles used
    implementation: str
    interface_signature: str
    dependencies: List[str]
    performance_metrics: Dict[str, float]
    integration_status: str = "pending"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "function_id": self.function_id,
            "name": self.name,
            "purpose": self.purpose,
            "source_principles": self.source_principles,
            "implementation": self.implementation,
            "interface_signature": self.interface_signature,
            "dependencies": self.dependencies,
            "performance_metrics": self.performance_metrics,
            "integration_status": self.integration_status,
            "timestamp": self.timestamp.isoformat()
        }


class PrincipleExtractor:
    """
    Extracts abstract principles from successful solutions.
    
    Uses pattern recognition and abstraction to identify the fundamental
    principles that made a solution successful.
    """
    
    def __init__(self):
        self.extraction_history: deque = deque(maxlen=1000)
        self.principle_templates: Dict[SolutionType, List[str]] = {
            SolutionType.ALGORITHMIC: [
                "Divide and conquer approach",
                "Dynamic programming optimization",
                "Greedy strategy application",
                "Recursive decomposition"
            ],
            SolutionType.OPTIMIZATION: [
                "Time-space tradeoff",
                "Caching intermediate results",
                "Early termination conditions",
                "Batch processing optimization"
            ],
            SolutionType.DEBUGGING: [
                "Isolation of failure points",
                "Systematic elimination",
                "Invariant preservation",
                "Defensive programming"
            ],
            SolutionType.ARCHITECTURAL: [
                "Separation of concerns",
                "Dependency inversion",
                "Interface segregation",
                "Single responsibility"
            ]
        }
    
    def extract_principle(self, solution_log: SolutionLog) -> Optional[AbstractPrinciple]:
        """
        Extract an abstract principle from a solution log.
        
        Analyzes the solution to identify the fundamental principle
        that led to success.
        """
        try:
            # Analyze the solution approach
            principle = self._analyze_solution_approach(solution_log)
            
            if principle:
                self.extraction_history.append(principle)
                logger.info(f"Extracted principle: {principle.name} from {solution_log.solution_id}")
            
            return principle
            
        except Exception as e:
            logger.error(f"Error extracting principle from solution {solution_log.solution_id}: {e}")
            return None
    
    def _analyze_solution_approach(self, solution_log: SolutionLog) -> Optional[AbstractPrinciple]:
        """Analyze the solution to extract the core principle"""
        # Get relevant templates for this solution type
        templates = self.principle_templates.get(solution_log.solution_type, [])
        
        # Score each template based on similarity to the solution
        best_template = None
        best_score = 0.0
        
        for template in templates:
            score = self._calculate_template_similarity(template, solution_log)
            if score > best_score:
                best_score = score
                best_template = template
        
        if best_template and best_score > 0.3:
            # Generate principle from template
            principle_id = hashlib.md5(
                f"{best_template}_{solution_log.solution_id}".encode()
            ).hexdigest()[:12]
            
            principle = AbstractPrinciple(
                principle_id=principle_id,
                name=self._generate_principle_name(best_template),
                category=self._categorize_principle(best_template),
                description=self._generate_description(best_template, solution_log),
                formal_statement=self._generate_formal_statement(best_template),
                applicability_conditions=self._generate_applicability_conditions(solution_log),
                implementation_pattern=self._extract_implementation_pattern(solution_log),
                confidence=best_score,
                source_solutions=[solution_log.solution_id]
            )
            
            return principle
        
        return None
    
    def _calculate_template_similarity(self, template: str, solution_log: SolutionLog) -> float:
        """Calculate similarity between template and solution"""
        # Simple keyword matching for demonstration
        template_words = set(template.lower().split())
        solution_words = set(solution_log.refined_approach.lower().split())
        
        if not template_words:
            return 0.0
        
        intersection = template_words & solution_words
        return len(intersection) / len(template_words)
    
    def _generate_principle_name(self, template: str) -> str:
        """Generate a concise name for the principle"""
        # Convert template to title case
        return template.title().replace(" ", "")
    
    def _categorize_principle(self, template: str) -> PrincipleCategory:
        """Categorize the principle"""
        template_lower = template.lower()
        
        if any(word in template_lower for word in ['efficient', 'fast', 'optimize', 'performance']):
            return PrincipleCategory.EFFICIENCY
        elif any(word in template_lower for word in ['robust', 'error', 'fail', 'defensive']):
            return PrincipleCategory.ROBUSTNESS
        elif any(word in template_lower for word in ['clear', 'simple', 'readable']):
            return PrincipleCategory.CLARITY
        elif any(word in template_lower for word in ['scale', 'distributed', 'concurrent']):
            return PrincipleCategory.SCALABILITY
        elif any(word in template_lower for word in ['secure', 'protect', 'validate']):
            return PrincipleCategory.SECURITY
        else:
            return PrincipleCategory.GENERALIZATION
    
    def _generate_description(self, template: str, solution_log: SolutionLog) -> str:
        """Generate human-readable description"""
        return f"{template}: Successfully applied to {solution_log.problem_description}"
    
    def _generate_formal_statement(self, template: str) -> str:
        """Generate formal mathematical/logical statement"""
        return f"∀ problems matching pattern: {template} → optimal solution"
    
    def _generate_applicability_conditions(self, solution_log: SolutionLog) -> List[str]:
        """Generate conditions under which this principle applies"""
        conditions = []
        
        # Extract conditions from context
        if 'domain' in solution_log.context:
            conditions.append(f"Domain: {solution_log.context['domain']}")
        if 'constraints' in solution_log.context:
            conditions.append(f"Constraints: {solution_log.context['constraints']}")
        if 'data_size' in solution_log.context:
            conditions.append(f"Data scale: {solution_log.context['data_size']}")
        
        return conditions if conditions else ["General applicability"]
    
    def _extract_implementation_pattern(self, solution_log: SolutionLog) -> str:
        """Extract the implementation pattern from the solution"""
        # Return the refined approach as the pattern
        return solution_log.refined_approach


class CognitiveFunctionGenerator:
    """
    Generates new cognitive functions from abstract principles.
    
    Combines multiple principles to create new cognitive capabilities
    that permanently elevate the system's baseline intelligence.
    """
    
    def __init__(self):
        self.generation_history: deque = deque(maxlen=500)
        self.function_templates: Dict[str, str] = {
            "efficiency": """
def {function_name}(input_data):
    '''
    {purpose}
    
    Generated from principles: {principles}
    '''
    # Implementation based on {principles}
    {implementation}
    return result
""",
            "robustness": """
def {function_name}(input_data, validation=True):
    '''
    {purpose}
    
    Generated from principles: {principles}
    '''
    if validation:
        # Validate input based on robustness principles
        if not input_data:
            raise ValueError("Invalid input")
    
    # Implementation based on {principles}
    {implementation}
    return result
""",
            "general": """
def {function_name}(*args, **kwargs):
    '''
    {purpose}
    
    Generated from principles: {principles}
    '''
    # Implementation based on {principles}
    {implementation}
    return result
"""
        }
    
    def generate_function(
        self, 
        principles: List[AbstractPrinciple],
        purpose: str,
        category: PrincipleCategory
    ) -> Optional[CognitiveFunction]:
        """
        Generate a new cognitive function from principles.
        
        Combines multiple principles to create a function that embodies
        the extracted wisdom.
        """
        try:
            # Select appropriate template
            template_key = category.value if category.value in self.function_templates else "general"
            template = self.function_templates[template_key]
            
            # Generate function name
            function_name = self._generate_function_name(principles, purpose)
            
            # Generate implementation
            implementation = self._generate_implementation(principles)
            
            # Generate function ID
            function_id = hashlib.md5(
                f"{function_name}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # Create cognitive function
            cognitive_function = CognitiveFunction(
                function_id=function_id,
                name=function_name,
                purpose=purpose,
                source_principles=[p.principle_id for p in principles],
                implementation=implementation,
                interface_signature=self._generate_signature(function_name, principles),
                dependencies=self._identify_dependencies(principles),
                performance_metrics={}
            )
            
            self.generation_history.append(cognitive_function)
            logger.info(f"Generated cognitive function: {function_name}")
            
            return cognitive_function
            
        except Exception as e:
            logger.error(f"Error generating cognitive function: {e}")
            return None
    
    def _generate_function_name(self, principles: List[AbstractPrinciple], purpose: str) -> str:
        """Generate a descriptive function name"""
        # Extract key words from purpose
        purpose_words = purpose.lower().split()
        key_words = [word for word in purpose_words if len(word) > 3][:3]
        
        # Combine with principle names
        principle_names = [p.name[:5] for p in principles[:2]]
        
        # Create function name
        name_parts = principle_names + key_words
        function_name = "_".join(name_parts).lower()
        
        return f"cognitive_{function_name}"
    
    def _generate_implementation(self, principles: List[AbstractPrinciple]) -> str:
        """Generate implementation based on principles"""
        implementations = []
        
        for principle in principles:
            implementations.append(f"# Principle: {principle.name}")
            implementations.append(f"# {principle.description}")
            implementations.append(principle.implementation_pattern)
            implementations.append("")
        
        return "\n".join(implementations)
    
    def _generate_signature(self, function_name: str, principles: List[AbstractPrinciple]) -> str:
        """Generate function signature"""
        # Determine parameters based on principles
        params = ["input_data"]
        
        for principle in principles:
            if "validation" in principle.description.lower():
                params.append("validation=True")
            if "context" in principle.description.lower():
                params.append("context=None")
        
        signature = f"def {function_name}({', '.join(params)})"
        return signature
    
    def _identify_dependencies(self, principles: List[AbstractPrinciple]) -> List[str]:
        """Identify dependencies for the generated function"""
        dependencies = []
        
        for principle in principles:
            # Extract dependencies from implementation pattern
            if "import" in principle.implementation_pattern:
                # Simple extraction - would be more sophisticated in production
                dependencies.append("standard_library")
        
        return dependencies


class MetaLearningEngine:
    """
    Main engine coordinating meta-learning process.
    
    1. Logs successful solutions
    2. Extracts abstract principles
    3. Generates cognitive functions
    4. Integrates new functions into the system
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.solution_logs: Dict[str, SolutionLog] = {}
        self.principles: Dict[str, AbstractPrinciple] = {}
        self.cognitive_functions: Dict[str, CognitiveFunction] = {}
        
        self.principle_extractor = PrincipleExtractor()
        self.function_generator = CognitiveFunctionGenerator()
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Load existing data
        self._load_persistent_data()
        
    def log_solution(
        self,
        problem_description: str,
        solution_type: SolutionType,
        original_approach: str,
        refined_approach: str,
        success_metrics: Dict[str, float],
        context: Dict[str, Any],
        execution_time: float,
        iterations: int,
        mutation_used: Optional[str] = None  # Link to AST mutation if applicable
    ) -> SolutionLog:
        """Log a successful solution for meta-learning"""
        solution_id = hashlib.md5(
            f"{problem_description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        solution_log = SolutionLog(
            solution_id=solution_id,
            problem_description=problem_description,
            solution_type=solution_type,
            original_approach=original_approach,
            refined_approach=refined_approach,
            success_metrics=success_metrics,
            context=context,
            timestamp=datetime.now(),
            execution_time=execution_time,
            iterations=iterations
        )
        
        self.solution_logs[solution_id] = solution_log
        self._save_solution_log(solution_log)
        
        logger.info(f"Logged solution: {solution_id} (mutation: {mutation_used})")
        
        # Trigger principle extraction
        self._extract_and_learn(solution_log, mutation_used)
        
        return solution_log
    
    def _extract_and_learn(self, solution_log: SolutionLog, mutation_used: Optional[str] = None) -> None:
        """Extract principles and generate cognitive functions from solution"""
        # Extract principle
        principle = self.principle_extractor.extract_principle(solution_log)
        
        if principle:
            self.principles[principle.principle_id] = principle
            self._save_principle(principle)
            
            # If mutation was used, enhance principle with mutation information
            if mutation_used:
                principle.metadata['mutation_used'] = mutation_used
                principle.metadata['self_improvement'] = True
            
            # Check if we have enough principles to generate a function
            if len(self.principles) >= 2:
                self._generate_cognitive_functions()
    
    def _generate_cognitive_functions(self) -> None:
        """Generate cognitive functions from available principles"""
        # Get recent principles
        recent_principles = list(self.principles.values())[-5:]
        
        if len(recent_principles) < 2:
            return
        
        # Group by category
        from collections import defaultdict
        category_groups = defaultdict(list)
        for principle in recent_principles:
            category_groups[principle.category].append(principle)
        
        # Generate functions for each category
        for category, principles in category_groups.items():
            if len(principles) >= 2:
                purpose = f"Apply {category.value} principles for optimal problem solving"
                
                cognitive_function = self.function_generator.generate_function(
                    principles=principles,
                    purpose=purpose,
                    category=category
                )
                
                if cognitive_function:
                    self.cognitive_functions[cognitive_function.function_id] = cognitive_function
                    self._save_cognitive_function(cognitive_function)
    
    def integrate_cognitive_function(self, function_id: str) -> bool:
        """
        Integrate a generated cognitive function into the live system.
        
        This writes the function to an appropriate module and makes it
        available for use.
        """
        try:
            if function_id not in self.cognitive_functions:
                logger.warning(f"Cognitive function {function_id} not found")
                return False
            
            cognitive_function = self.cognitive_functions[function_id]
            
            # Create the function file
            function_code = self._generate_function_code(cognitive_function)
            
            # Write to cognitive functions module
            module_path = os.path.join(self.data_dir, "cognitive_functions.py")
            
            with open(module_path, 'a' if os.path.exists(module_path) else 'w', encoding='utf-8') as f:
                f.write(function_code + "\n\n")
            
            # Update integration status
            cognitive_function.integration_status = "integrated"
            self._save_cognitive_function(cognitive_function)
            
            logger.info(f"Integrated cognitive function: {cognitive_function.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error integrating cognitive function {function_id}: {e}")
            return False
    
    def _generate_function_code(self, cognitive_function: CognitiveFunction) -> str:
        """Generate executable Python code for the cognitive function"""
        code = f'''
# Auto-generated cognitive function
# Purpose: {cognitive_function.purpose}
# Source Principles: {cognitive_function.source_principles}
# Generated: {cognitive_function.timestamp.isoformat()}

{cognitive_function.interface_signature}
    """
    {cognitive_function.purpose}
    
    Generated from principles: {cognitive_function.source_principles}
    """
    {cognitive_function.implementation}
'''
        return code
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of meta-learning progress"""
        return {
            "total_solutions": len(self.solution_logs),
            "total_principles": len(self.principles),
            "total_functions": len(self.cognitive_functions),
            "integrated_functions": sum(
                1 for f in self.cognitive_functions.values() 
                if f.integration_status == "integrated"
            ),
            "principle_categories": self._count_principle_categories(),
            "recent_solutions": [
                log.to_dict() for log in list(self.solution_logs.values())[-5:]
            ]
        }
    
    def _count_principle_categories(self) -> Dict[str, int]:
        """Count principles by category"""
        from collections import Counter
        categories = [p.category.value for p in self.principles.values()]
        return dict(Counter(categories))
    
    def _save_solution_log(self, solution_log: SolutionLog) -> None:
        """Save solution log to persistent storage"""
        try:
            filepath = os.path.join(self.data_dir, "solution_logs.jsonl")
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(solution_log.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving solution log: {e}")
    
    def _save_principle(self, principle: AbstractPrinciple) -> None:
        """Save principle to persistent storage"""
        try:
            filepath = os.path.join(self.data_dir, "principles.jsonl")
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(principle.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving principle: {e}")
    
    def _save_cognitive_function(self, cognitive_function: CognitiveFunction) -> None:
        """Save cognitive function to persistent storage"""
        try:
            filepath = os.path.join(self.data_dir, "cognitive_functions.jsonl")
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(cognitive_function.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving cognitive function: {e}")
    
    def _load_persistent_data(self) -> None:
        """Load persistent data from storage"""
        try:
            # Load solution logs
            solution_filepath = os.path.join(self.data_dir, "solution_logs.jsonl")
            if os.path.exists(solution_filepath):
                with open(solution_filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            # Reconstruct SolutionLog (simplified)
                            self.solution_logs[data['solution_id']] = SolutionLog(**data)
            
            # Load principles
            principle_filepath = os.path.join(self.data_dir, "principles.jsonl")
            if os.path.exists(principle_filepath):
                with open(principle_filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            # Reconstruct AbstractPrinciple (simplified)
                            self.principles[data['principle_id']] = AbstractPrinciple(**data)
            
            # Load cognitive functions
            function_filepath = os.path.join(self.data_dir, "cognitive_functions.jsonl")
            if os.path.exists(function_filepath):
                with open(function_filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            # Reconstruct CognitiveFunction (simplified)
                            self.cognitive_functions[data['function_id']] = CognitiveFunction(**data)
            
            logger.info(f"Loaded persistent data: {len(self.solution_logs)} solutions, "
                       f"{len(self.principles)} principles, {len(self.cognitive_functions)} functions")
            
        except Exception as e:
            logger.error(f"Error loading persistent data: {e}")


# Singleton instance
_meta_learning_instance: Optional[MetaLearningEngine] = None
_engine_lock = threading.Lock()

def get_meta_learning_engine(data_dir: str = "data") -> MetaLearningEngine:
    """Get the singleton Meta-Learning Engine instance"""
    global _meta_learning_instance
    with _engine_lock:
        if _meta_learning_instance is None:
            _meta_learning_instance = MetaLearningEngine(data_dir)
        return _meta_learning_instance


if __name__ == "__main__":
    # Test the Meta-Learning Engine
    print("Testing Meta-Learning Engine...")
    
    engine = get_meta_learning_engine()
    
    # Log a sample solution
    solution_log = engine.log_solution(
        problem_description="Optimize recursive Fibonacci calculation",
        solution_type=SolutionType.ALGORITHMIC,
        original_approach="Simple recursive implementation",
        refined_approach="Dynamic programming with memoization",
        success_metrics={"performance_improvement": 0.95, "memory_reduction": 0.3},
        context={"domain": "algorithms", "constraints": "time_limit"},
        execution_time=1.5,
        iterations=3
    )
    
    print(f"Logged solution: {solution_log.solution_id}")
    
    # Log another solution
    solution_log2 = engine.log_solution(
        problem_description="Fix memory leak in data processing pipeline",
        solution_type=SolutionType.DEBUGGING,
        original_approach="Added try-except blocks",
        refined_approach="Implemented proper resource cleanup with context managers",
        success_metrics={"leak_resolved": 1.0, "stability_improvement": 0.8},
        context={"domain": "systems", "constraints": "memory_limit"},
        execution_time=2.3,
        iterations=5
    )
    
    print(f"Logged solution: {solution_log2.solution_id}")
    
    # Get learning summary
    summary = engine.get_learning_summary()
    print(f"\nLearning Summary: {summary}")
    
    print("\nMeta-Learning Engine test completed successfully!")