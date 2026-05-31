with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Humor & Playfulness Trainer Tests --------------------------------------

class TestHumorPlayfulnessTrainer:
    """Test Humor & Playfulness Trainer."""
    
    def test_singleton(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        h1 = get_humor_playfulness_trainer()
        h2 = get_humor_playfulness_trainer()
        assert h1 is h2
    
    def test_record_play(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        entry = hpt.record_play(
            "Made a dad joke during serious meeting",
            "wordplay",
            0.5,
            0.7,
            0.3,
            "work",
            0.8,
        )
        assert entry is not None
        assert entry.moment == "Made a dad joke during serious meeting"
        assert entry.humor_type == "wordplay"
    
    def test_get_playfulness_stats(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        stats = hpt.get_playfulness_stats()
        assert isinstance(stats, dict)
    
    def test_get_playfulness_practice(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        practice = hpt.get_playfulness_practice(0.8, "work")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_playfulness_score(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        score = hpt.get_playfulness_score()
        assert 0 <= score <= 100


# -- Joy Cultivator Tests ---------------------------------------------------

class TestJoyCultivator:
    """Test Joy Cultivator."""
    
    def test_singleton(self):
        from core.joy_cultivator import get_joy_cultivator
        j1 = get_joy_cultivator()
        j2 = get_joy_cultivator()
        assert j1 is j2
    
    def test_record_joy(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        entry = jc.record_joy(
            "Sunrise over the mountains",
            "aesthetic",
            0.9,
            "Morning walk",
            15,
            True,
        )
        assert entry is not None
        assert entry.moment == "Sunrise over the mountains"
        assert entry.joy_type == "aesthetic"
    
    def test_get_joy_stats(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        stats = jc.get_joy_stats()
        assert isinstance(stats, dict)
    
    def test_get_joy_practice(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        practice = jc.get_joy_practice("sensory", 0.5)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_joy_score(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        score = jc.get_joy_score()
        assert 0 <= score <= 100


# -- Celebration Architect Tests --------------------------------------------

class TestCelebrationArchitect:
    """Test Celebration Architect."""
    
    def test_singleton(self):
        from core.celebration_architect import get_celebration_architect
        c1 = get_celebration_architect()
        c2 = get_celebration_architect()
        assert c1 is c2
    
    def test_record_celebration(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        entry = ca.record_celebration(
            "Completed marathon",
            "milestone",
            "Dinner with friends",
            0.9,
            0.7,
            0.9,
            0.9,
            True,
        )
        assert entry is not None
        assert entry.achievement == "Completed marathon"
        assert entry.celebration_type == "milestone"
    
    def test_get_celebration_stats(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        stats = ca.get_celebration_stats()
        assert isinstance(stats, dict)
    
    def test_get_celebration_plan(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        plan = ca.get_celebration_plan(0.8, 0.6)
        assert isinstance(plan, dict)
        assert "celebration" in plan
    
    def test_get_celebration_score(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        score = ca.get_celebration_score()
        assert 0 <= score <= 100


# -- Spontaneity Generator Tests --------------------------------------------

class TestSpontaneityGenerator:
    """Test Spontaneity Generator."""
    
    def test_singleton(self):
        from core.spontaneity_generator import get_spontaneity_generator
        s1 = get_spontaneity_generator()
        s2 = get_spontaneity_generator()
        assert s1 is s2
    
    def test_record_spontaneity(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        entry = sg.record_spontaneity(
            "Took unplanned road trip",
            "experiential",
            0.6,
            0.8,
            0.9,
            0.4,
            True,
        )
        assert entry is not None
        assert entry.moment == "Took unplanned road trip"
        assert entry.spontaneity_type == "experiential"
    
    def test_get_spontaneity_stats(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        stats = sg.get_spontaneity_stats()
        assert isinstance(stats, dict)
    
    def test_get_spontaneous_suggestion(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        suggestion = sg.get_spontaneous_suggestion(0.7, 0.5)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_spontaneity_score(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        score = sg.get_spontaneity_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 32 tests successfully')
