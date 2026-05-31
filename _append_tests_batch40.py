import os

p = r'c:/Users/balab/OneDrive/Documents/Projects/LLove/love/tests/test_modern_engines.py'

append = '''

# -- Longevity Optimizer Tests ---------------------------------------------------

class TestLongevityOptimizer:
    """Test Longevity Optimizer."""

    def test_singleton(self):
        from core.longevity_optimizer import get_longevity_optimizer
        l1 = get_longevity_optimizer()
        l2 = get_longevity_optimizer()
        assert l1 is l2

    def test_record_practice(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        entry = lo.record_practice(
            "Morning walk",
            "movement",
            0.6,
            0.7,
            0.6,
            0.5,
            0.9,
            "Daily habit",
        )
        assert entry is not None
        assert entry.practice == "Morning walk"
        assert entry.practice_type == "movement"

    def test_get_longevity_stats(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        stats = lo.get_longevity_stats()
        assert isinstance(stats, dict)

    def test_get_practice_suggestion(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        suggestion = lo.get_practice_suggestion(45, 0.7, "fatigue")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_longevity_score(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        score = lo.get_longevity_score()
        assert 0 <= score <= 100


# -- Vitality Tracker Tests ---------------------------------------------------

class TestVitalityTracker:
    """Test Vitality Tracker."""

    def test_singleton(self):
        from core.vitality_tracker import get_vitality_tracker
        v1 = get_vitality_tracker()
        v2 = get_vitality_tracker()
        assert v1 is v2

    def test_record_vitality(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        entry = vt.record_vitality(
            0.8,
            0.9,
            0.7,
            0.8,
            0.85,
            0.9,
            0.7,
            0.8,
            0.9,
            0.2,
            5,
            "Great day",
        )
        assert entry is not None
        assert entry.vitality == 0.8
        assert entry.peak_hours == 5

    def test_get_vitality_stats(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        stats = vt.get_vitality_stats()
        assert isinstance(stats, dict)

    def test_get_vitality_suggestion(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        suggestion = vt.get_vitality_suggestion("depleted", "burnout")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_vitality_score(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        score = vt.get_vitality_score()
        assert 0 <= score <= 100


# -- Age Reversal Coach Tests ---------------------------------------------------

class TestAgeReversalCoach:
    """Test Age Reversal Coach."""

    def test_singleton(self):
        from core.age_reversal_coach import get_age_reversal_coach
        a1 = get_age_reversal_coach()
        a2 = get_age_reversal_coach()
        assert a1 is a2

    def test_record_practice(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        entry = arc.record_practice(
            "Cold shower finish",
            "cold",
            0.6,
            0.7,
            0.6,
            0.5,
            0.8,
            "Energizing",
        )
        assert entry is not None
        assert entry.practice == "Cold shower finish"
        assert entry.practice_type == "cold"

    def test_get_reversal_stats(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        stats = arc.get_reversal_stats()
        assert isinstance(stats, dict)

    def test_get_practice_suggestion(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        suggestion = arc.get_practice_suggestion(50, 0.6, "stiffness")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_reversal_score(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        score = arc.get_reversal_score()
        assert 0 <= score <= 100


# -- Life Phase Navigator Tests ---------------------------------------------------

class TestLifePhaseNavigator:
    """Test Life Phase Navigator."""

    def test_singleton(self):
        from core.life_phase_navigator import get_life_phase_navigator
        l1 = get_life_phase_navigator()
        l2 = get_life_phase_navigator()
        assert l1 is l2

    def test_record_phase(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        entry = lpn.record_phase(
            "Senior developer role",
            "career",
            0.7,
            0.5,
            0.3,
            36,
            0.8,
            0.4,
            "Comfortable but plateauing",
        )
        assert entry is not None
        assert entry.phase == "Senior developer role"
        assert entry.phase_type == "career"

    def test_get_phase_stats(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        stats = lpn.get_phase_stats()
        assert isinstance(stats, dict)

    def test_get_transition_suggestion(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        suggestion = lpn.get_transition_suggestion("career", 0.7, "restless")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_phase_score(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        score = lpn.get_phase_score()
        assert 0 <= score <= 100
'''

with open(p, "a") as f:
    f.write(append)
print("Appended batch 40 tests")
