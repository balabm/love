import re

with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

appendix = '''

# -- Deep Listener Tests -----------------------------------------------------

class TestDeepListener:
    """Test Deep Listener."""

    def test_singleton(self):
        from core.deep_listener import get_deep_listener
        l1 = get_deep_listener()
        l2 = get_deep_listener()
        assert l1 is l2

    def test_record_session(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        session = dl.record_session(
            "Partner",
            "Career change",
            "empathetic",
            0.8,
            0.9,
            0.85,
            0,
            3,
            "Really heard them",
        )
        assert session is not None
        assert session.speaker == "Partner"
        assert session.comprehension == 0.8

    def test_get_listening_stats(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        stats = dl.get_listening_stats()
        assert isinstance(stats, dict)

    def test_get_listening_practice(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        practice = dl.get_listening_practice("emotional", 0.6)
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_listening_score(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        score = dl.get_listening_score()
        assert 0 <= score <= 100


# -- Conflict Navigator Tests ------------------------------------------------

class TestConflictNavigator:
    """Test Conflict Navigator."""

    def test_singleton(self):
        from core.conflict_navigator import get_conflict_navigator
        n1 = get_conflict_navigator()
        n2 = get_conflict_navigator()
        assert n1 is n2

    def test_record_conflict(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        entry = cn.record_conflict(
            "Roommate",
            "resource",
            0.6,
            "compromise",
            0.8,
            "resolved",
            0.9,
            "Found middle ground",
        )
        assert entry is not None
        assert entry.party == "Roommate"
        assert entry.outcome == "resolved"

    def test_get_conflict_stats(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        stats = cn.get_conflict_stats()
        assert isinstance(stats, dict)

    def test_get_resolution_strategy(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        strategy = cn.get_resolution_strategy("emotional", 0.7)
        assert isinstance(strategy, dict)
        assert "strategy" in strategy

    def test_get_conflict_score(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        score = cn.get_conflict_score()
        assert 0 <= score <= 100


# -- Assertiveness Builder Tests ---------------------------------------------

class TestAssertivenessBuilder:
    """Test Assertiveness Builder."""

    def test_singleton(self):
        from core.assertiveness_builder import get_assertiveness_builder
        b1 = get_assertiveness_builder()
        b2 = get_assertiveness_builder()
        assert b1 is b2

    def test_record_interaction(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        entry = ab.record_interaction(
            "Asked for raise",
            "request",
            "direct",
            0.7,
            0.9,
            0.8,
            "positive",
            "Got it",
        )
        assert entry is not None
        assert entry.situation == "Asked for raise"
        assert entry.outcome == "positive"

    def test_get_assertiveness_stats(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        stats = ab.get_assertiveness_stats()
        assert isinstance(stats, dict)

    def test_get_assertiveness_script(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        script = ab.get_assertiveness_script("work", "boundary")
        assert isinstance(script, dict)
        assert "script" in script

    def test_get_assertiveness_score(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        score = ab.get_assertiveness_score()
        assert 0 <= score <= 100


# -- Boundary Architect Tests ------------------------------------------------

class TestBoundaryArchitect:
    """Test Boundary Architect."""

    def test_singleton(self):
        from core.boundary_architect import get_boundary_architect
        a1 = get_boundary_architect()
        a2 = get_boundary_architect()
        assert a1 is a2

    def test_record_boundary(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        entry = ba.record_boundary(
            "time",
            "No meetings after 6pm",
            0.9,
            False,
            0.4,
            0.8,
            0.1,
            "protected",
            "Respected",
        )
        assert entry is not None
        assert entry.domain == "time"
        assert entry.outcome == "protected"

    def test_get_boundary_stats(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        stats = ba.get_boundary_stats()
        assert isinstance(stats, dict)

    def test_get_boundary_script(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        script = ba.get_boundary_script("digital", "weekend work messages")
        assert isinstance(script, dict)
        assert "script" in script

    def test_get_boundary_score(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        score = ba.get_boundary_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'a', encoding='utf-8') as f:
    f.write(appendix)

print('Appended 20 tests for batch 33 (Deep Listener, Conflict Navigator, Assertiveness Builder, Boundary Architect)')
