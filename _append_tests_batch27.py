with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Stress Resilience Trainer Tests ----------------------------------------

class TestStressResilienceTrainer:
    """Test Stress Resilience Trainer."""
    
    def test_singleton(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        s1 = get_stress_resilience_trainer()
        s2 = get_stress_resilience_trainer()
        assert s1 is s2
    
    def test_record_stress_event(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        event = srt.record_stress_event(
            "Deadline pressure",
            "acute",
            0.8,
            "fight",
            60,
            30,
            "Walk outside",
            0.6,
            0.4,
        )
        assert event is not None
        assert event.trigger == "Deadline pressure"
        assert event.intensity == 0.8
    
    def test_get_stress_stats(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        stats = srt.get_stress_stats()
        assert isinstance(stats, dict)
    
    def test_get_resilience_practice(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        practice = srt.get_resilience_practice("chronic", 0.4)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_resilience_score(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        score = srt.get_resilience_score()
        assert 0 <= score <= 100


# -- Emotional Regulation Coach Tests --------------------------------------

class TestEmotionalRegulationCoach:
    """Test Emotional Regulation Coach."""
    
    def test_singleton(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        e1 = get_emotional_regulation_coach()
        e2 = get_emotional_regulation_coach()
        assert e1 is e2
    
    def test_record_emotion(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        entry = erc.record_emotion(
            "anger",
            "Criticism at work",
            0.7,
            "reappraisal",
            0.8,
            "work",
            "tight chest",
            "Spoke calmly, set boundary",
        )
        assert entry is not None
        assert entry.emotion == "anger"
        assert entry.regulation_strategy == "reappraisal"
    
    def test_get_regulation_stats(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        stats = erc.get_regulation_stats()
        assert isinstance(stats, dict)
    
    def test_get_regulation_technique(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        technique = erc.get_regulation_technique("anxiety", "social", 0.5)
        assert isinstance(technique, dict)
        assert "technique" in technique
    
    def test_get_regulation_score(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        score = erc.get_regulation_score()
        assert 0 <= score <= 100


# -- Mindfulness Trainer Tests ----------------------------------------------

class TestMindfulnessTrainer:
    """Test Mindfulness Trainer."""
    
    def test_singleton(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        m1 = get_mindfulness_trainer()
        m2 = get_mindfulness_trainer()
        assert m1 is m2
    
    def test_record_practice(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        practice = mt.record_practice(
            "breath",
            15,
            0.7,
            8,
            8,
            0.6,
            0.5,
            0.8,
        )
        assert practice is not None
        assert practice.practice_type == "breath"
        assert practice.duration_minutes == 15
    
    def test_get_mindfulness_stats(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        stats = mt.get_mindfulness_stats()
        assert isinstance(stats, dict)
    
    def test_get_practice_suggestion(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        suggestion = mt.get_practice_suggestion("stress", 0.4)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_mindfulness_score(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        score = mt.get_mindfulness_score()
        assert 0 <= score <= 100


# -- Presence Amplifier Tests -----------------------------------------------

class TestPresenceAmplifier:
    """Test Presence Amplifier."""
    
    def test_singleton(self):
        from core.presence_amplifier import get_presence_amplifier
        p1 = get_presence_amplifier()
        p2 = get_presence_amplifier()
        assert p1 is p2
    
    def test_record_presence(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        entry = pa.record_presence(
            "meal",
            0.8,
            ["Taste", "Smell", "Texture"],
            ["Phone notification"],
            0.9,
            20,
        )
        assert entry is not None
        assert entry.context == "meal"
        assert entry.depth == 0.8
    
    def test_get_presence_stats(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        stats = pa.get_presence_stats()
        assert isinstance(stats, dict)
    
    def test_get_presence_practice(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        practice = pa.get_presence_practice("conversation", 0.6)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_presence_score(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        score = pa.get_presence_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 27 tests successfully')
