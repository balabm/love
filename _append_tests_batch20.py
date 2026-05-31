with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Energy Protector Tests -------------------------------------------------

class TestEnergyProtector:
    """Test Energy Protector."""
    
    def test_singleton(self):
        from core.energy_protector import get_energy_protector
        e1 = get_energy_protector()
        e2 = get_energy_protector()
        assert e1 is e2
    
    def test_record_energy_event(self):
        from core.energy_protector import get_energy_protector
        ep = get_energy_protector()
        event = ep.record_energy_event(
            "drain",
            "Long meeting",
            "task",
            -0.7,
            90,
            0.8,
            0.3,
            "14:00",
            True,
        )
        assert event is not None
        assert event.source == "Long meeting"
        assert event.impact == -0.7
    
    def test_get_energy_stats(self):
        from core.energy_protector import get_energy_protector
        ep = get_energy_protector()
        stats = ep.get_energy_stats()
        assert isinstance(stats, dict)
    
    def test_get_protection_strategy(self):
        from core.energy_protector import get_energy_protector
        ep = get_energy_protector()
        strategy = ep.get_protection_strategy(0.3, ["Meeting", "Presentation"], 15)
        assert isinstance(strategy, dict)
        assert "actions" in strategy
    
    def test_get_energy_score(self):
        from core.energy_protector import get_energy_protector
        ep = get_energy_protector()
        score = ep.get_energy_score()
        assert 0 <= score <= 100


# -- Boundary Enforcer Tests ------------------------------------------------

class TestBoundaryEnforcer:
    """Test Boundary Enforcer."""
    
    def test_singleton(self):
        from core.boundary_enforcer import get_boundary_enforcer
        b1 = get_boundary_enforcer()
        b2 = get_boundary_enforcer()
        assert b1 is b2
    
    def test_record_boundary(self):
        from core.boundary_enforcer import get_boundary_enforcer
        be = get_boundary_enforcer()
        event = be.record_boundary(
            "No work emails after 7pm",
            "time",
            False,
            "self",
            "Guilt about pending task",
            0.6,
            "Checked email anyway",
            0.2,
        )
        assert event is not None
        assert event.boundary == "No work emails after 7pm"
        assert event.maintained is False
    
    def test_get_boundary_stats(self):
        from core.boundary_enforcer import get_boundary_enforcer
        be = get_boundary_enforcer()
        stats = be.get_boundary_stats()
        assert isinstance(stats, dict)
    
    def test_get_boundary_script(self):
        from core.boundary_enforcer import get_boundary_enforcer
        be = get_boundary_enforcer()
        script = be.get_boundary_script("Friend asked to borrow money", "emotional", "friend")
        assert isinstance(script, dict)
        assert "script" in script
    
    def test_get_boundary_score(self):
        from core.boundary_enforcer import get_boundary_enforcer
        be = get_boundary_enforcer()
        score = be.get_boundary_score()
        assert 0 <= score <= 100


# -- Time Sovereign Tests ---------------------------------------------------

class TestTimeSovereign:
    """Test Time Sovereign."""
    
    def test_singleton(self):
        from core.time_sovereign import get_time_sovereign
        t1 = get_time_sovereign()
        t2 = get_time_sovereign()
        assert t1 is t2
    
    def test_record_time_block(self):
        from core.time_sovereign import get_time_sovereign
        ts = get_time_sovereign()
        block = ts.record_time_block(
            "Deep work on project",
            "deep_work",
            120,
            90,
            0.9,
            "high",
            "09:00",
            True,
        )
        assert block is not None
        assert block.activity == "Deep work on project"
        assert block.interrupted is True
    
    def test_get_time_stats(self):
        from core.time_sovereign import get_time_sovereign
        ts = get_time_sovereign()
        stats = ts.get_time_stats()
        assert isinstance(stats, dict)
    
    def test_get_sovereignty_suggestion(self):
        from core.time_sovereign import get_time_sovereign
        ts = get_time_sovereign()
        suggestion = ts.get_sovereignty_suggestion("meetings", "reclaim_time", 15)
        assert isinstance(suggestion, dict)
        assert "tactic" in suggestion
    
    def test_get_time_score(self):
        from core.time_sovereign import get_time_sovereign
        ts = get_time_sovereign()
        score = ts.get_time_score()
        assert 0 <= score <= 100


# -- Attention Guardian Tests -----------------------------------------------

class TestAttentionGuardian:
    """Test Attention Guardian."""
    
    def test_singleton(self):
        from core.attention_guardian import get_attention_guardian
        a1 = get_attention_guardian()
        a2 = get_attention_guardian()
        assert a1 is a2
    
    def test_record_attention(self):
        from core.attention_guardian import get_attention_guardian
        ag = get_attention_guardian()
        event = ag.record_attention(
            "Writing chapter",
            "creation",
            90,
            0.8,
            0.9,
            True,
            "Phone notification",
            0.9,
        )
        assert event is not None
        assert event.investment == "Writing chapter"
        assert event.fragmented is True
    
    def test_get_attention_stats(self):
        from core.attention_guardian import get_attention_guardian
        ag = get_attention_guardian()
        stats = ag.get_attention_stats()
        assert isinstance(stats, dict)
    
    def test_get_protection_strategy(self):
        from core.attention_guardian import get_attention_guardian
        ag = get_attention_guardian()
        strategy = ag.get_protection_strategy("phone", 0.4, "work")
        assert isinstance(strategy, dict)
        assert "defense" in strategy
    
    def test_get_attention_score(self):
        from core.attention_guardian import get_attention_guardian
        ag = get_attention_guardian()
        score = ag.get_attention_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 20 tests successfully')
