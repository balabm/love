with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Meaning Mapper Tests ---------------------------------------------------

class TestMeaningMapper:
    """Test Meaning Mapper."""
    
    def test_singleton(self):
        from core.meaning_mapper import get_meaning_mapper
        m1 = get_meaning_mapper()
        m2 = get_meaning_mapper()
        assert m1 is m2
    
    def test_record_moment(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        moment = mm.record_moment(
            "Deep conversation with mentor",
            "connection",
            0.9,
            90,
            "cafe",
            ["Mentor"],
            "Felt truly seen",
        )
        assert moment is not None
        assert moment.description == "Deep conversation with mentor"
        assert moment.source == "connection"
    
    def test_get_meaning_stats(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        stats = mm.get_meaning_stats()
        assert isinstance(stats, dict)
    
    def test_get_meaning_suggestion(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        suggestion = mm.get_meaning_suggestion(30, "medium", "connection")
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_meaning_score(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        score = mm.get_meaning_score()
        assert 0 <= score <= 100


# -- Purpose Navigator Tests ------------------------------------------------

class TestPurposeNavigator:
    """Test Purpose Navigator."""
    
    def test_singleton(self):
        from core.purpose_navigator import get_purpose_navigator
        p1 = get_purpose_navigator()
        p2 = get_purpose_navigator()
        assert p1 is p2
    
    def test_record_alignment(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        alignment = pn.record_alignment(
            "Volunteering at shelter",
            True,
            "service",
            0.9,
            "community",
            4,
        )
        assert alignment is not None
        assert alignment.activity == "Volunteering at shelter"
        assert alignment.aligned is True
    
    def test_get_purpose_stats(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        stats = pn.get_purpose_stats()
        assert isinstance(stats, dict)
    
    def test_get_navigation_suggestion(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        suggestion = pn.get_navigation_suggestion(0.2, "creation", 30)
        assert isinstance(suggestion, dict)
        assert "action" in suggestion
    
    def test_get_purpose_score(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        score = pn.get_purpose_score()
        assert 0 <= score <= 100


# -- Legacy Builder Tests ---------------------------------------------------

class TestLegacyBuilder:
    """Test Legacy Builder."""
    
    def test_singleton(self):
        from core.legacy_builder import get_legacy_builder
        l1 = get_legacy_builder()
        l2 = get_legacy_builder()
        assert l1 is l2
    
    def test_record_legacy_action(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        action = lb.record_legacy_action(
            "Mentored junior developer",
            "mentorship",
            "community",
            "lasting",
            1,
            "Shared career advice",
        )
        assert action is not None
        assert action.action == "Mentored junior developer"
        assert action.theme == "mentorship"
    
    def test_get_legacy_stats(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        stats = lb.get_legacy_stats()
        assert isinstance(stats, dict)
    
    def test_get_legacy_suggestion(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        suggestion = lb.get_legacy_suggestion(30, "creation", "normal")
        assert isinstance(suggestion, dict)
        assert "action" in suggestion
    
    def test_get_legacy_score(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        score = lb.get_legacy_score()
        assert 0 <= score <= 100


# -- Death Awareness Coach Tests --------------------------------------------

class TestDeathAwarenessCoach:
    """Test Death Awareness Coach."""
    
    def test_singleton(self):
        from core.death_awareness_coach import get_death_awareness_coach
        d1 = get_death_awareness_coach()
        d2 = get_death_awareness_coach()
        assert d1 is d2
    
    def test_record_memento(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        memento = dac.record_memento(
            "Visit to old family home",
            "grateful",
            "Time with parents is finite",
            "Call parents weekly",
            "precious",
            "experience",
        )
        assert memento is not None
        assert memento.trigger == "Visit to old family home"
        assert memento.emotional_response == "grateful"
    
    def test_get_death_awareness_stats(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        stats = dac.get_death_awareness_stats()
        assert isinstance(stats, dict)
    
    def test_get_memento_suggestion(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        suggestion = dac.get_memento_suggestion("gentle", 5)
        assert isinstance(suggestion, dict)
        assert "practice" in suggestion
    
    def test_get_death_awareness_score(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        score = dac.get_death_awareness_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 16 tests successfully')
