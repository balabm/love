with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 9 tests successfully')
