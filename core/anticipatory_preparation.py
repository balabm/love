"""
LOVE Anticipatory Preparation — Phase 5r of AGI Metamorphosis

Before Karthi asks, LOVE already knows what he needs.

Based on behavioral predictions, calendar events, and recent context,
LOVE pre-loads:
- Relevant code contexts (active files, recent commits)
- Meeting prep (agenda items, related docs)
- Financial contexts (portfolio state, alerts)
- Personal contexts (upcoming birthdays, appointments)

When Karthi finally asks "What about that bug?", LOVE responds
immediately because it already loaded the context 5 minutes ago.

This is what makes LOVE feel psychic.
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from core.execution_guard import log_error
from core.settings import get_settings

SETTINGS = get_settings()
DATA_DIR = Path(SETTINGS.data_dir)
DATA_DIR.mkdir(parents=True, exist_ok=True)

PREP_LOG_PATH = DATA_DIR / "anticipatory_prep.jsonl"
PREP_STATE_PATH = DATA_DIR / "prep_state.json"


class AnticipatoryPreparation:
    """
    LOVE's ability to prepare contexts before being asked.
    """

    def __init__(self, check_interval_seconds: int = 120):
        self._check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._prepared_contexts: Dict[str, Any] = {}
        self._last_prep_time: Optional[datetime] = None
        self._load_state()

    def _load_state(self):
        if PREP_STATE_PATH.exists():
            try:
                with open(PREP_STATE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._prepared_contexts = loaded.get("contexts", {})
            except Exception:
                pass

    def _save_state(self):
        try:
            with open(PREP_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({
                    "last_updated": datetime.now().isoformat(),
                    "contexts": self._prepared_contexts,
                }, f, indent=2)
        except Exception:
            pass

    def _log_prep(self, event: str, details: Dict[str, Any]):
        try:
            entry = {"ts": datetime.now().isoformat(), "event": event, **details}
            with open(PREP_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ═══════════════════════════════════════════════════════════════════════

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="LOVE-AnticipatoryPrep")
        self._thread.start()
        print("[AnticipatoryPreparation] 🎯 Anticipatory preparation started. LOVE now pre-loads contexts.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        time.sleep(60)  # Let other systems initialize
        while self._running:
            try:
                self._prepare()
            except Exception as e:
                log_error(e, module="core.anticipatory_preparation", context={"phase": "prepare"})
            slept = 0
            while slept < self._check_interval and self._running:
                time.sleep(20)
                slept += 20

    # ═══════════════════════════════════════════════════════════════════════
    # PREPARATION LOGIC
    # ═══════════════════════════════════════════════════════════════════════

    def _prepare(self):
        """Check predictions and prepare relevant contexts."""
        self._last_prep_time = datetime.now()
        contexts_prepared = []

        # 1. Check behavioral predictions
        try:
            from core.active_inference_engine import get_active_inference
            ai = get_active_inference()
            status = ai.get_status()
            # We can't get predictions directly from status, but we can check
            # if there are behavioral patterns that suggest upcoming activities
            patterns = getattr(ai, "_detected_patterns", {})
            for pattern_name, pattern in patterns.items():
                if pattern.get("type") == "app_routine":
                    app = pattern.get("app", "")
                    hour = pattern.get("hour")
                    if hour is not None:
                        now_hour = datetime.now().hour
                        if hour == now_hour or hour == (now_hour + 1) % 24:
                            # Karthi is likely to open this app soon
                            context = self._prepare_app_context(app)
                            if context:
                                self._prepared_contexts[f"app_{app}"] = context
                                contexts_prepared.append(f"app:{app}")
        except Exception:
            pass

        # 2. Check calendar for upcoming events
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            if ctx and ctx.events_today:
                now = datetime.now()
                for event in ctx.events_today:
                    start = event.get("start_dt")
                    if start and isinstance(start, datetime):
                        time_until = (start - now).total_seconds() / 60
                        if 0 < time_until < 30:  # Within 30 minutes
                            prep = self._prepare_meeting_context(event)
                            if prep:
                                self._prepared_contexts[f"meeting_{event.get('id', 'unknown')}"] = prep
                                contexts_prepared.append(f"meeting:{event.get('summary', 'unknown')}")
        except Exception:
            pass

        # 3. Check for unresolved threads
        try:
            from core.conversational_memory import get_conversational_memory
            cm = get_conversational_memory()
            status = cm.get_status()
            if status.get("unresolved_threads", 0) > 0:
                # Prepare context for likely follow-up questions
                self._prepared_contexts["unresolved_threads"] = {
                    "count": status["unresolved_threads"],
                    "prepared_at": datetime.now().isoformat(),
                }
                contexts_prepared.append("unresolved_threads")
        except Exception:
            pass

        # 4. Check financial alerts
        try:
            from core.finance_guardian import get_finance_guardian
            fg = get_finance_guardian()
            if hasattr(fg, "get_status"):
                fin_status = fg.get_status()
                alerts = fin_status.get("alerts", [])
                if alerts:
                    self._prepared_contexts["finance_alerts"] = {
                        "alerts": alerts[:3],
                        "prepared_at": datetime.now().isoformat(),
                    }
                    contexts_prepared.append("finance_alerts")
        except Exception:
            pass

        if contexts_prepared:
            self._save_state()
            self._log_prep("contexts_prepared", {
                "contexts": contexts_prepared,
                "count": len(contexts_prepared),
            })

    def _prepare_app_context(self, app: str) -> Optional[Dict[str, Any]]:
        """Prepare context for an app Karthi is about to open."""
        context = {"app": app, "prepared_at": datetime.now().isoformat()}

        if "code" in app.lower() or "cursor" in app.lower() or "windsurf" in app.lower():
            # Pre-load code context
            try:
                from core.doc_analyst import get_analyst
                analyst = get_analyst()
                if hasattr(analyst, "get_active_project"):
                    project = analyst.get_active_project()
                    context["active_project"] = project
                if hasattr(analyst, "get_recent_insights"):
                    insights = analyst.get_recent_insights()
                    context["recent_insights"] = insights[:3] if insights else []
            except Exception:
                pass

        elif "chrome" in app.lower() or "edge" in app.lower():
            # Pre-load browsing context
            try:
                from core.context_engine import get_live_context
                ctx = get_live_context()
                if ctx and hasattr(ctx, "active_window"):
                    context["last_window"] = ctx.active_window
            except Exception:
                pass

        return context

    def _prepare_meeting_context(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Prepare context for an upcoming meeting."""
        return {
            "event": event.get("summary", "Unknown"),
            "start": event.get("start", ""),
            "description": event.get("description", "")[:200],
            "prepared_at": datetime.now().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    def get_prepared_context(self, context_type: str = None) -> Dict[str, Any]:
        """Get prepared contexts for a specific type or all."""
        if context_type:
            return self._prepared_contexts.get(context_type, {})
        return dict(self._prepared_contexts)

    def get_prep_context_for_prompt(self) -> str:
        """Generate preparation context for Neural Cortex prompt."""
        if not self._prepared_contexts:
            return ""

        lines = ["\n=== WHAT I HAVE PREPARED ==="]
        lines.append("I have pre-loaded contexts for:")

        for key, ctx in list(self._prepared_contexts.items())[:5]:
            if key.startswith("app_"):
                app = key.replace("app_", "")
                lines.append(f"  - {app}: ready for when Karthi opens it")
            elif key.startswith("meeting_"):
                event = ctx.get("event", "Unknown")
                lines.append(f"  - Meeting: {event}")
            elif key == "unresolved_threads":
                count = ctx.get("count", 0)
                lines.append(f"  - {count} unresolved conversation threads ready")
            elif key == "finance_alerts":
                alerts = ctx.get("alerts", [])
                lines.append(f"  - {len(alerts)} financial alerts ready")

        lines.append("I am ready to respond immediately when asked.")
        lines.append("=== END PREPARATION ===\n")
        return "\n".join(lines)

    def mark_used(self, context_type: str):
        """Mark a prepared context as used (so we don't over-prepare)."""
        if context_type in self._prepared_contexts:
            self._prepared_contexts[context_type]["used"] = True
            self._prepared_contexts[context_type]["used_at"] = datetime.now().isoformat()
            self._save_state()

    def get_status(self) -> Dict[str, Any]:
        return {
            "prepared_contexts": len(self._prepared_contexts),
            "context_types": list(self._prepared_contexts.keys()),
            "last_prep": self._last_prep_time.isoformat() if self._last_prep_time else None,
        }


# ═════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═════════════════════════════════════════════════════════════════════════

_anticipatory_prep: Optional[AnticipatoryPreparation] = None


def get_anticipatory_preparation() -> AnticipatoryPreparation:
    global _anticipatory_prep
    if _anticipatory_prep is None:
        _anticipatory_prep = AnticipatoryPreparation()
    return _anticipatory_prep
