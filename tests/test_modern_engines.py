


# -- Habit Streak Tracker Tests ------------------------------------------------

class TestHabitStreakTracker:
    """Test Habit Streak Tracker."""
    
    def test_singleton(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        h1 = get_habit_streak_tracker()
        h2 = get_habit_streak_tracker()
        assert h1 is h2
    
    def test_record_habit_and_get_streaks(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        hst.record_habit("test_habit", "Test Habit", completed=True)
        streaks = hst.get_streaks()
        assert len(streaks) > 0
        assert streaks[0].habit_id == "test_habit"
    
    def test_momentum_score(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        score = hst.get_momentum_score("test_habit")
        assert 0 <= score <= 1
    
    def test_detect_slipping(self):
        from core.habit_streak_tracker import get_habit_streak_tracker
        hst = get_habit_streak_tracker()
        slipping = hst.detect_slipping()
        assert isinstance(slipping, list)


# -- Sleep Analyzer Tests ------------------------------------------------------

class TestSleepAnalyzer:
    """Test Sleep Analyzer."""
    
    def test_singleton(self):
        from core.sleep_analyzer import get_sleep_analyzer
        s1 = get_sleep_analyzer()
        s2 = get_sleep_analyzer()
        assert s1 is s2
    
    def test_record_sleep(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(hours=8)).isoformat()
        end = datetime.now().isoformat()
        session = sa.record_sleep(start, end, quality=0.8)
        assert session is not None
        assert session.duration_hours > 0
    
    def test_get_sleep_score(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        score = sa.get_sleep_score()
        assert 0 <= score <= 100
    
    def test_get_recommendations(self):
        from core.sleep_analyzer import get_sleep_analyzer
        sa = get_sleep_analyzer()
        recs = sa.get_recommendations()
        assert isinstance(recs, list)


# -- Social Connection Monitor Tests -------------------------------------------

class TestSocialConnectionMonitor:
    """Test Social Connection Monitor."""
    
    def test_singleton(self):
        from core.social_connection_monitor import get_social_connection_monitor
        s1 = get_social_connection_monitor()
        s2 = get_social_connection_monitor()
        assert s1 is s2
    
    def test_record_interaction(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        scm.record_interaction("Alice", "message", quality=0.8, duration=5.0)
        insights = scm.get_social_insights()
        assert insights.get("status") != "insufficient_data" or insights.get("total_interactions") is not None
    
    def test_get_social_score(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        score = scm.get_social_score()
        assert 0 <= score <= 100
    
    def test_get_reconnection_suggestions(self):
        from core.social_connection_monitor import get_social_connection_monitor
        scm = get_social_connection_monitor()
        suggestions = scm.get_reconnection_suggestions()
        assert isinstance(suggestions, list)


# -- Learning Path Optimizer Tests ---------------------------------------------

class TestLearningPathOptimizer:
    """Test Learning Path Optimizer."""
    
    def test_singleton(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        l1 = get_learning_path_optimizer()
        l2 = get_learning_path_optimizer()
        assert l1 is l2
    
    def test_add_skill(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python", level=0.3, prerequisites=["Basics"])
        stats = lpo.get_learning_stats()
        assert stats["total_skills"] > 0
    
    def test_record_review(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python")
        lpo.record_review("Python", performance=0.8, duration=30.0)
        stats = lpo.get_learning_stats()
        assert stats["total_reviews"] > 0
    
    def test_suggest_next_topic(self):
        from core.learning_path_optimizer import get_learning_path_optimizer
        lpo = get_learning_path_optimizer()
        lpo.add_skill("Python", level=0.3)
        suggestions = lpo.suggest_next_topic("Python")
        assert isinstance(suggestions, list)



# -- Focus Recovery Tracker Tests -----------------------------------------------

class TestFocusRecoveryTracker:
    """Test Focus Recovery Tracker."""
    
    def test_singleton(self):
        from core.focus_recovery_tracker import get_focus_recovery_tracker
        f1 = get_focus_recovery_tracker()
        f2 = get_focus_recovery_tracker()
        assert f1 is f2
    
    def test_record_session(self):
        from core.focus_recovery_tracker import get_focus_recovery_tracker
        frt = get_focus_recovery_tracker()
        session = frt.record_session(duration=25, depth=0.8, interruptions=0, task_type="coding")
        assert session is not None
        assert session.duration_minutes == 25
    
    def test_get_focus_stats(self):
        from core.focus_recovery_tracker import get_focus_recovery_tracker
        frt = get_focus_recovery_tracker()
        stats = frt.get_focus_stats()
        assert isinstance(stats, dict)
    
    def test_get_recovery_recommendation(self):
        from core.focus_recovery_tracker import get_focus_recovery_tracker
        frt = get_focus_recovery_tracker()
        rec = frt.get_recovery_recommendation()
        assert "activity" in rec
        assert "duration" in rec


# -- Decision Journal Tests ----------------------------------------------------

class TestDecisionJournal:
    """Test Decision Journal."""
    
    def test_singleton(self):
        from core.decision_journal import get_decision_journal
        d1 = get_decision_journal()
        d2 = get_decision_journal()
        assert d1 is d2
    
    def test_log_decision(self):
        from core.decision_journal import get_decision_journal
        dj = get_decision_journal()
        decision = dj.log_decision(
            context="Should I take the new job?",
            options=["Stay", "Leave"],
            choice="Leave",
            expected_outcome="Better growth",
            category="career",
            confidence=0.7,
        )
        assert decision is not None
        assert decision.choice == "Leave"
    
    def test_review_decision(self):
        from core.decision_journal import get_decision_journal
        dj = get_decision_journal()
        decision = dj.log_decision("Test", ["A", "B"], "A", "Good")
        dj.review_decision(decision.decision_id, "Actually great", 0.9)
        assert dj._decisions[decision.decision_id].outcome_quality == 0.9
    
    def test_get_framework_suggestion(self):
        from core.decision_journal import get_decision_journal
        dj = get_decision_journal()
        framework = dj.get_framework_suggestion("emotional choice", "emotional")
        assert "name" in framework
        assert "description" in framework


# -- Mood Journal Tests --------------------------------------------------------

class TestMoodJournal:
    """Test Mood Journal."""
    
    def test_singleton(self):
        from core.mood_journal import get_mood_journal
        m1 = get_mood_journal()
        m2 = get_mood_journal()
        assert m1 is m2
    
    def test_log_mood(self):
        from core.mood_journal import get_mood_journal
        mj = get_mood_journal()
        entry = mj.log_mood("happy", intensity=0.8, triggers=["sunshine", "walk"], context="home")
        assert entry is not None
        assert entry.mood == "happy"
    
    def test_get_mood_score(self):
        from core.mood_journal import get_mood_journal
        mj = get_mood_journal()
        score = mj.get_mood_score()
        assert 0 <= score <= 100
    
    def test_get_support_suggestion(self):
        from core.mood_journal import get_mood_journal
        mj = get_mood_journal()
        suggestion = mj.get_support_suggestion()
        assert "activity" in suggestion
        assert "urgency" in suggestion


# -- Values Alignment Checker Tests --------------------------------------------

class TestValuesAlignmentChecker:
    """Test Values Alignment Checker."""
    
    def test_singleton(self):
        from core.values_alignment_checker import get_values_alignment_checker
        v1 = get_values_alignment_checker()
        v2 = get_values_alignment_checker()
        assert v1 is v2
    
    def test_add_value(self):
        from core.values_alignment_checker import get_values_alignment_checker
        vac = get_values_alignment_checker()
        vac.add_value("health", priority=0.9, description="Physical and mental wellbeing")
        breakdown = vac.get_value_breakdown()
        assert len(breakdown) > 0
    
    def test_record_action(self):
        from core.values_alignment_checker import get_values_alignment_checker
        vac = get_values_alignment_checker()
        vac.add_value("health", priority=0.9)
        vac.record_action("Morning run", ["health"], energy_invested=0.8)
        assert vac._stats["actions_logged"] > 0
    
    def test_get_alignment_score(self):
        from core.values_alignment_checker import get_values_alignment_checker
        vac = get_values_alignment_checker()
        vac.add_value("health", priority=0.9)
        score = vac.get_alignment_score()
        assert 0 <= score <= 100
    
    def test_get_neglected_values(self):
        from core.values_alignment_checker import get_values_alignment_checker
        vac = get_values_alignment_checker()
        vac.add_value("health", priority=0.9)
        neglected = vac.get_neglected_values()
        assert isinstance(neglected, list)
    
    def test_get_alignment_suggestions(self):
        from core.values_alignment_checker import get_values_alignment_checker
        vac = get_values_alignment_checker()
        vac.add_value("health", priority=0.9)
        suggestions = vac.get_alignment_suggestions()
        assert isinstance(suggestions, list)



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



# -- Finance Pattern Detector Tests -------------------------------------------

class TestFinancePatternDetector:
    """Test Finance Pattern Detector."""
    
    def test_singleton(self):
        from core.finance_pattern_detector import get_finance_pattern_detector
        f1 = get_finance_pattern_detector()
        f2 = get_finance_pattern_detector()
        assert f1 is f2
    
    def test_record_transaction(self):
        from core.finance_pattern_detector import get_finance_pattern_detector
        fpd = get_finance_pattern_detector()
        txn = fpd.record_transaction(25.50, "Coffee Shop", "food", "expense", False)
        assert txn is not None
        assert txn.amount == 25.50
    
    def test_get_spending_insights(self):
        from core.finance_pattern_detector import get_finance_pattern_detector
        fpd = get_finance_pattern_detector()
        insights = fpd.get_spending_insights()
        assert isinstance(insights, dict)
    
    def test_detect_anomalies(self):
        from core.finance_pattern_detector import get_finance_pattern_detector
        fpd = get_finance_pattern_detector()
        fpd.record_transaction(5.0, "Coffee", "food")
        fpd.record_transaction(5.0, "Coffee", "food")
        fpd.record_transaction(500.0, "Electronics", "shopping")
        anomalies = fpd.detect_anomalies()
        assert isinstance(anomalies, list)
    
    def test_set_budget(self):
        from core.finance_pattern_detector import get_finance_pattern_detector
        fpd = get_finance_pattern_detector()
        fpd.set_budget("food", 500)
        budgets = fpd.get_budget_status()
        assert isinstance(budgets, list)


# -- Nutrition Analyzer Tests -------------------------------------------------

class TestNutritionAnalyzer:
    """Test Nutrition Analyzer."""
    
    def test_singleton(self):
        from core.nutrition_analyzer import get_nutrition_analyzer
        n1 = get_nutrition_analyzer()
        n2 = get_nutrition_analyzer()
        assert n1 is n2
    
    def test_record_meal(self):
        from core.nutrition_analyzer import get_nutrition_analyzer
        na = get_nutrition_analyzer()
        meal = na.record_meal(
            food_items=["Oatmeal", "Banana", "Almonds"],
            calories=350,
            protein_g=12,
            carbs_g=55,
            fat_g=8,
            fiber_g=6,
            meal_type="breakfast",
            processed_score=0.2,
        )
        assert meal is not None
        assert meal.calories == 350
    
    def test_get_diet_score(self):
        from core.nutrition_analyzer import get_nutrition_analyzer
        na = get_nutrition_analyzer()
        score = na.get_diet_score()
        assert 0 <= score <= 100
    
    def test_get_meal_suggestions(self):
        from core.nutrition_analyzer import get_nutrition_analyzer
        na = get_nutrition_analyzer()
        suggestions = na.get_meal_suggestions()
        assert isinstance(suggestions, list)


# -- Exercise Optimizer Tests -------------------------------------------------

class TestExerciseOptimizer:
    """Test Exercise Optimizer."""
    
    def test_singleton(self):
        from core.exercise_optimizer import get_exercise_optimizer
        e1 = get_exercise_optimizer()
        e2 = get_exercise_optimizer()
        assert e1 is e2
    
    def test_record_workout(self):
        from core.exercise_optimizer import get_exercise_optimizer
        eo = get_exercise_optimizer()
        workout = eo.record_workout(
            workout_type="strength",
            duration=45,
            intensity=0.7,
            perceived_exertion=7,
            muscle_groups=["chest", "triceps", "shoulders"],
            exercises=["Bench Press", "Dips", "Overhead Press"],
        )
        assert workout is not None
        assert workout.workout_type == "strength"
    
    def test_get_recovery_status(self):
        from core.exercise_optimizer import get_exercise_optimizer
        eo = get_exercise_optimizer()
        recovery = eo.get_recovery_status("chest")
        assert isinstance(recovery, dict)
    
    def test_get_workout_suggestion(self):
        from core.exercise_optimizer import get_exercise_optimizer
        eo = get_exercise_optimizer()
        suggestion = eo.get_workout_suggestion()
        assert "workout_type" in suggestion
        assert "reason" in suggestion
    
    def test_get_fitness_trends(self):
        from core.exercise_optimizer import get_exercise_optimizer
        eo = get_exercise_optimizer()
        trends = eo.get_fitness_trends()
        assert isinstance(trends, dict)


# -- Meditation Coach Tests ---------------------------------------------------

class TestMeditationCoach:
    """Test Meditation Coach."""
    
    def test_singleton(self):
        from core.meditation_coach import get_meditation_coach
        m1 = get_meditation_coach()
        m2 = get_meditation_coach()
        assert m1 is m2
    
    def test_record_session(self):
        from core.meditation_coach import get_meditation_coach
        mc = get_meditation_coach()
        session = mc.record_session(
            duration=10,
            meditation_type="breathing",
            quality=0.8,
            stress_before=0.7,
            stress_after=0.3,
            mood_before="anxious",
            mood_after="calm",
        )
        assert session is not None
        assert session.duration_minutes == 10
    
    def test_get_progress_stats(self):
        from core.meditation_coach import get_meditation_coach
        mc = get_meditation_coach()
        stats = mc.get_progress_stats()
        assert isinstance(stats, dict)
    
    def test_get_recommendation(self):
        from core.meditation_coach import get_meditation_coach
        mc = get_meditation_coach()
        rec = mc.get_recommendation("feeling stressed", current_stress=0.8)
        assert "meditation_type" in rec
        assert "duration_minutes" in rec
        assert "guidance" in rec
    
    def test_get_mindfulness_score(self):
        from core.meditation_coach import get_meditation_coach
        mc = get_meditation_coach()
        score = mc.get_mindfulness_score()
        assert 0 <= score <= 100



# -- Reading Tracker Tests -----------------------------------------------------

class TestReadingTracker:
    """Test Reading Tracker."""
    
    def test_singleton(self):
        from core.reading_tracker import get_reading_tracker
        r1 = get_reading_tracker()
        r2 = get_reading_tracker()
        assert r1 is r2
    
    def test_record_reading(self):
        from core.reading_tracker import get_reading_tracker
        rt = get_reading_tracker()
        session = rt.record_reading(
            title="Atomic Habits",
            content_type="book",
            pages=15,
            words=4500,
            duration=30,
            comprehension=0.8,
            engagement=0.9,
            topic_tags=["productivity", "psychology"],
        )
        assert session is not None
        assert session.title == "Atomic Habits"
        assert session.pages_read == 15
    
    def test_add_book(self):
        from core.reading_tracker import get_reading_tracker
        rt = get_reading_tracker()
        book = rt.add_book("Deep Work", "Cal Newport", 280, ["productivity", "focus"])
        assert book is not None
        assert book.title == "Deep Work"
    
    def test_get_reading_stats(self):
        from core.reading_tracker import get_reading_tracker
        rt = get_reading_tracker()
        stats = rt.get_reading_stats()
        assert isinstance(stats, dict)
    
    def test_get_recommendation(self):
        from core.reading_tracker import get_reading_tracker
        rt = get_reading_tracker()
        rec = rt.get_recommendation()
        assert "suggestions" in rec
        assert "reading_tip" in rec


# -- Writing Coach Tests ------------------------------------------------------

class TestWritingCoach:
    """Test Writing Coach."""
    
    def test_singleton(self):
        from core.writing_coach import get_writing_coach
        w1 = get_writing_coach()
        w2 = get_writing_coach()
        assert w1 is w2
    
    def test_record_session(self):
        from core.writing_coach import get_writing_coach
        wc = get_writing_coach()
        session = wc.record_session(
            project="Blog Post",
            session_type="drafting",
            word_count=500,
            duration=45,
            quality=0.7,
            flow=0.8,
            clarity=0.75,
            structure=0.8,
        )
        assert session is not None
        assert session.word_count == 500
    
    def test_add_project(self):
        from core.writing_coach import get_writing_coach
        wc = get_writing_coach()
        wc.add_project("Book Chapter 1", 3000, "book", "2026-06-15")
        stats = wc.get_writing_stats()
        assert isinstance(stats, dict)
    
    def test_get_suggestion(self):
        from core.writing_coach import get_writing_coach
        wc = get_writing_coach()
        suggestion = wc.get_suggestion()
        assert isinstance(suggestion, dict)
        assert "suggestions" in suggestion
    
    def test_get_flow_score(self):
        from core.writing_coach import get_writing_coach
        wc = get_writing_coach()
        score = wc.get_flow_score()
        assert 0 <= score <= 100


# -- Creativity Booster Tests -------------------------------------------------

class TestCreativityBooster:
    """Test Creativity Booster."""
    
    def test_singleton(self):
        from core.creativity_booster import get_creativity_booster
        c1 = get_creativity_booster()
        c2 = get_creativity_booster()
        assert c1 is c2
    
    def test_record_session(self):
        from core.creativity_booster import get_creativity_booster
        cb = get_creativity_booster()
        session = cb.record_session(
            session_type="brainstorming",
            duration=30,
            output_quality=0.8,
            flow=0.7,
            ideas_generated=12,
            ideas_executed=3,
            energy_before=0.5,
            energy_after=0.8,
        )
        assert session is not None
        assert session.ideas_generated == 12
    
    def test_get_creative_stats(self):
        from core.creativity_booster import get_creativity_booster
        cb = get_creativity_booster()
        stats = cb.get_creative_stats()
        assert isinstance(stats, dict)
    
    def test_get_block_breaker(self):
        from core.creativity_booster import get_creativity_booster
        cb = get_creativity_booster()
        breaker = cb.get_block_breaker("idea_drought")
        assert "suggested_technique" in breaker
        assert "description" in breaker
        assert "duration" in breaker
    
    def test_get_creative_energy_score(self):
        from core.creativity_booster import get_creativity_booster
        cb = get_creativity_booster()
        score = cb.get_creative_energy_score()
        assert 0 <= score <= 100


# -- Stress Response Coach Tests ----------------------------------------------

class TestStressResponseCoach:
    """Test Stress Response Coach."""
    
    def test_singleton(self):
        from core.stress_response_coach import get_stress_response_coach
        s1 = get_stress_response_coach()
        s2 = get_stress_response_coach()
        assert s1 is s2
    
    def test_record_stress_event(self):
        from core.stress_response_coach import get_stress_response_coach
        src = get_stress_response_coach()
        event = src.record_stress_event(
            trigger="Deadline pressure",
            intensity=0.7,
            physical_symptoms=["tension", "racing_heart"],
            emotional_state="overwhelmed",
            coping_strategy="box_breathing",
            strategy_effectiveness=0.8,
            recovery_minutes=10,
        )
        assert event is not None
        assert event.trigger == "Deadline pressure"
        assert event.resolved is True
    
    def test_get_stress_patterns(self):
        from core.stress_response_coach import get_stress_response_coach
        src = get_stress_response_coach()
        patterns = src.get_stress_patterns()
        assert isinstance(patterns, dict)
    
    def test_get_intervention(self):
        from core.stress_response_coach import get_stress_response_coach
        src = get_stress_response_coach()
        intervention = src.get_intervention(current_stress=0.6)
        assert "intervention" in intervention
        assert "description" in intervention
        assert "duration" in intervention
    
    def test_get_resilience_score(self):
        from core.stress_response_coach import get_stress_response_coach
        src = get_stress_response_coach()
        score = src.get_resilience_score()
        assert 0 <= score <= 100



# -- Communication Analyzer Tests --------------------------------------------

class TestCommunicationAnalyzer:
    """Test Communication Analyzer."""
    
    def test_singleton(self):
        from core.communication_analyzer import get_communication_analyzer
        c1 = get_communication_analyzer()
        c2 = get_communication_analyzer()
        assert c1 is c2
    
    def test_record_communication(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        comm = ca.record_communication(
            channel="email",
            recipient="team@example.com",
            purpose="request",
            duration=5,
            effectiveness=0.8,
            clarity=0.9,
            response_time=30,
        )
        assert comm is not None
        assert comm.channel == "email"
    
    def test_get_communication_stats(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        stats = ca.get_communication_stats()
        assert isinstance(stats, dict)
    
    def test_get_channel_recommendation(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        rec = ca.get_channel_recommendation("decision", "urgent")
        assert "recommended_channel" in rec
        assert "reason" in rec
    
    def test_get_communication_load_score(self):
        from core.communication_analyzer import get_communication_analyzer
        ca = get_communication_analyzer()
        score = ca.get_communication_load_score()
        assert 0 <= score <= 100


# -- Goal Progress Visualizer Tests -------------------------------------------

class TestGoalProgressVisualizer:
    """Test Goal Progress Visualizer."""
    
    def test_singleton(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        g1 = get_goal_progress_visualizer()
        g2 = get_goal_progress_visualizer()
        assert g1 is g2
    
    def test_add_goal(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        goal = gpv.add_goal("Write Book", "Complete first draft", 50000, "words", "2026-12-01", "high", "writing")
        assert goal is not None
        assert goal.title == "Write Book"
    
    def test_record_progress(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        goal = gpv.add_goal("Daily Steps", "Walk 10k steps", 10000, "steps")
        entry = gpv.record_progress(goal.goal_id, 5000, "Morning walk")
        assert entry is not None
        assert entry.amount == 5000
    
    def test_get_goal_status(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        status = gpv.get_goal_status()
        assert isinstance(status, list)
    
    def test_get_suggestions(self):
        from core.goal_progress_visualizer import get_goal_progress_visualizer
        gpv = get_goal_progress_visualizer()
        suggestions = gpv.get_suggestions()
        assert isinstance(suggestions, list)


# -- Life Balance Wheel Tests -------------------------------------------------

class TestLifeBalanceWheel:
    """Test Life Balance Wheel."""
    
    def test_singleton(self):
        from core.life_balance_wheel import get_life_balance_wheel
        l1 = get_life_balance_wheel()
        l2 = get_life_balance_wheel()
        assert l1 is l2
    
    def test_record_domain_rating(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        entry = lbw.record_domain_rating("work", 7.5, 45, 6.5, ["coding", "meetings"])
        assert entry is not None
        assert entry.domain == "work"
        assert entry.rating == 7.5
    
    def test_get_balance_score(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        score = lbw.get_balance_score()
        assert 0 <= score <= 100
    
    def test_get_domain_insights(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        insights = lbw.get_domain_insights()
        assert isinstance(insights, dict)
    
    def test_get_rebalancing_suggestions(self):
        from core.life_balance_wheel import get_life_balance_wheel
        lbw = get_life_balance_wheel()
        suggestions = lbw.get_rebalancing_suggestions()
        assert isinstance(suggestions, list)


# -- Productivity Gamifier Tests ----------------------------------------------

class TestProductivityGamifier:
    """Test Productivity Gamifier."""
    
    def test_singleton(self):
        from core.productivity_gamifier import get_productivity_gamifier
        p1 = get_productivity_gamifier()
        p2 = get_productivity_gamifier()
        assert p1 is p2
    
    def test_record_activity(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        activity = pg.record_activity("Deep Work", "work", 120, 0.9)
        assert activity is not None
        assert activity.activity == "Deep Work"
        assert activity.xp_earned > 0
    
    def test_get_level(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        level_info = pg.get_level()
        assert "level" in level_info
        assert "title" in level_info
        assert "total_xp" in level_info
    
    def test_get_achievements(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        achievements = pg.get_achievements()
        assert isinstance(achievements, dict)
        assert "total" in achievements
        assert "unlocked" in achievements
    
    def test_get_daily_challenge(self):
        from core.productivity_gamifier import get_productivity_gamifier
        pg = get_productivity_gamifier()
        challenge = pg.get_daily_challenge()
        assert "daily_challenges" in challenge
        assert isinstance(challenge["daily_challenges"], list)



# -- Environment Optimizer Tests ----------------------------------------------

class TestEnvironmentOptimizer:
    """Test Environment Optimizer."""
    
    def test_singleton(self):
        from core.environment_optimizer import get_environment_optimizer
        e1 = get_environment_optimizer()
        e2 = get_environment_optimizer()
        assert e1 is e2
    
    def test_record_conditions(self):
        from core.environment_optimizer import get_environment_optimizer
        eo = get_environment_optimizer()
        state = eo.record_conditions(
            location="desk",
            lighting=8,
            noise_level=3,
            temperature=22,
            clutter=2,
            air_quality=7,
            natural_light=True,
            focus_score=0.85,
            energy_score=0.8,
        )
        assert state is not None
        assert state.location == "desk"
        assert state.focus_score == 0.85
    
    def test_get_environment_insights(self):
        from core.environment_optimizer import get_environment_optimizer
        eo = get_environment_optimizer()
        insights = eo.get_environment_insights()
        assert isinstance(insights, dict)
    
    def test_get_optimization_suggestions(self):
        from core.environment_optimizer import get_environment_optimizer
        eo = get_environment_optimizer()
        suggestions = eo.get_optimization_suggestions()
        assert isinstance(suggestions, list)
    
    def test_get_environment_score(self):
        from core.environment_optimizer import get_environment_optimizer
        eo = get_environment_optimizer()
        score = eo.get_environment_score()
        assert 0 <= score <= 100


# -- Weather Suggester Tests --------------------------------------------------

class TestWeatherSuggester:
    """Test Weather Suggester."""
    
    def test_singleton(self):
        from core.weather_suggester import get_weather_suggester
        w1 = get_weather_suggester()
        w2 = get_weather_suggester()
        assert w1 is w2
    
    def test_record_weather(self):
        from core.weather_suggester import get_weather_suggester
        ws = get_weather_suggester()
        entry = ws.record_weather(
            temperature=22,
            condition="sunny",
            humidity=45,
            mood_before=6,
            mood_after=8,
            energy_level=7,
            productivity=7,
            outdoor_activity=True,
        )
        assert entry is not None
        assert entry.condition == "sunny"
        assert entry.mood_after == 8
    
    def test_get_weather_insights(self):
        from core.weather_suggester import get_weather_suggester
        ws = get_weather_suggester()
        insights = ws.get_weather_insights()
        assert isinstance(insights, dict)
    
    def test_get_activity_suggestion(self):
        from core.weather_suggester import get_weather_suggester
        ws = get_weather_suggester()
        suggestion = ws.get_activity_suggestion("rainy", 15)
        assert "condition" in suggestion
        assert "outdoor_activities" in suggestion
        assert "indoor_adjustments" in suggestion
    
    def test_get_weather_mood_score(self):
        from core.weather_suggester import get_weather_suggester
        ws = get_weather_suggester()
        score = ws.get_weather_mood_score()
        assert 0 <= score <= 100


# -- Travel Planner Tests -----------------------------------------------------

class TestTravelPlanner:
    """Test Travel Planner."""
    
    def test_singleton(self):
        from core.travel_planner import get_travel_planner
        t1 = get_travel_planner()
        t2 = get_travel_planner()
        assert t1 is t2
    
    def test_record_trip(self):
        from core.travel_planner import get_travel_planner
        tp = get_travel_planner()
        trip = tp.record_trip(
            destination="Tokyo",
            purpose="leisure",
            duration=7,
            satisfaction=0.9,
            stress_level=0.2,
            highlights=["Tsukiji Market", "TeamLab Borderless"],
            packing_score=0.8,
        )
        assert trip is not None
        assert trip.destination == "Tokyo"
        assert trip.satisfaction == 0.9
    
    def test_get_travel_stats(self):
        from core.travel_planner import get_travel_planner
        tp = get_travel_planner()
        stats = tp.get_travel_stats()
        assert isinstance(stats, dict)
    
    def test_get_packing_list(self):
        from core.travel_planner import get_travel_planner
        tp = get_travel_planner()
        packing = tp.get_packing_list("Paris", "spring", 5, ["city", "business"])
        assert "packing_list" in packing
        assert "essential" in packing["packing_list"]
    
    def test_get_trip_suggestion(self):
        from core.travel_planner import get_travel_planner
        tp = get_travel_planner()
        suggestion = tp.get_trip_suggestion()
        assert isinstance(suggestion, dict)


# -- Gift Idea Generator Tests ------------------------------------------------

class TestGiftIdeaGenerator:
    """Test Gift Idea Generator."""
    
    def test_singleton(self):
        from core.gift_idea_generator import get_gift_idea_generator
        g1 = get_gift_idea_generator()
        g2 = get_gift_idea_generator()
        assert g1 is g2
    
    def test_record_gift(self):
        from core.gift_idea_generator import get_gift_idea_generator
        gig = get_gift_idea_generator()
        gift = gig.record_gift(
            recipient="Mom",
            gift_description="Handmade photo album",
            category="handmade",
            price=30,
            reaction=0.95,
            occasion="birthday",
        )
        assert gift is not None
        assert gift.recipient == "Mom"
        assert gift.reaction == 0.95
    
    def test_add_recipient(self):
        from core.gift_idea_generator import get_gift_idea_generator
        gig = get_gift_idea_generator()
        gig.add_recipient(
            name="Dad",
            interests=["golf", "cooking", "reading"],
            preferred_categories=["experience", "food"],
            typical_budget=75,
            occasions={"birthday": "06-15", "fathers_day": "06-15"},
        )
        recipients = gig.get_occasion_reminders()
        assert isinstance(recipients, list)
    
    def test_get_gift_suggestions(self):
        from core.gift_idea_generator import get_gift_idea_generator
        gig = get_gift_idea_generator()
        gig.add_recipient("TestFriend", ["tech", "gaming"], ["gadget"], typical_budget=100)
        suggestions = gig.get_gift_suggestions("TestFriend", "birthday")
        assert isinstance(suggestions, list)
    
    def test_get_occasion_reminders(self):
        from core.gift_idea_generator import get_gift_idea_generator
        gig = get_gift_idea_generator()
        reminders = gig.get_occasion_reminders()
        assert isinstance(reminders, list)



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



# -- Document Organizer Tests -----------------------------------------------

class TestDocumentOrganizer:
    """Test Document Organizer."""
    
    def test_singleton(self):
        from core.document_organizer import get_document_organizer
        d1 = get_document_organizer()
        d2 = get_document_organizer()
        assert d1 is d2
    
    def test_record_document(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        doc = do.record_document(
            "Contract 2024",
            "contract",
            ["legal", "2024"],
            "high",
            "/docs/contracts/2024.pdf",
            1024,
            "2025-12-31",
        )
        assert doc is not None
        assert doc.name == "Contract 2024"
        assert doc.importance == "high"
        assert "legal" in doc.tags
    
    def test_access_document(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        doc = do.record_document("Test Doc", "note")
        accessed = do.access_document(doc.doc_id)
        assert accessed is not None
        assert accessed.access_count >= 1
    
    def test_get_document_stats(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        stats = do.get_document_stats()
        assert isinstance(stats, dict)
    
    def test_get_retrieval_suggestions(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        do.record_document("Tax Return 2024", "report", ["finance", "tax"], "high")
        suggestions = do.get_retrieval_suggestions("tax finance")
        assert isinstance(suggestions, list)
    
    def test_get_organization_score(self):
        from core.document_organizer import get_document_organizer
        do = get_document_organizer()
        score = do.get_organization_score()
        assert 0 <= score <= 100


# -- Password Health Checker Tests ------------------------------------------

class TestPasswordHealthChecker:
    """Test Password Health Checker."""
    
    def test_singleton(self):
        from core.password_health_checker import get_password_health_checker
        p1 = get_password_health_checker()
        p2 = get_password_health_checker()
        assert p1 is p2
    
    def test_record_account(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        account = phc.record_account(
            "Bank", "user123", 30, 0.9, True, "critical", "financial"
        )
        assert account is not None
        assert account.service == "Bank"
        assert account.has_2fa is True
    
    def test_get_password_health(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        health = phc.get_password_health()
        assert isinstance(health, dict)
        assert "overall_score" in health
    
    def test_get_risk_assessment(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        phc.record_account("OldSite", "user", 200, 0.2, False, "high", "social")
        risks = phc.get_risk_assessment()
        assert isinstance(risks, list)
        if risks:
            assert "risk_score" in risks[0]
    
    def test_get_security_recommendations(self):
        from core.password_health_checker import get_password_health_checker
        phc = get_password_health_checker()
        recs = phc.get_security_recommendations()
        assert isinstance(recs, list)


# -- Subscription Manager Tests ---------------------------------------------

class TestSubscriptionManager:
    """Test Subscription Manager."""
    
    def test_singleton(self):
        from core.subscription_manager import get_subscription_manager
        s1 = get_subscription_manager()
        s2 = get_subscription_manager()
        assert s1 is s2
    
    def test_record_subscription(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("Netflix", 15.99, "monthly", "streaming", "Netflix Inc", "2025-06-15")
        assert sub is not None
        assert sub.name == "Netflix"
        assert sub.cost == 15.99
    
    def test_record_usage(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("Spotify", 9.99, "monthly", "music")
        usage = sm.record_usage(sub.sub_id, 120, "playlist")
        assert usage is not None
        assert usage.sub_id == sub.sub_id
    
    def test_get_subscription_stats(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        stats = sm.get_subscription_stats()
        assert isinstance(stats, dict)
    
    def test_get_optimization_suggestions(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        suggestions = sm.get_optimization_suggestions()
        assert isinstance(suggestions, list)
    
    def test_cancel_subscription(self):
        from core.subscription_manager import get_subscription_manager
        sm = get_subscription_manager()
        sub = sm.record_subscription("TempSub", 5.0, "monthly", "test")
        sm.cancel_subscription(sub.sub_id)
        assert not sm._subscriptions[sub.sub_id].is_active


# -- Digital Declutterer Tests ----------------------------------------------

class TestDigitalDeclutterer:
    """Test Digital Declutterer."""
    
    def test_singleton(self):
        from core.digital_declutterer import get_digital_declutterer
        d1 = get_digital_declutterer()
        d2 = get_digital_declutterer()
        assert d1 is d2
    
    def test_record_storage_scan(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        record = dd.record_storage_scan("downloads", 25.5, 150, [], [])
        assert record is not None
        assert record.category == "downloads"
        assert record.size_gb == 25.5
    
    def test_record_app_usage(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        usage = dd.record_app_usage("VS Code", 240, "work", True)
        assert usage is not None
        assert usage.app_name == "VS Code"
        assert usage.was_productive is True
    
    def test_get_clutter_score(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        score = dd.get_clutter_score()
        assert 0 <= score <= 100
    
    def test_get_declutter_plan(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        plan = dd.get_declutter_plan()
        assert isinstance(plan, list)
    
    def test_get_digital_wellness_score(self):
        from core.digital_declutterer import get_digital_declutterer
        dd = get_digital_declutterer()
        score = dd.get_digital_wellness_score()
        assert 0 <= score <= 100



# -- Event Planner Tests ----------------------------------------------------

class TestEventPlanner:
    """Test Event Planner."""
    
    def test_singleton(self):
        from core.event_planner import get_event_planner
        e1 = get_event_planner()
        e2 = get_event_planner()
        assert e1 is e2
    
    def test_record_event(self):
        from core.event_planner import get_event_planner
        ep = get_event_planner()
        event = ep.record_event(
            "Team Dinner",
            "social",
            "2025-06-15T18:00:00",
            3,
            8,
            0.5,
            6,
            5,
            0.7,
            0.3,
            "Restaurant",
            "Good networking",
            ["Bring business cards"],
        )
        assert event is not None
        assert event.title == "Team Dinner"
        assert event.event_type == "social"
    
    def test_get_event_insights(self):
        from core.event_planner import get_event_planner
        ep = get_event_planner()
        insights = ep.get_event_insights()
        assert isinstance(insights, dict)
    
    def test_get_preparation_checklist(self):
        from core.event_planner import get_event_planner
        ep = get_event_planner()
        checklist = ep.get_preparation_checklist("networking", 20, 4)
        assert isinstance(checklist, list)
        assert len(checklist) > 0
    
    def test_get_social_energy_score(self):
        from core.event_planner import get_event_planner
        ep = get_event_planner()
        score = ep.get_social_energy_score()
        assert 0 <= score <= 100


# -- Habit Builder Tests ----------------------------------------------------

class TestHabitBuilder:
    """Test Habit Builder."""
    
    def test_singleton(self):
        from core.habit_builder import get_habit_builder
        h1 = get_habit_builder()
        h2 = get_habit_builder()
        assert h1 is h2
    
    def test_add_habit(self):
        from core.habit_builder import get_habit_builder
        hb = get_habit_builder()
        habit = hb.add_habit(
            "Morning Pushups",
            "Wake up",
            "20 pushups",
            "Feeling strong",
            "easy",
            "daily",
            "morning",
            "bedroom",
        )
        assert habit is not None
        assert habit.name == "Morning Pushups"
        assert habit.cue == "Wake up"
    
    def test_record_habit(self):
        from core.habit_builder import get_habit_builder
        hb = get_habit_builder()
        habit = hb.add_habit("Read 10 Pages", "After lunch", "Read book", "Knowledge", "medium")
        attempt = hb.record_habit(habit.habit_id, True, "", "Done!", 15)
        assert attempt is not None
        assert attempt.completed is True
    
    def test_get_habit_stats(self):
        from core.habit_builder import get_habit_builder
        hb = get_habit_builder()
        stats = hb.get_habit_stats()
        assert isinstance(stats, list)
    
    def test_get_habit_recommendations(self):
        from core.habit_builder import get_habit_builder
        hb = get_habit_builder()
        recs = hb.get_habit_recommendations()
        assert isinstance(recs, list)


# -- Morning Routine Designer Tests -----------------------------------------

class TestMorningRoutineDesigner:
    """Test Morning Routine Designer."""
    
    def test_singleton(self):
        from core.morning_routine_designer import get_morning_routine_designer
        m1 = get_morning_routine_designer()
        m2 = get_morning_routine_designer()
        assert m1 is m2
    
    def test_record_routine_element(self):
        from core.morning_routine_designer import get_morning_routine_designer
        mrd = get_morning_routine_designer()
        elem = mrd.record_routine_element("Stretch", "movement", 5, 2, 1, 0)
        assert elem is not None
        assert elem.name == "Stretch"
        assert elem.energy_impact == 2
    
    def test_record_morning(self):
        from core.morning_routine_designer import get_morning_routine_designer
        mrd = get_morning_routine_designer()
        morning = mrd.record_morning("06:30", ["Stretch", "Meditate"], 3, 7, 8, 8, 0.9)
        assert morning is not None
        assert morning.wake_up_time == "06:30"
        assert morning.day_rating == 0.9
    
    def test_get_morning_stats(self):
        from core.morning_routine_designer import get_morning_routine_designer
        mrd = get_morning_routine_designer()
        stats = mrd.get_morning_stats()
        assert isinstance(stats, dict)
    
    def test_get_routine_suggestion(self):
        from core.morning_routine_designer import get_morning_routine_designer
        mrd = get_morning_routine_designer()
        routine = mrd.get_routine_suggestion(["energy", "focus"], 30, "medium")
        assert isinstance(routine, list)
        assert len(routine) > 0
    
    def test_get_wake_up_optimization(self):
        from core.morning_routine_designer import get_morning_routine_designer
        mrd = get_morning_routine_designer()
        opt = mrd.get_wake_up_optimization()
        assert isinstance(opt, dict)


# -- Evening Wind-Down Coach Tests ------------------------------------------

class TestEveningWindDownCoach:
    """Test Evening Wind-Down Coach."""
    
    def test_singleton(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        e1 = get_evening_wind_down_coach()
        e2 = get_evening_wind_down_coach()
        assert e1 is e2
    
    def test_record_evening_activity(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        ewdc = get_evening_wind_down_coach()
        act = ewdc.record_evening_activity("Reading", "mindfulness", 30, 2, 3)
        assert act is not None
        assert act.activity == "Reading"
        assert act.stimulation_level == 2
    
    def test_record_evening(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        ewdc = get_evening_wind_down_coach()
        evening = ewdc.record_evening(
            ["Reading", "Stretching"],
            45,
            False,
            False,
            False,
            "21:00",
            "22:30",
            0.85,
            10,
        )
        assert evening is not None
        assert evening.sleep_quality == 0.85
        assert evening.time_to_fall_asleep == 10
    
    def test_get_sleep_prediction(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        ewdc = get_evening_wind_down_coach()
        pred = ewdc.get_sleep_prediction()
        assert isinstance(pred, dict)
        assert "prediction" in pred
    
    def test_get_wind_down_routine(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        ewdc = get_evening_wind_down_coach()
        routine = ewdc.get_wind_down_routine("high", 30)
        assert isinstance(routine, list)
        assert len(routine) > 0
    
    def test_get_optimal_bedtime(self):
        from core.evening_wind_down_coach import get_evening_wind_down_coach
        ewdc = get_evening_wind_down_coach()
        bedtime = ewdc.get_optimal_bedtime("06:30", 8)
        assert isinstance(bedtime, dict)
        assert "recommendation" in bedtime



# -- Conflict Resolution Coach Tests ---------------------------------------

class TestConflictResolutionCoach:
    """Test Conflict Resolution Coach."""
    
    def test_singleton(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        c1 = get_conflict_resolution_coach()
        c2 = get_conflict_resolution_coach()
        assert c1 is c2
    
    def test_record_conflict(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        conflict = crc.record_conflict(
            "Missed deadline",
            ["boss", "user"],
            "needs",
            6,
            30,
            "accommodating",
            "resolved",
            ["active_listening"],
            0.7,
            0.4,
            ["Set earlier deadlines"],
        )
        assert conflict is not None
        assert conflict.trigger == "Missed deadline"
        assert conflict.resolution == "resolved"
    
    def test_get_conflict_patterns(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        patterns = crc.get_conflict_patterns()
        assert isinstance(patterns, dict)
    
    def test_get_resolution_strategy(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        strategy = crc.get_resolution_strategy("needs", 8, ["partner"])
        assert isinstance(strategy, dict)
        assert "approach" in strategy
    
    def test_get_relationship_health(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        health = crc.get_relationship_health("boss")
        assert 0 <= health <= 100


# -- Boundaries Coach Tests -------------------------------------------------

class TestBoundariesCoach:
    """Test Boundaries Coach."""
    
    def test_singleton(self):
        from core.boundaries_coach import get_boundaries_coach
        b1 = get_boundaries_coach()
        b2 = get_boundaries_coach()
        assert b1 is b2
    
    def test_record_boundary(self):
        from core.boundaries_coach import get_boundaries_coach
        bc = get_boundaries_coach()
        boundary = bc.record_boundary(
            "work",
            "No meetings after 5 PM",
            "Weekdays",
            "firm",
            "respected",
            0.2,
            0.8,
            True,
            "Manager understood",
        )
        assert boundary is not None
        assert boundary.area == "work"
        assert boundary.outcome == "respected"
    
    def test_get_boundary_stats(self):
        from core.boundaries_coach import get_boundaries_coach
        bc = get_boundaries_coach()
        stats = bc.get_boundary_stats()
        assert isinstance(stats, dict)
    
    def test_get_boundary_script(self):
        from core.boundaries_coach import get_boundaries_coach
        bc = get_boundaries_coach()
        script = bc.get_boundary_script("Overworking", "work", "firm")
        assert isinstance(script, dict)
        assert "script" in script
    
    def test_get_boundary_strength_score(self):
        from core.boundaries_coach import get_boundaries_coach
        bc = get_boundaries_coach()
        score = bc.get_boundary_strength_score()
        assert 0 <= score <= 100


# -- Assertiveness Trainer Tests --------------------------------------------

class TestAssertivenessTrainer:
    """Test Assertiveness Trainer."""
    
    def test_singleton(self):
        from core.assertiveness_trainer import get_assertiveness_trainer
        a1 = get_assertiveness_trainer()
        a2 = get_assertiveness_trainer()
        assert a1 is a2
    
    def test_record_attempt(self):
        from core.assertiveness_trainer import get_assertiveness_trainer
        at = get_assertiveness_trainer()
        attempt = at.record_attempt(
            "Team meeting",
            "Push back on deadline",
            "assertive",
            "assertive",
            "achieved",
            0.3,
            "open",
            "calm",
            ["I need", "realistic timeline"],
            ["Clear request", "No apology"],
            [],
        )
        assert attempt is not None
        assert attempt.situation == "Team meeting"
        assert attempt.outcome == "achieved"
    
    def test_get_assertiveness_stats(self):
        from core.assertiveness_trainer import get_assertiveness_trainer
        at = get_assertiveness_trainer()
        stats = at.get_assertiveness_stats()
        assert isinstance(stats, dict)
    
    def test_get_script(self):
        from core.assertiveness_trainer import get_assertiveness_trainer
        at = get_assertiveness_trainer()
        script = at.get_script("saying_no", "Decline extra work", "medium")
        assert isinstance(script, dict)
        assert "script" in script
    
    def test_get_assertiveness_score(self):
        from core.assertiveness_trainer import get_assertiveness_trainer
        at = get_assertiveness_trainer()
        score = at.get_assertiveness_score()
        assert 0 <= score <= 100


# -- Active Listening Coach Tests -------------------------------------------

class TestActiveListeningCoach:
    """Test Active Listening Coach."""
    
    def test_singleton(self):
        from core.active_listening_coach import get_active_listening_coach
        a1 = get_active_listening_coach()
        a2 = get_active_listening_coach()
        assert a1 is a2
    
    def test_record_session(self):
        from core.active_listening_coach import get_active_listening_coach
        alc = get_active_listening_coach()
        session = alc.record_session(
            "Partner",
            "romantic",
            45,
            0.9,
            0,
            0,
            5,
            3,
            0.85,
            False,
            0.2,
            "Deep conversation about career",
        )
        assert session is not None
        assert session.person == "Partner"
        assert session.attention_score == 0.9
    
    def test_get_listening_stats(self):
        from core.active_listening_coach import get_active_listening_coach
        alc = get_active_listening_coach()
        stats = alc.get_listening_stats()
        assert isinstance(stats, dict)
    
    def test_get_reflection_script(self):
        from core.active_listening_coach import get_active_listening_coach
        alc = get_active_listening_coach()
        script = alc.get_reflection_script("sad", "Friend lost job")
        assert isinstance(script, dict)
        assert "validation" in script
    
    def test_get_listening_score(self):
        from core.active_listening_coach import get_active_listening_coach
        alc = get_active_listening_coach()
        score = alc.get_listening_score()
        assert 0 <= score <= 100



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



# -- Curiosity Spark Tests --------------------------------------------------

class TestCuriositySpark:
    """Test Curiosity Spark."""
    
    def test_singleton(self):
        from core.curiosity_spark import get_curiosity_spark
        c1 = get_curiosity_spark()
        c2 = get_curiosity_spark()
        assert c1 is c2
    
    def test_record_exploration(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        exp = cs.record_exploration(
            "Quantum entanglement",
            "science",
            "deep",
            "book",
            120,
            0.9,
            5,
            ["Partner"],
        )
        assert exp is not None
        assert exp.topic == "Quantum entanglement"
        assert exp.questions_generated == 5
    
    def test_get_curiosity_stats(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        stats = cs.get_curiosity_stats()
        assert isinstance(stats, dict)
    
    def test_get_spark(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        spark = cs.get_spark(["science"], 10, "science")
        assert isinstance(spark, dict)
        assert "spark" in spark
    
    def test_get_curiosity_score(self):
        from core.curiosity_spark import get_curiosity_spark
        cs = get_curiosity_spark()
        score = cs.get_curiosity_score()
        assert 0 <= score <= 100


# -- Play Coach Tests -------------------------------------------------------

class TestPlayCoach:
    """Test Play Coach."""
    
    def test_singleton(self):
        from core.play_coach import get_play_coach
        p1 = get_play_coach()
        p2 = get_play_coach()
        assert p1 is p2
    
    def test_record_play(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        session = pc.record_play(
            "Frisbee in park",
            "physical",
            60,
            0.9,
            "medium",
            False,
            False,
            "outdoors",
            ["Alex", "Sam"],
        )
        assert session is not None
        assert session.activity == "Frisbee in park"
        assert session.solo is False
    
    def test_get_play_stats(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        stats = pc.get_play_stats()
        assert isinstance(stats, dict)
    
    def test_get_play_suggestion(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        suggestion = pc.get_play_suggestion("medium", 30, "happy", True)
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_playfulness_score(self):
        from core.play_coach import get_play_coach
        pc = get_play_coach()
        score = pc.get_playfulness_score()
        assert 0 <= score <= 100


# -- Adventure Planner Tests ------------------------------------------------

class TestAdventurePlanner:
    """Test Adventure Planner."""
    
    def test_singleton(self):
        from core.adventure_planner import get_adventure_planner
        a1 = get_adventure_planner()
        a2 = get_adventure_planner()
        assert a1 is a2
    
    def test_record_adventure(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        adv = ap.record_adventure(
            "Solo camping trip",
            "nature",
            48,
            0.7,
            0.9,
            0.8,
            True,
            True,
            [],
            150,
            "Yosemite",
            "Incredible stars",
        )
        assert adv is not None
        assert adv.activity == "Solo camping trip"
        assert adv.location == "Yosemite"
    
    def test_get_adventure_stats(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        stats = ap.get_adventure_stats()
        assert isinstance(stats, dict)
    
    def test_get_adventure_suggestion(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        suggestion = ap.get_adventure_suggestion("low", "micro", "medium", True)
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_adventure_score(self):
        from core.adventure_planner import get_adventure_planner
        ap = get_adventure_planner()
        score = ap.get_adventure_score()
        assert 0 <= score <= 100


# -- Wonder Tracker Tests ---------------------------------------------------

class TestWonderTracker:
    """Test Wonder Tracker."""
    
    def test_singleton(self):
        from core.wonder_tracker import get_wonder_tracker
        w1 = get_wonder_tracker()
        w2 = get_wonder_tracker()
        assert w1 is w2
    
    def test_record_wonder(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        wonder = wt.record_wonder(
            "Milky Way visible",
            "vastness",
            0.9,
            20,
            "humbled",
            0.6,
            0.9,
            "Desert campsite",
            "22:00",
            "First time seeing it so clearly",
        )
        assert wonder is not None
        assert wonder.trigger == "Milky Way visible"
        assert wonder.intensity == 0.9
    
    def test_get_wonder_stats(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        stats = wt.get_wonder_stats()
        assert isinstance(stats, dict)
    
    def test_get_wonder_suggestion(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        suggestion = wt.get_wonder_suggestion("nature", 5, "outdoors")
        assert isinstance(suggestion, dict)
        assert "prompt" in suggestion
    
    def test_get_wonder_score(self):
        from core.wonder_tracker import get_wonder_tracker
        wt = get_wonder_tracker()
        score = wt.get_wonder_score()
        assert 0 <= score <= 100



# -- Meaning Mapper Tests ---------------------------------------------------

class TestMeaningMapper:
    """Test Meaning Mapper."""
    
    def test_singleton(self):
        from core.meaning_mapper import get_meaning_mapper
        m1 = get_meaning_mapper()
        m2 = get_meaning_mapper()
        assert m1 is m2
    
    def test_record_moment(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        moment = mm.record_moment(
            "Deep conversation with mentor",
            "connection",
            0.9,
            90,
            "cafe",
            ["Mentor"],
            "Felt truly seen",
        )
        assert moment is not None
        assert moment.description == "Deep conversation with mentor"
        assert moment.source == "connection"
    
    def test_get_meaning_stats(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        stats = mm.get_meaning_stats()
        assert isinstance(stats, dict)
    
    def test_get_meaning_suggestion(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        suggestion = mm.get_meaning_suggestion(30, "medium", "connection")
        assert isinstance(suggestion, dict)
        assert "activity" in suggestion
    
    def test_get_meaning_score(self):
        from core.meaning_mapper import get_meaning_mapper
        mm = get_meaning_mapper()
        score = mm.get_meaning_score()
        assert 0 <= score <= 100


# -- Purpose Navigator Tests ------------------------------------------------

class TestPurposeNavigator:
    """Test Purpose Navigator."""
    
    def test_singleton(self):
        from core.purpose_navigator import get_purpose_navigator
        p1 = get_purpose_navigator()
        p2 = get_purpose_navigator()
        assert p1 is p2
    
    def test_record_alignment(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        alignment = pn.record_alignment(
            "Volunteering at shelter",
            True,
            "service",
            0.9,
            "community",
            4,
        )
        assert alignment is not None
        assert alignment.activity == "Volunteering at shelter"
        assert alignment.aligned is True
    
    def test_get_purpose_stats(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        stats = pn.get_purpose_stats()
        assert isinstance(stats, dict)
    
    def test_get_navigation_suggestion(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        suggestion = pn.get_navigation_suggestion(0.2, "creation", 30)
        assert isinstance(suggestion, dict)
        assert "action" in suggestion
    
    def test_get_purpose_score(self):
        from core.purpose_navigator import get_purpose_navigator
        pn = get_purpose_navigator()
        score = pn.get_purpose_score()
        assert 0 <= score <= 100


# -- Legacy Builder Tests ---------------------------------------------------

class TestLegacyBuilder:
    """Test Legacy Builder."""
    
    def test_singleton(self):
        from core.legacy_builder import get_legacy_builder
        l1 = get_legacy_builder()
        l2 = get_legacy_builder()
        assert l1 is l2
    
    def test_record_legacy_action(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        action = lb.record_legacy_action(
            "Mentored junior developer",
            "mentorship",
            "community",
            "lasting",
            1,
            "Shared career advice",
        )
        assert action is not None
        assert action.action == "Mentored junior developer"
        assert action.theme == "mentorship"
    
    def test_get_legacy_stats(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        stats = lb.get_legacy_stats()
        assert isinstance(stats, dict)
    
    def test_get_legacy_suggestion(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        suggestion = lb.get_legacy_suggestion(30, "creation", "normal")
        assert isinstance(suggestion, dict)
        assert "action" in suggestion
    
    def test_get_legacy_score(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        score = lb.get_legacy_score()
        assert 0 <= score <= 100


# -- Death Awareness Coach Tests --------------------------------------------

class TestDeathAwarenessCoach:
    """Test Death Awareness Coach."""
    
    def test_singleton(self):
        from core.death_awareness_coach import get_death_awareness_coach
        d1 = get_death_awareness_coach()
        d2 = get_death_awareness_coach()
        assert d1 is d2
    
    def test_record_memento(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        memento = dac.record_memento(
            "Visit to old family home",
            "grateful",
            "Time with parents is finite",
            "Call parents weekly",
            "precious",
            "experience",
        )
        assert memento is not None
        assert memento.trigger == "Visit to old family home"
        assert memento.emotional_response == "grateful"
    
    def test_get_death_awareness_stats(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        stats = dac.get_death_awareness_stats()
        assert isinstance(stats, dict)
    
    def test_get_memento_suggestion(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        suggestion = dac.get_memento_suggestion("gentle", 5)
        assert isinstance(suggestion, dict)
        assert "practice" in suggestion
    
    def test_get_death_awareness_score(self):
        from core.death_awareness_coach import get_death_awareness_coach
        dac = get_death_awareness_coach()
        score = dac.get_death_awareness_score()
        assert 0 <= score <= 100



# -- Flow State Coach Tests -------------------------------------------------

class TestFlowStateCoach:
    """Test Flow State Coach."""
    
    def test_singleton(self):
        from core.flow_state_coach import get_flow_state_coach
        f1 = get_flow_state_coach()
        f2 = get_flow_state_coach()
        assert f1 is f2
    
    def test_record_flow_session(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        session = fsc.record_flow_session(
            "Coding feature",
            0.8,
            0.7,
            0.9,
            0.8,
            0.9,
            0.8,
            0,
            120,
            "Coffee + music",
        )
        assert session is not None
        assert session.activity == "Coding feature"
        assert session.immersion == 0.9
    
    def test_get_flow_stats(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        stats = fsc.get_flow_stats()
        assert isinstance(stats, dict)
    
    def test_get_flow_suggestion(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        suggestion = fsc.get_flow_suggestion("Writing report", 0.6, 90)
        assert isinstance(suggestion, dict)
        assert "challenge_adjustment" in suggestion
    
    def test_get_flow_score(self):
        from core.flow_state_coach import get_flow_state_coach
        fsc = get_flow_state_coach()
        score = fsc.get_flow_score()
        assert 0 <= score <= 100


# -- Savoring Trainer Tests -------------------------------------------------

class TestSavoringTrainer:
    """Test Savoring Trainer."""
    
    def test_singleton(self):
        from core.savoring_trainer import get_savoring_trainer
        s1 = get_savoring_trainer()
        s2 = get_savoring_trainer()
        assert s1 is s2
    
    def test_record_savoring(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        savoring = st.record_savoring(
            "First coffee of the day",
            "present",
            "basking",
            60,
            0.8,
            0.6,
            0.9,
            ["hurry"],
        )
        assert savoring is not None
        assert savoring.experience == "First coffee of the day"
        assert savoring.intensity_after == 0.9
    
    def test_get_savoring_stats(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        stats = st.get_savoring_stats()
        assert isinstance(stats, dict)
    
    def test_get_savoring_suggestion(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        suggestion = st.get_savoring_suggestion("Sunset", "happy", "present")
        assert isinstance(suggestion, dict)
        assert "technique" in suggestion
    
    def test_get_savoring_score(self):
        from core.savoring_trainer import get_savoring_trainer
        st = get_savoring_trainer()
        score = st.get_savoring_score()
        assert 0 <= score <= 100


# -- Presence Detector Tests ------------------------------------------------

class TestPresenceDetector:
    """Test Presence Detector."""
    
    def test_singleton(self):
        from core.presence_detector import get_presence_detector
        p1 = get_presence_detector()
        p2 = get_presence_detector()
        assert p1 is p2
    
    def test_record_presence(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        moment = pd.record_presence(
            "full",
            "Meditation bell",
            "sensory",
            20,
            0.9,
            "breath focus",
        )
        assert moment is not None
        assert moment.state == "full"
        assert moment.quality == 0.9
    
    def test_get_presence_stats(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        stats = pd.get_presence_stats()
        assert isinstance(stats, dict)
    
    def test_get_presence_suggestion(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        suggestion = pd.get_presence_suggestion("distracted", "work")
        assert isinstance(suggestion, dict)
        assert "technique" in suggestion
    
    def test_get_presence_score(self):
        from core.presence_detector import get_presence_detector
        pd = get_presence_detector()
        score = pd.get_presence_score()
        assert 0 <= score <= 100


# -- Intuition Trainer Tests ------------------------------------------------

class TestIntuitionTrainer:
    """Test Intuition Trainer."""
    
    def test_singleton(self):
        from core.intuition_trainer import get_intuition_trainer
        i1 = get_intuition_trainer()
        i2 = get_intuition_trainer()
        assert i1 is i2
    
    def test_record_hunch(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        hunch = it.record_hunch(
            "Don't take this job",
            "work",
            "somatic",
            0.7,
            True,
            "confirmed",
            "The salary is great",
            "Boss turned out toxic",
        )
        assert hunch is not None
        assert hunch.hunch == "Don't take this job"
        assert hunch.followed is True
        assert hunch.outcome == "confirmed"
    
    def test_get_intuition_stats(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        stats = it.get_intuition_stats()
        assert isinstance(stats, dict)
    
    def test_get_intuition_exercise(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        exercise = it.get_intuition_exercise("somatic", "relationship")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_intuition_score(self):
        from core.intuition_trainer import get_intuition_trainer
        it = get_intuition_trainer()
        score = it.get_intuition_score()
        assert 0 <= score <= 100



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



# -- Discipline Trainer Tests -----------------------------------------------

class TestDisciplineTrainer:
    """Test Discipline Trainer."""
    
    def test_singleton(self):
        from core.discipline_trainer import get_discipline_trainer
        d1 = get_discipline_trainer()
        d2 = get_discipline_trainer()
        assert d1 is d2
    
    def test_record_commitment(self):
        from core.discipline_trainer import get_discipline_trainer
        dt = get_discipline_trainer()
        commitment = dt.record_commitment(
            "Morning workout",
            "health",
            True,
            "morning",
            0.8,
            0.3,
            "I am someone who moves daily",
            "Proud and energized",
        )
        assert commitment is not None
        assert commitment.commitment == "Morning workout"
        assert commitment.kept is True
    
    def test_get_discipline_stats(self):
        from core.discipline_trainer import get_discipline_trainer
        dt = get_discipline_trainer()
        stats = dt.get_discipline_stats()
        assert isinstance(stats, dict)
    
    def test_get_discipline_suggestion(self):
        from core.discipline_trainer import get_discipline_trainer
        dt = get_discipline_trainer()
        suggestion = dt.get_discipline_suggestion("meditate daily", "evening", "tired")
        assert isinstance(suggestion, dict)
        assert "environment_designs" in suggestion
    
    def test_get_discipline_score(self):
        from core.discipline_trainer import get_discipline_trainer
        dt = get_discipline_trainer()
        score = dt.get_discipline_score()
        assert 0 <= score <= 100


# -- Consistency Coach Tests ------------------------------------------------

class TestConsistencyCoach:
    """Test Consistency Coach."""
    
    def test_singleton(self):
        from core.consistency_coach import get_consistency_coach
        c1 = get_consistency_coach()
        c2 = get_consistency_coach()
        assert c1 is c2
    
    def test_record_action(self):
        from core.consistency_coach import get_consistency_coach
        cc = get_consistency_coach()
        action = cc.record_action(
            "Read 20 pages",
            "learning",
            True,
            0.8,
            30,
            0.2,
            0.7,
            False,
        )
        assert action is not None
        assert action.action == "Read 20 pages"
        assert action.done is True
    
    def test_get_consistency_stats(self):
        from core.consistency_coach import get_consistency_coach
        cc = get_consistency_coach()
        stats = cc.get_consistency_stats()
        assert isinstance(stats, dict)
    
    def test_get_sustainability_suggestion(self):
        from core.consistency_coach import get_consistency_coach
        cc = get_consistency_coach()
        suggestion = cc.get_sustainability_suggestion("fitness", 14, "good")
        assert isinstance(suggestion, dict)
        assert "message" in suggestion
    
    def test_get_consistency_score(self):
        from core.consistency_coach import get_consistency_coach
        cc = get_consistency_coach()
        score = cc.get_consistency_score()
        assert 0 <= score <= 100


# -- Accountability Partner Tests -------------------------------------------

class TestAccountabilityPartner:
    """Test Accountability Partner."""
    
    def test_singleton(self):
        from core.accountability_partner import get_accountability_partner
        a1 = get_accountability_partner()
        a2 = get_accountability_partner()
        assert a1 is a2
    
    def test_record_commitment_shared(self):
        from core.accountability_partner import get_accountability_partner
        ap = get_accountability_partner()
        commitment = ap.record_commitment_shared(
            "Write book chapter",
            "Writing group",
            "group",
            "weekly",
            4,
            True,
            "supportive",
            0.9,
        )
        assert commitment is not None
        assert commitment.commitment == "Write book chapter"
        assert commitment.completed is True
    
    def test_get_accountability_stats(self):
        from core.accountability_partner import get_accountability_partner
        ap = get_accountability_partner()
        stats = ap.get_accountability_stats()
        assert isinstance(stats, dict)
    
    def test_get_accountability_design(self):
        from core.accountability_partner import get_accountability_partner
        ap = get_accountability_partner()
        design = ap.get_accountability_design("Launch product", "public", "high")
        assert isinstance(design, dict)
        assert "check_in" in design
    
    def test_get_accountability_score(self):
        from core.accountability_partner import get_accountability_partner
        ap = get_accountability_partner()
        score = ap.get_accountability_score()
        assert 0 <= score <= 100


# -- Progress Celebrator Tests ----------------------------------------------

class TestProgressCelebrator:
    """Test Progress Celebrator."""
    
    def test_singleton(self):
        from core.progress_celebrator import get_progress_celebrator
        p1 = get_progress_celebrator()
        p2 = get_progress_celebrator()
        assert p1 is p2
    
    def test_record_win(self):
        from core.progress_celebrator import get_progress_celebrator
        pc = get_progress_celebrator()
        win = pc.record_win(
            "Finished marathon",
            "milestone",
            "health",
            "persistence",
            "Bought running shoes I've wanted",
            0.9,
            0.9,
            0.95,
        )
        assert win is not None
        assert win.description == "Finished marathon"
        assert win.win_size == "milestone"
    
    def test_get_progress_stats(self):
        from core.progress_celebrator import get_progress_celebrator
        pc = get_progress_celebrator()
        stats = pc.get_progress_stats()
        assert isinstance(stats, dict)
    
    def test_get_celebration_suggestion(self):
        from core.progress_celebrator import get_progress_celebrator
        pc = get_progress_celebrator()
        suggestion = pc.get_celebration_suggestion("large", "experiential", 0.8)
        assert isinstance(suggestion, dict)
        assert "celebration" in suggestion
    
    def test_get_progress_score(self):
        from core.progress_celebrator import get_progress_celebrator
        pc = get_progress_celebrator()
        score = pc.get_progress_score()
        assert 0 <= score <= 100



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
