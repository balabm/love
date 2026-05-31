


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
