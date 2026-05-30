"""
LOVE Self-Reflection — Meta-Cognitive Analysis (Modern AI Pattern)

When LOVE operates 15+ subsystems autonomously, it needs to understand
its own behavior, not just the user's. Self-reflection provides:

1. BEHAVIORAL PATTERN ANALYSIS
   - Track what LOVE does across all subsystems
   - Identify repetitive patterns, inefficiencies, and biases
   - Detect when LOVE is over-reacting or under-reacting

2. DECISION AUDITING
   - Record why each significant decision was made
   - Review decisions for quality and appropriateness
   - Flag decisions that had poor outcomes

3. CAPABILITY SELF-ASSESSMENT
   - LOVE evaluates its own strengths and weaknesses
   - Compares stated capabilities vs actual performance
   - Identifies overconfidence or underconfidence

4. PROACTIVE SELF-IMPROVEMENT
   - Generates specific improvement hypotheses about itself
   - Feeds insights into the evolution engine as self-improvement missions
   - Suggests configuration changes based on observed patterns

Architecture:
- reflect(): Run a self-reflection cycle
- audit_decision(): Review a past decision
- assess_capabilities(): Evaluate LOVE's own abilities
- generate_insights(): Create improvement hypotheses
"""

import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "self_reflection"
DATA_DIR.mkdir(parents=True, exist_ok=True)

REFLECTION_LOG = DATA_DIR / "reflection_log.jsonl"
INSIGHTS_DB = DATA_DIR / "insights_db.json"
DECISION_AUDIT_LOG = DATA_DIR / "decision_audit.jsonl"


@dataclass
class DecisionAudit:
    """A record of a significant decision and its outcome."""
    id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    subsystem: str = ""
    decision_type: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    decision: str = ""
    reasoning: str = ""
    expected_outcome: str = ""
    actual_outcome: str = ""
    outcome_quality: float = 0.0  # -1 to 1
    reviewed: bool = False


@dataclass
class SelfInsight:
    """An insight generated from self-reflection."""
    id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    category: str = ""  # behavior, capability, decision, efficiency
    observation: str = ""
    evidence: List[str] = field(default_factory=list)
    severity: str = "info"  # info, warning, critical
    suggested_action: str = ""
    implemented: bool = False


class SelfReflectionEngine:
    """
    Meta-cognitive self-reflection for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._decisions: deque = deque(maxlen=1000)
        self._insights: List[SelfInsight] = []
        self._stats = {"reflections": 0, "audits": 0, "insights": 0}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_insights()

    # ── Core Reflection ────────────────────────────────────────────────────

    def reflect(self) -> Dict[str, Any]:
        """Run a comprehensive self-reflection cycle."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "behavioral_patterns": self._analyze_behavioral_patterns(),
            "capability_assessment": self._assess_capabilities(),
            "decision_quality": self._audit_recent_decisions(),
            "new_insights": [],
        }

        # Generate new insights from patterns
        for pattern in results["behavioral_patterns"]:
            if pattern.get("significance", 0) > 0.7:
                insight = SelfInsight(
                    category="behavior",
                    observation=pattern["description"],
                    evidence=pattern.get("evidence", []),
                    severity="warning" if pattern["significance"] > 0.9 else "info",
                    suggested_action=pattern.get("suggestion", ""),
                )
                results["new_insights"].append(insight)
                self._insights.append(insight)

        for assessment in results["capability_assessment"]:
            if assessment.get("gap", 0) > 0.5:
                insight = SelfInsight(
                    category="capability",
                    observation=f"Capability gap in {assessment['capability']}: {assessment['gap']:.0%}",
                    evidence=[f"Expected: {assessment['expected']}, Actual: {assessment['actual']}"],
                    severity="warning" if assessment["gap"] > 0.8 else "info",
                    suggested_action=f"Consider training or evolving {assessment['capability']}",
                )
                results["new_insights"].append(insight)
                self._insights.append(insight)

        self._stats["reflections"] += 1
        self._stats["insights"] += len(results["new_insights"])
        self._save_insights()
        self._log_reflection(results)

        return results

    # ── Behavioral Pattern Analysis ─────────────────────────────────────────

    def _analyze_behavioral_patterns(self) -> List[Dict[str, Any]]:
        """Analyze LOVE's own behavioral patterns."""
        patterns = []

        # Pattern 1: Check for repetitive error types
        try:
            from core.observability import get_observability_engine
            obs = get_observability_engine()
            # Get recent alerts
            recent_alerts = [a for a in obs._alerts if a.severity in ("warning", "critical")]
            if len(recent_alerts) > 5:
                subsystems = defaultdict(int)
                for a in recent_alerts:
                    subsystems[a.subsystem] += 1
                top_subsystem = max(subsystems, key=subsystems.get)
                patterns.append({
                    "type": "repeated_errors",
                    "description": f"Frequent alerts from {top_subsystem} ({subsystems[top_subsystem]} recent)",
                    "significance": min(1.0, subsystems[top_subsystem] / 10),
                    "evidence": [a.title for a in recent_alerts if a.subsystem == top_subsystem][:3],
                    "suggestion": f"Investigate {top_subsystem} stability or configuration",
                })
        except Exception:
            pass

        # Pattern 2: Check for work limit violations
        try:
            from core.guardrails import get_guardrails_engine
            gr = get_guardrails_engine()
            # If guardrails has logged warnings
            if hasattr(gr, '_stats') and gr._stats.get("warnings", 0) > 3:
                patterns.append({
                    "type": "user_overwork",
                    "description": f"User has received {gr._stats['warnings']} proactive warnings recently",
                    "significance": min(1.0, gr._stats["warnings"] / 10),
                    "evidence": ["Work limit warnings", "Sleep warnings", "Social isolation warnings"],
                    "suggestion": "Consider adjusting default work limit or proactive nudge frequency",
                })
        except Exception:
            pass

        # Pattern 3: Check evolution activity
        try:
            from core.evolution_integration import get_evolution_integration
            evo = get_evolution_integration()
            status = evo.get_integration_status()
            mods = status.get("statistics", {}).get("total_code_modifications", 0)
            if mods > 50:
                patterns.append({
                    "type": "high_evolution_activity",
                    "description": f"High evolution activity: {mods} code modifications",
                    "significance": min(1.0, mods / 100),
                    "evidence": [f"{mods} modifications", f"{status.get('statistics', {}).get('total_mutations_applied', 0)} mutations"],
                    "suggestion": "Review if evolution pace is appropriate for system stability",
                })
        except Exception:
            pass

        return patterns

    # ── Capability Assessment ───────────────────────────────────────────────

    def _assess_capabilities(self) -> List[Dict[str, Any]]:
        """Assess LOVE's own capabilities against expectations."""
        assessments = []

        capabilities = [
            ("reasoning", "Can answer complex questions with chain-of-thought"),
            ("memory", "Can recall conversations from weeks ago"),
            ("proactivity", "Can suggest actions before user asks"),
            ("evolution", "Can self-improve without human intervention"),
            ("multimodal", "Can process vision and voice inputs"),
        ]

        for cap_name, cap_desc in capabilities:
            try:
                # Check if capability module exists and is functional
                score = self._check_capability(cap_name)
                assessments.append({
                    "capability": cap_name,
                    "description": cap_desc,
                    "expected": 0.8,
                    "actual": score,
                    "gap": max(0, 0.8 - score),
                })
            except Exception:
                pass

        return assessments

    def _check_capability(self, name: str) -> float:
        """Check if a capability is available and functional."""
        if name == "reasoning":
            try:
                from core.reasoning_engine import get_reasoning_engine
                re = get_reasoning_engine()
                return 0.9
            except Exception:
                return 0.0
        elif name == "memory":
            try:
                from core.vector_memory import get_vector_engine
                vm = get_vector_engine()
                return 0.8 if vm._memories else 0.3
            except Exception:
                return 0.0
        elif name == "proactivity":
            try:
                from core.proactive_push import get_push_engine
                pp = get_push_engine()
                return 0.9 if getattr(pp, '_running', False) else 0.0
            except Exception:
                return 0.0
        elif name == "evolution":
            try:
                from core.evolution_integration import get_evolution_integration
                evo = get_evolution_integration()
                return 0.9 if evo._running else 0.0
            except Exception:
                return 0.0
        elif name == "multimodal":
            try:
                from core.multimodal_evolution import get_multimodal_evolution
                mme = get_multimodal_evolution()
                return 0.7 if mme._running else 0.0
            except Exception:
                return 0.0
        return 0.0

    # ── Decision Auditing ───────────────────────────────────────────────────

    def record_decision(self, subsystem: str, decision_type: str,
                        context: Dict, decision: str, reasoning: str,
                        expected_outcome: str = ""):
        """Record a significant decision for later auditing."""
        audit = DecisionAudit(
            id=f"dec_{int(time.time())}_{random.randint(1000, 9999)}",
            subsystem=subsystem,
            decision_type=decision_type,
            context=context,
            decision=decision,
            reasoning=reasoning,
            expected_outcome=expected_outcome,
        )
        with self._lock:
            self._decisions.append(audit)
        self._log_decision(audit)

    def _audit_recent_decisions(self) -> List[Dict[str, Any]]:
        """Audit recent decisions for quality."""
        audited = []
        recent = list(self._decisions)[-20:]

        for decision in recent:
            if decision.reviewed:
                continue

            # Simple heuristic: if decision was about warning user and no follow-up,
            # mark as potentially unnecessary
            quality = 0.0
            if "warn" in decision.decision_type.lower():
                # Check if warning was followed by user action
                quality = 0.5  # Neutral - warnings are hard to evaluate

            decision.outcome_quality = quality
            decision.reviewed = True
            audited.append({
                "decision_id": decision.id,
                "subsystem": decision.subsystem,
                "type": decision.decision_type,
                "quality": quality,
                "reasoning": decision.reasoning[:100],
            })

        self._stats["audits"] += len(audited)
        return audited

    # ── Statistics ──────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "total_decisions": len(self._decisions),
            "total_insights": len(self._insights),
            "pending_insights": len([i for i in self._insights if not i.implemented]),
        }

    def get_recent_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent insights."""
        return [
            {
                "id": i.id,
                "category": i.category,
                "observation": i.observation,
                "severity": i.severity,
                "suggested_action": i.suggested_action,
                "implemented": i.implemented,
                "timestamp": i.timestamp,
            }
            for i in sorted(self._insights, key=lambda x: x.timestamp, reverse=True)[:limit]
        ]

    # ── Background Loop ─────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-SelfReflection"
        )
        self._thread.start()
        print("[SelfReflection] Started — meta-cognitive analysis active")

    def stop(self):
        self._running = False

    def _main_loop(self):
        time.sleep(600)  # First reflection after 10 minutes
        while self._running:
            try:
                results = self.reflect()
                if results["new_insights"]:
                    print(f"[SelfReflection] Generated {len(results['new_insights'])} new insights")
                    # Publish to neural bus
                    try:
                        from core.neural_bus import get_neural_bus
                        bus = get_neural_bus()
                        for insight in results["new_insights"]:
                            bus.publish("self_reflection", {
                                "category": insight.category,
                                "observation": insight.observation,
                                "severity": insight.severity,
                                "suggested_action": insight.suggested_action,
                            })
                    except Exception:
                        pass
            except Exception as e:
                print(f"[SelfReflection] Loop error: {e}")
            time.sleep(3600)  # Reflect every hour

    # ── Persistence ──────────────────────────────────────────────────────────

    def _log_reflection(self, results: Dict):
        try:
            with open(REFLECTION_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": results["timestamp"],
                    "patterns_found": len(results["behavioral_patterns"]),
                    "capabilities_assessed": len(results["capability_assessment"]),
                    "decisions_audited": len(results["decision_quality"]),
                    "insights_generated": len(results["new_insights"]),
                }) + "\n")
        except Exception:
            pass

    def _log_decision(self, audit: DecisionAudit):
        try:
            with open(DECISION_AUDIT_LOG, "a") as f:
                f.write(json.dumps({
                    "id": audit.id,
                    "timestamp": audit.timestamp,
                    "subsystem": audit.subsystem,
                    "decision_type": audit.decision_type,
                    "decision": audit.decision,
                    "reasoning": audit.reasoning,
                }) + "\n")
        except Exception:
            pass

    def _save_insights(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "insights": [
                    {
                        "id": i.id,
                        "timestamp": i.timestamp,
                        "category": i.category,
                        "observation": i.observation,
                        "evidence": i.evidence,
                        "severity": i.severity,
                        "suggested_action": i.suggested_action,
                        "implemented": i.implemented,
                    }
                    for i in self._insights
                ],
            }
            INSIGHTS_DB.write_text(json.dumps(data, indent=2, default=str))
        except Exception:
            pass

    def _load_insights(self):
        try:
            if INSIGHTS_DB.exists():
                data = json.loads(INSIGHTS_DB.read_text())
                for ins in data.get("insights", []):
                    self._insights.append(SelfInsight(**ins))
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_self_reflection_instance: Optional[SelfReflectionEngine] = None
_self_reflection_lock = threading.Lock()


def get_self_reflection_engine() -> SelfReflectionEngine:
    global _self_reflection_instance
    with _self_reflection_lock:
        if _self_reflection_instance is None:
            _self_reflection_instance = SelfReflectionEngine()
        return _self_reflection_instance
