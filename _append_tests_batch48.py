import os

test_file = "tests/test_modern_engines.py"

batch48_tests = '''

class TestShadowIntegrator:
    def test_record_encounter(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        entry = si.record_encounter(shadow="envy", shadow_type="envy", awareness=0.6, acceptance=0.4, integration=0.3, trigger="colleague promotion", projection=0.8, notes="noticed projection")
        assert entry.shadow == "envy"
        assert entry.shadow_type == "envy"
        assert entry.awareness > 0
        assert entry.entry_id.startswith("shd_")

    def test_shadow_stats(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        stats = si.get_shadow_stats()
        assert isinstance(stats, dict)
        assert "avg_awareness" in stats

    def test_shadow_score(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        score = si.get_shadow_score()
        assert 0 <= score <= 100

    def test_shadow_suggestion(self):
        from core.shadow_integrator import get_shadow_integrator
        si = get_shadow_integrator()
        sug = si.get_shadow_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestInnerCriticTamer:
    def test_record_critic(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        entry = ic.record_critic(critic="you always mess up", critic_type="perfectionist", harshness=0.8, accuracy=0.3, response=0.5, self_compassion=0.4, challenge=0.2, notes="noticed the critic")
        assert entry.critic == "you always mess up"
        assert entry.critic_type == "perfectionist"
        assert entry.harshness > 0
        assert entry.entry_id.startswith("cric_")

    def test_critic_stats(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        stats = ic.get_critic_stats()
        assert isinstance(stats, dict)
        assert "avg_harshness" in stats

    def test_critic_score(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        score = ic.get_critic_score()
        assert 0 <= score <= 100

    def test_critic_suggestion(self):
        from core.inner_critic_tamer import get_inner_critic_tamer
        ic = get_inner_critic_tamer()
        sug = ic.get_critic_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestPerfectionismHealer:
    def test_record_perfectionism(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        entry = ph.record_perfectionism(situation="spending 5 hours on email", perfectionism_type="task", cost=0.8, completion=0.2, satisfaction=0.3, self_acceptance=0.4, good_enough=0.2, notes="over-editing")
        assert entry.situation == "spending 5 hours on email"
        assert entry.perfectionism_type == "task"
        assert entry.cost > 0
        assert entry.entry_id.startswith("prf_")

    def test_perfectionism_stats(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        stats = ph.get_perfectionism_stats()
        assert isinstance(stats, dict)
        assert "avg_cost" in stats

    def test_perfectionism_score(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        score = ph.get_perfectionism_score()
        assert 0 <= score <= 100

    def test_perfectionism_suggestion(self):
        from core.perfectionism_healer import get_perfectionism_healer
        ph = get_perfectionism_healer()
        sug = ph.get_perfectionism_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug


class TestComparisonDetoxifier:
    def test_record_comparison(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        entry = cd.record_comparison(comparison="colleague got promoted", comparison_type="upward", distress=0.7, accuracy=0.2, response=0.5, gratitude=0.3, self_compassion=0.4, self_reference=0.2, notes="social media triggered")
        assert entry.comparison == "colleague got promoted"
        assert entry.comparison_type == "upward"
        assert entry.distress > 0
        assert entry.entry_id.startswith("cmp_")

    def test_comparison_stats(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        stats = cd.get_comparison_stats()
        assert isinstance(stats, dict)
        assert "avg_distress" in stats

    def test_comparison_score(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        score = cd.get_comparison_score()
        assert 0 <= score <= 100

    def test_comparison_suggestion(self):
        from core.comparison_detoxifier import get_comparison_detoxifier
        cd = get_comparison_detoxifier()
        sug = cd.get_comparison_suggestion(capacity=0.6, context="work")
        assert "suggestion" in sug
        assert "capacity_note" in sug

'''

with open(test_file, "a") as f:
    f.write(batch48_tests)

print("Tests appended.")
