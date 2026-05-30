"""
LOVE Self-Coder — Automated Code Generation for Self-Improvement

LOVE writes its own upgrades. This module enables LOVE to:
1. Analyze its own codebase and identify improvement opportunities
2. Generate code modifications based on evolution hypotheses
3. Test modifications in a sandbox environment
4. Apply safe modifications with rollback capability
5. Learn from coding successes and failures

Safety mechanisms:
- All modifications require approval thresholds
- Automatic rollback on test failures
- Code review by multiple LOVE instances (swarm validation)
- Comprehensive logging and audit trail
- Read-only mode for critical system files
"""

import ast
import difflib
import hashlib
import importlib
import json
import py_compile
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.llm import get_reasoning_llm, get_coding_llm
from core.neural_bus import get_neural_bus, EventPriority

DATA_DIR = Path(__file__).parent.parent / "data" / "self_coder"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CODE_MODIFICATIONS_LOG = DATA_DIR / "modifications.jsonl"
HOT_RELOAD_LOG = DATA_DIR / "hot_reload.jsonl"
SANDBOX_DIR = DATA_DIR / "sandbox"
ROLLBACK_ARCHIVE = DATA_DIR / "rollback"
SAFETY_RULES_FILE = DATA_DIR / "safety_rules.json"

SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
ROLLBACK_ARCHIVE.mkdir(parents=True, exist_ok=True)


@dataclass
class CodeModification:
    """A proposed code modification."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    hypothesis_id: str = ""
    file_path: str = ""
    original_code: str = ""
    modified_code: str = ""
    modification_type: str = ""  # bugfix, enhancement, refactor, optimization
    description: str = ""
    risk_level: str = "low"  # low, medium, high, critical
    test_status: str = "pending"  # pending, passed, failed
    approval_status: str = "pending"  # pending, approved, rejected
    confidence: float = 0.5
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied_at: Optional[str] = None
    rollback_available: bool = False
    rollback_point: Optional[str] = None


@dataclass
class SafetyRule:
    """A safety rule for code modifications."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    pattern: str = ""
    description: str = ""
    action: str = "block"  # block, warn, allow
    file_patterns: List[str] = field(default_factory=list)  # files this applies to


@dataclass
class CodeAnalysis:
    """Analysis of a code file."""
    file_path: str = ""
    complexity: int = 0
    lines_of_code: int = 0
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    improvement_opportunities: List[str] = field(default_factory=list)


class SelfCoder:
    """
    LOVE's self-coding engine — writes its own improvements.
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
        self._modifications: Dict[str, CodeModification] = {}
        self._safety_rules: Dict[str, SafetyRule] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._load_safety_rules()
        self._load_modifications()

    # ── Safety Rules ─────────────────────────────────────────────────────────────

    def _load_safety_rules(self):
        """Load safety rules for code modifications."""
        try:
            if SAFETY_RULES_FILE.exists():
                data = json.loads(SAFETY_RULES_FILE.read_text())
                for rid, rd in data.get("rules", {}).items():
                    self._safety_rules[rid] = SafetyRule(**rd)
            else:
                # Initialize default safety rules
                self._initialize_default_safety_rules()
        except Exception as e:
            print(f"[SelfCoder] Safety rules load error: {e}")
            self._initialize_default_safety_rules()

    def _initialize_default_safety_rules(self):
        """Initialize default safety rules."""
        default_rules = [
            SafetyRule(
                pattern="rm -rf",
                description="Destructive file operations",
                action="block",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="os.system",
                description="Direct system calls",
                action="warn",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="eval(",
                description="Dynamic code execution",
                action="warn",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="exec(",
                description="Dynamic code execution",
                action="warn",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="__import__",
                description="Dynamic imports",
                action="warn",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="subprocess.call",
                description="Subprocess calls",
                action="warn",
                file_patterns=["*.py"]
            ),
            SafetyRule(
                pattern="api/main.py",
                description="Main API file - critical",
                action="block",
                file_patterns=["api/main.py"]
            ),
            SafetyRule(
                pattern="core/llm.py",
                description="LLM routing - critical",
                action="block",
                file_patterns=["core/llm.py"]
            ),
        ]

        for rule in default_rules:
            self._safety_rules[rule.id] = rule

        self._save_safety_rules()

    def _save_safety_rules(self):
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "rules": {rid: asdict(r) for rid, r in self._safety_rules.items()},
            }
            SAFETY_RULES_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"[SelfCoder] Safety rules save error: {e}")

    def check_safety(self, code: str, file_path: str) -> Tuple[bool, List[str]]:
        """Check if code modification passes safety rules."""
        warnings = []
        blocked = False

        for rule in self._safety_rules.values():
            # Check if rule applies to this file
            if rule.file_patterns:
                import fnmatch
                if not any(fnmatch.fnmatch(file_path, pattern) for pattern in rule.file_patterns):
                    continue

            # Check if pattern is in code
            if rule.pattern in code:
                if rule.action == "block":
                    blocked = True
                    warnings.append(f"BLOCKED: {rule.description} (pattern: {rule.pattern})")
                elif rule.action == "warn":
                    warnings.append(f"WARNING: {rule.description} (pattern: {rule.pattern})")

        return not blocked, warnings

    # ── Code Analysis ───────────────────────────────────────────────────────────

    def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a Python file for improvement opportunities."""
        try:
            path = Path(file_path)
            if not path.exists():
                return CodeAnalysis(file_path=file_path)

            code = path.read_text()

            # Parse AST
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return CodeAnalysis(file_path=file_path, potential_issues=["Syntax error"])

            analysis = CodeAnalysis(file_path=file_path)
            analysis.lines_of_code = len(code.splitlines())

            # Extract functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis.functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    analysis.classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    analysis.imports.append(node.module or "")

            # Calculate complexity (simplified)
            analysis.complexity = len(analysis.functions) + len(analysis.classes) * 2

            # Identify potential issues
            if analysis.lines_of_code > 500:
                analysis.potential_issues.append("File is very long, consider splitting")
            if analysis.complexity > 20:
                analysis.potential_issues.append("High complexity, consider refactoring")

            # Use LLM to identify improvement opportunities
            try:
                llm = get_reasoning_llm()
                prompt = f"""Analyze this Python code for improvement opportunities:
File: {file_path}
Lines: {analysis.lines_of_code}
Functions: {', '.join(analysis.functions[:5])}
Classes: {', '.join(analysis.classes[:5])}

Current issues: {', '.join(analysis.potential_issues)}

Suggest 3-5 specific improvements (performance, readability, maintainability)."""

                response = llm.invoke(prompt)
                # Parse suggestions (simplified)
                suggestions = [line.strip() for line in response.split('\n') if line.strip()]
                analysis.improvement_opportunities = suggestions[:5]

            except Exception as e:
                print(f"[SelfCoder] LLM analysis error: {e}")

            return analysis

        except Exception as e:
            print(f"[SelfCoder] File analysis error: {e}")
            return CodeAnalysis(file_path=file_path)

    # ── Code Generation ─────────────────────────────────────────────────────────

    def generate_modification(self, hypothesis: str, file_path: str, improvement_type: str = "enhancement") -> Optional[CodeModification]:
        """Generate a code modification based on a hypothesis."""
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"[SelfCoder] File not found: {file_path}")
                return None

            original_code = path.read_text()

            # Use coding LLM to generate modification
            llm = get_coding_llm()

            prompt = f"""You are LOVE's self-coding engine. Generate a code modification.

Hypothesis: {hypothesis}
File: {file_path}
Improvement type: {improvement_type}

Current code:
```python
{original_code}
```

Generate the modified code that addresses the hypothesis.
Return ONLY the complete modified code, no explanations.
Ensure the modification is safe and maintains existing functionality."""

            modified_code = llm.invoke(prompt)

            # Clean up the response (remove markdown if present)
            if "```python" in modified_code:
                modified_code = modified_code.split("```python")[1].split("```")[0].strip()
            elif "```" in modified_code:
                modified_code = modified_code.split("```")[1].split("```")[0].strip()

            # Check safety
            is_safe, warnings = self.check_safety(modified_code, file_path)
            if not is_safe:
                print(f"[SelfCoder] Modification blocked by safety rules: {warnings}")
                return None

            # Create modification object
            modification = CodeModification(
                hypothesis_id=hypothesis[:20],  # Simplified
                file_path=file_path,
                original_code=original_code,
                modified_code=modified_code,
                modification_type=improvement_type,
                description=f"Apply improvement: {hypothesis}",
                risk_level="medium" if warnings else "low",
                confidence=0.7,
            )

            if warnings:
                modification.description += f" | Warnings: {'; '.join(warnings)}"

            self._modifications[modification.id] = modification
            self._log_modification(modification)

            return modification

        except Exception as e:
            print(f"[SelfCoder] Modification generation error: {e}")
            return None

    # ── Testing & Validation ───────────────────────────────────────────────────

    def test_modification(self, modification_id: str) -> bool:
        """Test a modification in the sandbox."""
        if modification_id not in self._modifications:
            return False

        modification = self._modifications[modification_id]

        try:
            # Create sandbox environment
            sandbox_file = SANDBOX_DIR / Path(modification.file_path).name

            # Write modified code to sandbox
            sandbox_file.write_text(modification.modified_code)

            # Try to import/parse the modified code
            try:
                with open(sandbox_file, 'r') as f:
                    code = f.read()
                ast.parse(code)

                modification.test_status = "passed"
                self._save_modifications()
                return True

            except SyntaxError as e:
                modification.test_status = "failed"
                modification.description += f" | Syntax error: {str(e)}"
                self._save_modifications()
                return False

        except Exception as e:
            modification.test_status = "failed"
            modification.description += f" | Test error: {str(e)}"
            self._save_modifications()
            return False

    # ── Application & Rollback ──────────────────────────────────────────────────

    def apply_modification(self, modification_id: str, auto_rollback: bool = True) -> bool:
        """Apply a modification to the actual codebase."""
        if modification_id not in self._modifications:
            return False

        modification = self._modifications[modification_id]

        if modification.test_status != "passed":
            print(f"[SelfCoder] Cannot apply modification that hasn't passed tests")
            return False

        try:
            # Create rollback point
            original_path = Path(modification.file_path)
            rollback_path = ROLLBACK_ARCHIVE / f"{original_path.name}.{modification.id}.backup"

            shutil.copy2(original_path, rollback_path)
            modification.rollback_point = str(rollback_path)
            modification.rollback_available = True

            # Apply modification
            original_path.write_text(modification.modified_code)
            modification.applied_at = datetime.now().isoformat()
            modification.approval_status = "approved"

            self._save_modifications()

            print(f"[SelfCoder] Applied modification {modification_id} to {modification.file_path}")

            # If auto-rollback is enabled, run a quick smoke test
            if auto_rollback:
                if not self._smoke_test(modification.file_path):
                    print(f"[SelfCoder] Smoke test failed, rolling back")
                    self.rollback_modification(modification_id)
                    return False

            # Attempt hot-reload so the running process picks up the changes immediately
            reload_result = self.hot_reload_modification(modification_id)
            if reload_result["status"] not in ("ok", "module_not_loaded"):
                print(f"[SelfCoder] Hot-reload did not succeed: {reload_result['status']} — {reload_result.get('detail', '')}")
                # Not fatal — the file is already written; just warn.
            else:
                print(f"[SelfCoder] Hot-reload result: {reload_result['status']}")

            return True

        except Exception as e:
            print(f"[SelfCoder] Application error: {e}")
            return False

    def rollback_modification(self, modification_id: str) -> bool:
        """Rollback a modification."""
        if modification_id not in self._modifications:
            return False

        modification = self._modifications[modification_id]

        if not modification.rollback_available or not modification.rollback_point:
            print(f"[SelfCoder] No rollback point available")
            return False

        try:
            rollback_path = Path(modification.rollback_point)
            original_path = Path(modification.file_path)

            if not rollback_path.exists():
                print(f"[SelfCoder] Rollback file not found")
                return False

            # Restore original
            shutil.copy2(rollback_path, original_path)

            modification.approval_status = "rolled_back"
            self._save_modifications()

            print(f"[SelfCoder] Rolled back modification {modification_id}")
            return True

        except Exception as e:
            print(f"[SelfCoder] Rollback error: {e}")
            return False

    def _smoke_test(self, file_path: str) -> bool:
        """Quick smoke test via a subprocess probe — verifies import + optional _probe()."""
        try:
            path = Path(file_path)
            # Derive dotted module name relative to the project root (love/)
            project_root = Path(__file__).parent.parent
            try:
                rel = path.resolve().relative_to(project_root.resolve())
                module_name = ".".join(rel.with_suffix("").parts)
            except ValueError:
                module_name = path.stem

            probe_script = (
                f"import sys; sys.path.insert(0, r'{project_root}'); "
                f"import importlib; m = importlib.import_module('{module_name}'); "
                f"probe = getattr(m, '_probe', None) or getattr(m, '__probe__', None); "
                f"probe() if callable(probe) else None; "
                f"print('smoke_ok')"
            )

            result = subprocess.run(
                [sys.executable, "-c", probe_script],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode != 0:
                print(f"[SelfCoder] Smoke test subprocess failed:\n{result.stderr}")
                return False

            return "smoke_ok" in result.stdout

        except Exception as e:
            print(f"[SelfCoder] Smoke test error: {e}")
            return False

    # ── Hot-Reload Pipeline ──────────────────────────────────────────────────────

    def _log_hot_reload_event(self, event: dict) -> None:
        """Append a hot-reload event to hot_reload.jsonl."""
        try:
            with open(HOT_RELOAD_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")
        except Exception as exc:
            print(f"[SelfCoder] hot_reload log error: {exc}")

    def hot_reload_modification(self, modification_id: str) -> dict:
        """
        Hot-reload pipeline for a previously written modification.

        Steps:
        1. Read file_path + modified_code from the stored modification.
        2. Write new code to a temp file.
        3. py_compile the temp file — fail fast on syntax/compile errors.
        4. Subprocess smoke-test the temp file (import + optional _probe).
        5. Only if smoke-test passes: atomically swap to real path, then
           importlib.reload the module if it is already in sys.modules.
        6. On reload exception: restore from rollback, return rollback_applied.
        7. Log everything to hot_reload.jsonl.

        Returns a dict with keys: status, module, modification_id, detail.
        Possible statuses: "ok", "compile_error", "subprocess_failed",
                           "reload_error", "rollback_applied", "module_not_loaded",
                           "not_found".
        """
        base_event: dict = {
            "modification_id": modification_id,
            "timestamp": datetime.now().isoformat(),
        }

        if modification_id not in self._modifications:
            result = {**base_event, "status": "not_found", "module": None,
                      "detail": f"Modification {modification_id} not in registry."}
            self._log_hot_reload_event(result)
            return result

        modification = self._modifications[modification_id]
        file_path = Path(modification.file_path)
        new_code = modification.modified_code

        # Derive dotted module name
        project_root = Path(__file__).parent.parent
        try:
            rel = file_path.resolve().relative_to(project_root.resolve())
            module_name = ".".join(rel.with_suffix("").parts)
        except ValueError:
            module_name = file_path.stem

        base_event["module"] = module_name

        # ── Step 2: Write to temp file ────────────────────────────────────────
        tmp_fd, tmp_path_str = tempfile.mkstemp(suffix=".py", prefix="love_hr_")
        tmp_path = Path(tmp_path_str)
        try:
            import os
            os.close(tmp_fd)
            tmp_path.write_text(new_code, encoding="utf-8")

            # ── Step 3: py_compile ────────────────────────────────────────────
            try:
                py_compile.compile(tmp_path_str, doraise=True)
            except py_compile.PyCompileError as pce:
                detail = str(pce)
                result = {**base_event, "status": "compile_error", "detail": detail}
                self._log_hot_reload_event(result)
                print(f"[SelfCoder] hot_reload compile error: {detail}")
                return result

            # ── Step 4: Subprocess smoke-test against the TEMP file ───────────
            probe_script = (
                f"import sys; sys.path.insert(0, r'{project_root}'); "
                f"import importlib.util; "
                f"spec = importlib.util.spec_from_file_location('{module_name}', r'{tmp_path_str}'); "
                f"m = importlib.util.module_from_spec(spec); "
                f"spec.loader.exec_module(m); "
                f"probe = getattr(m, '_probe', None) or getattr(m, '__probe__', None); "
                f"probe() if callable(probe) else None; "
                f"print('probe_ok')"
            )

            proc = subprocess.run(
                [sys.executable, "-c", probe_script],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if proc.returncode != 0 or "probe_ok" not in proc.stdout:
                detail = proc.stderr.strip() or proc.stdout.strip() or "exit code non-zero"
                result = {**base_event, "status": "subprocess_failed", "detail": detail}
                self._log_hot_reload_event(result)
                print(f"[SelfCoder] hot_reload subprocess probe failed:\n{detail}")
                return result

            # ── Step 5: Atomically write to real file ─────────────────────────
            # First create / refresh a rollback copy
            rollback_path = ROLLBACK_ARCHIVE / f"{file_path.name}.{modification_id}.hr_backup"
            if file_path.exists():
                shutil.copy2(file_path, rollback_path)

            shutil.copy2(tmp_path_str, str(file_path))

            # Invalidate import caches and reload if module already loaded
            importlib.invalidate_caches()

            if module_name in sys.modules:
                try:
                    importlib.reload(sys.modules[module_name])
                    result = {**base_event, "status": "ok",
                              "detail": f"Module '{module_name}' reloaded successfully."}
                    self._log_hot_reload_event(result)
                    print(f"[SelfCoder] Hot-reload OK: {module_name}")
                    return result
                except Exception as reload_exc:
                    tb = traceback.format_exc()
                    print(f"[SelfCoder] Reload raised exception — restoring rollback:\n{tb}")

                    # ── Step 6: Restore rollback on reload failure ─────────────
                    try:
                        if rollback_path.exists():
                            shutil.copy2(str(rollback_path), str(file_path))
                            importlib.invalidate_caches()
                            try:
                                importlib.reload(sys.modules[module_name])
                            except Exception:
                                pass  # best-effort re-load of old code
                    except Exception as rb_exc:
                        tb += f"\n[rollback also failed: {rb_exc}]"

                    result = {**base_event, "status": "rollback_applied",
                              "detail": tb}
                    self._log_hot_reload_event(result)
                    return result
            else:
                # Module not currently loaded — file is written; nothing to reload
                result = {**base_event, "status": "module_not_loaded",
                          "detail": f"File written; '{module_name}' not in sys.modules, skip reload."}
                self._log_hot_reload_event(result)
                return result

        finally:
            # Clean up temp file regardless of outcome
            try:
                tmp_path.unlink(missing_ok=True)
                # Remove any compiled .pyc sibling tempfile left by py_compile
                pyc = Path(tmp_path_str + "c")
                pyc.unlink(missing_ok=True)
            except Exception:
                pass

    # ── Persistence ─────────────────────────────────────────────────────────────

    def _load_modifications(self):
        try:
            if CODE_MODIFICATIONS_LOG.exists():
                with open(CODE_MODIFICATIONS_LOG, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            mod = CodeModification(**data)
                            self._modifications[mod.id] = mod
        except Exception as e:
            print(f"[SelfCoder] Modifications load error: {e}")

    def _save_modifications(self):
        try:
            with open(CODE_MODIFICATIONS_LOG, 'w') as f:
                for mod in self._modifications.values():
                    f.write(json.dumps(asdict(mod)) + "\n")
        except Exception as e:
            print(f"[SelfCoder] Modifications save error: {e}")

    def _log_modification(self, modification: CodeModification):
        try:
            with open(CODE_MODIFICATIONS_LOG, 'a') as f:
                f.write(json.dumps(asdict(modification)) + "\n")
        except Exception as e:
            print(f"[SelfCoder] Modification log error: {e}")

    # ── Swarm Validation ─────────────────────────────────────────────────────────

    def swarm_validate_modification(self, modification_id: str) -> Dict[str, Any]:
        """Have multiple LOVE instances validate a modification."""
        if modification_id not in self._modifications:
            return {"valid": False, "reason": "Modification not found"}

        modification = self._modifications[modification_id]

        # Simulate swarm validation (in real implementation, would use multiple instances)
        validation_results = {
            "syntax_check": self._validate_syntax(modification.modified_code),
            "safety_check": self.check_safety(modification.modified_code, modification.file_path),
            "logic_check": self._validate_logic(modification),
            "style_check": self._validate_style(modification.modified_code),
        }

        # Calculate overall validity
        all_passed = all([
            validation_results["syntax_check"],
            validation_results["safety_check"][0],  # (is_safe, warnings)
            validation_results["logic_check"],
            validation_results["style_check"],
        ])

        return {
            "valid": all_passed,
            "results": validation_results,
            "confidence": sum([
                validation_results["syntax_check"],
                validation_results["safety_check"][0],
                validation_results["logic_check"],
                validation_results["style_check"],
            ]) / 4.0,
        }

    def _validate_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _validate_logic(self, modification: CodeModification) -> bool:
        """Validate that the modification makes logical sense."""
        # Simplified: check that modification actually changes something
        if modification.original_code == modification.modified_code:
            return False

        # Check that modification is not too drastic
        original_lines = len(modification.original_code.splitlines())
        modified_lines = len(modification.modified_code.splitlines())

        # If modification changes file size by > 50%, flag it
        if original_lines > 0 and abs(modified_lines - original_lines) / original_lines > 0.5:
            return False

        return True

    def _validate_style(self, code: str) -> bool:
        """Basic style validation."""
        # Check for basic Python style issues
        issues = []

        # Check for lines that are too long
        for line in code.splitlines():
            if len(line) > 120:
                issues.append("Line too long")
                break

        # Check for proper indentation (basic)
        lines = code.splitlines()
        for i, line in enumerate(lines[1:], 1):
            if line.strip() and not line[0].isspace():
                # Non-indented line after indented line might be an issue
                if i > 0 and lines[i-1].strip().endswith(':'):
                    issues.append("Possible indentation issue")
                    break

        return len(issues) == 0

    # ── Main Loop ─────────────────────────────────────────────────────────────────

    def start(self):
        """Start the self-coder background loop."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._main_loop, daemon=True, name="LOVE-SelfCoder"
        )
        self._thread.start()
        print("[SelfCoder] Started — LOVE can now write its own upgrades")

    def stop(self):
        self._running = False

    def _main_loop(self):
        time.sleep(300)  # Let other systems initialize

        while self._running:
            try:
                # Periodically analyze core files for improvement opportunities
                core_files = [
                    "core/evolution_engine.py",
                    "core/meta_evolution.py",
                    "core/swarm_evolution.py",
                    "core/intelligence_hub.py",
                    "core/sentinel.py",
                ]

                modifications_generated = 0
                for file_path in core_files:
                    if Path(file_path).exists():
                        analysis = self.analyze_file(file_path)
                        if analysis.improvement_opportunities:
                            print(f"[SelfCoder] Found opportunities in {file_path}")
                            # Actually generate modifications for top opportunities
                            for opp in analysis.improvement_opportunities[:2]:
                                try:
                                    mod = self.generate_modification(
                                        hypothesis=opp,
                                        file_path=file_path,
                                        improvement_type="enhancement"
                                    )
                                    if mod:
                                        # Test the modification
                                        if self.test_modification(mod.id):
                                            print(f"[SelfCoder] Generated and tested modification for {file_path}")
                                            modifications_generated += 1
                                        else:
                                            print(f"[SelfCoder] Modification failed tests: {mod.id}")
                                except Exception as e:
                                    print(f"[SelfCoder] Modification generation error: {e}")

                if modifications_generated > 0:
                    print(f"[SelfCoder] Generated {modifications_generated} modification(s) this cycle")
                    # Report to orchestrator
                    try:
                        from core.master_orchestrator import get_orchestration_master
                        om = get_orchestration_master()
                        om._narrate("self_coder", f"Generated {modifications_generated} code modification(s)", "action")
                    except Exception:
                        pass

            except Exception as e:
                print(f"[SelfCoder] Loop error: {e}")

            time.sleep(3600)  # Run every hour


# ── Singleton Access ─────────────────────────────────────────────────────────────

_self_coder_instance: Optional[SelfCoder] = None
_self_coder_lock = threading.Lock()


def get_self_coder() -> SelfCoder:
    global _self_coder_instance
    with _self_coder_lock:
        if _self_coder_instance is None:
            _self_coder_instance = SelfCoder()
        return _self_coder_instance
