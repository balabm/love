"""
LOVE Home Maintenance Scheduler — Home Intelligence (Modern AI Pattern)

Most home maintenance is reactive (fix when broken). This scheduler:

1. MAINTENANCE TRACKING
   - Track all home systems (HVAC, plumbing, electrical, appliances, exterior)
   - Record maintenance history with dates, costs, and service providers
   - Log DIY vs professional work

2. PREDICTIVE SCHEDULING
   - Calculate optimal maintenance intervals based on usage
   - Predict when systems will need attention based on age and condition
   - Seasonal maintenance reminders (gutters, HVAC filters, winterization)

3. COST ANALYSIS
   - Track maintenance costs over time
   - Compare DIY vs professional costs
   - Identify which systems are most expensive to maintain

4. PROACTIVE ALERTS
   - Alert when maintenance is due
   - Suggest preventive actions before problems occur
   - Track warranty expiration dates

Architecture:
- record_maintenance(system, task, cost, provider): Log maintenance
- schedule_task(system, task, frequency): Schedule recurring maintenance
- get_maintenance_status(): Get system health overview
- get_cost_analysis(): Get maintenance cost insights
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "home_maintenance_scheduler"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAINTENANCE_LOG = DATA_DIR / "maintenance.jsonl"
SCHEDULE_DB = DATA_DIR / "schedule.json"
STATS_DB = DATA_DIR / "stats.json"


@dataclass
class MaintenanceRecord:
    """A maintenance record."""
    system: str = ""  # hvac, plumbing, electrical, appliance, exterior, interior, safety
    task: str = ""
    cost: float = 0.0
    provider: str = ""  # DIY or professional name
    condition_before: str = ""  # good, fair, poor, critical
    condition_after: str = ""
    time_spent_minutes: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


@dataclass
class ScheduledTask:
    """A scheduled maintenance task."""
    task_id: str = ""
    system: str = ""
    task: str = ""
    frequency_days: int = 90
    last_completed: Optional[str] = None
    next_due: str = ""
    priority: str = "medium"  # low, medium, high, critical
    estimated_cost: float = 0.0
    provider_preference: str = ""


class HomeMaintenanceScheduler:
    """
    Intelligent home maintenance scheduler with predictive capabilities.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._records: deque = deque(maxlen=500)
        self._schedule: Dict[str, ScheduledTask] = {}
        self._stats = {
            "total_records": 0,
            "total_cost": 0.0,
            "avg_cost": 0.0,
            "diy_pct": 0.0,
        }
        self._load_stats()
        self._load_schedule()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_maintenance(self, system: str = "", task: str = "", cost: float = 0, provider: str = "", condition_before: str = "", condition_after: str = "", time_spent: float = 0, notes: str = "") -> MaintenanceRecord:
        """Record a maintenance activity."""
        record = MaintenanceRecord(
            system=system or "general",
            task=task or "inspection",
            cost=cost,
            provider=provider or "DIY",
            condition_before=condition_before or "unknown",
            condition_after=condition_after or "unknown",
            time_spent_minutes=time_spent,
            notes=notes,
        )

        with self._lock:
            self._records.append(record)
            self._stats["total_records"] += 1
            self._stats["total_cost"] += cost
            self._update_stats(record)
            self._update_schedule(system, task)

        self._save_stats()
        self._log_record(record)

        return record

    def schedule_task(self, system: str, task: str, frequency_days: int = 90, priority: str = "medium", estimated_cost: float = 0, provider_preference: str = "") -> ScheduledTask:
        """Add a recurring maintenance task."""
        task_id = f"{system}_{task.replace(' ', '_').lower()}"
        next_due = (datetime.now() + timedelta(days=frequency_days)).isoformat()

        scheduled = ScheduledTask(
            task_id=task_id,
            system=system,
            task=task,
            frequency_days=frequency_days,
            next_due=next_due,
            priority=priority,
            estimated_cost=estimated_cost,
            provider_preference=provider_preference,
        )

        with self._lock:
            self._schedule[task_id] = scheduled

        self._save_schedule()
        return scheduled

    # ── Analysis ──────────────────────────────────────────────────────────

    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get system health overview."""
        # Group records by system
        system_records = defaultdict(list)
        for r in self._records:
            system_records[r.system].append(r)

        status = {}
        for system, records in system_records.items():
            if not records:
                continue

            # Latest condition
            latest = max(records, key=lambda x: x.timestamp)
            
            # Cost tracking
            total_cost = sum(r.cost for r in records)
            avg_cost = total_cost / len(records)
            
            # Frequency
            if len(records) >= 2:
                dates = sorted([datetime.fromisoformat(r.timestamp) for r in records])
                intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                avg_interval = sum(intervals) / len(intervals)
            else:
                avg_interval = 0

            # DIY vs professional
            diy_count = sum(1 for r in records if r.provider.upper() == "DIY")
            diy_pct = diy_count / len(records) * 100

            status[system] = {
                "latest_condition": latest.condition_after or latest.condition_before,
                "last_service": latest.timestamp,
                "total_records": len(records),
                "total_cost": round(total_cost, 2),
                "avg_cost": round(avg_cost, 2),
                "avg_interval_days": round(avg_interval, 1),
                "diy_pct": round(diy_pct, 1),
            }

        # Check scheduled tasks
        overdue = []
        upcoming = []
        now = datetime.now().isoformat()

        for task in self._schedule.values():
            if task.next_due < now:
                overdue.append({
                    "system": task.system,
                    "task": task.task,
                    "due": task.next_due,
                    "overdue_days": (datetime.now() - datetime.fromisoformat(task.next_due)).days,
                    "priority": task.priority,
                })
            elif task.next_due < (datetime.now() + timedelta(days=7)).isoformat():
                upcoming.append({
                    "system": task.system,
                    "task": task.task,
                    "due": task.next_due,
                    "days_until": (datetime.fromisoformat(task.next_due) - datetime.now()).days,
                    "priority": task.priority,
                })

        return {
            "system_status": status,
            "overdue_tasks": sorted(overdue, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]]),
            "upcoming_tasks": sorted(upcoming, key=lambda x: x["days_until"]),
            "total_systems": len(status),
            "total_cost_ytd": round(sum(r.cost for r in self._records if r.timestamp > datetime.now().replace(month=1, day=1).isoformat()), 2),
        }

    def get_cost_analysis(self, months: int = 12) -> Dict[str, Any]:
        """Get maintenance cost insights."""
        cutoff = (datetime.now() - timedelta(days=months * 30)).isoformat()
        recent = [r for r in self._records if r.timestamp > cutoff]

        if not recent:
            return {"status": "insufficient_data"}

        # By system
        by_system = defaultdict(lambda: {"cost": 0.0, "count": 0, "time": 0})
        for r in recent:
            by_system[r.system]["cost"] += r.cost
            by_system[r.system]["count"] += 1
            by_system[r.system]["time"] += r.time_spent_minutes

        # DIY vs professional
        diy_cost = sum(r.cost for r in recent if r.provider.upper() == "DIY")
        pro_cost = sum(r.cost for r in recent if r.provider.upper() != "DIY")
        diy_count = sum(1 for r in recent if r.provider.upper() == "DIY")

        # Monthly trend
        by_month = defaultdict(float)
        for r in recent:
            month = r.timestamp[:7]
            by_month[month] += r.cost

        return {
            "months_analyzed": months,
            "total_cost": round(sum(r.cost for r in recent), 2),
            "avg_monthly": round(sum(by_month.values()) / max(1, len(by_month)), 2),
            "by_system": {k: {"cost": round(v["cost"], 2), "count": v["count"], "avg_time": round(v["time"]/max(1, v["count"]), 1)} for k, v in by_system.items()},
            "diy_vs_pro": {
                "diy_cost": round(diy_cost, 2),
                "pro_cost": round(pro_cost, 2),
                "diy_count": diy_count,
                "pro_count": len(recent) - diy_count,
            },
            "most_expensive_system": max(by_system.items(), key=lambda x: x[1]["cost"])[0] if by_system else "",
            "monthly_trend": dict(sorted(by_month.items())),
        }

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_stats(self, record: MaintenanceRecord):
        """Update running statistics."""
        n = self._stats["total_records"]
        self._stats["avg_cost"] = round((self._stats["avg_cost"] * (n - 1) + record.cost) / n, 2)
        
        diy_count = sum(1 for r in self._records if r.provider.upper() == "DIY")
        self._stats["diy_pct"] = round(diy_count / n * 100, 1)

    def _update_schedule(self, system: str, task: str):
        """Update scheduled task last completed date."""
        task_id = f"{system}_{task.replace(' ', '_').lower()}"
        if task_id in self._schedule:
            self._schedule[task_id].last_completed = datetime.now().isoformat()
            self._schedule[task_id].next_due = (datetime.now() + timedelta(days=self._schedule[task_id].frequency_days)).isoformat()
            self._save_schedule()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception:
            pass

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception:
            pass

    def _save_schedule(self):
        try:
            data = {k: {
                "task_id": v.task_id,
                "system": v.system,
                "task": v.task,
                "frequency_days": v.frequency_days,
                "last_completed": v.last_completed,
                "next_due": v.next_due,
                "priority": v.priority,
                "estimated_cost": v.estimated_cost,
                "provider_preference": v.provider_preference,
            } for k, v in self._schedule.items()}
            SCHEDULE_DB.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load_schedule(self):
        try:
            if SCHEDULE_DB.exists():
                data = json.loads(SCHEDULE_DB.read_text())
                for k, v in data.items():
                    self._schedule[k] = ScheduledTask(**v)
        except Exception:
            pass

    def _log_record(self, record: MaintenanceRecord):
        try:
            with open(MAINTENANCE_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": record.timestamp,
                    "system": record.system,
                    "task": record.task,
                    "cost": record.cost,
                    "provider": record.provider,
                    "condition_after": record.condition_after,
                }) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_hms_instance: Optional[HomeMaintenanceScheduler] = None
_hms_lock = threading.Lock()


def get_home_maintenance_scheduler() -> HomeMaintenanceScheduler:
    global _hms_instance
    with _hms_lock:
        if _hms_instance is None:
            _hms_instance = HomeMaintenanceScheduler()
        return _hms_instance
