


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
