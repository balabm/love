"""
wave_engine.py — Wave 23: Autonomous Wave Evolution Engine

LOVE's self-directed growth loop. Every 24h (or on demand), this engine:
1. Scans all life + system domains for gaps, stagnation, and opportunities
2. Generates a concrete Wave proposal (what to build next and why)
3. Stores the proposal, tracks execution status
4. Feeds outcomes back into the next cycle

Philosophy: LOVE doesn't wait to be told what to improve.
It watches, infers, proposes, and acts — like a founder with taste.
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.settings import get_settings

# ──────────────────────────────────────────────────────────────────────────────
# Storage
# ──────────────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "wave_engine"
DATA_DIR.mkdir(parents=True, exist_ok=True)

WAVES_FILE = DATA_DIR / "waves.json"
LOG_FILE = DATA_DIR / "wave_log.jsonl"
STATUS_FILE = DATA_DIR / "status.json"


def _load_waves() -> List[Dict]:
    if WAVES_FILE.exists():
        try:
            return json.loads(WAVES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_waves(waves: List[Dict]):
    WAVES_FILE.write_text(json.dumps(waves, indent=2, ensure_ascii=False), encoding="utf-8")


def _log(event: str, data: Dict):
    entry = {"ts": datetime.now().isoformat(), "event": event, **data}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Gap Scanner
# ──────────────────────────────────────────────────────────────────────────────

class GapScanner:
    """Aggregates signals from all LOVE subsystems to identify what's missing or weak."""

    def scan(self) -> Dict[str, Any]:
        gaps = []
        scores = {}

        # 1. Life domains
        try:
            from core.life_domains import get_life_domains_engine
            engine = get_life_domains_engine()
            dash = engine.get_dashboard()
            life_score = dash.get("life_score", 0)
            scores["life_domains"] = life_score
            nudges = dash.get("nudges", [])
            if nudges:
                gaps.append({
                    "domain": "life_domains",
                    "severity": max(0.3, (100 - life_score) / 100),
                    "description": f"Life domains score {life_score:.0f}/100. Active nudges: {'; '.join(nudges[:2])}",
                    "category": "physical_wellbeing"
                })
        except Exception as e:
            gaps.append({"domain": "life_domains", "severity": 0.4, "description": f"Life domains unavailable: {e}", "category": "system"})

        # 2. Emotional state
        try:
            from core.emotional import get_emotional_summary
            summary = get_emotional_summary(days=7)
            stress = summary.get("current_stress", 0)
            trend = summary.get("stress_trend", "stable")
            scores["emotional"] = max(0, 100 - stress)
            if stress > 60 or trend == "rising":
                gaps.append({
                    "domain": "emotional",
                    "severity": stress / 100,
                    "description": f"Stress at {stress}%, trend: {trend}. Emotional recovery features may help.",
                    "category": "mental_wellbeing"
                })
        except Exception:
            pass

        # 3. Guardian / work balance
        try:
            from tools.guardian import check_work_status
            ws = check_work_status()
            hours = ws.get("hours_today", 0)
            limit = ws.get("daily_limit", 8)
            pct = (hours / limit * 100) if limit else 0
            scores["guardian"] = max(0, 100 - max(0, pct - 100))
            if pct > 90:
                gaps.append({
                    "domain": "guardian",
                    "severity": min(1.0, pct / 100),
                    "description": f"Work at {pct:.0f}% of limit ({hours:.1f}h/{limit}h). Recovery automation lacking.",
                    "category": "productivity_balance"
                })
        except Exception:
            pass

        # 4. Memory health
        try:
            from core.memory import get_memory_stats
            stats = get_memory_stats()
            count = stats.get("total_memories", 0)
            scores["memory"] = min(100, count)
            if count < 10:
                gaps.append({
                    "domain": "memory",
                    "severity": 0.5,
                    "description": f"Only {count} memories stored. Context richness is low.",
                    "category": "intelligence"
                })
        except Exception:
            pass

        # 5. Capability gaps from detector
        try:
            from core.capability_gap_detector import CapabilityGapDetector
            detector = CapabilityGapDetector()
            detected = detector.detect_all_gaps()
            top_gaps = sorted(detected, key=lambda g: g.severity, reverse=True)[:3]
            for g in top_gaps:
                gaps.append({
                    "domain": g.domain if hasattr(g, "domain") else "capability",
                    "severity": g.severity if hasattr(g, "severity") else 0.5,
                    "description": g.description if hasattr(g, "description") else str(g),
                    "category": "capability"
                })
        except Exception:
            pass

        # 6. Module health
        try:
            from core.module_lifecycle import get_lifecycle_manager
            mgr = get_lifecycle_manager()
            statuses = mgr.get_all_statuses() if hasattr(mgr, 'get_all_statuses') else {}
            degraded = [k for k, v in statuses.items() if isinstance(v, dict) and v.get("status") not in ("ready", "running")]
            if degraded:
                gaps.append({
                    "domain": "modules",
                    "severity": min(0.8, len(degraded) * 0.15),
                    "description": f"{len(degraded)} modules degraded: {', '.join(degraded[:4])}",
                    "category": "system_health"
                })
        except Exception:
            pass

        # 7. Fitness
        try:
            from agents.fitness_agent import FitnessAgent
            agent = FitnessAgent()
            summary = agent.get_weekly_summary()
            workouts = summary.get("workouts_this_week", 0)
            scores["fitness"] = min(100, workouts * 25)
            if workouts < 2:
                gaps.append({
                    "domain": "fitness",
                    "severity": 0.5,
                    "description": f"Only {workouts} workouts this week. Fitness tracking is passive.",
                    "category": "physical_wellbeing"
                })
        except Exception:
            pass

        overall_gap_score = sum(g["severity"] for g in gaps) / max(1, len(gaps)) if gaps else 0

        return {
            "gaps": gaps,
            "scores": scores,
            "overall_gap_score": round(overall_gap_score, 3),
            "gap_count": len(gaps),
            "scanned_at": datetime.now().isoformat()
        }


# ──────────────────────────────────────────────────────────────────────────────
# Wave Proposer
# ──────────────────────────────────────────────────────────────────────────────

WAVE_TEMPLATES = {
    "physical_wellbeing": {
        "title": "Body Intelligence Upgrade",
        "description": "Deepen life domain tracking with pattern detection, adaptive goals, and proactive recovery nudges.",
        "features": [
            "Cross-domain correlation: detect when poor sleep degrades focus",
            "Adaptive hydration goals based on workout intensity",
            "Weekly body report with trend insights",
            "Smart nudge scheduler that respects focus mode",
        ],
        "priority": "high"
    },
    "mental_wellbeing": {
        "title": "Emotional Resilience Layer",
        "description": "Build LOVE's ability to detect and interrupt stress spirals before they compound.",
        "features": [
            "Stress pattern early-warning system",
            "Automatic recovery suggestion engine (breathwork, walks, shutdown rituals)",
            "Mood correlation with productivity, sleep, nutrition",
            "Weekly emotional report with actionable insights",
        ],
        "priority": "high"
    },
    "productivity_balance": {
        "title": "Deep Work Guardian v2",
        "description": "Make LOVE's work protection smarter — anticipatory, not reactive.",
        "features": [
            "Predict overwork risk from calendar + task density",
            "Auto-schedule recovery blocks",
            "End-of-day shutdown ritual trigger",
            "Weekly work pattern analysis",
        ],
        "priority": "medium"
    },
    "intelligence": {
        "title": "Memory Enrichment System",
        "description": "Grow LOVE's contextual recall and semantic understanding of the user's life.",
        "features": [
            "Auto-extract insights from daily conversations",
            "Semantic clustering of memories",
            "Proactive memory surfacing based on current context",
            "Life chapter detection (what phase of life are you in?)",
        ],
        "priority": "high"
    },
    "capability": {
        "title": "Capability Closure Sprint",
        "description": "Systematically close the highest-severity detected capability gaps.",
        "features": [
            "Prioritized gap resolution queue",
            "Auto-assign gaps to relevant agents",
            "Progress tracking dashboard",
            "Gap re-scan after 7 days",
        ],
        "priority": "medium"
    },
    "system_health": {
        "title": "Self-Healing Module Hardening",
        "description": "Zero degraded modules — make LOVE's substrate bulletproof.",
        "features": [
            "Auto-restart degraded modules with backoff",
            "Dependency health check chain",
            "Module upgrade scaffolding",
            "Health score in dashboard header",
        ],
        "priority": "medium"
    }
}

DEFAULT_WAVE = {
    "title": "General Life OS Enhancement",
    "description": "Broad improvement across all domains based on recent usage patterns.",
    "features": [
        "Improve proactive suggestion quality",
        "Add cross-domain pattern detection",
        "Enhance daily briefing with life domain data",
        "Wire life domains into Ritual view morning briefing",
    ],
    "priority": "medium"
}


class WaveProposer:
    """Turns a gap scan result into a concrete Wave proposal."""

    def propose(self, scan_result: Dict) -> Dict:
        gaps = scan_result.get("gaps", [])
        if not gaps:
            return self._build_wave(DEFAULT_WAVE, scan_result, "no_specific_gaps")

        # Find most impactful gap category
        category_severity = {}
        for g in gaps:
            cat = g.get("category", "general")
            category_severity[cat] = category_severity.get(cat, 0) + g.get("severity", 0.3)

        top_cat = max(category_severity, key=category_severity.get)
        template = WAVE_TEMPLATES.get(top_cat, DEFAULT_WAVE)

        return self._build_wave(template, scan_result, top_cat)

    def _build_wave(self, template: Dict, scan: Dict, trigger_category: str) -> Dict:
        existing_waves = _load_waves()
        wave_number = len(existing_waves) + 22  # Start Wave numbering from current Wave 22

        return {
            "wave_number": wave_number,
            "title": f"Wave {wave_number}: {template['title']}",
            "description": template["description"],
            "features": template["features"],
            "priority": template.get("priority", "medium"),
            "trigger_category": trigger_category,
            "trigger_gaps": [g["description"][:100] for g in scan.get("gaps", [])[:3]],
            "overall_gap_score": scan.get("overall_gap_score", 0),
            "status": "proposed",
            "proposed_at": datetime.now().isoformat(),
            "executed_at": None,
            "outcome": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Wave Engine (main controller)
# ──────────────────────────────────────────────────────────────────────────────

class WaveEngine:
    """
    Autonomous Wave Evolution Engine.
    Runs a 24h loop: scan → propose → store → (optionally) execute.
    """

    def __init__(self):
        self.scanner = GapScanner()
        self.proposer = WaveProposer()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def run_cycle(self) -> Dict:
        """Run one full scan-propose cycle. Returns the new wave proposal."""
        print("[WaveEngine] Running gap scan...", flush=True)
        scan = self.scanner.scan()
        proposal = self.proposer.propose(scan)

        waves = _load_waves()
        waves.append(proposal)
        _save_waves(waves)
        _log("wave_proposed", {"wave": proposal["title"], "trigger": proposal["trigger_category"]})

        # Update status
        self._update_status({
            "last_cycle": datetime.now().isoformat(),
            "total_waves": len(waves),
            "last_wave": proposal["title"],
            "last_gap_score": scan["overall_gap_score"],
            "last_gaps": [g["description"][:80] for g in scan["gaps"][:3]],
        })

        print(f"[WaveEngine] Proposed: {proposal['title']}", flush=True)
        return {"scan": scan, "proposal": proposal}

    def get_latest_proposal(self) -> Optional[Dict]:
        waves = _load_waves()
        if not waves:
            return None
        return waves[-1]

    def get_all_waves(self) -> List[Dict]:
        return _load_waves()

    def mark_wave_executed(self, wave_number: int, outcome: str = "completed"):
        waves = _load_waves()
        for w in waves:
            if w.get("wave_number") == wave_number:
                w["status"] = "executed"
                w["executed_at"] = datetime.now().isoformat()
                w["outcome"] = outcome
                break
        _save_waves(waves)
        _log("wave_executed", {"wave_number": wave_number, "outcome": outcome})

    def get_status(self) -> Dict:
        status = {}
        if STATUS_FILE.exists():
            try:
                status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        status["running"] = self._running
        waves = _load_waves()
        status["total_waves"] = len(waves)
        status["proposed"] = sum(1 for w in waves if w.get("status") == "proposed")
        status["executed"] = sum(1 for w in waves if w.get("status") == "executed")
        return status

    def _update_status(self, data: Dict):
        STATUS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def start_daemon(self, interval_hours: int = 24):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, args=(interval_hours,), daemon=True)
        self._thread.start()
        print(f"[WaveEngine] Daemon started (interval: {interval_hours}h)", flush=True)

    def stop_daemon(self):
        self._running = False

    def _loop(self, interval_hours: int):
        # Run immediately on start if no recent cycle
        try:
            status = self.get_status()
            last = status.get("last_cycle")
            if not last or (datetime.now() - datetime.fromisoformat(last)).total_seconds() > interval_hours * 3600 * 0.9:
                self.run_cycle()
        except Exception as e:
            print(f"[WaveEngine] Initial cycle error: {e}", flush=True)

        while self._running:
            sleep_secs = interval_hours * 3600
            for _ in range(int(sleep_secs / 60)):
                if not self._running:
                    break
                time.sleep(60)
            if self._running:
                try:
                    self.run_cycle()
                except Exception as e:
                    print(f"[WaveEngine] Cycle error: {e}", flush=True)


# Singleton
_engine: Optional[WaveEngine] = None


def get_wave_engine() -> WaveEngine:
    global _engine
    if _engine is None:
        _engine = WaveEngine()
    return _engine
