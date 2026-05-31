with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Values Explorer Tests --------------------------------------------------

class TestValuesExplorer:
    """Test Values Explorer."""
    
    def test_singleton(self):
        from core.values_explorer import get_values_explorer
        v1 = get_values_explorer()
        v2 = get_values_explorer()
        assert v1 is v2
    
    def test_record_value(self):
        from core.values_explorer import get_values_explorer
        ve = get_values_explorer()
        entry = ve.record_value(
            "Honesty",
            0.9,
            0.7,
            "personal",
            ["Comfort", "Harmony"],
            "Told truth in difficult conversation",
        )
        assert entry is not None
        assert entry.value == "Honesty"
        assert entry.importance == 0.9
    
    def test_get_values_stats(self):
        from core.values_explorer import get_values_explorer
        ve = get_values_explorer()
        stats = ve.get_values_stats()
        assert isinstance(stats, dict)
    
    def test_get_clarification_exercise(self):
        from core.values_explorer import get_values_explorer
        ve = get_values_explorer()
        exercise = ve.get_clarification_exercise("time", "Health")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_values_score(self):
        from core.values_explorer import get_values_explorer
        ve = get_values_explorer()
        score = ve.get_values_score()
        assert 0 <= score <= 100


# -- Belief Examiner Tests ----------------------------------------------------

class TestBeliefExaminer:
    """Test Belief Examiner."""
    
    def test_singleton(self):
        from core.belief_examiner import get_belief_examiner
        b1 = get_belief_examiner()
        b2 = get_belief_examiner()
        assert b1 is b2
    
    def test_record_belief(self):
        from core.belief_examiner import get_belief_examiner
        be = get_belief_examiner()
        entry = be.record_belief(
            "I am not good enough",
            ["Failed once", "Comparison"],
            0.2,
            0.8,
            0.9,
            0.7,
            "childhood",
        )
        assert entry is not None
        assert entry.belief == "I am not good enough"
        assert entry.rigidity == 0.9
    
    def test_get_belief_stats(self):
        from core.belief_examiner import get_belief_examiner
        be = get_belief_examiner()
        stats = be.get_belief_stats()
        assert isinstance(stats, dict)
    
    def test_get_examination_exercise(self):
        from core.belief_examiner import get_belief_examiner
        be = get_belief_examiner()
        exercise = be.get_examination_exercise("I'm too old to change", 0.8, "culture")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_belief_score(self):
        from core.belief_examiner import get_belief_examiner
        be = get_belief_examiner()
        score = be.get_belief_score()
        assert 0 <= score <= 100


# -- Shadow Integrator Tests ------------------------------------------------

class TestShadowIntegrator:
    """Test Shadow Integrator."""
    
    def test_singleton(self):
        from core.shadow_integrator import get_shadow_integrator
        s1 = get_shadow_integrator()
        s2 = get_shadow_integrator()
        assert s1 is s2
    
    def test_record_shadow(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        entry = si.record_shadow(
            "Anger",
            "Someone cut me off in traffic",
            "Other driver",
            "Yelled",
            "Sat with the feeling",
            0.4,
            0.8,
        )
        assert entry is not None
        assert entry.trait == "Anger"
        assert entry.projection_target == "Other driver"
    
    def test_get_shadow_stats(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        stats = si.get_shadow_stats()
        assert isinstance(stats, dict)
    
    def test_get_integration_exercise(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        exercise = si.get_integration_exercise("Jealousy", 0.7, "Colleague")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_shadow_score(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        score = si.get_shadow_score()
        assert 0 <= score <= 100


# -- Inner Critic Manager Tests ---------------------------------------------

class TestInnerCriticManager:
    """Test Inner Critic Manager."""
    
    def test_singleton(self):
        from core.inner_critic_manager import get_inner_critic_manager
        i1 = get_inner_critic_manager()
        i2 = get_inner_critic_manager()
        assert i1 is i2
    
    def test_record_critic_attack(self):
        from core.inner_critic_manager import get_inner_critic_manager
        icm = get_inner_critic_manager()
        attack = icm.record_critic_attack(
            "You'll never be good enough",
            "Made a small mistake",
            "shamer",
            "worth",
            0.9,
            "Said thank you for trying to protect me",
            0.6,
        )
        assert attack is not None
        assert attack.attack == "You'll never be good enough"
        assert attack.tone == "shamer"
    
    def test_get_critic_stats(self):
        from core.inner_critic_manager import get_inner_critic_manager
        icm = get_inner_critic_manager()
        stats = icm.get_critic_stats()
        assert isinstance(stats, dict)
    
    def test_get_response_strategy(self):
        from core.inner_critic_manager import get_inner_critic_manager
        icm = get_inner_critic_manager()
        strategy = icm.get_response_strategy("perfectionist", 0.8, "work")
        assert isinstance(strategy, dict)
        assert "counter_voice" in strategy
    
    def test_get_critic_score(self):
        from core.inner_critic_manager import get_inner_critic_manager
        icm = get_inner_critic_manager()
        score = icm.get_critic_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 22 tests successfully')
