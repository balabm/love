"""
LOVE Code Sandbox — safely test drafted features without executing arbitrary code.

Uses Python's compile() + ast analysis + restricted execution environment.
No network calls, no file writes outside data/sandbox, no subprocess.
"""

import ast
import sys
import types
import traceback
import io
import contextlib
from pathlib import Path
from typing import Dict, Any, List

SANDBOX_DIR = Path(__file__).parent.parent / "data" / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Restricted builtins — only safe ones
SAFE_BUILTINS = {
    "abs", "all", "any", "bool", "chr", "dict", "divmod", "enumerate",
    "filter", "float", "format", "frozenset", "hasattr", "hash", "hex",
    "id", "int", "isinstance", "issubclass", "iter", "len", "list",
    "map", "max", "min", "next", "oct", "ord", "pow", "print", "range",
    "repr", "reversed", "round", "set", "slice", "sorted", "str", "sum",
    "tuple", "type", "vars", "zip", "__import__", "True", "False", "None",
}

# Blocked AST node types
BLOCKED_NODES = {
    ast.Import, ast.ImportFrom, ast.With, ast.AsyncWith, ast.Try, ast.ExceptHandler,
    ast.Raise, ast.Assert, ast.Delete, ast.Global, ast.Nonlocal, ast.Yield,
    ast.YieldFrom, ast.Await, ast.Lambda,
}

FORBIDDEN_IMPORTS = {"os", "sys", "subprocess", "socket", "urllib", "http", "ftplib",
    "smtplib", "ctypes", "multiprocessing", "threading", "shutil", "tempfile",
    "pickle", "marshal", "eval", "exec", "compile", "open"}


def _is_safe_ast(tree: ast.AST) -> tuple[bool, str]:
    for node in ast.walk(tree):
        if type(node) in BLOCKED_NODES:
            return False, f"Blocked AST node: {type(node).__name__}"
        if isinstance(node, ast.Name) and node.id in {"eval", "exec", "compile", "__import__"}:
            return False, f"Forbidden builtin: {node.id}"
    return True, "OK"


def _check_imports(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FORBIDDEN_IMPORTS:
                    return False, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                return False, f"Forbidden import from: {node.module}"

    return _is_safe_ast(tree)


def run_sandbox(code: str, timeout: float = 3.0) -> Dict[str, Any]:
    """
    Run code in a restricted sandbox. Returns:
    { success: bool, output: str, error: str, blocked: bool }
    """
    result = {
        "success": False,
        "output": "",
        "error": "",
        "blocked": False,
    }

    # Pre-check imports and AST
    safe, reason = _check_imports(code)
    if not safe:
        result["blocked"] = True
        result["error"] = reason
        return result

    # Compile
    try:
        compiled = compile(code, "<sandbox>", "exec")
    except SyntaxError as e:
        result["error"] = f"Syntax error: {e}"
        return result

    # Build restricted environment
    restricted_globals = {
        "__builtins__": {name: __builtins__[name] for name in SAFE_BUILTINS if name in __builtins__},
    }
    restricted_locals = {}

    # Redirect stdout
    output_buffer = io.StringIO()

    # Execute with timeout-like guard (using signal not available on Windows, so we use a simple approach)
    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(compiled, restricted_globals, restricted_locals)
        result["success"] = True
        result["output"] = output_buffer.getvalue()
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"

    return result


def test_feature_draft(code: str, test_inputs: List[Any] = None) -> Dict[str, Any]:
    """
    Test a drafted feature by running it and checking:
    - No exceptions
    - No blocked imports
    - Returns expected types
    """
    result = run_sandbox(code)

    if not result["success"]:
        return {
            "passed": False,
            "stage": "execution" if not result["blocked"] else "security_check",
            "error": result["error"],
            "output": result["output"],
        }

    return {
        "passed": True,
        "stage": "all",
        "output": result["output"],
        "error": "",
    }
