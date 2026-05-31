with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Emotional Intelligence Trainer Tests ----------------------------------

class TestEmotionalIntelligenceTrainer:
    """Test Emotional Intelligence Trainer."""
    
    def test_singleton(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        e1 = get_emotional_intelligence_trainer()
        e2 = get_emotional_intelligence_trainer()
        assert e1 is e2
    
    def test_record_emotion(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        entry = eq.record_emotion(
            "anxious",
            "fear",
            "Upcoming presentation",
            0.7,
            "Box breathing",
            0.6,
            "work",
            "tight chest",
        )
        assert entry is not None
        assert entry.emotion == "anxious"
        assert entry.intensity == 0.7
    
    def test_get_eq_stats(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        stats = eq.get_eq_stats()
        assert isinstance(stats, dict)
    
    def test_get_eq_exercise(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        exercise = eq.get_eq_exercise("regulation", 0.4)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_eq_score(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        score = eq.get_eq_score()
        assert 0 <= score <= 100


# -- Empathy Builder Tests --------------------------------------------------

class TestEmpathyBuilder:
    """Test Empathy Builder."""
    
    def test_singleton(self):
        from core.empathy_builder import get_empathy_builder
        e1 = get_empathy_builder()
        e2 = get_empathy_builder()
        assert e1 is e2
    
    def test_record_empathy_attempt(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        attempt = eb.record_empathy_attempt(
            "Friend lost job",
            "Sarah",
            "close",
            0.8,
            0.7,
            "Listened without offering solutions",
            "Wanted to fix it",
            0.3,
        )
        assert attempt is not None
        assert attempt.situation == "Friend lost job"
        assert attempt.accuracy == 0.8
    
    def test_get_empathy_stats(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        stats = eb.get_empathy_stats()
        assert isinstance(stats, dict)
    
    def test_get_empathy_exercise(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        exercise = eb.get_empathy_exercise("difficult", 0.8)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_empathy_score(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        score = eb.get_empathy_score()
        assert 0 <= score <= 100


# -- Compassion Generator Tests ---------------------------------------------

class TestCompassionGenerator:
    """Test Compassion Generator."""
    
    def test_singleton(self):
        from core.compassion_generator import get_compassion_generator
        c1 = get_compassion_generator()
        c2 = get_compassion_generator()
        assert c1 is c2
    
    def test_record_compassion(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        entry = cg.record_compassion(
            "Self",
            "self",
            "tender",
            0.8,
            0.7,
            "Loving-kindness meditation",
            "Feeling undeserving",
        )
        assert entry is not None
        assert entry.target == "Self"
        assert entry.intensity == 0.8
    
    def test_get_compassion_stats(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        stats = cg.get_compassion_stats()
        assert isinstance(stats, dict)
    
    def test_get_compassion_practice(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        practice = cg.get_compassion_practice("difficult", 0.7)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_compassion_score(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        score = cg.get_compassion_score()
        assert 0 <= score <= 100


# -- Gratitude Amplifier Tests ----------------------------------------------

class TestGratitudeAmplifier:
    """Test Gratitude Amplifier."""
    
    def test_singleton(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        g1 = get_gratitude_amplifier()
        g2 = get_gratitude_amplifier()
        assert g1 is g2
    
    def test_record_gratitude(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        entry = ga.record_gratitude(
            "Morning coffee ritual",
            "simple",
            0.9,
            0.6,
            "Savoring practice",
            True,
            0.6,
            0.8,
        )
        assert entry is not None
        assert entry.target == "Morning coffee ritual"
        assert entry.depth == 0.9
    
    def test_get_gratitude_stats(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        stats = ga.get_gratitude_stats()
        assert isinstance(stats, dict)
    
    def test_get_amplification_exercise(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        exercise = ga.get_amplification_exercise("novelty", "nature")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_gratitude_score(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        score = ga.get_gratitude_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 23 tests successfully')
