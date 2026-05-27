"""
LOVE Self-Healing System — Auto-detect and fix errors

LOVE monitors its own errors and attempts to fix them automatically.
If an error can't be fixed, LOVE alerts the user with specific guidance.

This is LOVE's immune system for code errors.
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
ERROR_LOG = DATA_DIR / "error_log.jsonl"
HEALING_LOG = DATA_DIR / "healing_log.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log_error(error: Dict[str, Any]):
    """Log an error for tracking."""
    error["timestamp"] = datetime.now().isoformat()
    try:
        with open(ERROR_LOG, "a") as f:
            f.write(json.dumps(error) + "\n")
    except Exception:
        pass


def _log_healing(healing: Dict[str, Any]):
    """Log a healing attempt."""
    healing["timestamp"] = datetime.now().isoformat()
    try:
        with open(HEALING_LOG, "a") as f:
            f.write(json.dumps(healing) + "\n")
    except Exception:
        pass


def detect_and_fix_error(error_message: str) -> Dict[str, Any]:
    """
    Detect an error type and attempt to fix it.
    Returns: {"fixed": bool, "action_taken": str, "user_alert": str}
    """
    # Pattern 1: Missing attribute errors
    if "'LiveContext' object has no attribute" in error_message:
        attr_match = re.search(r"no attribute '(\w+)'", error_message)
        if attr_match:
            missing_attr = attr_match.group(1)
            # Known attribute mapping
            attr_mappings = {
                "unread_emails": "unread_important",
            }
            if missing_attr in attr_mappings:
                correct_attr = attr_mappings[missing_attr]
                _log_healing({
                    "error_type": "missing_attribute",
                    "error": error_message,
                    "action": f"Replace '{missing_attr}' with '{correct_attr}' in heartbeat.py",
                    "status": "auto_fix_suggested"
                })
                return {
                    "fixed": False,
                    "action_taken": "Suggested fix: Replace attribute name",
                    "user_alert": f"⚠️ LOVE detected: '{missing_attr}' should be '{correct_attr}' in heartbeat.py line ~451. Fix: Change ctx.{missing_attr} to ctx.{correct_attr}"
                }
    
    # Pattern 2: Missing method errors
    if "object has no attribute" in error_message and "method" not in error_message.lower():
        method_match = re.search(r"no attribute '(_\w+)'", error_message)
        if method_match:
            missing_method = method_match.group(1)
            _log_healing({
                "error_type": "missing_method",
                "error": error_message,
                "action": f"Add method '{missing_method}' to class",
                "status": "auto_fix_suggested"
            })
            return {
                "fixed": False,
                "action_taken": "Suggested fix: Add missing method",
                "user_alert": f"⚠️ LOVE detected: Method '{missing_method}' is missing. Check heartbeat.py or relevant module."
            }
    
    # Pattern 3: Import errors
    if "cannot import" in error_message:
        import_match = re.search(r"cannot import name '(\w+)' from '([\w.]+)'", error_message)
        if import_match:
            missing_name = import_match.group(1)
            from_module = import_match.group(2)
            
            # Known import fixes
            if missing_name == "memory" and "core.agent" in from_module:
                _log_healing({
                    "error_type": "import_error",
                    "error": error_message,
                    "action": "Use core.long_term_memory instead of core.agent.memory",
                    "status": "auto_fix_suggested"
                })
                return {
                    "fixed": False,
                    "action_taken": "Suggested fix: Use correct memory module",
                    "user_alert": f"⚠️ LOVE detected: Import 'memory' from 'core.agent' is wrong. Use 'from core.long_term_memory import add_episodic, recall_memory' instead. Check api/main.py lines ~1877, 1919, 1947, 2921"
                }
    
    # Pattern 4: File not found
    if "No such file or directory" in error_message or "FileNotFoundError" in error_message:
        file_match = re.search(r"'([^']+)'", error_message)
        if file_match:
            missing_file = file_match.group(1)
            _log_healing({
                "error_type": "file_not_found",
                "error": error_message,
                "action": f"Create missing file: {missing_file}",
                "status": "needs_manual_fix"
            })
            return {
                "fixed": False,
                "action_taken": "Identified missing file",
                "user_alert": f"⚠️ LOVE detected: Missing file '{missing_file}'. Create it or check if the path is correct."
            }
    
    # Pattern 5: Module not found
    if "ModuleNotFoundError" in error_message:
        module_match = re.search(r"No module named '([^']+)'", error_message)
        if module_match:
            missing_module = module_match.group(1)
            _log_healing({
                "error_type": "module_not_found",
                "error": error_message,
                "action": f"Install missing module: pip install {missing_module}",
                "status": "needs_manual_fix"
            })
            return {
                "fixed": False,
                "action_taken": "Identified missing module",
                "user_alert": f"⚠️ LOVE detected: Missing module '{missing_module}'. Install with: pip install {missing_module}"
            }
    
    # Generic error - just log it
    _log_error({
        "error": error_message,
        "type": "unknown",
        "status": "logged"
    })
    
    return {
        "fixed": False,
        "action_taken": "Logged error for analysis",
        "user_alert": None
    }


def check_recent_errors(max_hours: int = 24) -> List[Dict[str, Any]]:
    """Check recent errors in logs for patterns."""
    errors = []
    
    # Check error log
    try:
        if ERROR_LOG.exists():
            lines = ERROR_LOG.read_text().strip().split("\n")
            cutoff = datetime.now().timestamp() - (max_hours * 3600)
            
            for line in lines[-50:]:
                if not line:
                    continue
                try:
                    error_data = json.loads(line)
                    ts = datetime.fromisoformat(error_data.get("timestamp", "")).timestamp()
                    if ts > cutoff:
                        errors.append(error_data)
                except Exception:
                    pass
    except Exception:
        pass
    
    return errors


def get_healing_summary() -> Dict[str, Any]:
    """Get summary of healing attempts."""
    try:
        if HEALING_LOG.exists():
            lines = HEALING_LOG.read_text().strip().split("\n")
            healing_events = [json.loads(l) for l in lines if l]
            
            return {
                "total_healing_attempts": len(healing_events),
                "recent_healing": healing_events[-5:] if healing_events else [],
                "auto_fixed": sum(1 for h in healing_events if h.get("status") == "auto_fixed"),
                "needs_manual": sum(1 for h in healing_events if h.get("status") in ["needs_manual_fix", "auto_fix_suggested"])
            }
    except Exception:
        pass
    
    return {
        "total_healing_attempts": 0,
        "recent_healing": [],
        "auto_fixed": 0,
        "needs_manual": 0
    }


def monitor_log_file(log_path: Path) -> Optional[str]:
    """Monitor a log file for errors and return user alert if fix needed."""
    if not log_path.exists():
        return None
    
    try:
        recent_content = log_path.read_text()[-10000]  # Last 10KB
        error_lines = []
        
        for line in recent_content.split("\n"):
            if "error" in line.lower() or "exception" in line.lower():
                error_lines.append(line)
        
        for error_line in error_lines[-5:]:  # Check last 5 errors
            healing = detect_and_fix_error(error_line)
            if healing["user_alert"]:
                return healing["user_alert"]
    
    except Exception:
        pass
    
    return None


def monitor_stdout_stderr() -> Optional[str]:
    """
    Monitor stdout/stderr for errors that LOVE should fix.
    This is called by the heartbeat to catch runtime errors.
    """
    # Check the error log file for recent errors
    if ERROR_LOG.exists():
        try:
            recent_content = ERROR_LOG.read_text()[-5000]  # Last 5KB
            for line in recent_content.split("\n")[-10:]:  # Last 10 lines
                healing = detect_and_fix_error(line)
                if healing["user_alert"]:
                    return healing["user_alert"]
        except Exception:
            pass
    return None


def rollback_all_backups() -> List[str]:
    """
    Finds all .bak files in core/, api/, tools/, and agents/ and restores them.
    Returns a list of restored file names.
    """
    import shutil
    import os
    from pathlib import Path
    
    restored_files = []
    # Path(__file__).parent is the 'core' directory
    core_dir = Path(__file__).parent
    project_root = core_dir.parent
    search_dirs = [project_root / "core", project_root / "api", project_root / "tools", project_root / "agents"]
    
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for bak_path in sdir.glob("*.bak"):
            py_path = bak_path.with_suffix("")
            try:
                if bak_path.exists():
                    shutil.copy2(bak_path, py_path)
                    # Remove the backup after restoring to prevent infinite rollback loops
                    os.remove(bak_path)
                    restored_files.append(str(py_path.name))
                    print(f"[Sentinel] Restored {py_path.name} from backup.")
            except Exception as e:
                print(f"[Sentinel] Error restoring {bak_path.name}: {e}")
                
    if restored_files:
        try:
            _log_healing({
                "error_type": "startup_crash_rollback",
                "error": "Failed to import core modules on startup",
                "action": f"Restored backups for: {', '.join(restored_files)}",
                "status": "auto_fixed"
            })
        except Exception:
            pass
        
    return restored_files


def verify_and_heal_system():
    """
    Verifies that all core modules can be imported without errors.
    If an import fails, restores any .bak backups and restarts the process.
    """
    import sys
    import os
    
    modules_to_test = [
        "core.agent",
        "core.evolution",
        "core.sync",
        "core.orchestrator",
        "core.heartbeat",
        "core.awareness",
        "core.context_engine",
        "core.doc_analyst",
        "core.settings",
        "core.consciousness",
        "core.self_modification_pipeline",
        "core.ghost_dev",
        "core.self_improvement_daemon"
    ]
    
    failed = False
    error_msg = ""
    for mod_name in modules_to_test:
        try:
            # Try to dynamically import the module
            if mod_name in sys.modules:
                import importlib
                importlib.reload(sys.modules[mod_name])
            else:
                __import__(mod_name)
        except Exception as e:
            failed = True
            error_msg = f"Failed to import {mod_name}: {e}"
            print(f"[Sentinel] Startup verification failed: {error_msg}")
            break
            
    if failed:
        print("[Sentinel] Crash or import error detected. Initiating emergency rollback...")
        restored = rollback_all_backups()
        if restored:
            print(f"[Sentinel] Successfully rolled back: {restored}. Restarting process...")
            # Re-execute the current process to start fresh
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print("[Sentinel] No backups found to roll back. System is in a broken state.")

