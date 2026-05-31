with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Habit Streak Tracker Tests ------------------------------------------------

class TestHabitStreakTracker:
    """Test Habit Streak Tracker."""
    
    def test_singleton(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        h1 = get_habit_streak_tracker()
        h2 = get_habit_streak_tracker()
        assert h1 is h2
    
    def test_record_habit_and_get_streaks(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        hst.record_habit("test_habit", "Test Habit", completed=True)
        streaks = hst.get_streaks()
        assert len(streaks) > 0
        assert streaks[0].habit_id == "test_habit"
    
    def test_momentum_score(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        score = hst.get_momentum_score("test_habit")
        assert 0 <= score <= 1
    
    def test_detect_slipping(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        slipping = hst.detect_slipping()
        assert isinstance(slipping, list)


# -- Sleep Analyzer Tests ------------------------------------------------------

class TestSleepAnalyzer:
    """Test Sleep Analyzer."""
    
    def test_singleton(self):
        from core.sleep_analyzer import get_sleep_analyzer
        s1 = get_sleep_analyzer()
        s2 = get_sleep_analyzer()
        assert s1 is s2
    
    def test_record_sleep(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(hours=8)).isoformat()
        end = datetime.now().isoformat()
        session = sa.record_sleep(start, end, quality=0.8)
        assert session is not None
        assert session.duration_hours > 0
    
    def test_get_sleep_score(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        score = sa.get_sleep_score()
        assert 0 <= score <= 100
    
    def test_get_recommendations(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        recs = sa.get_recommendations()
        assert isinstance(recs, list)


# -- Social Connection Monitor Tests -------------------------------------------

class TestSocialConnectionMonitor:
    """Test Social Connection Monitor."""
    
    def test_singleton(self):
        from core.social_connection_monitor import get_social_connection_monitor
        s1 = get_social_connection_monitor()
        s2 = get_social_connection_monitor()
        assert s1 is s2
    
    def test_record_interaction(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        scm.record_interaction("Alice", "message", quality=0.8, duration=5.0)
        insights = scm.get_social_insights()
        assert insights.get("status") != "insufficient_data" or insights.get("total_interactions") is not None
    
    def test_get_social_score(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        score = scm.get_social_score()
        assert 0 <= score <= 100
    
    def test_get_reconnection_suggestions(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        suggestions = scm.get_reconnection_suggestions()
        assert isinstance(suggestions, list)


# -- Learning Path Optimizer Tests ---------------------------------------------

class TestLearningPathOptimizer:
    """Test Learning Path Optimizer."""
    
    def test_singleton(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        l1 = get_learning_path_optimizer()
        l2 = get_learning_path_optimizer()
        assert l1 is l2
    
    def test_add_skill(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python", level=0.3, prerequisites=["Basics"])
        stats = lpo.get_learning_stats()
        assert stats["total_skills"] > 0
    
    def test_record_review(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python")
        lpo.record_review("Python", performance=0.8, duration=30.0)
        stats = lpo.get_learning_stats()
        assert stats["total_reviews"] > 0
    
    def test_suggest_next_topic(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python", level=0.3)
        suggestions = lpo.suggest_next_topic("Python")
        assert isinstance(suggestions, list)
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended new tests successfully')
