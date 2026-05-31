with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 7 tests successfully')
