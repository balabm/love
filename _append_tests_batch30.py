with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Purpose Clarity Engine Tests -------------------------------------------

class TestPurposeClarityEngine:
    """Test Purpose Clarity Engine."""
    
    def test_singleton(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        p1 = get_purpose_clarity_engine()
        p2 = get_purpose_clarity_engine()
        assert p1 is p2
    
    def test_record_exploration(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        exploration = pce.record_exploration(
            "Career direction",
            0.4,
            0.7,
            0.6,
            "Applied for 3 roles aligned with values",
            0.8,
            0.5,
            0.6,
        )
        assert exploration is not None
        assert exploration.theme == "Career direction"
        assert exploration.clarity_after == 0.7
    
    def test_get_purpose_stats(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        stats = pce.get_purpose_stats()
        assert isinstance(stats, dict)
    
    def test_get_clarity_exercise(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        exercise = pce.get_clarity_exercise("uncertainty", 0.4)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_purpose_score(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        score = pce.get_purpose_score()
        assert 0 <= score <= 100


# -- Legacy Builder Tests ---------------------------------------------------

class TestLegacyBuilder:
    """Test Legacy Builder."""
    
    def test_singleton(self):
        from core.legacy_builder import get_legacy_builder
        l1 = get_legacy_builder()
        l2 = get_legacy_builder()
        assert l1 is l2
    
    def test_record_contribution(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        contribution = lb.record_contribution(
            "Mentored 3 junior developers",
            "mentorship",
            ["Alice", "Bob", "Charlie"],
            0.8,
            0.9,
            0.4,
            0.95,
        )
        assert contribution is not None
        assert contribution.contribution == "Mentored 3 junior developers"
        assert contribution.legacy_type == "mentorship"
    
    def test_get_legacy_stats(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        stats = lb.get_legacy_stats()
        assert isinstance(stats, dict)
    
    def test_get_legacy_plan(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        plan = lb.get_legacy_plan("mentor", "5_years")
        assert isinstance(plan, dict)
        assert "plan" in plan
    
    def test_get_legacy_score(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        score = lb.get_legacy_score()
        assert 0 <= score <= 100


# -- Impact Maximizer Tests -------------------------------------------------

class TestImpactMaximizer:
    """Test Impact Maximizer."""
    
    def test_singleton(self):
        from core.impact_maximizer import get_impact_maximizer
        i1 = get_impact_maximizer()
        i2 = get_impact_maximizer()
        assert i1 is i2
    
    def test_record_impact(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        entry = im.record_impact(
            "Automated reporting pipeline",
            "systemic",
            0.6,
            50,
            "Saved 10 hours/week across team",
            0.9,
            0.8,
        )
        assert entry is not None
        assert entry.action == "Automated reporting pipeline"
        assert entry.impact_type == "systemic"
    
    def test_get_impact_stats(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        stats = im.get_impact_stats()
        assert isinstance(stats, dict)
    
    def test_get_leverage_suggestion(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        suggestion = im.get_leverage_suggestion("busywork", 0.5)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_impact_score(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        score = im.get_impact_score()
        assert 0 <= score <= 100


# -- Meaning Amplifier Tests ------------------------------------------------

class TestMeaningAmplifier:
    """Test Meaning Amplifier."""
    
    def test_singleton(self):
        from core.meaning_amplifier import get_meaning_amplifier
        m1 = get_meaning_amplifier()
        m2 = get_meaning_amplifier()
        assert m1 is m2
    
    def test_record_experience(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        entry = ma.record_experience(
            "Difficult conversation with partner",
            "Honest communication deepens trust",
            "relational",
            0.8,
            0.5,
            0.7,
            "relationships",
        )
        assert entry is not None
        assert entry.experience == "Difficult conversation with partner"
        assert entry.meaning_type == "relational"
    
    def test_get_meaning_stats(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        stats = ma.get_meaning_stats()
        assert isinstance(stats, dict)
    
    def test_get_meaning_practice(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        practice = ma.get_meaning_practice("suffering", "health")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_meaning_score(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        score = ma.get_meaning_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 30 tests successfully')
