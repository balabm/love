


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



# -- Identity Designer Tests -------------------------------------------------

class TestIdentityDesigner:
    """Test Identity Designer."""
    
    def test_singleton(self):
        from core.identity_designer import get_identity_designer
        i1 = get_identity_designer()
        i2 = get_identity_designer()
        assert i1 is i2
    
    def test_record_identity(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        entry = idd.record_identity(
            "I am a runner",
            ["Ran 3 times this week", "Enjoyed the process"],
            0.7,
            "current",
            0.8,
            "self",
        )
        assert entry is not None
        assert entry.identity_statement == "I am a runner"
        assert entry.strength == 0.7
    
    def test_get_identity_stats(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        stats = idd.get_identity_stats()
        assert isinstance(stats, dict)
    
    def test_get_identity_design(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        design = idd.get_identity_design("I am a writer", 0.6, "creativity")
        assert isinstance(design, dict)
        assert "small_steps" in design
    
    def test_get_identity_score(self):
        from core.identity_designer import get_identity_designer
        idd = get_identity_designer()
        score = idd.get_identity_score()
        assert 0 <= score <= 100


# -- Habit Architect Tests --------------------------------------------------

class TestHabitArchitect:
    """Test Habit Architect."""
    
    def test_singleton(self):
        from core.habit_architect import get_habit_architect
        h1 = get_habit_architect()
        h2 = get_habit_architect()
        assert h1 is h2
    
    def test_record_habit_attempt(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        attempt = ha.record_habit_attempt(
            "Morning meditation",
            "health",
            True,
            "Wake up alarm",
            "Feel calm",
            0.2,
            0.8,
            "I am mindful",
        )
        assert attempt is not None
        assert attempt.habit == "Morning meditation"
        assert attempt.success is True
    
    def test_get_habit_stats(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        stats = ha.get_habit_stats()
        assert isinstance(stats, dict)
    
    def test_get_habit_design(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        design = ha.get_habit_design("Read daily", "morning coffee", 0.6)
        assert isinstance(design, dict)
        assert "stack_template" in design
    
    def test_get_habit_score(self):
        from core.habit_architect import get_habit_architect
        ha = get_habit_architect()
        score = ha.get_habit_score()
        assert 0 <= score <= 100


# -- Environment Curator Tests ----------------------------------------------

class TestEnvironmentCurator:
    """Test Environment Curator."""
    
    def test_singleton(self):
        from core.environment_curator import get_environment_curator
        e1 = get_environment_curator()
        e2 = get_environment_curator()
        assert e1 is e2
    
    def test_record_environment(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        entry = ec.record_environment(
            "office",
            "clutter",
            -0.6,
            "focus",
            -0.4,
            "Cleared desk",
        )
        assert entry is not None
        assert entry.space == "office"
        assert entry.factor == "clutter"
    
    def test_get_environment_stats(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        stats = ec.get_environment_stats()
        assert isinstance(stats, dict)
    
    def test_get_curation_suggestion(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        suggestion = ec.get_curation_suggestion("focus", "office", "low")
        assert isinstance(suggestion, dict)
        assert "modifications" in suggestion
    
    def test_get_environment_score(self):
        from core.environment_curator import get_environment_curator
        ec = get_environment_curator()
        score = ec.get_environment_score()
        assert 0 <= score <= 100


# -- Ritual Master Tests ----------------------------------------------------

class TestRitualMaster:
    """Test Ritual Master."""
    
    def test_singleton(self):
        from core.ritual_master import get_ritual_master
        r1 = get_ritual_master()
        r2 = get_ritual_master()
        assert r1 is r2
    
    def test_record_ritual(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        ritual = rm.record_ritual(
            "Evening wind-down",
            "transition",
            0.8,
            0.9,
            20,
            "work_to_rest",
            ["lighting", "sound", "movement"],
        )
        assert ritual is not None
        assert ritual.ritual == "Evening wind-down"
        assert ritual.transition == "work_to_rest"
    
    def test_get_ritual_stats(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        stats = rm.get_ritual_stats()
        assert isinstance(stats, dict)
    
    def test_get_ritual_design(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        design = rm.get_ritual_design("morning", "minimal", 5)
        assert isinstance(design, dict)
        assert "template" in design
    
    def test_get_ritual_score(self):
        from core.ritual_master import get_ritual_master
        rm = get_ritual_master()
        score = rm.get_ritual_score()
        assert 0 <= score <= 100



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



# -- Emotional Intelligence Trainer Tests ----------------------------------

class TestEmotionalIntelligenceTrainer:
    """Test Emotional Intelligence Trainer."""
    
    def test_singleton(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        e1 = get_emotional_intelligence_trainer()
        e2 = get_emotional_intelligence_trainer()
        assert e1 is e2
    
    def test_record_emotion(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        entry = eq.record_emotion(
            "anxious",
            "fear",
            "Upcoming presentation",
            0.7,
            "Box breathing",
            0.6,
            "work",
            "tight chest",
        )
        assert entry is not None
        assert entry.emotion == "anxious"
        assert entry.intensity == 0.7
    
    def test_get_eq_stats(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        stats = eq.get_eq_stats()
        assert isinstance(stats, dict)
    
    def test_get_eq_exercise(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        exercise = eq.get_eq_exercise("regulation", 0.4)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_eq_score(self):
        from core.emotional_intelligence_trainer import get_emotional_intelligence_trainer
        eq = get_emotional_intelligence_trainer()
        score = eq.get_eq_score()
        assert 0 <= score <= 100


# -- Empathy Builder Tests --------------------------------------------------

class TestEmpathyBuilder:
    """Test Empathy Builder."""
    
    def test_singleton(self):
        from core.empathy_builder import get_empathy_builder
        e1 = get_empathy_builder()
        e2 = get_empathy_builder()
        assert e1 is e2
    
    def test_record_empathy_attempt(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        attempt = eb.record_empathy_attempt(
            "Friend lost job",
            "Sarah",
            "close",
            0.8,
            0.7,
            "Listened without offering solutions",
            "Wanted to fix it",
            0.3,
        )
        assert attempt is not None
        assert attempt.situation == "Friend lost job"
        assert attempt.accuracy == 0.8
    
    def test_get_empathy_stats(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        stats = eb.get_empathy_stats()
        assert isinstance(stats, dict)
    
    def test_get_empathy_exercise(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        exercise = eb.get_empathy_exercise("difficult", 0.8)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_empathy_score(self):
        from core.empathy_builder import get_empathy_builder
        eb = get_empathy_builder()
        score = eb.get_empathy_score()
        assert 0 <= score <= 100


# -- Compassion Generator Tests ---------------------------------------------

class TestCompassionGenerator:
    """Test Compassion Generator."""
    
    def test_singleton(self):
        from core.compassion_generator import get_compassion_generator
        c1 = get_compassion_generator()
        c2 = get_compassion_generator()
        assert c1 is c2
    
    def test_record_compassion(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        entry = cg.record_compassion(
            "Self",
            "self",
            "tender",
            0.8,
            0.7,
            "Loving-kindness meditation",
            "Feeling undeserving",
        )
        assert entry is not None
        assert entry.target == "Self"
        assert entry.intensity == 0.8
    
    def test_get_compassion_stats(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        stats = cg.get_compassion_stats()
        assert isinstance(stats, dict)
    
    def test_get_compassion_practice(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        practice = cg.get_compassion_practice("difficult", 0.7)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_compassion_score(self):
        from core.compassion_generator import get_compassion_generator
        cg = get_compassion_generator()
        score = cg.get_compassion_score()
        assert 0 <= score <= 100


# -- Gratitude Amplifier Tests ----------------------------------------------

class TestGratitudeAmplifier:
    """Test Gratitude Amplifier."""
    
    def test_singleton(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        g1 = get_gratitude_amplifier()
        g2 = get_gratitude_amplifier()
        assert g1 is g2
    
    def test_record_gratitude(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        entry = ga.record_gratitude(
            "Morning coffee ritual",
            "simple",
            0.9,
            0.6,
            "Savoring practice",
            True,
            0.6,
            0.8,
        )
        assert entry is not None
        assert entry.target == "Morning coffee ritual"
        assert entry.depth == 0.9
    
    def test_get_gratitude_stats(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        stats = ga.get_gratitude_stats()
        assert isinstance(stats, dict)
    
    def test_get_amplification_exercise(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        exercise = ga.get_amplification_exercise("novelty", "nature")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_gratitude_score(self):
        from core.gratitude_amplifier import get_gratitude_amplifier
        ga = get_gratitude_amplifier()
        score = ga.get_gratitude_score()
        assert 0 <= score <= 100



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



# -- Sleep Optimizer Tests --------------------------------------------------

class TestSleepOptimizer:
    """Test Sleep Optimizer."""
    
    def test_singleton(self):
        from core.sleep_optimizer import get_sleep_optimizer
        s1 = get_sleep_optimizer()
        s2 = get_sleep_optimizer()
        assert s1 is s2
    
    def test_record_sleep_session(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        session = so.record_sleep_session(
            7.5,
            0.8,
            15,
            1,
            20.0,
            25.0,
            "23:00",
            "06:30",
            False,
            10,
            False,
            False,
            0.3,
            68.0,
        )
        assert session is not None
        assert session.duration_hours == 7.5
        assert session.quality == 0.8
    
    def test_get_sleep_stats(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        stats = so.get_sleep_stats()
        assert isinstance(stats, dict)
    
    def test_get_sleep_recommendation(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        rec = so.get_sleep_recommendation(3.0, "night_owl")
        assert isinstance(rec, dict)
        assert "routine" in rec
    
    def test_get_sleep_score(self):
        from core.sleep_optimizer import get_sleep_optimizer
        so = get_sleep_optimizer()
        score = so.get_sleep_score()
        assert 0 <= score <= 100


# -- Nutrition Coach Tests --------------------------------------------------

class TestNutritionCoach:
    """Test Nutrition Coach."""
    
    def test_singleton(self):
        from core.nutrition_coach import get_nutrition_coach
        n1 = get_nutrition_coach()
        n2 = get_nutrition_coach()
        assert n1 is n2
    
    def test_record_meal(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        entry = nc.record_meal(
            ["Oatmeal", "Berries", "Almonds"],
            "breakfast",
            "planned",
            0.6,
            0.7,
            "slow",
            0.5,
            0.7,
            0.8,
            True,
            True,
            False,
        )
        assert entry is not None
        assert entry.meal_type == "breakfast"
        assert entry.protein_present is True
    
    def test_get_nutrition_stats(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        stats = nc.get_nutrition_stats()
        assert isinstance(stats, dict)
    
    def test_get_meal_suggestion(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        suggestion = nc.get_meal_suggestion("energy", ["vegetarian"])
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_nutrition_score(self):
        from core.nutrition_coach import get_nutrition_coach
        nc = get_nutrition_coach()
        score = nc.get_nutrition_score()
        assert 0 <= score <= 100


# -- Movement Tracker Tests -------------------------------------------------

class TestMovementTracker:
    """Test Movement Tracker."""
    
    def test_singleton(self):
        from core.movement_tracker import get_movement_tracker
        m1 = get_movement_tracker()
        m2 = get_movement_tracker()
        assert m1 is m2
    
    def test_record_session(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        session = mt.record_session(
            "Morning jog",
            "run",
            30,
            0.7,
            0.5,
            0.8,
            0.9,
            "energized",
            False,
            True,
        )
        assert session is not None
        assert session.activity == "Morning jog"
        assert session.movement_type == "run"
        assert session.outdoors is True
    
    def test_get_movement_stats(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        stats = mt.get_movement_stats()
        assert isinstance(stats, dict)
    
    def test_get_movement_suggestion(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        suggestion = mt.get_movement_suggestion(0.3, 0.4, 15, "social")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_movement_score(self):
        from core.movement_tracker import get_movement_tracker
        mt = get_movement_tracker()
        score = mt.get_movement_score()
        assert 0 <= score <= 100


# -- Health Integrator Tests ------------------------------------------------

class TestHealthIntegrator:
    """Test Health Integrator."""
    
    def test_singleton(self):
        from core.health_integrator import get_health_integrator
        h1 = get_health_integrator()
        h2 = get_health_integrator()
        assert h1 is h2
    
    def test_record_wellbeing_snapshot(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        snapshot = hi.record_wellbeing_snapshot(
            7.5,
            0.8,
            0.7,
            30,
            0.8,
            0.7,
            0.6,
            0.4,
            0.7,
            0.8,
        )
        assert snapshot is not None
        assert snapshot.sleep_hours == 7.5
        assert snapshot.mood == 0.7
    
    def test_get_health_stats(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        stats = hi.get_health_stats()
        assert isinstance(stats, dict)
    
    def test_get_health_priority(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        priority = hi.get_health_priority({"sleep": 0.3, "nutrition": 0.7, "movement": 0.6, "mood": 0.5, "energy": 0.4, "stress": 0.8})
        assert isinstance(priority, dict)
        assert "priority_domain" in priority
    
    def test_get_health_score(self):
        from core.health_integrator import get_health_integrator
        hi = get_health_integrator()
        score = hi.get_health_score()
        assert 0 <= score <= 100



# -- Digital Minimalism Coach Tests -----------------------------------------

class TestDigitalMinimalismCoach:
    """Test Digital Minimalism Coach."""
    
    def test_singleton(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        d1 = get_digital_minimalism_coach()
        d2 = get_digital_minimalism_coach()
        assert d1 is d2
    
    def test_record_session(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        session = dmc.record_session(
            "Instagram",
            "social_media",
            45,
            0.2,
            0.1,
            0.6,
            0.4,
            0.3,
            True,
        )
        assert session is not None
        assert session.app_or_site == "Instagram"
        assert session.compulsive is True
    
    def test_get_digital_stats(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        stats = dmc.get_digital_stats()
        assert isinstance(stats, dict)
    
    def test_get_minimalism_practice(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        practice = dmc.get_minimalism_practice("escapist", "reduce_compulsive")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_digital_score(self):
        from core.digital_minimalism_coach import get_digital_minimalism_coach
        dmc = get_digital_minimalism_coach()
        score = dmc.get_digital_score()
        assert 0 <= score <= 100


# -- Focus Ritual Designer Tests --------------------------------------------

class TestFocusRitualDesigner:
    """Test Focus Ritual Designer."""
    
    def test_singleton(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        f1 = get_focus_ritual_designer()
        f2 = get_focus_ritual_designer()
        assert f1 is f2
    
    def test_record_ritual(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        entry = frd.record_ritual(
            "Morning writing ritual",
            "creative",
            ["Clear desk", "Close apps", "Set timer", "Write intention", "3 deep breaths"],
            10,
            0.9,
            1.0,
            0.7,
            0.6,
            0.9,
        )
        assert entry is not None
        assert entry.name == "Morning writing ritual"
        assert len(entry.components) == 5
    
    def test_get_ritual_stats(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        stats = frd.get_ritual_stats()
        assert isinstance(stats, dict)
    
    def test_get_ritual_design(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        design = frd.get_ritual_design("deep_work", 0.8, 8)
        assert isinstance(design, dict)
        assert "components" in design
    
    def test_get_ritual_score(self):
        from core.focus_ritual_designer import get_focus_ritual_designer
        frd = get_focus_ritual_designer()
        score = frd.get_ritual_score()
        assert 0 <= score <= 100


# -- Attention Recovery Specialist Tests ------------------------------------

class TestAttentionRecoverySpecialist:
    """Test Attention Recovery Specialist."""
    
    def test_singleton(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        a1 = get_attention_recovery_specialist()
        a2 = get_attention_recovery_specialist()
        assert a1 is a2
    
    def test_record_attention_state(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        state = ars.record_attention_state(
            0.3,
            "sustained",
            "social_media",
            30,
            0.4,
            "Walk outside",
            0.7,
        )
        assert state is not None
        assert state.focus_level == 0.3
        assert state.source == "social_media"
    
    def test_get_attention_stats(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        stats = ars.get_attention_stats()
        assert isinstance(stats, dict)
    
    def test_get_recovery_protocol(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        protocol = ars.get_recovery_protocol("digital_overload", "high")
        assert isinstance(protocol, dict)
        assert "protocol" in protocol
    
    def test_get_attention_score(self):
        from core.attention_recovery_specialist import get_attention_recovery_specialist
        ars = get_attention_recovery_specialist()
        score = ars.get_attention_score()
        assert 0 <= score <= 100


# -- Cognitive Load Manager Tests -------------------------------------------

class TestCognitiveLoadManager:
    """Test Cognitive Load Manager."""
    
    def test_singleton(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        c1 = get_cognitive_load_manager()
        c2 = get_cognitive_load_manager()
        assert c1 is c2
    
    def test_record_load_event(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        event = clm.record_load_event(
            "decisions",
            0.8,
            60,
            ["fatigue", "irritability"],
            0.6,
            0.3,
            0.4,
        )
        assert event is not None
        assert event.source == "decisions"
        assert event.intensity == 0.8
    
    def test_get_cognitive_stats(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        stats = clm.get_cognitive_stats()
        assert isinstance(stats, dict)
    
    def test_get_load_reduction(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        reduction = clm.get_load_reduction("decisions", 0.7)
        assert isinstance(reduction, dict)
        assert "reduction_technique" in reduction
    
    def test_get_cognitive_score(self):
        from core.cognitive_load_manager import get_cognitive_load_manager
        clm = get_cognitive_load_manager()
        score = clm.get_cognitive_score()
        assert 0 <= score <= 100



# -- Stress Resilience Trainer Tests ----------------------------------------

class TestStressResilienceTrainer:
    """Test Stress Resilience Trainer."""
    
    def test_singleton(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        s1 = get_stress_resilience_trainer()
        s2 = get_stress_resilience_trainer()
        assert s1 is s2
    
    def test_record_stress_event(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        event = srt.record_stress_event(
            "Deadline pressure",
            "acute",
            0.8,
            "fight",
            60,
            30,
            "Walk outside",
            0.6,
            0.4,
        )
        assert event is not None
        assert event.trigger == "Deadline pressure"
        assert event.intensity == 0.8
    
    def test_get_stress_stats(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        stats = srt.get_stress_stats()
        assert isinstance(stats, dict)
    
    def test_get_resilience_practice(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        practice = srt.get_resilience_practice("chronic", 0.4)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_resilience_score(self):
        from core.stress_resilience_trainer import get_stress_resilience_trainer
        srt = get_stress_resilience_trainer()
        score = srt.get_resilience_score()
        assert 0 <= score <= 100


# -- Emotional Regulation Coach Tests --------------------------------------

class TestEmotionalRegulationCoach:
    """Test Emotional Regulation Coach."""
    
    def test_singleton(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        e1 = get_emotional_regulation_coach()
        e2 = get_emotional_regulation_coach()
        assert e1 is e2
    
    def test_record_emotion(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        entry = erc.record_emotion(
            "anger",
            "Criticism at work",
            0.7,
            "reappraisal",
            0.8,
            "work",
            "tight chest",
            "Spoke calmly, set boundary",
        )
        assert entry is not None
        assert entry.emotion == "anger"
        assert entry.regulation_strategy == "reappraisal"
    
    def test_get_regulation_stats(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        stats = erc.get_regulation_stats()
        assert isinstance(stats, dict)
    
    def test_get_regulation_technique(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        technique = erc.get_regulation_technique("anxiety", "social", 0.5)
        assert isinstance(technique, dict)
        assert "technique" in technique
    
    def test_get_regulation_score(self):
        from core.emotional_regulation_coach import get_emotional_regulation_coach
        erc = get_emotional_regulation_coach()
        score = erc.get_regulation_score()
        assert 0 <= score <= 100


# -- Mindfulness Trainer Tests ----------------------------------------------

class TestMindfulnessTrainer:
    """Test Mindfulness Trainer."""
    
    def test_singleton(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        m1 = get_mindfulness_trainer()
        m2 = get_mindfulness_trainer()
        assert m1 is m2
    
    def test_record_practice(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        practice = mt.record_practice(
            "breath",
            15,
            0.7,
            8,
            8,
            0.6,
            0.5,
            0.8,
        )
        assert practice is not None
        assert practice.practice_type == "breath"
        assert practice.duration_minutes == 15
    
    def test_get_mindfulness_stats(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        stats = mt.get_mindfulness_stats()
        assert isinstance(stats, dict)
    
    def test_get_practice_suggestion(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        suggestion = mt.get_practice_suggestion("stress", 0.4)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_mindfulness_score(self):
        from core.mindfulness_trainer import get_mindfulness_trainer
        mt = get_mindfulness_trainer()
        score = mt.get_mindfulness_score()
        assert 0 <= score <= 100


# -- Presence Amplifier Tests -----------------------------------------------

class TestPresenceAmplifier:
    """Test Presence Amplifier."""
    
    def test_singleton(self):
        from core.presence_amplifier import get_presence_amplifier
        p1 = get_presence_amplifier()
        p2 = get_presence_amplifier()
        assert p1 is p2
    
    def test_record_presence(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        entry = pa.record_presence(
            "meal",
            0.8,
            ["Taste", "Smell", "Texture"],
            ["Phone notification"],
            0.9,
            20,
        )
        assert entry is not None
        assert entry.context == "meal"
        assert entry.depth == 0.8
    
    def test_get_presence_stats(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        stats = pa.get_presence_stats()
        assert isinstance(stats, dict)
    
    def test_get_presence_practice(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        practice = pa.get_presence_practice("conversation", 0.6)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_presence_score(self):
        from core.presence_amplifier import get_presence_amplifier
        pa = get_presence_amplifier()
        score = pa.get_presence_score()
        assert 0 <= score <= 100



# -- Creativity Catalyst Tests ----------------------------------------------

class TestCreativityCatalyst:
    """Test Creativity Catalyst."""
    
    def test_singleton(self):
        from core.creativity_catalyst import get_creativity_catalyst
        c1 = get_creativity_catalyst()
        c2 = get_creativity_catalyst()
        assert c1 is c2
    
    def test_record_session(self):
        from core.creativity_catalyst import get_creativity_catalyst
        cc = get_creativity_catalyst()
        session = cc.record_session(
            "Brainstorming new product features",
            "design",
            8,
            0.7,
            "none",
            "Morning coffee in cafe",
            0.6,
            0.5,
            0.8,
        )
        assert session is not None
        assert session.activity == "Brainstorming new product features"
        assert session.domain == "design"
    
    def test_get_creative_stats(self):
        from core.creativity_catalyst import get_creativity_catalyst
        cc = get_creativity_catalyst()
        stats = cc.get_creative_stats()
        assert isinstance(stats, dict)
    
    def test_get_creative_prompt(self):
        from core.creativity_catalyst import get_creativity_catalyst
        cc = get_creativity_catalyst()
        prompt = cc.get_creative_prompt("perfectionism", "writing")
        assert isinstance(prompt, dict)
        assert "prompt" in prompt
    
    def test_get_creative_score(self):
        from core.creativity_catalyst import get_creativity_catalyst
        cc = get_creativity_catalyst()
        score = cc.get_creative_score()
        assert 0 <= score <= 100


# -- Innovation Spark Generator Tests ---------------------------------------

class TestInnovationSparkGenerator:
    """Test Innovation Spark Generator."""
    
    def test_singleton(self):
        from core.innovation_spark_generator import get_innovation_spark_generator
        i1 = get_innovation_spark_generator()
        i2 = get_innovation_spark_generator()
        assert i1 is i2
    
    def test_record_innovation(self):
        from core.innovation_spark_generator import get_innovation_spark_generator
        isg = get_innovation_spark_generator()
        entry = isg.record_innovation(
            "Subscription model for physical goods",
            "analogy",
            "retail",
            "software",
            0.8,
            0.6,
            0.9,
            "prototyped",
        )
        assert entry is not None
        assert entry.idea == "Subscription model for physical goods"
        assert entry.source == "analogy"
    
    def test_get_innovation_stats(self):
        from core.innovation_spark_generator import get_innovation_spark_generator
        isg = get_innovation_spark_generator()
        stats = isg.get_innovation_stats()
        assert isinstance(stats, dict)
    
    def test_get_spark_challenge(self):
        from core.innovation_spark_generator import get_innovation_spark_generator
        isg = get_innovation_spark_generator()
        challenge = isg.get_spark_challenge("healthcare", "constraint")
        assert isinstance(challenge, dict)
        assert "challenge" in challenge
    
    def test_get_innovation_score(self):
        from core.innovation_spark_generator import get_innovation_spark_generator
        isg = get_innovation_spark_generator()
        score = isg.get_innovation_score()
        assert 0 <= score <= 100


# -- Problem Reframer Tests -------------------------------------------------

class TestProblemReframer:
    """Test Problem Reframer."""
    
    def test_singleton(self):
        from core.problem_reframer import get_problem_reframer
        p1 = get_problem_reframer()
        p2 = get_problem_reframer()
        assert p1 is p2
    
    def test_record_problem(self):
        from core.problem_reframer import get_problem_reframer
        pr = get_problem_reframer()
        entry = pr.record_problem(
            "Team conflicts over priorities",
            "relational",
            "People are difficult",
            "We need better alignment processes",
            "perspective_shift",
            0.8,
            45,
            0.9,
        )
        assert entry is not None
        assert entry.problem == "Team conflicts over priorities"
        assert entry.reframe_strategy == "perspective_shift"
    
    def test_get_reframing_stats(self):
        from core.problem_reframer import get_problem_reframer
        pr = get_problem_reframer()
        stats = pr.get_reframing_stats()
        assert isinstance(stats, dict)
    
    def test_get_reframe_suggestion(self):
        from core.problem_reframer import get_problem_reframer
        pr = get_problem_reframer()
        suggestion = pr.get_reframe_suggestion("strategic", 0.6)
        assert isinstance(suggestion, dict)
        assert "reframe" in suggestion
    
    def test_get_reframing_score(self):
        from core.problem_reframer import get_problem_reframer
        pr = get_problem_reframer()
        score = pr.get_reframing_score()
        assert 0 <= score <= 100


# -- Perspective Shifter Tests ---------------------------------------------

class TestPerspectiveShifter:
    """Test Perspective Shifter."""
    
    def test_singleton(self):
        from core.perspective_shifter import get_perspective_shifter
        p1 = get_perspective_shifter()
        p2 = get_perspective_shifter()
        assert p1 is p2
    
    def test_record_shift(self):
        from core.perspective_shifter import get_perspective_shifter
        ps = get_perspective_shifter()
        shift = ps.record_shift(
            "Disagreement with partner",
            "They're being unreasonable",
            "They're overwhelmed and expressing it poorly",
            "role_taking",
            0.9,
            "Resolved conflict peacefully",
        )
        assert shift is not None
        assert shift.situation == "Disagreement with partner"
        assert shift.shift_technique == "role_taking"
    
    def test_get_perspective_stats(self):
        from core.perspective_shifter import get_perspective_shifter
        ps = get_perspective_shifter()
        stats = ps.get_perspective_stats()
        assert isinstance(stats, dict)
    
    def test_get_perspective_shift(self):
        from core.perspective_shifter import get_perspective_shifter
        ps = get_perspective_shifter()
        shift = ps.get_perspective_shift("Project failure", "confirmation_bias")
        assert isinstance(shift, dict)
        assert "shift" in shift
    
    def test_get_perspective_score(self):
        from core.perspective_shifter import get_perspective_shifter
        ps = get_perspective_shifter()
        score = ps.get_perspective_score()
        assert 0 <= score <= 100



# -- Curiosity Cultivator Tests ---------------------------------------------

class TestCuriosityCultivator:
    """Test Curiosity Cultivator."""
    
    def test_singleton(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        c1 = get_curiosity_cultivator()
        c2 = get_curiosity_cultivator()
        assert c1 is c2
    
    def test_record_curiosity(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        entry = cc.record_curiosity(
            "Why do some people thrive under pressure while others crumble?",
            "epistemic",
            0.8,
            "Podcast about stress responses",
            "Read research on eustress",
            0.9,
        )
        assert entry is not None
        assert entry.topic == "Why do some people thrive under pressure while others crumble?"
        assert entry.curiosity_type == "epistemic"
    
    def test_get_curiosity_stats(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        stats = cc.get_curiosity_stats()
        assert isinstance(stats, dict)
    
    def test_get_curiosity_practice(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        practice = cc.get_curiosity_practice("certainty", "science")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_curiosity_score(self):
        from core.curiosity_cultivator import get_curiosity_cultivator
        cc = get_curiosity_cultivator()
        score = cc.get_curiosity_score()
        assert 0 <= score <= 100


# -- Learning Acceleration Engine Tests -------------------------------------

class TestLearningAccelerationEngine:
    """Test Learning Acceleration Engine."""
    
    def test_singleton(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        l1 = get_learning_acceleration_engine()
        l2 = get_learning_acceleration_engine()
        assert l1 is l2
    
    def test_record_session(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        session = lae.record_session(
            "Machine Learning Fundamentals",
            "active_recall",
            45,
            0.7,
            0.8,
            0.6,
            0.9,
        )
        assert session is not None
        assert session.topic == "Machine Learning Fundamentals"
        assert session.technique == "active_recall"
    
    def test_get_learning_stats(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        stats = lae.get_learning_stats()
        assert isinstance(stats, dict)
    
    def test_get_acceleration_plan(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        plan = lae.get_acceleration_plan("Python Programming", "2 weeks", 0.3, 0.8)
        assert isinstance(plan, dict)
        assert "recommended_techniques" in plan
    
    def test_get_learning_score(self):
        from core.learning_acceleration_engine import get_learning_acceleration_engine
        lae = get_learning_acceleration_engine()
        score = lae.get_learning_score()
        assert 0 <= score <= 100


# -- Knowledge Synthesizer Tests --------------------------------------------

class TestKnowledgeSynthesizer:
    """Test Knowledge Synthesizer."""
    
    def test_singleton(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        k1 = get_knowledge_synthesizer()
        k2 = get_knowledge_synthesizer()
        assert k1 is k2
    
    def test_record_knowledge(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        entry = ks.record_knowledge(
            "Neuroplasticity",
            "book",
            "neuroscience",
            ["habits", "learning", "brain"],
            "The brain rewires itself based on repeated behaviors",
            0.9,
        )
        assert entry is not None
        assert entry.topic == "Neuroplasticity"
        assert len(entry.connections) == 3
    
    def test_get_synthesis_stats(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        stats = ks.get_synthesis_stats()
        assert isinstance(stats, dict)
    
    def test_get_synthesis_exercise(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        exercise = ks.get_synthesis_exercise(["psychology", "business"], "bridge_silos")
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_synthesis_score(self):
        from core.knowledge_synthesizer import get_knowledge_synthesizer
        ks = get_knowledge_synthesizer()
        score = ks.get_synthesis_score()
        assert 0 <= score <= 100


# -- Wisdom Distiller Tests -------------------------------------------------

class TestWisdomDistiller:
    """Test Wisdom Distiller."""
    
    def test_singleton(self):
        from core.wisdom_distiller import get_wisdom_distiller
        w1 = get_wisdom_distiller()
        w2 = get_wisdom_distiller()
        assert w1 is w2
    
    def test_record_wisdom(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        entry = wd.record_wisdom(
            "Team conflicts over priorities",
            0.8,
            "Alignment comes before execution",
            "Shared purpose prevents resource conflicts",
            0.9,
            0.8,
            "leadership",
        )
        assert entry is not None
        assert entry.situation == "Team conflicts over priorities"
        assert entry.principle == "Shared purpose prevents resource conflicts"
    
    def test_get_wisdom_stats(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        stats = wd.get_wisdom_stats()
        assert isinstance(stats, dict)
    
    def test_get_distillation_practice(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        practice = wd.get_distillation_practice(0.7, "business")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_wisdom_score(self):
        from core.wisdom_distiller import get_wisdom_distiller
        wd = get_wisdom_distiller()
        score = wd.get_wisdom_score()
        assert 0 <= score <= 100



# -- Purpose Clarity Engine Tests -------------------------------------------

class TestPurposeClarityEngine:
    """Test Purpose Clarity Engine."""
    
    def test_singleton(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        p1 = get_purpose_clarity_engine()
        p2 = get_purpose_clarity_engine()
        assert p1 is p2
    
    def test_record_exploration(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        exploration = pce.record_exploration(
            "Career direction",
            0.4,
            0.7,
            0.6,
            "Applied for 3 roles aligned with values",
            0.8,
            0.5,
            0.6,
        )
        assert exploration is not None
        assert exploration.theme == "Career direction"
        assert exploration.clarity_after == 0.7
    
    def test_get_purpose_stats(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        stats = pce.get_purpose_stats()
        assert isinstance(stats, dict)
    
    def test_get_clarity_exercise(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        exercise = pce.get_clarity_exercise("uncertainty", 0.4)
        assert isinstance(exercise, dict)
        assert "exercise" in exercise
    
    def test_get_purpose_score(self):
        from core.purpose_clarity_engine import get_purpose_clarity_engine
        pce = get_purpose_clarity_engine()
        score = pce.get_purpose_score()
        assert 0 <= score <= 100


# -- Legacy Builder Tests ---------------------------------------------------

class TestLegacyBuilder:
    """Test Legacy Builder."""
    
    def test_singleton(self):
        from core.legacy_builder import get_legacy_builder
        l1 = get_legacy_builder()
        l2 = get_legacy_builder()
        assert l1 is l2
    
    def test_record_contribution(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        contribution = lb.record_contribution(
            "Mentored 3 junior developers",
            "mentorship",
            ["Alice", "Bob", "Charlie"],
            0.8,
            0.9,
            0.4,
            0.95,
        )
        assert contribution is not None
        assert contribution.contribution == "Mentored 3 junior developers"
        assert contribution.legacy_type == "mentorship"
    
    def test_get_legacy_stats(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        stats = lb.get_legacy_stats()
        assert isinstance(stats, dict)
    
    def test_get_legacy_plan(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        plan = lb.get_legacy_plan("mentor", "5_years")
        assert isinstance(plan, dict)
        assert "plan" in plan
    
    def test_get_legacy_score(self):
        from core.legacy_builder import get_legacy_builder
        lb = get_legacy_builder()
        score = lb.get_legacy_score()
        assert 0 <= score <= 100


# -- Impact Maximizer Tests -------------------------------------------------

class TestImpactMaximizer:
    """Test Impact Maximizer."""
    
    def test_singleton(self):
        from core.impact_maximizer import get_impact_maximizer
        i1 = get_impact_maximizer()
        i2 = get_impact_maximizer()
        assert i1 is i2
    
    def test_record_impact(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        entry = im.record_impact(
            "Automated reporting pipeline",
            "systemic",
            0.6,
            50,
            "Saved 10 hours/week across team",
            0.9,
            0.8,
        )
        assert entry is not None
        assert entry.action == "Automated reporting pipeline"
        assert entry.impact_type == "systemic"
    
    def test_get_impact_stats(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        stats = im.get_impact_stats()
        assert isinstance(stats, dict)
    
    def test_get_leverage_suggestion(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        suggestion = im.get_leverage_suggestion("busywork", 0.5)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_impact_score(self):
        from core.impact_maximizer import get_impact_maximizer
        im = get_impact_maximizer()
        score = im.get_impact_score()
        assert 0 <= score <= 100


# -- Meaning Amplifier Tests ------------------------------------------------

class TestMeaningAmplifier:
    """Test Meaning Amplifier."""
    
    def test_singleton(self):
        from core.meaning_amplifier import get_meaning_amplifier
        m1 = get_meaning_amplifier()
        m2 = get_meaning_amplifier()
        assert m1 is m2
    
    def test_record_experience(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        entry = ma.record_experience(
            "Difficult conversation with partner",
            "Honest communication deepens trust",
            "relational",
            0.8,
            0.5,
            0.7,
            "relationships",
        )
        assert entry is not None
        assert entry.experience == "Difficult conversation with partner"
        assert entry.meaning_type == "relational"
    
    def test_get_meaning_stats(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        stats = ma.get_meaning_stats()
        assert isinstance(stats, dict)
    
    def test_get_meaning_practice(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        practice = ma.get_meaning_practice("suffering", "health")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_meaning_score(self):
        from core.meaning_amplifier import get_meaning_amplifier
        ma = get_meaning_amplifier()
        score = ma.get_meaning_score()
        assert 0 <= score <= 100



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



# -- Humor & Playfulness Trainer Tests --------------------------------------

class TestHumorPlayfulnessTrainer:
    """Test Humor & Playfulness Trainer."""
    
    def test_singleton(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        h1 = get_humor_playfulness_trainer()
        h2 = get_humor_playfulness_trainer()
        assert h1 is h2
    
    def test_record_play(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        entry = hpt.record_play(
            "Made a dad joke during serious meeting",
            "wordplay",
            0.5,
            0.7,
            0.3,
            "work",
            0.8,
        )
        assert entry is not None
        assert entry.moment == "Made a dad joke during serious meeting"
        assert entry.humor_type == "wordplay"
    
    def test_get_playfulness_stats(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        stats = hpt.get_playfulness_stats()
        assert isinstance(stats, dict)
    
    def test_get_playfulness_practice(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        practice = hpt.get_playfulness_practice(0.8, "work")
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_playfulness_score(self):
        from core.humor_playfulness_trainer import get_humor_playfulness_trainer
        hpt = get_humor_playfulness_trainer()
        score = hpt.get_playfulness_score()
        assert 0 <= score <= 100


# -- Joy Cultivator Tests ---------------------------------------------------

class TestJoyCultivator:
    """Test Joy Cultivator."""
    
    def test_singleton(self):
        from core.joy_cultivator import get_joy_cultivator
        j1 = get_joy_cultivator()
        j2 = get_joy_cultivator()
        assert j1 is j2
    
    def test_record_joy(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        entry = jc.record_joy(
            "Sunrise over the mountains",
            "aesthetic",
            0.9,
            "Morning walk",
            15,
            True,
        )
        assert entry is not None
        assert entry.moment == "Sunrise over the mountains"
        assert entry.joy_type == "aesthetic"
    
    def test_get_joy_stats(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        stats = jc.get_joy_stats()
        assert isinstance(stats, dict)
    
    def test_get_joy_practice(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        practice = jc.get_joy_practice("sensory", 0.5)
        assert isinstance(practice, dict)
        assert "practice" in practice
    
    def test_get_joy_score(self):
        from core.joy_cultivator import get_joy_cultivator
        jc = get_joy_cultivator()
        score = jc.get_joy_score()
        assert 0 <= score <= 100


# -- Celebration Architect Tests --------------------------------------------

class TestCelebrationArchitect:
    """Test Celebration Architect."""
    
    def test_singleton(self):
        from core.celebration_architect import get_celebration_architect
        c1 = get_celebration_architect()
        c2 = get_celebration_architect()
        assert c1 is c2
    
    def test_record_celebration(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        entry = ca.record_celebration(
            "Completed marathon",
            "milestone",
            "Dinner with friends",
            0.9,
            0.7,
            0.9,
            0.9,
            True,
        )
        assert entry is not None
        assert entry.achievement == "Completed marathon"
        assert entry.celebration_type == "milestone"
    
    def test_get_celebration_stats(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        stats = ca.get_celebration_stats()
        assert isinstance(stats, dict)
    
    def test_get_celebration_plan(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        plan = ca.get_celebration_plan(0.8, 0.6)
        assert isinstance(plan, dict)
        assert "celebration" in plan
    
    def test_get_celebration_score(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        score = ca.get_celebration_score()
        assert 0 <= score <= 100


# -- Spontaneity Generator Tests --------------------------------------------

class TestSpontaneityGenerator:
    """Test Spontaneity Generator."""
    
    def test_singleton(self):
        from core.spontaneity_generator import get_spontaneity_generator
        s1 = get_spontaneity_generator()
        s2 = get_spontaneity_generator()
        assert s1 is s2
    
    def test_record_spontaneity(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        entry = sg.record_spontaneity(
            "Took unplanned road trip",
            "experiential",
            0.6,
            0.8,
            0.9,
            0.4,
            True,
        )
        assert entry is not None
        assert entry.moment == "Took unplanned road trip"
        assert entry.spontaneity_type == "experiential"
    
    def test_get_spontaneity_stats(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        stats = sg.get_spontaneity_stats()
        assert isinstance(stats, dict)
    
    def test_get_spontaneous_suggestion(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        suggestion = sg.get_spontaneous_suggestion(0.7, 0.5)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion
    
    def test_get_spontaneity_score(self):
        from core.spontaneity_generator import get_spontaneity_generator
        sg = get_spontaneity_generator()
        score = sg.get_spontaneity_score()
        assert 0 <= score <= 100


# -- Forgiveness Coach Tests -------------------------------------------------

class TestForgivenessCoach:
    """Test Forgiveness Coach."""

    def test_singleton(self):
        from core.forgiveness_coach import get_forgiveness_coach
        c1 = get_forgiveness_coach()
        c2 = get_forgiveness_coach()
        assert c1 is c2

    def test_record_forgiveness(self):
        from core.forgiveness_coach import get_forgiveness_coach
        fc = get_forgiveness_coach()
        entry = fc.record_forgiveness(
            "Former partner",
            "other",
            "understanding",
            0.8,
            0.6,
            0.4,
            True,
            "Let go of resentment",
        )
        assert entry is not None
        assert entry.target == "Former partner"
        assert entry.forgiveness_type == "other"

    def test_get_forgiveness_stats(self):
        from core.forgiveness_coach import get_forgiveness_coach
        fc = get_forgiveness_coach()
        stats = fc.get_forgiveness_stats()
        assert isinstance(stats, dict)

    def test_get_forgiveness_practice(self):
        from core.forgiveness_coach import get_forgiveness_coach
        fc = get_forgiveness_coach()
        practice = fc.get_forgiveness_practice("other", 0.5)
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_forgiveness_score(self):
        from core.forgiveness_coach import get_forgiveness_coach
        fc = get_forgiveness_coach()
        score = fc.get_forgiveness_score()
        assert 0 <= score <= 100


# -- Reconciliation Builder Tests -------------------------------------------

class TestReconciliationBuilder:
    """Test Reconciliation Builder."""

    def test_singleton(self):
        from core.reconciliation_builder import get_reconciliation_builder
        b1 = get_reconciliation_builder()
        b2 = get_reconciliation_builder()
        assert b1 is b2

    def test_record_repair(self):
        from core.reconciliation_builder import get_reconciliation_builder
        rb = get_reconciliation_builder()
        entry = rb.record_repair(
            "Sibling",
            "conflict",
            0.7,
            "apology",
            0.8,
            0.5,
            "restored",
            0.9,
            "Made amends",
        )
        assert entry is not None
        assert entry.relationship == "Sibling"
        assert entry.outcome == "restored"

    def test_get_reconciliation_stats(self):
        from core.reconciliation_builder import get_reconciliation_builder
        rb = get_reconciliation_builder()
        stats = rb.get_reconciliation_stats()
        assert isinstance(stats, dict)

    def test_get_repair_strategy(self):
        from core.reconciliation_builder import get_reconciliation_builder
        rb = get_reconciliation_builder()
        strategy = rb.get_repair_strategy("conflict", "friend")
        assert isinstance(strategy, dict)
        assert "strategy" in strategy

    def test_get_reconciliation_score(self):
        from core.reconciliation_builder import get_reconciliation_builder
        rb = get_reconciliation_builder()
        score = rb.get_reconciliation_score()
        assert 0 <= score <= 100


# -- Trust Architect Tests ---------------------------------------------------

class TestTrustArchitect:
    """Test Trust Architect."""

    def test_singleton(self):
        from core.trust_architect import get_trust_architect
        a1 = get_trust_architect()
        a2 = get_trust_architect()
        assert a1 is a2

    def test_record_action(self):
        from core.trust_architect import get_trust_architect
        ta = get_trust_architect()
        entry = ta.record_action(
            "Delivered project early",
            "competence",
            "Client",
            "Complete by Friday",
            True,
            0.8,
            0.6,
            0.9,
            "Kept promise",
        )
        assert entry is not None
        assert entry.action == "Delivered project early"
        assert entry.commitment_kept is True

    def test_get_trust_stats(self):
        from core.trust_architect import get_trust_architect
        ta = get_trust_architect()
        stats = ta.get_trust_stats()
        assert isinstance(stats, dict)

    def test_get_trust_action(self):
        from core.trust_architect import get_trust_architect
        ta = get_trust_architect()
        action = ta.get_trust_action("consistency", "work")
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_trust_score(self):
        from core.trust_architect import get_trust_architect
        ta = get_trust_architect()
        score = ta.get_trust_score()
        assert 0 <= score <= 100


# -- Repair Specialist Tests -------------------------------------------------

class TestRepairSpecialist:
    """Test Repair Specialist."""

    def test_singleton(self):
        from core.repair_specialist import get_repair_specialist
        s1 = get_repair_specialist()
        s2 = get_repair_specialist()
        assert s1 is s2

    def test_record_repair(self):
        from core.repair_specialist import get_repair_specialist
        rs = get_repair_specialist()
        entry = rs.record_repair(
            "Missed deadlines",
            "habits",
            0.7,
            "Implemented daily planning",
            False,
            3.5,
            "fixed",
            0.9,
            0.4,
            "Back on track",
        )
        assert entry is not None
        assert entry.damage == "Missed deadlines"
        assert entry.outcome == "fixed"

    def test_get_repair_stats(self):
        from core.repair_specialist import get_repair_specialist
        rs = get_repair_specialist()
        stats = rs.get_repair_stats()
        assert isinstance(stats, dict)

    def test_get_repair_plan(self):
        from core.repair_specialist import get_repair_specialist
        rs = get_repair_specialist()
        plan = rs.get_repair_plan("procrastination", "habits", 0.8)
        assert isinstance(plan, dict)
        assert "plan" in plan

    def test_get_repair_score(self):
        from core.repair_specialist import get_repair_specialist
        rs = get_repair_specialist()
        score = rs.get_repair_score()
        assert 0 <= score <= 100


# -- Deep Listener Tests -----------------------------------------------------

class TestDeepListener:
    """Test Deep Listener."""

    def test_singleton(self):
        from core.deep_listener import get_deep_listener
        l1 = get_deep_listener()
        l2 = get_deep_listener()
        assert l1 is l2

    def test_record_session(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        session = dl.record_session(
            "Partner",
            "Career change",
            "empathetic",
            0.8,
            0.9,
            0.85,
            0,
            3,
            "Really heard them",
        )
        assert session is not None
        assert session.speaker == "Partner"
        assert session.comprehension == 0.8

    def test_get_listening_stats(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        stats = dl.get_listening_stats()
        assert isinstance(stats, dict)

    def test_get_listening_practice(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        practice = dl.get_listening_practice("emotional", 0.6)
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_listening_score(self):
        from core.deep_listener import get_deep_listener
        dl = get_deep_listener()
        score = dl.get_listening_score()
        assert 0 <= score <= 100


# -- Conflict Navigator Tests ------------------------------------------------

class TestConflictNavigator:
    """Test Conflict Navigator."""

    def test_singleton(self):
        from core.conflict_navigator import get_conflict_navigator
        n1 = get_conflict_navigator()
        n2 = get_conflict_navigator()
        assert n1 is n2

    def test_record_conflict(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        entry = cn.record_conflict(
            "Roommate",
            "resource",
            0.6,
            "compromise",
            0.8,
            "resolved",
            0.9,
            "Found middle ground",
        )
        assert entry is not None
        assert entry.party == "Roommate"
        assert entry.outcome == "resolved"

    def test_get_conflict_stats(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        stats = cn.get_conflict_stats()
        assert isinstance(stats, dict)

    def test_get_resolution_strategy(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        strategy = cn.get_resolution_strategy("emotional", 0.7)
        assert isinstance(strategy, dict)
        assert "strategy" in strategy

    def test_get_conflict_score(self):
        from core.conflict_navigator import get_conflict_navigator
        cn = get_conflict_navigator()
        score = cn.get_conflict_score()
        assert 0 <= score <= 100


# -- Assertiveness Builder Tests ---------------------------------------------

class TestAssertivenessBuilder:
    """Test Assertiveness Builder."""

    def test_singleton(self):
        from core.assertiveness_builder import get_assertiveness_builder
        b1 = get_assertiveness_builder()
        b2 = get_assertiveness_builder()
        assert b1 is b2

    def test_record_interaction(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        entry = ab.record_interaction(
            "Asked for raise",
            "request",
            "direct",
            0.7,
            0.9,
            0.8,
            "positive",
            "Got it",
        )
        assert entry is not None
        assert entry.situation == "Asked for raise"
        assert entry.outcome == "positive"

    def test_get_assertiveness_stats(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        stats = ab.get_assertiveness_stats()
        assert isinstance(stats, dict)

    def test_get_assertiveness_script(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        script = ab.get_assertiveness_script("work", "boundary")
        assert isinstance(script, dict)
        assert "script" in script

    def test_get_assertiveness_score(self):
        from core.assertiveness_builder import get_assertiveness_builder
        ab = get_assertiveness_builder()
        score = ab.get_assertiveness_score()
        assert 0 <= score <= 100


# -- Boundary Architect Tests ------------------------------------------------

class TestBoundaryArchitect:
    """Test Boundary Architect."""

    def test_singleton(self):
        from core.boundary_architect import get_boundary_architect
        a1 = get_boundary_architect()
        a2 = get_boundary_architect()
        assert a1 is a2

    def test_record_boundary(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        entry = ba.record_boundary(
            "time",
            "No meetings after 6pm",
            0.9,
            False,
            0.4,
            0.8,
            0.1,
            "protected",
            "Respected",
        )
        assert entry is not None
        assert entry.domain == "time"
        assert entry.outcome == "protected"

    def test_get_boundary_stats(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        stats = ba.get_boundary_stats()
        assert isinstance(stats, dict)

    def test_get_boundary_script(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        script = ba.get_boundary_script("digital", "weekend work messages")
        assert isinstance(script, dict)
        assert "script" in script

    def test_get_boundary_score(self):
        from core.boundary_architect import get_boundary_architect
        ba = get_boundary_architect()
        score = ba.get_boundary_score()
        assert 0 <= score <= 100


# -- Leadership Coach Tests --------------------------------------------------

class TestLeadershipCoach:
    """Test Leadership Coach."""

    def test_singleton(self):
        from core.leadership_coach import get_leadership_coach
        c1 = get_leadership_coach()
        c2 = get_leadership_coach()
        assert c1 is c2

    def test_record_action(self):
        from core.leadership_coach import get_leadership_coach
        lc = get_leadership_coach()
        entry = lc.record_action(
            "Team retrospective",
            "coaching",
            "Engineering",
            5,
            0.8,
            0.9,
            0.85,
            0.9,
            0.95,
            "Great session",
        )
        assert entry is not None
        assert entry.action == "Team retrospective"
        assert entry.team == "Engineering"

    def test_get_leadership_stats(self):
        from core.leadership_coach import get_leadership_coach
        lc = get_leadership_coach()
        stats = lc.get_leadership_stats()
        assert isinstance(stats, dict)

    def test_get_leadership_action(self):
        from core.leadership_coach import get_leadership_coach
        lc = get_leadership_coach()
        action = lc.get_leadership_action("growth", 5)
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_leadership_score(self):
        from core.leadership_coach import get_leadership_coach
        lc = get_leadership_coach()
        score = lc.get_leadership_score()
        assert 0 <= score <= 100


# -- Influence Builder Tests -------------------------------------------------

class TestInfluenceBuilder:
    """Test Influence Builder."""

    def test_singleton(self):
        from core.influence_builder import get_influence_builder
        b1 = get_influence_builder()
        b2 = get_influence_builder()
        assert b1 is b2

    def test_record_attempt(self):
        from core.influence_builder import get_influence_builder
        ib = get_influence_builder()
        entry = ib.record_attempt(
            "Cross-functional team",
            "Adopt new process",
            "rational",
            "collaborative",
            0.7,
            0.8,
            0.9,
            True,
            "Data won the day",
        )
        assert entry is not None
        assert entry.audience == "Cross-functional team"
        assert entry.ethical is True

    def test_get_influence_stats(self):
        from core.influence_builder import get_influence_builder
        ib = get_influence_builder()
        stats = ib.get_influence_stats()
        assert isinstance(stats, dict)

    def test_get_influence_strategy(self):
        from core.influence_builder import get_influence_builder
        ib = get_influence_builder()
        strategy = ib.get_influence_strategy("team", "buy-in", "emotional")
        assert isinstance(strategy, dict)
        assert "strategy" in strategy

    def test_get_influence_score(self):
        from core.influence_builder import get_influence_builder
        ib = get_influence_builder()
        score = ib.get_influence_score()
        assert 0 <= score <= 100


# -- Delegation Trainer Tests ------------------------------------------------

class TestDelegationTrainer:
    """Test Delegation Trainer."""

    def test_singleton(self):
        from core.delegation_trainer import get_delegation_trainer
        t1 = get_delegation_trainer()
        t2 = get_delegation_trainer()
        assert t1 is t2

    def test_record_delegation(self):
        from core.delegation_trainer import get_delegation_trainer
        dt = get_delegation_trainer()
        entry = dt.record_delegation(
            "Q3 report",
            "Alex",
            "task",
            0.9,
            0.8,
            0.7,
            0.95,
            0.8,
            4.5,
            "Excellent result",
        )
        assert entry is not None
        assert entry.task == "Q3 report"
        assert entry.person == "Alex"

    def test_get_delegation_stats(self):
        from core.delegation_trainer import get_delegation_trainer
        dt = get_delegation_trainer()
        stats = dt.get_delegation_stats()
        assert isinstance(stats, dict)

    def test_get_delegation_plan(self):
        from core.delegation_trainer import get_delegation_trainer
        dt = get_delegation_trainer()
        plan = dt.get_delegation_plan("Code review", 0.7)
        assert isinstance(plan, dict)
        assert "plan" in plan

    def test_get_delegation_score(self):
        from core.delegation_trainer import get_delegation_trainer
        dt = get_delegation_trainer()
        score = dt.get_delegation_score()
        assert 0 <= score <= 100


# -- Vision Keeper Tests -----------------------------------------------------

class TestVisionKeeper:
    """Test Vision Keeper."""

    def test_singleton(self):
        from core.vision_keeper import get_vision_keeper
        k1 = get_vision_keeper()
        k2 = get_vision_keeper()
        assert k1 is k2

    def test_record_action(self):
        from core.vision_keeper import get_vision_keeper
        vk = get_vision_keeper()
        entry = vk.record_action(
            "Product roadmap review",
            "team",
            "Be the most trusted platform",
            0.9,
            0.95,
            0.85,
            0.9,
            "Aligned perfectly",
        )
        assert entry is not None
        assert entry.vision_type == "team"
        assert entry.alignment == 0.9

    def test_get_vision_stats(self):
        from core.vision_keeper import get_vision_keeper
        vk = get_vision_keeper()
        stats = vk.get_vision_stats()
        assert isinstance(stats, dict)

    def test_get_vision_practice(self):
        from core.vision_keeper import get_vision_keeper
        vk = get_vision_keeper()
        practice = vk.get_vision_practice("personal", 0.7)
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_vision_score(self):
        from core.vision_keeper import get_vision_keeper
        vk = get_vision_keeper()
        score = vk.get_vision_score()
        assert 0 <= score <= 100


# -- Investment Strategist Tests ---------------------------------------------

class TestInvestmentStrategist:
    """Test Investment Strategist."""

    def test_singleton(self):
        from core.investment_strategist import get_investment_strategist
        s1 = get_investment_strategist()
        s2 = get_investment_strategist()
        assert s1 is s2

    def test_record_decision(self):
        from core.investment_strategist import get_investment_strategist
        ist = get_investment_strategist()
        entry = ist.record_decision(
            "VTI",
            "equity",
            5000,
            "Broad market index",
            0.2,
            0.07,
            0.08,
            365,
            "Good decision",
        )
        assert entry is not None
        assert entry.asset == "VTI"
        assert entry.emotion_level == 0.2

    def test_get_investment_stats(self):
        from core.investment_strategist import get_investment_strategist
        ist = get_investment_strategist()
        stats = ist.get_investment_stats()
        assert isinstance(stats, dict)

    def test_get_portfolio_suggestion(self):
        from core.investment_strategist import get_investment_strategist
        ist = get_investment_strategist()
        suggestion = ist.get_portfolio_suggestion("growth", 20, 0.6)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_investment_score(self):
        from core.investment_strategist import get_investment_strategist
        ist = get_investment_strategist()
        score = ist.get_investment_score()
        assert 0 <= score <= 100


# -- Wealth Builder Tests ----------------------------------------------------

class TestWealthBuilder:
    """Test Wealth Builder."""

    def test_singleton(self):
        from core.wealth_builder import get_wealth_builder
        b1 = get_wealth_builder()
        b2 = get_wealth_builder()
        assert b1 is b2

    def test_record_action(self):
        from core.wealth_builder import get_wealth_builder
        wb = get_wealth_builder()
        entry = wb.record_action(
            "Automated savings",
            "savings",
            2000,
            8000,
            0.25,
            0.02,
            False,
            "Consistent",
        )
        assert entry is not None
        assert entry.action == "Automated savings"
        assert entry.savings_rate == 0.25

    def test_get_wealth_stats(self):
        from core.wealth_builder import get_wealth_builder
        wb = get_wealth_builder()
        stats = wb.get_wealth_stats()
        assert isinstance(stats, dict)

    def test_get_wealth_action(self):
        from core.wealth_builder import get_wealth_builder
        wb = get_wealth_builder()
        action = wb.get_wealth_action("growth", 8000, 0.25)
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_wealth_score(self):
        from core.wealth_builder import get_wealth_builder
        wb = get_wealth_builder()
        score = wb.get_wealth_score()
        assert 0 <= score <= 100


# -- Income Diversifier Tests ------------------------------------------------

class TestIncomeDiversifier:
    """Test Income Diversifier."""

    def test_singleton(self):
        from core.income_diversifier import get_income_diversifier
        d1 = get_income_diversifier()
        d2 = get_income_diversifier()
        assert d1 is d2

    def test_record_source(self):
        from core.income_diversifier import get_income_diversifier
        idiv = get_income_diversifier()
        entry = idiv.record_source(
            "Consulting",
            "business",
            2000,
            0.7,
            0.6,
            0.8,
            "Growing well",
        )
        assert entry is not None
        assert entry.source == "Consulting"
        assert entry.income_type == "business"

    def test_get_income_stats(self):
        from core.income_diversifier import get_income_diversifier
        idiv = get_income_diversifier()
        stats = idiv.get_income_stats()
        assert isinstance(stats, dict)

    def test_get_diversification_suggestion(self):
        from core.income_diversifier import get_income_diversifier
        idiv = get_income_diversifier()
        suggestion = idiv.get_diversification_suggestion("skill_based", 0.6, 0.5)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_income_score(self):
        from core.income_diversifier import get_income_diversifier
        idiv = get_income_diversifier()
        score = idiv.get_income_score()
        assert 0 <= score <= 100


# -- Financial Independence Tracker Tests ------------------------------------

class TestFinancialIndependenceTracker:
    """Test Financial Independence Tracker."""

    def test_singleton(self):
        from core.financial_independence_tracker import get_financial_independence_tracker
        t1 = get_financial_independence_tracker()
        t2 = get_financial_independence_tracker()
        assert t1 is t2

    def test_record_snapshot(self):
        from core.financial_independence_tracker import get_financial_independence_tracker
        fit = get_financial_independence_tracker()
        entry = fit.record_snapshot(
            500000,
            4000,
            10000,
            1200000,
            0.42,
            "regular",
            "accumulation",
            8.5,
            0.4,
            "On track",
        )
        assert entry is not None
        assert entry.fi_progress == 0.42
        assert entry.stage == "accumulation"

    def test_get_fi_stats(self):
        from core.financial_independence_tracker import get_financial_independence_tracker
        fit = get_financial_independence_tracker()
        stats = fit.get_fi_stats()
        assert isinstance(stats, dict)

    def test_get_fi_action(self):
        from core.financial_independence_tracker import get_financial_independence_tracker
        fit = get_financial_independence_tracker()
        action = fit.get_fi_action("accumulation", 10, 0.5)
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_fi_score(self):
        from core.financial_independence_tracker import get_financial_independence_tracker
        fit = get_financial_independence_tracker()
        score = fit.get_fi_score()
        assert 0 <= score <= 100


# -- Sustainability Coach Tests ----------------------------------------------

class TestSustainabilityCoach:
    """Test Sustainability Coach."""

    def test_singleton(self):
        from core.sustainability_coach import get_sustainability_coach
        c1 = get_sustainability_coach()
        c2 = get_sustainability_coach()
        assert c1 is c2

    def test_record_action(self):
        from core.sustainability_coach import get_sustainability_coach
        sc = get_sustainability_coach()
        entry = sc.record_action(
            "Installed LED bulbs",
            "energy",
            50.0,
            0.3,
            0.9,
            True,
            "Easy win",
        )
        assert entry is not None
        assert entry.action == "Installed LED bulbs"
        assert entry.domain == "energy"

    def test_get_sustainability_stats(self):
        from core.sustainability_coach import get_sustainability_coach
        sc = get_sustainability_coach()
        stats = sc.get_sustainability_stats()
        assert isinstance(stats, dict)

    def test_get_sustainability_action(self):
        from core.sustainability_coach import get_sustainability_coach
        sc = get_sustainability_coach()
        action = sc.get_sustainability_action("transport", 0.6)
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_sustainability_score(self):
        from core.sustainability_coach import get_sustainability_coach
        sc = get_sustainability_coach()
        score = sc.get_sustainability_score()
        assert 0 <= score <= 100


# -- Nature Connector Tests --------------------------------------------------

class TestNatureConnector:
    """Test Nature Connector."""

    def test_singleton(self):
        from core.nature_connector import get_nature_connector
        n1 = get_nature_connector()
        n2 = get_nature_connector()
        assert n1 is n2

    def test_record_interaction(self):
        from core.nature_connector import get_nature_connector
        nc = get_nature_connector()
        entry = nc.record_interaction(
            "forest",
            "walking",
            45.0,
            0.5,
            0.9,
            True,
            "summer",
            "Peaceful",
        )
        assert entry is not None
        assert entry.environment == "forest"
        assert entry.awe_experienced is True

    def test_get_nature_stats(self):
        from core.nature_connector import get_nature_connector
        nc = get_nature_connector()
        stats = nc.get_nature_stats()
        assert isinstance(stats, dict)

    def test_get_nature_suggestion(self):
        from core.nature_connector import get_nature_connector
        nc = get_nature_connector()
        suggestion = nc.get_nature_suggestion("urban", 0.5, "spring")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_nature_score(self):
        from core.nature_connector import get_nature_connector
        nc = get_nature_connector()
        score = nc.get_nature_score()
        assert 0 <= score <= 100


# -- Eco Footprint Tracker Tests ---------------------------------------------

class TestEcoFootprintTracker:
    """Test Eco Footprint Tracker."""

    def test_singleton(self):
        from core.eco_footprint_tracker import get_eco_footprint_tracker
        t1 = get_eco_footprint_tracker()
        t2 = get_eco_footprint_tracker()
        assert t1 is t2

    def test_record_measurement(self):
        from core.eco_footprint_tracker import get_eco_footprint_tracker
        eft = get_eco_footprint_tracker()
        entry = eft.record_measurement(
            "transport",
            1200.0,
            "kg CO2",
            200.0,
            "Started biking",
            1600.0,
            "Making progress",
        )
        assert entry is not None
        assert entry.category == "transport"
        assert entry.reduction == 200.0

    def test_get_footprint_stats(self):
        from core.eco_footprint_tracker import get_eco_footprint_tracker
        eft = get_eco_footprint_tracker()
        stats = eft.get_footprint_stats()
        assert isinstance(stats, dict)

    def test_get_reduction_strategy(self):
        from core.eco_footprint_tracker import get_eco_footprint_tracker
        eft = get_eco_footprint_tracker()
        strategy = eft.get_reduction_strategy("home", 800, 600)
        assert isinstance(strategy, dict)
        assert "strategy" in strategy

    def test_get_footprint_score(self):
        from core.eco_footprint_tracker import get_eco_footprint_tracker
        eft = get_eco_footprint_tracker()
        score = eft.get_footprint_score()
        assert 0 <= score <= 100


# -- Regenerative Living Guide Tests -----------------------------------------

class TestRegenerativeLivingGuide:
    """Test Regenerative Living Guide."""

    def test_singleton(self):
        from core.regenerative_living_guide import get_regenerative_living_guide
        g1 = get_regenerative_living_guide()
        g2 = get_regenerative_living_guide()
        assert g1 is g2

    def test_record_action(self):
        from core.regenerative_living_guide import get_regenerative_living_guide
        rlg = get_regenerative_living_guide()
        entry = rlg.record_action(
            "Planted pollinator garden",
            "biodiversity",
            100.0,
            True,
            0.8,
            0.7,
            "Neighbors joined",
        )
        assert entry is not None
        assert entry.action == "Planted pollinator garden"
        assert entry.net_positive is True

    def test_get_regenerative_stats(self):
        from core.regenerative_living_guide import get_regenerative_living_guide
        rlg = get_regenerative_living_guide()
        stats = rlg.get_regenerative_stats()
        assert isinstance(stats, dict)

    def test_get_regenerative_action(self):
        from core.regenerative_living_guide import get_regenerative_living_guide
        rlg = get_regenerative_living_guide()
        action = rlg.get_regenerative_action(0.7, "soil")
        assert isinstance(action, dict)
        assert "action" in action

    def test_get_regenerative_score(self):
        from core.regenerative_living_guide import get_regenerative_living_guide
        rlg = get_regenerative_living_guide()
        score = rlg.get_regenerative_score()
        assert 0 <= score <= 100


# -- Spiritual Practice Coach Tests ------------------------------------------

class TestSpiritualPracticeCoach:
    """Test Spiritual Practice Coach."""

    def test_singleton(self):
        from core.spiritual_practice_coach import get_spiritual_practice_coach
        c1 = get_spiritual_practice_coach()
        c2 = get_spiritual_practice_coach()
        assert c1 is c2

    def test_record_practice(self):
        from core.spiritual_practice_coach import get_spiritual_practice_coach
        spc = get_spiritual_practice_coach()
        entry = spc.record_practice(
            "Centering prayer",
            "prayer",
            20,
            0.8,
            0.7,
            0.9,
            False,
            "Deep connection",
        )
        assert entry is not None
        assert entry.practice == "Centering prayer"
        assert entry.bypassing is False

    def test_get_spiritual_stats(self):
        from core.spiritual_practice_coach import get_spiritual_practice_coach
        spc = get_spiritual_practice_coach()
        stats = spc.get_spiritual_stats()
        assert isinstance(stats, dict)

    def test_get_practice_suggestion(self):
        from core.spiritual_practice_coach import get_spiritual_practice_coach
        spc = get_spiritual_practice_coach()
        suggestion = spc.get_practice_suggestion("peace", 0.6)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_spiritual_score(self):
        from core.spiritual_practice_coach import get_spiritual_practice_coach
        spc = get_spiritual_practice_coach()
        score = spc.get_spiritual_score()
        assert 0 <= score <= 100


# -- Transcendence Guide Tests -----------------------------------------------

class TestTranscendenceGuide:
    """Test Transcendence Guide."""

    def test_singleton(self):
        from core.transcendence_guide import get_transcendence_guide
        g1 = get_transcendence_guide()
        g2 = get_transcendence_guide()
        assert g1 is g2

    def test_record_experience(self):
        from core.transcendence_guide import get_transcendence_guide
        tg = get_transcendence_guide()
        entry = tg.record_experience(
            "Meditation retreat",
            "unity",
            0.9,
            120,
            0.8,
            0.7,
            False,
            "Profound",
        )
        assert entry is not None
        assert entry.trigger == "Meditation retreat"
        assert entry.chasing is False

    def test_get_transcendence_stats(self):
        from core.transcendence_guide import get_transcendence_guide
        tg = get_transcendence_guide()
        stats = tg.get_transcendence_stats()
        assert isinstance(stats, dict)

    def test_get_transcendence_practice(self):
        from core.transcendence_guide import get_transcendence_guide
        tg = get_transcendence_guide()
        practice = tg.get_transcendence_practice("unity", 0.7)
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_transcendence_score(self):
        from core.transcendence_guide import get_transcendence_guide
        tg = get_transcendence_guide()
        score = tg.get_transcendence_score()
        assert 0 <= score <= 100


# -- Sacred Ritual Designer Tests --------------------------------------------

class TestSacredRitualDesigner:
    """Test Sacred Ritual Designer."""

    def test_singleton(self):
        from core.sacred_ritual_designer import get_sacred_ritual_designer
        d1 = get_sacred_ritual_designer()
        d2 = get_sacred_ritual_designer()
        assert d1 is d2

    def test_record_ritual(self):
        from core.sacred_ritual_designer import get_sacred_ritual_designer
        srd = get_sacred_ritual_designer()
        entry = srd.record_ritual(
            "Morning gratitude",
            "daily",
            3,
            0.9,
            0.9,
            0.8,
            False,
            1,
            "Powerful",
        )
        assert entry is not None
        assert entry.name == "Morning gratitude"
        assert entry.rote is False

    def test_get_ritual_stats(self):
        from core.sacred_ritual_designer import get_sacred_ritual_designer
        srd = get_sacred_ritual_designer()
        stats = srd.get_ritual_stats()
        assert isinstance(stats, dict)

    def test_get_ritual_design(self):
        from core.sacred_ritual_designer import get_sacred_ritual_designer
        srd = get_sacred_ritual_designer()
        design = srd.get_ritual_design("morning", 1, "intention setting")
        assert isinstance(design, dict)
        assert "design" in design

    def test_get_ritual_score(self):
        from core.sacred_ritual_designer import get_sacred_ritual_designer
        srd = get_sacred_ritual_designer()
        score = srd.get_ritual_score()
        assert 0 <= score <= 100


# -- Contemplation Keeper Tests ----------------------------------------------

class TestContemplationKeeper:
    """Test Contemplation Keeper."""

    def test_singleton(self):
        from core.contemplation_keeper import get_contemplation_keeper
        k1 = get_contemplation_keeper()
        k2 = get_contemplation_keeper()
        assert k1 is k2

    def test_record_session(self):
        from core.contemplation_keeper import get_contemplation_keeper
        ck = get_contemplation_keeper()
        entry = ck.record_session(
            "Journal on career change",
            "journaling",
            30,
            0.8,
            0.9,
            0.7,
            "What do I truly want?",
            False,
            "Breakthrough insight",
        )
        assert entry is not None
        assert entry.practice == "Journal on career change"
        assert entry.performative is False

    def test_get_contemplation_stats(self):
        from core.contemplation_keeper import get_contemplation_keeper
        ck = get_contemplation_keeper()
        stats = ck.get_contemplation_stats()
        assert isinstance(stats, dict)

    def test_get_contemplation_practice(self):
        from core.contemplation_keeper import get_contemplation_keeper
        ck = get_contemplation_keeper()
        practice = ck.get_contemplation_practice("What next?", 0.6, "decision")
        assert isinstance(practice, dict)
        assert "practice" in practice

    def test_get_contemplation_score(self):
        from core.contemplation_keeper import get_contemplation_keeper
        ck = get_contemplation_keeper()
        score = ck.get_contemplation_score()
        assert 0 <= score <= 100


# -- Experience Maximizer Tests ---------------------------------------------------

class TestExperienceMaximizer:
    """Test Experience Maximizer."""

    def test_singleton(self):
        from core.experience_maximizer import get_experience_maximizer
        e1 = get_experience_maximizer()
        e2 = get_experience_maximizer()
        assert e1 is e2

    def test_record_experience(self):
        from core.experience_maximizer import get_experience_maximizer
        em = get_experience_maximizer()
        entry = em.record_experience(
            "Concert",
            0.9,
            0.8,
            0.7,
            120,
            0.85,
            0.6,
            0.1,
            "Live music breakthrough",
        )
        assert entry is not None
        assert entry.activity == "Concert"
        assert entry.depth == 0.9

    def test_get_experience_stats(self):
        from core.experience_maximizer import get_experience_maximizer
        em = get_experience_maximizer()
        stats = em.get_experience_stats()
        assert isinstance(stats, dict)

    def test_get_depth_suggestion(self):
        from core.experience_maximizer import get_experience_maximizer
        em = get_experience_maximizer()
        suggestion = em.get_depth_suggestion("meal", "dinner")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_depth_score(self):
        from core.experience_maximizer import get_experience_maximizer
        em = get_experience_maximizer()
        score = em.get_depth_score()
        assert 0 <= score <= 100


# -- Wonder Cultivator Tests ---------------------------------------------------

class TestWonderCultivator:
    """Test Wonder Cultivator."""

    def test_singleton(self):
        from core.wonder_cultivator import get_wonder_cultivator
        w1 = get_wonder_cultivator()
        w2 = get_wonder_cultivator()
        assert w1 is w2

    def test_record_wonder(self):
        from core.wonder_cultivator import get_wonder_cultivator
        wc = get_wonder_cultivator()
        entry = wc.record_wonder(
            "Grand canyon sunrise",
            "vastness",
            0.95,
            0.9,
            0.85,
            30,
            0.9,
            "Overwhelming beauty",
        )
        assert entry is not None
        assert entry.moment == "Grand canyon sunrise"
        assert entry.intensity == 0.95

    def test_get_wonder_stats(self):
        from core.wonder_cultivator import get_wonder_cultivator
        wc = get_wonder_cultivator()
        stats = wc.get_wonder_stats()
        assert isinstance(stats, dict)

    def test_get_wonder_suggestion(self):
        from core.wonder_cultivator import get_wonder_cultivator
        wc = get_wonder_cultivator()
        suggestion = wc.get_wonder_suggestion("nature", 0.7)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_wonder_score(self):
        from core.wonder_cultivator import get_wonder_cultivator
        wc = get_wonder_cultivator()
        score = wc.get_wonder_score()
        assert 0 <= score <= 100


# -- Travel Optimizer Tests ---------------------------------------------------

class TestTravelOptimizer:
    """Test Travel Optimizer."""

    def test_singleton(self):
        from core.travel_optimizer import get_travel_optimizer
        t1 = get_travel_optimizer()
        t2 = get_travel_optimizer()
        assert t1 is t2

    def test_record_trip(self):
        from core.travel_optimizer import get_travel_optimizer
        to = get_travel_optimizer()
        entry = to.record_trip(
            "Kyoto, Japan",
            "international",
            14,
            0.9,
            0.7,
            0.8,
            0.9,
            0.6,
            0.85,
            0.7,
            "Temples and tea",
        )
        assert entry is not None
        assert entry.destination == "Kyoto, Japan"
        assert entry.trip_type == "international"

    def test_get_travel_stats(self):
        from core.travel_optimizer import get_travel_optimizer
        to = get_travel_optimizer()
        stats = to.get_travel_stats()
        assert isinstance(stats, dict)

    def test_get_trip_suggestion(self):
        from core.travel_optimizer import get_travel_optimizer
        to = get_travel_optimizer()
        suggestion = to.get_trip_suggestion("perspective", 0.7, "burnout")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_travel_score(self):
        from core.travel_optimizer import get_travel_optimizer
        to = get_travel_optimizer()
        score = to.get_travel_score()
        assert 0 <= score <= 100


# -- Community Builder Tests ---------------------------------------------------

class TestCommunityBuilder:
    """Test Community Builder."""

    def test_singleton(self):
        from core.community_builder import get_community_builder
        c1 = get_community_builder()
        c2 = get_community_builder()
        assert c1 is c2

    def test_record_interaction(self):
        from core.community_builder import get_community_builder
        cb = get_community_builder()
        entry = cb.record_interaction(
            "Book club",
            "gathering",
            0.8,
            0.7,
            0.6,
            0.5,
            True,
            120,
            "Great discussion",
        )
        assert entry is not None
        assert entry.community == "Book club"
        assert entry.belonging == 0.8

    def test_get_community_stats(self):
        from core.community_builder import get_community_builder
        cb = get_community_builder()
        stats = cb.get_community_stats()
        assert isinstance(stats, dict)

    def test_get_building_suggestion(self):
        from core.community_builder import get_community_builder
        cb = get_community_builder()
        suggestion = cb.get_building_suggestion(0.7, "lonely")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_community_score(self):
        from core.community_builder import get_community_builder
        cb = get_community_builder()
        score = cb.get_community_score()
        assert 0 <= score <= 100


# -- Social Impact Tracker Tests ---------------------------------------------------

class TestSocialImpactTracker:
    """Test Social Impact Tracker."""

    def test_singleton(self):
        from core.social_impact_tracker import get_social_impact_tracker
        s1 = get_social_impact_tracker()
        s2 = get_social_impact_tracker()
        assert s1 is s2

    def test_record_impact(self):
        from core.social_impact_tracker import get_social_impact_tracker
        sit = get_social_impact_tracker()
        entry = sit.record_impact(
            "Tutored student",
            "education",
            0.3,
            0.9,
            0.8,
            0.95,
            0.7,
            0.4,
            "Long-term mentoring",
        )
        assert entry is not None
        assert entry.action == "Tutored student"
        assert entry.depth == 0.9

    def test_get_impact_stats(self):
        from core.social_impact_tracker import get_social_impact_tracker
        sit = get_social_impact_tracker()
        stats = sit.get_impact_stats()
        assert isinstance(stats, dict)

    def test_get_impact_suggestion(self):
        from core.social_impact_tracker import get_social_impact_tracker
        sit = get_social_impact_tracker()
        suggestion = sit.get_impact_suggestion(0.6, "burnout")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_impact_score(self):
        from core.social_impact_tracker import get_social_impact_tracker
        sit = get_social_impact_tracker()
        score = sit.get_impact_score()
        assert 0 <= score <= 100


# -- Volunteer Coordinator Tests ---------------------------------------------------

class TestVolunteerCoordinator:
    """Test Volunteer Coordinator."""

    def test_singleton(self):
        from core.volunteer_coordinator import get_volunteer_coordinator
        v1 = get_volunteer_coordinator()
        v2 = get_volunteer_coordinator()
        assert v1 is v2

    def test_record_activity(self):
        from core.volunteer_coordinator import get_volunteer_coordinator
        vc = get_volunteer_coordinator()
        entry = vc.record_activity(
            "Food bank sorting",
            "direct_service",
            4,
            0.85,
            0.7,
            0.9,
            0.8,
            0.2,
            "Fulfilling morning",
        )
        assert entry is not None
        assert entry.activity == "Food bank sorting"
        assert entry.hours == 4

    def test_get_volunteer_stats(self):
        from core.volunteer_coordinator import get_volunteer_coordinator
        vc = get_volunteer_coordinator()
        stats = vc.get_volunteer_stats()
        assert isinstance(stats, dict)

    def test_get_opportunity_suggestion(self):
        from core.volunteer_coordinator import get_volunteer_coordinator
        vc = get_volunteer_coordinator()
        suggestion = vc.get_opportunity_suggestion("teaching", 0.7)
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_volunteer_score(self):
        from core.volunteer_coordinator import get_volunteer_coordinator
        vc = get_volunteer_coordinator()
        score = vc.get_volunteer_score()
        assert 0 <= score <= 100


# -- Network Weaver Tests ---------------------------------------------------

class TestNetworkWeaver:
    """Test Network Weaver."""

    def test_singleton(self):
        from core.network_weaver import get_network_weaver
        n1 = get_network_weaver()
        n2 = get_network_weaver()
        assert n1 is n2

    def test_record_interaction(self):
        from core.network_weaver import get_network_weaver
        nw = get_network_weaver()
        entry = nw.record_interaction(
            "Sarah Chen",
            "deep",
            0.9,
            0.8,
            0.7,
            0.85,
            "work",
            True,
            "Great sync",
        )
        assert entry is not None
        assert entry.contact == "Sarah Chen"
        assert entry.quality == 0.9

    def test_get_network_stats(self):
        from core.network_weaver import get_network_weaver
        nw = get_network_weaver()
        stats = nw.get_network_stats()
        assert isinstance(stats, dict)

    def test_get_weaving_suggestion(self):
        from core.network_weaver import get_network_weaver
        nw = get_network_weaver()
        suggestion = nw.get_weaving_suggestion(0.6, "remote")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_network_score(self):
        from core.network_weaver import get_network_weaver
        nw = get_network_weaver()
        score = nw.get_network_score()
        assert 0 <= score <= 100


# -- Longevity Optimizer Tests ---------------------------------------------------

class TestLongevityOptimizer:
    """Test Longevity Optimizer."""

    def test_singleton(self):
        from core.longevity_optimizer import get_longevity_optimizer
        l1 = get_longevity_optimizer()
        l2 = get_longevity_optimizer()
        assert l1 is l2

    def test_record_practice(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        entry = lo.record_practice(
            "Morning walk",
            "movement",
            0.6,
            0.7,
            0.6,
            0.5,
            0.9,
            "Daily habit",
        )
        assert entry is not None
        assert entry.practice == "Morning walk"
        assert entry.practice_type == "movement"

    def test_get_longevity_stats(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        stats = lo.get_longevity_stats()
        assert isinstance(stats, dict)

    def test_get_practice_suggestion(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        suggestion = lo.get_practice_suggestion(45, 0.7, "fatigue")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_longevity_score(self):
        from core.longevity_optimizer import get_longevity_optimizer
        lo = get_longevity_optimizer()
        score = lo.get_longevity_score()
        assert 0 <= score <= 100


# -- Vitality Tracker Tests ---------------------------------------------------

class TestVitalityTracker:
    """Test Vitality Tracker."""

    def test_singleton(self):
        from core.vitality_tracker import get_vitality_tracker
        v1 = get_vitality_tracker()
        v2 = get_vitality_tracker()
        assert v1 is v2

    def test_record_vitality(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        entry = vt.record_vitality(
            0.8,
            0.9,
            0.7,
            0.8,
            0.85,
            0.9,
            0.7,
            0.8,
            0.9,
            0.2,
            5,
            "Great day",
        )
        assert entry is not None
        assert entry.vitality == 0.8
        assert entry.peak_hours == 5

    def test_get_vitality_stats(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        stats = vt.get_vitality_stats()
        assert isinstance(stats, dict)

    def test_get_vitality_suggestion(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        suggestion = vt.get_vitality_suggestion("depleted", "burnout")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_vitality_score(self):
        from core.vitality_tracker import get_vitality_tracker
        vt = get_vitality_tracker()
        score = vt.get_vitality_score()
        assert 0 <= score <= 100


# -- Age Reversal Coach Tests ---------------------------------------------------

class TestAgeReversalCoach:
    """Test Age Reversal Coach."""

    def test_singleton(self):
        from core.age_reversal_coach import get_age_reversal_coach
        a1 = get_age_reversal_coach()
        a2 = get_age_reversal_coach()
        assert a1 is a2

    def test_record_practice(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        entry = arc.record_practice(
            "Cold shower finish",
            "cold",
            0.6,
            0.7,
            0.6,
            0.5,
            0.8,
            "Energizing",
        )
        assert entry is not None
        assert entry.practice == "Cold shower finish"
        assert entry.practice_type == "cold"

    def test_get_reversal_stats(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        stats = arc.get_reversal_stats()
        assert isinstance(stats, dict)

    def test_get_practice_suggestion(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        suggestion = arc.get_practice_suggestion(50, 0.6, "stiffness")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_reversal_score(self):
        from core.age_reversal_coach import get_age_reversal_coach
        arc = get_age_reversal_coach()
        score = arc.get_reversal_score()
        assert 0 <= score <= 100


# -- Life Phase Navigator Tests ---------------------------------------------------

class TestLifePhaseNavigator:
    """Test Life Phase Navigator."""

    def test_singleton(self):
        from core.life_phase_navigator import get_life_phase_navigator
        l1 = get_life_phase_navigator()
        l2 = get_life_phase_navigator()
        assert l1 is l2

    def test_record_phase(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        entry = lpn.record_phase(
            "Senior developer role",
            "career",
            0.7,
            0.5,
            0.3,
            36,
            0.8,
            0.4,
            "Comfortable but plateauing",
        )
        assert entry is not None
        assert entry.phase == "Senior developer role"
        assert entry.phase_type == "career"

    def test_get_phase_stats(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        stats = lpn.get_phase_stats()
        assert isinstance(stats, dict)

    def test_get_transition_suggestion(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        suggestion = lpn.get_transition_suggestion("career", 0.7, "restless")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_phase_score(self):
        from core.life_phase_navigator import get_life_phase_navigator
        lpn = get_life_phase_navigator()
        score = lpn.get_phase_score()
        assert 0 <= score <= 100


# -- Parenting Coach Tests ---------------------------------------------------

class TestParentingCoach:
    """Test Parenting Coach."""

    def test_singleton(self):
        from core.parenting_coach import get_parenting_coach
        p1 = get_parenting_coach()
        p2 = get_parenting_coach()
        assert p1 is p2

    def test_record_interaction(self):
        from core.parenting_coach import get_parenting_coach
        pc = get_parenting_coach()
        entry = pc.record_interaction(
            "Emma",
            "play",
            0.9,
            0.8,
            0.9,
            0.5,
            0.3,
            0.9,
            "Wonderful afternoon",
        )
        assert entry is not None
        assert entry.child == "Emma"
        assert entry.interaction_type == "play"

    def test_get_parenting_stats(self):
        from core.parenting_coach import get_parenting_coach
        pc = get_parenting_coach()
        stats = pc.get_parenting_stats()
        assert isinstance(stats, dict)

    def test_get_parenting_suggestion(self):
        from core.parenting_coach import get_parenting_coach
        pc = get_parenting_coach()
        suggestion = pc.get_parenting_suggestion(8, 0.7, "tantrum")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_parenting_score(self):
        from core.parenting_coach import get_parenting_coach
        pc = get_parenting_coach()
        score = pc.get_parenting_score()
        assert 0 <= score <= 100


# -- Family Harmony Builder Tests ---------------------------------------------------

class TestFamilyHarmonyBuilder:
    """Test Family Harmony Builder."""

    def test_singleton(self):
        from core.family_harmony_builder import get_family_harmony_builder
        f1 = get_family_harmony_builder()
        f2 = get_family_harmony_builder()
        assert f1 is f2

    def test_record_interaction(self):
        from core.family_harmony_builder import get_family_harmony_builder
        fhb = get_family_harmony_builder()
        entry = fhb.record_interaction(
            "Dad",
            "meal",
            0.8,
            0.7,
            0.6,
            0.0,
            0.5,
            "Sunday dinner",
        )
        assert entry is not None
        assert entry.member == "Dad"
        assert entry.interaction_type == "meal"

    def test_get_family_stats(self):
        from core.family_harmony_builder import get_family_harmony_builder
        fhb = get_family_harmony_builder()
        stats = fhb.get_family_stats()
        assert isinstance(stats, dict)

    def test_get_harmony_suggestion(self):
        from core.family_harmony_builder import get_family_harmony_builder
        fhb = get_family_harmony_builder()
        suggestion = fhb.get_harmony_suggestion(0.6, "tension")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_family_score(self):
        from core.family_harmony_builder import get_family_harmony_builder
        fhb = get_family_harmony_builder()
        score = fhb.get_family_score()
        assert 0 <= score <= 100


# -- Grief Support Companion Tests ---------------------------------------------------

class TestGriefSupportCompanion:
    """Test Grief Support Companion."""

    def test_singleton(self):
        from core.grief_support_companion import get_grief_support_companion
        g1 = get_grief_support_companion()
        g2 = get_grief_support_companion()
        assert g1 is g2

    def test_record_grief(self):
        from core.grief_support_companion import get_grief_support_companion
        gsc = get_grief_support_companion()
        entry = gsc.record_grief(
            "Missed Mom terribly today",
            "acute",
            0.9,
            0.6,
            0.7,
            0.3,
            0.5,
            "Anniversary of loss",
        )
        assert entry is not None
        assert entry.experience == "Missed Mom terribly today"
        assert entry.grief_type == "acute"

    def test_get_grief_stats(self):
        from core.grief_support_companion import get_grief_support_companion
        gsc = get_grief_support_companion()
        stats = gsc.get_grief_stats()
        assert isinstance(stats, dict)

    def test_get_support_suggestion(self):
        from core.grief_support_companion import get_grief_support_companion
        gsc = get_grief_support_companion()
        suggestion = gsc.get_support_suggestion("acute", 0.4, "overwhelmed")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_grief_score(self):
        from core.grief_support_companion import get_grief_support_companion
        gsc = get_grief_support_companion()
        score = gsc.get_grief_score()
        assert 0 <= score <= 100


# -- Humor Cultivator Tests ---------------------------------------------------

class TestHumorCultivator:
    """Test Humor Cultivator."""

    def test_singleton(self):
        from core.humor_cultivator import get_humor_cultivator
        h1 = get_humor_cultivator()
        h2 = get_humor_cultivator()
        assert h1 is h2

    def test_record_laughter(self):
        from core.humor_cultivator import get_humor_cultivator
        hc = get_humor_cultivator()
        entry = hc.record_laughter(
            "Cat fell off couch",
            "absurdity",
            0.9,
            0.8,
            0.7,
            0.4,
            5,
            "Could not stop laughing",
        )
        assert entry is not None
        assert entry.moment == "Cat fell off couch"
        assert entry.humor_type == "absurdity"

    def test_get_humor_stats(self):
        from core.humor_cultivator import get_humor_cultivator
        hc = get_humor_cultivator()
        stats = hc.get_humor_stats()
        assert isinstance(stats, dict)

    def test_get_humor_suggestion(self):
        from core.humor_cultivator import get_humor_cultivator
        hc = get_humor_cultivator()
        suggestion = hc.get_humor_suggestion(0.6, "stressed")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_humor_score(self):
        from core.humor_cultivator import get_humor_cultivator
        hc = get_humor_cultivator()
        score = hc.get_humor_score()
        assert 0 <= score <= 100


# -- Civic Engagement Tracker Tests ---------------------------------------------------

class TestCivicEngagementTracker:
    """Test Civic Engagement Tracker."""

    def test_singleton(self):
        from core.civic_engagement_tracker import get_civic_engagement_tracker
        c1 = get_civic_engagement_tracker()
        c2 = get_civic_engagement_tracker()
        assert c1 is c2

    def test_record_activity(self):
        from core.civic_engagement_tracker import get_civic_engagement_tracker
        cet = get_civic_engagement_tracker()
        entry = cet.record_activity(
            "Voted in local election",
            "voting",
            0.8,
            0.6,
            0.5,
            0.7,
            0.9,
            1.0,
            "Felt empowered",
        )
        assert entry is not None
        assert entry.activity == "Voted in local election"
        assert entry.activity_type == "voting"

    def test_get_civic_stats(self):
        from core.civic_engagement_tracker import get_civic_engagement_tracker
        cet = get_civic_engagement_tracker()
        stats = cet.get_civic_stats()
        assert isinstance(stats, dict)

    def test_get_engagement_suggestion(self):
        from core.civic_engagement_tracker import get_civic_engagement_tracker
        cet = get_civic_engagement_tracker()
        suggestion = cet.get_engagement_suggestion(0.6, "advocacy")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_civic_score(self):
        from core.civic_engagement_tracker import get_civic_engagement_tracker
        cet = get_civic_engagement_tracker()
        score = cet.get_civic_score()
        assert 0 <= score <= 100


# -- Mentorship Weaver Tests ---------------------------------------------------

class TestMentorshipWeaver:
    """Test Mentorship Weaver."""

    def test_singleton(self):
        from core.mentorship_weaver import get_mentorship_weaver
        m1 = get_mentorship_weaver()
        m2 = get_mentorship_weaver()
        assert m1 is m2

    def test_record_interaction(self):
        from core.mentorship_weaver import get_mentorship_weaver
        mw = get_mentorship_weaver()
        entry = mw.record_interaction(
            "mentor",
            "Alex",
            "informal",
            0.8,
            0.7,
            0.9,
            0.6,
            45,
            "Great conversation about career",
        )
        assert entry is not None
        assert entry.role == "mentor"
        assert entry.person == "Alex"

    def test_get_mentorship_stats(self):
        from core.mentorship_weaver import get_mentorship_weaver
        mw = get_mentorship_weaver()
        stats = mw.get_mentorship_stats()
        assert isinstance(stats, dict)

    def test_get_mentorship_suggestion(self):
        from core.mentorship_weaver import get_mentorship_weaver
        mw = get_mentorship_weaver()
        suggestion = mw.get_mentorship_suggestion(0.7, "seeking")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_mentorship_score(self):
        from core.mentorship_weaver import get_mentorship_weaver
        mw = get_mentorship_weaver()
        score = mw.get_mentorship_score()
        assert 0 <= score <= 100


# -- Wisdom Keeper Tests ---------------------------------------------------

class TestWisdomKeeper:
    """Test Wisdom Keeper."""

    def test_singleton(self):
        from core.wisdom_keeper import get_wisdom_keeper
        w1 = get_wisdom_keeper()
        w2 = get_wisdom_keeper()
        assert w1 is w2

    def test_record_insight(self):
        from core.wisdom_keeper import get_wisdom_keeper
        wk = get_wisdom_keeper()
        entry = wk.record_insight(
            "Failure teaches more than success",
            "practical",
            0.8,
            0.9,
            0.6,
            "recent_job_loss",
            "Key realization after layoff",
        )
        assert entry is not None
        assert entry.insight == "Failure teaches more than success"
        assert entry.insight_type == "practical"

    def test_get_wisdom_stats(self):
        from core.wisdom_keeper import get_wisdom_keeper
        wk = get_wisdom_keeper()
        stats = wk.get_wisdom_stats()
        assert isinstance(stats, dict)

    def test_get_wisdom_suggestion(self):
        from core.wisdom_keeper import get_wisdom_keeper
        wk = get_wisdom_keeper()
        suggestion = wk.get_wisdom_suggestion(0.6, "integration")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_wisdom_score(self):
        from core.wisdom_keeper import get_wisdom_keeper
        wk = get_wisdom_keeper()
        score = wk.get_wisdom_score()
        assert 0 <= score <= 100


# -- Play Architect Tests ---------------------------------------------------

class TestPlayArchitect:
    """Test Play Architect."""

    def test_singleton(self):
        from core.play_architect import get_play_architect
        p1 = get_play_architect()
        p2 = get_play_architect()
        assert p1 is p2

    def test_record_play(self):
        from core.play_architect import get_play_architect
        pa = get_play_architect()
        entry = pa.record_play(
            "Frisbee in park",
            "physical",
            0.9,
            0.8,
            0.9,
            0.7,
            0.6,
            60,
            "Best part of the week",
        )
        assert entry is not None
        assert entry.activity == "Frisbee in park"
        assert entry.play_type == "physical"

    def test_get_play_stats(self):
        from core.play_architect import get_play_architect
        pa = get_play_architect()
        stats = pa.get_play_stats()
        assert isinstance(stats, dict)

    def test_get_play_suggestion(self):
        from core.play_architect import get_play_architect
        pa = get_play_architect()
        suggestion = pa.get_play_suggestion(0.7, "stressed")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_play_score(self):
        from core.play_architect import get_play_architect
        pa = get_play_architect()
        score = pa.get_play_score()
        assert 0 <= score <= 100


# -- Home Environment Optimizer Tests ---------------------------------------------------

class TestHomeEnvironmentOptimizer:
    """Test Home Environment Optimizer."""

    def test_singleton(self):
        from core.home_environment_optimizer import get_home_environment_optimizer
        h1 = get_home_environment_optimizer()
        h2 = get_home_environment_optimizer()
        assert h1 is h2

    def test_record_assessment(self):
        from core.home_environment_optimizer import get_home_environment_optimizer
        heo = get_home_environment_optimizer()
        entry = heo.record_assessment(
            "Bedroom",
            "sleep",
            0.8,
            0.7,
            0.6,
            0.5,
            0.9,
            "Peaceful",
        )
        assert entry is not None
        assert entry.space == "Bedroom"
        assert entry.environment_type == "sleep"

    def test_get_environment_stats(self):
        from core.home_environment_optimizer import get_home_environment_optimizer
        heo = get_home_environment_optimizer()
        stats = heo.get_environment_stats()
        assert isinstance(stats, dict)

    def test_get_optimization_suggestion(self):
        from core.home_environment_optimizer import get_home_environment_optimizer
        heo = get_home_environment_optimizer()
        suggestion = heo.get_optimization_suggestion(0.6, "clutter")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_environment_score(self):
        from core.home_environment_optimizer import get_home_environment_optimizer
        heo = get_home_environment_optimizer()
        score = heo.get_environment_score()
        assert 0 <= score <= 100


# -- Intergenerational Bridge Builder Tests ---------------------------------------------------

class TestIntergenerationalBridgeBuilder:
    """Test Intergenerational Bridge Builder."""

    def test_singleton(self):
        from core.intergenerational_bridge_builder import get_intergenerational_bridge_builder
        i1 = get_intergenerational_bridge_builder()
        i2 = get_intergenerational_bridge_builder()
        assert i1 is i2

    def test_record_interaction(self):
        from core.intergenerational_bridge_builder import get_intergenerational_bridge_builder
        ibb = get_intergenerational_bridge_builder()
        entry = ibb.record_interaction(
            "older",
            "Grandma",
            "learning",
            0.8,
            0.9,
            0.7,
            0.9,
            0.6,
            "Learned her life story",
        )
        assert entry is not None
        assert entry.generation == "older"
        assert entry.person == "Grandma"

    def test_get_bridge_stats(self):
        from core.intergenerational_bridge_builder import get_intergenerational_bridge_builder
        ibb = get_intergenerational_bridge_builder()
        stats = ibb.get_bridge_stats()
        assert isinstance(stats, dict)

    def test_get_bridge_suggestion(self):
        from core.intergenerational_bridge_builder import get_intergenerational_bridge_builder
        ibb = get_intergenerational_bridge_builder()
        suggestion = ibb.get_bridge_suggestion(0.7, "distant")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_bridge_score(self):
        from core.intergenerational_bridge_builder import get_intergenerational_bridge_builder
        ibb = get_intergenerational_bridge_builder()
        score = ibb.get_bridge_score()
        assert 0 <= score <= 100


# -- Aesthetic Life Designer Tests ---------------------------------------------------

class TestAestheticLifeDesigner:
    """Test Aesthetic Life Designer."""

    def test_singleton(self):
        from core.aesthetic_life_designer import get_aesthetic_life_designer
        a1 = get_aesthetic_life_designer()
        a2 = get_aesthetic_life_designer()
        assert a1 is a2

    def test_record_experience(self):
        from core.aesthetic_life_designer import get_aesthetic_life_designer
        ald = get_aesthetic_life_designer()
        entry = ald.record_experience(
            "Sunset over mountains",
            "natural",
            0.9,
            0.8,
            0.7,
            0.9,
            0.6,
            "Took breath away",
        )
        assert entry is not None
        assert entry.experience == "Sunset over mountains"
        assert entry.aesthetic_type == "natural"

    def test_get_aesthetic_stats(self):
        from core.aesthetic_life_designer import get_aesthetic_life_designer
        ald = get_aesthetic_life_designer()
        stats = ald.get_aesthetic_stats()
        assert isinstance(stats, dict)

    def test_get_aesthetic_suggestion(self):
        from core.aesthetic_life_designer import get_aesthetic_life_designer
        ald = get_aesthetic_life_designer()
        suggestion = ald.get_aesthetic_suggestion(0.6, "inspired")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_aesthetic_score(self):
        from core.aesthetic_life_designer import get_aesthetic_life_designer
        ald = get_aesthetic_life_designer()
        score = ald.get_aesthetic_score()
        assert 0 <= score <= 100


# -- Comfort Zone Challenger Tests ---------------------------------------------------

class TestComfortZoneChallenger:
    """Test Comfort Zone Challenger."""

    def test_singleton(self):
        from core.comfort_zone_challenger import get_comfort_zone_challenger
        c1 = get_comfort_zone_challenger()
        c2 = get_comfort_zone_challenger()
        assert c1 is c2

    def test_record_challenge(self):
        from core.comfort_zone_challenger import get_comfort_zone_challenger
        czc = get_comfort_zone_challenger()
        entry = czc.record_challenge(
            "Public speaking at meetup",
            "social",
            0.8,
            0.7,
            0.8,
            0.6,
            0.9,
            "Terrifying but worth it",
        )
        assert entry is not None
        assert entry.challenge == "Public speaking at meetup"
        assert entry.challenge_type == "social"

    def test_get_challenge_stats(self):
        from core.comfort_zone_challenger import get_comfort_zone_challenger
        czc = get_comfort_zone_challenger()
        stats = czc.get_challenge_stats()
        assert isinstance(stats, dict)

    def test_get_challenge_suggestion(self):
        from core.comfort_zone_challenger import get_comfort_zone_challenger
        czc = get_comfort_zone_challenger()
        suggestion = czc.get_challenge_suggestion(0.7, "stuck")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_challenge_score(self):
        from core.comfort_zone_challenger import get_comfort_zone_challenger
        czc = get_comfort_zone_challenger()
        score = czc.get_challenge_score()
        assert 0 <= score <= 100


# -- Conflict Resolution Coach Tests ---------------------------------------------------

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
        entry = crc.record_conflict(
            "Disagreement about project direction",
            "values",
            0.7,
            0.6,
            0.8,
            0.5,
            0.7,
            "Resolved through active listening",
        )
        assert entry is not None
        assert entry.conflict == "Disagreement about project direction"
        assert entry.conflict_type == "values"

    def test_get_conflict_stats(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        stats = crc.get_conflict_stats()
        assert isinstance(stats, dict)

    def test_get_resolution_suggestion(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        suggestion = crc.get_resolution_suggestion(0.6, "escalating")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_conflict_score(self):
        from core.conflict_resolution_coach import get_conflict_resolution_coach
        crc = get_conflict_resolution_coach()
        score = crc.get_conflict_score()
        assert 0 <= score <= 100


# -- Forgiveness Facilitator Tests ---------------------------------------------------

class TestForgivenessFacilitator:
    """Test Forgiveness Facilitator."""

    def test_singleton(self):
        from core.forgiveness_facilitator import get_forgiveness_facilitator
        f1 = get_forgiveness_facilitator()
        f2 = get_forgiveness_facilitator()
        assert f1 is f2

    def test_record_forgiveness(self):
        from core.forgiveness_facilitator import get_forgiveness_facilitator
        ff = get_forgiveness_facilitator()
        entry = ff.record_forgiveness(
            "Former friend who betrayed trust",
            "other",
            0.6,
            0.7,
            0.5,
            0.8,
            0.4,
            "Working on letting go",
        )
        assert entry is not None
        assert entry.target == "Former friend who betrayed trust"
        assert entry.forgiveness_type == "other"

    def test_get_forgiveness_stats(self):
        from core.forgiveness_facilitator import get_forgiveness_facilitator
        ff = get_forgiveness_facilitator()
        stats = ff.get_forgiveness_stats()
        assert isinstance(stats, dict)

    def test_get_forgiveness_suggestion(self):
        from core.forgiveness_facilitator import get_forgiveness_facilitator
        ff = get_forgiveness_facilitator()
        suggestion = ff.get_forgiveness_suggestion(0.5, "resentment")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_forgiveness_score(self):
        from core.forgiveness_facilitator import get_forgiveness_facilitator
        ff = get_forgiveness_facilitator()
        score = ff.get_forgiveness_score()
        assert 0 <= score <= 100


# -- Celebration Architect Tests ---------------------------------------------------

class TestCelebrationArchitect:
    """Test Celebration Architect."""

    def test_singleton(self):
        from core.celebration_architect import get_celebration_architect
        c1 = get_celebration_architect()
        c2 = get_celebration_architect()
        assert c1 is c2

    def test_record_celebration(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        entry = ca.record_celebration(
            "Completed marathon",
            "achievement",
            0.9,
            0.8,
            0.7,
            0.6,
            0.9,
            "Shared with family",
        )
        assert entry is not None
        assert entry.achievement == "Completed marathon"
        assert entry.celebration_type == "achievement"

    def test_get_celebration_stats(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        stats = ca.get_celebration_stats()
        assert isinstance(stats, dict)

    def test_get_celebration_suggestion(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        suggestion = ca.get_celebration_suggestion(0.7, "milestone")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_celebration_score(self):
        from core.celebration_architect import get_celebration_architect
        ca = get_celebration_architect()
        score = ca.get_celebration_score()
        assert 0 <= score <= 100


# -- Rest Designer Tests ---------------------------------------------------

class TestRestDesigner:
    """Test Rest Designer."""

    def test_singleton(self):
        from core.rest_designer import get_rest_designer
        r1 = get_rest_designer()
        r2 = get_rest_designer()
        assert r1 is r2

    def test_record_rest(self):
        from core.rest_designer import get_rest_designer
        rd = get_rest_designer()
        entry = rd.record_rest(
            "Afternoon nap",
            "physical",
            0.8,
            0.7,
            0.9,
            0.1,
            45,
            "Felt restored",
        )
        assert entry is not None
        assert entry.activity == "Afternoon nap"
        assert entry.rest_type == "physical"

    def test_get_rest_stats(self):
        from core.rest_designer import get_rest_designer
        rd = get_rest_designer()
        stats = rd.get_rest_stats()
        assert isinstance(stats, dict)

    def test_get_rest_suggestion(self):
        from core.rest_designer import get_rest_designer
        rd = get_rest_designer()
        suggestion = rd.get_rest_suggestion(0.5, "exhausted")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_rest_score(self):
        from core.rest_designer import get_rest_designer
        rd = get_rest_designer()
        score = rd.get_rest_score()
        assert 0 <= score <= 100


# -- Boundary Coach Tests ---------------------------------------------------

class TestBoundaryCoach:
    """Test Boundary Coach."""

    def test_singleton(self):
        from core.boundary_coach import get_boundary_coach
        b1 = get_boundary_coach()
        b2 = get_boundary_coach()
        assert b1 is b2

    def test_record_boundary(self):
        from core.boundary_coach import get_boundary_coach
        bc = get_boundary_coach()
        entry = bc.record_boundary(
            "Declined extra work request",
            "time",
            0.8,
            0.9,
            0.7,
            0.6,
            0.8,
            "Felt empowered",
        )
        assert entry is not None
        assert entry.situation == "Declined extra work request"
        assert entry.boundary_type == "time"

    def test_get_boundary_stats(self):
        from core.boundary_coach import get_boundary_coach
        bc = get_boundary_coach()
        stats = bc.get_boundary_stats()
        assert isinstance(stats, dict)

    def test_get_boundary_suggestion(self):
        from core.boundary_coach import get_boundary_coach
        bc = get_boundary_coach()
        suggestion = bc.get_boundary_suggestion(0.6, "overwhelmed")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_boundary_score(self):
        from core.boundary_coach import get_boundary_coach
        bc = get_boundary_coach()
        score = bc.get_boundary_score()
        assert 0 <= score <= 100


# -- Emotional Literacy Trainer Tests ---------------------------------------------------

class TestEmotionalLiteracyTrainer:
    """Test Emotional Literacy Trainer."""

    def test_singleton(self):
        from core.emotional_literacy_trainer import get_emotional_literacy_trainer
        e1 = get_emotional_literacy_trainer()
        e2 = get_emotional_literacy_trainer()
        assert e1 is e2

    def test_record_emotion(self):
        from core.emotional_literacy_trainer import get_emotional_literacy_trainer
        elt = get_emotional_literacy_trainer()
        entry = elt.record_emotion(
            "Frustrated with slow progress",
            "anger",
            0.7,
            0.6,
            0.5,
            "Unmet expectations",
            0.4,
            "Recognized it early",
        )
        assert entry is not None
        assert entry.emotion == "Frustrated with slow progress"
        assert entry.emotion_type == "anger"

    def test_get_emotion_stats(self):
        from core.emotional_literacy_trainer import get_emotional_literacy_trainer
        elt = get_emotional_literacy_trainer()
        stats = elt.get_emotion_stats()
        assert isinstance(stats, dict)

    def test_get_emotion_suggestion(self):
        from core.emotional_literacy_trainer import get_emotional_literacy_trainer
        elt = get_emotional_literacy_trainer()
        suggestion = elt.get_emotion_suggestion(0.6, "reactive")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_emotion_score(self):
        from core.emotional_literacy_trainer import get_emotional_literacy_trainer
        elt = get_emotional_literacy_trainer()
        score = elt.get_emotion_score()
        assert 0 <= score <= 100


# -- Hope Cultivator Tests ---------------------------------------------------

class TestHopeCultivator:
    """Test Hope Cultivator."""

    def test_singleton(self):
        from core.hope_cultivator import get_hope_cultivator
        h1 = get_hope_cultivator()
        h2 = get_hope_cultivator()
        assert h1 is h2

    def test_record_hope(self):
        from core.hope_cultivator import get_hope_cultivator
        hc = get_hope_cultivator()
        entry = hc.record_hope(
            "Building a better career",
            "motivational",
            0.8,
            0.7,
            0.6,
            0.5,
            0.9,
            "Small steps forward",
        )
        assert entry is not None
        assert entry.hope == "Building a better career"
        assert entry.hope_type == "motivational"

    def test_get_hope_stats(self):
        from core.hope_cultivator import get_hope_cultivator
        hc = get_hope_cultivator()
        stats = hc.get_hope_stats()
        assert isinstance(stats, dict)

    def test_get_hope_suggestion(self):
        from core.hope_cultivator import get_hope_cultivator
        hc = get_hope_cultivator()
        suggestion = hc.get_hope_suggestion(0.5, "despairing")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_hope_score(self):
        from core.hope_cultivator import get_hope_cultivator
        hc = get_hope_cultivator()
        score = hc.get_hope_score()
        assert 0 <= score <= 100


# -- Attention Steward Tests ---------------------------------------------------

class TestAttentionSteward:
    """Test Attention Steward."""

    def test_singleton(self):
        from core.attention_steward import get_attention_steward
        a1 = get_attention_steward()
        a2 = get_attention_steward()
        assert a1 is a2

    def test_record_attention(self):
        from core.attention_steward import get_attention_steward
        ast = get_attention_steward()
        entry = ast.record_attention(
            "Deep work on report",
            "deep",
            0.9,
            0.8,
            0.9,
            90,
            1,
            "Highly productive session",
        )
        assert entry is not None
        assert entry.activity == "Deep work on report"
        assert entry.attention_type == "deep"

    def test_get_attention_stats(self):
        from core.attention_steward import get_attention_steward
        ast = get_attention_steward()
        stats = ast.get_attention_stats()
        assert isinstance(stats, dict)

    def test_get_attention_suggestion(self):
        from core.attention_steward import get_attention_steward
        ast = get_attention_steward()
        suggestion = ast.get_attention_suggestion(0.6, "scattered")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_attention_score(self):
        from core.attention_steward import get_attention_steward
        ast = get_attention_steward()
        score = ast.get_attention_score()
        assert 0 <= score <= 100


# -- Identity Explorer Tests ---------------------------------------------------

class TestIdentityExplorer:
    """Test Identity Explorer."""

    def test_singleton(self):
        from core.identity_explorer import get_identity_explorer
        i1 = get_identity_explorer()
        i2 = get_identity_explorer()
        assert i1 is i2

    def test_record_reflection(self):
        from core.identity_explorer import get_identity_explorer
        ie = get_identity_explorer()
        entry = ie.record_reflection(
            "Realized I value creativity over status",
            "values",
            0.8,
            0.9,
            0.7,
            0.8,
            0.6,
            "Major insight",
        )
        assert entry is not None
        assert entry.reflection == "Realized I value creativity over status"
        assert entry.aspect == "values"

    def test_get_identity_stats(self):
        from core.identity_explorer import get_identity_explorer
        ie = get_identity_explorer()
        stats = ie.get_identity_stats()
        assert isinstance(stats, dict)

    def test_get_identity_suggestion(self):
        from core.identity_explorer import get_identity_explorer
        ie = get_identity_explorer()
        suggestion = ie.get_identity_suggestion(0.6, "fragmented")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_identity_score(self):
        from core.identity_explorer import get_identity_explorer
        ie = get_identity_explorer()
        score = ie.get_identity_score()
        assert 0 <= score <= 100


# -- Values Navigator Tests ---------------------------------------------------

class TestValuesNavigator:
    """Test Values Navigator."""

    def test_singleton(self):
        from core.values_navigator import get_values_navigator
        v1 = get_values_navigator()
        v2 = get_values_navigator()
        assert v1 is v2

    def test_record_decision(self):
        from core.values_navigator import get_values_navigator
        vn = get_values_navigator()
        entry = vn.record_decision(
            "Turned down lucrative but unethical project",
            "integrity",
            0.9,
            0.7,
            0.8,
            0.9,
            0.9,
            "Stood by principles",
        )
        assert entry is not None
        assert entry.decision == "Turned down lucrative but unethical project"
        assert entry.value == "integrity"

    def test_get_values_stats(self):
        from core.values_navigator import get_values_navigator
        vn = get_values_navigator()
        stats = vn.get_values_stats()
        assert isinstance(stats, dict)

    def test_get_values_suggestion(self):
        from core.values_navigator import get_values_navigator
        vn = get_values_navigator()
        suggestion = vn.get_values_suggestion(0.6, "conflict")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_values_score(self):
        from core.values_navigator import get_values_navigator
        vn = get_values_navigator()
        score = vn.get_values_score()
        assert 0 <= score <= 100


# -- Belonging Builder Tests ---------------------------------------------------

class TestBelongingBuilder:
    """Test Belonging Builder."""

    def test_singleton(self):
        from core.belonging_builder import get_belonging_builder
        b1 = get_belonging_builder()
        b2 = get_belonging_builder()
        assert b1 is b2

    def test_record_experience(self):
        from core.belonging_builder import get_belonging_builder
        bb = get_belonging_builder()
        entry = bb.record_experience(
            "Felt truly seen at dinner with friends",
            "friendship",
            0.9,
            0.8,
            0.9,
            0.7,
            0.8,
            "Deep connection",
        )
        assert entry is not None
        assert entry.experience == "Felt truly seen at dinner with friends"
        assert entry.belonging_type == "friendship"

    def test_get_belonging_stats(self):
        from core.belonging_builder import get_belonging_builder
        bb = get_belonging_builder()
        stats = bb.get_belonging_stats()
        assert isinstance(stats, dict)

    def test_get_belonging_suggestion(self):
        from core.belonging_builder import get_belonging_builder
        bb = get_belonging_builder()
        suggestion = bb.get_belonging_suggestion(0.5, "lonely")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_belonging_score(self):
        from core.belonging_builder import get_belonging_builder
        bb = get_belonging_builder()
        score = bb.get_belonging_score()
        assert 0 <= score <= 100


# -- Rejection Resilience Coach Tests ---------------------------------------------------

class TestRejectionResilienceCoach:
    """Test Rejection Resilience Coach."""

    def test_singleton(self):
        from core.rejection_resilience_coach import get_rejection_resilience_coach
        r1 = get_rejection_resilience_coach()
        r2 = get_rejection_resilience_coach()
        assert r1 is r2

    def test_record_rejection(self):
        from core.rejection_resilience_coach import get_rejection_resilience_coach
        rrc = get_rejection_resilience_coach()
        entry = rrc.record_rejection(
            "Proposal rejected by client",
            "professional",
            0.6,
            0.7,
            0.8,
            0.7,
            0.6,
            "Learned from feedback",
        )
        assert entry is not None
        assert entry.rejection == "Proposal rejected by client"
        assert entry.rejection_type == "professional"

    def test_get_rejection_stats(self):
        from core.rejection_resilience_coach import get_rejection_resilience_coach
        rrc = get_rejection_resilience_coach()
        stats = rrc.get_rejection_stats()
        assert isinstance(stats, dict)

    def test_get_rejection_suggestion(self):
        from core.rejection_resilience_coach import get_rejection_resilience_coach
        rrc = get_rejection_resilience_coach()
        suggestion = rrc.get_rejection_suggestion(0.5, "devastated")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_rejection_score(self):
        from core.rejection_resilience_coach import get_rejection_resilience_coach
        rrc = get_rejection_resilience_coach()
        score = rrc.get_rejection_score()
        assert 0 <= score <= 100


# -- Storytelling Coach Tests ---------------------------------------------------

class TestStorytellingCoach:
    """Test Storytelling Coach."""

    def test_singleton(self):
        from core.storytelling_coach import get_storytelling_coach
        s1 = get_storytelling_coach()
        s2 = get_storytelling_coach()
        assert s1 is s2

    def test_record_story(self):
        from core.storytelling_coach import get_storytelling_coach
        sc = get_storytelling_coach()
        entry = sc.record_story(
            "Shared my failure at the team meeting",
            "personal",
            0.8,
            0.9,
            0.9,
            0.8,
            0.7,
            "Connected with colleagues",
        )
        assert entry is not None
        assert entry.story == "Shared my failure at the team meeting"
        assert entry.story_type == "personal"

    def test_get_storytelling_stats(self):
        from core.storytelling_coach import get_storytelling_coach
        sc = get_storytelling_coach()
        stats = sc.get_storytelling_stats()
        assert isinstance(stats, dict)

    def test_get_storytelling_suggestion(self):
        from core.storytelling_coach import get_storytelling_coach
        sc = get_storytelling_coach()
        suggestion = sc.get_storytelling_suggestion(0.6, "hesitant")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_storytelling_score(self):
        from core.storytelling_coach import get_storytelling_coach
        sc = get_storytelling_coach()
        score = sc.get_storytelling_score()
        assert 0 <= score <= 100


# -- Voice Finder Tests ---------------------------------------------------

class TestVoiceFinder:
    """Test Voice Finder."""

    def test_singleton(self):
        from core.voice_finder import get_voice_finder
        v1 = get_voice_finder()
        v2 = get_voice_finder()
        assert v1 is v2

    def test_record_expression(self):
        from core.voice_finder import get_voice_finder
        vf = get_voice_finder()
        entry = vf.record_expression(
            "Finally told my boss what I really think",
            "professional",
            0.8,
            0.7,
            0.6,
            0.9,
            0.8,
            "Liberating",
        )
        assert entry is not None
        assert entry.expression == "Finally told my boss what I really think"
        assert entry.expression_type == "professional"

    def test_get_voice_stats(self):
        from core.voice_finder import get_voice_finder
        vf = get_voice_finder()
        stats = vf.get_voice_stats()
        assert isinstance(stats, dict)

    def test_get_voice_suggestion(self):
        from core.voice_finder import get_voice_finder
        vf = get_voice_finder()
        suggestion = vf.get_voice_suggestion(0.6, "suppressed")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_voice_score(self):
        from core.voice_finder import get_voice_finder
        vf = get_voice_finder()
        score = vf.get_voice_score()
        assert 0 <= score <= 100


# -- Transition Companion Tests ---------------------------------------------------

class TestTransitionCompanion:
    """Test Transition Companion."""

    def test_singleton(self):
        from core.transition_companion import get_transition_companion
        t1 = get_transition_companion()
        t2 = get_transition_companion()
        assert t1 is t2

    def test_record_transition(self):
        from core.transition_companion import get_transition_companion
        tc = get_transition_companion()
        entry = tc.record_transition(
            "Left corporate job for freelance",
            "career",
            0.7,
            0.6,
            0.5,
            0.4,
            0.8,
            "Scary but right",
        )
        assert entry is not None
        assert entry.transition == "Left corporate job for freelance"
        assert entry.transition_type == "career"

    def test_get_transition_stats(self):
        from core.transition_companion import get_transition_companion
        tc = get_transition_companion()
        stats = tc.get_transition_stats()
        assert isinstance(stats, dict)

    def test_get_transition_suggestion(self):
        from core.transition_companion import get_transition_companion
        tc = get_transition_companion()
        suggestion = tc.get_transition_suggestion(0.5, "resistant")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_transition_score(self):
        from core.transition_companion import get_transition_companion
        tc = get_transition_companion()
        score = tc.get_transition_score()
        assert 0 <= score <= 100


# -- Uncertainty Embracer Tests ---------------------------------------------------

class TestUncertaintyEmbracer:
    """Test Uncertainty Embracer."""

    def test_singleton(self):
        from core.uncertainty_embracer import get_uncertainty_embracer
        u1 = get_uncertainty_embracer()
        u2 = get_uncertainty_embracer()
        assert u1 is u2

    def test_record_uncertainty(self):
        from core.uncertainty_embracer import get_uncertainty_embracer
        ue = get_uncertainty_embracer()
        entry = ue.record_uncertainty(
            "Not sure about moving cities",
            "location",
            0.6,
            0.5,
            0.7,
            0.4,
            0.6,
            "Exploring options",
        )
        assert entry is not None
        assert entry.uncertainty == "Not sure about moving cities"
        assert entry.uncertainty_type == "location"

    def test_get_uncertainty_stats(self):
        from core.uncertainty_embracer import get_uncertainty_embracer
        ue = get_uncertainty_embracer()
        stats = ue.get_uncertainty_stats()
        assert isinstance(stats, dict)

    def test_get_uncertainty_suggestion(self):
        from core.uncertainty_embracer import get_uncertainty_embracer
        ue = get_uncertainty_embracer()
        suggestion = ue.get_uncertainty_suggestion(0.5, "anxious")
        assert isinstance(suggestion, dict)
        assert "suggestion" in suggestion

    def test_get_uncertainty_score(self):
        from core.uncertainty_embracer import get_uncertainty_embracer
        ue = get_uncertainty_embracer()
        score = ue.get_uncertainty_score()
        assert 0 <= score <= 100


class TestShadowIntegrator:
    def test_record_encounter(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        entry = si.record_encounter(shadow="envy", shadow_type="envy", awareness=0.6, acceptance=0.4, integration=0.3, trigger="colleague promotion", projection=0.8, notes="noticed projection")
        assert entry.shadow == "envy"
        assert entry.shadow_type == "envy"
        assert entry.awareness > 0
        assert entry.entry_id.startswith("shd_")

    def test_shadow_stats(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        stats = si.get_shadow_stats()
        assert isinstance(stats, dict)
        assert "avg_awareness" in stats

    def test_shadow_score(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        score = si.get_shadow_score()
        assert 0 <= score <= 100

    def test_shadow_suggestion(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        sug = si.get_shadow_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestInnerCriticTamer:
    def test_record_critic(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        entry = ic.record_critic(critic="you always mess up", critic_type="perfectionist", harshness=0.8, accuracy=0.3, response=0.5, self_compassion=0.4, challenge=0.2, notes="noticed the critic")
        assert entry.critic == "you always mess up"
        assert entry.critic_type == "perfectionist"
        assert entry.harshness > 0
        assert entry.entry_id.startswith("cric_")

    def test_critic_stats(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        stats = ic.get_critic_stats()
        assert isinstance(stats, dict)
        assert "avg_harshness" in stats

    def test_critic_score(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        score = ic.get_critic_score()
        assert 0 <= score <= 100

    def test_critic_suggestion(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        sug = ic.get_critic_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestPerfectionismHealer:
    def test_record_perfectionism(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        entry = ph.record_perfectionism(situation="spending 5 hours on email", perfectionism_type="task", cost=0.8, completion=0.2, satisfaction=0.3, self_acceptance=0.4, good_enough=0.2, notes="over-editing")
        assert entry.situation == "spending 5 hours on email"
        assert entry.perfectionism_type == "task"
        assert entry.cost > 0
        assert entry.entry_id.startswith("prf_")

    def test_perfectionism_stats(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        stats = ph.get_perfectionism_stats()
        assert isinstance(stats, dict)
        assert "avg_cost" in stats

    def test_perfectionism_score(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        score = ph.get_perfectionism_score()
        assert 0 <= score <= 100

    def test_perfectionism_suggestion(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        sug = ph.get_perfectionism_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestComparisonDetoxifier:
    def test_record_comparison(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        entry = cd.record_comparison(comparison="colleague got promoted", comparison_type="upward", distress=0.7, accuracy=0.2, response=0.5, gratitude=0.3, self_compassion=0.4, self_reference=0.2, notes="social media triggered")
        assert entry.comparison == "colleague got promoted"
        assert entry.comparison_type == "upward"
        assert entry.distress > 0
        assert entry.entry_id.startswith("cmp_")

    def test_comparison_stats(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        stats = cd.get_comparison_stats()
        assert isinstance(stats, dict)
        assert "avg_distress" in stats

    def test_comparison_score(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        score = cd.get_comparison_score()
        assert 0 <= score <= 100

    def test_comparison_suggestion(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        sug = cd.get_comparison_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug



class TestMoneyMindsetCoach:
    def test_record_mindset(self):
        from core.money_mindset_coach import get_money_mindset_coach
        mmc = get_money_mindset_coach()
        entry = mmc.record_mindset(situation="panic about bill", mindset_type="fear", clarity=0.3, confidence=0.2, alignment=0.4, generosity=0.5, action_taken=0.3, notes="avoided looking at account")
        assert entry.situation == "panic about bill"
        assert entry.mindset_type == "fear"
        assert entry.clarity > 0
        assert entry.entry_id.startswith("mnd_")

    def test_mindset_stats(self):
        from core.money_mindset_coach import get_money_mindset_coach
        mmc = get_money_mindset_coach()
        stats = mmc.get_mindset_stats()
        assert isinstance(stats, dict)
        assert "avg_clarity" in stats

    def test_mindset_score(self):
        from core.money_mindset_coach import get_money_mindset_coach
        mmc = get_money_mindset_coach()
        score = mmc.get_mindset_score()
        assert 0 <= score <= 100

    def test_mindset_suggestion(self):
        from core.money_mindset_coach import get_money_mindset_coach
        mmc = get_money_mindset_coach()
        sug = mmc.get_mindset_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestScarcityHealer:
    def test_record_scarcity(self):
        from core.scarcity_healer import get_scarcity_healer
        sh = get_scarcity_healer()
        entry = sh.record_scarcity(situation="not enough time for project", scarcity_type="time", distress=0.8, reality=0.3, response=0.4, gratitude=0.2, perspective=0.3, sufficiency=0.2, notes="overcommitted again")
        assert entry.situation == "not enough time for project"
        assert entry.scarcity_type == "time"
        assert entry.distress > 0
        assert entry.entry_id.startswith("scr_")

    def test_scarcity_stats(self):
        from core.scarcity_healer import get_scarcity_healer
        sh = get_scarcity_healer()
        stats = sh.get_scarcity_stats()
        assert isinstance(stats, dict)
        assert "avg_distress" in stats

    def test_scarcity_score(self):
        from core.scarcity_healer import get_scarcity_healer
        sh = get_scarcity_healer()
        score = sh.get_scarcity_score()
        assert 0 <= score <= 100

    def test_scarcity_suggestion(self):
        from core.scarcity_healer import get_scarcity_healer
        sh = get_scarcity_healer()
        sug = sh.get_scarcity_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestGenerosityCultivator:
    def test_record_generosity(self):
        from core.generosity_cultivator import get_generosity_cultivator
        gc = get_generosity_cultivator()
        entry = gc.record_generosity(gift="helped friend move", generosity_type="time", joy=0.7, reciprocity=0.4, sustainability=0.6, boundaries=0.5, receiving=0.3, notes="felt good but tired")
        assert entry.gift == "helped friend move"
        assert entry.generosity_type == "time"
        assert entry.joy > 0
        assert entry.entry_id.startswith("gen_")

    def test_generosity_stats(self):
        from core.generosity_cultivator import get_generosity_cultivator
        gc = get_generosity_cultivator()
        stats = gc.get_generosity_stats()
        assert isinstance(stats, dict)
        assert "avg_joy" in stats

    def test_generosity_score(self):
        from core.generosity_cultivator import get_generosity_cultivator
        gc = get_generosity_cultivator()
        score = gc.get_generosity_score()
        assert 0 <= score <= 100

    def test_generosity_suggestion(self):
        from core.generosity_cultivator import get_generosity_cultivator
        gc = get_generosity_cultivator()
        sug = gc.get_generosity_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestAbundanceArchitect:
    def test_record_abundance(self):
        from core.abundance_architect import get_abundance_architect
        aa = get_abundance_architect()
        entry = aa.record_abundance(manifestation="unexpected refund", abundance_type="financial", recognition=0.8, gratitude=0.7, expansion=0.5, sharing=0.3, blocking=0.1, notes="noticed and appreciated")
        assert entry.manifestation == "unexpected refund"
        assert entry.abundance_type == "financial"
        assert entry.recognition > 0
        assert entry.entry_id.startswith("abn_")

    def test_abundance_stats(self):
        from core.abundance_architect import get_abundance_architect
        aa = get_abundance_architect()
        stats = aa.get_abundance_stats()
        assert isinstance(stats, dict)
        assert "avg_recognition" in stats

    def test_abundance_score(self):
        from core.abundance_architect import get_abundance_architect
        aa = get_abundance_architect()
        score = aa.get_abundance_score()
        assert 0 <= score <= 100

    def test_abundance_suggestion(self):
        from core.abundance_architect import get_abundance_architect
        aa = get_abundance_architect()
        sug = aa.get_abundance_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug



class TestDecisionQualityTracker:
    def test_record_decision(self):
        from core.decision_quality_tracker import get_decision_quality_tracker
        dqt = get_decision_quality_tracker()
        entry = dqt.record_decision(decision="take the job offer", decision_type="career", quality=0.7, speed=0.6, information=0.8, outcome=0.9, clarity=0.7, values_alignment=0.8, notes="good process")
        assert entry.decision == "take the job offer"
        assert entry.decision_type == "career"
        assert entry.quality > 0
        assert entry.entry_id.startswith("dec_")

    def test_decision_stats(self):
        from core.decision_quality_tracker import get_decision_quality_tracker
        dqt = get_decision_quality_tracker()
        stats = dqt.get_decision_stats()
        assert isinstance(stats, dict)
        assert "avg_quality" in stats

    def test_decision_score(self):
        from core.decision_quality_tracker import get_decision_quality_tracker
        dqt = get_decision_quality_tracker()
        score = dqt.get_decision_score()
        assert 0 <= score <= 100

    def test_decision_suggestion(self):
        from core.decision_quality_tracker import get_decision_quality_tracker
        dqt = get_decision_quality_tracker()
        sug = dqt.get_decision_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestOptionalityMaximizer:
    def test_record_optionality(self):
        from core.optionality_maximizer import get_optionality_maximizer
        om = get_optionality_maximizer()
        entry = om.record_optionality(decision="learn new skill", optionality_type="skill", doors_opened=0.8, doors_closed=0.1, reversibility=0.9, flexibility=0.7, strategic_value=0.8, notes="increased options")
        assert entry.decision == "learn new skill"
        assert entry.optionality_type == "skill"
        assert entry.doors_opened > 0
        assert entry.entry_id.startswith("opt_")

    def test_optionality_stats(self):
        from core.optionality_maximizer import get_optionality_maximizer
        om = get_optionality_maximizer()
        stats = om.get_optionality_stats()
        assert isinstance(stats, dict)
        assert "avg_doors_opened" in stats

    def test_optionality_score(self):
        from core.optionality_maximizer import get_optionality_maximizer
        om = get_optionality_maximizer()
        score = om.get_optionality_score()
        assert 0 <= score <= 100

    def test_optionality_suggestion(self):
        from core.optionality_maximizer import get_optionality_maximizer
        om = get_optionality_maximizer()
        sug = om.get_optionality_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestExpectedValueCoach:
    def test_record_ev(self):
        from core.expected_value_coach import get_expected_value_coach
        evc = get_expected_value_coach()
        entry = evc.record_ev(decision="invest in course", ev_type="career", probability=0.7, payoff=0.8, actual_outcome=0.9, emotion_influence=0.3, calibration=0.8, notes="calculated risk paid off")
        assert entry.decision == "invest in course"
        assert entry.ev_type == "career"
        assert entry.probability > 0
        assert entry.entry_id.startswith("evc_")

    def test_ev_stats(self):
        from core.expected_value_coach import get_expected_value_coach
        evc = get_expected_value_coach()
        stats = evc.get_ev_stats()
        assert isinstance(stats, dict)
        assert "avg_calibration" in stats

    def test_ev_score(self):
        from core.expected_value_coach import get_expected_value_coach
        evc = get_expected_value_coach()
        score = evc.get_ev_score()
        assert 0 <= score <= 100

    def test_ev_suggestion(self):
        from core.expected_value_coach import get_expected_value_coach
        evc = get_expected_value_coach()
        sug = evc.get_ev_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestRegretMinimizer:
    def test_record_regret(self):
        from core.regret_minimizer import get_regret_minimizer
        rm = get_regret_minimizer()
        entry = rm.record_regret(regret="not traveling when I had the chance", regret_type="inaction", intensity=0.7, learning=0.6, resolution=0.4, anticipation=0.3, action_taken=0.5, notes="planning trip now")
        assert entry.regret == "not traveling when I had the chance"
        assert entry.regret_type == "inaction"
        assert entry.intensity > 0
        assert entry.entry_id.startswith("rgr_")

    def test_regret_stats(self):
        from core.regret_minimizer import get_regret_minimizer
        rm = get_regret_minimizer()
        stats = rm.get_regret_stats()
        assert isinstance(stats, dict)
        assert "avg_intensity" in stats

    def test_regret_score(self):
        from core.regret_minimizer import get_regret_minimizer
        rm = get_regret_minimizer()
        score = rm.get_regret_score()
        assert 0 <= score <= 100

    def test_regret_suggestion(self):
        from core.regret_minimizer import get_regret_minimizer
        rm = get_regret_minimizer()
        sug = rm.get_regret_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug



class TestCognitiveBiasDetector:
    def test_record_bias(self):
        from core.cognitive_bias_detector import get_cognitive_bias_detector
        cbd = get_cognitive_bias_detector()
        entry = cbd.record_bias(situation="hired someone who looked like me", bias_type="halo", detection=0.4, severity=0.7, correction=0.3, emotion_level=0.6, outcome=0.5, notes="realized too late")
        assert entry.situation == "hired someone who looked like me"
        assert entry.bias_type == "halo"
        assert entry.detection > 0
        assert entry.entry_id.startswith("bis_")

    def test_bias_stats(self):
        from core.cognitive_bias_detector import get_cognitive_bias_detector
        cbd = get_cognitive_bias_detector()
        stats = cbd.get_bias_stats()
        assert isinstance(stats, dict)
        assert "avg_detection" in stats

    def test_bias_score(self):
        from core.cognitive_bias_detector import get_cognitive_bias_detector
        cbd = get_cognitive_bias_detector()
        score = cbd.get_bias_score()
        assert 0 <= score <= 100

    def test_bias_suggestion(self):
        from core.cognitive_bias_detector import get_cognitive_bias_detector
        cbd = get_cognitive_bias_detector()
        sug = cbd.get_bias_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestMentalModelTrainer:
    def test_record_model(self):
        from core.mental_model_trainer import get_mental_model_trainer
        mmt = get_mental_model_trainer()
        entry = mmt.record_model(situation="deciding whether to quit job", model_type="opportunity_cost", application=0.8, effectiveness=0.7, integration=0.5, cross_domain=0.3, outcome=0.8, notes="helped clarify tradeoffs")
        assert entry.situation == "deciding whether to quit job"
        assert entry.model_type == "opportunity_cost"
        assert entry.application > 0
        assert entry.entry_id.startswith("mdl_")

    def test_model_stats(self):
        from core.mental_model_trainer import get_mental_model_trainer
        mmt = get_mental_model_trainer()
        stats = mmt.get_model_stats()
        assert isinstance(stats, dict)
        assert "avg_application" in stats

    def test_model_score(self):
        from core.mental_model_trainer import get_mental_model_trainer
        mmt = get_mental_model_trainer()
        score = mmt.get_model_score()
        assert 0 <= score <= 100

    def test_model_suggestion(self):
        from core.mental_model_trainer import get_mental_model_trainer
        mmt = get_mental_model_trainer()
        sug = mmt.get_model_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestFirstPrinciplesThinker:
    def test_record_thinking(self):
        from core.first_principles_thinker import get_first_principles_thinker
        fpt = get_first_principles_thinker()
        entry = fpt.record_thinking(problem="why is rent so high", thinking_type="deconstruction", depth=0.7, clarity=0.6, application=0.5, assumption_challenged=0.8, novelty=0.6, notes="broke down to supply and demand")
        assert entry.problem == "why is rent so high"
        assert entry.thinking_type == "deconstruction"
        assert entry.depth > 0
        assert entry.entry_id.startswith("fpt_")

    def test_thinking_stats(self):
        from core.first_principles_thinker import get_first_principles_thinker
        fpt = get_first_principles_thinker()
        stats = fpt.get_thinking_stats()
        assert isinstance(stats, dict)
        assert "avg_depth" in stats

    def test_thinking_score(self):
        from core.first_principles_thinker import get_first_principles_thinker
        fpt = get_first_principles_thinker()
        score = fpt.get_thinking_score()
        assert 0 <= score <= 100

    def test_thinking_suggestion(self):
        from core.first_principles_thinker import get_first_principles_thinker
        fpt = get_first_principles_thinker()
        sug = fpt.get_thinking_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestSystemsThinkingCoach:
    def test_record_systems(self):
        from core.systems_thinking_coach import get_systems_thinking_coach
        stc = get_systems_thinking_coach()
        entry = stc.record_systems(situation="team morale dropping", systems_type="feedback_loops", interconnection=0.7, perspective=0.6, intervention=0.5, feedback_seen=0.8, leverage_found=0.4, notes="identified vicious cycle")
        assert entry.situation == "team morale dropping"
        assert entry.systems_type == "feedback_loops"
        assert entry.interconnection > 0
        assert entry.entry_id.startswith("sys_")

    def test_systems_stats(self):
        from core.systems_thinking_coach import get_systems_thinking_coach
        stc = get_systems_thinking_coach()
        stats = stc.get_systems_stats()
        assert isinstance(stats, dict)
        assert "avg_interconnection" in stats

    def test_systems_score(self):
        from core.systems_thinking_coach import get_systems_thinking_coach
        stc = get_systems_thinking_coach()
        score = stc.get_systems_score()
        assert 0 <= score <= 100

    def test_systems_suggestion(self):
        from core.systems_thinking_coach import get_systems_thinking_coach
        stc = get_systems_thinking_coach()
        sug = stc.get_systems_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug



class TestAuthenticExpressionCoach:
    def test_record_expression(self):
        from core.authentic_expression_coach import get_authentic_expression_coach
        aec = get_authentic_expression_coach()
        entry = aec.record_expression(expression="I need alone time", expression_type="need", authenticity=0.8, fear=0.4, reception=0.7, satisfaction=0.8, kindness=0.9, notes="partner understood")
        assert entry.expression == "I need alone time"
        assert entry.expression_type == "need"
        assert entry.authenticity > 0
        assert entry.entry_id.startswith("exp_")

    def test_expression_stats(self):
        from core.authentic_expression_coach import get_authentic_expression_coach
        aec = get_authentic_expression_coach()
        stats = aec.get_expression_stats()
        assert isinstance(stats, dict)
        assert "avg_authenticity" in stats

    def test_expression_score(self):
        from core.authentic_expression_coach import get_authentic_expression_coach
        aec = get_authentic_expression_coach()
        score = aec.get_expression_score()
        assert 0 <= score <= 100

    def test_expression_suggestion(self):
        from core.authentic_expression_coach import get_authentic_expression_coach
        aec = get_authentic_expression_coach()
        sug = aec.get_expression_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestVulnerableCommunicationTrainer:
    def test_record_vulnerability(self):
        from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
        vct = get_vulnerable_communication_trainer()
        entry = vct.record_vulnerability(vulnerability="I am afraid of failing", vulnerability_type="fear", courage=0.8, reception=0.7, connection=0.9, safety=0.8, reciprocity=0.6, notes="friend shared back")
        assert entry.vulnerability == "I am afraid of failing"
        assert entry.vulnerability_type == "fear"
        assert entry.courage > 0
        assert entry.entry_id.startswith("vul_")

    def test_vulnerability_stats(self):
        from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
        vct = get_vulnerable_communication_trainer()
        stats = vct.get_vulnerability_stats()
        assert isinstance(stats, dict)
        assert "avg_courage" in stats

    def test_vulnerability_score(self):
        from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
        vct = get_vulnerable_communication_trainer()
        score = vct.get_vulnerability_score()
        assert 0 <= score <= 100

    def test_vulnerability_suggestion(self):
        from core.vulnerable_communication_trainer import get_vulnerable_communication_trainer
        vct = get_vulnerable_communication_trainer()
        sug = vct.get_vulnerability_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestDifficultConversationNavigator:
    def test_record_conversation(self):
        from core.difficult_conversation_navigator import get_difficult_conversation_navigator
        dcn = get_difficult_conversation_navigator()
        entry = dcn.record_conversation(topic="missed deadline", conversation_type="feedback", preparation=0.7, delivery=0.8, reception=0.6, outcome=0.7, emotion_management=0.8, follow_up=0.5, notes="went better than expected")
        assert entry.topic == "missed deadline"
        assert entry.conversation_type == "feedback"
        assert entry.preparation > 0
        assert entry.entry_id.startswith("cnv_")

    def test_conversation_stats(self):
        from core.difficult_conversation_navigator import get_difficult_conversation_navigator
        dcn = get_difficult_conversation_navigator()
        stats = dcn.get_conversation_stats()
        assert isinstance(stats, dict)
        assert "avg_preparation" in stats

    def test_conversation_score(self):
        from core.difficult_conversation_navigator import get_difficult_conversation_navigator
        dcn = get_difficult_conversation_navigator()
        score = dcn.get_conversation_score()
        assert 0 <= score <= 100

    def test_conversation_suggestion(self):
        from core.difficult_conversation_navigator import get_difficult_conversation_navigator
        dcn = get_difficult_conversation_navigator()
        sug = dcn.get_conversation_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestActiveListeningMaster:
    def test_record_listening(self):
        from core.active_listening_master import get_active_listening_master
        alm = get_active_listening_master()
        entry = alm.record_listening(situation="friend going through divorce", listening_type="empathic", presence=0.9, understanding=0.8, impact=0.9, no_fixing=0.9, no_judging=0.8, notes="just sat with them")
        assert entry.situation == "friend going through divorce"
        assert entry.listening_type == "empathic"
        assert entry.presence > 0
        assert entry.entry_id.startswith("lst_")

    def test_listening_stats(self):
        from core.active_listening_master import get_active_listening_master
        alm = get_active_listening_master()
        stats = alm.get_listening_stats()
        assert isinstance(stats, dict)
        assert "avg_presence" in stats

    def test_listening_score(self):
        from core.active_listening_master import get_active_listening_master
        alm = get_active_listening_master()
        score = alm.get_listening_score()
        assert 0 <= score <= 100

    def test_listening_suggestion(self):
        from core.active_listening_master import get_active_listening_master
        alm = get_active_listening_master()
        sug = alm.get_listening_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug

