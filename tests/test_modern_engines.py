


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
