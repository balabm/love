with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 13 tests successfully')
