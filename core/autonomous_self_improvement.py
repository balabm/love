"""
LOVE Autonomous Self-Improvement — Closed-loop daily self-modification

The pipeline that closes the loop:
  1. CapabilityGapDetector identifies LOVE's weakest behavioural areas
  2. EvolutionEngine scores current genome + generates improvement hypotheses
  3. SelfCoder generates a code modification for the top hypothesis
  4. hot_reload_modification() applies it live (or rolls back on failure)
  5. EvolutionEngine records the outcome — fitness improves or reverts

Runs once per day during low-activity / sleep phase (homeostasis.phase == "sleep").
Can also be triggered manually via /self_improve API endpoint.

Safety:
  - Never modifies api/main.py, core/llm.py, core/agent.py, or this file itself
  - Max 1 modification per 24h cycle by default
  - All changes go through self_coder's existing safety rules + hot_reload rollback
  - If 3 consecutive cycles fail, enter "cautious mode" (skip 48h)
"""
from __future__ import annotations

import json
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Paths ─────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "self_improvement"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CYCLE_HISTORY_FILE = DATA_DIR / "cycle_history.jsonl"

# Modules LOVE must never touch — EVER.
_PROTECTED_MODULES: frozenset[str] = frozenset({
    "api/main.py",
    "core/llm.py",
    "core/agent.py",
    "core/autonomous_self_improvement.py",
})

# hot_reload statuses that count as genuine failures.
_FAILURE_STATUSES: frozenset[str] = frozenset({
    "subprocess_failed",
    "reload_error",
    "compile_error",
    "not_found",
})

# Candidate core modules that are good self-improvement targets.
_CANDIDATE_MODULES: List[str] = [
    "core/capability_gap_detector.py",
    "core/evolution_engine.py",
    "core/homeostasis.py",
    "core/embodied_self.py",
    "core/moe_router.py",
    "core/self_coder.py",
    "core/memory.py",
    "core/curiosity_engine.py",
    "core/daily_briefing.py",
    "core/conversation_flow.py",
    "core/emotional.py",
    "core/context_engine.py",
    "agents/task_agent.py",
    "agents/fitness_agent.py",
]


# ── AutonomousSelfImprovement ─────────────────────────────────────────────────

class AutonomousSelfImprovement:
    """
    Singleton orchestrator that closes the self-improvement loop.

    Every ~24h during LOVE's sleep phase:
      gap → hypothesis → code mod → hot-reload → outcome recorded
    """

    _instance: Optional["AutonomousSelfImprovement"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "AutonomousSelfImprovement":
        with cls._instance_lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                obj._initialized = False
                cls._instance = obj
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._lock = threading.Lock()
        self._cycle_history: List[Dict[str, Any]] = []   # last 30 cycles
        self._consecutive_failures: int = 0
        self._cautious_until: Optional[datetime] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._load_history()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load_history(self) -> None:
        """Warm-start: read the last 30 cycles from disk."""
        try:
            if not CYCLE_HISTORY_FILE.exists():
                return
            rows = CYCLE_HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
            parsed: List[Dict[str, Any]] = []
            for line in rows:
                try:
                    parsed.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            self._cycle_history = parsed[-30:]
            # Restore consecutive failure counter from history
            self._consecutive_failures = 0
            for rec in reversed(self._cycle_history):
                if rec.get("status") in _FAILURE_STATUSES:
                    self._consecutive_failures += 1
                else:
                    break
            # Restore cautious_until
            for rec in reversed(self._cycle_history):
                if rec.get("cautious_until"):
                    cu = datetime.fromisoformat(rec["cautious_until"])
                    if cu > datetime.now():
                        self._cautious_until = cu
                    break
        except Exception as exc:
            print(f"[ASI] History load error: {exc}")

    def _persist_cycle(self, result: Dict[str, Any]) -> None:
        """Append one cycle result to JSONL file."""
        try:
            with CYCLE_HISTORY_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(result, default=str) + "\n")
        except Exception as exc:
            print(f"[ASI] Persist error: {exc}")

    # ── Step helpers ──────────────────────────────────────────────────────────

    def _get_target_module(self) -> Optional[str]:
        """
        Pick the module most likely to benefit from improvement today.

        Signals consulted (all best-effort — any can fail gracefully):
          1. CapabilityGapDetector open gaps → domain hints
          2. MoE router lowest-reward expert → expert name hint
          3. Homeostasis dissatisfaction level → urgency modifier
        Returns a relative path string (e.g. "core/emotion.py") or None.
        """
        project_root = Path(__file__).parent.parent

        # ── Signal 1: capability gaps ──────────────────────────────────────
        gap_domains: List[str] = []
        try:
            from core.capability_gap_detector import get_capability_gap_detector
            detector = get_capability_gap_detector()
            gaps = detector.detect_all_gaps()
            # prioritize_gaps() sorts by severity*0.4 + impact*0.3 + urgency*0.3
            prioritized = detector.prioritize_gaps()
            gap_domains = [g.domain for g in prioritized[:5]]
        except Exception as exc:
            print(f"[ASI] Gap detector signal failed (non-fatal): {exc}")

        # ── Signal 2: MoE lowest-reward expert ────────────────────────────
        lowest_expert: str = ""
        try:
            from core.moe_router import get_moe_router
            snap = get_moe_router().snapshot()
            experts = snap.get("top_experts", [])
            if experts:
                # top_experts is sorted highest→lowest; weakest is last
                lowest_expert = experts[-1].get("name", "")
        except Exception as exc:
            print(f"[ASI] MoE router signal failed (non-fatal): {exc}")

        # ── Signal 3: homeostasis dissatisfaction ──────────────────────────
        dissatisfaction: float = 0.0
        try:
            from core.homeostasis import get_homeostasis
            h_snap = get_homeostasis().snapshot()
            dissatisfaction = h_snap.get("drives", {}).get("dissatisfaction", 0.0)
        except Exception as exc:
            print(f"[ASI] Homeostasis signal failed (non-fatal): {exc}")

        # ── Score each candidate ───────────────────────────────────────────
        scored: List[tuple[float, str]] = []
        for rel_path in _CANDIDATE_MODULES:
            # Hard exclusion
            if rel_path in _PROTECTED_MODULES:
                continue
            full = project_root / rel_path
            if not full.exists():
                continue

            score = 0.0

            # Domain match: if any gap domain keyword appears in the path
            stem = rel_path.lower()
            for domain in gap_domains:
                if domain.lower() in stem:
                    score += 0.4
                    break

            # Expert match: lowest-reward expert name in path
            if lowest_expert and lowest_expert.lower().replace("_", "") in stem.replace("_", ""):
                score += 0.3

            # Dissatisfaction bonus (applies uniformly — nudge toward *any* change)
            score += dissatisfaction * 0.3

            # Small bonus for files not recently touched
            score += 0.05  # baseline so every file is eligible

            scored.append((score, rel_path))

        if not scored:
            return None

        # Pick highest scorer, break ties by first occurrence
        scored.sort(key=lambda t: -t[0])
        best_score, best_path = scored[0]

        # If the best score is suspiciously low, still proceed — we can always find *something*
        print(f"[ASI] Target module selected: {best_path} (score={best_score:.3f})")
        return best_path

    def _generate_hypothesis(self, module_path: str) -> str:
        """
        Ask the reasoning LLM for ONE specific, testable improvement hypothesis
        for the given module, informed by SelfCoder's static analysis.
        """
        from core.self_coder import get_self_coder
        from core.llm import get_reasoning_llm

        project_root = Path(__file__).parent.parent
        full_path = str(project_root / module_path)

        # Static analysis (may include LLM-generated opportunities)
        analysis = get_self_coder().analyze_file(full_path)
        opps = analysis.improvement_opportunities or analysis.potential_issues or []
        opps_text = "\n".join(f"  - {o}" for o in opps[:8]) if opps else "  - No specific issues detected"

        prompt = (
            f"You are LOVE's autonomous self-improvement system. "
            f"Your job is to make LOVE more helpful, responsive, and insightful for the user.\n\n"
            f"Module: {module_path}\n"
            f"Lines of code: {analysis.lines_of_code}\n"
            f"Functions: {', '.join(analysis.functions[:8]) or 'none'}\n"
            f"Classes: {', '.join(analysis.classes[:4]) or 'none'}\n\n"
            f"Improvement opportunities:\n{opps_text}\n\n"
            f"Propose ONE specific, testable code improvement that would make LOVE "
            f"more helpful to the user. Be concrete: name the function, describe the "
            f"change, explain the expected benefit in one sentence. "
            f"Do NOT suggest adding imports, docstrings-only changes, or reformatting. "
            f"Return a single paragraph, no bullet points."
        )

        try:
            llm = get_reasoning_llm()
            hypothesis = str(llm.invoke(prompt)).strip()
            # Truncate very long LLM responses — we only need the hypothesis, not an essay
            if len(hypothesis) > 800:
                hypothesis = hypothesis[:800].rsplit(".", 1)[0] + "."
            return hypothesis
        except Exception as exc:
            print(f"[ASI] Hypothesis generation error: {exc}")
            # Fallback: use the top improvement opportunity as hypothesis
            if opps:
                return f"Improve {module_path}: {opps[0]}"
            return f"Refactor {module_path} to reduce complexity and improve proactive behaviour."

    def _attempt_modification(
        self,
        module_path: str,
        hypothesis: str,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the SelfCoder pipeline: generate → test → hot-reload.
        Returns a result dict with at minimum {"status": ...}.
        """
        from core.self_coder import get_self_coder
        project_root = Path(__file__).parent.parent
        full_path = str(project_root / module_path)

        sc = get_self_coder()

        # 1. Generate modification
        mod = sc.generate_modification(hypothesis, full_path, "enhancement")
        if mod is None:
            return {
                "status": "generation_failed",
                "detail": "SelfCoder returned None — safety rules may have blocked it",
            }

        modification_id = mod.id

        # 2. Test in sandbox
        passed = sc.test_modification(modification_id)
        if not passed:
            return {
                "status": "subprocess_failed",
                "modification_id": modification_id,
                "detail": f"Sandbox test failed for modification {modification_id}",
            }

        # 3. Dry-run bail-out
        if dry_run:
            return {
                "status": "dry_run_ok",
                "modification_id": modification_id,
                "hypothesis": hypothesis,
                "detail": "Sandbox passed; skipped live apply (dry_run=True)",
            }

        # 4. Hot-reload into the live process
        reload_result = sc.hot_reload_modification(modification_id)
        return {
            "status": reload_result.get("status", "unknown"),
            "modification_id": modification_id,
            "hot_reload_detail": reload_result.get("detail", ""),
            "module_reloaded": reload_result.get("module", ""),
        }

    def _record_outcome(self, cycle_result: Dict[str, Any]) -> None:
        """
        Update consecutive-failure counter, cautious-mode flag,
        trim in-memory history, and persist.
        """
        with self._lock:
            status = cycle_result.get("status", "unknown")

            if status in _FAILURE_STATUSES:
                self._consecutive_failures += 1
                if self._consecutive_failures >= 3:
                    self._cautious_until = datetime.now() + timedelta(hours=48)
                    cycle_result["cautious_until"] = self._cautious_until.isoformat()
                    print(
                        f"[ASI] ⚠ 3 consecutive failures — entering cautious mode "
                        f"until {self._cautious_until.isoformat()}"
                    )
            else:
                self._consecutive_failures = 0
                self._cautious_until = None

            cycle_result["consecutive_failures"] = self._consecutive_failures

            self._cycle_history.append(cycle_result)
            if len(self._cycle_history) > 30:
                self._cycle_history = self._cycle_history[-30:]

        self._persist_cycle(cycle_result)

    # ── Public: run_cycle ─────────────────────────────────────────────────────

    def run_cycle(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        The main closed-loop self-improvement cycle.

        Steps:
          1. Cautious-mode gate
          2. Target module selection
          3. Hypothesis generation
          4. Modification attempt (generate → test → hot-reload)
          5. Outcome recording

        Returns a comprehensive result dict.
        """
        t_start = time.monotonic()
        timestamp = datetime.now().isoformat()

        base: Dict[str, Any] = {
            "timestamp": timestamp,
            "dry_run": dry_run,
            "target_module": None,
            "hypothesis": None,
            "modification_id": None,
            "hot_reload_status": None,
            "duration_seconds": 0.0,
            "consecutive_failures": self._consecutive_failures,
        }

        # ── Step 1: Cautious mode ──────────────────────────────────────────
        with self._lock:
            cautious_until = self._cautious_until

        if cautious_until and datetime.now() < cautious_until:
            result = {
                **base,
                "status": "cautious_mode",
                "detail": f"Cautious mode active until {cautious_until.isoformat()}",
            }
            self._record_outcome(result)
            print(f"[ASI] Skipping cycle — cautious mode active until {cautious_until.isoformat()}")
            return result

        # ── Step 2: Target module ──────────────────────────────────────────
        try:
            target = self._get_target_module()
        except Exception as exc:
            target = None
            print(f"[ASI] get_target_module() raised: {exc}\n{traceback.format_exc()}")

        if not target:
            result = {**base, "status": "no_target", "detail": "No suitable target module found"}
            self._record_outcome(result)
            return result

        base["target_module"] = target

        # ── Step 3: Hypothesis ─────────────────────────────────────────────
        try:
            hypothesis = self._generate_hypothesis(target)
        except Exception as exc:
            hypothesis = f"Improve proactive helpfulness in {target}."
            print(f"[ASI] Hypothesis generation raised: {exc}")

        base["hypothesis"] = hypothesis
        print(f"[ASI] Hypothesis: {hypothesis[:120]}{'...' if len(hypothesis) > 120 else ''}")

        # ── Step 4: Modification attempt ──────────────────────────────────
        try:
            mod_result = self._attempt_modification(target, hypothesis, dry_run=dry_run)
        except Exception as exc:
            mod_result = {
                "status": "subprocess_failed",
                "detail": f"Unhandled exception in attempt_modification: {exc}",
            }
            print(f"[ASI] Modification attempt raised: {exc}\n{traceback.format_exc()}")

        base.update({
            "status": mod_result.get("status", "unknown"),
            "modification_id": mod_result.get("modification_id"),
            "hot_reload_status": mod_result.get("status"),
            "hot_reload_detail": mod_result.get("hot_reload_detail") or mod_result.get("detail", ""),
            "module_reloaded": mod_result.get("module_reloaded", ""),
        })
        base["duration_seconds"] = round(time.monotonic() - t_start, 2)

        # ── Step 5: Record outcome ─────────────────────────────────────────
        self._record_outcome(base)

        _emoji = "✅" if base["status"] == "ok" else ("🔍" if dry_run else "❌")
        print(
            f"[ASI] Cycle complete {_emoji} | status={base['status']} | "
            f"target={target} | {base['duration_seconds']}s"
        )
        return base

    # ── Daemon ────────────────────────────────────────────────────────────────

    def _daemon_loop(self) -> None:
        """
        Background thread: check every hour if it's time to run a cycle.
        Runs during homeostasis "sleep" phase, or between 02:00–05:00 local time
        as a fallback. Ensures at least 20h between cycles.
        """
        print("[ASI] Daemon started.")
        while self._running:
            try:
                self._maybe_run_cycle()
            except Exception as exc:
                print(f"[ASI] Daemon loop error: {exc}\n{traceback.format_exc()}")
            # Check again in 1 hour
            for _ in range(3600):
                if not self._running:
                    return
                time.sleep(1)

    def _is_sleep_phase(self) -> bool:
        """Return True if homeostasis says 'sleep', falling back to 02-05 local time."""
        try:
            from core.homeostasis import get_homeostasis
            snap = get_homeostasis().snapshot()
            return snap.get("circadian_phase") == "sleep"
        except Exception:
            pass
        # Fallback: 02:00–05:00 local time
        hour = datetime.now().hour
        return 2 <= hour < 5

    def _last_cycle_age_hours(self) -> float:
        """How many hours since the last completed cycle (regardless of status)."""
        with self._lock:
            history = list(self._cycle_history)
        if not history:
            return float("inf")
        last_ts_str = history[-1].get("timestamp", "")
        if not last_ts_str:
            return float("inf")
        try:
            last_ts = datetime.fromisoformat(last_ts_str)
            return (datetime.now() - last_ts).total_seconds() / 3600.0
        except Exception:
            return float("inf")

    def _maybe_run_cycle(self) -> None:
        """Run a cycle if conditions are met (sleep phase + >20h since last)."""
        if not self._is_sleep_phase():
            return
        age_h = self._last_cycle_age_hours()
        if age_h < 20.0:
            print(f"[ASI] Skipping — last cycle was {age_h:.1f}h ago (need ≥20h)")
            return
        print(f"[ASI] Conditions met (sleep phase, {age_h:.1f}h since last) — running cycle")
        self.run_cycle(dry_run=False)

    def start_daemon(self) -> None:
        """Start the background improvement daemon (idempotent)."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(
            target=self._daemon_loop,
            daemon=True,
            name="LOVE-AutonomousSelfImprovement",
        )
        self._thread.start()
        print("[ASI] Daemon thread launched.")

    def stop_daemon(self) -> None:
        """Signal the daemon to stop (graceful)."""
        with self._lock:
            self._running = False
        print("[ASI] Daemon stop requested.")

    # ── Status / Introspection ────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Public status summary — suitable for API endpoints."""
        with self._lock:
            history = list(self._cycle_history)
            consecutive_failures = self._consecutive_failures
            cautious_until = self._cautious_until
            running = self._running

        last_cycle: Optional[Dict[str, Any]] = history[-1] if history else None
        total = len(history)
        successes = sum(1 for c in history if c.get("status") == "ok")
        success_rate = round(successes / total, 3) if total else 0.0

        # Estimate next run: earliest of (last_cycle + 20h) while in sleep phase
        next_run_estimate: Optional[str] = None
        if last_cycle and last_cycle.get("timestamp"):
            try:
                last_dt = datetime.fromisoformat(last_cycle["timestamp"])
                candidate = last_dt + timedelta(hours=20)
                next_run_estimate = candidate.isoformat()
            except Exception:
                pass

        return {
            "running": running,
            "last_cycle": last_cycle,
            "consecutive_failures": consecutive_failures,
            "cautious_until": cautious_until.isoformat() if cautious_until else None,
            "cycles_total": total,
            "success_rate": success_rate,
            "next_run_estimate": next_run_estimate,
        }

    def snapshot(self) -> Dict[str, Any]:
        """Alias for get_status() — used by living_substrate.substrate_snapshot()."""
        return self.get_status()


# ── Singleton accessor ────────────────────────────────────────────────────────

_asi_instance: Optional[AutonomousSelfImprovement] = None
_asi_lock = threading.Lock()


def get_autonomous_self_improvement() -> AutonomousSelfImprovement:
    global _asi_instance
    if _asi_instance is None:
        with _asi_lock:
            if _asi_instance is None:
                _asi_instance = AutonomousSelfImprovement()
    return _asi_instance
