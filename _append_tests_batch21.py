with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Identity Designer Tests -------------------------------------------------

class TestIdentityDesigner:
    """Test Identity Designer."""
    
    def test_singleton(self):
        from core.identity_designer import get_identity_designer
        i1 = get_identity_designer()
        i2 = get_identity_designer()
        assert i1 is i2
    
    def test_record_identity(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        entry = idd.record_identity(
            "I am a runner",
            ["Ran 3 times this week", "Enjoyed the process"],
            0.7,
            "current",
            0.8,
            "self",
        )
        assert entry is not None
        assert entry.identity_statement == "I am a runner"
        assert entry.strength == 0.7
    
    def test_get_identity_stats(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        stats = idd.get_identity_stats()
        assert isinstance(stats, dict)
    
    def test_get_identity_design(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        design = idd.get_identity_design("I am a writer", 0.6, "creativity")
        assert isinstance(design, dict)
        assert "small_steps" in design
    
    def test_get_identity_score(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        score = idd.get_identity_score()
        assert 0 <= score <= 100


# -- Habit Architect Tests --------------------------------------------------

class TestHabitArchitect:
    """Test Habit Architect."""
    
    def test_singleton(self):
        from core.habit_architect import get_habit_architect
        h1 = get_habit_architect()
        h2 = get_habit_architect()
        assert h1 is h2
    
    def test_record_habit_attempt(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        attempt = ha.record_habit_attempt(
            "Morning meditation",
            "health",
            True,
            "Wake up alarm",
            "Feel calm",
            0.2,
            0.8,
            "I am mindful",
        )
        assert attempt is not None
        assert attempt.habit == "Morning meditation"
        assert attempt.success is True
    
    def test_get_habit_stats(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        stats = ha.get_habit_stats()
        assert isinstance(stats, dict)
    
    def test_get_habit_design(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        design = ha.get_habit_design("Read daily", "morning coffee", 0.6)
        assert isinstance(design, dict)
        assert "stack_template" in design
    
    def test_get_habit_score(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        score = ha.get_habit_score()
        assert 0 <= score <= 100


# -- Environment Curator Tests ----------------------------------------------

class TestEnvironmentCurator:
    """Test Environment Curator."""
    
    def test_singleton(self):
        from core.environment_curator import get_environment_curator
        e1 = get_environment_curator()
        e2 = get_environment_curator()
        assert e1 is e2
    
    def test_record_environment(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        entry = ec.record_environment(
            "office",
            "clutter",
            -0.6,
            "focus",
            -0.4,
            "Cleared desk",
        )
        assert entry is not None
        assert entry.space == "office"
        assert entry.factor == "clutter"
    
    def test_get_environment_stats(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        stats = ec.get_environment_stats()
        assert isinstance(stats, dict)
    
    def test_get_curation_suggestion(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        suggestion = ec.get_curation_suggestion("focus", "office", "low")
        assert isinstance(suggestion, dict)
        assert "modifications" in suggestion
    
    def test_get_environment_score(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        score = ec.get_environment_score()
        assert 0 <= score <= 100


# -- Ritual Master Tests ----------------------------------------------------

class TestRitualMaster:
    """Test Ritual Master."""
    
    def test_singleton(self):
        from core.ritual_master import get_ritual_master
        r1 = get_ritual_master()
        r2 = get_ritual_master()
        assert r1 is r2
    
    def test_record_ritual(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        ritual = rm.record_ritual(
            "Evening wind-down",
            "transition",
            0.8,
            0.9,
            20,
            "work_to_rest",
            ["lighting", "sound", "movement"],
        )
        assert ritual is not None
        assert ritual.ritual == "Evening wind-down"
        assert ritual.transition == "work_to_rest"
    
    def test_get_ritual_stats(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        stats = rm.get_ritual_stats()
        assert isinstance(stats, dict)
    
    def test_get_ritual_design(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        design = rm.get_ritual_design("morning", "minimal", 5)
        assert isinstance(design, dict)
        assert "template" in design
    
    def test_get_ritual_score(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        score = rm.get_ritual_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 21 tests successfully')
