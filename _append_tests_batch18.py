with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Resilience Builder Tests -----------------------------------------------

class TestResilienceBuilder:
    """Test Resilience Builder."""
    
    def test_singleton(self):
        from core.resilience_builder import get_resilience_builder
        r1 = get_resilience_builder()
        r2 = get_resilience_builder()
        assert r1 is r2
    
    def test_record_setback(self):
        from core.resilience_builder import get_resilience_builder
        rb = get_resilience_builder()
        setback = rb.record_setback(
            "Lost job",
            "work",
            0.8,
            "shock",
            ["Updated resume", "Networked"],
            ["Partner", "Friend"],
            14,
            ["I can survive uncertainty", "My network is strong"],
            0.7,
        )
        assert setback is not None
        assert setback.event == "Lost job"
        assert setback.category == "work"
    
    def test_get_resilience_stats(self):
        from core.resilience_builder import get_resilience_builder
        rb = get_resilience_builder()
        stats = rb.get_resilience_stats()
        assert isinstance(stats, dict)
    
    def test_get_recovery_suggestion(self):
        from core.resilience_builder import get_resilience_builder
        rb = get_resilience_builder()
        suggestion = rb.get_recovery_suggestion("work", "shock", 0.8)
        assert isinstance(suggestion, dict)
        assert "immediate_response" in suggestion
    
    def test_get_resilience_score(self):
        from core.resilience_builder import get_resilience_builder
        rb = get_resilience_builder()
        score = rb.get_resilience_score()
        assert 0 <= score <= 100


# -- Growth Mindset Coach Tests ---------------------------------------------

class TestGrowthMindsetCoach:
    """Test Growth Mindset Coach."""
    
    def test_singleton(self):
        from core.growth_mindset_coach import get_growth_mindset_coach
        g1 = get_growth_mindset_coach()
        g2 = get_growth_mindset_coach()
        assert g1 is g2
    
    def test_record_mindset_moment(self):
        from core.growth_mindset_coach import get_growth_mindset_coach
        gmc = get_growth_mindset_coach()
        moment = gmc.record_mindset_moment(
            "Failed presentation",
            "failure",
            "I'm not a good speaker",
            "I can learn to present better with practice",
            "leadership",
            "growth",
            "improved",
            0.8,
            3,
            True,
        )
        assert moment is not None
        assert moment.fixed_response == "I'm not a good speaker"
        assert moment.mindset_used == "growth"
    
    def test_get_mindset_stats(self):
        from core.growth_mindset_coach import get_growth_mindset_coach
        gmc = get_growth_mindset_coach()
        stats = gmc.get_mindset_stats()
        assert isinstance(stats, dict)
    
    def test_get_reframe(self):
        from core.growth_mindset_coach import get_growth_mindset_coach
        gmc = get_growth_mindset_coach()
        reframe = gmc.get_reframe("I'm not smart enough", "intelligence")
        assert isinstance(reframe, dict)
        assert "growth" in reframe
    
    def test_get_growth_mindset_score(self):
        from core.growth_mindset_coach import get_growth_mindset_coach
        gmc = get_growth_mindset_coach()
        score = gmc.get_growth_mindset_score()
        assert 0 <= score <= 100


# -- Adaptability Trainer Tests ---------------------------------------------

class TestAdaptabilityTrainer:
    """Test Adaptability Trainer."""
    
    def test_singleton(self):
        from core.adaptability_trainer import get_adaptability_trainer
        a1 = get_adaptability_trainer()
        a2 = get_adaptability_trainer()
        assert a1 is a2
    
    def test_record_adaptation(self):
        from core.adaptability_trainer import get_adaptability_trainer
        at = get_adaptability_trainer()
        adaptation = at.record_adaptation(
            "Moved to new city",
            "imposed",
            "large",
            0.3,
            0.7,
            "slow",
            ["Explored neighborhoods", "Joined clubs"],
            ["Family"],
            "coping",
            0.6,
        )
        assert adaptation is not None
        assert adaptation.change == "Moved to new city"
        assert adaptation.outcome == "coping"
    
    def test_get_adaptability_stats(self):
        from core.adaptability_trainer import get_adaptability_trainer
        at = get_adaptability_trainer()
        stats = at.get_adaptability_stats()
        assert isinstance(stats, dict)
    
    def test_get_adaptation_strategy(self):
        from core.adaptability_trainer import get_adaptability_trainer
        at = get_adaptability_trainer()
        strategy = at.get_adaptation_strategy("imposed", 0.7, "large")
        assert isinstance(strategy, dict)
        assert "approach" in strategy
    
    def test_get_adaptability_score(self):
        from core.adaptability_trainer import get_adaptability_trainer
        at = get_adaptability_trainer()
        score = at.get_adaptability_score()
        assert 0 <= score <= 100


# -- Antifragility Tracker Tests --------------------------------------------

class TestAntifragilityTracker:
    """Test Antifragility Tracker."""
    
    def test_singleton(self):
        from core.antifragility_tracker import get_antifragility_tracker
        a1 = get_antifragility_tracker()
        a2 = get_antifragility_tracker()
        assert a1 is a2
    
    def test_record_stressor(self):
        from core.antifragility_tracker import get_antifragility_tracker
        aft = get_antifragility_tracker()
        stressor = aft.record_stressor(
            "Public speaking",
            "emotional",
            "moderate",
            2,
            "stronger",
            0.8,
            24,
            0.6,
            0.8,
        )
        assert stressor is not None
        assert stressor.stressor == "Public speaking"
        assert stressor.effect == "stronger"
    
    def test_get_antifragility_stats(self):
        from core.antifragility_tracker import get_antifragility_tracker
        aft = get_antifragility_tracker()
        stats = aft.get_antifragility_stats()
        assert isinstance(stats, dict)
    
    def test_get_hormesis_suggestion(self):
        from core.antifragility_tracker import get_antifragility_tracker
        aft = get_antifragility_tracker()
        suggestion = aft.get_hormesis_suggestion(0.7, "growth", "physical")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_antifragility_score(self):
        from core.antifragility_tracker import get_antifragility_tracker
        aft = get_antifragility_tracker()
        score = aft.get_antifragility_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 18 tests successfully')
