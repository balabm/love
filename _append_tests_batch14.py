with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Self-Compassion Coach Tests --------------------------------------------

class TestSelfCompassionCoach:
    """Test Self-Compassion Coach."""
    
    def test_singleton(self):
        from core.self_compassion_coach import get_self_compassion_coach
        s1 = get_self_compassion_coach()
        s2 = get_self_compassion_coach()
        assert s1 is s2
    
    def test_record_thought(self):
        from core.self_compassion_coach import get_self_compassion_coach
        scc = get_self_compassion_coach()
        thought = scc.record_thought(
            "I'm such a failure",
            "critical",
            "Made a mistake at work",
            "work",
            0.8,
            False,
        )
        assert thought is not None
        assert thought.thought == "I'm such a failure"
        assert thought.talk_type == "critical"
    
    def test_get_self_compassion_stats(self):
        from core.self_compassion_coach import get_self_compassion_coach
        scc = get_self_compassion_coach()
        stats = scc.get_self_compassion_stats()
        assert isinstance(stats, dict)
    
    def test_get_reframe(self):
        from core.self_compassion_coach import get_self_compassion_coach
        scc = get_self_compassion_coach()
        reframe = scc.get_reframe("I'm a failure", "work")
        assert isinstance(reframe, dict)
        assert "mindfulness" in reframe
        assert "self_kindness" in reframe
    
    def test_get_self_compassion_score(self):
        from core.self_compassion_coach import get_self_compassion_coach
        scc = get_self_compassion_coach()
        score = scc.get_self_compassion_score()
        assert 0 <= score <= 100


# -- Forgiveness Tracker Tests ----------------------------------------------

class TestForgivenessTracker:
    """Test Forgiveness Tracker."""
    
    def test_singleton(self):
        from core.forgiveness_tracker import get_forgiveness_tracker
        f1 = get_forgiveness_tracker()
        f2 = get_forgiveness_tracker()
        assert f1 is f2
    
    def test_record_forgiveness(self):
        from core.forgiveness_tracker import get_forgiveness_tracker
        ft = get_forgiveness_tracker()
        f = ft.record_forgiveness(
            "Ex-partner",
            "Cheated",
            "other",
            0.9,
            0.3,
            "letter",
            "release",
            "",
            "Felt lighter after writing",
        )
        assert f is not None
        assert f.who == "Ex-partner"
        assert f.weight_after == 0.3
    
    def test_get_forgiveness_stats(self):
        from core.forgiveness_tracker import get_forgiveness_tracker
        ft = get_forgiveness_tracker()
        stats = ft.get_forgiveness_stats()
        assert isinstance(stats, dict)
    
    def test_get_forgiveness_suggestion(self):
        from core.forgiveness_tracker import get_forgiveness_tracker
        ft = get_forgiveness_tracker()
        suggestion = ft.get_forgiveness_suggestion("Boss", 8, "other")
        assert isinstance(suggestion, dict)
        assert "approach" in suggestion
    
    def test_get_forgiveness_score(self):
        from core.forgiveness_tracker import get_forgiveness_tracker
        ft = get_forgiveness_tracker()
        score = ft.get_forgiveness_score()
        assert 0 <= score <= 100


# -- Vulnerability Builder Tests --------------------------------------------

class TestVulnerabilityBuilder:
    """Test Vulnerability Builder."""
    
    def test_singleton(self):
        from core.vulnerability_builder import get_vulnerability_builder
        v1 = get_vulnerability_builder()
        v2 = get_vulnerability_builder()
        assert v1 is v2
    
    def test_record_vulnerability(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        attempt = vb.record_vulnerability(
            "I feel inadequate at work",
            "Partner",
            "romantic",
            0.6,
            "supportive",
            0.8,
            0.5,
            0.0,
            "Felt closer after sharing",
        )
        assert attempt is not None
        assert attempt.what == "I feel inadequate at work"
        assert attempt.response == "supportive"
    
    def test_get_vulnerability_stats(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        stats = vb.get_vulnerability_stats()
        assert isinstance(stats, dict)
    
    def test_get_vulnerability_suggestion(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        suggestion = vb.get_vulnerability_suggestion("low", "deeper_connection", "romantic")
        assert isinstance(suggestion, dict)
        assert "next_step" in suggestion
    
    def test_get_vulnerability_score(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        score = vb.get_vulnerability_score()
        assert 0 <= score <= 100


# -- Trust Builder Tests ----------------------------------------------------

class TestTrustBuilder:
    """Test Trust Builder."""
    
    def test_singleton(self):
        from core.trust_builder import get_trust_builder
        t1 = get_trust_builder()
        t2 = get_trust_builder()
        assert t1 is t2
    
    def test_record_trust_event(self):
        from core.trust_builder import get_trust_builder
        tb = get_trust_builder()
        event = tb.record_trust_event(
            "Partner",
            "built",
            "consistency",
            0.5,
            "Showed up on time for date night",
            False,
            False,
        )
        assert event is not None
        assert event.person == "Partner"
        assert event.event_type == "built"
    
    def test_get_trust_stats(self):
        from core.trust_builder import get_trust_builder
        tb = get_trust_builder()
        stats = tb.get_trust_stats()
        assert isinstance(stats, dict)
    
    def test_get_repair_guide(self):
        from core.trust_builder import get_trust_builder
        tb = get_trust_builder()
        guide = tb.get_repair_guide("broken_promise", "medium")
        assert isinstance(guide, dict)
        assert "steps" in guide
    
    def test_get_trust_score(self):
        from core.trust_builder import get_trust_builder
        tb = get_trust_builder()
        score = tb.get_trust_score("Partner")
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 14 tests successfully')
