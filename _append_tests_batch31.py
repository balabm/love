with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Courage Coach Tests ----------------------------------------------------

class TestCourageCoach:
    """Test Courage Coach."""
    
    def test_singleton(self):
        from core.courage_coach import get_courage_coach
        c1 = get_courage_coach()
        c2 = get_courage_coach()
        assert c1 is c2
    
    def test_record_action(self):
        from core.courage_coach import get_courage_coach
        cc = get_courage_coach()
        action = cc.record_action(
            "Gave honest feedback to manager",
            0.7,
            "social",
            "Values alignment",
            0.5,
            "Conversation was productive",
            0.8,
            0.9,
        )
        assert action is not None
        assert action.action == "Gave honest feedback to manager"
        assert action.courage_type == "social"
    
    def test_get_courage_stats(self):
        from core.courage_coach import get_courage_coach
        cc = get_courage_coach()
        stats = cc.get_courage_stats()
        assert isinstance(stats, dict)
    
    def test_get_courage_practice(self):
        from core.courage_coach import get_courage_coach
        cc = get_courage_coach()
        practice = cc.get_courage_practice("social", 0.4)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_courage_score(self):
        from core.courage_coach import get_courage_coach
        cc = get_courage_coach()
        score = cc.get_courage_score()
        assert 0 <= score <= 100


# -- Risk Intelligence Trainer Tests --------------------------------------

class TestRiskIntelligenceTrainer:
    """Test Risk Intelligence Trainer."""
    
    def test_singleton(self):
        from core.risk_intelligence_trainer import get_risk_intelligence_trainer
        r1 = get_risk_intelligence_trainer()
        r2 = get_risk_intelligence_trainer()
        assert r1 is r2
    
    def test_record_risk(self):
        from core.risk_intelligence_trainer import get_risk_intelligence_trainer
        rit = get_risk_intelligence_trainer()
        entry = rit.record_risk(
            "Switched careers",
            "career",
            0.7,
            0.8,
            0.6,
            0.8,
            "Successful transition",
            0.9,
            0.2,
        )
        assert entry is not None
        assert entry.decision == "Switched careers"
        assert entry.risk_type == "career"
    
    def test_get_risk_stats(self):
        from core.risk_intelligence_trainer import get_risk_intelligence_trainer
        rit = get_risk_intelligence_trainer()
        stats = rit.get_risk_stats()
        assert isinstance(stats, dict)
    
    def test_get_risk_suggestion(self):
        from core.risk_intelligence_trainer import get_risk_intelligence_trainer
        rit = get_risk_intelligence_trainer()
        suggestion = rit.get_risk_suggestion("loss_aversion", "financial")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_risk_score(self):
        from core.risk_intelligence_trainer import get_risk_intelligence_trainer
        rit = get_risk_intelligence_trainer()
        score = rit.get_risk_score()
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
        entry = vb.record_vulnerability(
            "Shared fear of failure with mentor",
            "emotional",
            "Mentor",
            0.9,
            "Supportive and validating",
            0.8,
            0.1,
            0.7,
        )
        assert entry is not None
        assert entry.moment == "Shared fear of failure with mentor"
        assert entry.vulnerability_type == "emotional"
    
    def test_get_vulnerability_stats(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        stats = vb.get_vulnerability_stats()
        assert isinstance(stats, dict)
    
    def test_get_vulnerability_practice(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        practice = vb.get_vulnerability_practice("shame", 0.6)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_vulnerability_score(self):
        from core.vulnerability_builder import get_vulnerability_builder
        vb = get_vulnerability_builder()
        score = vb.get_vulnerability_score()
        assert 0 <= score <= 100


# -- Authenticity Amplifier Tests -------------------------------------------

class TestAuthenticityAmplifier:
    """Test Authenticity Amplifier."""
    
    def test_singleton(self):
        from core.authenticity_amplifier import get_authenticity_amplifier
        a1 = get_authenticity_amplifier()
        a2 = get_authenticity_amplifier()
        assert a1 is a2
    
    def test_record_moment(self):
        from core.authenticity_amplifier import get_authenticity_amplifier
        aa = get_authenticity_amplifier()
        moment = aa.record_moment(
            "work",
            0.8,
            0.2,
            0.1,
            0.9,
            "Competent professional",
            "Someone figuring it out",
            0.9,
        )
        assert moment is not None
        assert moment.context == "work"
        assert moment.authenticity == 0.8
    
    def test_get_authenticity_stats(self):
        from core.authenticity_amplifier import get_authenticity_amplifier
        aa = get_authenticity_amplifier()
        stats = aa.get_authenticity_stats()
        assert isinstance(stats, dict)
    
    def test_get_authenticity_practice(self):
        from core.authenticity_amplifier import get_authenticity_amplifier
        aa = get_authenticity_amplifier()
        practice = aa.get_authenticity_practice("work", 0.5)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_authenticity_score(self):
        from core.authenticity_amplifier import get_authenticity_amplifier
        aa = get_authenticity_amplifier()
        score = aa.get_authenticity_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 31 tests successfully')
