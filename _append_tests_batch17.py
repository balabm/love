with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Flow State Coach Tests -------------------------------------------------

class TestFlowStateCoach:
    """Test Flow State Coach."""
    
    def test_singleton(self):
        from core.flow_state_coach import get_flow_state_coach
        f1 = get_flow_state_coach()
        f2 = get_flow_state_coach()
        assert f1 is f2
    
    def test_record_flow_session(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        session = fsc.record_flow_session(
            "Coding feature",
            0.8,
            0.7,
            0.9,
            0.8,
            0.9,
            0.8,
            0,
            120,
            "Coffee + music",
        )
        assert session is not None
        assert session.activity == "Coding feature"
        assert session.immersion == 0.9
    
    def test_get_flow_stats(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        stats = fsc.get_flow_stats()
        assert isinstance(stats, dict)
    
    def test_get_flow_suggestion(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        suggestion = fsc.get_flow_suggestion("Writing report", 0.6, 90)
        assert isinstance(suggestion, dict)
        assert "challenge_adjustment" in suggestion
    
    def test_get_flow_score(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        score = fsc.get_flow_score()
        assert 0 <= score <= 100


# -- Savoring Trainer Tests -------------------------------------------------

class TestSavoringTrainer:
    """Test Savoring Trainer."""
    
    def test_singleton(self):
        from core.savoring_trainer import get_savoring_trainer
        s1 = get_savoring_trainer()
        s2 = get_savoring_trainer()
        assert s1 is s2
    
    def test_record_savoring(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        savoring = st.record_savoring(
            "First coffee of the day",
            "present",
            "basking",
            60,
            0.8,
            0.6,
            0.9,
            ["hurry"],
        )
        assert savoring is not None
        assert savoring.experience == "First coffee of the day"
        assert savoring.intensity_after == 0.9
    
    def test_get_savoring_stats(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        stats = st.get_savoring_stats()
        assert isinstance(stats, dict)
    
    def test_get_savoring_suggestion(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        suggestion = st.get_savoring_suggestion("Sunset", "happy", "present")
        assert isinstance(suggestion, dict)
        assert "technique" in suggestion
    
    def test_get_savoring_score(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        score = st.get_savoring_score()
        assert 0 <= score <= 100


# -- Presence Detector Tests ------------------------------------------------

class TestPresenceDetector:
    """Test Presence Detector."""
    
    def test_singleton(self):
        from core.presence_detector import get_presence_detector
        p1 = get_presence_detector()
        p2 = get_presence_detector()
        assert p1 is p2
    
    def test_record_presence(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        moment = pd.record_presence(
            "full",
            "Meditation bell",
            "sensory",
            20,
            0.9,
            "breath focus",
        )
        assert moment is not None
        assert moment.state == "full"
        assert moment.quality == 0.9
    
    def test_get_presence_stats(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        stats = pd.get_presence_stats()
        assert isinstance(stats, dict)
    
    def test_get_presence_suggestion(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        suggestion = pd.get_presence_suggestion("distracted", "work")
        assert isinstance(suggestion, dict)
        assert "technique" in suggestion
    
    def test_get_presence_score(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        score = pd.get_presence_score()
        assert 0 <= score <= 100


# -- Intuition Trainer Tests ------------------------------------------------

class TestIntuitionTrainer:
    """Test Intuition Trainer."""
    
    def test_singleton(self):
        from core.intuition_trainer import get_intuition_trainer
        i1 = get_intuition_trainer()
        i2 = get_intuition_trainer()
        assert i1 is i2
    
    def test_record_hunch(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        hunch = it.record_hunch(
            "Don't take this job",
            "work",
            "somatic",
            0.7,
            True,
            "confirmed",
            "The salary is great",
            "Boss turned out toxic",
        )
        assert hunch is not None
        assert hunch.hunch == "Don't take this job"
        assert hunch.followed is True
        assert hunch.outcome == "confirmed"
    
    def test_get_intuition_stats(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        stats = it.get_intuition_stats()
        assert isinstance(stats, dict)
    
    def test_get_intuition_exercise(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        exercise = it.get_intuition_exercise("somatic", "relationship")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_intuition_score(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        score = it.get_intuition_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 17 tests successfully')
