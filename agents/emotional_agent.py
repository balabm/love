"""
Emotional Agent - Mood Tracking & Wellness Insights
Tracks emotional patterns, provides insights, and suggests interventions.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
from core.settings import get_settings
from core.memory import save_log

SETTINGS = get_settings()
DATA_DIR = Path(__file__).parent.parent / "data"
EMOTIONAL_DB = DATA_DIR / "emotional_log.json"


@dataclass
class MoodEntry:
    timestamp: str
    mood_score: int  # 1-10
    energy_level: int  # 1-10
    stress_level: int  # 1-10
    emotions: List[str]  # happy, anxious, focused, tired, excited, etc.
    context: str = ""  # what was happening
    notes: str = ""
    triggers: List[str] = None
    
    def __post_init__(self):
        if self.triggers is None:
            self.triggers = []


@dataclass
class WellnessInsight:
    date: str
    insight_type: str  # pattern, alert, positive, suggestion
    message: str
    confidence: float
    recommended_action: Optional[str] = None


class EmotionalAgent:
    """Emotional wellness tracker and insights provider."""
    
    def __init__(self):
        self.data_file = EMOTIONAL_DB
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        if not self.data_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_data({
                'mood_entries': [],
                'insights': [],
                'patterns': {},
                'interventions': []
            })
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {'mood_entries': [], 'insights': [], 'patterns': {}, 'interventions': []}
    
    def _save_data(self, data: Dict):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_mood(self, mood_score: int, energy: int, stress: int, 
                 emotions: List[str], context: str = "", notes: str = "") -> Dict[str, Any]:
        """Log a mood entry."""
        data = self._load_data()
        
        entry = MoodEntry(
            timestamp=datetime.now().isoformat(),
            mood_score=mood_score,
            energy_level=energy,
            stress_level=stress,
            emotions=emotions,
            context=context,
            notes=notes
        )
        
        data['mood_entries'].append(asdict(entry))
        
        # Generate immediate insight
        insight = self._generate_immediate_insight(entry)
        if insight:
            data['insights'].append(asdict(insight))
        
        self._save_data(data)
        
        save_log('emotional', {
            'event': 'mood_logged',
            'mood': mood_score,
            'energy': energy,
            'stress': stress,
            'emotions': emotions
        })
        
        return {
            'success': True,
            'entry': asdict(entry),
            'insight': asdict(insight) if insight else None,
            'message': self._format_mood_response(entry)
        }
    
    def _format_mood_response(self, entry: MoodEntry) -> str:
        """Format mood confirmation with empathy."""
        if entry.mood_score >= 8:
            base = f"Mood at {entry.mood_score}/10. Good energy."
        elif entry.mood_score >= 5:
            if entry.stress_level >= 7:
                base = f"Mood okay at {entry.mood_score}/10, but stress is high. What's weighing on you?"
            else:
                base = f"Mood at {entry.mood_score}/10. Steady state."
        else:
            if entry.energy_level <= 3:
                base = f"Low energy and mood today. Be gentle with yourself. Rest is productive too."
            else:
                base = f"Mood at {entry.mood_score}/10. That's hard. Want to talk about what's going on?"
        
        return base
    
    def _generate_immediate_insight(self, entry: MoodEntry) -> Optional[WellnessInsight]:
        """Generate insight based on single entry."""
        if entry.stress_level >= 8 and entry.mood_score <= 4:
            return WellnessInsight(
                date=datetime.now().isoformat(),
                insight_type='alert',
                message='High stress and low mood detected. Consider taking a break or doing something restorative.',
                confidence=0.9,
                recommended_action='Take a 10-minute walk, do breathing exercises, or step away from work.'
            )
        
        if entry.energy_level <= 3 and entry.stress_level >= 7:
            return WellnessInsight(
                date=datetime.now().isoformat(),
                insight_type='alert',
                message='Burnout indicators: low energy + high stress. Priority is recovery, not productivity.',
                confidence=0.85,
                recommended_action='Cancel non-essential tasks. Focus on sleep, nutrition, and rest.'
            )
        
        return None
    
    def get_emotional_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get emotional wellness summary for period."""
        data = self._load_data()
        
        cutoff = datetime.now() - timedelta(days=days)
        entries = [
            e for e in data['mood_entries']
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        if not entries:
            return {
                'period_days': days,
                'entries_count': 0,
                'avg_mood': None,
                'avg_energy': None,
                'avg_stress': None,
                'trend': 'insufficient_data',
                'message': 'No mood data this week. Want to check in?'
            }
        
        # Calculate averages
        avg_mood = sum(e['mood_score'] for e in entries) / len(entries)
        avg_energy = sum(e['energy_level'] for e in entries) / len(entries)
        avg_stress = sum(e['stress_level'] for e in entries) / len(entries)
        
        # Detect trend
        if len(entries) >= 3:
            recent = entries[-3:]
            older = entries[:3] if len(entries) >= 6 else entries[:len(entries)//2]
            
            recent_mood = sum(e['mood_score'] for e in recent) / len(recent)
            older_mood = sum(e['mood_score'] for e in older) / len(older)
            
            if recent_mood > older_mood + 0.5:
                trend = 'improving'
                trend_msg = 'Mood trending up. Momentum is building.'
            elif recent_mood < older_mood - 0.5:
                trend = 'declining'
                trend_msg = f'Mood trending down over the last {days} days. Worth paying attention to.'
            else:
                trend = 'stable'
                trend_msg = 'Emotional baseline steady.'
        else:
            trend = 'insufficient_data'
            trend_msg = 'Logging more entries will help me spot patterns.'
        
        # Common emotions
        emotion_counts = defaultdict(int)
        for e in entries:
            for emotion in e.get('emotions', []):
                emotion_counts[emotion] += 1
        
        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Generate insight
        if avg_stress >= 7:
            insight = f"High stress averaging {avg_stress:.1f}/10. Body is in fight-or-flight mode."
        elif avg_mood >= 7 and avg_energy >= 6:
            insight = f"Strong week. Mood {avg_mood:.1f}/10, energy {avg_energy:.1f}/10. Keep the habits that got you here."
        elif avg_mood <= 5:
            insight = f"Tough stretch emotionally. Mood averaging {avg_mood:.1f}/10. Self-compassion mode activated."
        else:
            insight = f"Emotional baseline: mood {avg_mood:.1f}/10, energy {avg_energy:.1f}/10, stress {avg_stress:.1f}/10."
        
        return {
            'period_days': days,
            'entries_count': len(entries),
            'avg_mood': round(avg_mood, 1),
            'avg_energy': round(avg_energy, 1),
            'avg_stress': round(avg_stress, 1),
            'trend': trend,
            'trend_message': trend_msg,
            'top_emotions': [e[0] for e in top_emotions],
            'insight': insight,
            'suggestion': self._generate_wellness_suggestion(avg_mood, avg_energy, avg_stress, trend)
        }
    
    def _generate_wellness_suggestion(self, mood: float, energy: float, stress: float, trend: str) -> str:
        """Generate wellness suggestion based on metrics."""
        if stress >= 7:
            return "Stress is primary concern. Try 4-7-8 breathing or a 20min walk."
        elif energy <= 4:
            return "Low energy zone. Check sleep, nutrition, and movement."
        elif mood <= 5 and trend == 'declining':
            return "Consider talking to someone. This pattern matters."
        elif mood >= 7 and energy >= 6:
            return "You're in a good window. Use this energy for important work."
        else:
            return "Steady state. Small actions: 10min walk, good meal, early bedtime."
    
    def detect_patterns(self) -> List[Dict[str, Any]]:
        """Detect emotional patterns from historical data."""
        data = self._load_data()
        
        if len(data['mood_entries']) < 14:
            return [{'type': 'insufficient_data', 'message': 'Need more data to detect patterns.'}]
        
        patterns = []
        
        # Day of week patterns
        dow_moods = defaultdict(list)
        for e in data['mood_entries']:
            dt = datetime.fromisoformat(e['timestamp'])
            dow_moods[dt.strftime('%A')].append(e['mood_score'])
        
        lowest_dow = min(dow_moods.items(), key=lambda x: sum(x[1])/len(x[1]))
        highest_dow = max(dow_moods.items(), key=lambda x: sum(x[1])/len(x[1]))
        
        if len(dow_moods) >= 5:
            patterns.append({
                'type': 'day_of_week',
                'description': f"Lowest mood tends to be on {lowest_dow[0]}s.",
                'recommendation': f"Plan lighter tasks on {lowest_dow[0]}s. Extra self-care that day."
            })
        
        # Time of day patterns
        hour_moods = defaultdict(list)
        for e in data['mood_entries']:
            dt = datetime.fromisoformat(e['timestamp'])
            hour_moods[dt.hour].append(e['mood_score'])
        
        if hour_moods:
            best_hour = max(hour_moods.items(), key=lambda x: sum(x[1])/len(x[1]))
            patterns.append({
                'type': 'time_of_day',
                'description': f"Peak mood typically at {best_hour[0]}:00.",
                'recommendation': "Schedule important decisions and creative work during peak mood hours."
            })
        
        return patterns
    
    def should_check_in(self) -> Dict[str, Any]:
        """Determine if LOVE should proactively check in."""
        data = self._load_data()
        
        if not data['mood_entries']:
            return {'should_check_in': True, 'reason': 'no_data', 'message': 'First check-in. How are you feeling?'}
        
        last_entry = data['mood_entries'][-1]
        last_time = datetime.fromisoformat(last_entry['timestamp'])
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        
        # Check in if it's been over 24 hours
        if hours_since >= 24:
            return {
                'should_check_in': True, 
                'reason': 'time_elapsed',
                'hours_since': hours_since,
                'message': f"Haven't checked in for {int(hours_since)} hours. Quick mood check?"
            }
        
        # Check in if last entry was concerning
        if last_entry['mood_score'] <= 4 or last_entry['stress_level'] >= 8:
            return {
                'should_check_in': True,
                'reason': 'follow_up',
                'message': 'Following up from yesterday. How are you feeling now?'
            }
        
        return {'should_check_in': False}


# Public API functions
def log_mood(mood: int, energy: int, stress: int, emotions: List[str], 
             **kwargs) -> Dict[str, Any]:
    """Log mood entry."""
    agent = EmotionalAgent()
    return agent.log_mood(mood, energy, stress, emotions, **kwargs)


def get_emotional_insights(days: int = 7) -> Dict[str, Any]:
    """Get emotional insights."""
    agent = EmotionalAgent()
    return agent.get_emotional_summary(days)


def check_wellness_checkin() -> Dict[str, Any]:
    """Check if wellness check-in is needed."""
    agent = EmotionalAgent()
    return agent.should_check_in()
