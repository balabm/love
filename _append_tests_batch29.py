with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Curiosity Cultivator Tests ---------------------------------------------

class TestCuriosityCultivator:
    """Test Curiosity Cultivator."""
    
    def test_singleton(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        c1 = get_curiosity_cultivator()
        c2 = get_curiosity_cultivator()
        assert c1 is c2
    
    def test_record_curiosity(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        entry = cc.record_curiosity(
            "Why do some people thrive under pressure while others crumble?",
            "epistemic",
            0.8,
            "Podcast about stress responses",
            "Read research on eustress",
            0.9,
        )
        assert entry is not None
        assert entry.topic == "Why do some people thrive under pressure while others crumble?"
        assert entry.curiosity_type == "epistemic"
    
    def test_get_curiosity_stats(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        stats = cc.get_curiosity_stats()
        assert isinstance(stats, dict)
    
    def test_get_curiosity_practice(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        practice = cc.get_curiosity_practice("certainty", "science")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_curiosity_score(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        score = cc.get_curiosity_score()
        assert 0 <= score <= 100


# -- Learning Acceleration Engine Tests -------------------------------------

class TestLearningAccelerationEngine:
    """Test Learning Acceleration Engine."""
    
    def test_singleton(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        l1 = get_learning_acceleration_engine()
        l2 = get_learning_acceleration_engine()
        assert l1 is l2
    
    def test_record_session(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        session = lae.record_session(
            "Machine Learning Fundamentals",
            "active_recall",
            45,
            0.7,
            0.8,
            0.6,
            0.9,
        )
        assert session is not None
        assert session.topic == "Machine Learning Fundamentals"
        assert session.technique == "active_recall"
    
    def test_get_learning_stats(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        stats = lae.get_learning_stats()
        assert isinstance(stats, dict)
    
    def test_get_acceleration_plan(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        plan = lae.get_acceleration_plan("Python Programming", "2 weeks", 0.3, 0.8)
        assert isinstance(plan, dict)
        assert "recommended_techniques" in plan
    
    def test_get_learning_score(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        score = lae.get_learning_score()
        assert 0 <= score <= 100


# -- Knowledge Synthesizer Tests --------------------------------------------

class TestKnowledgeSynthesizer:
    """Test Knowledge Synthesizer."""
    
    def test_singleton(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        k1 = get_knowledge_synthesizer()
        k2 = get_knowledge_synthesizer()
        assert k1 is k2
    
    def test_record_knowledge(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        entry = ks.record_knowledge(
            "Neuroplasticity",
            "book",
            "neuroscience",
            ["habits", "learning", "brain"],
            "The brain rewires itself based on repeated behaviors",
            0.9,
        )
        assert entry is not None
        assert entry.topic == "Neuroplasticity"
        assert len(entry.connections) == 3
    
    def test_get_synthesis_stats(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        stats = ks.get_synthesis_stats()
        assert isinstance(stats, dict)
    
    def test_get_synthesis_exercise(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        exercise = ks.get_synthesis_exercise(["psychology", "business"], "bridge_silos")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_synthesis_score(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        score = ks.get_synthesis_score()
        assert 0 <= score <= 100


# -- Wisdom Distiller Tests -------------------------------------------------

class TestWisdomDistiller:
    """Test Wisdom Distiller."""
    
    def test_singleton(self):
        from core.wisdom_distiller import get_wisdom_distiller
        w1 = get_wisdom_distiller()
        w2 = get_wisdom_distiller()
        assert w1 is w2
    
    def test_record_wisdom(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        entry = wd.record_wisdom(
            "Team conflicts over priorities",
            0.8,
            "Alignment comes before execution",
            "Shared purpose prevents resource conflicts",
            0.9,
            0.8,
            "leadership",
        )
        assert entry is not None
        assert entry.situation == "Team conflicts over priorities"
        assert entry.principle == "Shared purpose prevents resource conflicts"
    
    def test_get_wisdom_stats(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        stats = wd.get_wisdom_stats()
        assert isinstance(stats, dict)
    
    def test_get_distillation_practice(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        practice = wd.get_distillation_practice(0.7, "business")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_wisdom_score(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        score = wd.get_wisdom_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 29 tests successfully')
