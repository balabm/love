"""
LOVE Capability Gap Detector — Cross-Domain Analysis

This module enhances LOVE's ability to detect capability gaps across
multiple life domains and generate comprehensive improvement hypotheses.

Enhanced capabilities:
1. CROSS-DOMAIN GAP ANALYSIS
   - Detects gaps that span multiple life areas
   - Identifies interconnected issues
   - Generates holistic solutions

2. DYNAMIC GAP PRIORITIZATION
   - Prioritizes gaps based on user goals and values
   - Considers urgency and impact
   - Adapts to changing circumstances

3. ROOT CAUSE ANALYSIS
   - Traces gaps to underlying causes
   - Identifies systemic issues
   - Suggests fundamental improvements

4. GAP TREND ANALYSIS
   - Tracks how gaps change over time
   - Detects emerging issues
   - Predicts future gaps
"""

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from core.llm import get_reasoning_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "capability_gaps"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GAPS_FILE = DATA_DIR / "gaps.json"
GAP_HISTORY = DATA_DIR / "gap_history.jsonl"
ANALYSIS_LOG = DATA_DIR / "analysis_log.jsonl"


@dataclass
class CapabilityGap:
    """A detected capability gap."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    domain: str = ""  # health, career, finance, relationships, creativity, productivity
    subdomain: str = ""  # specific area within domain
    description: str = ""
    severity: float = 0.5  # 0-1: how severe the gap is
    impact: float = 0.5  # 0-1: how much this affects the user's life
    urgency: float = 0.5  # 0-1: how urgently this needs to be addressed
    root_causes: List[str] = field(default_factory=list)
    related_gaps: List[str] = field(default_factory=list)  # IDs of related gaps
    suggested_fixes: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    first_detected: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "open"  # open, addressing, resolved, ignored
    resolution_notes: str = ""
    trend: str = "stable"  # worsening, stable, improving


@dataclass
class CrossDomainGap:
    """A gap that spans multiple domains."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    domains: List[str] = field(default_factory=list)
    description: str = ""
    pattern: str = ""  # the pattern connecting the domains
    severity: float = 0.5
    component_gaps: List[str] = field(default_factory=list)  # IDs of component gaps
    holistic_solution: str = ""
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class GapTrend:
    """Trend analysis for a specific gap."""
    gap_id: str = ""
    metric_name: str = ""
    historical_values: List[Tuple[str, float]] = field(default_factory=list)  # (timestamp, value)
    trend_direction: str = "stable"  # improving, stable, worsening
    trend_strength: float = 0.0  # 0-1: how strong the trend is
    predicted_value: float = 0.0
    prediction_confidence: float = 0.0


class CapabilityGapDetector:
    """
    Enhanced capability gap detection with cross-domain analysis.
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
        self._gaps: Dict[str, CapabilityGap] = {}
        self._cross_domain_gaps: Dict[str, CrossDomainGap] = {}
        self._gap_trends: Dict[str, GapTrend] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_gaps()
    
    # ── Gap Detection ───────────────────────────────────────────────────────────
    
    def detect_all_gaps(self) -> List[CapabilityGap]:
        """Detect gaps across all domains."""
        new_gaps = []
        
        # Detect gaps in each domain
        new_gaps.extend(self._detect_health_gaps())
        new_gaps.extend(self._detect_career_gaps())
        new_gaps.extend(self._detect_finance_gaps())
        new_gaps.extend(self._detect_relationship_gaps())
        new_gaps.extend(self._detect_creativity_gaps())
        new_gaps.extend(self._detect_productivity_gaps())
        
        # Detect cross-domain gaps
        self._detect_cross_domain_gaps()
        
        # Update trends
        self._update_gap_trends()
        
        # Save new gaps
        for gap in new_gaps:
            self._gaps[gap.id] = gap
        
        self._save_gaps()
        
        # ── TRIGGER SELF-CODER FOR HIGH-IMPACT GAPS ──
        try:
            from core.self_coder import get_self_coder
            sc = get_self_coder()
            for gap in high_impact[:1]:  # Trigger at most 1 per scan
                domain_file_map = {
                    "health": "core/heartbeat.py",
                    "career": "core/daily_briefing.py",
                    "finance": "integrations/finance_intelligence.py",
                    "relationships": "core/life_domains.py",
                    "creativity": "core/dream_engine.py",
                }
                target_file = domain_file_map.get(gap.domain, "core/evolution_engine.py")
                hypothesis = f"Improve {gap.subdomain}: {gap.description}"
                mod = sc.generate_modification(
                    hypothesis=hypothesis,
                    file_path=target_file,
                    improvement_type="gap_closure"
                )
                if mod:
                    print(f"[GapDetector] Triggered self-coder for gap: {gap.subdomain}")
        except Exception as e:
            print(f"[GapDetector] Self-coder trigger error: {e}")

        # ── CREATE MISSIONS FROM HIGH-IMPACT GAPS ──
        try:
            high_impact = [g for g in new_gaps if g.impact > 0.6 and g.urgency > 0.5]
            if high_impact:
                from core.autonomous_mission_queue import get_mission_queue
                mq = get_mission_queue()
                for gap in high_impact[:3]:
                    mq.add_mission(
                        title=f"Close gap: {gap.subdomain}",
                        description=f"{gap.description}. Fixes: {', '.join(gap.suggested_fixes[:2])}",
                        domain=gap.domain,
                        priority="high" if gap.urgency > 0.7 else "normal",
                        source="capability_gap_detector",
                    )
                # Report to orchestrator
                try:
                    from core.master_orchestrator import get_orchestration_master
                    om = get_orchestration_master()
                    om._narrate("gap_missions", f"Created {len(high_impact[:3])} missions from capability gaps", "action")
                except Exception:
                    pass
        except Exception:
            pass
        
        return new_gaps
    
    def _detect_health_gaps(self) -> List[CapabilityGap]:
        """Detect health-related capability gaps."""
        gaps = []
        
        try:
            from agents.fitness_agent import get_fitness_overview
            fitness = get_fitness_overview()
            
            # Check for inactivity
            activity_level = fitness.get("recent_activity_level", 0.5)
            if activity_level < 0.3:
                gap = CapabilityGap(
                    domain="health",
                    subdomain="physical_activity",
                    description="Low physical activity level",
                    severity=0.7,
                    impact=0.6,
                    urgency=0.5,
                    evidence=[f"Activity level: {activity_level}"],
                    suggested_fixes=[
                        "Schedule daily 30-minute walks",
                        "Set up exercise reminders",
                        "Find a physical activity you enjoy",
                    ],
                )
                gaps.append(gap)
            
            # Check for sleep issues
            sleep_quality = fitness.get("sleep_quality", 0.5)
            if sleep_quality < 0.4:
                gap = CapabilityGap(
                    domain="health",
                    subdomain="sleep",
                    description="Poor sleep quality",
                    severity=0.8,
                    impact=0.7,
                    urgency=0.6,
                    evidence=[f"Sleep quality: {sleep_quality}"],
                    suggested_fixes=[
                        "Establish consistent sleep schedule",
                        "Reduce screen time before bed",
                        "Create relaxing bedtime routine",
                    ],
                )
                gaps.append(gap)
            
        except Exception as e:
            print(f"[GapDetector] Health gap detection error: {e}")
        
        return gaps
    
    def _detect_career_gaps(self) -> List[CapabilityGap]:
        """Detect career-related capability gaps."""
        gaps = []
        
        try:
            from agents.task_agent import get_task_overview
            tasks = get_task_overview()
            
            # Check for overdue tasks
            overdue_count = tasks.get("overdue_count", 0)
            if overdue_count > 3:
                gap = CapabilityGap(
                    domain="career",
                    subdomain="task_management",
                    description=f"High number of overdue tasks ({overdue_count})",
                    severity=0.8,
                    impact=0.7,
                    urgency=0.9,
                    evidence=[f"Overdue tasks: {overdue_count}"],
                    root_causes=[
                        "Poor time estimation",
                        "Too many commitments",
                        "Lack of prioritization",
                    ],
                    suggested_fixes=[
                        "Implement time-blocking",
                        "Reduce commitment load",
                        "Use Eisenhower matrix for prioritization",
                    ],
                )
                gaps.append(gap)
            
            # Check for project completion issues
            completion_rate = tasks.get("completion_rate", 0.5)
            if completion_rate < 0.5:
                gap = CapabilityGap(
                    domain="career",
                    subdomain="project_completion",
                    description="Low project completion rate",
                    severity=0.6,
                    impact=0.8,
                    urgency=0.7,
                    evidence=[f"Completion rate: {completion_rate}"],
                    suggested_fixes=[
                        "Break projects into smaller tasks",
                        "Set intermediate milestones",
                        "Implement accountability system",
                    ],
                )
                gaps.append(gap)
            
        except Exception as e:
            print(f"[GapDetector] Career gap detection error: {e}")
        
        return gaps
    
    def _detect_finance_gaps(self) -> List[CapabilityGap]:
        """Detect finance-related capability gaps."""
        gaps = []
        
        try:
            from integrations.finance_intelligence import get_finance_intelligence
            fi = get_finance_intelligence()
            
            # Check for financial alerts
            alerts = fi.get_alerts(10)
            if len(alerts) > 5:
                gap = CapabilityGap(
                    domain="finance",
                    subdomain="financial_monitoring",
                    description=f"Multiple financial alerts ({len(alerts)})",
                    severity=0.7,
                    impact=0.6,
                    urgency=0.8,
                    evidence=[f"Alert count: {len(alerts)}"],
                    suggested_fixes=[
                        "Review financial portfolio",
                        "Set up alert thresholds",
                        "Consider risk adjustment",
                    ],
                )
                gaps.append(gap)
            
        except Exception as e:
            print(f"[GapDetector] Finance gap detection error: {e}")
        
        return gaps
    
    def _detect_relationship_gaps(self) -> List[CapabilityGap]:
        """Detect relationship-related capability gaps."""
        gaps = []
        
        try:
            from core.autonomous import get_relationship_state
            rel_state = get_relationship_state()
            if not rel_state:
                return gaps
            
            raw_freq = rel_state.get("interaction_frequency")
            if raw_freq is None:
                return gaps
            
            try:
                interaction_freq = float(raw_freq)
            except (ValueError, TypeError):
                return gaps
            
            if interaction_freq < 0.3:
                gap = CapabilityGap(
                    domain="relationships",
                    subdomain="social_connection",
                    description="Low social interaction frequency",
                    severity=0.5,
                    impact=0.6,
                    urgency=0.4,
                    evidence=[f"Interaction frequency: {interaction_freq}"],
                    suggested_fixes=[
                        "Schedule regular social activities",
                        "Reach out to friends/family",
                        "Join community groups",
                    ],
                )
                gaps.append(gap)
            
        except Exception:
            pass
        
        return gaps
    
    def _detect_creativity_gaps(self) -> List[CapabilityGap]:
        """Detect creativity-related capability gaps."""
        gaps = []
        
        try:
            from core.memory import recall_memory
            creative_activities = recall_memory("creative activities", n=10)
            
            # Check for low creative output
            if not creative_activities or len(str(creative_activities)) < 100:
                gap = CapabilityGap(
                    domain="creativity",
                    subdomain="creative_output",
                    description="Low creative activity",
                    severity=0.4,
                    impact=0.5,
                    urgency=0.3,
                    evidence=["Few or no recent creative activities recorded"],
                    suggested_fixes=[
                        "Schedule creative time",
                        "Start a creative project",
                        "Explore new creative outlets",
                    ],
                )
                gaps.append(gap)
            
        except Exception as e:
            print(f"[GapDetector] Creativity gap detection error: {e}")
        
        return gaps
    
    def _detect_productivity_gaps(self) -> List[CapabilityGap]:
        """Detect productivity-related capability gaps."""
        gaps = []
        
        try:
            from core.awareness import get_awareness
            awareness = get_awareness()
            snapshot = awareness.get_snapshot()
            
            # Check for poor focus
            focus_depth = snapshot.get("focus_depth", 1.0)
            if focus_depth < 0.5:
                gap = CapabilityGap(
                    domain="productivity",
                    subdomain="focus",
                    description="Poor focus depth",
                    severity=0.6,
                    impact=0.7,
                    urgency=0.6,
                    evidence=[f"Focus depth: {focus_depth}"],
                    suggested_fixes=[
                        "Implement focus techniques (Pomodoro)",
                        "Reduce distractions",
                        "Optimize work environment",
                    ],
                )
                gaps.append(gap)
            
        except Exception as e:
            print(f"[GapDetector] Productivity gap detection error: {e}")
        
        return gaps
    
    # ── Cross-Domain Analysis ─────────────────────────────────────────────────
    
    def _detect_cross_domain_gaps(self):
        """Detect gaps that span multiple domains."""
        # Group gaps by domain
        domain_gaps = defaultdict(list)
        for gap in self._gaps.values():
            if gap.status == "open":
                domain_gaps[gap.domain].append(gap)
        
        # Look for patterns across domains
        cross_domain_patterns = [
            {
                "domains": ["health", "productivity"],
                "pattern": "Health issues affecting productivity",
                "description": "Poor health leading to decreased productivity",
            },
            {
                "domains": ["finance", "career"],
                "pattern": "Financial stress affecting work performance",
                "description": "Financial concerns impacting career focus",
            },
            {
                "domains": ["health", "relationships"],
                "pattern": "Health issues affecting social connections",
                "description": "Poor health limiting social activities",
            },
            {
                "domains": ["career", "relationships"],
                "pattern": "Work-life imbalance",
                "description": "Career demands affecting relationships",
            },
        ]
        
        for pattern_def in cross_domain_patterns:
            domains = pattern_def["domains"]
            
            # Check if all domains have significant gaps
            has_gaps = all(
                len(domain_gaps.get(d, [])) > 0 for d in domains
            )
            
            if has_gaps:
                # Create cross-domain gap
                component_gap_ids = []
                for domain in domains:
                    for gap in domain_gaps[domain]:
                        component_gap_ids.append(gap.id)
                
                cross_gap = CrossDomainGap(
                    domains=domains,
                    description=pattern_def["description"],
                    pattern=pattern_def["pattern"],
                    component_gaps=component_gap_ids,
                    severity=max(
                        self._gaps[gid].severity 
                        for gid in component_gap_ids
                    ),
                )
                
                # Generate holistic solution using LLM
                cross_gap.holistic_solution = self._generate_holistic_solution(cross_gap)
                
                self._cross_domain_gaps[cross_gap.id] = cross_gap
    
    def _generate_holistic_solution(self, cross_gap: CrossDomainGap) -> str:
        """Generate a holistic solution for a cross-domain gap."""
        try:
            llm = get_reasoning_llm()
            
            # Get component gap details
            component_details = []
            for gap_id in cross_gap.component_gaps:
                if gap_id in self._gaps:
                    gap = self._gaps[gap_id]
                    component_details.append(
                        f"- {gap.domain}/{gap.subdomain}: {gap.description}"
                    )
            
            prompt = f"""Generate a holistic solution for this cross-domain issue:

Pattern: {cross_gap.pattern}
Description: {cross_gap.description}

Component gaps:
{chr(10).join(component_details)}

Provide a comprehensive solution that addresses all domains holistically.
Focus on interconnected improvements rather than isolated fixes."""
            
            response = llm.invoke(prompt)
            return response
            
        except Exception as e:
            print(f"[GapDetector] Holistic solution generation error: {e}")
            return "Address each component gap individually"
    
    # ── Trend Analysis ───────────────────────────────────────────────────────────
    
    def _update_gap_trends(self):
        """Update trend analysis for all gaps."""
        for gap in self._gaps.values():
            if gap.id not in self._gap_trends:
                self._gap_trends[gap.id] = GapTrend(gap_id=gap.id)
            
            trend = self._gap_trends[gap.id]
            
            # Add current severity to historical values
            trend.historical_values.append((datetime.now().isoformat(), gap.severity))
            
            # Keep only last 30 data points
            if len(trend.historical_values) > 30:
                trend.historical_values = trend.historical_values[-30:]
            
            # Calculate trend direction
            if len(trend.historical_values) >= 3:
                recent_values = [v for _, v in trend.historical_values[-5:]]
                if len(recent_values) >= 3:
                    # Simple linear regression
                    n = len(recent_values)
                    x = list(range(n))
                    sum_x = sum(x)
                    sum_y = sum(recent_values)
                    sum_xy = sum(xi * yi for xi, yi in zip(x, recent_values))
                    sum_x2 = sum(xi * xi for xi in x)
                    
                    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                    
                    if slope > 0.01:
                        trend.trend_direction = "worsening"
                        trend.trend_strength = min(1.0, abs(slope) * 10)
                    elif slope < -0.01:
                        trend.trend_direction = "improving"
                        trend.trend_strength = min(1.0, abs(slope) * 10)
                    else:
                        trend.trend_direction = "stable"
                        trend.trend_strength = 0.0
                    
                    # Simple prediction
                    if len(recent_values) > 0:
                        trend.predicted_value = recent_values[-1] + slope
                        trend.predicted_value = max(0.0, min(1.0, trend.predicted_value))
                        trend.prediction_confidence = trend.trend_strength
    
    # ── Gap Management ───────────────────────────────────────────────────────────
    
    def prioritize_gaps(self) -> List[CapabilityGap]:
        """Prioritize gaps based on severity, impact, and urgency."""
        open_gaps = [g for g in self._gaps.values() if g.status == "open"]
        
        # Calculate priority score
        for gap in open_gaps:
            gap.priority_score = (
                gap.severity * 0.4 + 
                gap.impact * 0.3 + 
                gap.urgency * 0.3
            )
        
        # Sort by priority score
        prioritized = sorted(open_gaps, key=lambda g: g.priority_score, reverse=True)
        
        return prioritized
    
    def mark_gap_resolved(self, gap_id: str, resolution_notes: str = ""):
        """Mark a gap as resolved."""
        if gap_id in self._gaps:
            self._gaps[gap_id].status = "resolved"
            self._gaps[gap_id].resolution_notes = resolution_notes
            self._gaps[gap_id].last_updated = datetime.now().isoformat()
            self._save_gaps()
    
    def update_gap_evidence(self, gap_id: str, new_evidence: str):
        """Add evidence to a gap."""
        if gap_id in self._gaps:
            self._gaps[gap_id].evidence.append(new_evidence)
            self._gaps[gap_id].last_updated = datetime.now().isoformat()
            self._save_gaps()
    
    # ── Persistence ─────────────────────────────────────────────────────────────
    
    def _load_gaps(self):
        try:
            if GAPS_FILE.exists():
                data = json.loads(GAPS_FILE.read_text())
                for gid, gd in data.get("gaps", {}).items():
                    self._gaps[gid] = CapabilityGap(**gd)
                for cid, cd in data.get("cross_domain_gaps", {}).items():
                    self._cross_domain_gaps[cid] = CrossDomainGap(**cd)
                for tid, td in data.get("trends", {}).items():
                    self._gap_trends[tid] = GapTrend(**td)
        except Exception as e:
            print(f"[GapDetector] Gaps load error: {e}")
    
    def _save_gaps(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "gaps": {gid: asdict(g) for gid, g in self._gaps.items()},
                "cross_domain_gaps": {cid: asdict(c) for cid, c in self._cross_domain_gaps.items()},
                "trends": {tid: asdict(t) for tid, t in self._gap_trends.items()},
            }
            GAPS_FILE.write_text(json.dumps(data, indent=2, default=str))
        except Exception as e:
            print(f"[GapDetector] Gaps save error: {e}")
    
    def _log_analysis(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(ANALYSIS_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass
    
    # ── Main Loop ─────────────────────────────────────────────────────────────────
    
    def start(self):
        """Start the gap detection background loop."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-CapabilityGapDetector"
        )
        self._thread.start()
        print("[CapabilityGapDetector] Started — enhanced gap detection active")
    
    def stop(self):
        self._running = False
    
    def _main_loop(self):
        time.sleep(180)  # Let other systems initialize
        
        while self._running:
            try:
                # Detect all gaps
                new_gaps = self.detect_all_gaps()
                
                if new_gaps:
                    self._log_analysis({
                        "event": "gaps_detected",
                        "count": len(new_gaps),
                    })
                
            except Exception as e:
                print(f"[GapDetector] Loop error: {e}")
            
            time.sleep(1800)  # Run every 30 minutes
    
    # ── Query Methods ───────────────────────────────────────────────────────────
    
    def get_open_gaps(self, domain: str = "") -> List[Dict]:
        """Get open gaps, optionally filtered by domain."""
        gaps = [g for g in self._gaps.values() if g.status == "open"]
        
        if domain:
            gaps = [g for g in gaps if g.domain == domain]
        
        return [asdict(g) for g in gaps]
    
    def get_cross_domain_gaps(self) -> List[Dict]:
        """Get all cross-domain gaps."""
        return [asdict(g) for g in self._cross_domain_gaps.values()]
    
    def get_gap_trends(self, gap_id: str) -> Optional[Dict]:
        """Get trend analysis for a specific gap."""
        if gap_id not in self._gap_trends:
            return None
        return asdict(self._gap_trends[gap_id])


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gap_detector_instance: Optional[CapabilityGapDetector] = None
_gap_detector_lock = threading.Lock()


def get_capability_gap_detector() -> CapabilityGapDetector:
    global _gap_detector_instance
    with _gap_detector_lock:
        if _gap_detector_instance is None:
            _gap_detector_instance = CapabilityGapDetector()
        return _gap_detector_instance