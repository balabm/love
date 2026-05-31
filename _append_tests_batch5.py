with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


# -- Proactive Preparation Engine Tests ---------------------------------------

class TestProactivePreparationEngine:
    """Test Proactive Preparation Engine."""
    
    def test_singleton(self):
        from core.proactive_preparation_engine import get_proactive_preparation_engine
        p1 = get_proactive_preparation_engine()
        p2 = get_proactive_preparation_engine()
        assert p1 is p2
    
    def test_suggest_preparation(self):
        from core.proactive_preparation_engine import get_proactive_preparation_engine, UpcomingEvent
        ppe = get_proactive_preparation_engine()
        event = UpcomingEvent(
            event_id="test_meeting",
            title="Team Standup",
            start_time=(__import__("datetime").datetime.now() + __import__("datetime").timedelta(hours=2)).isoformat(),
            event_type="meeting",
            urgency="medium",
        )
        tasks = ppe.suggest_preparation(event)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
    
    def test_get_prep_timeline(self):
        from core.proactive_preparation_engine import get_proactive_preparation_engine
        ppe = get_proactive_preparation_engine()
        timeline = ppe.get_prep_timeline()
        assert isinstance(timeline, list)
    
    def test_check_prep_status(self):
        from core.proactive_preparation_engine import get_proactive_preparation_engine
        ppe = get_proactive_preparation_engine()
        status = ppe.check_prep_status("nonexistent")
        assert status["total_tasks"] == 0


# -- Context Switching Minimizer Tests ----------------------------------------

class TestContextSwitchingMinimizer:
    """Test Context Switching Minimizer."""
    
    def test_singleton(self):
        from core.context_switching_minimizer import get_context_switching_minimizer
        c1 = get_context_switching_minimizer()
        c2 = get_context_switching_minimizer()
        assert c1 is c2
    
    def test_record_task_switch(self):
        from core.context_switching_minimizer import get_context_switching_minimizer
        csm = get_context_switching_minimizer()
        switch = csm.record_task_switch("Email", "admin", switch_time=30, recovery_time=60)
        assert switch is not None
        assert switch.to_task == "Email"
    
    def test_get_switch_stats(self):
        from core.context_switching_minimizer import get_context_switching_minimizer
        csm = get_context_switching_minimizer()
        stats = csm.get_switch_stats()
        assert isinstance(stats, dict)
    
    def test_protect_flow(self):
        from core.context_switching_minimizer import get_context_switching_minimizer
        csm = get_context_switching_minimizer()
        protection = csm.protect_flow("Coding", "development")
        assert "flow_state" in protection
        assert "recommendations" in protection


# -- Task Batch Optimizer Tests -----------------------------------------------

class TestTaskBatchOptimizer:
    """Test Task Batch Optimizer."""
    
    def test_singleton(self):
        from core.task_batch_optimizer import get_task_batch_optimizer
        t1 = get_task_batch_optimizer()
        t2 = get_task_batch_optimizer()
        assert t1 is t2
    
    def test_add_task(self):
        from core.task_batch_optimizer import get_task_batch_optimizer
        tbo = get_task_batch_optimizer()
        task = tbo.add_task("Review PR", "coding", "medium", 15, ["ide"])
        assert task is not None
        assert task.title == "Review PR"
    
    def test_optimize_batches(self):
        from core.task_batch_optimizer import get_task_batch_optimizer
        tbo = get_task_batch_optimizer()
        tbo.add_task("Email reply", "admin", "low", 5)
        tbo.add_task("Schedule meeting", "admin", "low", 10)
        batches = tbo.optimize_batches()
        assert isinstance(batches, list)
    
    def test_get_execution_plan(self):
        from core.task_batch_optimizer import get_task_batch_optimizer
        tbo = get_task_batch_optimizer()
        plan = tbo.get_execution_plan()
        assert isinstance(plan, list)


# -- Meeting Optimizer Tests ---------------------------------------------------

class TestMeetingOptimizer:
    """Test Meeting Optimizer."""
    
    def test_singleton(self):
        from core.meeting_optimizer import get_meeting_optimizer
        m1 = get_meeting_optimizer()
        m2 = get_meeting_optimizer()
        assert m1 is m2
    
    def test_record_meeting(self):
        from core.meeting_optimizer import get_meeting_optimizer
        mo = get_meeting_optimizer()
        meeting = mo.record_meeting(
            title="Team Standup",
            scheduled_minutes=30,
            actual_minutes=25,
            attendee_count=5,
            active_participants=4,
            had_agenda=True,
            outcome="productive",
            outcome_quality=0.8,
            meeting_type="standup",
        )
        assert meeting is not None
        assert meeting.title == "Team Standup"
    
    def test_get_efficiency_score(self):
        from core.meeting_optimizer import get_meeting_optimizer
        mo = get_meeting_optimizer()
        score = mo.get_efficiency_score()
        assert 0 <= score <= 100
    
    def test_get_optimization_suggestions(self):
        from core.meeting_optimizer import get_meeting_optimizer
        mo = get_meeting_optimizer()
        suggestions = mo.get_optimization_suggestions()
        assert isinstance(suggestions, list)
    
    def test_get_meeting_free_blocks(self):
        from core.meeting_optimizer import get_meeting_optimizer
        mo = get_meeting_optimizer()
        blocks = mo.get_meeting_free_blocks()
        assert isinstance(blocks, list)
        assert len(blocks) > 0
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 5 tests successfully')
