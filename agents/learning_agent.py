"""
Learning Agent - Knowledge Management & Study Tracking
Implements spaced repetition, study sessions, and skill development.
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
LEARNING_DB = DATA_DIR / "learning_log.json"


@dataclass
class StudyMaterial:
    id: str
    title: str
    category: str  # book, course, article, video, podcast
    source: str
    url: Optional[str] = None
    difficulty: str = "intermediate"  # beginner, intermediate, advanced
    estimated_hours: float = 0
    tags: List[str] = None
    added_date: str = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.added_date is None:
            self.added_date = datetime.now().isoformat()


@dataclass
class StudySession:
    material_id: str
    start_time: str
    duration_minutes: int
    notes: str = ""
    comprehension: int = 5  # 1-10
    retention_confidence: int = 5  # 1-10


@dataclass
class ReviewItem:
    """For spaced repetition tracking."""
    material_id: str
    concept: str
    last_reviewed: str
    next_review: str
    interval_days: int = 1
    ease_factor: float = 2.5
    repetitions: int = 0


class LearningAgent:
    """Personal learning coach for skill development."""
    
    def __init__(self):
        self.data_file = LEARNING_DB
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Initialize learning database."""
        if not self.data_file.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            self._save_data({
                'materials': [],
                'study_sessions': [],
                'review_queue': [],
                'skills': {},
                'goals': []
            })
    
    def _load_data(self) -> Dict:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except:
            return {'materials': [], 'study_sessions': [], 'review_queue': [], 'skills': {}, 'goals': []}
    
    def _save_data(self, data: Dict):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_material(self, title: str, category: str, source: str, 
                     **kwargs) -> Dict[str, Any]:
        """Add learning material to track."""
        data = self._load_data()
        
        material = StudyMaterial(
            id=f"mat_{len(data['materials']) + 1}_{datetime.now().strftime('%Y%m%d')}",
            title=title,
            category=category,
            source=source,
            **kwargs
        )
        
        data['materials'].append(asdict(material))
        self._save_data(data)
        
        return {
            'success': True,
            'material': asdict(material),
            'message': f"Added '{title}' to your learning queue."
        }
    
    def log_study_session(self, material_id: str, duration: int, 
                         notes: str = "", comprehension: int = 5) -> Dict[str, Any]:
        """Log a study session."""
        data = self._load_data()
        
        session = StudySession(
            material_id=material_id,
            start_time=datetime.now().isoformat(),
            duration_minutes=duration,
            notes=notes,
            comprehension=comprehension
        )
        
        data['study_sessions'].append(asdict(session))
        
        # Update skill time if material has tags
        material = self._find_material(data['materials'], material_id)
        if material:
            for tag in material.get('tags', []):
                if tag not in data['skills']:
                    data['skills'][tag] = {'total_hours': 0, 'sessions': 0}
                data['skills'][tag]['total_hours'] += duration / 60
                data['skills'][tag]['sessions'] += 1
        
        self._save_data(data)
        
        # Calculate daily stats
        today_sessions = [
            s for s in data['study_sessions']
            if datetime.fromisoformat(s['start_time']).date() == datetime.now().date()
        ]
        today_minutes = sum(s['duration_minutes'] for s in today_sessions)
        
        return {
            'success': True,
            'session': asdict(session),
            'today_total_minutes': today_minutes,
            'today_sessions': len(today_sessions),
            'message': f"Logged {duration}min study session. Today's total: {today_minutes}min."
        }
    
    def _find_material(self, materials: List[Dict], material_id: str) -> Optional[Dict]:
        """Find material by ID."""
        for m in materials:
            if m['id'] == material_id:
                return m
        return None
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics and insights."""
        data = self._load_data()
        
        # Weekly stats
        week_ago = datetime.now() - timedelta(days=7)
        week_sessions = [
            s for s in data['study_sessions']
            if datetime.fromisoformat(s['start_time']) > week_ago
        ]
        
        total_week_hours = sum(s['duration_minutes'] for s in week_sessions) / 60
        
        # Streak calculation
        study_dates = set()
        for s in data['study_sessions']:
            date = datetime.fromisoformat(s['start_time']).date()
            study_dates.add(date)
        
        streak = 0
        today = datetime.now().date()
        for i in range(365):
            check_date = today - timedelta(days=i)
            if check_date in study_dates:
                streak += 1
            elif i == 0:
                continue  # Today doesn't break streak if not studied yet
            else:
                break
        
        # Active materials
        active_materials = [
            m for m in data['materials']
            if not m.get('completed', False)
        ]
        
        # Generate insight
        if streak >= 7:
            insight = f"{streak} day learning streak. Knowledge compounds."
        elif total_week_hours >= 5:
            insight = f"{total_week_hours:.1f} hours of deep learning this week. Solid."
        elif total_week_hours > 0:
            insight = f"{total_week_hours:.1f} hours studied. Room to grow the habit."
        else:
            insight = "No study sessions this week. What skill are you building?"
        
        return {
            'weekly_hours': round(total_week_hours, 1),
            'weekly_sessions': len(week_sessions),
            'current_streak': streak,
            'active_materials': len(active_materials),
            'total_materials': len(data['materials']),
            'skills': data['skills'],
            'insight': insight,
            'suggestion': self._generate_learning_suggestion(data, active_materials)
        }
    
    def _generate_learning_suggestion(self, data: Dict, active_materials: List[Dict]) -> str:
        """Generate learning suggestion."""
        if not active_materials:
            return "Add a book, course, or skill to start tracking your growth."
        
        # Check for overdue reviews
        now = datetime.now()
        overdue = [
            r for r in data.get('review_queue', [])
            if datetime.fromisoformat(r['next_review']) <= now
        ]
        
        if overdue:
            return f"{len(overdue)} concepts ready for review. Spaced repetition works."
        
        # Suggest next material
        if active_materials:
            mat = active_materials[0]
            return f"Continue with '{mat['title']}' or start something new?"
        
        return "Keep the learning momentum going."
    
    def add_review_item(self, material_id: str, concept: str) -> Dict[str, Any]:
        """Add item to spaced repetition queue."""
        data = self._load_data()
        
        review = ReviewItem(
            material_id=material_id,
            concept=concept,
            last_reviewed=datetime.now().isoformat(),
            next_review=(datetime.now() + timedelta(days=1)).isoformat()
        )
        
        data['review_queue'].append(asdict(review))
        self._save_data(data)
        
        return {'success': True, 'message': f"Added '{concept}' to review queue."}
    
    def get_due_reviews(self) -> List[Dict[str, Any]]:
        """Get review items due today."""
        data = self._load_data()
        now = datetime.now()
        
        due = [
            r for r in data.get('review_queue', [])
            if datetime.fromisoformat(r['next_review']) <= now
        ]
        
        # Enrich with material info
        for item in due:
            mat = self._find_material(data['materials'], item['material_id'])
            if mat:
                item['material_title'] = mat['title']
        
        return due
    
    def review_item(self, review_id: int, quality: int) -> Dict[str, Any]:
        """
        Process a review with quality rating (0-5).
        Implements SM-2 spaced repetition algorithm.
        """
        data = self._load_data()
        
        if review_id >= len(data.get('review_queue', [])):
            return {'success': False, 'error': 'Review item not found'}
        
        item = data['review_queue'][review_id]
        
        # SM-2 algorithm
        if quality >= 3:
            if item['repetitions'] == 0:
                item['interval_days'] = 1
            elif item['repetitions'] == 1:
                item['interval_days'] = 6
            else:
                item['interval_days'] = int(item['interval_days'] * item['ease_factor'])
            
            item['repetitions'] += 1
        else:
            item['repetitions'] = 0
            item['interval_days'] = 1
        
        # Update ease factor
        item['ease_factor'] = max(1.3, item['ease_factor'] + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        
        item['last_reviewed'] = datetime.now().isoformat()
        item['next_review'] = (datetime.now() + timedelta(days=item['interval_days'])).isoformat()
        
        self._save_data(data)
        
        return {
            'success': True,
            'next_review_in': item['interval_days'],
            'message': f"Review logged. Next review in {item['interval_days']} days."
        }


# Public API functions
def get_learning_progress() -> Dict[str, Any]:
    """Get learning progress for LOVE's awareness."""
    agent = LearningAgent()
    return agent.get_learning_stats()


def add_study_material(title: str, category: str, source: str, **kwargs) -> Dict[str, Any]:
    """Add learning material."""
    agent = LearningAgent()
    return agent.add_material(title, category, source, **kwargs)


def log_study(material_id: str, duration: int, **kwargs) -> Dict[str, Any]:
    """Log study session."""
    agent = LearningAgent()
    return agent.log_study_session(material_id, duration, **kwargs)
