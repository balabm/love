with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Curiosity Spark Tests --------------------------------------------------

class TestCuriositySpark:
    """Test Curiosity Spark."""
    
    def test_singleton(self):
        from core.curiosity_spark import get_curiosity_spark
        c1 = get_curiosity_spark()
        c2 = get_curiosity_spark()
        assert c1 is c2
    
    def test_record_exploration(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        exp = cs.record_exploration(
            "Quantum entanglement",
            "science",
            "deep",
            "book",
            120,
            0.9,
            5,
            ["Partner"],
        )
        assert exp is not None
        assert exp.topic == "Quantum entanglement"
        assert exp.questions_generated == 5
    
    def test_get_curiosity_stats(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        stats = cs.get_curiosity_stats()
        assert isinstance(stats, dict)
    
    def test_get_spark(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        spark = cs.get_spark(["science"], 10, "science")
        assert isinstance(spark, dict)
        assert "spark" in spark
    
    def test_get_curiosity_score(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        score = cs.get_curiosity_score()
        assert 0 <= score <= 100


# -- Play Coach Tests -------------------------------------------------------

class TestPlayCoach:
    """Test Play Coach."""
    
    def test_singleton(self):
        from core.play_coach import get_play_coach
        p1 = get_play_coach()
        p2 = get_play_coach()
        assert p1 is p2
    
    def test_record_play(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        session = pc.record_play(
            "Frisbee in park",
            "physical",
            60,
            0.9,
            "medium",
            False,
            False,
            "outdoors",
            ["Alex", "Sam"],
        )
        assert session is not None
        assert session.activity == "Frisbee in park"
        assert session.solo is False
    
    def test_get_play_stats(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        stats = pc.get_play_stats()
        assert isinstance(stats, dict)
    
    def test_get_play_suggestion(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        suggestion = pc.get_play_suggestion("medium", 30, "happy", True)
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_playfulness_score(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        score = pc.get_playfulness_score()
        assert 0 <= score <= 100


# -- Adventure Planner Tests ------------------------------------------------

class TestAdventurePlanner:
    """Test Adventure Planner."""
    
    def test_singleton(self):
        from core.adventure_planner import get_adventure_planner
        a1 = get_adventure_planner()
        a2 = get_adventure_planner()
        assert a1 is a2
    
    def test_record_adventure(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        adv = ap.record_adventure(
            "Solo camping trip",
            "nature",
            48,
            0.7,
            0.9,
            0.8,
            True,
            True,
            [],
            150,
            "Yosemite",
            "Incredible stars",
        )
        assert adv is not None
        assert adv.activity == "Solo camping trip"
        assert adv.location == "Yosemite"
    
    def test_get_adventure_stats(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        stats = ap.get_adventure_stats()
        assert isinstance(stats, dict)
    
    def test_get_adventure_suggestion(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        suggestion = ap.get_adventure_suggestion("low", "micro", "medium", True)
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_adventure_score(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        score = ap.get_adventure_score()
        assert 0 <= score <= 100


# -- Wonder Tracker Tests ---------------------------------------------------

class TestWonderTracker:
    """Test Wonder Tracker."""
    
    def test_singleton(self):
        from core.wonder_tracker import get_wonder_tracker
        w1 = get_wonder_tracker()
        w2 = get_wonder_tracker()
        assert w1 is w2
    
    def test_record_wonder(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        wonder = wt.record_wonder(
            "Milky Way visible",
            "vastness",
            0.9,
            20,
            "humbled",
            0.6,
            0.9,
            "Desert campsite",
            "22:00",
            "First time seeing it so clearly",
        )
        assert wonder is not None
        assert wonder.trigger == "Milky Way visible"
        assert wonder.intensity == 0.9
    
    def test_get_wonder_stats(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        stats = wt.get_wonder_stats()
        assert isinstance(stats, dict)
    
    def test_get_wonder_suggestion(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        suggestion = wt.get_wonder_suggestion("nature", 5, "outdoors")
        assert isinstance(suggestion, dict)
        assert "prompt" in suggestion
    
    def test_get_wonder_score(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        score = wt.get_wonder_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 15 tests successfully')
