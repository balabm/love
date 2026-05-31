with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Sleep Optimizer Tests --------------------------------------------------

class TestSleepOptimizer:
    """Test Sleep Optimizer."""
    
    def test_singleton(self):
        from core.sleep_optimizer import get_sleep_optimizer
        s1 = get_sleep_optimizer()
        s2 = get_sleep_optimizer()
        assert s1 is s2
    
    def test_record_sleep_session(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        session = so.record_sleep_session(
            7.5,
            0.8,
            15,
            1,
            20.0,
            25.0,
            "23:00",
            "06:30",
            False,
            10,
            False,
            False,
            0.3,
            68.0,
        )
        assert session is not None
        assert session.duration_hours == 7.5
        assert session.quality == 0.8
    
    def test_get_sleep_stats(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        stats = so.get_sleep_stats()
        assert isinstance(stats, dict)
    
    def test_get_sleep_recommendation(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        rec = so.get_sleep_recommendation(3.0, "night_owl")
        assert isinstance(rec, dict)
        assert "routine" in rec
    
    def test_get_sleep_score(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        score = so.get_sleep_score()
        assert 0 <= score <= 100


# -- Nutrition Coach Tests --------------------------------------------------

class TestNutritionCoach:
    """Test Nutrition Coach."""
    
    def test_singleton(self):
        from core.nutrition_coach import get_nutrition_coach
        n1 = get_nutrition_coach()
        n2 = get_nutrition_coach()
        assert n1 is n2
    
    def test_record_meal(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        entry = nc.record_meal(
            ["Oatmeal", "Berries", "Almonds"],
            "breakfast",
            "planned",
            0.6,
            0.7,
            "slow",
            0.5,
            0.7,
            0.8,
            True,
            True,
            False,
        )
        assert entry is not None
        assert entry.meal_type == "breakfast"
        assert entry.protein_present is True
    
    def test_get_nutrition_stats(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        stats = nc.get_nutrition_stats()
        assert isinstance(stats, dict)
    
    def test_get_meal_suggestion(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        suggestion = nc.get_meal_suggestion("energy", ["vegetarian"])
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_nutrition_score(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        score = nc.get_nutrition_score()
        assert 0 <= score <= 100


# -- Movement Tracker Tests -------------------------------------------------

class TestMovementTracker:
    """Test Movement Tracker."""
    
    def test_singleton(self):
        from core.movement_tracker import get_movement_tracker
        m1 = get_movement_tracker()
        m2 = get_movement_tracker()
        assert m1 is m2
    
    def test_record_session(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        session = mt.record_session(
            "Morning jog",
            "run",
            30,
            0.7,
            0.5,
            0.8,
            0.9,
            "energized",
            False,
            True,
        )
        assert session is not None
        assert session.activity == "Morning jog"
        assert session.movement_type == "run"
        assert session.outdoors is True
    
    def test_get_movement_stats(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        stats = mt.get_movement_stats()
        assert isinstance(stats, dict)
    
    def test_get_movement_suggestion(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        suggestion = mt.get_movement_suggestion(0.3, 0.4, 15, "social")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_movement_score(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        score = mt.get_movement_score()
        assert 0 <= score <= 100


# -- Health Integrator Tests ------------------------------------------------

class TestHealthIntegrator:
    """Test Health Integrator."""
    
    def test_singleton(self):
        from core.health_integrator import get_health_integrator
        h1 = get_health_integrator()
        h2 = get_health_integrator()
        assert h1 is h2
    
    def test_record_wellbeing_snapshot(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        snapshot = hi.record_wellbeing_snapshot(
            7.5,
            0.8,
            0.7,
            30,
            0.8,
            0.7,
            0.6,
            0.4,
            0.7,
            0.8,
        )
        assert snapshot is not None
        assert snapshot.sleep_hours == 7.5
        assert snapshot.mood == 0.7
    
    def test_get_health_stats(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        stats = hi.get_health_stats()
        assert isinstance(stats, dict)
    
    def test_get_health_priority(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        priority = hi.get_health_priority({"sleep": 0.3, "nutrition": 0.7, "movement": 0.6, "mood": 0.5, "energy": 0.4, "stress": 0.8})
        assert isinstance(priority, dict)
        assert "priority_domain" in priority
    
    def test_get_health_score(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        score = hi.get_health_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 25 tests successfully')
