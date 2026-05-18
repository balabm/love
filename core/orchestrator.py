"""
Neural Orchestrator - Master Intelligence Hub
Cross-domain reasoning engine that connects all LOVE modules.
Detects life patterns across agents and generates proactive interventions.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from threading import Lock
import time

from core.settings import get_settings
from core.memory import save_log

SETTINGS = get_settings()
DATA_DIR = Path(__file__).parent.parent / "data"
ORCHESTRATOR_LOG = DATA_DIR / "orchestrator_log.json"


@dataclass
class Intervention:
    """A cross-domain intervention LOVE wants to make."""
    id: str
    type: str  # 'block', 'suggest', 'alert', 'celebrate', 'nudge'
    priority: str  # 'critical', 'high', 'medium', 'low'
    message: str
    action: Optional[str] = None
    expires_at: Optional[str] = None
    triggered_by: List[str] = field(default_factory=list)
    accepted: bool = False
    dismissed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CrossDomainPattern:
    """A detected pattern spanning multiple life domains."""
    name: str
    description: str
    confidence: float  # 0.0 to 1.0
    affected_domains: List[str]
    severity: str  # 'critical', 'warning', 'info', 'positive'
    suggestion: str
    triggered_at: str = field(default_factory=lambda: datetime.now().isoformat())


class NeuralOrchestrator:
    """
    The Brain of Brains. Monitors all agents and performs cross-domain reasoning.
    
    Detects patterns like:
    - High stress + market volatility → Block trades, suggest walk
    - Work limit reached + deadline → Suggest sleep protocol
    - Low energy + heavy tasks → Suggest lighter work
    - No workout + good mood → Suggest workout
    - Poor sleep + high stress → Wellness alert
    """
    
    def __init__(self):
        self.data_file = ORCHESTRATOR_LOG
        self._ensure_data_file()
        self.interventions: List[Intervention] = []
        self.patterns: List[CrossDomainPattern] = []
        self._lock = Lock()
        self._callbacks: List[Callable] = []
    
    def _ensure_data_file(self):
        """Initialize orchestrator log."""
        if not self.data_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_data({
                'interventions': [],
                'patterns_detected': [],
                'unified_states': [],
                'cross_domain_rules': self._get_default_rules()
            })
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {'interventions': [], 'patterns_detected': [], 'unified_states': []}
    
    def _save_data(self, data: Dict):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _get_default_rules(self) -> List[Dict]:
        """Default cross-domain reasoning rules."""
        return [
            {
                'name': 'stress_market_lock',
                'domains': ['wellness', 'finance'],
                'condition': 'stress >= 7 AND market_volatility > 0.03',
                'action': 'block_trades',
                'message': "You're stressed and the market is volatile. I've locked the trade button for 2 hours. Go for a 10-minute walk.",
                'priority': 'high'
            },
            {
                'name': 'work_deadline_sleep',
                'domains': ['guardian', 'tasks'],
                'condition': 'hours_worked >= limit AND has_critical_deadline',
                'action': 'suggest_sleep',
                'message': "You've hit your work limit but have a critical deadline. Sleep now, you'll be sharper in the morning. I've deferred non-urgent tasks.",
                'priority': 'critical'
            },
            {
                'name': 'low_energy_heavy_tasks',
                'domains': ['wellness', 'tasks'],
                'condition': 'energy <= 3 AND has_deep_work_scheduled',
                'action': 'reschedule_tasks',
                'message': "Energy is low. I've moved your deep work to tomorrow morning when you're usually sharper. Focus on admin tasks today.",
                'priority': 'medium'
            },
            {
                'name': 'good_mood_no_workout',
                'domains': ['wellness', 'fitness'],
                'condition': 'mood >= 7 AND no_workout_today',
                'action': 'suggest_workout',
                'message': "You're in a great mood. Channel it into a workout — you'll feel even better after.",
                'priority': 'low'
            },
            {
                'name': 'poor_sleep_stress_spiral',
                'domains': ['wellness', 'fitness'],
                'condition': 'sleep < 5 AND stress >= 6',
                'action': 'wellness_alert',
                'message': "Sleep is poor and stress is climbing. This is a spiral. Tonight: no screens after 9pm, 10-min meditation, early bedtime.",
                'priority': 'high'
            },
            {
                'name': 'learning_streak_fitness_drop',
                'domains': ['learning', 'fitness'],
                'condition': 'learning_streak >= 5 AND workouts_this_week < 2',
                'action': 'movement_break',
                'message': "5 days of learning, but body needs movement. Take a 20-min walk between study sessions.",
                'priority': 'medium'
            },
            {
                'name': 'market_opportunity_focused',
                'domains': ['finance', 'wellness'],
                'condition': 'market_opportunity AND focus_score >= 7',
                'action': 'alert_opportunity',
                'message': "You're dialed in and there's a trade setup. 15 minutes, set your limits, then get back to flow.",
                'priority': 'medium'
            },
            {
                'name': 'work_marathon_no_breaks',
                'domains': ['guardian', 'wellness'],
                'condition': 'hours_since_break > 2 AND hours_worked > 4',
                'action': 'force_break',
                'message': "You've been grinding for {hours} hours straight. 5-minute stretch break. Eyes off the screen.",
                'priority': 'medium'
            }
        ]
    
    def collect_agent_states(self) -> Dict[str, Any]:
        """Gather current state from all agents."""
        states = {}
        
        # Fitness
        try:
            from agents.fitness_agent import get_fitness_status
            states['fitness'] = get_fitness_status()
        except Exception as e:
            states['fitness'] = {'error': str(e)}
        
        # Learning
        try:
            from agents.learning_agent import get_learning_progress
            states['learning'] = get_learning_progress()
        except Exception as e:
            states['learning'] = {'error': str(e)}
        
        # Wellness
        try:
            from agents.emotional_agent import get_emotional_insights
            states['wellness'] = get_emotional_insights(days=7)
        except Exception as e:
            states['wellness'] = {'error': str(e)}
        
        # Tasks
        try:
            from agents.task_agent import get_task_overview
            states['tasks'] = get_task_overview()
        except Exception as e:
            states['tasks'] = {'error': str(e)}
        
        # Guardian
        try:
            from tools.guardian import check_work_status
            states['guardian'] = check_work_status()
        except Exception as e:
            states['guardian'] = {'error': str(e)}
        
        # Finance
        try:
            from tools.finance import AlphaSentinel
            sentinel = AlphaSentinel()
            # Get quick portfolio snapshot
            states['finance'] = {'status': 'monitoring'}
        except Exception as e:
            states['finance'] = {'error': str(e)}
        
        return states
    
    def detect_patterns(self, states: Dict[str, Any]) -> List[CrossDomainPattern]:
        """Analyze cross-domain patterns from agent states."""
        patterns = []
        
        wellness = states.get('wellness', {})
        fitness = states.get('fitness', {})
        tasks = states.get('tasks', {})
        guardian = states.get('guardian', {})
        learning = states.get('learning', {})
        finance = states.get('finance', {})
        
        # Safely extract numeric values (handle None)
        stress = (wellness.get('avg_stress') or 0) if isinstance(wellness, dict) else 0
        mood = (wellness.get('avg_mood') or 5) if isinstance(wellness, dict) else 5
        energy = (wellness.get('avg_energy') or 5) if isinstance(wellness, dict) else 5
        hours_worked = (guardian.get('hours_today') or 0) if isinstance(guardian, dict) else 0
        workouts = (fitness.get('workouts_this_week') or 0) if isinstance(fitness, dict) else 0
        learning_streak = (learning.get('current_streak') or 0) if isinstance(learning, dict) else 0
        work_limit = SETTINGS.work.daily_limit_hours
        
        # Pattern 1: Stress + Market Volatility
        if stress >= 7:
            patterns.append(CrossDomainPattern(
                name='stress_market_lock',
                description=f'Stress at {stress}/10 with active market monitoring',
                confidence=0.85,
                affected_domains=['wellness', 'finance'],
                severity='warning',
                suggestion="Lock trading for 2 hours. Go for a walk."
            ))
        
        # Pattern 2: Work limit + Critical deadline
        has_critical = any(
            t.get('priority') == 'critical' 
            for t in tasks.get('due_soon', []) if isinstance(t, dict)
        )
        
        if hours_worked >= work_limit and has_critical:
            patterns.append(CrossDomainPattern(
                name='work_deadline_sleep',
                description=f'Work limit reached ({hours_worked:.1f}h) with critical deadline',
                confidence=0.9,
                affected_domains=['guardian', 'tasks'],
                severity='critical',
                suggestion="Sleep now, tackle deadline fresh in morning."
            ))
        
        # Pattern 3: Low energy + Deep work
        if energy <= 3:
            patterns.append(CrossDomainPattern(
                name='low_energy_heavy_tasks',
                description=f'Low energy ({energy}/10) with active tasks',
                confidence=0.8,
                affected_domains=['wellness', 'tasks'],
                severity='warning',
                suggestion="Reschedule deep work. Do admin tasks today."
            ))
        
        # Pattern 4: Good mood, no workout
        if mood >= 7 and workouts == 0:
            patterns.append(CrossDomainPattern(
                name='good_mood_no_workout',
                description='Positive mood but no workouts this week',
                confidence=0.7,
                affected_domains=['wellness', 'fitness'],
                severity='info',
                suggestion="Channel good mood into a workout session."
            ))
        
        # Pattern 5: Learning streak + fitness neglect
        if learning_streak >= 5 and workouts < 2:
            patterns.append(CrossDomainPattern(
                name='learning_streak_fitness_drop',
                description=f'{learning_streak}-day learning streak with low fitness activity',
                confidence=0.75,
                affected_domains=['learning', 'fitness'],
                severity='warning',
                suggestion="Take a movement break between study sessions."
            ))
        
        # Pattern 6: Too long without break
        if hours_worked > 4:
            patterns.append(CrossDomainPattern(
                name='work_marathon_no_breaks',
                description=f'{hours_worked:.1f} hours worked without enforced break',
                confidence=0.8,
                affected_domains=['guardian', 'wellness'],
                severity='warning',
                suggestion=f"Take a 5-minute break. You've been at it for {hours_worked:.1f} hours."
            ))
        
        # Pattern 7: Balanced life (positive)
        if (mood >= 7 and energy >= 6 and workouts >= 2 and 
            learning_streak >= 3 and hours_worked < work_limit * 0.8):
            patterns.append(CrossDomainPattern(
                name='balanced_life',
                description='Multiple domains showing positive momentum',
                confidence=0.9,
                affected_domains=['wellness', 'fitness', 'learning', 'guardian'],
                severity='positive',
                suggestion="You're firing on all cylinders. This is your optimal state. Keep the habits."
            ))
        
        self.patterns = patterns
        return patterns
    
    def generate_interventions(self, patterns: List[CrossDomainPattern]) -> List[Intervention]:
        """Convert patterns into actionable interventions."""
        interventions = []
        
        for pattern in patterns:
            # Skip if already generated this pattern today
            if self._pattern_already_intervened(pattern.name):
                continue
            
            intervention = None
            
            if pattern.name == 'stress_market_lock':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='block',
                    priority='high',
                    message="You're stressed and the market is volatile. I've locked the trade button for 2 hours. Go for a 10-minute walk.",
                    action='pause_trading',
                    triggered_by=['wellness', 'finance'],
                    expires_at=(datetime.now() + timedelta(hours=2)).isoformat()
                )
            
            elif pattern.name == 'work_deadline_sleep':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='suggest',
                    priority='critical',
                    message="You've hit your work limit but have a critical deadline. Sleep now, you'll be sharper in the morning. I've deferred non-urgent tasks.",
                    action='sleep_protocol',
                    triggered_by=['guardian', 'tasks']
                )
            
            elif pattern.name == 'low_energy_heavy_tasks':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='reschedule',
                    priority='medium',
                    message="Energy is low. I've moved your deep work to tomorrow morning when you're usually sharper. Focus on admin tasks today.",
                    action='reschedule_tasks',
                    triggered_by=['wellness', 'tasks']
                )
            
            elif pattern.name == 'good_mood_no_workout':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='suggest',
                    priority='low',
                    message="You're in a great mood. Channel it into a workout — you'll feel even better after.",
                    action='suggest_workout',
                    triggered_by=['wellness', 'fitness']
                )
            
            elif pattern.name == 'learning_streak_fitness_drop':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='nudge',
                    priority='medium',
                    message="5 days of learning, but body needs movement. Take a 20-min walk between study sessions.",
                    action='movement_break',
                    triggered_by=['learning', 'fitness']
                )
            
            elif pattern.name == 'work_marathon_no_breaks':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='force',
                    priority='medium',
                    message=f"You've been grinding for hours straight. 5-minute stretch break. Eyes off the screen.",
                    action='force_break',
                    triggered_by=['guardian', 'wellness']
                )
            
            elif pattern.name == 'balanced_life':
                intervention = Intervention(
                    id=f"int_{pattern.name}_{datetime.now().strftime('%H%M')}",
                    type='celebrate',
                    priority='low',
                    message="You're firing on all cylinders. This is your optimal state. Keep the habits.",
                    triggered_by=['wellness', 'fitness', 'learning']
                )
            
            if intervention:
                interventions.append(intervention)
                self._log_intervention(intervention)
        
        self.interventions = interventions
        return interventions
    
    def _pattern_already_intervened(self, pattern_name: str) -> bool:
        """Check if we already generated an intervention for this pattern today."""
        data = self._load_data()
        today = datetime.now().date().isoformat()
        
        for inv in data.get('interventions', []):
            if (inv.get('id', '').startswith(f"int_{pattern_name}") and
                inv.get('created_at', '').startswith(today)):
                return True
        return False
    
    def _log_intervention(self, intervention: Intervention):
        """Log intervention to file."""
        data = self._load_data()
        data['interventions'].append({
            'id': intervention.id,
            'type': intervention.type,
            'priority': intervention.priority,
            'message': intervention.message,
            'action': intervention.action,
            'triggered_by': intervention.triggered_by,
            'created_at': intervention.created_at
        })
        self._save_data(data)
        
        save_log('orchestrator', {
            'event': 'intervention_generated',
            'intervention_id': intervention.id,
            'type': intervention.type,
            'priority': intervention.priority
        })
    
    def get_unified_state(self) -> Dict[str, Any]:
        """
        Merge all agent states into a single 'Life Status' object.
        This is the single source of truth for the Dashboard.
        """
        states = self.collect_agent_states()
        patterns = self.detect_patterns(states)
        interventions = self.generate_interventions(patterns)
        
        # Calculate Life Score (0-100)
        life_score = self._calculate_life_score(states)
        
        # Determine overall state
        critical_count = sum(1 for p in patterns if p.severity == 'critical')
        warning_count = sum(1 for p in patterns if p.severity == 'warning')
        positive_count = sum(1 for p in patterns if p.severity == 'positive')
        
        if critical_count > 0:
            overall_state = 'critical'
            state_message = f'{critical_count} critical issue(s) detected. Immediate attention needed.'
        elif warning_count > 0:
            overall_state = 'attention'
            state_message = f'{warning_count} area(s) need attention. Review interventions.'
        elif positive_count > 0:
            overall_state = 'optimal'
            state_message = 'Life is in balance. Keep the momentum.'
        else:
            overall_state = 'steady'
            state_message = 'Steady state. Nothing urgent, but always room to improve.'
        
        # Active interventions
        active = [i for i in interventions if not i.dismissed and not i.accepted]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_state': overall_state,
            'state_message': state_message,
            'life_score': life_score,
            'score_breakdown': self._get_score_breakdown(states),
            'domains': states,
            'patterns': [
                {
                    'name': p.name,
                    'description': p.description,
                    'severity': p.severity,
                    'confidence': p.confidence,
                    'suggestion': p.suggestion
                }
                for p in patterns
            ],
            'active_interventions': [
                {
                    'id': i.id,
                    'type': i.type,
                    'priority': i.priority,
                    'message': i.message,
                    'action': i.action,
                    'expires_at': i.expires_at
                }
                for i in active
            ],
            'recommendations': self._generate_recommendations(states, patterns)
        }
    
    def _calculate_life_score(self, states: Dict[str, Any]) -> int:
        """Calculate overall life score 0-100."""
        score = 50  # Baseline
        
        # Wellness (30 points)
        wellness = states.get('wellness', {})
        if isinstance(wellness, dict):
            mood = wellness.get('avg_mood') or 5
            energy = wellness.get('avg_energy') or 5
            stress = wellness.get('avg_stress') or 5
            wellness_score = (mood * 2 + energy * 2 + (10 - stress)) / 5 * 10
            score += min(30, max(0, wellness_score - 15))
        
        # Fitness (20 points)
        fitness = states.get('fitness', {})
        if isinstance(fitness, dict):
            progress = fitness.get('progress_percent', 0)
            streak = fitness.get('streak', 0)
            fitness_score = min(20, progress * 0.2 + streak * 2)
            score += fitness_score
        
        # Learning (15 points)
        learning = states.get('learning', {})
        if isinstance(learning, dict):
            hours = learning.get('weekly_hours', 0)
            streak = learning.get('current_streak', 0)
            learning_score = min(15, hours * 2 + streak * 1.5)
            score += learning_score
        
        # Tasks (15 points)
        tasks = states.get('tasks', {})
        if isinstance(tasks, dict):
            active = tasks.get('active_count', 0)
            due_soon = len(tasks.get('due_soon', []))
            if active < 10 and due_soon < 3:
                score += 15
            elif active < 15:
                score += 10
            else:
                score += 5
        
        # Guardian/Work balance (20 points)
        guardian = states.get('guardian', {})
        if isinstance(guardian, dict):
            hours = guardian.get('hours_today', 0)
            limit = SETTINGS.work.daily_limit_hours
            if hours < limit * 0.8:
                score += 20
            elif hours <= limit:
                score += 15
            else:
                score += 5
        
        return max(0, min(100, int(score)))
    
    def _get_score_breakdown(self, states: Dict[str, Any]) -> Dict[str, int]:
        """Get per-domain score contributions."""
        breakdown = {}
        
        wellness = states.get('wellness', {})
        if isinstance(wellness, dict):
            mood = wellness.get('avg_mood') or 5
            energy = wellness.get('avg_energy') or 5
            stress = wellness.get('avg_stress') or 5
            breakdown['wellness'] = int(max(0, (mood * 2 + energy * 2 + (10 - stress)) / 5 * 10 - 15))
        
        fitness = states.get('fitness', {})
        if isinstance(fitness, dict):
            progress = fitness.get('progress_percent', 0)
            streak = fitness.get('streak', 0)
            breakdown['fitness'] = int(min(20, progress * 0.2 + streak * 2))
        
        learning = states.get('learning', {})
        if isinstance(learning, dict):
            hours = learning.get('weekly_hours', 0)
            streak = learning.get('current_streak', 0)
            breakdown['learning'] = int(min(15, hours * 2 + streak * 1.5))
        
        tasks = states.get('tasks', {})
        if isinstance(tasks, dict):
            active = tasks.get('active_count', 0)
            breakdown['tasks'] = 15 if active < 10 else 10 if active < 15 else 5
        
        guardian = states.get('guardian', {})
        if isinstance(guardian, dict):
            hours = guardian.get('hours_today', 0)
            limit = SETTINGS.work.daily_limit_hours
            breakdown['work_life'] = 20 if hours < limit * 0.8 else 15 if hours <= limit else 5
        
        return breakdown
    
    def _generate_recommendations(self, states: Dict, patterns: List[CrossDomainPattern]) -> List[str]:
        """Generate prioritized recommendations."""
        recs = []
        
        # Sort by severity
        for p in sorted(patterns, key=lambda x: {'critical': 0, 'warning': 1, 'info': 2, 'positive': 3}.get(x.severity, 2)):
            if p.severity in ['critical', 'warning']:
                recs.append(f"[{p.severity.upper()}] {p.suggestion}")
        
        # Add general recommendations
        fitness = states.get('fitness', {})
        if isinstance(fitness, dict) and fitness.get('workouts_this_week', 0) == 0:
            recs.append("[INFO] No workouts this week. Even 15 minutes of movement helps.")
        
        learning = states.get('learning', {})
        if isinstance(learning, dict) and learning.get('weekly_hours', 0) < 2:
            recs.append("[INFO] Learning under 2 hours this week. Dedicate 30 minutes to a skill.")
        
        return recs[:5]  # Top 5
    
    def run_cycle(self) -> Dict[str, Any]:
        """Run one full orchestration cycle."""
        return self.get_unified_state()
    
    def dismiss_intervention(self, intervention_id: str) -> bool:
        """Dismiss an intervention."""
        for i in self.interventions:
            if i.id == intervention_id:
                i.dismissed = True
                return True
        return False
    
    def accept_intervention(self, intervention_id: str) -> bool:
        """Accept/mark an intervention as done."""
        for i in self.interventions:
            if i.id == intervention_id:
                i.accepted = True
                save_log('orchestrator', {
                    'event': 'intervention_accepted',
                    'intervention_id': intervention_id
                })
                return True
        return False


# Singleton instance
_orchestrator = None

def get_orchestrator() -> NeuralOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NeuralOrchestrator()
    return _orchestrator


def get_unified_state() -> Dict[str, Any]:
    """Public API: Get unified life state."""
    return get_orchestrator().get_unified_state()


def run_orchestrator_cycle() -> Dict[str, Any]:
    """Public API: Run one orchestration cycle."""
    return get_orchestrator().run_cycle()


def get_active_interventions() -> List[Dict[str, Any]]:
    """Get currently active interventions."""
    orch = get_orchestrator()
    state = orch.get_unified_state()
    return state.get('active_interventions', [])
