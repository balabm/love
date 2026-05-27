"""
Symbiotic Interface - Zero-Latency Predictive Intent

The interaction paradigm shifts from "Command-Response" to "Symbiotic Extension."
The system begins executing solutions before the user finishes formulating the problem.

Ingests keystroke velocity, mouse micro-movements, eye-tracking (if hardware available),
and code-editor state into a continuous stream. Trains a lightweight local sub-model to
detect "Friction Signatures" (e.g., deleting and rewriting the same variable three times,
rapid tab switching between docs and IDE).

When a Friction Signature breaches the confidence threshold, the system dynamically
renders the exact solution (a refactored function, a compiled doc-snippet, or a terminal
command) directly into the Antigravity IDE's predictive buffer, waiting for a single
Tab to accept.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from collections import deque
import hashlib
import json
import threading
import time
import re
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InputType(Enum):
    """Types of input signals for intent decoding"""
    KEYSTROKE = "keystroke"
    MOUSE_MOVEMENT = "mouse_movement"
    MOUSE_CLICK = "mouse_click"
    EYE_TRACKING = "eye_tracking"
    EDITOR_STATE = "editor_state"
    VOICE_PATTERN = "voice_pattern"
    TIMING_PATTERN = "timing_pattern"


class FrictionType(Enum):
    """Types of friction signatures that indicate user needs help"""
    REPETITIVE_EDITING = "repetitive_editing"  # Rewriting same code multiple times
    RAPID_CONTEXT_SWITCHING = "rapid_context_switching"  # Fast tab/document switching
    HESITATION_PATTERN = "hesitation_pattern"  # Pauses, backspaces, corrections
    SEARCH_PATTERN = "search_pattern"  * 10  # Looking for documentation/solutions
    DEBUGGING_LOOP = "debugging_loop"  # Repeated test-fix cycles
    SYNTAX_CONFUSION = "syntax_confusion"  # Struggling with syntax
    API_FORGETFULNESS = "api_forgetfulness"  * 10  # Can't remember API details
    LOGIC_BLOCK = "logic_block"  # Stuck on algorithm/logic


class SolutionType(Enum):
    """Types of predictive solutions"""
    CODE_COMPLETION = "code_completion"
    REFACTORING_SUGGESTION = "refactoring_suggestion"
    DOCUMENTATION_SNIPPET = "documentation_snippet"
    TERMINAL_COMMAND = "terminal_command"
    API_USAGE_EXAMPLE = "api_usage_example"
    ALGORITHM_HINT = "algorithm_hint"
    DEBUGGING_SUGGESTION = "debugging_suggestion"
    IMPORT_SUGGESTION = "import_suggestion"


@dataclass
class InputSignal:
    """A raw input signal from the user"""
    signal_id: str
    input_type: InputType
    timestamp: datetime
    data: Dict[str, Any]
    velocity: float = 0.0  # Speed of input (keystrokes/sec, pixels/sec, etc.)
    pressure: float = 0.0  # Force/intensity of input
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "signal_id": self.signal_id,
            "input_type": self.input_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "velocity": self.velocity,
            "pressure": self.pressure
        }


@dataclass
class FrictionSignature:
    """A detected friction signature indicating user needs help"""
    signature_id: str
    friction_type: FrictionType
    confidence: float
    severity: float  # How severe the friction is
    context: Dict[str, Any]
    contributing_signals: List[str]  # IDs of signals that contributed
    first_detected: datetime
    last_updated: datetime
    occurrence_count: int = 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "signature_id": self.signature_id,
            "friction_type": self.friction_type.value,
            "confidence": self.confidence,
            "severity": self.severity,
            "context": self.context,
            "contributing_signals": self.contributing_signals,
            "first_detected": self.first_detected.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "occurrence_count": self.occurrence_count
        }


@dataclass
class PredictiveSolution:
    """A predictive solution generated for a friction signature"""
    solution_id: str
    solution_type: SolutionType
    content: str
    confidence: float
    source_signature: str
    context: Dict[str, Any]
    acceptance_rate: float = 0.0  # Historical acceptance rate
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "solution_id": self.solution_id,
            "solution_type": self.solution_type.value,
            "content": self.content,
            "confidence": self.confidence,
            "source_signature": self.source_signature,
            "context": self.context,
            "acceptance_rate": self.acceptance_rate,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class IntentPrediction:
    """A prediction of user intent based on input patterns"""
    prediction_id: str
    intent: str
    confidence: float
    time_horizon: timedelta  # How far into the future this predicts
    required_action: Optional[str]
    suggested_solutions: List[PredictiveSolution]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "prediction_id": self.prediction_id,
            "intent": self.intent,
            "confidence": self.confidence,
            "time_horizon_seconds": self.time_horizon.total_seconds(),
            "required_action": self.required_action,
            "suggested_solutions": [s.to_dict() for s in self.suggested_solutions],
            "timestamp": self.timestamp.isoformat()
        }


class InputStreamProcessor:
    """
    Processes continuous input streams from various sources.
    
    Ingests keystrokes, mouse movements, eye-tracking, and editor state
    to build a comprehensive picture of user intent.
    """
    
    def __init__(self, buffer_size: int = 1000):
        self.input_buffer: deque = deque(maxlen=buffer_size)
        self.velocity_calculator = VelocityCalculator()
        self.pattern_detector = PatternDetector()
        
    def add_signal(self, signal: InputSignal) -> None:
        """Add an input signal to the stream"""
        # Calculate velocity if not provided
        if signal.velocity == 0.0:
            signal.velocity = self.velocity_calculator.calculate_velocity(signal, self.input_buffer)
        
        self.input_buffer.append(signal)
        logger.debug(f"Added signal: {signal.input_type.value}")
    
    def get_recent_signals(self, time_window: timedelta = timedelta(seconds=5)) -> List[InputSignal]:
        """Get signals from the recent time window"""
        cutoff = datetime.now() - time_window
        return [s for s in self.input_buffer if s.timestamp > cutoff]
    
    def get_signals_by_type(self, input_type: InputType) -> List[InputSignal]:
        """Get all signals of a specific type"""
        return [s for s in self.input_buffer if s.input_type == input_type]
    
    def get_input_statistics(self) -> Dict[str, Any]:
        """Get statistics about the input stream"""
        if not self.input_buffer:
            return {}
        
        signals = list(self.input_buffer)
        
        # Calculate statistics
        keystroke_rate = len([s for s in signals if s.input_type == InputType.KEYSTROKE]) / 60.0  # per minute
        avg_velocity = np.mean([s.velocity for s in signals if s.velocity > 0])
        
        # Type distribution
        type_counts = {}
        for signal in signals:
            type_counts[signal.input_type.value] = type_counts.get(signal.input_type.value, 0) + 1
        
        return {
            "total_signals": len(signals),
            "keystroke_rate": keystroke_rate,
            "average_velocity": avg_velocity,
            "type_distribution": type_counts,
            "time_span": (signals[-1].timestamp - signals[0].timestamp).total_seconds() if len(signals) > 1 else 0
        }


class VelocityCalculator:
    """Calculates velocity and pressure metrics from input signals"""
    
    def __init__(self):
        self.history: Dict[str, deque] = {}  # input_type -> recent signals
        
    def calculate_velocity(self, signal: InputSignal, buffer: deque) -> float:
        """Calculate velocity based on recent signals of same type"""
        input_type = signal.input_type.value
        
        # Get recent signals of same type
        if input_type not in self.history:
            self.history[input_type] = deque(maxlen=10)
        
        recent_signals = self.history[input_type]
        
        if not recent_signals:
            recent_signals.append(signal)
            return 0.0
        
        # Calculate time difference
        time_diff = (signal.timestamp - recent_signals[-1].timestamp).total_seconds()
        
        if time_diff == 0:
            return 0.0
        
        # Calculate velocity based on input type
        if signal.input_type == InputType.KEYSTROKE:
            velocity = 1.0 / time_diff  # keystrokes per second
        elif signal.input_type in [InputType.MOUSE_MOVEMENT, InputType.MOUSE_CLICK]:
            # Calculate pixel distance
            prev_data = recent_signals[-1].data
            curr_data = signal.data
            dx = curr_data.get('x', 0) - prev_data.get('x', 0)
            dy = curr_data.get('y', 0) - prev_data.get('y', 0)
            distance = np.sqrt(dx**2 + dy**2)
            velocity = distance / time_diff  # pixels per second
        else:
            velocity = 1.0 / time_diff  # generic velocity
        
        recent_signals.append(signal)
        return velocity


class PatternDetector:
    """Detects patterns in input streams that indicate user intent"""
    
    def __init__(self):
        self.pattern_templates = {
            FrictionType.REPETITIVE_EDITING: self._detect_repetitive_editing,
            FrictionType.RAPID_CONTEXT_SWITCHING: self._detect_rapid_context_switching,
            FrictionType.HESITATION_PATTERN: self._detect_hesitation_pattern,
            FrictionType.DEBUGGING_LOOP: self._detect_debugging_loop,
            FrictionType.SYNTAX_CONFUSION: self._detect_syntax_confusion
        }
    
    def detect_patterns(self, signals: List[InputSignal]) -> List[Tuple[FrictionType, float]]:
        """Detect friction patterns in the signal stream"""
        detected_patterns = []
        
        for friction_type, detector in self.pattern_templates.items():
            confidence = detector(signals)
            if confidence > 0.5:  # Threshold for pattern detection
                detected_patterns.append((friction_type, confidence))
        
        return detected_patterns
    
    def _detect_repetitive_editing(self, signals: List[InputSignal]) -> float:
        """Detect repetitive editing patterns"""
        keystrokes = [s for s in signals if s.input_type == InputType.KEYSTROKE]
        
        if len(keystrokes) < 10:
            return 0.0
        
        # Look for repeated deletions and rewrites
        delete_count = sum(1 for k in keystrokes if k.data.get('key') == 'backspace')
        total_keystrokes = len(keystrokes)
        
        if delete_count / total_keystrokes > 0.3:  # High delete ratio
            return 0.8
        
        return 0.0
    
    def _detect_rapid_context_switching(self, signals: List[InputSignal]) -> float:
        """Detect rapid context switching (tab switching, etc.)"""
        editor_signals = [s for s in signals if s.input_type == InputType.EDITOR_STATE]
        
        if len(editor_signals) < 5:
            return 0.0
        
        # Count file/tab changes
        file_changes = 0
        prev_file = None
        
        for signal in editor_signals:
            current_file = signal.data.get('file')
            if current_file and current_file != prev_file:
                file_changes += 1
                prev_file = current_file
        
        # High frequency of file changes indicates context switching
        if file_changes / len(editor_signals) > 0.4:
            return 0.7
        
        return 0.0
    
    def _detect_hesitation_pattern(self, signals: List[InputSignal]) -> float:
        """Detect hesitation patterns (pauses, corrections)"""
        if len(signals) < 5:
            return 0.0
        
        # Calculate time variance between signals
        timestamps = [s.timestamp for s in signals]
        time_diffs = []
        
        for i in range(1, len(timestamps)):
            diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            time_diffs.append(diff)
        
        if not time_diffs:
            return 0.0
        
        # High variance in timing indicates hesitation
        time_variance = np.var(time_diffs)
        if time_variance > 1.0:  # Significant variance
            return 0.6
        
        return 0.0
    
    def _detect_debugging_loop(self, signals: List[InputSignal]) -> float:
        """Detect debugging loops (test-fix cycles)"""
        # Look for patterns of running tests and editing code
        terminal_signals = [s for s in signals if s.input_type == InputType.TERMINAL_COMMAND]
        code_signals = [s for s in signals if s.input_type == InputType.KEYSTROKE]
        
        if len(terminal_signals) < 3 or len(code_signals) < 10:
            return 0.0
        
        # Check for repeated test commands
        test_commands = [s for s in terminal_signals if 'test' in s.data.get('command', '').lower()]
        
        if len(test_commands) / len(terminal_signals) > 0.5:
            return 0.75
        
        return 0.0
    
    def _detect_syntax_confusion(self, signals: List[InputSignal]) -> float:
        """Detect syntax confusion (struggling with language syntax)"""
        keystrokes = [s for s in signals if s.input_type == InputType.KEYSTROKE]
        
        if len(keystrokes) < 15:
            return 0.0
        
        # Look for syntax error patterns (brackets, quotes, etc.)
        syntax_keys = ['(', ')', '[', ']', '{', '}', '"', "'", ':', ';']
        syntax_count = sum(1 for k in keystrokes if k.data.get('key') in syntax_keys)
        
        # High frequency of syntax keys + backspaces suggests confusion
        backspace_count = sum(1 for k in keystrokes if k.data.get('key') == 'backspace')
        
        if (syntax_count + backspace_count) / len(keystrokes) > 0.4:
            return 0.7
        
        return 0.0


class FrictionSignatureDetector:
    """
    Detects friction signatures that indicate the user needs help.
    
    Monitors input patterns and identifies when the user is struggling
    with a task, enabling proactive assistance.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.active_signatures: Dict[str, FrictionSignature] = {}
        self.pattern_detector = PatternDetector()
        self.detection_history: deque = deque(maxlen=500)
        
    def analyze_stream(self, signals: List[InputSignal]) -> List[FrictionSignature]:
        """Analyze input stream for friction signatures"""
        detected_patterns = self.pattern_detector.detect_patterns(signals)
        new_signatures = []
        
        for friction_type, confidence in detected_patterns:
            signature_id = hashlib.md5(
                f"{friction_type.value}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
            
            # Check if this signature already exists
            if signature_id in self.active_signatures:
                # Update existing signature
                existing = self.active_signatures[signature_id]
                existing.confidence = max(existing.confidence, confidence)
                existing.last_updated = datetime.now()
                existing.occurrence_count += 1
            else:
                # Create new signature
                signature = FrictionSignature(
                    signature_id=signature_id,
                    friction_type=friction_type,
                    confidence=confidence,
                    severity=self._calculate_severity(confidence, signals),
                    context=self._extract_context(signals),
                    contributing_signals=[s.signal_id for s in signals[-10:]],
                    first_detected=datetime.now(),
                    last_updated=datetime.now()
                )
                self.active_signatures[signature_id] = signature
                new_signatures.append(signature)
        
        # Clean up old signatures
        self._cleanup_old_signatures()
        
        return new_signatures
    
    def _calculate_severity(self, confidence: float, signals: List[InputSignal]) -> float:
        """Calculate severity of friction signature"""
        # Base severity from confidence
        severity = confidence
        
        # Adjust based on signal intensity
        avg_velocity = np.mean([s.velocity for s in signals if s.velocity > 0])
        if avg_velocity > 10.0:  # High velocity indicates frustration
            severity += 0.2
        
        return min(1.0, severity)
    
    def _extract_context(self, signals: List[InputSignal]) -> Dict[str, Any]:
        """Extract context from signals"""
        context = {}
        
        # Get editor state
        editor_signals = [s for s in signals if s.input_type == InputType.EDITOR_STATE]
        if editor_signals:
            latest_editor = editor_signals[-1]
            context['file'] = latest_editor.data.get('file')
            context['line'] = latest_editor.data.get('line')
            context['language'] = latest_editor.data.get('language')
        
        # Get recent keystrokes
        keystrokes = [s for s in signals if s.input_type == InputType.KEYSTROKE]
        if keystrokes:
            context['recent_keys'] = [k.data.get('key') for k in keystrokes[-20:]]
        
        return context
    
    def _cleanup_old_signatures(self) -> None:
        """Remove signatures that haven't been updated recently"""
        cutoff = datetime.now() - timedelta(minutes=5)
        
        to_remove = [
            sig_id for sig_id, sig in self.active_signatures.items()
            if sig.last_updated < cutoff
        ]
        
        for sig_id in to_remove:
            del self.active_signatures[sig_id]
    
    def get_active_signatures(self) -> List[FrictionSignature]:
        """Get all active friction signatures"""
        return list(self.active_signatures.values())
    
    def get_critical_signatures(self) -> List[FrictionSignature]:
        """Get signatures that exceed confidence threshold"""
        return [
            sig for sig in self.active_signatures.values()
            if sig.confidence >= self.confidence_threshold
        ]


class PredictiveSolutionGenerator:
    """
    Generates predictive solutions for detected friction signatures.
    
    Creates contextually relevant solutions before the user explicitly asks for help.
    """
    
    def __init__(self):
        self.solution_templates = {
            FrictionType.REPETITIVE_EDITING: self._generate_refactoring_suggestion,
            FrictionType.RAPID_CONTEXT_SWITCHING: self._generate_documentation_snippet,
            FrictionType.HESITATION_PATTERN: self._generate_code_completion,
            FrictionType.DEBUGGING_LOOP: self._generate_debugging_suggestion,
            FrictionType.SYNTAX_CONFUSION: self._generate_syntax_help
        }
        self.generation_history: deque = deque(maxlen=500)
        
    def generate_solutions(
        self, 
        signature: FrictionSignature
    ) -> List[PredictiveSolution]:
        """Generate predictive solutions for a friction signature"""
        generator = self.solution_templates.get(signature.friction_type)
        
        if not generator:
            return []
        
        solutions = generator(signature)
        
        for solution in solutions:
            self.generation_history.append(solution)
        
        return solutions
    
    def _generate_refactoring_suggestion(self, signature: FrictionSignature) -> List[PredictiveSolution]:
        """Generate refactoring suggestions for repetitive editing"""
        context = signature.context
        
        solutions = []
        
        # Generate solution ID
        solution_id = hashlib.md5(
            f"refactor_{signature.signature_id}".encode()
        ).hexdigest()[:12]
        
        # Create refactoring suggestion based on context
        if 'file' in context:
            file_ext = context['file'].split('.')[-1] if '.' in context['file'] else ''
            
            if file_ext in ['py', 'js', 'ts']:
                suggestion = f"# Consider extracting repetitive code into a function\n"
                suggestion += f"# Current pattern suggests duplication in {context['file']}\n"
                suggestion += f"# def extracted_function(params):\n"
                suggestion += f"#     # Your refactored code here\n"
                suggestion += f"#     pass"
            else:
                suggestion = f"# Consider refactoring repetitive code in {context['file']}"
            
            solution = PredictiveSolution(
                solution_id=solution_id,
                solution_type=SolutionType.REFACTORING_SUGGESTION,
                content=suggestion,
                confidence=signature.confidence,
                source_signature=signature.signature_id,
                context=context
            )
            solutions.append(solution)
        
        return solutions
    
    def _generate_documentation_snippet(self, signature: FrictionSignature) -> List[PredictiveSolution]:
        """Generate documentation snippets for rapid context switching"""
        context = signature.context
        
        solutions = []
        
        solution_id = hashlib.md5(
            f"docs_{signature.signature_id}".encode()
        ).hexdigest()[:12]
        
        # Generate documentation based on context
        if 'language' in context:
            language = context['language']
            snippet = f"# Quick reference for {language}\n"
            snippet += f"# You seem to be switching contexts frequently\n"
            snippet += f"# Consider using bookmarks or split view\n"
            
            solution = PredictiveSolution(
                solution_id=solution_id,
                solution_type=SolutionType.DOCUMENTATION_SNIPPET,
                content=snippet,
                confidence=signature.confidence * 0.8,
                source_signature=signature.signature_id,
                context=context
            )
            solutions.append(solution)
        
        return solutions
    
    def _generate_code_completion(self, signature: FrictionSignature) -> List[PredictiveSolution]:
        """Generate code completion for hesitation patterns"""
        context = signature.context
        
        solutions = []
        
        solution_id = hashlib.md5(
            f"complete_{signature.signature_id}".encode()
        ).hexdigest()[:12]
        
        # Generate completion based on recent keys
        if 'recent_keys' in context:
            recent_keys = context['recent_keys']
            # Simple completion based on recent typing
            completion = f"# Auto-completion suggestion based on: {''.join(recent_keys[-5:])}\n"
            completion += f"# Consider using IDE autocomplete or AI assistance"
            
            solution = PredictiveSolution(
                solution_id=solution_id,
                solution_type=SolutionType.CODE_COMPLETION,
                content=completion,
                confidence=signature.confidence * 0.7,
                source_signature=signature.signature_id,
                context=context
            )
            solutions.append(solution)
        
        return solutions
    
    def _generate_debugging_suggestion(self, signature: FrictionSignature) -> List[PredictiveSolution]:
        """Generate debugging suggestions for debugging loops"""
        context = signature.context
        
        solutions = []
        
        solution_id = hashlib.md5(
            f"debug_{signature.signature_id}".encode()
        ).hexdigest()[:12]
        
        suggestion = "# Debugging assistance\n"
        suggestion += "# You seem to be in a test-fix cycle\n"
        suggestion += "# Consider:\n"
        suggestion += "# 1. Adding more specific assertions\n"
        suggestion += "# 2. Using debugger instead of print statements\n"
        suggestion += "# 3. Writing a minimal reproduction case\n"
        
        solution = PredictiveSolution(
            solution_id=solution_id,
            solution_type=SolutionType.DEBUGGING_SUGGESTION,
            content=suggestion,
            confidence=signature.confidence,
            source_signature=signature.signature_id,
            context=context
        )
        solutions.append(solution)
        
        return solutions
    
    def _generate_syntax_help(self, signature: FrictionSignature) -> List[PredictiveSolution]:
        """Generate syntax help for syntax confusion"""
        context = signature.context
        
        solutions = []
        
        solution_id = hashlib.md5(
            f"syntax_{signature.signature_id}".encode()
        ).hexdigest()[:12]
        
        if 'language' in context:
            language = context['language']
            help_text = f"# Syntax assistance for {language}\n"
            help_text += f"# Consider using a linter or formatter\n"
            help_text += f"# Common syntax errors to check:\n"
            help_text += f"# - Matching brackets/quotes\n"
            help_text += f"# - Proper indentation\n"
            help_text += f"# - Correct statement termination"
            
            solution = PredictiveSolution(
                solution_id=solution_id,
                solution_type=SolutionType.API_USAGE_EXAMPLE,
                content=help_text,
                confidence=signature.confidence * 0.9,
                source_signature=signature.signature_id,
                context=context
            )
            solutions.append(solution)
        
        return solutions


class IntentDecoder:
    """
    Main intent decoder coordinating the symbiotic interface.
    
    Processes input streams, detects friction signatures, generates predictive
    solutions, and manages the predictive buffer for seamless user assistance.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.input_processor = InputStreamProcessor()
        self.friction_detector = FrictionSignatureDetector(confidence_threshold)
        self.solution_generator = PredictiveSolutionGenerator()
        self.predictive_buffer: List[PredictiveSolution] = []
        self.acceptance_history: Dict[str, bool] = {}  # solution_id -> accepted
        self.running = False
        self.lock = threading.Lock()
        
    def start(self) -> None:
        """Start the intent decoder processing loop"""
        self.running = True
        logger.info("Intent decoder started")
        
        def processing_loop():
            while self.running:
                try:
                    self._process_cycle()
                    time.sleep(0.1)  # 100ms processing cycle
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    time.sleep(1.0)
        
        thread = threading.Thread(target=processing_loop, daemon=True)
        thread.start()
    
    def stop(self) -> None:
        """Stop the intent decoder"""
        self.running = False
        logger.info("Intent decoder stopped")
    
    def add_input_signal(self, signal: InputSignal) -> None:
        """Add an input signal to the processing stream"""
        with self.lock:
            self.input_processor.add_signal(signal)
    
    def _process_cycle(self) -> None:
        """Process one cycle of intent decoding"""
        with self.lock:
            # Get recent signals
            recent_signals = self.input_processor.get_recent_signals()
            
            if not recent_signals:
                return
            
            # Detect friction signatures
            new_signatures = self.friction_detector.analyze_stream(recent_signals)
            
            # Check for critical signatures
            critical_signatures = self.friction_detector.get_critical_signatures()
            
            # Generate solutions for critical signatures
            for signature in critical_signatures:
                solutions = self.solution_generator.generate_solutions(signature)
                
                # Add to predictive buffer
                for solution in solutions:
                    if solution not in self.predictive_buffer:
                        self.predictive_buffer.append(solution)
                        logger.info(f"Added predictive solution to buffer: {solution.solution_type.value}")
    
    def get_predictive_buffer(self) -> List[PredictiveSolution]:
        """Get current predictive buffer contents"""
        with self.lock:
            return self.predictive_buffer.copy()
    
    def accept_solution(self, solution_id: str) -> bool:
        """Accept a predictive solution (user pressed Tab)"""
        with self.lock:
            for i, solution in enumerate(self.predictive_buffer):
                if solution.solution_id == solution_id:
                    # Record acceptance
                    self.acceptance_history[solution_id] = True
                    solution.acceptance_rate = min(1.0, solution.acceptance_rate + 0.1)
                    
                    # Remove from buffer
                    self.predictive_buffer.pop(i)
                    logger.info(f"Solution accepted: {solution_id}")
                    return True
            
            return False
    
    def reject_solution(self, solution_id: str) -> bool:
        """Reject a predictive solution (user ignored or dismissed)"""
        with self.lock:
            for i, solution in enumerate(self.predictive_buffer):
                if solution.solution_id == solution_id:
                    # Record rejection
                    self.acceptance_history[solution_id] = False
                    solution.acceptance_rate = max(0.0, solution.acceptance_rate - 0.1)
                    
                    # Remove from buffer
                    self.predictive_buffer.pop(i)
                    logger.info(f"Solution rejected: {solution_id}")
                    return True
            
            return False
    
    def clear_buffer(self) -> None:
        """Clear the predictive buffer"""
        with self.lock:
            self.predictive_buffer.clear()
            logger.info("Predictive buffer cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get intent decoder statistics"""
        with self.lock:
            total_acceptances = sum(1 for accepted in self.acceptance_history.values() if accepted)
            total_rejections = len(self.acceptance_history) - total_acceptances
            
            acceptance_rate = (
                total_acceptances / len(self.acceptance_history)
                if self.acceptance_history else 0.0
            )
            
            return {
                "buffer_size": len(self.predictive_buffer),
                "active_signatures": len(self.friction_detector.get_active_signatures()),
                "critical_signatures": len(self.friction_detector.get_critical_signatures()),
                "total_acceptances": total_acceptances,
                "total_rejections": total_rejections,
                "acceptance_rate": acceptance_rate,
                "input_statistics": self.input_processor.get_input_statistics()
            }


# Singleton instance
_intent_decoder_instance: Optional[IntentDecoder] = None
_decoder_lock = threading.Lock()

def get_intent_decoder(confidence_threshold: float = 0.7) -> IntentDecoder:
    """Get the singleton Intent Decoder instance"""
    global _intent_decoder_instance
    with _decoder_lock:
        if _intent_decoder_instance is None:
            _intent_decoder_instance = IntentDecoder(confidence_threshold)
            _intent_decoder_instance.start()
        return _intent_decoder_instance


# Convenience functions for common operations
def add_keystroke(key: str, timestamp: Optional[datetime] = None) -> None:
    """Add a keystroke signal"""
    decoder = get_intent_decoder()
    signal = InputSignal(
        signal_id=hashlib.md5(f"key_{key}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        input_type=InputType.KEYSTROKE,
        timestamp=timestamp or datetime.now(),
        data={"key": key}
    )
    decoder.add_input_signal(signal)


def add_mouse_movement(x: int, y: int, timestamp: Optional[datetime] = None) -> None:
    """Add a mouse movement signal"""
    decoder = get_intent_decoder()
    signal = InputSignal(
        signal_id=hashlib.md5(f"mouse_{x}_{y}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        input_type=InputType.MOUSE_MOVEMENT,
        timestamp=timestamp or datetime.now(),
        data={"x": x, "y": y}
    )
    decoder.add_input_signal(signal)


def add_editor_state(file: str, line: int, language: str, timestamp: Optional[datetime] = None) -> None:
    """Add an editor state signal"""
    decoder = get_intent_decoder()
    signal = InputSignal(
        signal_id=hashlib.md5(f"editor_{file}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        input_type=InputType.EDITOR_STATE,
        timestamp=timestamp or datetime.now(),
        data={"file": file, "line": line, "language": language}
    )
    decoder.add_input_signal(signal)


if __name__ == "__main__":
    # Test the Intent Decoder
    print("Testing Intent Decoder...")
    
    decoder = get_intent_decoder()
    
    # Simulate user input patterns
    print("Simulating user input patterns...")
    
    # Simulate repetitive editing (deleting and rewriting)
    for i in range(15):
        add_keystroke("backspace")
        time.sleep(0.05)
    
    # Add some editor context
    add_editor_state("main.py", 42, "python")
    
    # Wait for processing
    time.sleep(2)
    
    # Check predictive buffer
    buffer = decoder.get_predictive_buffer()
    print(f"\nPredictive Buffer Size: {len(buffer)}")
    
    for solution in buffer:
        print(f"Solution: {solution.solution_type.value}")
        print(f"Content: {solution.content}")
        print(f"Confidence: {solution.confidence:.2%}")
        print()
    
    # Get statistics
    stats = decoder.get_statistics()
    print(f"Statistics: {stats}")
    
    # Test solution acceptance
    if buffer:
        decoder.accept_solution(buffer[0].solution_id)
        print("Accepted first solution")
    
    # Stop decoder
    decoder.stop()
    
    print("\nIntent Decoder test completed successfully!")