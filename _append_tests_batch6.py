with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 6 tests successfully')
