with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 19 tests successfully')
