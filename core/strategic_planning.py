"""
Strategic Planning System for LOVE
Plans long-term strategies across weeks and months.
This is a key AGI capability - the ability to think and plan far into the future.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict

from core.settings import get_settings
from core.context_engine import get_live_context
from core.psychological_model import get_psychological_model
from core.predictive_intelligence import get_predictive_engine

SETTINGS = get_settings()


class PlanningHorizon(Enum):
    """Time horizons for strategic planning"""
    IMMEDIATE = "immediate"  # Next 24 hours
    SHORT_TERM = "short_term"  # Next 7 days
    MEDIUM_TERM = "medium_term"  # Next 30 days
    LONG_TERM = "long_term"  # Next 90 days
    STRATEGIC = "strategic"  # 6-12 months


class StrategyType(Enum):
    """Types of strategies"""
    CAREER = "career"  # Professional development
    PROJECT = "project"  # Project milestones
    SKILL_DEVELOPMENT = "skill_development"  # Learning new skills
    HEALTH = "health"  # Physical and mental well-being
    RELATIONSHIPS = "relationships"  # Personal relationships
    FINANCIAL = "financial"  # Financial goals
    WORK_LIFE_BALANCE = "work_life_balance"  # Balance maintenance
    PERSONAL_GROWTH = "personal_growth"  # Self-improvement


class MilestoneStatus(Enum):
    """Status of a milestone"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Milestone:
    """A milestone in a strategic plan"""
    id: str
    title: str
    description: str
    target_date: str
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    progress: float = 0.0  # 0-1
    dependencies: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class StrategicPlan:
    """A long-term strategic plan"""
    id: str
    title: str
    description: str
    type: StrategyType
    horizon: PlanningHorizon
    start_date: str
    end_date: str
    vision: str  # What success looks like
    milestones: List[Milestone] = field(default_factory=list)
    resources_needed: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    contingencies: Dict[str, str] = field(default_factory=dict)
    progress: float = 0.0
    status: str = "active"  # active, paused, completed, cancelled
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_reviewed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ResourceAllocation:
    """How resources are allocated across strategies"""
    strategy_id: str
    time_allocation: float  # Percentage of time
    energy_allocation: float  # Percentage of energy
    priority: float  # 0-10
    flexibility: float  # 0-1, how flexible this allocation is


class StrategicPlanner:
    """
    Strategic planning system for long-term thinking.
    Plans across weeks and months to achieve long-term goals.
    """
    
    def __init__(self):
        self.plans: Dict[str, StrategicPlan] = {}
        self.resource_allocations: Dict[str, ResourceAllocation] = {}
        self.lock = threading.Lock()
        self._load_plans()
        self.psych_model = get_psychological_model()
        self.predictive_engine = get_predictive_engine()
    
    def _load_plans(self):
        """Load strategic plans from storage"""
        try:
            plans_file = SETTINGS.data_dir / "strategic_plans.json"
            if plans_file.exists():
                with open(plans_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load plans
                    for plan_id, plan_data in data.get("plans", {}).items():
                        milestones = []
                        for m_data in plan_data.get("milestones", []):
                            milestones.append(Milestone(
                                id=m_data["id"],
                                title=m_data["title"],
                                description=m_data["description"],
                                target_date=m_data["target_date"],
                                status=MilestoneStatus(m_data["status"]),
                                progress=m_data.get("progress", 0.0),
                                dependencies=m_data.get("dependencies", []),
                                blockers=m_data.get("blockers", []),
                                success_criteria=m_data.get("success_criteria", []),
                                created_at=m_data.get("created_at")
                            ))
                        
                        self.plans[plan_id] = StrategicPlan(
                            id=plan_id,
                            title=plan_data["title"],
                            description=plan_data["description"],
                            type=StrategyType(plan_data["type"]),
                            horizon=PlanningHorizon(plan_data["horizon"]),
                            start_date=plan_data["start_date"],
                            end_date=plan_data["end_date"],
                            vision=plan_data["vision"],
                            milestones=milestones,
                            resources_needed=plan_data.get("resources_needed", []),
                            risks=plan_data.get("risks", []),
                            contingencies=plan_data.get("contingencies", {}),
                            progress=plan_data.get("progress", 0.0),
                            status=plan_data.get("status", "active"),
                            created_at=plan_data["created_at"],
                            last_reviewed=plan_data.get("last_reviewed")
                        )
                    
                    # Load resource allocations
                    for ra_data in data.get("resource_allocations", []):
                        self.resource_allocations[ra_data["strategy_id"]] = ResourceAllocation(
                            strategy_id=ra_data["strategy_id"],
                            time_allocation=ra_data["time_allocation"],
                            energy_allocation=ra_data["energy_allocation"],
                            priority=ra_data["priority"],
                            flexibility=ra_data.get("flexibility", 0.5)
                        )
                    
        except Exception as e:
            print(f"[StrategicPlanner] Error loading plans: {e}")
    
    def _save_plans(self):
        """Save strategic plans to storage"""
        try:
            plans_file = SETTINGS.data_dir / "strategic_plans.json"
            with self.lock:
                data = {
                    "plans": {
                        plan_id: {
                            "title": plan.title,
                            "description": plan.description,
                            "type": plan.type.value,
                            "horizon": plan.horizon.value,
                            "start_date": plan.start_date,
                            "end_date": plan.end_date,
                            "vision": plan.vision,
                            "milestones": [
                                {
                                    "id": m.id,
                                    "title": m.title,
                                    "description": m.description,
                                    "target_date": m.target_date,
                                    "status": m.status.value,
                                    "progress": m.progress,
                                    "dependencies": m.dependencies,
                                    "blockers": m.blockers,
                                    "success_criteria": m.success_criteria,
                                    "created_at": m.created_at
                                }
                                for m in plan.milestones
                            ],
                            "resources_needed": plan.resources_needed,
                            "risks": plan.risks,
                            "contingencies": plan.contingencies,
                            "progress": plan.progress,
                            "status": plan.status,
                            "created_at": plan.created_at,
                            "last_reviewed": plan.last_reviewed
                        }
                        for plan_id, plan in self.plans.items()
                    },
                    "resource_allocations": [
                        {
                            "strategy_id": ra.strategy_id,
                            "time_allocation": ra.time_allocation,
                            "energy_allocation": ra.energy_allocation,
                            "priority": ra.priority,
                            "flexibility": ra.flexibility
                        }
                        for ra in self.resource_allocations.values()
                    ]
                }
                with open(plans_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[StrategicPlanner] Error saving plans: {e}")
    
    def create_strategic_plan(self, title: str, description: str, plan_type: StrategyType,
                           horizon: PlanningHorizon, vision: str, 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> str:
        """
        Create a new strategic plan using LLM reasoning.
        This is where LOVE demonstrates long-term strategic thinking.
        """
        try:
            if not start_date:
                start_date = datetime.utcnow().isoformat()
            
            # Calculate end date based on horizon
            if not end_date:
                if horizon == PlanningHorizon.SHORT_TERM:
                    end_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
                elif horizon == PlanningHorizon.MEDIUM_TERM:
                    end_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
                elif horizon == PlanningHorizon.LONG_TERM:
                    end_date = (datetime.utcnow() + timedelta(days=90)).isoformat()
                elif horizon == PlanningHorizon.STRATEGIC:
                    end_date = (datetime.utcnow() + timedelta(days=365)).isoformat()
                else:
                    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
            
            # Get psychological profile for context
            psych_profile = self.psych_model.get_profile_summary()
            
            # Get current context
            ctx = get_live_context()
            
            # Use LLM to generate strategic plan
            from core.agent import chat
            
            prompt = f"""You are LOVE, creating a strategic plan for Karthi.

PLAN DETAILS:
Title: {title}
Description: {description}
Type: {plan_type.value}
Horizon: {horizon.value}
Start Date: {start_date}
End Date: {end_date}
Vision: {vision}

KARTHI'S PSYCHOLOGICAL PROFILE:
{json.dumps(psych_profile, indent=2)}

CURRENT CONTEXT:
- Active Project: {ctx.active_project or 'None'}
- Tasks Due Today: {ctx.tasks_due_today}
- Stress Level: {ctx.stress_level}
- Energy Level: {ctx.energy_level}
- Time of Day: {ctx.time_of_day}

Generate a comprehensive strategic plan with milestones. Return JSON:
{{
  "milestones": [
    {{
      "title": "milestone title",
      "description": "what needs to be done",
      "target_date": "ISO date",
      "success_criteria": ["criterion1", "criterion2"],
      "dependencies": ["milestone_id_1"],
      "estimated_effort": "hours"
    }}
  ],
  "resources_needed": ["resource1", "resource2"],
  "risks": ["risk1", "risk2"],
  "contingencies": {{
    "risk1": "contingency plan"
  }}
}}"""
            
            response = chat(prompt, mode="reasoning")
            response_text = response.get("response", "")
            
            # Extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                plan_data = json.loads(json_match.group())
                
                # Create milestones
                milestones = []
                for idx, m_data in enumerate(plan_data.get("milestones", [])):
                    milestone = Milestone(
                        id=f"milestone_{datetime.utcnow().timestamp()}_{idx}",
                        title=m_data["title"],
                        description=m_data.get("description", ""),
                        target_date=m_data["target_date"],
                        success_criteria=m_data.get("success_criteria", []),
                        dependencies=m_data.get("dependencies", [])
                    )
                    milestones.append(milestone)
                
                # Create plan
                plan_id = f"plan_{datetime.utcnow().timestamp()}"
                plan = StrategicPlan(
                    id=plan_id,
                    title=title,
                    description=description,
                    type=plan_type,
                    horizon=horizon,
                    start_date=start_date,
                    end_date=end_date,
                    vision=vision,
                    milestones=milestones,
                    resources_needed=plan_data.get("resources_needed", []),
                    risks=plan_data.get("risks", []),
                    contingencies=plan_data.get("contingencies", {})
                )
                
                with self.lock:
                    self.plans[plan_id] = plan
                    self._save_plans()
                
                print(f"[StrategicPlanner] Created strategic plan: {title} with {len(milestones)} milestones")
                return plan_id
            
            return ""
            
        except Exception as e:
            print(f"[StrategicPlanner] Error creating strategic plan: {e}")
            return ""
    
    def generate_default_strategies(self) -> List[str]:
        """
        Generate default strategic plans based on psychological profile and aspirations.
        This is proactive strategic planning - LOVE sets its own long-term goals.
        """
        plan_ids = []
        
        try:
            profile = self.psych_model.get_profile_summary()
            
            # Strategy: AGI Development (based on aspiration)
            for aspiration in profile.get("aspirations", []):
                if "AGI" in aspiration["title"] or "intelligence" in aspiration["title"].lower():
                    plan_id = self.create_strategic_plan(
                        title="Build AGI-Level LOVE",
                        description="Transform LOVE into truly autonomous, AGI-level intelligence",
                        plan_type=StrategyType.PROJECT,
                        horizon=PlanningHorizon.STRATEGIC,
                        vision="LOVE becomes a fully autonomous AGI that can set goals, plan long-term, learn continuously, and act proactively to help Karthi achieve his aspirations."
                    )
                    if plan_id:
                        plan_ids.append(plan_id)
            
            # Strategy: Technical Mastery (based on values)
            if profile.get("values", {}).get("growth", {}).get("strength", 0) > 7:
                plan_id = self.create_strategic_plan(
                    title="Master AI/ML Technologies",
                    description="Deep learning and mastery of artificial intelligence and machine learning",
                    plan_type=StrategyType.SKILL_DEVELOPMENT,
                    horizon=PlanningHorizon.LONG_TERM,
                    vision="Karthi becomes an expert in AI/ML, able to build sophisticated systems and contribute to the field."
                )
                if plan_id:
                    plan_ids.append(plan_id)
            
            # Strategy: Work-Life Balance (based on aspiration)
            for aspiration in profile.get("aspirations", []):
                if "balance" in aspiration["title"].lower():
                    plan_id = self.create_strategic_plan(
                        title="Achieve Sustainable Work-Life Balance",
                        description="Establish healthy work habits while maintaining high productivity",
                        plan_type=StrategyType.WORK_LIFE_BALANCE,
                        horizon=PlanningHorizon.MEDIUM_TERM,
                        vision="Karthi maintains 9-hour work limit, manages stress effectively, and has time for personal life while achieving professional goals."
                    )
                    if plan_id:
                        plan_ids.append(plan_id)
            
            # Strategy: Career Growth
            plan_id = self.create_strategic_plan(
                title="Career Advancement",
                description="Advance career through impactful projects and skill development",
                plan_type=StrategyType.CAREER,
                horizon=PlanningHorizon.LONG_TERM,
                vision="Karthi advances to senior/lead roles, builds impactful systems, and becomes recognized in the field."
            )
            if plan_id:
                plan_ids.append(plan_id)
            
            print(f"[StrategicPlanner] Generated {len(plan_ids)} default strategic plans")
            return plan_ids
            
        except Exception as e:
            print(f"[StrategicPlanner] Error generating default strategies: {e}")
            return plan_ids
    
    def update_plan_progress(self, plan_id: str, progress: float = None):
        """
        Update progress of a strategic plan based on milestone completion.
        """
        try:
            if plan_id not in self.plans:
                return False
            
            plan = self.plans[plan_id]
            
            # Calculate progress from milestones
            if plan.milestones:
                completed = sum(1 for m in plan.milestones if m.status == MilestoneStatus.COMPLETED)
                plan.progress = completed / len(plan.milestones)
            elif progress is not None:
                plan.progress = progress
            
            plan.last_reviewed = datetime.utcnow().isoformat()
            
            with self.lock:
                self._save_plans()
            
            return True
            
        except Exception as e:
            print(f"[StrategicPlanner] Error updating plan progress: {e}")
            return False
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict]:
        """Get detailed status of a strategic plan"""
        if plan_id not in self.plans:
            return None
        
        plan = self.plans[plan_id]
        
        # Calculate milestone status
        milestone_status = {
            "total": len(plan.milestones),
            "completed": sum(1 for m in plan.milestones if m.status == MilestoneStatus.COMPLETED),
            "in_progress": sum(1 for m in plan.milestones if m.status == MilestoneStatus.IN_PROGRESS),
            "blocked": sum(1 for m in plan.milestones if m.status == MilestoneStatus.BLOCKED),
            "not_started": sum(1 for m in plan.milestones if m.status == MilestoneStatus.NOT_STARTED)
        }
        
        # Check for overdue milestones
        now = datetime.utcnow()
        overdue = []
        for m in plan.milestones:
            if m.status not in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
                target = datetime.fromisoformat(m.target_date)
                if target < now:
                    overdue.append({
                        "id": m.id,
                        "title": m.title,
                        "target_date": m.target_date,
                        "days_overdue": (now - target).days
                    })
        
        return {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "type": plan.type.value,
            "horizon": plan.horizon.value,
            "vision": plan.vision,
            "progress": plan.progress,
            "status": plan.status,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "milestone_status": milestone_status,
            "overdue_milestones": overdue,
            "active_risks": [r for r in plan.risks if len(r) > 0],
            "last_reviewed": plan.last_reviewed
        }
    
    def get_all_plans(self) -> List[Dict]:
        """Get all strategic plans with their status"""
        return [self.get_plan_status(pid) for pid in self.plans.keys()]
    
    def generate_weekly_strategy(self) -> Dict:
        """
        Generate a weekly strategy based on long-term plans and current context.
        This bridges long-term planning with weekly execution.
        """
        try:
            ctx = get_live_context()
            now = datetime.utcnow()
            week_end = now + timedelta(days=7)
            
            # Get active plans
            active_plans = [p for p in self.plans.values() if p.status == "active"]
            
            # Identify milestones due this week
            week_milestones = []
            for plan in active_plans:
                for milestone in plan.milestones:
                    target = datetime.fromisoformat(milestone.target_date)
                    if now <= target <= week_end and milestone.status not in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
                        week_milestones.append({
                            "plan_title": plan.title,
                            "milestone": milestone.title,
                            "target_date": milestone.target_date,
                            "priority": plan.type.value  # Use plan type as priority indicator
                        })
            
            # Sort by target date
            week_milestones.sort(key=lambda x: x["target_date"])
            
            # Generate weekly focus areas
            focus_areas = []
            if ctx.stress_level > 6:
                focus_areas.append({
                    "area": "Stress Management",
                    "reason": "High stress detected",
                    "actions": ["Take breaks", "Prioritize tasks", "Reduce non-essential work"]
                })
            
            if ctx.tasks_due_today > 3:
                focus_areas.append({
                    "area": "Task Completion",
                    "reason": "Multiple tasks due",
                    "actions": ["Prioritize by deadline", "Focus on high-impact tasks", "Delegate if possible"]
                })
            
            # Add focus from strategic plans
            for plan in active_plans[:2]:  # Top 2 active plans
                focus_areas.append({
                    "area": plan.title,
                    "reason": f"Strategic priority ({plan.horizon.value})",
                    "actions": [m.title for m in plan.milestones[:2] if m.status != MilestoneStatus.COMPLETED]
                })
            
            return {
                "week_start": now.isoformat(),
                "week_end": week_end.isoformat(),
                "milestones_due": week_milestones,
                "focus_areas": focus_areas,
                "context": {
                    "stress_level": ctx.stress_level,
                    "energy_level": ctx.energy_level,
                    "tasks_due_today": ctx.tasks_due_today,
                    "active_project": ctx.active_project
                }
            }
            
        except Exception as e:
            print(f"[StrategicPlanner] Error generating weekly strategy: {e}")
            return {"error": str(e)}


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_strategic_planner() -> StrategicPlanner:
    """Get the singleton strategic planner instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = StrategicPlanner()
    return _instance
