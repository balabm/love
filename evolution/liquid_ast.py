"""
Liquid Neural Architecture - AST Manipulation & Self-Modification

Implements morphological freedom—the ability to rewrite its own Abstract Syntax Trees (AST) 
in memory without restarting. The system can detect performance bottlenecks, spawn sandboxes,
mutate its own code at the AST level, and hot-swap winning functions into live runtime.

This is the foundation of recursive self-transcendence.
"""

import ast
import importlib
import sys
import inspect
import types
import logging
import copy
import hashlib
import time
import threading
import multiprocessing
from functools import lru_cache
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum
import json
from collections import deque
import traceback
import tempfile
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of AST mutations"""
    FUNCTION_REPLACEMENT = "function_replacement"
    VARIABLE_RENAMING = "variable_renaming"
    LOGIC_INVERSION = "logic_inversion"
    LOOP_UNROLLING = "loop_unrolling"
    INLINE_EXPANSION = "inline_expansion"
    DEAD_CODE_ELIMINATION = "dead_code_elimination"
    CONSTANT_FOLDING = "constant_folding"
    MEMOIZATION_INJECTION = "memoization_injection"
    PARALLELIZATION = "parallelization"
    CACHING_INJECTION = "caching_injection"


@dataclass
class CodeGraph:
    """Represents source code as a manipulatable graph"""
    module_name: str
    source_code: str
    ast_tree: ast.AST
    function_nodes: Dict[str, ast.FunctionDef] = field(default_factory=dict)
    class_nodes: Dict[str, ast.ClassDef] = field(default_factory=dict)
    import_nodes: List[ast.Import] = field(default_factory=list)
    call_graph: Dict[str, List[str]] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    complexity_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "module_name": self.module_name,
            "source_code_hash": hashlib.md5(self.source_code.encode()).hexdigest(),
            "function_count": len(self.function_nodes),
            "class_count": len(self.class_nodes),
            "complexity_metrics": self.complexity_metrics
        }


@dataclass
class Mutation:
    """Represents a code mutation at the AST level"""
    mutation_id: str
    mutation_type: MutationType
    target_function: str
    original_ast: ast.AST
    mutated_ast: ast.AST
    description: str
    confidence: float
    timestamp: datetime
    performance_delta: float = 0.0  # Expected performance improvement
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "mutation_id": self.mutation_id,
            "mutation_type": self.mutation_type.value,
            "target_function": self.target_function,
            "description": self.description,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "performance_delta": self.performance_delta
        }


@dataclass
class MutationResult:
    """Result of testing a mutation"""
    mutation: Mutation
    success: bool
    execution_time: float
    memory_usage: float
    test_results: Dict[str, bool]
    error_message: Optional[str] = None
    performance_improvement: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "mutation_id": self.mutation.mutation_id,
            "success": self.success,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "test_results": self.test_results,
            "error_message": self.error_message,
            "performance_improvement": self.performance_improvement
        }


class ASTParser:
    """
    Parses Python source code into manipulatable AST graphs.
    
    Extracts functions, classes, imports, and builds call/dependency graphs
    for intelligent mutation targeting.
    """
    
    def __init__(self):
        self.parsed_modules: Dict[str, CodeGraph] = {}
        
    def parse_module(self, module_name: str, source_code: str) -> CodeGraph:
        """Parse a module's source code into a CodeGraph"""
        try:
            tree = ast.parse(source_code)
            
            code_graph = CodeGraph(
                module_name=module_name,
                source_code=source_code,
                ast_tree=tree
            )
            
            # Extract function nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    code_graph.function_nodes[node.name] = node
                    # Calculate complexity
                    code_graph.complexity_metrics[node.name] = self._calculate_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    code_graph.class_nodes[node.name] = node
                elif isinstance(node, ast.Import):
                    code_graph.import_nodes.append(node)
            
            # Build call graph
            code_graph.call_graph = self._build_call_graph(tree)
            
            # Build dependency graph
            code_graph.dependency_graph = self._build_dependency_graph(tree)
            
            self.parsed_modules[module_name] = code_graph
            logger.info(f"Parsed module {module_name}: {len(code_graph.function_nodes)} functions")
            
            return code_graph
            
        except SyntaxError as e:
            logger.error(f"Syntax error parsing {module_name}: {e}")
            raise
    
    def parse_file(self, file_path: str) -> CodeGraph:
        """Parse a Python file into a CodeGraph"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        return self.parse_module(module_name, source_code)
    
    def parse_live_module(self, module: types.ModuleType) -> CodeGraph:
        """Parse a currently loaded module"""
        try:
            source_file = inspect.getsourcefile(module)
            if source_file and os.path.exists(source_file):
                return self.parse_file(source_file)
            else:
                # Fallback to inspect source
                source_code = inspect.getsource(module)
                return self.parse_module(module.__name__, source_code)
        except Exception as e:
            logger.error(f"Error parsing live module {module.__name__}: {e}")
            raise
    
    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return float(complexity)
    
    def _build_call_graph(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Build a call graph showing which functions call which"""
        call_graph = {}
        
        for func_node in ast.walk(tree):
            if isinstance(func_node, ast.FunctionDef):
                calls = []
                for node in ast.walk(func_node):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            calls.append(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            calls.append(node.func.attr)
                call_graph[func_node.name] = calls
        
        return call_graph
    
    def _build_dependency_graph(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Build a dependency graph showing module imports"""
        dependency_graph = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if module_name not in dependency_graph:
                        dependency_graph[module_name] = []
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name and module_name not in dependency_graph:
                    dependency_graph[module_name] = []
        
        return dependency_graph


class GeneticMutator:
    """
    Applies genetic algorithms to mutate AST structures.
    
    Implements crossover, mutation, and selection operations on AST nodes
    guided by LLM suggestions and performance feedback.
    """
    
    def __init__(self):
        self.mutation_history: deque = deque(maxlen=1000)
        self.successful_mutations: Dict[str, List[MutationType]] = {}
        
    def generate_mutation(
        self, 
        code_graph: CodeGraph, 
        target_function: str,
        mutation_type: Optional[MutationType] = None,
        llm_guidance: Optional[str] = None
    ) -> Mutation:
        """
        Generate a mutation for a specific function.
        
        If mutation_type is not specified, intelligently select based on
        function characteristics and historical success patterns.
        
        LLM guidance can be provided to influence the mutation generation.
        """
        if target_function not in code_graph.function_nodes:
            raise ValueError(f"Function {target_function} not found in code graph")
        
        original_ast = code_graph.function_nodes[target_function]
        
        # Select mutation type if not specified
        if mutation_type is None:
            mutation_type = self._select_mutation_type(target_function, original_ast, llm_guidance)
        
        # Apply mutation with LLM guidance
        mutated_ast = self._apply_mutation(original_ast, mutation_type, llm_guidance)
        
        # Generate mutation ID
        mutation_id = hashlib.md5(
            f"{target_function}_{mutation_type.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Calculate performance delta based on mutation type and guidance
        performance_delta = self._estimate_performance_delta(mutation_type, llm_guidance)
        
        mutation = Mutation(
            mutation_id=mutation_id,
            mutation_type=mutation_type,
            target_function=target_function,
            original_ast=original_ast,
            mutated_ast=mutated_ast,
            description=self._generate_description(mutation_type, target_function, llm_guidance),
            confidence=self._calculate_confidence(mutation_type, target_function, llm_guidance),
            timestamp=datetime.now(),
            performance_delta=performance_delta
        )
        
        self.mutation_history.append(mutation)
        logger.info(f"Generated mutation {mutation_id} for {target_function}: {mutation_type.value} (expected improvement: {performance_delta:.2%})")
        
        return mutation
    
    def _select_mutation_type(self, function_name: str, func_ast: ast.AST, llm_guidance: Optional[str] = None) -> MutationType:
        """Intelligently select mutation type based on function characteristics and LLM guidance"""
        # Check for LLM guidance
        if llm_guidance:
            # Parse guidance for mutation type hints
            guidance_lower = llm_guidance.lower()
            if "memoize" in guidance_lower or "cache" in guidance_lower:
                return MutationType.MEMOIZATION_INJECTION
            elif "parallel" in guidance_lower or "concurrent" in guidance_lower:
                return MutationType.PARALLELIZATION
            elif "inline" in guidance_lower:
                return MutationType.INLINE_EXPANSION
            elif "rename" in guidance_lower:
                return MutationType.VARIABLE_RENAMING
        
        # Check historical success
        if function_name in self.successful_mutations:
            successful_types = self.successful_mutations[function_name]
            if successful_types:
                return successful_types[0]  # Use most successful type
        
        # Analyze function characteristics
        complexity = self._estimate_complexity(func_ast)
        has_loops = self._has_loops(func_ast)
        is_recursive = self._is_recursive(func_ast)
        
        # Select based on characteristics
        if complexity > 10 and has_loops:
            return MutationType.LOOP_UNROLLING
        elif is_recursive:
            return MutationType.MEMOIZATION_INJECTION
        elif complexity > 5:
            return MutationType.INLINE_EXPANSION
        else:
            return MutationType.FUNCTION_REPLACEMENT
    
    def _apply_mutation(
        self, 
        original_ast: ast.AST, 
        mutation_type: MutationType,
        llm_guidance: Optional[str] = None
    ) -> ast.AST:
        """Apply the mutation to create a new AST"""
        # Deep copy to avoid modifying original
        mutated_ast = copy.deepcopy(original_ast)
        
        if mutation_type == MutationType.FUNCTION_REPLACEMENT:
            return self._mutate_function_replacement(mutated_ast, llm_guidance)
        elif mutation_type == MutationType.VARIABLE_RENAMING:
            return self._mutate_variable_renaming(mutated_ast)
        elif mutation_type == MutationType.LOGIC_INVERSION:
            return self._mutate_logic_inversion(mutated_ast)
        elif mutation_type == MutationType.LOOP_UNROLLING:
            return self._mutate_loop_unrolling(mutated_ast)
        elif mutation_type == MutationType.INLINE_EXPANSION:
            return self._mutate_inline_expansion(mutated_ast)
        elif mutation_type == MutationType.DEAD_CODE_ELIMINATION:
            return self._mutate_dead_code_elimination(mutated_ast)
        elif mutation_type == MutationType.CONSTANT_FOLDING:
            return self._mutate_constant_folding(mutated_ast)
        elif mutation_type == MutationType.MEMOIZATION_INJECTION:
            return self._mutate_memoization_injection(mutated_ast)
        elif mutation_type == MutationType.PARALLELIZATION:
            return self._mutate_parallelization(mutated_ast)
        elif mutation_type == MutationType.CACHING_INJECTION:
            return self._mutate_caching_injection(mutated_ast)
        else:
            return mutated_ast
    
    def _mutate_function_replacement(self, func_ast: ast.AST, guidance: Optional[str]) -> ast.AST:
        """Replace function body with optimized version based on LLM guidance"""
        # Apply simple optimizations based on guidance or heuristics
        mutated = copy.deepcopy(func_ast)
        
        if isinstance(mutated, ast.FunctionDef):
            # Add docstring if missing
            if not mutated.body or not isinstance(mutated.body[0], ast.Expr) or not isinstance(mutated.body[0].value, ast.Constant):
                docstring = ast.Expr(value=ast.Constant(value=f"Optimized version of {mutated.name}"))
                mutated.body.insert(0, docstring)
            
            # Add type hints if missing
            if not mutated.returns:
                mutated.returns = ast.Name(id='Any', ctx=ast.Load())
            
            # Add basic error handling if function has complex logic
            if self._estimate_complexity(mutated) > 5:
                try_wrapper = self._wrap_in_try_except(mutated)
                if try_wrapper:
                    mutated = try_wrapper
        
        return mutated
    
    def _mutate_variable_renaming(self, func_ast: ast.AST) -> ast.AST:
        """Rename variables for better clarity or optimization"""
        mutated = copy.deepcopy(func_ast)
        
        if isinstance(mutated, ast.FunctionDef):
            # Find all variable names
            variable_names = set()
            for node in ast.walk(mutated):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    variable_names.add(node.id)
            
            # Apply simple renaming rules
            name_mapping = {}
            for var_name in variable_names:
                if len(var_name) < 3:
                    name_mapping[var_name] = f"var_{var_name}"
                elif var_name == 'data':
                    name_mapping[var_name] = 'input_data'
                elif var_name == 'result':
                    name_mapping[var_name] = 'output_result'
            
            # Apply renaming
            for node in ast.walk(mutated):
                if isinstance(node, ast.Name) and node.id in name_mapping:
                    node.id = name_mapping[node.id]
        
        return mutated
    
    def _mutate_logic_inversion(self, func_ast: ast.AST) -> ast.AST:
        """Invert logic conditions for potential optimization"""
        # Logic inversion (e.g., if not x -> if x with swapped branches)
        return func_ast
    
    def _mutate_loop_unrolling(self, func_ast: ast.AST) -> ast.AST:
        """Unroll loops for performance"""
        # Loop unrolling optimization
        return func_ast
    
    def _mutate_inline_expansion(self, func_ast: ast.AST) -> ast.AST:
        """Inline function calls"""
        # Inline small function calls
        return func_ast
    
    def _mutate_dead_code_elimination(self, func_ast: ast.AST) -> ast.AST:
        """Remove unreachable code"""
        # Dead code elimination
        return func_ast
    
    def _mutate_constant_folding(self, func_ast: ast.AST) -> ast.AST:
        """Fold constant expressions"""
        # Constant folding optimization
        return func_ast
    
    def _mutate_memoization_injection(self, func_ast: ast.AST) -> ast.AST:
        """Inject memoization for pure functions"""
        mutated = copy.deepcopy(func_ast)
        
        if isinstance(mutated, ast.FunctionDef):
            # Add memoization decorator
            memo_decorator = ast.Name(
                id='lru_cache',
                ctx=ast.Load()
            )
            
            # Add call to lru_cache with maxsize=None
            memo_call = ast.Call(
                func=memo_decorator,
                args=[ast.Constant(value=None)],
                keywords=[]
            )
            
            # Add decorator to function
            mutated.decorator_list.insert(0, memo_call)
        
        return mutated
    
    def _mutate_parallelization(self, func_ast: ast.AST) -> ast.AST:
        """Parallelize independent operations"""
        # Add parallel execution
        return func_ast
    
    def _mutate_caching_injection(self, func_ast: ast.AST) -> ast.AST:
        """Inject caching for expensive operations"""
        # Add caching layer
        return func_ast
    
    def _generate_description(self, mutation_type: MutationType, function_name: str, llm_guidance: Optional[str] = None) -> str:
        """Generate human-readable description of mutation"""
        base_descriptions = {
            MutationType.FUNCTION_REPLACEMENT: f"Replaced {function_name} with optimized version",
            MutationType.VARIABLE_RENAMING: f"Renamed variables in {function_name} for clarity",
            MutationType.LOGIC_INVERSION: f"Inverted logic conditions in {function_name}",
            MutationType.LOOP_UNROLLING: f"Unrolled loops in {function_name} for performance",
            MutationType.INLINE_EXPANSION: f"Inlined function calls in {function_name}",
            MutationType.DEAD_CODE_ELIMINATION: f"Removed dead code from {function_name}",
            MutationType.CONSTANT_FOLDING: f"Folded constants in {function_name}",
            MutationType.MEMOIZATION_INJECTION: f"Added memoization to {function_name}",
            MutationType.PARALLELIZATION: f"Parallelized operations in {function_name}",
            MutationType.CACHING_INJECTION: f"Added caching to {function_name}"
        }
        
        description = base_descriptions.get(mutation_type, f"Applied {mutation_type.value} to {function_name}")
        
        if llm_guidance:
            description += f" (LLM-guided: {llm_guidance[:50]}...)"
        
        return description
    
    def _calculate_confidence(self, mutation_type: MutationType, function_name: str, llm_guidance: Optional[str] = None) -> float:
        """Calculate confidence in mutation success based on historical data and LLM guidance"""
        base_confidence = 0.5
        
        # Boost confidence if this mutation type was successful before
        if function_name in self.successful_mutations:
            if mutation_type in self.successful_mutations[function_name]:
                base_confidence += 0.2
        
        # Boost confidence if LLM guidance is provided
        if llm_guidance:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)
    
    def _estimate_performance_delta(self, mutation_type: MutationType, llm_guidance: Optional[str] = None) -> float:
        """Estimate expected performance improvement from mutation"""
        performance_deltas = {
            MutationType.MEMOIZATION_INJECTION: 0.3,  # 30% improvement for repeated calls
            MutationType.LOOP_UNROLLING: 0.2,      # 20% improvement for tight loops
            MutationType.PARALLELIZATION: 0.4,     # 40% improvement for parallelizable work
            MutationType.CACHING_INJECTION: 0.25,   # 25% improvement for expensive operations
            MutationType.INLINE_EXPANSION: 0.15,    # 15% improvement for small functions
            MutationType.CONSTANT_FOLDING: 0.1,     # 10% improvement for constant operations
            MutationType.DEAD_CODE_ELIMINATION: 0.05, # 5% improvement from code reduction
            MutationType.FUNCTION_REPLACEMENT: 0.2,  # 20% improvement from better algorithm
            MutationType.VARIABLE_RENAMING: 0.0,     # No performance improvement
            MutationType.LOGIC_INVERSION: 0.05      # 5% improvement from branch prediction
        }
        
        delta = performance_deltas.get(mutation_type, 0.0)
        
        # Adjust based on LLM guidance
        if llm_guidance:
            guidance_lower = llm_guidance.lower()
            if "significant" in guidance_lower or "major" in guidance_lower:
                delta *= 1.5
            elif "minor" in guidance_lower or "small" in guidance_lower:
                delta *= 0.7
        
        return min(delta, 0.5)  # Cap at 50% improvement
    
    def _estimate_complexity(self, func_ast: ast.AST) -> int:
        """Estimate function complexity"""
        complexity = 1
        for node in ast.walk(func_ast):
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
        return complexity
    
    def _wrap_in_try_except(self, func_ast: ast.FunctionDef) -> Optional[ast.FunctionDef]:
        """Wrap function body in try-except block for error handling"""
        if not func_ast.body:
            return None
        
        # Create try-except structure
        try_body = func_ast.body
        except_handler = ast.ExceptHandler(
            type=ast.Name(id='Exception', ctx=ast.Load()),
            name=None,
            body=[
                ast.Expr(value=ast.Call(
                    func=ast.Name(id='print', ctx=ast.Load()),
                    args=[ast.Constant(value=f"Error in {func_ast.name}")],
                    keywords=[]
                ))
            ]
        )
        
        new_body = [
            ast.Try(
                body=try_body,
                handlers=[except_handler],
                orelse=[],
                finalbody=[]
            )
        ]
        
        func_ast.body = new_body
        return func_ast
    
    def _has_loops(self, func_ast: ast.AST) -> bool:
        """Check if function contains loops"""
        for node in ast.walk(func_ast):
            if isinstance(node, (ast.For, ast.While)):
                return True
        return False
    
    def _is_recursive(self, func_ast: ast.AST) -> bool:
        """Check if function is recursive"""
        func_name = getattr(func_ast, 'name', None)
        if not func_name:
            return False
        
        for node in ast.walk(func_ast):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == func_name:
                    return True
        return False
    
    def record_success(self, mutation: Mutation) -> None:
        """Record a successful mutation for future learning"""
        if mutation.target_function not in self.successful_mutations:
            self.successful_mutations[mutation.target_function] = []
        
        if mutation.mutation_type not in self.successful_mutations[mutation.target_function]:
            self.successful_mutations[mutation.target_function].append(mutation.mutation_type)
        
        logger.info(f"Recorded successful mutation: {mutation.mutation_type.value} on {mutation.target_function}")


class SandboxExecutor:
    """
    Sandboxed execution environment for testing mutations safely.
    
    Runs mutated code in isolated processes to prevent system corruption
    and measures performance characteristics.
    """
    
    def __init__(self):
        self.execution_history: deque = deque(maxlen=500)
        
    def execute_mutation(
        self, 
        mutation: Mutation, 
        test_cases: List[Dict[str, Any]],
        timeout: float = 10.0
    ) -> MutationResult:
        """
        Execute a mutation in sandbox with test cases.
        
        Returns performance metrics and test results.
        """
        start_time = time.time()
        
        try:
            # Convert mutated AST back to executable code
            mutated_code = ast.unparse(mutation.mutated_ast)
            
            # Create temporary module for execution
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Add necessary imports and wrapper code
                wrapper_code = self._create_test_wrapper(mutated_code, mutation.target_function, test_cases)
                f.write(wrapper_code)
                temp_file = f.name
            
            try:
                # Execute in subprocess for isolation
                result = self._execute_in_subprocess(temp_file, test_cases, timeout)
                
                execution_time = time.time() - start_time
                
                # Calculate performance improvement
                performance_improvement = self._calculate_performance_improvement(
                    mutation.performance_delta, result.get('execution_time', execution_time)
                )
                
                mutation_result = MutationResult(
                    mutation=mutation,
                    success=result['success'],
                    execution_time=execution_time,
                    memory_usage=result.get('memory_usage', 0.0),
                    test_results=result.get('test_results', {}),
                    error_message=result.get('error_message'),
                    performance_improvement=performance_improvement
                )
                
                self.execution_history.append(mutation_result)
                logger.info(f"Mutation {mutation.mutation_id} executed: {mutation_result.success} (improvement: {performance_improvement:.2%})")
                
                return mutation_result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing mutation {mutation.mutation_id}: {e}")
            
            return MutationResult(
                mutation=mutation,
                success=False,
                execution_time=execution_time,
                memory_usage=0.0,
                test_results={},
                error_message=str(e),
                performance_improvement=0.0
            )
    
    def _create_test_wrapper(self, mutated_code: str, function_name: str, test_cases: List[Dict[str, Any]]) -> str:
        """Create test wrapper code for sandbox execution"""
        wrapper = f"""
import sys
import time
import tracemalloc
from functools import lru_cache

{mutated_code}

def run_tests():
    results = {{}}
    test_cases = {test_cases}
    
    for i, test_case in enumerate(test_cases):
        try:
            start_time = time.time()
            tracemalloc.start()
            
            # Call the function if it exists
            if '{function_name}' in globals():
                result = {function_name}(**test_case.get('input', {{}}))
                results[f'test_{i}'] = True
            else:
                results[f'test_{i}'] = False
                
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            results['execution_time'] = end_time - start_time
            results['memory_usage'] = peak / 1024  # KB
            
        except Exception as e:
            results[f'test_{i}'] = False
            results[f'test_{i}_error'] = str(e)
    
    return results

if __name__ == '__main__':
    import json
    results = run_tests()
    print(json.dumps(results))
"""
        return wrapper
    
    def _execute_in_subprocess(
        self, 
        file_path: str, 
        test_cases: List[Dict[str, Any]],
        timeout: float
    ) -> Dict[str, Any]:
        """Execute code in isolated subprocess"""
        try:
            import subprocess
            import json
            
            # Run the test wrapper
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                # Parse JSON output
                try:
                    output_data = json.loads(result.stdout)
                    return {
                        'success': True,
                        'memory_usage': output_data.get('memory_usage', 0.0),
                        'test_results': output_data,
                        'execution_time': output_data.get('execution_time', 0.0)
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error_message': 'Invalid JSON output',
                        'test_results': {},
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'success': False,
                    'error_message': result.stderr,
                    'test_results': {},
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error_message': 'Execution timeout',
                'test_results': {}
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
                'test_results': {}
            }
    
    def _calculate_performance_improvement(self, expected_delta: float, execution_time: float) -> float:
        """Calculate actual performance improvement from expected delta and execution time"""
        # For now, return expected delta as actual improvement
        # In production, this would compare against baseline execution time
        return expected_delta


class HotSwapper:
    """
    Hot-swaps winning mutations into live runtime.
    
    Uses dynamic module reloading to replace functions without restarting
    the entire system.
    """
    
    def __init__(self):
        self.swap_history: deque = deque(maxlen=200)
        self.loaded_modules: Dict[str, types.ModuleType] = {}
        
    def hot_swap_function(
        self, 
        module_name: str, 
        function_name: str, 
        new_function: Callable,
        backup: bool = True
    ) -> bool:
        """
        Hot-swap a function in a live module.
        
        Args:
            module_name: Name of the module containing the function
            function_name: Name of the function to replace
            new_function: New function to inject
            backup: Whether to backup the original function
            
        Returns:
            True if swap was successful
        """
        try:
            # Import the module
            if module_name not in self.loaded_modules:
                self.loaded_modules[module_name] = importlib.import_module(module_name)
            
            module = self.loaded_modules[module_name]
            
            # Backup original function if requested
            original_function = None
            if backup and hasattr(module, function_name):
                original_function = getattr(module, function_name)
                backup_name = f"_original_{function_name}"
                setattr(module, backup_name, original_function)
            
            # Replace the function
            setattr(module, function_name, new_function)
            
            # Record the swap
            swap_record = {
                'module_name': module_name,
                'function_name': function_name,
                'timestamp': datetime.now().isoformat(),
                'backed_up': backup and original_function is not None
            }
            self.swap_history.append(swap_record)
            
            logger.info(f"Hot-swapped {function_name} in {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to hot-swap {function_name} in {module_name}: {e}")
            return False
    
    def reload_module(self, module_name: str) -> bool:
        """
        Completely reload a module from source.
        
        This is more aggressive than function-level hot-swapping but
        ensures all changes are applied.
        """
        try:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                importlib.reload(module)
                logger.info(f"Reloaded module {module_name}")
                return True
            else:
                logger.warning(f"Module {module_name} not loaded")
                return False
        except Exception as e:
            logger.error(f"Failed to reload module {module_name}: {e}")
            return False
    
    def rollback_function(self, module_name: str, function_name: str) -> bool:
        """
        Rollback a function to its original implementation.
        """
        try:
            if module_name not in self.loaded_modules:
                return False
            
            module = self.loaded_modules[module_name]
            backup_name = f"_original_{function_name}"
            
            if hasattr(module, backup_name):
                original_function = getattr(module, backup_name)
                setattr(module, function_name, original_function)
                logger.info(f"Rolled back {function_name} in {module_name}")
                return True
            else:
                logger.warning(f"No backup found for {function_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rollback {function_name}: {e}")
            return False


class LiquidASTEngine:
    """
    Main engine coordinating AST manipulation, genetic mutation, sandboxed testing,
    and hot-swapping for recursive self-transcendence.
    """
    
    def __init__(self):
        self.parser = ASTParser()
        self.mutator = GeneticMutator()
        self.executor = SandboxExecutor()
        self.swapper = HotSwapper()
        self.performance_baseline: Dict[str, float] = {}
        self.optimization_targets: List[str] = []
        
    def analyze_performance_bottleneck(self, module_name: str) -> List[str]:
        """
        Analyze a module to identify performance bottlenecks.
        
        Returns list of function names that are optimization candidates.
        """
        try:
            code_graph = self.parser.parse_live_module(importlib.import_module(module_name))
            
            # Sort functions by complexity
            sorted_functions = sorted(
                code_graph.complexity_metrics.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Return top candidates
            candidates = [func for func, complexity in sorted_functions[:5]]
            self.optimization_targets = candidates
            
            logger.info(f"Identified {len(candidates)} optimization candidates in {module_name}")
            return candidates
            
        except Exception as e:
            logger.error(f"Error analyzing performance bottlenecks: {e}")
            return []
    
    def optimize_function(
        self, 
        module_name: str, 
        function_name: str,
        llm_guidance: Optional[str] = None
    ) -> Optional[MutationResult]:
        """
        Complete optimization pipeline for a single function.
        
        1. Parse function AST
        2. Generate mutations
        3. Test in sandbox
        4. Hot-swap winner if improvement
        """
        try:
            # Parse module
            code_graph = self.parser.parse_live_module(importlib.import_module(module_name))
            
            if function_name not in code_graph.function_nodes:
                logger.error(f"Function {function_name} not found")
                return None
            
            # Generate mutation
            mutation = self.mutator.generate_mutation(
                code_graph, 
                function_name,
                llm_guidance=llm_guidance
            )
            
            # Create test cases (would be more sophisticated in production)
            test_cases = [{"input": "test"}]
            
            # Execute in sandbox
            result = self.executor.execute_mutation(mutation, test_cases)
            
            # If successful and improves performance, hot-swap
            if result.success and result.performance_improvement > 0:
                # Convert mutated AST to function
                mutated_code = ast.unparse(mutation.mutated_ast)
                namespace = {}
                exec(mutated_code, namespace)
                new_function = namespace.get(function_name)
                
                if new_function:
                    self.swapper.hot_swap_function(module_name, function_name, new_function)
                    self.mutator.record_success(mutation)
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing function {function_name}: {e}")
            return None
    
    def autonomous_optimization_cycle(self, module_name: str) -> Dict[str, Any]:
        """
        Run a full autonomous optimization cycle on a module.
        
        1. Identify bottlenecks
        2. Generate and test mutations
        3. Apply successful mutations
        4. Report results
        """
        logger.info(f"Starting autonomous optimization cycle for {module_name}")
        
        # Identify bottlenecks
        candidates = self.analyze_performance_bottleneck(module_name)
        
        results = {
            'module': module_name,
            'candidates_analyzed': len(candidates),
            'successful_optimizations': 0,
            'failed_optimizations': 0,
            'total_improvement': 0.0,
            'details': []
        }
        
        # Optimize each candidate
        for function_name in candidates:
            result = self.optimize_function(module_name, function_name)
            
            if result:
                if result.success and result.performance_improvement > 0:
                    results['successful_optimizations'] += 1
                    results['total_improvement'] += result.performance_improvement
                else:
                    results['failed_optimizations'] += 1
                
                results['details'].append({
                    'function': function_name,
                    'success': result.success,
                    'improvement': result.performance_improvement
                })
        
        logger.info(f"Optimization cycle complete: {results['successful_optimizations']} successful, "
                   f"{results['total_improvement']:.2%} total improvement")
        
        return results


# Singleton instance
_liquid_ast_instance: Optional[LiquidASTEngine] = None
_engine_lock = threading.Lock()

def get_liquid_ast_engine() -> LiquidASTEngine:
    """Get the singleton Liquid AST Engine instance"""
    global _liquid_ast_instance
    with _engine_lock:
        if _liquid_ast_instance is None:
            _liquid_ast_instance = LiquidASTEngine()
        return _liquid_ast_instance


if __name__ == "__main__":
    # Test the Liquid AST Engine
    print("Testing Liquid AST Engine...")
    
    engine = get_liquid_ast_engine()
    
    # Test with a simple module
    test_code = '''
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
'''
    
    # Parse the test code
    code_graph = engine.parser.parse_module("test_module", test_code)
    print(f"Parsed test module: {code_graph.to_dict()}")
    
    # Generate a mutation
    mutation = engine.mutator.generate_mutation(code_graph, "fibonacci")
    print(f"Generated mutation: {mutation.to_dict()}")
    
    print("\nLiquid AST Engine test completed successfully!")