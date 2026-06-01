"""
LOVE Context Engine - fuses environment signals into live situational awareness.
"""
import os
import time
import threading
from datetime import datetime
from typing import Dict, Optional


class LiveContext:
    def __init__(self):
        self.active_app = ''
        self.active_window = ''
        self.activity = ''
        self.time_of_day = ''
        self.local_time = datetime.now().strftime('%I:%M %p')
        self.day_type = 'weekend' if datetime.now().weekday() >= 5 else 'weekday'
        self.system_cpu = 0.0
        self.system_ram = 0.0
        self.battery = None
        self.battery_charging = False
        self.network_up = True
        self.recent_files = []
        self.location = ''
        self.stress_level = 0.0
        self.energy_level = 0.0
        self.fitness_streak = 0
        self.sleep_hours_last_night = 0.0
        self.hydration_pct = 0.0
        self.meals_today = 0
        self.work_hours_today = 0.0
        self.focus_mode_active = False
        self.last_interaction = ''
        self.context_summary = ''
        self.proactive_alerts = []
        self.suggested_action = ''
        self.is_in_meeting = False
        self.next_event = None
        self.events_today = []
        self.urgent_emails = []
        self.unread_important = 0
        self.phone_connected = False
        self.tasks_overdue = 0
        self.tasks_due_today = 0
        self.hours_worked_today = 0.0
        self.stress_score = None
        self.mood_score = None
        self.energy_score = None
        self.learning_streak = 0
        self.active_project = ''
        self.phone_battery = None
        self.pc_battery = None

    def refresh(self):
        now = datetime.now()
        hour = now.hour
        self.local_time = now.strftime('%I:%M %p')
        self.day_type = 'weekend' if now.weekday() >= 5 else 'weekday'
        if 5 <= hour < 12:
            self.time_of_day = 'morning'
        elif 12 <= hour < 17:
            self.time_of_day = 'afternoon'
        elif 17 <= hour < 21:
            self.time_of_day = 'evening'
        else:
            self.time_of_day = 'night'
        try:
            import psutil
            self.system_cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            self.system_ram = round(mem.used / mem.total * 100, 1)
            if hasattr(psutil, 'sensors_battery'):
                bat = psutil.sensors_battery()
                if bat:
                    self.battery = int(bat.percent)
                    self.pc_battery = int(bat.percent)
                    self.battery_charging = bat.power_plugged
        except Exception:
            pass
        try:
            from core.browser_monitor import get_active_window_title
            self.active_window = get_active_window_title()
            self.active_app = self.active_window.split(' - ')[-1] if ' - ' in self.active_window else self.active_window
        except Exception:
            pass
        try:
            from core.life_domains import get_all_domain_stats
            stats = get_all_domain_stats()
            self.sleep_hours_last_night = stats.get('sleep', {}).get('last_night_hours', 0)
            self.hydration_pct = stats.get('hydration', {}).get('today_pct', 0)
            self.meals_today = stats.get('nutrition', {}).get('meals_today', 0)
        except Exception:
            pass
        try:
            from core.guardian import get_guardian_status
            g = get_guardian_status()
            self.work_hours_today = g.get('hours_today', 0)
            self.focus_mode_active = g.get('focus_mode', False)
        except Exception:
            pass
        try:
            from core.emotional_state import get_current_state
            emo = get_current_state()
            self.stress_level = emo.get('stress', 0)
            self.energy_level = emo.get('energy', 0)
        except Exception:
            pass
        parts = [
            f'It is {self.time_of_day} on a {self.day_type}.',
            f'System CPU: {self.system_cpu:.0f}%, RAM: {self.system_ram:.0f}%.',
        ]
        if self.battery is not None:
            charge_str = ' (charging)' if self.battery_charging else ''
            parts.append(f'Battery: {self.battery}%{charge_str}.')
        if self.active_app:
            parts.append(f'Active app: {self.active_app}.')
        if self.work_hours_today:
            parts.append(f'Work today: {self.work_hours_today:.1f}h.')
        if self.sleep_hours_last_night:
            parts.append(f'Sleep last night: {self.sleep_hours_last_night:.1f}h.')
        self.context_summary = ' '.join(parts)


_ctx = LiveContext()
_daemon_running = False
_daemon_thread = None


def start_context_engine(interval_seconds: int = 60):
    global _daemon_running, _daemon_thread
    if _daemon_running:
        return
    _daemon_running = True

    def _loop():
        while _daemon_running:
            try:
                _ctx.refresh()
            except Exception:
                pass
            for _ in range(interval_seconds):
                if not _daemon_running:
                    break
                time.sleep(1)

    _daemon_thread = threading.Thread(target=_loop, daemon=True, name='context-engine')
    _daemon_thread.start()
    try:
        _ctx.refresh()
    except Exception:
        pass


def stop_context_engine():
    global _daemon_running
    _daemon_running = False


def get_live_context() -> LiveContext:
    return _ctx


def get_prompt_context() -> str:
    """Get a rich human-readable context summary for LLM prompt injection.

    This is consumed by jarvis_protocol, agent.py, and tool_registry.
    """
    _ctx.refresh()
    parts = []
    if _ctx.context_summary:
        parts.append(_ctx.context_summary)
    if _ctx.active_app:
        parts.append(f"Currently using: {_ctx.active_app}")
    if _ctx.work_hours_today:
        parts.append(f"Work today: {_ctx.work_hours_today:.1f} hours")
    if _ctx.sleep_hours_last_night:
        parts.append(f"Sleep last night: {_ctx.sleep_hours_last_night:.1f} hours")
    if _ctx.stress_level:
        parts.append(f"Stress level: {_ctx.stress_level}")
    if _ctx.energy_level:
        parts.append(f"Energy level: {_ctx.energy_level}")
    return "\n".join(parts) if parts else "No live context available."


def get_context_dict() -> Dict:
    _ctx.refresh()
    return {
        'active_app': _ctx.active_app,
        'active_window': _ctx.active_window,
        'activity': _ctx.activity,
        'time_of_day': _ctx.time_of_day,
        'local_time': _ctx.local_time,
        'day_type': _ctx.day_type,
        'system_cpu': _ctx.system_cpu,
        'system_ram': _ctx.system_ram,
        'battery': _ctx.battery,
        'battery_charging': _ctx.battery_charging,
        'network_up': _ctx.network_up,
        'recent_files': _ctx.recent_files,
        'location': _ctx.location,
        'stress_level': _ctx.stress_level,
        'energy_level': _ctx.energy_level,
        'fitness_streak': _ctx.fitness_streak,
        'sleep_hours_last_night': _ctx.sleep_hours_last_night,
        'hydration_pct': _ctx.hydration_pct,
        'meals_today': _ctx.meals_today,
        'work_hours_today': _ctx.work_hours_today,
        'focus_mode_active': _ctx.focus_mode_active,
        'last_interaction': _ctx.last_interaction,
        'context_summary': _ctx.context_summary,
    }


def get_unified_prompt_context(user_input: str, mode: str = "general", injected_context: str = "") -> str:
    """Gather context from all subsystems intelligently, with consolidation to avoid truncation."""
    blocks = []
    
    # 1. Live Jarvis context
    live_context = get_prompt_context()
    if injected_context:
        live_context = f"{injected_context}\n\n{live_context}".strip()
    if live_context:
        blocks.append(f"=== WHAT I CURRENTLY KNOW ===\n{live_context}")

    # 2. Long-term memory
    try:
        from core.long_term_memory import remember, format_memory_for_chat
        ltm_result = remember(user_input, limit=3)
        ltm_text = format_memory_for_chat(ltm_result)
        if ltm_text:
            blocks.append(ltm_text)
    except Exception:
        pass

    # 3. User profile
    try:
        from agents.file_explorer import enrich_prompt_context
        profile_ctx = enrich_prompt_context()
        if profile_ctx:
            blocks.append(f"=== WHAT I KNOW ABOUT KARTHI ===\n{profile_ctx}")
    except Exception:
        pass

    # 4. AGI-Level Systems
    try:
        agi_context_parts = []
        from core.psychological_model import get_psychological_model
        pm = get_psychological_model()
        if pm:
            profile = pm.get_profile_summary()
            import json
            agi_context_parts.append(f"Psychological Profile: {json.dumps(profile, indent=2)[:200]}...")
        if agi_context_parts:
            blocks.append("=== AGI-LEVEL INSIGHTS ===\n" + "\n".join(agi_context_parts))
    except Exception:
        pass

    # 5. Web Search
    try:
        from core.internet import auto_search_for_query
        web_results = auto_search_for_query(user_input)
        if web_results:
            blocks.append(f"REAL-TIME WEB DATA:\n{web_results}")
    except Exception:
        pass

    # 6. Temporal Memory
    try:
        from core.temporal_memory import get_temporal_memory
        tmem = get_temporal_memory()
        temporal_ctx = tmem.get_temporal_context(query=user_input, limit=3)
        if temporal_ctx:
            blocks.append(f"=== MY AUTOBIOGRAPHICAL MEMORY ===\n{temporal_ctx}")
    except Exception:
        pass
        
    # 7. Intelligence Hub
    try:
        from core.intelligence_hub import get_intelligence_hub
        hub = get_intelligence_hub()
        intel_ctx = hub.get_context_for_prompt()
        if intel_ctx:
            blocks.append("=== LIVE INTELLIGENCE ===\n" + intel_ctx)
    except Exception:
        pass
        
    # 8. Agent Registry
    try:
        from core.agent_registry import get_agent_registry
        registry = get_agent_registry()
        agent_ctx = registry.get_all_context(user_input)
        if agent_ctx:
            blocks.append("=== LIVE LIFE CONTEXT ===\n" + agent_ctx)
    except Exception:
        pass
        
    # 9. Active Goals
    try:
        from core.autonomous_goal_engine import get_goal_status
        goal_status = get_goal_status()
        active_goals = goal_status.get("goals", [])
        if active_goals:
            goal_lines = [f"  • {g['title']} [{g['priority']}] {g['progress']:.0f}% done" for g in active_goals[:3]]
            blocks.append("=== ACTIVE GOALS ===\n" + "\n".join(goal_lines))
    except Exception:
        pass
        
    # Join and enforce a hard limit to avoid prompt truncation upstream
    unified = "\n\n".join(blocks)
    if len(unified) > 8000:
        return unified[:8000] + "\n...[context truncated]"
    return unified
