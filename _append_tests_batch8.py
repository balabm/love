with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Communication Analyzer Tests --------------------------------------------

class TestCommunicationAnalyzer:
    """Test Communication Analyzer."""
    
    def test_singleton(self):
        from core.communication_analyzer import get_communication_analyzer
        c1 = get_communication_analyzer()
        c2 = get_communication_analyzer()
        assert c1 is c2
    
    def test_record_communication(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        comm = ca.record_communication(
            channel="email",
            recipient="team@example.com",
            purpose="request",
            duration=5,
            effectiveness=0.8,
            clarity=0.9,
            response_time=30,
        )
        assert comm is not None
        assert comm.channel == "email"
    
    def test_get_communication_stats(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        stats = ca.get_communication_stats()
        assert isinstance(stats, dict)
    
    def test_get_channel_recommendation(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        rec = ca.get_channel_recommendation("decision", "urgent")
        assert "recommended_channel" in rec
        assert "reason" in rec
    
    def test_get_communication_load_score(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        score = ca.get_communication_load_score()
        assert 0 <= score <= 100


# -- Goal Progress Visualizer Tests -------------------------------------------

class TestGoalProgressVisualizer:
    """Test Goal Progress Visualizer."""
    
    def test_singleton(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        g1 = get_goal_progress_visualizer()
        g2 = get_goal_progress_visualizer()
        assert g1 is g2
    
    def test_add_goal(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        goal = gpv.add_goal("Write Book", "Complete first draft", 50000, "words", "2026-12-01", "high", "writing")
        assert goal is not None
        assert goal.title == "Write Book"
    
    def test_record_progress(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        goal = gpv.add_goal("Daily Steps", "Walk 10k steps", 10000, "steps")
        entry = gpv.record_progress(goal.goal_id, 5000, "Morning walk")
        assert entry is not None
        assert entry.amount == 5000
    
    def test_get_goal_status(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        status = gpv.get_goal_status()
        assert isinstance(status, list)
    
    def test_get_suggestions(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        suggestions = gpv.get_suggestions()
        assert isinstance(suggestions, list)


# -- Life Balance Wheel Tests -------------------------------------------------

class TestLifeBalanceWheel:
    """Test Life Balance Wheel."""
    
    def test_singleton(self):
        from core.life_balance_wheel import get_life_balance_wheel
        l1 = get_life_balance_wheel()
        l2 = get_life_balance_wheel()
        assert l1 is l2
    
    def test_record_domain_rating(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        entry = lbw.record_domain_rating("work", 7.5, 45, 6.5, ["coding", "meetings"])
        assert entry is not None
        assert entry.domain == "work"
        assert entry.rating == 7.5
    
    def test_get_balance_score(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        score = lbw.get_balance_score()
        assert 0 <= score <= 100
    
    def test_get_domain_insights(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        insights = lbw.get_domain_insights()
        assert isinstance(insights, dict)
    
    def test_get_rebalancing_suggestions(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        suggestions = lbw.get_rebalancing_suggestions()
        assert isinstance(suggestions, list)


# -- Productivity Gamifier Tests ----------------------------------------------

class TestProductivityGamifier:
    """Test Productivity Gamifier."""
    
    def test_singleton(self):
        from core.productivity_gamifier import get_productivity_gamifier
        p1 = get_productivity_gamifier()
        p2 = get_productivity_gamifier()
        assert p1 is p2
    
    def test_record_activity(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        activity = pg.record_activity("Deep Work", "work", 120, 0.9)
        assert activity is not None
        assert activity.activity == "Deep Work"
        assert activity.xp_earned > 0
    
    def test_get_level(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        level_info = pg.get_level()
        assert "level" in level_info
        assert "title" in level_info
        assert "total_xp" in level_info
    
    def test_get_achievements(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        achievements = pg.get_achievements()
        assert isinstance(achievements, dict)
        assert "total" in achievements
        assert "unlocked" in achievements
    
    def test_get_daily_challenge(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        challenge = pg.get_daily_challenge()
        assert "daily_challenges" in challenge
        assert isinstance(challenge["daily_challenges"], list)
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 8 tests successfully')
