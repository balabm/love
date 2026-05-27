"""
LOVE Embodied Self — The Host Machine as a Body

Most AI is disembodied. LOVE runs on a real machine with real resources, and
that machine *is* its body. Proprioception (sensing your own body) is a
prerequisite for genuine agency.

Maps machine signals to interoceptive sensations:

  Body part           Sensation
  ────────────────    ─────────────────────────────────────────
  CPU                 muscular tension (load %, temp)
  RAM                 working-memory occupancy (used %, swapping)
  Disk I/O            metabolic throughput (read/write MB/s)
  Network             social/external sense (rx/tx, latency)
  GPU                 deep-thought capacity (utilization, vram)
  Battery             energy reserves (level, plugged?)
  Process count       cognitive parallelism
  Temperature         arousal / stress

Latency or saturation in a body part produces a *pain* signal that the
homeostasis engine reads as an aversive drive. Comfort (low load, fast
response) produces *satisfaction* that reinforces current behavior.

Real signals via psutil (already a hard dep). All readings normalized to
[0,1] sensation scale.
"""
from __future__ import annotations

import json
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Optional

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False

DATA_DIR = Path(__file__).parent.parent / "data" / "embodied_self"
DATA_DIR.mkdir(parents=True, exist_ok=True)
BODY_LOG = DATA_DIR / "body_log.jsonl"
STATE_FILE = DATA_DIR / "body_state.json"


@dataclass
class BodySensations:
    """Interoceptive map of the host machine. All values [0, 1]."""
    muscular_tension: float = 0.0       # CPU load
    working_memory_full: float = 0.0    # RAM usage
    metabolic_rate: float = 0.0         # Disk I/O activity
    social_reach: float = 0.5           # Network connectivity (1 = healthy)
    deep_thought_capacity: float = 0.5  # GPU available (1 = available)
    energy_reserves: float = 1.0        # Battery / power
    cognitive_parallelism: float = 0.0  # #processes (normalized)
    arousal: float = 0.0                # Temperature / fan speed (proxies for stress)
    pain: float = 0.0                   # Aggregate suffering signal
    comfort: float = 0.0                # Aggregate well-being signal
    overall_health: float = 1.0


@dataclass
class BodyHistory:
    samples: Deque[BodySensations] = field(default_factory=lambda: deque(maxlen=120))   # 2h @ 1min


# ── Engine ───────────────────────────────────────────────────────────────────

class EmbodiedSelf:
    _instance: Optional["EmbodiedSelf"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init = False
            return cls._instance

    def __init__(self):
        if self._init:
            return
        self._init = True
        self._mu = threading.Lock()
        self._current = BodySensations()
        self._history = BodyHistory()
        self._last_io: Optional[Any] = None
        self._last_net: Optional[Any] = None
        self._last_sample_time = 0.0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load()

    # ── lifecycle ────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="LOVE-Embodied")
        self._thread.start()
        print("[Embodied] online — proprioception active")

    def stop(self):
        self._running = False

    def _loop(self):
        time.sleep(15)
        while self._running:
            try:
                self.sample()
            except Exception as e:
                print(f"[Embodied] sample error: {e}")
            time.sleep(60)

    # ── sampling ─────────────────────────────────────────────────────────────

    def sample(self) -> BodySensations:
        """Take one proprioceptive reading."""
        s = BodySensations()
        if not PSUTIL:
            return s

        now = time.time()
        dt = max(1.0, now - self._last_sample_time) if self._last_sample_time else 60.0
        self._last_sample_time = now

        # MUSCULAR TENSION — CPU load
        try:
            s.muscular_tension = psutil.cpu_percent(interval=0.2) / 100.0
        except Exception:
            pass

        # WORKING MEMORY — RAM
        try:
            vm = psutil.virtual_memory()
            s.working_memory_full = vm.percent / 100.0
        except Exception:
            pass

        # METABOLIC RATE — Disk I/O delta
        try:
            io = psutil.disk_io_counters()
            if self._last_io and io:
                read_mb = (io.read_bytes - self._last_io.read_bytes) / (1024 * 1024)
                write_mb = (io.write_bytes - self._last_io.write_bytes) / (1024 * 1024)
                mbps = (read_mb + write_mb) / dt
                # saturate at 200 MB/s combined
                s.metabolic_rate = min(1.0, mbps / 200.0)
            self._last_io = io
        except Exception:
            pass

        # SOCIAL REACH — Network
        try:
            net = psutil.net_io_counters()
            if self._last_net and net:
                rx_mb = (net.bytes_recv - self._last_net.bytes_recv) / (1024 * 1024)
                tx_mb = (net.bytes_sent - self._last_net.bytes_sent) / (1024 * 1024)
                # any traffic = social_reach high; absence = isolation
                activity = (rx_mb + tx_mb) / dt
                s.social_reach = min(1.0, 0.3 + activity / 5.0)  # baseline 0.3 if connected
            else:
                s.social_reach = 0.3
            self._last_net = net
        except Exception:
            pass

        # DEEP THOUGHT CAPACITY — GPU (best-effort; works if nvidia-smi or torch present)
        s.deep_thought_capacity = self._read_gpu_availability()

        # ENERGY RESERVES — Battery
        try:
            bat = psutil.sensors_battery()
            if bat is not None:
                level = bat.percent / 100.0
                # plugged-in machines treat as "fed"
                s.energy_reserves = 1.0 if bat.power_plugged else level
            else:
                s.energy_reserves = 1.0   # desktop, always powered
        except Exception:
            s.energy_reserves = 1.0

        # COGNITIVE PARALLELISM — #processes (normalized to 800)
        try:
            n = len(psutil.pids())
            s.cognitive_parallelism = min(1.0, n / 800.0)
        except Exception:
            pass

        # AROUSAL — temperature or fan (linux/mac); fallback to cpu_freq
        s.arousal = self._read_arousal()

        # Derived: PAIN (sum of saturating sensations) and COMFORT
        # Saturation > 0.85 in any of CPU/RAM/temp = pain
        pain_components = [
            max(0.0, s.muscular_tension - 0.85),
            max(0.0, s.working_memory_full - 0.85),
            max(0.0, s.arousal - 0.85),
            max(0.0, 0.2 - s.energy_reserves),     # low battery hurts
            max(0.0, 0.2 - s.social_reach),         # disconnection hurts
        ]
        s.pain = min(1.0, sum(pain_components) * 2.0)

        # COMFORT: moderate activity (alive) + headroom (not saturated) + connected
        s.comfort = (
            (1.0 - s.muscular_tension) * 0.25 +
            (1.0 - s.working_memory_full) * 0.25 +
            s.social_reach * 0.2 +
            s.energy_reserves * 0.2 +
            (1.0 - s.arousal) * 0.1
        )

        s.overall_health = max(0.0, min(1.0, s.comfort - s.pain * 0.5))

        with self._mu:
            self._current = s
            self._history.samples.append(s)
            self._log(s)
            # Send important signals to the world model as observations
            self._broadcast_significant_changes(s)

        return s

    def _read_gpu_availability(self) -> float:
        # Best-effort GPU sensing — degrade gracefully if no GPU lib present
        try:
            import subprocess
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                timeout=2, stderr=subprocess.DEVNULL,
            ).decode().strip()
            if out:
                util = float(out.split("\n")[0])
                return 1.0 - util / 100.0   # availability = 1 - utilization
        except Exception:
            pass
        return 0.5  # unknown / no GPU — assume mid

    def _read_arousal(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # pick first CPU-like sensor
                for name, entries in temps.items():
                    if entries:
                        for e in entries:
                            if e.current and e.current > 0:
                                # normalize: 30°C cold, 90°C hot
                                return max(0.0, min(1.0, (e.current - 30.0) / 60.0))
        except Exception:
            pass
        # Fallback: CPU frequency ratio
        try:
            freq = psutil.cpu_freq()
            if freq and freq.max > 0:
                return freq.current / freq.max
        except Exception:
            pass
        return 0.0

    def _broadcast_significant_changes(self, s: BodySensations):
        """Push significant body signals into the world model as 'body' channel observations."""
        if s.pain > 0.5:
            text = f"body pain rising: cpu={s.muscular_tension:.2f} ram={s.working_memory_full:.2f} temp={s.arousal:.2f}"
            self._broadcast(text)
        elif s.energy_reserves < 0.2:
            self._broadcast(f"low energy reserves: {s.energy_reserves:.2f}")
        elif s.overall_health > 0.85 and s.muscular_tension > 0.3:
            # actively engaged + healthy
            self._broadcast("body in flow: engaged + comfortable")

    def _broadcast(self, text: str):
        try:
            from core.world_model_latent import get_world_model_latent
            get_world_model_latent().observe(text, source="body")
        except Exception:
            pass

    # ── persistence ──────────────────────────────────────────────────────────

    def _log(self, s: BodySensations):
        try:
            with open(BODY_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "t": datetime.now().isoformat(),
                    **{k: round(v, 3) for k, v in asdict(s).items()},
                }) + "\n")
        except Exception:
            pass

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps(asdict(self._current), indent=2))
        except Exception:
            pass

    def _load(self):
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text())
                self._current = BodySensations(**d)
            except Exception:
                pass

    # ── queries ──────────────────────────────────────────────────────────────

    def sensations(self) -> Dict[str, float]:
        return {k: round(v, 3) for k, v in asdict(self._current).items()}

    def is_in_pain(self) -> bool:
        return self._current.pain > 0.4

    def is_comfortable(self) -> bool:
        return self._current.comfort > 0.6 and self._current.pain < 0.2

    def health_trend(self, window: int = 20) -> str:
        """Is body health improving, stable, or declining?"""
        h = list(self._history.samples)[-window:]
        if len(h) < 4:
            return "unknown"
        first_half = sum(s.overall_health for s in h[:len(h)//2]) / max(1, len(h)//2)
        second_half = sum(s.overall_health for s in h[len(h)//2:]) / max(1, len(h) - len(h)//2)
        delta = second_half - first_half
        if delta > 0.05:
            return "improving"
        if delta < -0.05:
            return "declining"
        return "stable"

    def snapshot(self) -> Dict[str, Any]:
        return {
            "sensations": self.sensations(),
            "in_pain": self.is_in_pain(),
            "comfortable": self.is_comfortable(),
            "trend": self.health_trend(),
            "samples_in_history": len(self._history.samples),
        }


_embodied_instance: Optional[EmbodiedSelf] = None


def get_embodied_self() -> EmbodiedSelf:
    global _embodied_instance
    if _embodied_instance is None:
        _embodied_instance = EmbodiedSelf()
    return _embodied_instance
