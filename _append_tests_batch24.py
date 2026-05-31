with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Deep Work Enabler Tests ------------------------------------------------

class TestDeepWorkEnabler:
    """Test Deep Work Enabler."""
    
    def test_singleton(self):
        from core.deep_work_enabler import get_deep_work_enabler
        d1 = get_deep_work_enabler()
        d2 = get_deep_work_enabler()
        assert d1 is d2
    
    def test_record_session(self):
        from core.deep_work_enabler import get_deep_work_enabler
        dwe = get_deep_work_enabler()
        session = dwe.record_session(
            "Write report",
            "writing",
            120,
            0.8,
            0.9,
            0.7,
            2,
            ["Phone", "Email"],
            10,
            5,
            "09:00",
        )
        assert session is not None
        assert session.task == "Write report"
        assert session.depth == 0.8
    
    def test_get_deep_work_stats(self):
        from core.deep_work_enabler import get_deep_work_enabler
        dwe = get_deep_work_enabler()
        stats = dwe.get_deep_work_stats()
        assert isinstance(stats, dict)
    
    def test_get_session_design(self):
        from core.deep_work_enabler import get_deep_work_enabler
        dwe = get_deep_work_enabler()
        design = dwe.get_session_design("coding", 90, 0.7)
        assert isinstance(design, dict)
        assert "structure" in design
    
    def test_get_deep_work_score(self):
        from core.deep_work_enabler import get_deep_work_enabler
        dwe = get_deep_work_enabler()
        score = dwe.get_deep_work_score()
        assert 0 <= score <= 100


# -- Recovery Optimizer Tests -----------------------------------------------

class TestRecoveryOptimizer:
    """Test Recovery Optimizer."""
    
    def test_singleton(self):
        from core.recovery_optimizer import get_recovery_optimizer
        r1 = get_recovery_optimizer()
        r2 = get_recovery_optimizer()
        assert r1 is r2
    
    def test_record_recovery(self):
        from core.recovery_optimizer import get_recovery_optimizer
        ro = get_recovery_optimizer()
        entry = ro.record_recovery(
            "Walk in park",
            "nature",
            0.8,
            "mental",
            30,
            0.3,
            0.7,
        )
        assert entry is not None
        assert entry.activity == "Walk in park"
        assert entry.recovery_type == "nature"
    
    def test_get_recovery_stats(self):
        from core.recovery_optimizer import get_recovery_optimizer
        ro = get_recovery_optimizer()
        stats = ro.get_recovery_stats()
        assert isinstance(stats, dict)
    
    def test_get_recovery_recommendation(self):
        from core.recovery_optimizer import get_recovery_optimizer
        ro = get_recovery_optimizer()
        rec = ro.get_recovery_recommendation("emotional", 20, 0.3)
        assert isinstance(rec, dict)
        assert "recommendation" in rec
    
    def test_get_recovery_score(self):
        from core.recovery_optimizer import get_recovery_optimizer
        ro = get_recovery_optimizer()
        score = ro.get_recovery_score()
        assert 0 <= score <= 100


# -- Peak Performance Tracker Tests -----------------------------------------

class TestPeakPerformanceTracker:
    """Test Peak Performance Tracker."""
    
    def test_singleton(self):
        from core.peak_performance_tracker import get_peak_performance_tracker
        p1 = get_peak_performance_tracker()
        p2 = get_peak_performance_tracker()
        assert p1 is p2
    
    def test_record_performance(self):
        from core.peak_performance_tracker import get_peak_performance_tracker
        ppt = get_peak_performance_tracker()
        entry = ppt.record_performance(
            "Present to board",
            0.9,
            0.85,
            0.8,
            0.9,
            8.0,
            0.3,
            30,
            20,
            "10:00",
            "office",
        )
        assert entry is not None
        assert entry.task == "Present to board"
        assert entry.output_score == 0.9
    
    def test_get_performance_stats(self):
        from core.peak_performance_tracker import get_peak_performance_tracker
        ppt = get_peak_performance_tracker()
        stats = ppt.get_performance_stats()
        assert isinstance(stats, dict)
    
    def test_get_peak_conditions(self):
        from core.peak_performance_tracker import get_peak_performance_tracker
        ppt = get_peak_performance_tracker()
        conditions = ppt.get_peak_conditions("Important demo", "tomorrow")
        assert isinstance(conditions, dict)
        assert "routine" in conditions
    
    def test_get_performance_score(self):
        from core.peak_performance_tracker import get_peak_performance_tracker
        ppt = get_peak_performance_tracker()
        score = ppt.get_performance_score()
        assert 0 <= score <= 100


# -- Mindful Productivity Coach Tests ---------------------------------------

class TestMindfulProductivityCoach:
    """Test Mindful Productivity Coach."""
    
    def test_singleton(self):
        from core.mindful_productivity_coach import get_mindful_productivity_coach
        m1 = get_mindful_productivity_coach()
        m2 = get_mindful_productivity_coach()
        assert m1 is m2
    
    def test_record_block(self):
        from core.mindful_productivity_coach import get_mindful_productivity_coach
        mpc = get_mindful_productivity_coach()
        block = mpc.record_block(
            "Complete project proposal",
            ["Drafted outline", "Researched competitors"],
            0.8,
            0.9,
            0.7,
            0.6,
            0.5,
            "none",
        )
        assert block is not None
        assert block.intention == "Complete project proposal"
        assert block.alignment == 0.9
    
    def test_get_productivity_stats(self):
        from core.mindful_productivity_coach import get_mindful_productivity_coach
        mpc = get_mindful_productivity_coach()
        stats = mpc.get_productivity_stats()
        assert isinstance(stats, dict)
    
    def test_get_mindful_practice(self):
        from core.mindful_productivity_coach import get_mindful_productivity_coach
        mpc = get_mindful_productivity_coach()
        practice = mpc.get_mindful_practice("flow", "perfectionism")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_productivity_score(self):
        from core.mindful_productivity_coach import get_mindful_productivity_coach
        mpc = get_mindful_productivity_coach()
        score = mpc.get_productivity_score()
        assert 0 <= score <= 100
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 24 tests successfully')
