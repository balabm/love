with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Emergency Preparedness Tracker Tests -----------------------------------

class TestEmergencyPreparednessTracker:
    """Test Emergency Preparedness Tracker."""
    
    def test_singleton(self):
        from core.emergency_preparedness_tracker import get_emergency_preparedness_tracker
        e1 = get_emergency_preparedness_tracker()
        e2 = get_emergency_preparedness_tracker()
        assert e1 is e2
    
    def test_record_supply(self):
        from core.emergency_preparedness_tracker import get_emergency_preparedness_tracker
        ept = get_emergency_preparedness_tracker()
        supply = ept.record_supply("water", " bottled water", 14, "gallons", "2027-01-01", "good")
        assert supply is not None
        assert supply.category == "water"
        assert supply.quantity == 14
    
    def test_record_drill(self):
        from core.emergency_preparedness_tracker import get_emergency_preparedness_tracker
        ept = get_emergency_preparedness_tracker()
        drill = ept.record_drill("fire", 15, 0.8, ["slow exit"], ["practice faster"])
        assert drill is not None
        assert drill.scenario == "fire"
        assert drill.effectiveness == 0.8
    
    def test_get_readiness_score(self):
        from core.emergency_preparedness_tracker import get_emergency_preparedness_tracker
        ept = get_emergency_preparedness_tracker()
        score = ept.get_readiness_score()
        assert isinstance(score, dict)
        assert "overall_score" in score
    
    def test_get_preparation_gaps(self):
        from core.emergency_preparedness_tracker import get_emergency_preparedness_tracker
        ept = get_emergency_preparedness_tracker()
        gaps = ept.get_preparation_gaps()
        assert isinstance(gaps, list)


# -- Home Maintenance Scheduler Tests ---------------------------------------

class TestHomeMaintenanceScheduler:
    """Test Home Maintenance Scheduler."""
    
    def test_singleton(self):
        from core.home_maintenance_scheduler import get_home_maintenance_scheduler
        h1 = get_home_maintenance_scheduler()
        h2 = get_home_maintenance_scheduler()
        assert h1 is h2
    
    def test_record_maintenance(self):
        from core.home_maintenance_scheduler import get_home_maintenance_scheduler
        hms = get_home_maintenance_scheduler()
        record = hms.record_maintenance("hvac", "filter change", 25, "DIY", "fair", "good", 30)
        assert record is not None
        assert record.system == "hvac"
        assert record.cost == 25
    
    def test_schedule_task(self):
        from core.home_maintenance_scheduler import get_home_maintenance_scheduler
        hms = get_home_maintenance_scheduler()
        task = hms.schedule_task("plumbing", "inspection", 180, "medium", 150)
        assert task is not None
        assert task.system == "plumbing"
        assert task.frequency_days == 180
    
    def test_get_maintenance_status(self):
        from core.home_maintenance_scheduler import get_home_maintenance_scheduler
        hms = get_home_maintenance_scheduler()
        status = hms.get_maintenance_status()
        assert isinstance(status, dict)
        assert "system_status" in status
    
    def test_get_cost_analysis(self):
        from core.home_maintenance_scheduler import get_home_maintenance_scheduler
        hms = get_home_maintenance_scheduler()
        analysis = hms.get_cost_analysis()
        assert isinstance(analysis, dict)


# -- Career Path Mapper Tests -----------------------------------------------

class TestCareerPathMapper:
    """Test Career Path Mapper."""
    
    def test_singleton(self):
        from core.career_path_mapper import get_career_path_mapper
        c1 = get_career_path_mapper()
        c2 = get_career_path_mapper()
        assert c1 is c2
    
    def test_record_role(self):
        from core.career_path_mapper import get_career_path_mapper
        cpm = get_career_path_mapper()
        role = cpm.record_role(
            "Senior Engineer", "TechCorp", "Engineering",
            "2023-01-01", None,
            ["Python", "Leadership", "Architecture"],
            ["Led migration", "Reduced latency 40%"],
            0.8, 0.7, 0.75,
        )
        assert role is not None
        assert role.title == "Senior Engineer"
        assert role.satisfaction == 0.8
    
    def test_add_goal(self):
        from core.career_path_mapper import get_career_path_mapper
        cpm = get_career_path_mapper()
        cpm.add_goal("Engineering Manager", "2027-01-01", ["Leadership", "Communication", "Strategy"])
        assert "Engineering Manager" in cpm._goals
    
    def test_get_career_trajectory(self):
        from core.career_path_mapper import get_career_path_mapper
        cpm = get_career_path_mapper()
        trajectory = cpm.get_career_trajectory()
        assert isinstance(trajectory, dict)
    
    def test_get_next_role_suggestions(self):
        from core.career_path_mapper import get_career_path_mapper
        cpm = get_career_path_mapper()
        suggestions = cpm.get_next_role_suggestions()
        assert isinstance(suggestions, list)


# -- Skill Gap Analyzer Tests -------------------------------------------------

class TestSkillGapAnalyzer:
    """Test Skill Gap Analyzer."""
    
    def test_singleton(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        s1 = get_skill_gap_analyzer()
        s2 = get_skill_gap_analyzer()
        assert s1 is s2
    
    def test_record_skill(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        sga = get_skill_gap_analyzer()
        skill = sga.record_skill("Python", 0.8, "technical", 15, ["web_app", "data_pipeline"], 200, "AWS Certified")
        assert skill is not None
        assert skill.name == "Python"
        assert skill.proficiency == 0.8
    
    def test_add_target(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        sga = get_skill_gap_analyzer()
        sga.add_target("Machine Learning", 0.7, "high", "technical", "Required for AI role")
        assert "machine_learning" in sga._targets
    
    def test_analyze_gaps(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        sga = get_skill_gap_analyzer()
        sga.add_target("Rust", 0.6, "medium", "technical", "Systems programming")
        analysis = sga.analyze_gaps()
        assert isinstance(analysis, dict)
        assert "gaps" in analysis
    
    def test_get_learning_priority(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        sga = get_skill_gap_analyzer()
        plan = sga.get_learning_priority()
        assert isinstance(plan, list)
    
    def test_get_skill_health_score(self):
        from core.skill_gap_analyzer import get_skill_gap_analyzer
        sga = get_skill_gap_analyzer()
        score = sga.get_skill_health_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 10 tests successfully')
