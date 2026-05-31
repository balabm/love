with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 12 tests successfully')
