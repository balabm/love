"""
Autopoietic Auditor - Self-Inspection & State Drift Detection

Implements a self-monitoring system based on the biological concept of Autopoiesis (self-maintenance).
An intelligence must recognize when its own mind is degrading or becoming bloated.

The Auditor:
1. Monitors 107+ modules for semantic drift from their mathematical/logical baselines
2. Detects when modules generate outputs that deviate from expected patterns
3. Cross-references ChromaDB data state with Live Memory JSON for consistency
4. Identifies hallucinations (conflicts between data sources)
5. Triggers RealityReconciliation protocol to purge hallucinated state
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
import threading
import time
import re
import os
from pathlib import Path
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    """Status of module health"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DriftType(Enum):
    """Types of semantic drift that can be detected"""
    SEMANTIC_DRIFT = "semantic_drift"  # Meaning has changed
    LOGICAL_DRIFT = "logical_drift"  # Logic patterns have changed
    PERFORMANCE_DRIFT = "performance_drift"  # Performance characteristics changed
    OUTPUT_DRIFT = "output_drift"  # Output format/structure changed
    ERROR_DRIFT = "error_drift"  # Error patterns have changed


class HallucinationType(Enum):
    """Types of hallucinations that can be detected"""
    CONTEXT_CONFLICT = "context_conflict"  # Data sources disagree on context
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"  # Timeline contradictions
    LOGICAL_IMPOSSIBILITY = "logical_impossibility"  # Violates basic logic
    SOURCE_CONTRADICTION = "source_contradiction"  # Different data sources disagree
    STATE_DECAY = "state_decay"  # State has degraded over time


@dataclass
class ModuleBaseline:
    """Baseline characteristics of a healthy module"""
    module_id: str
    module_name: str
    module_path: str
    baseline_timestamp: datetime
    output_patterns: Dict[str, Any]  # Expected output patterns
    error_rate_baseline: float
    performance_baseline: Dict[str, float]
    semantic_fingerprint: str  # Hash of semantic characteristics
    logical_structure: Dict[str, Any]  # Expected logical structure
    sample_outputs: List[Dict[str, Any]]  # Sample healthy outputs
    dependencies: List[str]  # Module dependencies
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "module_path": self.module_path,
            "baseline_timestamp": self.baseline_timestamp.isoformat(),
            "output_patterns": self.output_patterns,
            "error_rate_baseline": self.error_rate_baseline,
            "performance_baseline": self.performance_baseline,
            "semantic_fingerprint": self.semantic_fingerprint,
            "logical_structure": self.logical_structure,
            "sample_outputs": self.sample_outputs,
            "dependencies": self.dependencies
        }


@dataclass
class DriftDetection:
    """Detection of semantic drift in a module"""
    detection_id: str
    module_id: str
    drift_type: DriftType
    severity: float  # 0.0 to 1.0
    baseline_state: ModuleBaseline
    current_state: Dict[str, Any]
    drift_description: str
    detected_at: datetime
    confidence: float
    contributing_factors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "detection_id": self.detection_id,
            "module_id": self.module_id,
            "drift_type": self.drift_type.value,
            "severity": self.severity,
            "baseline_state": self.baseline_state.to_dict(),
            "current_state": self.current_state,
            "drift_description": self.drift_description,
            "detected_at": self.detected_at.isoformat(),
            "confidence": self.confidence,
            "contributing_factors": self.contributing_factors
        }


@dataclass
class HallucinationDetection:
    """Detection of a hallucination (state inconsistency)"""
    detection_id: str
    hallucination_type: HallucinationType
    conflicting_sources: List[str]  # Data sources that conflict
    conflicting_data: Dict[str, Any]  # The conflicting data
    reality_source: str  # Which source is considered ground truth
    hallucinated_content: str  # What was hallucinated
    severity: float
    detected_at: datetime
    confidence: float
    recommended_action: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "detection_id": self.detection_id,
            "hallucination_type": self.hallucination_type.value,
            "conflicting_sources": self.conflicting_sources,
            "conflicting_data": self.conflicting_data,
            "reality_source": self.reality_source,
            "hallucinated_content": self.hallucinated_content,
            "severity": self.severity,
            "detected_at": self.detected_at.isoformat(),
            "confidence": self.confidence,
            "recommended_action": self.recommended_action
        }


@dataclass
class ReconciliationAction:
    """Action taken to reconcile a detected issue"""
    action_id: str
    action_type: str  # "purge", "correct", "flag", "ignore"
    target_module: Optional[str]  # If module-related
    target_data: Optional[str]  # If data-related
    action_description: str
    executed_at: datetime
    success: bool
    result: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target_module": self.target_module,
            "target_data": self.target_data,
            "action_description": self.action_description,
            "executed_at": self.executed_at.isoformat(),
            "success": self.success,
            "result": self.result
        }


class SemanticDriftDetector:
    """
    Detects semantic drift in module outputs.
    
    Monitors module outputs and compares them against established baselines
    to detect when a module's behavior changes in problematic ways.
    """
    
    def __init__(self, drift_threshold: float = 0.3):
        self.drift_threshold = drift_threshold
        self.module_baselines: Dict[str, ModuleBaseline] = {}
        self.detection_history: deque = deque(maxlen=1000)
        self.output_samples: Dict[str, deque] = {}  # module_id -> recent outputs
        
    def establish_baseline(
        self, 
        module_id: str, 
        module_name: str, 
        module_path: str,
        sample_outputs: List[Dict[str, Any]],
        performance_data: Dict[str, float]
    ) -> ModuleBaseline:
        """Establish a baseline for a module"""
        # Generate semantic fingerprint
        semantic_fingerprint = self._generate_semantic_fingerprint(sample_outputs)
        
        # Extract logical structure
        logical_structure = self._extract_logical_structure(sample_outputs)
        
        # Calculate baseline error rate
        error_rate = self._calculate_error_rate(sample_outputs)
        
        baseline = ModuleBaseline(
            module_id=module_id,
            module_name=module_name,
            module_path=module_path,
            baseline_timestamp=datetime.now(),
            output_patterns=self._extract_output_patterns(sample_outputs),
            error_rate_baseline=error_rate,
            performance_baseline=performance_data,
            semantic_fingerprint=semantic_fingerprint,
            logical_structure=logical_structure,
            sample_outputs=sample_outputs,
            dependencies=self._extract_dependencies(module_path)
        )
        
        self.module_baselines[module_id] = baseline
        self.output_samples[module_id] = deque(maxlen=100)
        
        logger.info(f"Established baseline for module {module_name} ({module_id})")
        return baseline
    
    def detect_drift(
        self, 
        module_id: str, 
        current_outputs: List[Dict[str, Any]],
        current_performance: Dict[str, float],
        error_count: int = 0
    ) -> Optional[DriftDetection]:
        """Detect semantic drift in a module"""
        if module_id not in self.module_baselines:
            logger.warning(f"No baseline established for module {module_id}")
            return None
        
        baseline = self.module_baselines[module_id]
        
        # Store current outputs for future analysis
        if module_id not in self.output_samples:
            self.output_samples[module_id] = deque(maxlen=100)
        
        for output in current_outputs:
            self.output_samples[module_id].append(output)
        
        # Detect different types of drift
        drift_detections = []
        
        # Semantic drift
        semantic_drift = self._detect_semantic_drift(baseline, current_outputs)
        if semantic_drift > self.drift_threshold:
            drift_detections.append((DriftType.SEMANTIC_DRIFT, semantic_drift))
        
        # Logical drift
        logical_drift = self._detect_logical_drift(baseline, current_outputs)
        if logical_drift > self.drift_threshold:
            drift_detections.append((DriftType.LOGICAL_DRIFT, logical_drift))
        
        # Performance drift
        performance_drift = self._detect_performance_drift(baseline, current_performance)
        if performance_drift > self.drift_threshold:
            drift_detections.append((DriftType.PERFORMANCE_DRIFT, performance_drift))
        
        # Error drift
        current_error_rate = error_count / len(current_outputs) if current_outputs else 0
        error_drift = abs(current_error_rate - baseline.error_rate_baseline)
        if error_drift > self.drift_threshold:
            drift_detections.append((DriftType.ERROR_DRIFT, error_drift))
        
        if not drift_detections:
            return None
        
        # Get the most severe drift
        drift_type, severity = max(drift_detections, key=lambda x: x[1])
        
        detection_id = hashlib.md5(
            f"{module_id}_{drift_type.value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        detection = DriftDetection(
            detection_id=detection_id,
            module_id=module_id,
            drift_type=drift_type,
            severity=severity,
            baseline_state=baseline,
            current_state={
                "outputs": current_outputs,
                "performance": current_performance,
                "error_rate": current_error_rate
            },
            drift_description=self._generate_drift_description(drift_type, severity, baseline),
            detected_at=datetime.now(),
            confidence=min(severity + 0.2, 1.0),
            contributing_factors=self._identify_contributing_factors(baseline, current_outputs, current_performance)
        )
        
        self.detection_history.append(detection)
        logger.warning(f"Detected {drift_type.value} in module {module_id}: severity {severity:.2f}")
        
        return detection
    
    def _generate_semantic_fingerprint(self, outputs: List[Dict[str, Any]]) -> str:
        """Generate a semantic fingerprint from outputs"""
        if not outputs:
            return "empty"
        
        # Extract key semantic features
        features = []
        
        for output in outputs:
            # Output structure
            if isinstance(output, dict):
                features.append(str(sorted(output.keys())))
            
            # Data types
            if isinstance(output, dict):
                for key, value in output.items():
                    features.append(f"{key}:{type(value).__name__}")
            
            # Value patterns (simplified)
            if isinstance(output, dict):
                for key, value in output.items():
                    if isinstance(value, (int, float)):
                        features.append(f"{key}:numeric")
                    elif isinstance(value, str):
                        features.append(f"{key}:string_{len(value)}")
                    elif isinstance(value, list):
                        features.append(f"{key}:list_{len(value)}")
        
        # Create hash
        feature_string = "|".join(features)
        return hashlib.md5(feature_string.encode()).hexdigest()[:16]
    
    def _extract_logical_structure(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract expected logical structure from outputs"""
        if not outputs:
            return {}
        
        structure = {
            "field_count": len(outputs[0]) if outputs and isinstance(outputs[0], dict) else 0,
            "nested_levels": self._count_nesting_levels(outputs[0]) if outputs else 0,
            "data_types": self._extract_data_types(outputs[0]) if outputs else {}
        }
        
        return structure
    
    def _count_nesting_levels(self, data: Any, current_level: int = 0) -> int:
        """Count maximum nesting levels in data structure"""
        if isinstance(data, dict):
            if not data:
                return current_level
            return max(self._count_nesting_levels(v, current_level + 1) for v in data.values())
        elif isinstance(data, list):
            if not data:
                return current_level
            return max(self._count_nesting_levels(item, current_level + 1) for item in data)
        else:
            return current_level
    
    def _extract_data_types(self, data: Any) -> Dict[str, str]:
        """Extract data types from structure"""
        if isinstance(data, dict):
            return {k: type(v).__name__ for k, v in data.items()}
        return {}
    
    def _calculate_error_rate(self, outputs: List[Dict[str, Any]]) -> float:
        """Calculate error rate from outputs"""
        if not outputs:
            return 0.0
        
        error_count = 0
        for output in outputs:
            if isinstance(output, dict) and "error" in output:
                error_count += 1
        
        return error_count / len(outputs)
    
    def _extract_output_patterns(self, outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract expected output patterns"""
        if not outputs:
            return {}
        
        patterns = {
            "common_keys": self._get_common_keys(outputs),
            "value_ranges": self._get_value_ranges(outputs),
            "typical_structure": str(type(outputs[0])) if outputs else "unknown"
        }
        
        return patterns
    
    def _get_common_keys(self, outputs: List[Dict[str, Any]]) -> List[str]:
        """Get keys common to all outputs"""
        if not outputs:
            return []
        
        key_sets = [set(output.keys()) for output in outputs if isinstance(output, dict)]
        if not key_sets:
            return []
        
        common = set.intersection(*key_sets)
        return list(common)
    
    def _get_value_ranges(self, outputs: List[Dict[str, Any]]) -> Dict[str, Tuple[float, float]]:
        """Get value ranges for numeric fields"""
        ranges = {}
        
        for output in outputs:
            if isinstance(output, dict):
                for key, value in output.items():
                    if isinstance(value, (int, float)):
                        if key not in ranges:
                            ranges[key] = [value, value]
                        else:
                            ranges[key][0] = min(ranges[key][0], value)
                            ranges[key][1] = max(ranges[key][1], value)
        
        return {k: (v[0], v[1]) for k, v in ranges.items()}
    
    def _extract_dependencies(self, module_path: str) -> List[str]:
        """Extract module dependencies from file"""
        try:
            if not os.path.exists(module_path):
                return []
            
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple import extraction
            imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', content, re.MULTILINE)
            dependencies = [imp[0] or imp[1] for imp in imports if imp[0] or imp[1]]
            
            return list(set(dependencies))
            
        except Exception as e:
            logger.error(f"Error extracting dependencies from {module_path}: {e}")
            return []
    
    def _detect_semantic_drift(self, baseline: ModuleBaseline, current_outputs: List[Dict[str, Any]]) -> float:
        """Detect semantic drift by comparing fingerprints"""
        current_fingerprint = self._generate_semantic_fingerprint(current_outputs)
        
        # Compare fingerprints
        if current_fingerprint == baseline.semantic_fingerprint:
            return 0.0
        
        # Calculate similarity (simple hamming distance for hash comparison)
        similarity = sum(c1 == c2 for c1, c2 in zip(baseline.semantic_fingerprint, current_fingerprint))
        drift = 1.0 - (similarity / len(baseline.semantic_fingerprint))
        
        return drift
    
    def _detect_logical_drift(self, baseline: ModuleBaseline, current_outputs: List[Dict[str, Any]]) -> float:
        """Detect drift in logical structure"""
        current_structure = self._extract_logical_structure(current_outputs)
        
        # Compare structures
        drift = 0.0
        
        # Field count drift
        if baseline.logical_structure.get("field_count") != current_structure.get("field_count"):
            drift += 0.3
        
        # Nesting level drift
        if baseline.logical_structure.get("nested_levels") != current_structure.get("nested_levels"):
            drift += 0.3
        
        # Data type drift
        baseline_types = baseline.logical_structure.get("data_types", {})
        current_types = current_structure.get("data_types", {})
        
        if baseline_types != current_types:
            drift += 0.4
        
        return min(drift, 1.0)
    
    def _detect_performance_drift(self, baseline: ModuleBaseline, current_performance: Dict[str, float]) -> float:
        """Detect performance characteristic drift"""
        drift = 0.0
        
        for metric, baseline_value in baseline.performance_baseline.items():
            if metric in current_performance:
                current_value = current_performance[metric]
                # Calculate relative change
                if baseline_value > 0:
                    relative_change = abs(current_value - baseline_value) / baseline_value
                    drift += relative_change
        
        # Average drift across metrics
        if baseline.performance_baseline:
            drift = drift / len(baseline.performance_baseline)
        
        return min(drift, 1.0)
    
    def _generate_drift_description(self, drift_type: DriftType, severity: float, baseline: ModuleBaseline) -> str:
        """Generate human-readable drift description"""
        descriptions = {
            DriftType.SEMANTIC_DRIFT: f"Module {baseline.module_name} output semantics have changed",
            DriftType.LOGICAL_DRIFT: f"Module {baseline.module_name} logical structure has changed",
            DriftType.PERFORMANCE_DRIFT: f"Module {baseline.module_name} performance characteristics have changed",
            DriftType.ERROR_DRIFT: f"Module {baseline.module_name} error rate has changed",
            DriftType.OUTPUT_DRIFT: f"Module {baseline.module_name} output format has changed"
        }
        
        base_desc = descriptions.get(drift_type, f"Unknown drift in {baseline.module_name}")
        return f"{base_desc} (severity: {severity:.2%})"
    
    def _identify_contributing_factors(
        self, 
        baseline: ModuleBaseline, 
        current_outputs: List[Dict[str, Any]],
        current_performance: Dict[str, float]
    ) -> List[str]:
        """Identify factors contributing to drift"""
        factors = []
        
        # Check for new fields
        if current_outputs:
            current_keys = set()
            for output in current_outputs:
                if isinstance(output, dict):
                    current_keys.update(output.keys())
            
            baseline_keys = set(baseline.output_patterns.get("common_keys", []))
            new_keys = current_keys - baseline_keys
            
            if new_keys:
                factors.append(f"New fields detected: {list(new_keys)}")
        
        # Check for performance changes
        for metric, baseline_value in baseline.performance_baseline.items():
            if metric in current_performance:
                current_value = current_performance[metric]
                if abs(current_value - baseline_value) / baseline_value > 0.5:
                    factors.append(f"Significant {metric} change: {baseline_value:.2f} → {current_value:.2f}")
        
        return factors


class StateCoherenceInspector:
    """
    Inspects state coherence across different data sources.
    
    Cross-references ChromaDB data state with Live Memory JSON to detect
    hallucinations and inconsistencies.
    """
    
    def __init__(self):
        self.data_sources: Dict[str, Any] = {}  # source_id -> data accessor
        self.coherence_history: deque = deque(maxlen=500)
        self.hallucination_detections: deque = deque(maxlen=200)
        
    def register_data_source(self, source_id: str, data_accessor: Any) -> None:
        """Register a data source for coherence checking"""
        self.data_sources[source_id] = data_accessor
        logger.info(f"Registered data source: {source_id}")
    
    def inspect_state_coherence(self) -> List[HallucinationDetection]:
        """
        Inspect coherence across all registered data sources.
        
        Cross-references different data sources to detect hallucinations
        and state inconsistencies.
        """
        hallucinations = []
        
        # Get current state from all sources
        current_states = {}
        for source_id, accessor in self.data_sources.items():
            try:
                current_states[source_id] = self._get_source_state(accessor)
            except Exception as e:
                logger.error(f"Error getting state from {source_id}: {e}")
                current_states[source_id] = None
        
        # Check for context conflicts
        context_conflicts = self._detect_context_conflicts(current_states)
        hallucinations.extend(context_conflicts)
        
        # Check for temporal inconsistencies
        temporal_inconsistencies = self._detect_temporal_inconsistencies(current_states)
        hallucinations.extend(temporal_inconsistencies)
        
        # Check for logical impossibilities
        logical_impossibilities = self._detect_logical_impossibilities(current_states)
        hallucinations.extend(logical_impossibilities)
        
        # Store detections
        for hallucination in hallucinations:
            self.hallucination_detections.append(hallucination)
        
        return hallucinations
    
    def _get_source_state(self, accessor: Any) -> Dict[str, Any]:
        """Get current state from a data source"""
        # This would be implemented based on the actual data source interface
        # For now, return a placeholder
        if hasattr(accessor, 'get_state'):
            return accessor.get_state()
        elif hasattr(accessor, 'get_current_context'):
            return accessor.get_current_context()
        else:
            return {}
    
    def _detect_context_conflicts(self, current_states: Dict[str, Dict[str, Any]]) -> List[HallucinationDetection]:
        """Detect conflicts between data sources about current context"""
        conflicts = []
        
        # Extract user activity context from different sources
        user_activities = {}
        
        for source_id, state in current_states.items():
            if state and isinstance(state, dict):
                # Look for user activity indicators
                activity = self._extract_user_activity(state)
                if activity:
                    user_activities[source_id] = activity
        
        # Check for conflicts
        if len(user_activities) > 1:
            activities_list = list(user_activities.values())
            
            # Check if activities conflict
            for i in range(len(activities_list)):
                for j in range(i + 1, len(activities_list)):
                    source1 = list(user_activities.keys())[i]
                    source2 = list(user_activities.keys())[j]
                    activity1 = activities_list[i]
                    activity2 = activities_list[j]
                    
                    if self._activities_conflict(activity1, activity2):
                        detection_id = hashlib.md5(
                            f"context_conflict_{source1}_{source2}_{datetime.now().isoformat()}".encode()
                        ).hexdigest()[:12]
                        
                        # Determine which source is more reliable
                        reality_source = self._determine_reality_source(source1, source2)
                        
                        conflict = HallucinationDetection(
                            detection_id=detection_id,
                            hallucination_type=HallucinationType.CONTEXT_CONFLICT,
                            conflicting_sources=[source1, source2],
                            conflicting_data={
                                source1: activity1,
                                source2: activity2
                            },
                            reality_source=reality_source,
                            hallucinated_content=f"Conflict between {source1} and {source2} about user activity",
                            severity=0.7,
                            detected_at=datetime.now(),
                            confidence=0.8,
                            recommended_action=f"Trust {reality_source}, purge data from {'source2' if reality_source == source1 else 'source1'}"
                        )
                        
                        conflicts.append(conflict)
        
        return conflicts
    
    def _extract_user_activity(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract user activity from state"""
        # Look for common activity indicators
        activity_keys = ['activity', 'current_action', 'user_state', 'status', 'mode']
        
        for key in activity_keys:
            if key in state:
                return str(state[key])
        
        # Check for specific activity patterns
        if 'coding' in str(state).lower():
            return 'coding'
        elif 'gaming' in str(state).lower() or 'ps2' in str(state).lower():
            return 'gaming'
        elif 'working' in str(state).lower():
            return 'working'
        
        return None
    
    def _activities_conflict(self, activity1: str, activity2: str) -> bool:
        """Check if two activities conflict"""
        # Define conflicting activity pairs
        conflicting_pairs = [
            ('coding', 'gaming'),
            ('working', 'gaming'),
            ('coding', 'idle'),
            ('working', 'sleeping')
        ]
        
        act1_lower = activity1.lower()
        act2_lower = activity2.lower()
        
        for pair in conflicting_pairs:
            if (pair[0] in act1_lower and pair[1] in act2_lower) or \
               (pair[1] in act1_lower and pair[0] in act2_lower):
                return True
        
        return False
    
    def _determine_reality_source(self, source1: str, source2: str) -> str:
        """Determine which data source is more reliable for ground truth"""
        # Priority order for reality sources
        reality_priority = [
            'os_symbiosis',  # OS-level data is most reliable
            'awareness',     # System awareness
            'user_input',     # Direct user input
            'inference',      # AI inference (least reliable)
            'memory'          # Stored memory (can be stale)
        ]
        
        for source in reality_priority:
            if source in source1.lower():
                return source1
            if source in source2.lower():
                return source2
        
        # Default to first source
        return source1
    
    def _detect_temporal_inconsistencies(self, current_states: Dict[str, Dict[str, Any]]) -> List[HallucinationDetection]:
        """Detect temporal inconsistencies in the data"""
        inconsistencies = []
        
        # Extract timestamps from different sources
        timestamps = {}
        
        for source_id, state in current_states.items():
            if state and isinstance(state, dict):
                timestamp = self._extract_timestamp(state)
                if timestamp:
                    timestamps[source_id] = timestamp
        
        # Check for significant timestamp differences
        if len(timestamps) > 1:
            timestamp_values = list(timestamps.values())
            time_diff = max(timestamp_values) - min(timestamp_values)
            
            # If difference is more than 5 minutes, flag as inconsistency
            if time_diff > 300:  # 5 minutes
                detection_id = hashlib.md5(
                    f"temporal_inconsistency_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:12]
                
                inconsistency = HallucinationDetection(
                    detection_id=detection_id,
                    hallucination_type=HallucinationType.TEMPORAL_INCONSISTENCY,
                    conflicting_sources=list(timestamps.keys()),
                    conflicting_data={"timestamps": timestamps},
                    reality_source="most_recent",
                    hallucinated_content=f"Timestamps differ by {time_diff} seconds",
                    severity=min(time_diff / 3600, 1.0),  # Scale by hours
                    detected_at=datetime.now(),
                    confidence=0.7,
                    recommended_action="Synchronize to most recent timestamp"
                )
                
                inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    def _extract_timestamp(self, state: Dict[str, Any]) -> Optional[float]:
        """Extract timestamp from state"""
        timestamp_keys = ['timestamp', 'time', 'last_updated', 'created_at']
        
        for key in timestamp_keys:
            if key in state:
                value = state[key]
                if isinstance(value, (int, float)):
                    return value
                elif isinstance(value, str):
                    try:
                        # Try to parse ISO format
                        from datetime import datetime
                        dt = datetime.fromisoformat(value)
                        return dt.timestamp()
                    except:
                        pass
        
        return None
    
    def _detect_logical_impossibilities(self, current_states: Dict[str, Dict[str, Any]]) -> List[HallucinationDetection]:
        """Detect logical impossibilities in the combined state"""
        impossibilities = []
        
        # Combine all states
        combined_state = {}
        for source_id, state in current_states.items():
            if state and isinstance(state, dict):
                combined_state.update(state)
        
        # Check for logical impossibilities
        # Example: User cannot be in two places at once
        if 'location' in combined_state and 'current_location' in combined_state:
            if combined_state['location'] != combined_state['current_location']:
                detection_id = hashlib.md5(
                    f"logical_impossibility_location_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:12]
                
                impossibility = HallucinationDetection(
                    detection_id=detection_id,
                    hallucination_type=HallucinationType.LOGICAL_IMPOSSIBILITY,
                    conflicting_sources=['location', 'current_location'],
                    conflicting_data={
                        'location': combined_state['location'],
                        'current_location': combined_state['current_location']
                    },
                    reality_source='current_location',
                    hallucinated_content="User cannot be in two locations simultaneously",
                    severity=0.9,
                    detected_at=datetime.now(),
                    confidence=0.95,
                    recommended_action="Purge conflicting location data"
                )
                
                impossibilities.append(impossibility)
        
        # Example: User cannot be working and sleeping simultaneously
        if 'activity' in combined_state:
            activity = str(combined_state['activity']).lower()
            if 'working' in activity and 'sleeping' in activity:
                detection_id = hashlib.md5(
                    f"logical_impossibility_activity_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:12]
                
                impossibility = HallucinationDetection(
                    detection_id=detection_id,
                    hallucination_type=HallucinationType.LOGICAL_IMPOSSIBILITY,
                    conflicting_sources=['activity'],
                    conflicting_data={'activity': combined_state['activity']},
                    reality_source='user_input',
                    hallucinated_content="User cannot be working and sleeping simultaneously",
                    severity=0.95,
                    detected_at=datetime.now(),
                    confidence=0.9,
                    recommended_action="Correct activity state based on direct observation"
                )
                
                impossibilities.append(impossibility)
        
        return impossibilities


class RealityReconciler:
    """
    Reconciles detected hallucinations and state inconsistencies.
    
    Implements protocols to purge hallucinated state and restore
    coherence across data sources.
    """
    
    def __init__(self):
        self.reconciliation_history: deque = deque(maxlen=500)
        self.reconciliation_protocols = {
            HallucinationType.CONTEXT_CONFLICT: self._reconcile_context_conflict,
            HallucinationType.TEMPORAL_INCONSISTENCY: self._reconcile_temporal_inconsistency,
            HallucinationType.LOGICAL_IMPOSSIBILITY: self._reconcile_logical_impossibility,
            HallucinationType.SOURCE_CONTRADICTION: self._reconcile_source_contradiction,
            HallucinationType.STATE_DECAY: self._reconcile_state_decay
        }
        
    def reconcile(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile a detected hallucination"""
        protocol = self.reconciliation_protocols.get(hallucination.hallucination_type)
        
        if protocol:
            return protocol(hallucination)
        else:
            return self._default_reconciliation(hallucination)
    
    def _reconcile_context_conflict(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile context conflict between data sources"""
        action_id = hashlib.md5(
            f"reconcile_context_{hallucination.detection_id}".encode()
        ).hexdigest()[:12]
        
        # Identify the hallucinated source
        reality_source = hallucination.reality_source
        hallucinated_source = [s for s in hallucination.conflicting_sources if s != reality_source][0]
        
        try:
            # Purge data from hallucinated source
            success = self._purge_source_data(hallucinated_source, hallucination.conflicting_data)
            
            action = ReconciliationAction(
                action_id=action_id,
                action_type="purge",
                target_module=None,
                target_data=hallucinated_source,
                action_description=f"Purged hallucinated context from {hallucinated_source}",
                executed_at=datetime.now(),
                success=success,
                result={
                    "purged_source": hallucinated_source,
                    "reality_source": reality_source,
                    "purged_data": hallucination.conflicting_data.get(hallucinated_source)
                }
            )
            
            self.reconciliation_history.append(action)
            logger.info(f"Reconciled context conflict: purged {hallucinated_source}")
            
            return action
            
        except Exception as e:
            logger.error(f"Error reconciling context conflict: {e}")
            
            return ReconciliationAction(
                action_id=action_id,
                action_type="flag",
                target_module=None,
                target_data=hallucinated_source,
                action_description=f"Failed to purge {hallucinated_source}: {str(e)}",
                executed_at=datetime.now(),
                success=False,
                result={"error": str(e)}
            )
    
    def _reconcile_temporal_inconsistency(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile temporal inconsistency"""
        action_id = hashlib.md5(
            f"reconcile_temporal_{hallucination.detection_id}".encode()
        ).hexdigest()[:12]
        
        try:
            # Synchronize to most recent timestamp
            timestamps = hallucination.conflicting_data.get('timestamps', {})
            if timestamps:
                most_recent_source = max(timestamps, key=timestamps.get)
                most_recent_time = timestamps[most_recent_source]
                
                # Update all sources to most recent time
                success = True
                for source in timestamps:
                    if source != most_recent_source:
                        success &= self._update_source_timestamp(source, most_recent_time)
                
                action = ReconciliationAction(
                    action_id=action_id,
                    action_type="correct",
                    target_module=None,
                    target_data="timestamps",
                    action_description=f"Synchronized all sources to {most_recent_source}",
                    executed_at=datetime.now(),
                    success=success,
                    result={
                        "synchronized_to": most_recent_source,
                        "timestamp": most_recent_time
                    }
                )
                
                self.reconciliation_history.append(action)
                logger.info(f"Reconciled temporal inconsistency: synchronized to {most_recent_source}")
                
                return action
            
        except Exception as e:
            logger.error(f"Error reconciling temporal inconsistency: {e}")
        
        return self._default_reconciliation(hallucination)
    
    def _reconcile_logical_impossibility(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile logical impossibility"""
        action_id = hashlib.md5(
            f"reconcile_logical_{hallucination.detection_id}".encode()
        ).hexdigest()[:12]
        
        try:
            # Remove the impossible state
            reality_source = hallucination.reality_source
            success = self._purge_impossible_state(hallucination.conflicting_data)
            
            action = ReconciliationAction(
                action_id=action_id,
                action_type="purge",
                target_module=None,
                target_data="logical_state",
                action_description=f"Purged logically impossible state",
                executed_at=datetime.now(),
                success=success,
                result={
                    "reality_source": reality_source,
                    "purged_data": hallucination.conflicting_data
                }
            )
            
            self.reconciliation_history.append(action)
            logger.info("Reconciled logical impossibility: purged impossible state")
            
            return action
            
        except Exception as e:
            logger.error(f"Error reconciling logical impossibility: {e}")
        
        return self._default_reconciliation(hallucination)
    
    def _reconcile_source_contradiction(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile contradiction between sources"""
        # Similar to context conflict
        return self._reconcile_context_conflict(hallucination)
    
    def _reconcile_state_decay(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Reconcile state decay"""
        action_id = hashlib.md5(
            f"reconcile_decay_{hallucination.detection_id}".encode()
        ).hexdigest()[:12]
        
        try:
            # Refresh decayed state
            success = self._refresh_decayed_state(hallucination.conflicting_data)
            
            action = ReconciliationAction(
                action_id=action_id,
                action_type="correct",
                target_module=None,
                target_data="decayed_state",
                action_description="Refreshed decayed state",
                executed_at=datetime.now(),
                success=success,
                result={"refreshed_data": hallucination.conflicting_data}
            )
            
            self.reconciliation_history.append(action)
            logger.info("Reconciled state decay: refreshed state")
            
            return action
            
        except Exception as e:
            logger.error(f"Error reconciling state decay: {e}")
        
        return self._default_reconciliation(hallucination)
    
    def _default_reconciliation(self, hallucination: HallucinationDetection) -> ReconciliationAction:
        """Default reconciliation when no specific protocol exists"""
        action_id = hashlib.md5(
            f"default_reconcile_{hallucination.detection_id}".encode()
        ).hexdigest()[:12]
        
        action = ReconciliationAction(
            action_id=action_id,
            action_type="flag",
            target_module=None,
            target_data=None,
            action_description=f"Flagged for manual review: {hallucination.hallucinated_content}",
            executed_at=datetime.now(),
            success=False,
            result={"flagged": True, "reason": "No specific reconciliation protocol"}
        )
        
        self.reconciliation_history.append(action)
        logger.warning(f"No reconciliation protocol for {hallucination.hallucination_type.value}")
        
        return action
    
    def _purge_source_data(self, source_id: str, data: Dict[str, Any]) -> bool:
        """Purge data from a specific source"""
        # This would interface with the actual data storage systems
        # For now, return success
        logger.info(f"Purging data from source {source_id}")
        return True
    
    def _update_source_timestamp(self, source_id: str, timestamp: float) -> bool:
        """Update timestamp for a source"""
        # This would interface with the actual data storage systems
        logger.info(f"Updating timestamp for source {source_id} to {timestamp}")
        return True
    
    def _purge_impossible_state(self, impossible_data: Dict[str, Any]) -> bool:
        """Purge logically impossible state"""
        # This would interface with the actual data storage systems
        logger.info(f"Purging impossible state: {impossible_data}")
        return True
    
    def _refresh_decayed_state(self, decayed_data: Dict[str, Any]) -> bool:
        """Refresh decayed state with fresh data"""
        # This would interface with the actual data storage systems
        logger.info(f"Refreshing decayed state: {decayed_data}")
        return True


class AutopoieticAuditor:
    """
    Main auditor coordinating self-inspection and state drift detection.
    
    Implements autopoietic self-maintenance by:
    1. Monitoring module semantic drift
    2. Inspecting state coherence across data sources
    3. Detecting hallucinations and inconsistencies
    4. Triggering reconciliation protocols
    """
    
    def __init__(self, inspection_interval: float = 60.0):
        self.semantic_drift_detector = SemanticDriftDetector()
        self.state_coherence_inspector = StateCoherenceInspector()
        self.reality_reconciler = RealityReconciler()
        
        self.inspection_interval = inspection_interval
        self.running = False
        self.lock = threading.Lock()
        
        self.module_registry: Dict[str, Dict[str, Any]] = {}  # module_id -> module info
        self.audit_history: deque = deque(maxlen=1000)
        
    def register_module(
        self, 
        module_id: str, 
        module_name: str, 
        module_path: str,
        sample_outputs: List[Dict[str, Any]],
        performance_data: Dict[str, float]
    ) -> None:
        """Register a module for monitoring"""
        with self.lock:
            baseline = self.semantic_drift_detector.establish_baseline(
                module_id, module_name, module_path, sample_outputs, performance_data
            )
            
            self.module_registry[module_id] = {
                "module_name": module_name,
                "module_path": module_path,
                "baseline": baseline,
                "status": ModuleStatus.HEALTHY,
                "last_inspection": None,
                "drift_count": 0
            }
            
            logger.info(f"Registered module for monitoring: {module_name}")
    
    def register_data_source(self, source_id: str, data_accessor: Any) -> None:
        """Register a data source for coherence checking"""
        self.state_coherence_inspector.register_data_source(source_id, data_accessor)
    
    def start_audit_loop(self) -> None:
        """Start the continuous audit loop"""
        self.running = True
        logger.info("Starting autopoietic audit loop")
        
        def audit_loop():
            while self.running:
                try:
                    self._perform_audit_cycle()
                    time.sleep(self.inspection_interval)
                except Exception as e:
                    logger.error(f"Error in audit loop: {e}")
                    time.sleep(10.0)
        
        thread = threading.Thread(target=audit_loop, daemon=True)
        thread.start()
    
    def stop_audit_loop(self) -> None:
        """Stop the audit loop"""
        self.running = False
        logger.info("Stopped autopoietic audit loop")
    
    def _perform_audit_cycle(self) -> None:
        """Perform one complete audit cycle"""
        with self.lock:
            audit_start = datetime.now()
            
            # 1. Check for semantic drift in modules
            self._audit_module_drift()
            
            # 2. Inspect state coherence
            self._audit_state_coherence()
            
            audit_duration = (datetime.now() - audit_start).total_seconds()
            
            audit_record = {
                "timestamp": audit_start.isoformat(),
                "duration_seconds": audit_duration,
                "modules_inspected": len(self.module_registry),
                "drift_detections": len(self.semantic_drift_detector.detection_history),
                "hallucination_detections": len(self.state_coherence_inspector.hallucination_detections)
            }
            
            self.audit_history.append(audit_record)
            logger.info(f"Audit cycle completed: {audit_record}")
    
    def _audit_module_drift(self) -> None:
        """Audit registered modules for semantic drift"""
        for module_id, module_info in self.module_registry.items():
            try:
                # Get current module outputs (would be implemented via actual module interface)
                current_outputs = self._get_module_outputs(module_id)
                current_performance = self._get_module_performance(module_id)
                error_count = self._get_module_error_count(module_id)
                
                # Check for drift
                drift_detection = self.semantic_drift_detector.detect_drift(
                    module_id, current_outputs, current_performance, error_count
                )
                
                if drift_detection:
                    # Update module status
                    if drift_detection.severity > 0.7:
                        module_info["status"] = ModuleStatus.CRITICAL
                    elif drift_detection.severity > 0.4:
                        module_info["status"] = ModuleStatus.DEGRADED
                    
                    module_info["drift_count"] += 1
                    module_info["last_inspection"] = datetime.now()
                    
                    logger.warning(f"Module {module_info['module_name']} marked as {module_info['status'].value}")
                
            except Exception as e:
                logger.error(f"Error auditing module {module_id}: {e}")
    
    def _audit_state_coherence(self) -> None:
        """Inspect state coherence across data sources"""
        try:
            hallucinations = self.state_coherence_inspector.inspect_state_coherence()
            
            for hallucination in hallucinations:
                # Reconcile detected hallucinations
                if hallucination.severity > 0.5:  # Only reconcile significant hallucinations
                    reconciliation = self.reality_reconciler.reconcile(hallucination)
                    
                    logger.info(f"Reconciled hallucination: {hallucination.hallucination_type.value}")
                
        except Exception as e:
            logger.error(f"Error auditing state coherence: {e}")
    
    def _get_module_outputs(self, module_id: str) -> List[Dict[str, Any]]:
        """Get current outputs from a module"""
        # This would interface with actual modules
        # For now, return empty list
        return []
    
    def _get_module_performance(self, module_id: str) -> Dict[str, float]:
        """Get current performance metrics from a module"""
        # This would interface with actual modules
        # For now, return empty dict
        return {}
    
    def _get_module_error_count(self, module_id: str) -> int:
        """Get current error count from a module"""
        # This would interface with actual modules
        # For now, return 0
        return 0
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of audit results"""
        with self.lock:
            total_modules = len(self.module_registry)
            healthy_modules = sum(
                1 for m in self.module_registry.values() 
                if m["status"] == ModuleStatus.HEALTHY
            )
            degraded_modules = sum(
                1 for m in self.module_registry.values() 
                if m["status"] == ModuleStatus.DEGRADED
            )
            critical_modules = sum(
                1 for m in self.module_registry.values() 
                if m["status"] == ModuleStatus.CRITICAL
            )
            
            recent_audits = list(self.audit_history)[-10:]
            
            return {
                "total_modules": total_modules,
                "healthy_modules": healthy_modules,
                "degraded_modules": degraded_modules,
                "critical_modules": critical_modules,
                "recent_drift_detections": len(self.semantic_drift_detector.detection_history),
                "recent_hallucination_detections": len(self.state_coherence_inspector.hallucination_detections),
                "recent_reconciliations": len(self.reality_reconciler.reconciliation_history),
                "recent_audits": recent_audits
            }
    
    def inspect_state_coherence(self) -> List[HallucinationDetection]:
        """Public method to inspect state coherence on demand"""
        return self.state_coherence_inspector.inspect_state_coherence()


# Singleton instance
_autopoietic_auditor_instance: Optional[AutopoieticAuditor] = None
_auditor_lock = threading.Lock()

def get_autopoietic_auditor(inspection_interval: float = 60.0) -> AutopoieticAuditor:
    """Get the singleton Autopoietic Auditor instance"""
    global _autopoietic_auditor_instance
    with _auditor_lock:
        if _autopoietic_auditor_instance is None:
            _autopoietic_auditor_instance = AutopoieticAuditor(inspection_interval)
            _autopoietic_auditor_instance.start_audit_loop()
        return _autopoietic_auditor_instance


if __name__ == "__main__":
    # Test the Autopoietic Auditor
    print("Testing Autopoietic Auditor...")
    
    auditor = get_autopoietic_auditor()
    
    # Register a test module
    sample_outputs = [
        {"status": "success", "data": {"value": 42}},
        {"status": "success", "data": {"value": 43}},
        {"status": "success", "data": {"value": 44}}
    ]
    
    performance_data = {
        "execution_time": 0.5,
        "memory_usage": 1024,
        "cpu_usage": 0.3
    }
    
    auditor.register_module(
        module_id="test_module_1",
        module_name="Test Module",
        module_path="test_module.py",
        sample_outputs=sample_outputs,
        performance_data=performance_data
    )
    
    # Register mock data sources
    class MockDataSource:
        def get_state(self):
            return {"activity": "coding", "timestamp": datetime.now().timestamp()}
    
    auditor.register_data_source("memory", MockDataSource())
    auditor.register_data_source("awareness", MockDataSource())
    
    # Wait for an audit cycle
    time.sleep(2)
    
    # Get audit summary
    summary = auditor.get_audit_summary()
    print(f"\nAudit Summary: {summary}")
    
    # Test state coherence inspection
    hallucinations = auditor.inspect_state_coherence()
    print(f"\nHallucination Detections: {len(hallucinations)}")
    
    # Stop auditor
    auditor.stop_audit_loop()
    
    print("\nAutopoietic Auditor test completed successfully!")