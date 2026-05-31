with open('tests/test_modern_engines.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_tests = '''


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
'''

with open('tests/test_modern_engines.py', 'w', encoding='utf-8') as f:
    f.write(content + new_tests)

print('Appended batch 28 tests successfully')
