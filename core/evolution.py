"""
Self-Evolution Core (Self-Healing)
LOVE monitors logs, detects crashes, analyzes tracebacks, and proposes fixes.
"""

import os
import re
import sys
import json
import subprocess
import traceback
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from core.llm import get_coding_llm
from core.memory import save_log

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CRASH_LOG_DIR = DATA_DIR / "crashes"
API_LOG_FILE = DATA_DIR / "api.log"
ERROR_LOG_FILE = DATA_DIR / "error.log"

# Ensure directories exist
CRASH_LOG_DIR.mkdir(parents=True, exist_ok=True)

class CrashMonitor:
    """Monitors logs and stderr for crashes and exceptions."""
    
    def __init__(self):
        self.crashes: List[Dict[str, Any]] = []
        self.last_check_time = datetime.now()
        
    def scan_logs(self) -> List[Dict[str, Any]]:
        """Scan API and error logs for new crashes since last check."""
        new_crashes = []
        
        # Check API log
        if API_LOG_FILE.exists():
            crashes = self._parse_log_file(API_LOG_FILE, "api")
            new_crashes.extend(crashes)
            
        # Check error log
        if ERROR_LOG_FILE.exists():
            crashes = self._parse_log_file(ERROR_LOG_FILE, "error")
            new_crashes.extend(crashes)
            
        self.crashes.extend(new_crashes)
        return new_crashes
    
    def _parse_log_file(self, log_file: Path, source: str) -> List[Dict[str, Any]]:
        """Parse a log file for tracebacks and exceptions."""
        crashes = []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Find tracebacks using regex
            traceback_pattern = r'(Traceback \(most recent call last\):.*?)(?:\n\n|\Z)'
            matches = re.finditer(traceback_pattern, content, re.DOTALL)
            
            for match in matches:
                tb_text = match.group(1)
                crash_id = self._generate_crash_id(tb_text)
                
                # Skip if already processed
                if self._is_crash_processed(crash_id):
                    continue
                    
                crash = {
                    "id": crash_id,
                    "timestamp": datetime.now().isoformat(),
                    "source": source,
                    "traceback": tb_text,
                    "file_path": self._extract_error_file(tb_text),
                    "error_line": self._extract_error_line(tb_text),
                    "error_type": self._extract_error_type(tb_text),
                    "status": "detected",
                    "fix_proposed": None,
                    "fix_applied": False
                }
                crashes.append(crash)
                self._save_crash(crash)
                
        except Exception as e:
            print(f"Error parsing log file {log_file}: {e}")
            
        return crashes
    
    def _generate_crash_id(self, traceback_text: str) -> str:
        """Generate unique ID from traceback hash."""
        return hashlib.md5(traceback_text.encode()).hexdigest()[:12]
    
    def _is_crash_processed(self, crash_id: str) -> bool:
        """Check if crash was already processed."""
        crash_file = CRASH_LOG_DIR / f"{crash_id}.json"
        return crash_file.exists()
    
    def _save_crash(self, crash: Dict[str, Any]):
        """Save crash details to file."""
        crash_file = CRASH_LOG_DIR / f"{crash['id']}.json"
        with open(crash_file, 'w') as f:
            json.dump(crash, f, indent=2)
            
    def _extract_error_file(self, traceback_text: str) -> Optional[str]:
        """Extract the file path where error occurred."""
        # Match the last "File \"path\", line X" in traceback
        pattern = r'File "([^"]+)", line \d+'
        matches = re.findall(pattern, traceback_text)
        return matches[-1] if matches else None
    
    def _extract_error_line(self, traceback_text: str) -> Optional[int]:
        """Extract the line number where error occurred."""
        pattern = r'File "[^"]+", line (\d+)'
        matches = re.findall(pattern, traceback_text)
        return int(matches[-1]) if matches else None
    
    def _extract_error_type(self, traceback_text: str) -> Optional[str]:
        """Extract the exception type and message."""
        lines = traceback_text.strip().split('\n')
        for line in reversed(lines):
            if ':' in line and not line.startswith(' '):
                return line.strip()
        return None
    
    def get_pending_crashes(self) -> List[Dict[str, Any]]:
        """Get all crashes awaiting fix."""
        pending = []
        for crash_file in CRASH_LOG_DIR.glob("*.json"):
            with open(crash_file, 'r') as f:
                crash = json.load(f)
                if crash.get("status") in ["detected", "fix_proposed"]:
                    pending.append(crash)
        return pending


class FixProposer:
    """Uses Qwen to analyze crashes and propose fixes."""
    
    def __init__(self):
        self.llm = get_coding_llm()
        
    def analyze_crash(self, crash: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a crash and propose a fix using the coding model."""
        
        # Read the problematic file
        file_path = crash.get("file_path")
        file_content = ""
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
            except Exception as e:
                file_content = f"[Could not read file: {e}]"
                
        # Build the prompt for Qwen
        prompt = f"""You are LOVE's self-healing system. A crash occurred in the user's system.

CRASH DETAILS:
- Error Type: {crash.get('error_type', 'Unknown')}
- File: {crash.get('file_path', 'Unknown')}
- Line: {crash.get('error_line', 'Unknown')}

TRACEBACK:
```
{crash.get('traceback', 'No traceback')}
```

SOURCE FILE CONTENT:
```python
{file_content}
```

TASK: Analyze this crash and propose a specific fix. Return your response as JSON:
{{
    "analysis": "Brief explanation of what caused the error",
    "root_cause": "The specific line or logic causing the issue",
    "proposed_fix": "The exact code change needed",
    "fixed_code": "Complete fixed version of the relevant section",
    "confidence": "high/medium/low",
    "requires_user_approval": true/false,
    "can_auto_apply": true/false
}}

Rules:
- Be specific about which lines to change
- If the fix is obvious (syntax error, missing import, simple None check), set can_auto_apply to true
- If the fix changes core logic or might have side effects, set requires_user_approval to true
- The fixed_code should be complete enough to replace the problematic section
"""

        try:
            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                fix_data = json.loads(json_match.group())
            else:
                fix_data = {
                    "analysis": response[:500],
                    "root_cause": "Unknown - could not parse fix",
                    "proposed_fix": "Manual review required",
                    "fixed_code": "",
                    "confidence": "low",
                    "requires_user_approval": True,
                    "can_auto_apply": False
                }
                
            # Update crash record
            crash["fix_proposed"] = fix_data
            crash["status"] = "fix_proposed"
            self._update_crash_file(crash)
            
            return fix_data
            
        except Exception as e:
            error_fix = {
                "analysis": f"Error analyzing crash: {str(e)}",
                "root_cause": "Analysis failed",
                "proposed_fix": "Manual intervention required",
                "fixed_code": "",
                "confidence": "low",
                "requires_user_approval": True,
                "can_auto_apply": False
            }
            crash["fix_proposed"] = error_fix
            crash["status"] = "fix_proposed"
            self._update_crash_file(crash)
            return error_fix
    
    def _update_crash_file(self, crash: Dict[str, Any]):
        """Update crash file with fix proposal."""
        crash_file = CRASH_LOG_DIR / f"{crash['id']}.json"
        with open(crash_file, 'w') as f:
            json.dump(crash, f, indent=2)


class FixApplicator:
    """Applies approved fixes to the codebase."""
    
    def __init__(self):
        self.backup_dir = DATA_DIR / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def apply_fix(self, crash_id: str) -> Dict[str, Any]:
        """Apply a proposed fix after user approves."""
        crash_file = CRASH_LOG_DIR / f"{crash_id}.json"
        
        if not crash_file.exists():
            return {"success": False, "error": "Crash not found"}
            
        with open(crash_file, 'r') as f:
            crash = json.load(f)
            
        fix = crash.get("fix_proposed")
        if not fix:
            return {"success": False, "error": "No fix proposed for this crash"}
            
        file_path = crash.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return {"success": False, "error": f"Target file not found: {file_path}"}
            
        try:
            # Create backup
            backup_path = self._create_backup(file_path)
            
            # Read current file
            with open(file_path, 'r') as f:
                original_content = f.read()
                
            # Apply fix (simple replacement strategy)
            fixed_code = fix.get("fixed_code")
            if fixed_code and len(fixed_code) > 10:
                # Try to find and replace the problematic section
                error_line = crash.get("error_line")
                if error_line:
                    lines = original_content.split('\n')
                    # Replace around the error line (context-aware)
                    context_start = max(0, error_line - 5)
                    context_end = min(len(lines), error_line + 5)
                    
                    # Build new content
                    new_lines = lines[:context_start] + [fixed_code] + lines[context_end:]
                    new_content = '\n'.join(new_lines)
                else:
                    # Fallback: append fix as comment
                    new_content = original_content + f"\n\n# LOVE FIX: {fixed_code}\n"
            else:
                return {"success": False, "error": "Invalid fixed_code provided"}
                
            # Write fixed content
            with open(file_path, 'w') as f:
                f.write(new_content)
                
            # Update crash status
            crash["status"] = "fix_applied"
            crash["fix_applied"] = True
            crash["backup_path"] = str(backup_path)
            with open(crash_file, 'w') as f:
                json.dump(crash, f, indent=2)
                
            # Log the fix
            save_log("system_fixes", {
                "crash_id": crash_id,
                "file": file_path,
                "backup": str(backup_path),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "message": f"Fix applied to {file_path}",
                "backup": str(backup_path),
                "restart_required": True
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to apply fix: {str(e)}"}
    
    def _create_backup(self, file_path: str) -> Path:
        """Create timestamped backup of file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path(file_path).name
        backup_path = self.backup_dir / f"{filename}.{timestamp}.bak"
        
        with open(file_path, 'r') as src:
            content = src.read()
        with open(backup_path, 'w') as dst:
            dst.write(content)
            
        return backup_path
    
    def rollback(self, crash_id: str) -> Dict[str, Any]:
        """Rollback a fix using backup."""
        crash_file = CRASH_LOG_DIR / f"{crash_id}.json"
        
        with open(crash_file, 'r') as f:
            crash = json.load(f)
            
        backup_path = crash.get("backup_path")
        if not backup_path or not os.path.exists(backup_path):
            return {"success": False, "error": "Backup not found"}
            
        file_path = crash.get("file_path")
        
        try:
            with open(backup_path, 'r') as src:
                content = src.read()
            with open(file_path, 'w') as dst:
                dst.write(content)
                
            crash["status"] = "rolled_back"
            with open(crash_file, 'w') as f:
                json.dump(crash, f, indent=2)
                
            return {"success": True, "message": f"Rolled back {file_path}"}
            
        except Exception as e:
            return {"success": False, "error": f"Rollback failed: {str(e)}"}


class PackageInstaller:
    """Autonomous package installation for new features."""
    
    def __init__(self):
        self.venv_path = PROJECT_ROOT / "venv"
        self.requirements_file = PROJECT_ROOT / "requirements.txt"
        
    def find_missing_packages(self, code_request: str) -> List[str]:
        """Use Qwen to identify packages needed for a feature."""
        llm = get_coding_llm()
        
        prompt = f"""A new feature was requested: "{code_request}"

List the Python packages that would need to be installed to implement this.
Only list widely-used, stable packages from PyPI.
Return as a simple comma-separated list, nothing else.

Example response: requests, pandas, numpy
"""
        try:
            response = llm.invoke(prompt)
            # Parse comma-separated packages
            packages = [p.strip() for p in response.split(',') if p.strip()]
            return packages
        except Exception:
            return []
    
    def is_installed(self, package: str) -> bool:
        """Check if package is installed in venv."""
        try:
            __import__(package.split('[')[0].replace('-', '_'))
            return True
        except ImportError:
            return False
    
    def install_package(self, package: str) -> Dict[str, Any]:
        """Install a package into the venv."""
        if self.is_installed(package):
            return {"success": True, "message": f"{package} already installed", "installed": False}
            
        try:
            # Use pip to install
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                # Update requirements.txt
                self._update_requirements(package)
                
                return {
                    "success": True,
                    "message": f"Installed {package}",
                    "installed": True,
                    "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Installation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_requirements(self, package: str):
        """Add package to requirements.txt if not present."""
        if not self.requirements_file.exists():
            self.requirements_file.write_text("")
            
        content = self.requirements_file.read_text()
        if package not in content:
            with open(self.requirements_file, 'a') as f:
                f.write(f"\n{package}")


# Global instances
crash_monitor = CrashMonitor()
fix_proposer = FixProposer()
fix_applicator = FixApplicator()
package_installer = PackageInstaller()


def check_for_crashes() -> List[Dict[str, Any]]:
    """Public function to scan for new crashes."""
    return crash_monitor.scan_logs()


def propose_fix_for_crash(crash_id: str) -> Dict[str, Any]:
    """Public function to analyze and propose fix."""
    crash_file = CRASH_LOG_DIR / f"{crash_id}.json"
    
    if not crash_file.exists():
        return {"error": "Crash not found"}
        
    with open(crash_file, 'r') as f:
        crash = json.load(f)
        
    return fix_proposer.analyze_crash(crash)


def apply_fix(crash_id: str) -> Dict[str, Any]:
    """Public function to apply approved fix."""
    return fix_applicator.apply_fix(crash_id)


def auto_install_for_feature(feature_request: str) -> Dict[str, Any]:
    """Identify and install packages for a new feature."""
    packages = package_installer.find_missing_packages(feature_request)
    
    if not packages:
        return {"success": True, "message": "No new packages needed", "installed": []}
        
    results = []
    for pkg in packages:
        if not package_installer.is_installed(pkg):
            result = package_installer.install_package(pkg)
            results.append({"package": pkg, "result": result})
        else:
            results.append({"package": pkg, "result": {"already_installed": True}})
            
    return {
        "success": all(r["result"].get("success", True) for r in results),
        "packages_checked": packages,
        "installations": results
    }


def format_crash_for_chat(crash: Dict[str, Any], fix: Dict[str, Any]) -> str:
    """Format crash and fix for LOVE's companion chat."""
    error_type = crash.get("error_type", "Unknown error")
    file_path = crash.get("file_path", "unknown file")
    
    analysis = fix.get("analysis", "No analysis available")
    proposed = fix.get("proposed_fix", "No fix proposed")
    confidence = fix.get("confidence", "unknown")
    can_auto = fix.get("can_auto_apply", False)
    
    if can_auto and confidence == "high":
        tone = "I've spotted an error and I can fix it right now."
        action = "Say 'Fix it' and I'll patch it immediately."
    else:
        tone = "I found an error that needs your eyes on it."
        action = "Want me to explain what's wrong before we fix it?"
    
    return f"""{tone}

**Error**: {error_type} in `{file_path}`

**What happened**: {analysis}

**Proposed fix**: {proposed}

{action}"""


class ContinuousImprovement:
    """Proactive code optimization and self-refactoring agent."""
    
    def __init__(self):
        self.llm = get_coding_llm()
        self.optimization_log = CRASH_LOG_DIR.parent / "optimizations.json"
        self.performance_baseline = {}
        
    def profile_api_performance(self) -> Dict[str, Any]:
        """Profile API response times and reasoning paths."""
        import time
        
        # Simulate profiling (in production, this would use actual timing data)
        # Check API log for response times
        results = {
            "timestamp": datetime.now().isoformat(),
            "tools_profiled": [],
            "slow_operations": [],
            "reasoning_vs_coding_ratio": {"reasoning": 0, "coding": 0}
        }
        
        # Profile finance.py if it exists
        finance_path = PROJECT_ROOT / "tools" / "finance.py"
        if finance_path.exists():
            file_size = finance_path.stat().st_size
            results["tools_profiled"].append({
                "file": "finance.py",
                "size_bytes": file_size,
                "lines": len(finance_path.read_text().split('\n'))
            })
            
            # Check if file is large (potential optimization target)
            if file_size > 20000:  # > 20KB
                results["slow_operations"].append({
                    "file": "finance.py",
                    "issue": "Large file size",
                    "suggestion": "Consider splitting into modules"
                })
        
        # Profile guardian.py
        guardian_path = PROJECT_ROOT / "tools" / "guardian.py"
        if guardian_path.exists():
            file_size = guardian_path.stat().st_size
            results["tools_profiled"].append({
                "file": "guardian.py",
                "size_bytes": file_size,
                "lines": len(guardian_path.read_text().split('\n'))
            })
        
        return results
    
    def analyze_for_optimization(self, file_path: Path) -> Dict[str, Any]:
        """Use Qwen to analyze code for optimization opportunities."""
        if not file_path.exists():
            return {"error": "File not found"}
        
        content = file_path.read_text()
        
        prompt = f"""You are LOVE's Continuous Improvement agent. Analyze this Python code for optimization opportunities.

FILE: {file_path.name}

CODE:
```python
{content[:2000]}  # First 2000 chars for analysis
```

Look for:
1. Inefficient algorithms or loops
2. Duplicate code that could be refactored
3. Heavy operations that could be cached
4. Unnecessary imports or complexity
5. API calls that could be batched

Return a JSON object:
{{
    "optimizations_found": true/false,
    "issues": [
        {{
            "line": line_number,
            "severity": "high/medium/low",
            "description": "what's inefficient",
            "impact": "time/memory savings estimate",
            "refactored_code": "optimized version"
        }}
    ],
    "estimated_improvement": "e.g., '20% faster'",
    "safe_to_apply": true/false
}}

Be specific and practical. Only suggest changes that are safe and measurable."""

        try:
            response = self.llm.invoke(prompt)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {
                    "optimizations_found": False,
                    "issues": [],
                    "estimated_improvement": "0%",
                    "safe_to_apply": False
                }
            
            return analysis
            
        except Exception as e:
            return {
                "optimizations_found": False,
                "error": str(e),
                "issues": []
            }
    
    def draft_refactored_version(self, file_path: Path, optimization: Dict) -> str:
        """Create a refactored version in a temp file for testing."""
        temp_dir = DATA_DIR / "refactor_tests"
        temp_dir.mkdir(exist_ok=True)
        
        original_content = file_path.read_text()
        
        # Apply the optimization
        refactored = original_content
        for issue in optimization.get("issues", []):
            if issue.get("refactored_code") and issue.get("line"):
                # Simple line-based replacement (in production, use AST)
                lines = refactored.split('\n')
                line_idx = issue["line"] - 1
                if 0 <= line_idx < len(lines):
                    lines[line_idx] = issue["refactored_code"]
                    refactored = '\n'.join(lines)
        
        # Save to temp file
        temp_file = temp_dir / f"{file_path.stem}_refactored.py"
        temp_file.write_text(refactored)
        
        return str(temp_file)
    
    def should_run_sunday_check(self) -> bool:
        """Check if it's Sunday midnight - time for optimization review."""
        now = datetime.now()
        return now.weekday() == 6 and now.hour == 0 and now.minute < 5
    
    def run_weekly_optimization(self) -> Dict[str, Any]:
        """Run the Sunday midnight optimization check."""
        if not self.should_run_sunday_check():
            return {"ran": False, "reason": "Not Sunday midnight"}
        
        # Profile current performance
        profile = self.profile_api_performance()
        
        optimizations = []
        
        # Analyze tools for optimization
        tools_dir = PROJECT_ROOT / "tools"
        for py_file in tools_dir.glob("*.py"):
            analysis = self.analyze_for_optimization(py_file)
            
            if analysis.get("optimizations_found") and analysis.get("safe_to_apply"):
                # Create refactored version
                temp_file = self.draft_refactored_version(py_file, analysis)
                
                optimizations.append({
                    "file": py_file.name,
                    "improvement": analysis.get("estimated_improvement", "unknown"),
                    "issues_count": len(analysis.get("issues", [])),
                    "temp_file": temp_file,
                    "can_apply": True
                })
        
        # Log the optimization check
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "profile": profile,
            "optimizations_found": optimizations
        }
        
        # Save to log
        if self.optimization_log.exists():
            with open(self.optimization_log, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(log_entry)
        with open(self.optimization_log, 'w') as f:
            json.dump(history[-10:], f, indent=2)  # Keep last 10
        
        return {
            "ran": True,
            "optimizations_found": len(optimizations),
            "optimizations": optimizations,
            "love_message": self._format_optimization_message(optimizations)
        }
    
    def _format_optimization_message(self, optimizations: List[Dict]) -> str:
        """Format optimization findings for LOVE's chat."""
        if not optimizations:
            return "Weekly code review complete. Everything's running tight—no optimizations needed."
        
        top_opt = optimizations[0]
        return f"""Weekly self-review done. Found a way to make {top_opt['file']} {top_opt['improvement']} faster by fixing {top_opt['issues_count']} inefficiencies. 

I've drafted the changes in a test file. Want me to apply the update? Say 'Apply optimization' and I'll make it happen."""
    
    def apply_optimization(self, file_name: str) -> Dict[str, Any]:
        """Apply a refactored optimization after user approves."""
        # Find the temp file
        temp_dir = DATA_DIR / "refactor_tests"
        temp_file = temp_dir / f"{Path(file_name).stem}_refactored.py"
        target_file = PROJECT_ROOT / "tools" / file_name
        
        if not temp_file.exists():
            return {"success": False, "error": "Refactored version not found"}
        
        if not target_file.exists():
            return {"success": False, "error": "Target file not found"}
        
        try:
            # Backup original
            backup_path = fix_applicator._create_backup(str(target_file))
            
            # Apply refactored version
            refactored_content = temp_file.read_text()
            target_file.write_text(refactored_content)
            
            return {
                "success": True,
                "message": f"Applied optimization to {file_name}",
                "backup": str(backup_path),
                "improvement": "Code refactored for better performance"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instances for new features
continuous_improvement = ContinuousImprovement()


def run_weekly_optimization_check() -> Dict[str, Any]:
    """Public function to trigger weekly optimization."""
    return continuous_improvement.run_weekly_optimization()


def apply_code_optimization(file_name: str) -> Dict[str, Any]:
    """Public function to apply optimization after approval."""
    return continuous_improvement.apply_optimization(file_name)


def get_optimization_status() -> Dict[str, Any]:
    """Get current optimization status."""
    profile = continuous_improvement.profile_api_performance()
    
    # Check for pending optimizations
    temp_dir = DATA_DIR / "refactor_tests"
    pending = []
    if temp_dir.exists():
        for temp_file in temp_dir.glob("*_refactored.py"):
            original_name = temp_file.stem.replace("_refactored", ".py")
            pending.append({
                "file": original_name,
                "temp_file": str(temp_file),
                "ready_to_apply": True
            })
    
    return {
        "current_profile": profile,
        "pending_optimizations": pending,
        "next_scheduled_check": "Sunday midnight"
    }
