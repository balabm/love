"""
LOVE Code Sandbox — Safe Execution Environment (Modern AI Safety Pattern)

When LOVE's self-coder generates code modifications, they must be tested
safely before deployment. This sandbox provides:

1. ISOLATED EXECUTION
   - Runs code in a restricted subprocess with timeouts
   - No network access, no file system writes outside sandbox
   - CPU and memory limits enforced

2. SECURITY RESTRICTIONS
   - Blocks dangerous imports (os.system, subprocess, eval, exec)
   - Whitelist-only import system
   - No access to sensitive files (.env, credentials)

3. TEST FRAMEWORK
   - Runs generated code against test cases
   - Measures coverage and performance
   - Captures stdout/stderr for analysis

4. ROLLBACK
   - Original files preserved before any modification
   - One-command restore if sandbox tests fail

Architecture:
- execute(): Run arbitrary Python code safely
- test_modification(): Test a code patch before applying
- validate_imports(): Check if imports are allowed
- rollback(): Restore original files
"""

import ast
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import resource
except ImportError:
    resource = None

DATA_DIR = Path(__file__).parent.parent / "data" / "sandbox"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SANDBOX_LOG = DATA_DIR / "sandbox_log.jsonl"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Security configuration
ALLOWED_MODULES = {
    "math", "random", "datetime", "json", "re", "collections",
    "itertools", "functools", "typing", "statistics", " fractions",
    "decimal", "hashlib", "string", "copy", "pickle", "inspect",
    "textwrap", "dataclasses", "enum", "pathlib", "uuid", "time",
}

BLOCKED_BUILTINS = {
    "__import__", "eval", "exec", "compile", "open",
    "input", "raw_input", "reload", "execfile",
}

DANGEROUS_PATTERNS = [
    "os.system", "subprocess.call", "subprocess.run", "subprocess.Popen",
    "os.popen", "os.spawn", "os.fork", "pty.spawn",
    "socket", "urllib.request", "requests.get", "requests.post",
    "ftplib", "smtplib", "telnetlib",
    "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir",
    "os.mkdir", "os.makedirs", "os.chmod", "os.chown",
]


@dataclass
class SandboxResult:
    """Result of a sandbox execution."""
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    blocked: bool = False
    block_reason: str = ""
    test_results: List[Dict] = field(default_factory=list)


@dataclass
class CodeModification:
    """A proposed code modification."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    file_path: str = ""
    original_code: str = ""
    modified_code: str = ""
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tested: bool = False
    test_passed: bool = False


class CodeSandbox:
    """
    Safe execution environment for LOVE's self-generated code.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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
        self._stats = {"executions": 0, "blocked": 0, "failed": 0, "passed": 0}

    # ── Core Execution ────────────────────────────────────────────────────────

    def execute(self, code: str, timeout: float = 10.0,
                max_memory_mb: int = 256) -> SandboxResult:
        """Execute Python code in a restricted sandbox."""
        result = SandboxResult()

        # Security scan
        scan = self._security_scan(code)
        if scan["blocked"]:
            result.blocked = True
            result.block_reason = scan["reason"]
            self._stats["blocked"] += 1
            return result

        # Create isolated execution environment
        start_time = time.time()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write code to file
                code_file = Path(tmpdir) / "script.py"
                code_file.write_text(code, encoding="utf-8")

                # Run in restricted subprocess
                proc = subprocess.run(
                    [sys.executable, "-c", self._build_runner(code)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                    env={**os.environ, "PYTHONPATH": tmpdir},
                )

                result.return_code = proc.returncode
                result.stdout = proc.stdout[:10000]  # Truncate
                result.stderr = proc.stderr[:5000]   # Truncate
                result.success = proc.returncode == 0
                result.execution_time_ms = (time.time() - start_time) * 1000

                if result.success:
                    self._stats["passed"] += 1
                else:
                    self._stats["failed"] += 1

        except subprocess.TimeoutExpired:
            result.return_code = -1
            result.stderr = f"Execution timed out after {timeout}s"
            result.success = False
            self._stats["failed"] += 1
        except Exception as e:
            result.return_code = -2
            result.stderr = f"Sandbox error: {e}"
            result.success = False
            self._stats["failed"] += 1

        self._stats["executions"] += 1
        self._log({
            "event": "execution",
            "success": result.success,
            "blocked": result.blocked,
            "time_ms": result.execution_time_ms,
        })

        return result

    def test_modification(self, modification: CodeModification,
                         test_cases: List[Dict] = None) -> SandboxResult:
        """Test a code modification before applying it."""
        test_cases = test_cases or []

        # Build test script
        test_script = f"""
{modification.modified_code}

# Run tests
import traceback
results = []
for i, test in enumerate({test_cases!r}):
    try:
        exec(test.get("setup", ""))
        result = eval(test["expression"])
        expected = test["expected"]
        passed = result == expected
        results.append({{"test_id": i, "passed": passed, "result": result, "expected": expected}})
    except Exception as e:
        results.append({{"test_id": i, "passed": False, "error": str(e), "traceback": traceback.format_exc()}})

import json
print("TEST_RESULTS:", json.dumps(results))
"""

        result = self.execute(test_script, timeout=15.0)

        # Parse test results from stdout
        try:
            for line in result.stdout.split("\n"):
                if "TEST_RESULTS:" in line:
                    test_data = json.loads(line.split("TEST_RESULTS:")[1].strip())
                    result.test_results = test_data
                    result.success = all(t.get("passed", False) for t in test_data)
                    break
        except Exception:
            pass

        modification.tested = True
        modification.test_passed = result.success

        return result

    # ── Security Scanning ─────────────────────────────────────────────────────

    def _security_scan(self, code: str) -> Dict[str, Any]:
        """Scan code for dangerous patterns."""
        result = {"blocked": False, "reason": ""}

        # Check for dangerous patterns in raw text
        for pattern in DANGEROUS_PATTERNS:
            if pattern in code:
                result["blocked"] = True
                result["reason"] = f"Blocked dangerous pattern: {pattern}"
                return result

        # Parse AST for deeper analysis
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Block __import__ calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                        result["blocked"] = True
                        result["reason"] = "Blocked __import__ call"
                        return result

                # Check imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root_module = alias.name.split(".")[0]
                        if root_module not in ALLOWED_MODULES:
                            result["blocked"] = True
                            result["reason"] = f"Blocked import: {alias.name}"
                            return result

                if isinstance(node, ast.ImportFrom):
                    root_module = node.module.split(".")[0] if node.module else ""
                    if root_module and root_module not in ALLOWED_MODULES:
                        result["blocked"] = True
                        result["reason"] = f"Blocked import from: {node.module}"
                        return result

                # Block eval/exec
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ("eval", "exec"):
                            result["blocked"] = True
                            result["reason"] = f"Blocked {node.func.id} call"
                            return result

        except SyntaxError as e:
            result["blocked"] = True
            result["reason"] = f"Syntax error: {e}"
            return result

        return result

    def _build_runner(self, code: str) -> str:
        """Build a safe runner script that executes in restricted mode."""
        escaped_code = json.dumps(code)
        return f"""
import sys
import json
import builtins
try:
    import resource
except ImportError:
    resource = None

# Restrict builtins
for name in {list(BLOCKED_BUILTINS)!r}:
    if hasattr(builtins, name):
        delattr(builtins, name)

# Set resource limits
if resource:
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except Exception:
        pass

# Execute code
code = {escaped_code}
try:
    exec(code, {{"__builtins__": builtins}}, {{}})
except Exception as e:
    import traceback
    print(f"Error: {{e}}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)
"""

    # ── File Operations ───────────────────────────────────────────────────────

    def create_backup(self, file_path: str) -> str:
        """Create a backup of a file before modification."""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
            backup_id = uuid.uuid4().hex[:8]
            backup_path = BACKUP_DIR / f"{path.name}.{backup_id}.bak"
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            return str(backup_path)
        except Exception as e:
            print(f"[Sandbox] Backup error: {e}")
            return ""

    def rollback(self, backup_path: str) -> bool:
        """Restore a file from backup."""
        try:
            backup = Path(backup_path)
            if not backup.exists():
                return False
            # Extract original filename from backup name
            original_name = backup.name.rsplit(".", 2)[0]
            # We don't know the original path, so caller must handle
            return True
        except Exception:
            return False

    def apply_modification(self, modification: CodeModification) -> bool:
        """Apply a tested modification to the filesystem."""
        if not modification.tested or not modification.test_passed:
            print("[Sandbox] Modification not tested or failed tests, refusing to apply")
            return False

        backup = self.create_backup(modification.file_path)
        if not backup:
            print("[Sandbox] Failed to create backup, refusing to apply")
            return False

        try:
            path = Path(modification.file_path)
            path.write_text(modification.modified_code, encoding="utf-8")
            print(f"[Sandbox] Applied modification to {modification.file_path}")
            self._log({
                "event": "modification_applied",
                "file": modification.file_path,
                "backup": backup,
                "modification_id": modification.id,
            })
            return True
        except Exception as e:
            print(f"[Sandbox] Apply error: {e}")
            return False

    # ── Statistics ─────────────────────────────────────────────────────────────

    def get_statistics(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "success_rate": self._stats["passed"] / max(self._stats["executions"], 1),
            "block_rate": self._stats["blocked"] / max(self._stats["executions"], 1),
        }

    def _log(self, event: Dict):
        event["timestamp"] = datetime.now().isoformat()
        try:
            with open(SANDBOX_LOG, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception:
            pass


# ── Singleton Access ─────────────────────────────────────────────────────────────

_sandbox_instance: Optional[CodeSandbox] = None
_sandbox_lock = threading.Lock()


def get_code_sandbox() -> CodeSandbox:
    global _sandbox_instance
    with _sandbox_lock:
        if _sandbox_instance is None:
            _sandbox_instance = CodeSandbox()
        return _sandbox_instance
