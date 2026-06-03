import time
import asyncio
from enum import Enum
from typing import List, Dict, Any, Callable, Optional, Union
import traceback
import builtins

def safe_print(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    file = kwargs.get("file", None)
    flush = kwargs.get("flush", False)
    
    msg = sep.join(str(arg) for arg in args)
    try:
        _original_print(msg, end=end, file=file, flush=flush)
    except UnicodeEncodeError:
        replacements = {
            "❌": "[X]",
            "⚠️": "[!]",
            "✅": "[OK]",
            "🛑": "[STOP]",
            "╔": "+",
            "╗": "+",
            "╠": "+",
            "╣": "+",
            "╚": "+",
            "╝": "+",
            "═": "-",
            "║": "|",
        }
        for char, repl in replacements.items():
            msg = msg.replace(char, repl)
        try:
            _original_print(msg, end=end, file=file, flush=flush)
        except Exception:
            ascii_msg = msg.encode("ascii", errors="replace").decode("ascii")
            _original_print(ascii_msg, end=end, file=file, flush=flush)

_original_print = builtins.print
print = safe_print


class ModuleState(str, Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"

class ModuleDescriptor:
    def __init__(
        self,
        name: str,
        wave: int,
        start_fn: Callable,
        depends_on: List[str] = None,
        stop_fn: Optional[Callable] = None,
        health_fn: Optional[Callable] = None,
        optional: bool = True,
        description: str = ""
    ):
        self.name = name
        self.wave = wave
        self.start_fn = start_fn
        self.depends_on = depends_on or []
        self.stop_fn = stop_fn
        self.health_fn = health_fn
        self.optional = optional
        self.description = description
        self.state = ModuleState.REGISTERED
        self.error: Optional[str] = None
        self.elapsed_ms: float = 0.0

class LifecycleManager:
    def __init__(self):
        self.modules: Dict[str, ModuleDescriptor] = {}
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def register(self, descriptor: ModuleDescriptor):
        if descriptor.name in self.modules:
            raise ValueError(f"Module '{descriptor.name}' is already registered.")
        self.modules[descriptor.name] = descriptor

    def clear_modules(self):
        """Reset all module registrations — useful on Uvicorn reload."""
        self.modules.clear()

    def get(self, name: str) -> Optional[ModuleDescriptor]:
        return self.modules.get(name)

    def is_ready(self, name: str) -> bool:
        mod = self.get(name)
        return mod is not None and mod.state in (ModuleState.READY, ModuleState.DEGRADED)

    MODULE_START_TIMEOUT = 30   # seconds per module

    async def start_all(self):
        self.loop = asyncio.get_event_loop()
        self.start_time = time.time()
        print("\n" + "="*60)
        print("          PROJECT LOVE CORE AGENTIC STARTUP")
        print("="*60)
        
        # We group modules by wave
        waves = {}
        for mod in self.modules.values():
            waves.setdefault(mod.wave, []).append(mod)
        
        sorted_waves = sorted(waves.keys())
        
        for wave_num in sorted_waves:
            wave_modules = waves[wave_num]
            print(f"\n[Wave {wave_num}] Starting modules...")
            
            for mod in wave_modules:
                # Check dependencies first
                failed_deps = []
                for dep in mod.depends_on:
                    dep_mod = self.get(dep)
                    if not dep_mod or dep_mod.state in (ModuleState.FAILED, ModuleState.STOPPED):
                        failed_deps.append(dep)
                
                if failed_deps:
                    mod.state = ModuleState.FAILED
                    mod.error = f"Missing or failed dependencies: {', '.join(failed_deps)}"
                    print(f"  [X] {mod.name:<20} failed     (dependency error: {mod.error})")
                    continue

                mod.state = ModuleState.STARTING
                t0 = time.time()
                try:
                    # Execute start_fn with a timeout to prevent blocking
                    if asyncio.iscoroutinefunction(mod.start_fn):
                        res = await asyncio.wait_for(mod.start_fn(), timeout=self.MODULE_START_TIMEOUT)
                    else:
                        res = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, mod.start_fn),
                            timeout=self.MODULE_START_TIMEOUT
                        )
                    
                    mod.elapsed_ms = (time.time() - t0) * 1000
                    
                    # Some start_fn might return info or indicate degraded status
                    if isinstance(res, dict) and res.get("status") == "degraded":
                        mod.state = ModuleState.DEGRADED
                        mod.error = res.get("error", "Started in degraded mode")
                        print(f"  [!] {mod.name:<20} degraded   ({mod.elapsed_ms:.1f}ms - {mod.error})")
                    else:
                        mod.state = ModuleState.READY
                        print(f"  [OK] {mod.name:<20} ready      ({mod.elapsed_ms:.1f}ms)")
                except asyncio.TimeoutError:
                    mod.elapsed_ms = (time.time() - t0) * 1000
                    mod.state = ModuleState.FAILED if not mod.optional else ModuleState.DEGRADED
                    mod.error = f"Timed out after {self.MODULE_START_TIMEOUT}s"
                    print(f"  [!] {mod.name:<20} {'degraded' if mod.optional else 'TIMEOUT'}   ({mod.elapsed_ms:.1f}ms - {mod.error})")
                    if not mod.optional:
                        print(f"\n[CRITICAL FAILURE] Critical module '{mod.name}' timed out. Continuing with degraded state.")
                        # Don't abort — let other modules try to start
                        mod.state = ModuleState.DEGRADED
                except Exception as e:
                    mod.elapsed_ms = (time.time() - t0) * 1000
                    mod.state = ModuleState.FAILED
                    mod.error = str(e)
                    print(f"  [X] {mod.name:<20} failed     ({mod.elapsed_ms:.1f}ms - {e})")
                    if not mod.optional:
                        print(f"\n[CRITICAL FAILURE] Critical module '{mod.name}' failed to start. Continuing with degraded state.")
                        # Don't abort — let other modules try to start
                        mod.state = ModuleState.DEGRADED
        
        self.end_time = time.time()
        self.print_summary()

    async def stop_all(self):
        print("\n" + "="*60)
        print("          PROJECT LOVE CORE AGENTIC SHUTDOWN")
        print("="*60)
        
        # Stop in reverse order of waves
        waves = {}
        for mod in self.modules.values():
            waves.setdefault(mod.wave, []).append(mod)
        
        sorted_waves = sorted(waves.keys(), reverse=True)
        for wave_num in sorted_waves:
            wave_modules = waves[wave_num]
            print(f"\n[Wave {wave_num}] Stopping modules...")
            for mod in reversed(wave_modules):
                if mod.state in (ModuleState.READY, ModuleState.DEGRADED, ModuleState.STARTING):
                    if mod.stop_fn:
                        try:
                            t0 = time.time()
                            if asyncio.iscoroutinefunction(mod.stop_fn):
                                await mod.stop_fn()
                            else:
                                mod.stop_fn()
                            elapsed = (time.time() - t0) * 1000
                            mod.state = ModuleState.STOPPED
                            print(f"  🛑 {mod.name:<20} stopped    ({elapsed:.1f}ms)")
                        except Exception as e:
                            print(f"  ❌ Error stopping {mod.name}: {e}")
                            mod.state = ModuleState.FAILED
                    else:
                        mod.state = ModuleState.STOPPED
                        print(f"  🛑 {mod.name:<20} stopped")

    async def restart_module(self, name: str) -> bool:
        mod = self.get(name)
        if not mod:
            return False
        
        print(f"[LifecycleManager] 🛠️ Attempting to restart module '{name}'...")
        mod.state = ModuleState.STARTING
        t0 = time.time()
        try:
            if asyncio.iscoroutinefunction(mod.start_fn):
                res = await mod.start_fn()
            else:
                res = mod.start_fn()
            
            mod.elapsed_ms = (time.time() - t0) * 1000
            if isinstance(res, dict) and res.get("status") == "degraded":
                mod.state = ModuleState.DEGRADED
                mod.error = res.get("error", "Started in degraded mode")
                print(f"  ⚠️  {mod.name:<20} degraded   ({mod.elapsed_ms:.1f}ms - {mod.error})")
            else:
                mod.state = ModuleState.READY
                mod.error = None
                print(f"  ✅ {mod.name:<20} ready      ({mod.elapsed_ms:.1f}ms - successfully restarted)")
            return True
        except Exception as e:
            mod.elapsed_ms = (time.time() - t0) * 1000
            mod.state = ModuleState.FAILED
            mod.error = str(e)
            print(f"  ❌ {mod.name:<20} failed restart ({mod.elapsed_ms:.1f}ms - {e})")
            return False

    def print_summary(self):
        total = len(self.modules)
        ready = sum(1 for m in self.modules.values() if m.state == ModuleState.READY)
        degraded = sum(1 for m in self.modules.values() if m.state == ModuleState.DEGRADED)
        failed = sum(1 for m in self.modules.values() if m.state == ModuleState.FAILED)
        duration = self.end_time - self.start_time
        
        print("\n" + "╔" + "═"*57 + "╗")
        print("║              LOVE SYSTEM STARTUP REPORT                  ║")
        print("╠" + "═"*57 + "╣")
        
        # Print wave by wave
        waves = {}
        for mod in self.modules.values():
            waves.setdefault(mod.wave, []).append(mod)
            
        for w in sorted(waves.keys()):
            print(f"║  Wave {w:<50} ║")
            for m in waves[w]:
                status_symbol = "✅" if m.state == ModuleState.READY else "⚠️ " if m.state == ModuleState.DEGRADED else "❌"
                status_str = m.state.value
                time_str = f"({m.elapsed_ms:.1f}ms)" if m.elapsed_ms > 0 else ""
                info = f"{status_symbol} {m.name:<20} {status_str:<10} {time_str}"
                print(f"║    {info:<50} ║")
            print("║                                                           ║")
            
        summary_line = f"Summary: {ready}/{total} modules ready, {degraded} degraded, {failed} failed"
        time_line = f"Total Startup Time: {duration:.2f}s"
        print(f"║  {summary_line:<52} ║")
        print(f"║  {time_line:<52} ║")
        print("╚" + "═"*57 + "╝\n")

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_modules": len(self.modules),
            "modules": {
                name: {
                    "wave": m.wave,
                    "state": m.state.value,
                    "depends_on": m.depends_on,
                    "elapsed_ms": m.elapsed_ms,
                    "error": m.error,
                    "optional": m.optional,
                    "health": m.health_fn() if (m.health_fn and m.state in (ModuleState.READY, ModuleState.DEGRADED)) else None
                } for name, m in self.modules.items()
            }
        }

# Global Singleton instance
_instance: Optional[LifecycleManager] = None

def get_lifecycle() -> LifecycleManager:
    global _instance
    if _instance is None:
        _instance = LifecycleManager()
    return _instance
