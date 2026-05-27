"""
Proactive Heartbeat - Background Intelligence
Runs every 15 minutes to scan for life triggers and nudge the user.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from core.settings import get_settings
from core.memory import save_log

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

SETTINGS = get_settings()


@dataclass
class TriggerEvent:
    """A detected trigger that needs user attention."""
    source: str  # 'finance', 'learning', 'guardian', 'wellness'
    trigger_type: str
    severity: str  # 'critical', 'warning', 'info', 'celebration'
    message: str
    action_suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ProactiveHeartbeat:
    """
    Background intelligence that proactively nudges the user.
    Runs on a 15-minute cycle, scanning all domains for triggers.
    """
    
    def __init__(self, interval_minutes: int = 15):
        self.interval = interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None
        self.last_triggers: Dict[str, datetime] = {}
        self._callbacks: List[Any] = []  # Notification callbacks
    
    def register_callback(self, callback):
        """Register a notification callback (e.g., TTS, PWA push)."""
        self._callbacks.append(callback)
    
    def start(self):
        """Start the heartbeat thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        # Defer ChromaDB log write to background so start() returns immediately
        def _log_start():
            try:
                save_log('heartbeat', {
                    'event': 'heartbeat_started',
                    'interval_minutes': self.interval // 60
                })
            except Exception:
                pass
        threading.Thread(target=_log_start, daemon=True).start()
        print(f"[Heartbeat] Proactive intelligence started ({self.interval // 60}min interval)")
    
    def stop(self):
        """Stop the heartbeat thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[Heartbeat] Proactive intelligence stopped")
    
    def _run_loop(self):
        """Main heartbeat loop."""
        while self.running:
            try:
                self._scan_cycle()
            except Exception as e:
                print(f"[Heartbeat] Scan error: {e}")
            
            # Sleep in chunks to allow quick shutdown
            slept = 0
            while slept < self.interval and self.running:
                time.sleep(5)
                slept += 5
    
    def _scan_cycle(self):
        """Run one full scan cycle across all domains."""
        triggers = []

        # Scan each domain
        triggers.extend(self._scan_finance())
        triggers.extend(self._scan_learning())
        triggers.extend(self._scan_guardian())
        triggers.extend(self._scan_wellness())
        triggers.extend(self._scan_fitness())
        triggers.extend(self._scan_tasks())
        triggers.extend(self._scan_life_domains())
        triggers.extend(self._scan_memory_consolidation())
        triggers.extend(self._scan_dream_engine())

        # Jarvis-level proactive scans from context engine
        triggers.extend(self._scan_context_engine())

        # AGI-Level background processing
        self._scan_agi_systems()

        # Weekly self-improvement proposal
        self._maybe_self_improve()

        # Self-healing check - monitor for errors and attempt auto-heal
        try:
            from core.self_healing import monitor_and_autoheal, detect_and_fix_error
            alert = monitor_and_autoheal()
            if alert:
                print(f"[Self-Healing] {alert}")
                # Also log the error for tracking
                detect_and_fix_error(alert)
        except Exception:
            pass

        # Deduplicate and filter (focus-aware, Wave 27)
        active_triggers = self._filter_triggers(triggers)

        # Deliver previously-suppressed triggers if focus mode ended
        if not self._is_focus_mode():
            queued = self._deliver_suppressed()
            if queued:
                print(f"[Heartbeat] Delivering {len(queued)} queued trigger(s) from focus mode")
                active_triggers.extend(queued)

        # Notify for each trigger
        for trigger in active_triggers:
            self._notify(trigger)

        if active_triggers:
            print(f"[Heartbeat] {len(active_triggers)} trigger(s) detected")
    
    def _scan_finance(self) -> List[TriggerEvent]:
        """Scan for finance triggers."""
        triggers = []
        
        try:
            # Check for significant market moves
            # This would integrate with actual price APIs
            # For now, placeholder logic
            pass
        except Exception:
            pass
        
        return triggers
    
    def _scan_learning(self) -> List[TriggerEvent]:
        """Scan for learning triggers."""
        triggers = []
        
        try:
            from agents.learning_agent import LearningAgent
            agent = LearningAgent()
            due_reviews = agent.get_due_reviews()
            
            if len(due_reviews) >= 5:
                triggers.append(TriggerEvent(
                    source='learning',
                    trigger_type='reviews_due',
                    severity='info',
                    message=f"{len(due_reviews)} flashcards due for review. Spaced repetition waiting.",
                    action_suggestion='Take 5 minutes for flashcard review',
                    metadata={'count': len(due_reviews)}
                ))
        except Exception:
            pass
        
        return triggers
    
    def _scan_guardian(self) -> List[TriggerEvent]:
        """Scan for work/guardian triggers."""
        triggers = []
        
        try:
            from tools.guardian import check_work_status
            status = check_work_status()
            
            hours_today = status.get('hours_today', 0)
            limit = SETTINGS.work.daily_limit_hours
            
            # 30 min warning before limit
            if limit - hours_today <= 0.5 and hours_today < limit:
                if not self._recently_triggered('guardian_limit_warning'):
                    triggers.append(TriggerEvent(
                        source='guardian',
                        trigger_type='limit_approaching',
                        severity='warning',
                        message=f"30 minutes left in your {limit}-hour work day. Start wrapping up.",
                        action_suggestion='Finish current task, commit code, prepare for shutdown'
                    ))
            
            # At limit
            if hours_today >= limit:
                if not self._recently_triggered('guardian_limit_reached'):
                    triggers.append(TriggerEvent(
                        source='guardian',
                        trigger_type='limit_reached',
                        severity='critical',
                        message=f"Work limit reached ({hours_today:.1f}h). Time to clock out.",
                        action_suggestion='Save work, commit, step away from screen'
                    ))
            
            # 2+ hours without break
            if hours_today > 2:
                if not self._recently_triggered('guardian_break_needed'):
                    triggers.append(TriggerEvent(
                        source='guardian',
                        trigger_type='break_needed',
                        severity='info',
                        message=f"You've been working for {hours_today:.1f} hours. Take a 5-min stretch break.",
                        action_suggestion='Stand up, stretch, look away from screen'
                    ))
        except Exception:
            pass
        
        return triggers
    
    def _scan_wellness(self) -> List[TriggerEvent]:
        """Scan for wellness triggers including emotional state."""
        triggers = []

        try:
            from core.emotional import get_emotional_summary
            from agents.emotional_agent import EmotionalAgent
            agent = EmotionalAgent()

            # Check if mood hasn't been logged for 6+ hours
            data = agent._load_data()
            if data.get('mood_entries'):
                last_entry = data['mood_entries'][-1]
                last_time = datetime.fromisoformat(last_entry['timestamp'])
                hours_since = (datetime.now() - last_time).total_seconds() / 3600

                if hours_since >= 6 and not self._recently_triggered('wellness_checkin'):
                    triggers.append(TriggerEvent(
                        source='wellness',
                        trigger_type='mood_checkin',
                        severity='info',
                        message=f"Haven't checked in for {int(hours_since)} hours. Quick mood check?",
                        action_suggestion='Log your current mood and energy level'
                    ))

            # Check stress trends from core emotional module
            summary = get_emotional_summary(days=3)
            current_stress = summary.get("current_stress", 0)
            trend = summary.get("trend", "stable")
            dominant = summary.get("dominant_mood", "neutral")

            # High stress alert
            if current_stress > 70 and trend == "rising" and not self._recently_triggered('wellness_stress_alert', cooldown_minutes=120):
                triggers.append(TriggerEvent(
                    source='wellness',
                    trigger_type='stress_rising',
                    severity='warning',
                    message=f"Your stress level is climbing — {current_stress:.0f}/100 and rising. Something's building up.",
                    action_suggestion='Take 2 minutes to breathe, or tell me what is on your mind'
                ))

            # Crisis level stress
            if current_stress > 85 and not self._recently_triggered('wellness_crisis', cooldown_minutes=180):
                triggers.append(TriggerEvent(
                    source='wellness',
                    trigger_type='stress_crisis',
                    severity='critical',
                    message=f"Your stress is at {current_stress:.0f}/100. This is serious. You need to step back right now.",
                    action_suggestion='Close your eyes for 60 seconds. Walk away from the screen.'
                ))

            # Proactive celebration for positive streak
            if dominant in {"joyful", "accomplished", "grateful", "relaxed"} and not self._recently_triggered('wellness_positive', cooldown_minutes=240):
                triggers.append(TriggerEvent(
                    source='wellness',
                    trigger_type='positive_streak',
                    severity='celebration',
                    message=f"You've been feeling {dominant}. That's worth noticing. Good energy right now.",
                    action_suggestion='Channel this momentum into something meaningful'
                ))

        except Exception:
            pass

        return triggers
    
    def _scan_fitness(self) -> List[TriggerEvent]:
        """Scan for fitness triggers."""
        triggers = []
        
        try:
            from agents.fitness_agent import FitnessAgent
            agent = FitnessAgent()
            summary = agent.get_weekly_summary()
            
            # No workouts for 3+ days
            if summary.get('workouts_this_week', 0) == 0:
                if not self._recently_triggered('fitness_inactive'):
                    triggers.append(TriggerEvent(
                        source='fitness',
                        trigger_type='no_workouts',
                        severity='warning',
                        message="No workouts this week. Body needs movement to support your mind.",
                        action_suggestion='10-minute walk, 5 pushups, anything to start'
                    ))
        except Exception:
            pass
        
        return triggers
    
    def _scan_tasks(self) -> List[TriggerEvent]:
        """Scan for task triggers."""
        triggers = []
        
        try:
            from agents.task_agent import TaskAgent
            agent = TaskAgent()
            overview = agent.get_task_overview()
            
            # Due soon tasks
            due_soon = overview.get('due_soon', [])
            critical_due = [t for t in due_soon if isinstance(t, dict) and t.get('priority') == 'critical']
            
            if critical_due:
                if not self._recently_triggered('tasks_critical_due'):
                    triggers.append(TriggerEvent(
                        source='tasks',
                        trigger_type='critical_deadline',
                        severity='warning',
                        message=f"'{critical_due[0].get('title', 'Task')}' is due soon and marked critical.",
                        action_suggestion='Focus on this task now, block distractions'
                    ))
        except Exception:
            pass
        
        return triggers

    def _scan_life_domains(self) -> List[TriggerEvent]:
        """Scan life domains via Life Coach for time-aware, context-aware nudges."""
        triggers = []
        try:
            from core.life_coach import get_life_coach
            coach = get_life_coach()
            nudges = coach.get_nudges()
            severity_map = {"high": "warning", "medium": "info", "low": "info"}
            for nudge in nudges:
                key = f"life_coach_{nudge.get('type', 'generic')}_{nudge.get('domain', '')}"
                cooldown = 120 if nudge.get("priority") == "high" else 180
                if not self._recently_triggered(key, cooldown_minutes=cooldown):
                    triggers.append(TriggerEvent(
                        source='life_domains',
                        trigger_type=nudge.get("type", "nudge"),
                        severity=severity_map.get(nudge.get("priority", "low"), "info"),
                        message=nudge.get("message", ""),
                        action_suggestion=nudge.get("action", "Check the Life panel")
                    ))
        except Exception as e:
            print(f"[Heartbeat] Life coach scan error: {e}")
        return triggers

    def _maybe_self_improve(self):
        """Once per week, LOVE proposes its own next improvement autonomously."""
        try:
            from pathlib import Path as _P
            import json as _json, datetime as _dt
            marker = _P("data/last_self_improve.txt")
            now = _dt.datetime.now()
            if marker.exists():
                last = _dt.datetime.fromisoformat(marker.read_text().strip())
                if (now - last).days < 7:
                    return
            # Trigger improvement proposal in background (non-blocking)
            import threading, requests as _req
            def _run():
                try:
                    _req.post("http://127.0.0.1:8000/self-improve", timeout=120)
                    marker.write_text(now.isoformat())
                    print("[LOVE] 🧬 Weekly self-improvement proposal submitted", flush=True)
                except Exception as e:
                    print(f"[LOVE] Self-improve failed: {e}", flush=True)
            threading.Thread(target=_run, daemon=True).start()
        except Exception:
            pass

    def _scan_memory_consolidation(self) -> List[TriggerEvent]:
        """Check if nightly memory consolidation should run."""
        triggers = []
        try:
            from core.memory_consolidation import should_run_consolidation, consolidate_period
            if should_run_consolidation():
                result = consolidate_period(hours=24)
                created = result.get("created", 0)
                if created > 0:
                    triggers.append(TriggerEvent(
                        source="memory",
                        trigger_type="consolidation_complete",
                        severity="celebration",
                        message=f"✨ Dreamed about the day — {created} new memories stored for life.",
                        action_suggestion="Review your Life timeline",
                        metadata=result,
                    ))
        except Exception:
            pass
        return triggers

    def _scan_dream_engine(self) -> List[TriggerEvent]:
        """Trigger deep dream processing during idle periods."""
        triggers = []
        try:
            from core.dream_engine import run_dream, get_active_predictions
            from core.idle_mind import is_idle

            # Only run dream if idle for a while or it's late night
            hour = datetime.now().hour
            is_late = hour >= 23 or hour <= 5

            if is_idle() or is_late:
                result = run_dream()
                insights = result.get("insights", [])
                predictions = result.get("predictions", [])

                if insights or predictions:
                    triggers.append(TriggerEvent(
                        source="dream",
                        trigger_type="deep_insight",
                        severity="info",
                        message=f"I spent time thinking about you. Found {len(insights)} insights and {len(predictions)} patterns.",
                        action_suggestion="Ask me what I learned",
                        metadata={"insights": len(insights), "predictions": len(predictions)},
                    ))
        except Exception:
            pass
        return triggers

    def _scan_prediction_market(self) -> List[TriggerEvent]:
        """Auto-generate predictions from world model and expire old ones."""
        triggers = []
        try:
            from core.prediction_market import auto_resolve_expired, generate_predictions_from_world
            from core.dream_engine import get_world_model

            # Clean up expired predictions
            auto_resolve_expired()

            # Generate new predictions from world model
            world = get_world_model()
            new_preds = generate_predictions_from_world(world)

            if new_preds and not self._recently_triggered('prediction_generated', minutes=60):
                triggers.append(TriggerEvent(
                    source="prediction",
                    trigger_type="new_prediction",
                    severity="info",
                    message=f"I made {len(new_preds)} new prediction(s) about you based on patterns I've noticed.",
                    action_suggestion="Ask me what I'm predicting",
                    metadata={"count": len(new_preds)},
                ))
        except Exception:
            pass
        return triggers

    def _scan_context_engine(self) -> List[TriggerEvent]:
        """Jarvis-level proactive scans: calendar, phone, battery, environment."""
        triggers = []
        try:
            from core.context_engine import get_live_context
            from core.autonomous import maybe_send_autonomous_message
            
            ctx = get_live_context()
            
            if not ctx:
                return triggers
            
            # Battery critical
            if ctx.battery is not None and ctx.battery < 20:
                triggers.append(TriggerEvent(
                    source="context",
                    trigger_type="battery_critical",
                    severity="critical",
                    message=f"Low battery: {ctx.battery}%",
                    action_suggestion="Plug in or save work",
                    metadata={"battery": ctx.battery},
                ))
            
            # Phone battery critical
            if ctx.phone_battery is not None and ctx.phone_battery < 20:
                triggers.append(TriggerEvent(
                    source="context",
                    trigger_type="phone_battery_critical",
                    severity="warning",
                    message=f"Phone battery low: {ctx.phone_battery}%",
                    action_suggestion="Charge phone",
                    metadata={"phone_battery": ctx.phone_battery},
                ))
        except Exception as e:
            print(f"[Heartbeat] Context scan error: {e}")
        
        return triggers

    def _scan_agi_systems(self):
        """Run AGI-level background processing: autonomous goals, predictions, learning."""
        try:
            # Autonomous agent - generate proactive goals
            try:
                from core.autonomous_agent import get_autonomous_agent
                agent = get_autonomous_agent()
                if agent:
                    # Generate autonomous goals based on current context
                    goal_ids = agent.generate_autonomous_goals()
                    if goal_ids:
                        print(f"[AGI] Generated {len(goal_ids)} autonomous goals")
                        # Send notification about new goals
                        self._notify_agi_goals(goal_ids)
            except Exception as e:
                print(f"[AGI] Autonomous agent error: {e}")
            
            # Predictive intelligence - generate predictions and proactive notifications
            try:
                from core.predictive_intelligence import get_predictive_engine
                engine = get_predictive_engine()
                if engine:
                    predictions = engine.generate_predictions()
                    if predictions:
                        print(f"[AGI] Generated {len(predictions)} predictions")
                        # Send proactive notifications based on predictions
                        self._notify_predictions(predictions)
                    
                    # Anticipate needs and suggest proactive actions
                    needs = engine.anticipate_needs({})
                    if needs:
                        self._notify_proactive_needs(needs)
            except Exception as e:
                print(f"[AGI] Predictive intelligence error: {e}")
            
            # Meta-cognition - reflect on current state
            try:
                from core.meta_cognition import get_meta_cognition_engine
                meta = get_meta_cognition_engine()
                if meta:
                    # Monitor cognitive state
                    state = meta.monitor_cognitive_state()
                    # Record a reflection thought
                    meta.record_thought(
                        thought_type="reflection",
                        content="Periodic cognitive state check during heartbeat scan",
                        confidence=0.7
                    )
            except Exception as e:
                print(f"[AGI] Meta-cognition error: {e}")
            
            # Continuous learning - integrate recent learnings
            try:
                from core.continuous_learning import get_continuous_learning_engine
                learning = get_continuous_learning_engine()
                if learning:
                    # Apply any pending learnings
                    learning.consolidate_learnings()
            except Exception as e:
                print(f"[AGI] Continuous learning error: {e}")
            
            # Strategic planning - update weekly strategy
            try:
                from core.strategic_planning import get_strategic_planner
                planner = get_strategic_planner()
                if planner:
                    # Update progress on existing plans
                    plans = planner.get_all_plans()
                    for plan in plans:
                        planner.update_progress(plan["id"], "progressing")
            except Exception as e:
                print(f"[AGI] Strategic planning error: {e}")
            
            # Psychological model - update profile from context
            try:
                from core.psychological_model import get_psychological_model
                psych = get_psychological_model()
                if psych:
                    # The psychological model updates through conversation analysis
                    # This is just a placeholder for potential background updates
                    pass
            except Exception as e:
                print(f"[AGI] Psychological model error: {e}")
            
        except Exception as e:
            print(f"[Heartbeat] AGI scan error: {e}")

    def _notify_agi_goals(self, goal_ids):
        """Send notification about new autonomous goals."""
        try:
            from core.autonomous_agent import get_autonomous_agent
            agent = get_autonomous_agent()
            goals = []
            for goal_id in goal_ids:
                status = agent.get_goal_status(goal_id)
                if status:
                    goals.append(f"- {status['title']} ({status['priority']})")
            
            if goals:
                notification = TriggerEvent(
                    source="agi",
                    trigger_type="autonomous_goals",
                    severity="info",
                    message=f"LOVE set {len(goal_ids)} autonomous goals",
                    action_suggestion="Review goals in AGI panel",
                    metadata={"goals": goal_ids}
                )
                self._notify(notification)
                print(f"[AGI Notification] Autonomous goals: {'; '.join(goals[:2])}")
        except Exception as e:
            print(f"[Heartbeat] Error notifying AGI goals: {e}")

    def _notify_predictions(self, predictions):
        """Send proactive notifications based on predictions."""
        try:
            # Only notify high-impact or high-confidence predictions
            high_priority = [p for p in predictions if p.impact in ["critical", "high"] or p.confidence > 0.7]
            
            for prediction in high_priority[:2]:  # Limit to top 2
                notification = TriggerEvent(
                    source="agi",
                    trigger_type="prediction",
                    severity="info" if prediction.confidence < 0.8 else "warning",
                    message=f"Prediction: {prediction.description}",
                    action_suggestion=prediction.suggested_actions[0] if prediction.suggested_actions else "Monitor",
                    metadata={
                        "prediction_id": prediction.id,
                        "confidence": prediction.confidence,
                        "timeframe": prediction.timeframe
                    }
                )
                self._notify(notification)
                print(f"[AGI Notification] Prediction: {prediction.description}")
        except Exception as e:
            print(f"[Heartbeat] Error notifying predictions: {e}")

    def _notify_proactive_needs(self, needs):
        """Send proactive notifications about anticipated needs."""
        try:
            # Only notify high-urgency needs
            high_urgency = [n for n in needs if n.get("urgency") == "high"]
            
            for need in high_urgency[:2]:  # Limit to top 2
                notification = TriggerEvent(
                    source="agi",
                    trigger_type="proactive_need",
                    severity="info",
                    message=f"Anticipated need: {need.get('description')}",
                    action_suggestion=need.get("suggested_action", "Review"),
                    metadata={"need_type": need.get("type")}
                )
                self._notify(notification)
                print(f"[AGI Notification] Proactive need: {need.get('description')}")
        except Exception as e:
            print(f"[Heartbeat] Error notifying proactive needs: {e}")
    
    def _recently_triggered(self, key: str, cooldown_minutes: int = 60) -> bool:
        """Check if this trigger was recently fired."""
        if key not in self.last_triggers:
            return False
        
        elapsed = (datetime.now() - self.last_triggers[key]).total_seconds() / 60
        return elapsed < cooldown_minutes
    
    def _is_focus_mode(self) -> bool:
        """Check if user is currently in a focus/deep work session (Wave 27)."""
        try:
            from pathlib import Path as _P
            import json as _json
            focus_file = _P(__file__).parent.parent / "data" / "focus_session.json"
            if focus_file.exists():
                data = _json.loads(focus_file.read_text(encoding="utf-8"))
                if data.get("active", False):
                    started = data.get("started_at", 0)
                    if time.time() - started < 4 * 3600:
                        return True
        except Exception:
            pass
        try:
            from core.work_tracker import get_work_tracker
            tracker = get_work_tracker()
            status = tracker.get_status()
            if status.get("focus_active", False):
                return True
        except Exception:
            pass
        return False

    def _filter_triggers(self, triggers: List[TriggerEvent]) -> List[TriggerEvent]:
        """Filter triggers: respect cooldowns + suppress non-critical during focus (Wave 27)."""
        in_focus = self._is_focus_mode()
        suppressed = []
        active = []
        for trigger in triggers:
            key = f"{trigger.source}_{trigger.trigger_type}"

            if self._recently_triggered(key):
                continue

            # Focus mode gating: only critical/warning pass through
            if in_focus and trigger.severity not in ("critical", "warning"):
                suppressed.append(trigger)
                continue

            self.last_triggers[key] = datetime.now()
            active.append(trigger)

        if suppressed:
            self._queue_suppressed(suppressed)
            print(f"[Heartbeat] Focus mode: suppressed {len(suppressed)} non-critical trigger(s)")

        return active

    def _queue_suppressed(self, triggers: List[TriggerEvent]) -> None:
        """Store suppressed triggers for delivery after focus mode ends."""
        try:
            from pathlib import Path as _P
            import json as _json
            queue_file = _P(__file__).parent.parent / "data" / "suppressed_nudges.json"
            existing = []
            if queue_file.exists():
                try:
                    existing = _json.loads(queue_file.read_text(encoding="utf-8"))
                except Exception:
                    existing = []
            for t in triggers:
                existing.append({
                    "source": t.source, "trigger_type": t.trigger_type,
                    "severity": t.severity, "message": t.message,
                    "action_suggestion": t.action_suggestion,
                    "suppressed_at": datetime.now().isoformat(),
                })
            existing = existing[-20:]
            queue_file.write_text(_json.dumps(existing, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _deliver_suppressed(self) -> List[TriggerEvent]:
        """Deliver queued triggers when focus mode ends."""
        try:
            from pathlib import Path as _P
            import json as _json
            queue_file = _P(__file__).parent.parent / "data" / "suppressed_nudges.json"
            if not queue_file.exists():
                return []
            queued = _json.loads(queue_file.read_text(encoding="utf-8"))
            if not queued:
                return []
            triggers = []
            for item in queued:
                triggers.append(TriggerEvent(
                    source=item["source"], trigger_type=item["trigger_type"],
                    severity=item["severity"],
                    message=f"[queued] {item['message']}",
                    action_suggestion=item.get("action_suggestion"),
                ))
            queue_file.write_text("[]", encoding="utf-8")
            return triggers
        except Exception:
            return []
    
    def _notify(self, trigger: TriggerEvent):
        """Send notification through all registered channels."""
        # Log the trigger
        save_log('heartbeat', {
            'event': 'trigger_fired',
            'source': trigger.source,
            'type': trigger.trigger_type,
            'severity': trigger.severity,
            'message': trigger.message
        })

        # Publish to neural bus for cross-module awareness
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                priority_map = {
                    "critical": EventPriority.CRITICAL,
                    "warning": EventPriority.HIGH,
                    "info": EventPriority.NORMAL,
                    "celebration": EventPriority.NORMAL
                }
                bus.publish(
                    domain="heartbeat",
                    event_type="trigger_fired",
                    payload={
                        "source": trigger.source,
                        "trigger_type": trigger.trigger_type,
                        "severity": trigger.severity,
                        "message": trigger.message,
                        "action_suggestion": trigger.action_suggestion,
                        "metadata": trigger.metadata
                    },
                    source_module="heartbeat",
                    priority=priority_map.get(trigger.severity, EventPriority.NORMAL)
                )
            except Exception as e:
                print(f"[Heartbeat] Neural bus publish error: {e}")

        # Call registered notification callbacks
        for callback in self._callbacks:
            try:
                callback(trigger)
            except Exception as e:
                print(f"[Heartbeat] Callback error: {e}")

        # Speak aloud for warning/critical/celebration
        if trigger.severity in {"warning", "critical", "celebration"}:
            try:
                from core.voice_loop import speak_proactive_alert
                speak_proactive_alert(trigger.message, trigger.severity)
            except Exception:
                pass

        # Print to console
        icon = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️',
            'celebration': '🎉'
        }.get(trigger.severity, '•')

        print(f"[Heartbeat] {icon} [{trigger.source.upper()}] {trigger.message}")
        
        # For autonomous initiatives, also trigger a chat notification
        if trigger.source == "autonomous" and trigger.trigger_type == "initiative":
            try:
                from core.agent import chat
                # Send as a proactive message to the user
                print(f"[Heartbeat] Autonomous initiative: {trigger.message}")
            except Exception:
                pass


# Singleton instance
_heartbeat = None

def get_heartbeat() -> ProactiveHeartbeat:
    """Get singleton heartbeat instance."""
    global _heartbeat
    if _heartbeat is None:
        _heartbeat = ProactiveHeartbeat(interval_minutes=15)
    return _heartbeat


def start_heartbeat():
    """Start the proactive heartbeat."""
    hb = get_heartbeat()
    hb.start()
    return hb


def stop_heartbeat():
    """Stop the proactive heartbeat."""
    hb = get_heartbeat()
    hb.stop()


def add_notification_callback(callback):
    """Add a notification callback (e.g., TTS, push notification)."""
    hb = get_heartbeat()
    hb.register_callback(callback)
