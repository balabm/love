"""
Fitness Agent - Personal Training & Health Tracking
Tracks workouts, nutrition, recovery, and provides coaching.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from core.settings import get_settings
from core.memory import save_log

SETTINGS = get_settings()
DATA_DIR = Path(__file__).parent.parent / "data"
FITNESS_DB = DATA_DIR / "fitness_log.json"


@dataclass
class Workout:
    date: str
    type: str  # strength, cardio, mobility, sport
    duration_minutes: int
    exercises: List[Dict[str, Any]]
    intensity: str  # low, moderate, high
    notes: str = ""
    recovery_score: Optional[int] = None


@dataclass
class BodyMetrics:
    date: str
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    resting_hr: Optional[int] = None
    sleep_hours: Optional[float] = None
    energy_level: Optional[int] = None  # 1-10


class FitnessAgent:
    """Personal trainer agent for workout tracking and coaching."""
    
    def __init__(self):
        self.data_file = FITNESS_DB
        self._ensure_data_file()
        self.user_name = SETTINGS.user.name
    
    def _ensure_data_file(self):
        """Initialize fitness database if needed."""
        if not self.data_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_data({
                'workouts': [],
                'body_metrics': [],
                'goals': {
                    'weekly_workouts': 4,
                    'target_weight': None,
                    'focus_areas': []
                },
                'streak': {
                    'current': 0,
                    'last_workout': None,
                    'longest': 0
                }
            })
    
    def _load_data(self) -> Dict:
        """Load fitness data."""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {'workouts': [], 'body_metrics': [], 'goals': {}, 'streak': {}}
    
    def _save_data(self, data: Dict):
        """Save fitness data."""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_workout(self, workout_type: str, duration: int, exercises: List[Dict], 
                    intensity: str = "moderate", notes: str = "") -> Dict[str, Any]:
        """Log a workout session."""
        data = self._load_data()
        
        workout = Workout(
            date=datetime.now().isoformat(),
            type=workout_type,
            duration_minutes=duration,
            exercises=exercises,
            intensity=intensity,
            notes=notes
        )
        
        data['workouts'].append(asdict(workout))
        
        # Update streak
        today = datetime.now().date()
        last_workout = data['streak'].get('last_workout')
        
        if last_workout:
            last_date = datetime.fromisoformat(last_workout).date()
            if (today - last_date).days == 1:
                data['streak']['current'] += 1
            elif (today - last_date).days > 1:
                data['streak']['current'] = 1
        else:
            data['streak']['current'] = 1
        
        data['streak']['last_workout'] = workout.date
        data['streak']['longest'] = max(data['streak']['current'], data['streak'].get('longest', 0))
        
        self._save_data(data)
        
        save_log('fitness', {
            'event': 'workout_logged',
            'type': workout_type,
            'duration': duration,
            'streak': data['streak']['current']
        })
        
        return {
            'success': True,
            'workout': asdict(workout),
            'streak': data['streak']['current'],
            'message': self._format_workout_message(workout, data['streak']['current'])
        }
    
    def _format_workout_message(self, workout: Workout, streak: int) -> str:
        """Format workout confirmation for LOVE's voice."""
        if workout.type == "strength":
            emoji = ""
        elif workout.type == "cardio":
            emoji = ""
        elif workout.type == "mobility":
            emoji = ""
        else:
            emoji = ""
        
        if streak >= 7:
            streak_msg = f"{streak} day streak. You're locked in."
        elif streak >= 3:
            streak_msg = f"{streak} days strong. Keep it going."
        else:
            streak_msg = f"Streak started. Day {streak}."
        
        return f"{emoji} Logged {workout.duration_minutes}min {workout.type}. {streak_msg}"
    
    def get_weekly_summary(self) -> Dict[str, Any]:
        """Get this week's fitness summary."""
        data = self._load_data()
        
        week_start = datetime.now() - timedelta(days=7)
        week_workouts = [
            w for w in data['workouts']
            if datetime.fromisoformat(w['date']) > week_start
        ]
        
        # Calculate stats
        total_minutes = sum(w['duration_minutes'] for w in week_workouts)
        by_type = {}
        for w in week_workouts:
            by_type[w['type']] = by_type.get(w['type'], 0) + 1
        
        goal = data['goals'].get('weekly_workouts', 4)
        progress = len(week_workouts) / goal if goal else 0
        
        # Generate insight
        if len(week_workouts) >= goal:
            insight = f"Goal crushed. {len(week_workouts)} workouts this week."
        elif len(week_workouts) >= goal * 0.75:
            insight = f"Close to goal. {len(week_workouts)}/{goal} workouts. One more session?"
        elif len(week_workouts) > 0:
            insight = f"{len(week_workouts)} workouts logged. Room to push more."
        else:
            insight = "No workouts this week. Body needs movement."
        
        return {
            'workouts_this_week': len(week_workouts),
            'goal': goal,
            'progress_percent': round(progress * 100, 1),
            'total_minutes': total_minutes,
            'by_type': by_type,
            'streak': data['streak']['current'],
            'insight': insight,
            'suggestion': self._generate_workout_suggestion(by_type)
        }
    
    def _generate_workout_suggestion(self, by_type: Dict) -> str:
        """Suggest next workout based on balance."""
        if not by_type:
            return "Start with mobility and light cardio to build the habit."
        
        if by_type.get('strength', 0) < 2:
            return "Need more strength work. Try a full-body session."
        elif by_type.get('cardio', 0) < 2:
            return "Cardio is low this week. 20min run or bike would balance it."
        elif by_type.get('mobility', 0) < 1:
            return "Body needs recovery. Yoga or stretching session."
        else:
            return "Good balance. Keep the momentum."
    
    def log_body_metrics(self, **metrics) -> Dict[str, Any]:
        """Log body metrics and health data."""
        data = self._load_data()
        
        entry = BodyMetrics(
            date=datetime.now().isoformat(),
            **{k: v for k, v in metrics.items() if k in BodyMetrics.__dataclass_fields__}
        )
        
        data['body_metrics'].append(asdict(entry))
        self._save_data(data)
        
        # Analyze trends
        if len(data['body_metrics']) >= 2:
            return self._analyze_trends(data['body_metrics'])
        
        return {'success': True, 'message': 'Metrics logged. Building baseline.'}
    
    def _analyze_trends(self, metrics: List[Dict]) -> Dict[str, Any]:
        """Analyze fitness trends over time."""
        recent = metrics[-7:]  # Last 7 entries
        
        # Calculate sleep average
        sleep_values = [m.get('sleep_hours') for m in recent if m.get('sleep_hours')]
        avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else None
        
        insights = []
        if avg_sleep:
            if avg_sleep < 6:
                insights.append(f"Sleep averaging {avg_sleep:.1f}h — recovery will suffer.")
            elif avg_sleep > 7.5:
                insights.append(f"Sleep solid at {avg_sleep:.1f}h — good recovery base.")
        
        return {
            'success': True,
            'insights': insights,
            'avg_sleep': avg_sleep,
            'entries_count': len(metrics)
        }
    
    def suggest_recovery(self) -> Dict[str, Any]:
        """Suggest recovery activities based on recent training."""
        data = self._load_data()
        recent_workouts = data['workouts'][-3:]
        
        high_intensity = sum(1 for w in recent_workouts if w.get('intensity') == 'high')
        
        if high_intensity >= 2:
            return {
                'needs_recovery': True,
                'suggestion': 'Two hard sessions back-to-back. Active recovery today — light walk, stretching, foam rolling.',
                'priority': 'high'
            }
        elif len(recent_workouts) >= 3:
            return {
                'needs_recovery': True,
                'suggestion': 'Three sessions in a row. Take a rest day or easy mobility work.',
                'priority': 'medium'
            }
        
        return {
            'needs_recovery': False,
            'suggestion': 'Recovery status good. Ready for next session.',
            'priority': 'low'
        }


# Public API functions
def get_fitness_status() -> Dict[str, Any]:
    """Get current fitness status for LOVE's awareness."""
    agent = FitnessAgent()
    return agent.get_weekly_summary()


def log_workout(workout_type: str, duration: int, exercises: List[Dict], 
                intensity: str = "moderate", notes: str = "") -> Dict[str, Any]:
    """Log a workout session."""
    agent = FitnessAgent()
    return agent.log_workout(workout_type, duration, exercises, intensity, notes)


def get_fitness_overview() -> Dict[str, Any]:
    """Get fitness overview for gap detection and meta-evolution pressure."""
    agent = FitnessAgent()
    data = agent._load_data()
    workouts = data.get('workouts', [])
    metrics = data.get('body_metrics', [])
    
    # Recent activity level: workouts in last 7 days / 7
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=7)
    recent_workouts = [w for w in workouts if datetime.fromisoformat(w['date']) > cutoff] if workouts else []
    activity_level = min(1.0, len(recent_workouts) / 7.0)
    
    # Sleep quality from latest metric
    sleep_quality = 0.5
    if metrics:
        latest = metrics[-1]
        sleep_hours = latest.get('sleep_hours', 0)
        if sleep_hours >= 7.5:
            sleep_quality = 0.9
        elif sleep_hours >= 6:
            sleep_quality = 0.6
        elif sleep_hours >= 4:
            sleep_quality = 0.3
        else:
            sleep_quality = 0.1
    
    return {
        "recent_activity_level": activity_level,
        "sleep_quality": sleep_quality,
        "total_workouts": len(workouts),
        "total_metrics": len(metrics),
        "streak": data.get('streak', {}).get('current', 0),
    }


def suggest_next_workout() -> str:
    """Get suggestion for next workout."""
    agent = FitnessAgent()
    summary = agent.get_weekly_summary()
    return summary.get('suggestion', 'Move your body today.')
