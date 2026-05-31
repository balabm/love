with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Gratitude Tracker Tests ---------------------------------------------------

class TestGratitudeTracker:
    """Test Gratitude Tracker."""
    
    def test_singleton(self):
        from core.gratitude_tracker import get_gratitude_tracker
        g1 = get_gratitude_tracker()
        g2 = get_gratitude_tracker()
        assert g1 is g2
    
    def test_log_gratitude(self):
        from core.gratitude_tracker import get_gratitude_tracker
        gt = get_gratitude_tracker()
        entry = gt.log_gratitude("Sunshine", depth=0.8, category="nature", person="")
        assert entry is not None
        assert entry.what == "Sunshine"
    
    def test_get_gratitude_score(self):
        from core.gratitude_tracker import get_gratitude_tracker
        gt = get_gratitude_tracker()
        score = gt.get_gratitude_score()
        assert 0 <= score <= 100
    
    def test_get_gratitude_suggestion(self):
        from core.gratitude_tracker import get_gratitude_tracker
        gt = get_gratitude_tracker()
        suggestion = gt.get_gratitude_suggestion()
        assert "suggestion" in suggestion
        assert "category" in suggestion


# -- Energy Audit Tool Tests ---------------------------------------------------

class TestEnergyAuditTool:
    """Test Energy Audit Tool."""
    
    def test_singleton(self):
        from core.energy_audit_tool import get_energy_audit_tool
        e1 = get_energy_audit_tool()
        e2 = get_energy_audit_tool()
        assert e1 is e2
    
    def test_record_energy(self):
        from core.energy_audit_tool import get_energy_audit_tool
        eat = get_energy_audit_tool()
        record = eat.record_energy("Morning run", before_energy=0.4, after_energy=0.8, activity_type="exercise", duration=30)
        assert record is not None
        assert record.activity == "Morning run"
    
    def test_get_activity_impact(self):
        from core.energy_audit_tool import get_energy_audit_tool
        eat = get_energy_audit_tool()
        impacts = eat.get_activity_impact()
        assert isinstance(impacts, list)
    
    def test_get_recovery_suggestion(self):
        from core.energy_audit_tool import get_energy_audit_tool
        eat = get_energy_audit_tool()
        suggestion = eat.get_recovery_suggestion()
        assert "activity" in suggestion
        assert "expected_boost" in suggestion


# -- Time Audit Tool Tests -----------------------------------------------------

class TestTimeAuditTool:
    """Test Time Audit Tool."""
    
    def test_singleton(self):
        from core.time_audit_tool import get_time_audit_tool
        t1 = get_time_audit_tool()
        t2 = get_time_audit_tool()
        assert t1 is t2
    
    def test_record_time_block(self):
        from core.time_audit_tool import get_time_audit_tool
        tat = get_time_audit_tool()
        block = tat.record_time_block("work", 60, quality=0.8, goal_aligned=True, task="Coding")
        assert block is not None
        assert block.category == "work"
    
    def test_get_time_quality_score(self):
        from core.time_audit_tool import get_time_audit_tool
        tat = get_time_audit_tool()
        score = tat.get_time_quality_score()
        assert 0 <= score <= 100
    
    def test_get_optimization_suggestions(self):
        from core.time_audit_tool import get_time_audit_tool
        tat = get_time_audit_tool()
        suggestions = tat.get_optimization_suggestions()
        assert isinstance(suggestions, list)


# -- Reflection Prompt Generator Tests -----------------------------------------

class TestReflectionPromptGenerator:
    """Test Reflection Prompt Generator."""
    
    def test_singleton(self):
        from core.reflection_prompt_generator import get_reflection_prompt_generator
        r1 = get_reflection_prompt_generator()
        r2 = get_reflection_prompt_generator()
        assert r1 is r2
    
    def test_generate_prompt(self):
        from core.reflection_prompt_generator import get_reflection_prompt_generator
        rpg = get_reflection_prompt_generator()
        prompt = rpg.generate_prompt("test context", "daily", 1)
        assert prompt is not None
        assert len(prompt.prompt) > 0
    
    def test_get_daily_prompt(self):
        from core.reflection_prompt_generator import get_reflection_prompt_generator
        rpg = get_reflection_prompt_generator()
        prompt = rpg.get_daily_prompt()
        assert prompt is not None
        assert prompt.category == "daily"
    
    def test_get_event_prompt(self):
        from core.reflection_prompt_generator import get_reflection_prompt_generator
        rpg = get_reflection_prompt_generator()
        prompt = rpg.get_event_prompt("decision_made", {"decision": "new job"})
        assert prompt is not None
        assert prompt.category == "event"
    
    def test_get_blind_spot_prompt(self):
        from core.reflection_prompt_generator import get_reflection_prompt_generator
        rpg = get_reflection_prompt_generator()
        prompt = rpg.get_blind_spot_prompt()
        assert prompt is not None
        assert prompt.category == "blind_spot"
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 4 tests successfully')
