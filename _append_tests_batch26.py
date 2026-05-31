with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Digital Minimalism Coach Tests -----------------------------------------

class TestDigitalMinimalismCoach:
    """Test Digital Minimalism Coach."""
    
    def test_singleton(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        d1 = get_digital_minimalism_coach()
        d2 = get_digital_minimalism_coach()
        assert d1 is d2
    
    def test_record_session(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        session = dmc.record_session(
            "Instagram",
            "social_media",
            45,
            0.2,
            0.1,
            0.6,
            0.4,
            0.3,
            True,
        )
        assert session is not None
        assert session.app_or_site == "Instagram"
        assert session.compulsive is True
    
    def test_get_digital_stats(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        stats = dmc.get_digital_stats()
        assert isinstance(stats, dict)
    
    def test_get_minimalism_practice(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        practice = dmc.get_minimalism_practice("escapist", "reduce_compulsive")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_digital_score(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        score = dmc.get_digital_score()
        assert 0 <= score <= 100


# -- Focus Ritual Designer Tests --------------------------------------------

class TestFocusRitualDesigner:
    """Test Focus Ritual Designer."""
    
    def test_singleton(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        f1 = get_focus_ritual_designer()
        f2 = get_focus_ritual_designer()
        assert f1 is f2
    
    def test_record_ritual(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        entry = frd.record_ritual(
            "Morning writing ritual",
            "creative",
            ["Clear desk", "Close apps", "Set timer", "Write intention", "3 deep breaths"],
            10,
            0.9,
            1.0,
            0.7,
            0.6,
            0.9,
        )
        assert entry is not None
        assert entry.name == "Morning writing ritual"
        assert len(entry.components) == 5
    
    def test_get_ritual_stats(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        stats = frd.get_ritual_stats()
        assert isinstance(stats, dict)
    
    def test_get_ritual_design(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        design = frd.get_ritual_design("deep_work", 0.8, 8)
        assert isinstance(design, dict)
        assert "components" in design
    
    def test_get_ritual_score(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        score = frd.get_ritual_score()
        assert 0 <= score <= 100


# -- Attention Recovery Specialist Tests ------------------------------------

class TestAttentionRecoverySpecialist:
    """Test Attention Recovery Specialist."""
    
    def test_singleton(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        a1 = get_attention_recovery_specialist()
        a2 = get_attention_recovery_specialist()
        assert a1 is a2
    
    def test_record_attention_state(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        state = ars.record_attention_state(
            0.3,
            "sustained",
            "social_media",
            30,
            0.4,
            "Walk outside",
            0.7,
        )
        assert state is not None
        assert state.focus_level == 0.3
        assert state.source == "social_media"
    
    def test_get_attention_stats(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        stats = ars.get_attention_stats()
        assert isinstance(stats, dict)
    
    def test_get_recovery_protocol(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        protocol = ars.get_recovery_protocol("digital_overload", "high")
        assert isinstance(protocol, dict)
        assert "protocol" in protocol
    
    def test_get_attention_score(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        score = ars.get_attention_score()
        assert 0 <= score <= 100


# -- Cognitive Load Manager Tests -------------------------------------------

class TestCognitiveLoadManager:
    """Test Cognitive Load Manager."""
    
    def test_singleton(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        c1 = get_cognitive_load_manager()
        c2 = get_cognitive_load_manager()
        assert c1 is c2
    
    def test_record_load_event(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        event = clm.record_load_event(
            "decisions",
            0.8,
            60,
            ["fatigue", "irritability"],
            0.6,
            0.3,
            0.4,
        )
        assert event is not None
        assert event.source == "decisions"
        assert event.intensity == 0.8
    
    def test_get_cognitive_stats(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        stats = clm.get_cognitive_stats()
        assert isinstance(stats, dict)
    
    def test_get_load_reduction(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        reduction = clm.get_load_reduction("decisions", 0.7)
        assert isinstance(reduction, dict)
        assert "reduction_technique" in reduction
    
    def test_get_cognitive_score(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        score = clm.get_cognitive_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 26 tests successfully')
