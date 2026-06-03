"""
LOVE Document Analyst
Watches your dev folders and documents, reads them, extracts insights.
Gives LOVE knowledge of:
  - What you're building (code structure, recent changes)
  - What's in your docs (README, specs, notes)
  - What problems exist (TODOs, FIXMEs, open issues)
  - What the active project is

Supports: .py .cs .dart .js .ts .jsx .tsx .md .txt .pdf .json .yaml
"""

import os
import re
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock, Thread
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
INSIGHTS_FILE = DATA_DIR / "doc_insights.json"

MAX_FILE_SIZE_KB = 200
WATCH_EXTENSIONS = {".py", ".cs", ".dart", ".js", ".ts", ".jsx", ".tsx",
                    ".md", ".txt", ".json", ".yaml", ".toml", ".sql", ".html"}


class DocAnalyst:
    """
    Watches dev folders and extracts actionable insights:
    - TODOs, FIXMEs, HACKs in code
    - README summaries
    - Recent changes
    - Project structure
    """

    def __init__(self):
        self._lock = Lock()
        self._insights: List[str] = []
        self._active_project: Optional[str] = None
        self._project_summary: Dict[str, Any] = {}
        self._watch_paths = []
        self._running = False
        self._thread: Optional[Thread] = None
        self._last_scan: Optional[datetime] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._load_persisted()

    def add_watch_path(self, path: str):
        from pathlib import Path
        p = Path(path)
        if p.exists() and p not in self._watch_paths:
            self._watch_paths.append(p)
            print(f"[DocAnalyst] Watching: {p}")

    def start(self, interval_seconds: int = 120):
        if self._running:
            return
        self._running = True
        self._thread = Thread(target=self._loop, args=(interval_seconds,), daemon=True)
        self._thread.start()
        print(f"[DocAnalyst] Document intelligence started ({interval_seconds}s interval)")

    def stop(self):
        self._running = False

    def get_recent_insights(self) -> List[str]:
        with self._lock:
            return list(self._insights[:10])

    def get_active_project(self) -> Optional[str]:
        with self._lock:
            return self._active_project

    def get_project_summary(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._project_summary)

    def scan_now(self) -> Dict[str, Any]:
        """Force immediate scan and return results."""
        return self._scan()

    # ──────────────────────────────────────────────
    # SCAN LOOP
    # ──────────────────────────────────────────────

    def _loop(self, interval: int):
        import traceback
        while self._running:
            try:
                self._scan()
            except Exception as e:
                print(f"[DocAnalyst] Scan error: {e}")
                print(f"[DocAnalyst] Traceback: {traceback.format_exc()}")
            time.sleep(interval)

    def _scan(self) -> Dict[str, Any]:
        insights = []
        todos = []
        readmes = []
        recent_changes = []
        file_counts: Dict[str, int] = {}
        project_names = []

        cutoff = datetime.now() - timedelta(hours=4)

        for watch_path in self._watch_paths:
            if not watch_path.exists():
                continue

            # Detect project name from folder
            project_names.append(watch_path.name)

            for item in watch_path.rglob("*"):
                # Skip common noise directories
                skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv",
                             "bin", "obj", "dist", "build", ".next", "coverage"}
                if any(part in skip_dirs for part in item.parts):
                    continue

                if not item.is_file():
                    continue
                if item.suffix.lower() not in WATCH_EXTENSIONS:
                    continue
                if item.stat().st_size > MAX_FILE_SIZE_KB * 1024:
                    continue

                ext = item.suffix.lower()
                file_counts[ext] = file_counts.get(ext, 0) + 1

                mtime = datetime.fromtimestamp(item.stat().st_mtime)

                # Recently modified
                if mtime > cutoff:
                    recent_changes.append({
                        "name": item.name,
                        "path": str(item),
                        "modified": mtime.isoformat(),
                        "ext": ext
                    })

                # Read file for analysis
                try:
                    content = item.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                # Extract TODOs / FIXMEs / HACKs
                for line_num, line in enumerate(content.splitlines(), 1):
                    line_stripped = line.strip()
                    if any(marker in line_stripped.upper() for marker in ["TODO", "FIXME", "HACK", "XXX", "BUG"]):
                        snippet = line_stripped[:100]
                        todos.append({
                            "file": item.name,
                            "line": line_num,
                            "text": snippet
                        })

                # Code pattern detection
                patterns = self._detect_code_patterns(content, ext)
                if patterns:
                    for pattern in patterns:
                        insights.append(f"[{item.name}] {pattern}")

                # README analysis
                if item.name.lower() in ["readme.md", "readme.txt"]:
                    summary = self._summarize_readme(content)
                    if summary:
                        readmes.append({"file": str(item), "summary": summary})

        # Build insights list
        recent_changes.sort(key=lambda x: x.get("modified", ""), reverse=True)

        if recent_changes:
            names = [f.get("name", "") for f in recent_changes[:3]]
            insights.append(f"Recently modified: {', '.join(names)}")

        if todos:
            high_priority = [t for t in todos if "FIXME" in t["text"].upper() or "BUG" in t["text"].upper()]
            if high_priority:
                insights.append(f"{len(high_priority)} FIXME/BUG in code — {high_priority[0]['file']}:{high_priority[0]['line']}")
            elif todos:
                insights.append(f"{len(todos)} TODO(s) across codebase")

        for readme in readmes[:1]:
            insights.append(f"Project: {readme['summary']}")

        # Infer active project
        active = None
        if project_names:
            active = project_names[0] if len(project_names) == 1 else self._infer_active_project(recent_changes, project_names)

        result = {
            "insights": insights,
            "todos": todos[:20],
            "recent_changes": recent_changes[:20],
            "readmes": readmes,
            "file_counts": file_counts,
            "active_project": active,
            "scanned_at": datetime.now().isoformat()
        }

        with self._lock:
            self._insights = insights
            self._active_project = active
            self._project_summary = result
            self._last_scan = datetime.now()

        self._persist(result)
        return result

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def _summarize_readme(self, content: str) -> str:
        """Extract first meaningful line from README."""
        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            # Skip headers, badges, empty lines
            if not line or line.startswith("!") or line.startswith("<") or line.startswith("["):
                continue
            line = re.sub(r"^#+\s*", "", line)  # Remove markdown heading markers
            if len(line) > 20:
                return line[:120]
        return ""

    def _infer_active_project(self, recent_changes: List[Dict], project_names: List[str]) -> Optional[str]:
        """Infer which project is currently being worked on from recent file changes."""
        if not recent_changes:
            return project_names[0] if project_names else None
        # Count recent changes per project
        counts: Dict[str, int] = {p: 0 for p in project_names}
        for change in recent_changes:
            path = change.get("path", "")
            for proj in project_names:
                if proj in path:
                    counts[proj] = counts.get(proj, 0) + 1
        return max(counts, key=counts.get) if counts else None

    def _detect_code_patterns(self, content: str, ext: str) -> List[str]:
        """Detect code patterns, anti-patterns, and insights."""
        patterns = []
        lines = content.splitlines()
        
        # Common anti-patterns across languages
        anti_patterns = {
            "console.log": lambda line: "console.log" in line and "console.log(" in line,
            "print_debug": lambda line: "print(" in line and "debug" in line.lower(),
            "hardcoded_url": lambda line: re.search(r'http[s]?://["\']', line),
            "magic_number": lambda line: re.search(r'\b\d{3,}\b', line) and not line.strip().startswith("#") and not line.strip().startswith("//"),
            "long_line": lambda line: len(line) > 120,
            "empty_catch": lambda line: "except" in line and ("pass" in line or "{}" in line or ";" in line.replace(";", "").strip()),
            "nested_if": lambda line: line.count("if") > 1 or (line.count("if") == 1 and line.count("else") > 0),
        }
        
        # Language-specific patterns
        if ext in {".py", ".pyx"}:
            patterns.extend(self._detect_python_patterns(content, lines))
        elif ext in {".js", ".ts", ".jsx", ".tsx"}:
            patterns.extend(self._detect_javascript_patterns(content, lines))
        elif ext in {".cs"}:
            patterns.extend(self._detect_csharp_patterns(content, lines))
        
        # Check for anti-patterns
        for pattern_name, check in anti_patterns.items():
            matches = sum(1 for line in lines if check(line))
            if matches > 0:
                if pattern_name == "long_line":
                    patterns.append(f"{matches} lines exceed 120 chars")
                elif pattern_name == "magic_number":
                    patterns.append("Potential magic numbers detected")
                elif pattern_name == "console.log":
                    patterns.append(f"{matches} console.log statements (remove for production)")
                elif pattern_name == "print_debug":
                    patterns.append(f"{matches} debug print statements")
                elif pattern_name == "empty_catch":
                    patterns.append(f"{matches} empty catch blocks")
                elif pattern_name == "nested_if":
                    patterns.append("Nested if statements detected (consider refactoring)")
                elif pattern_name == "hardcoded_url":
                    patterns.append("Hardcoded URLs detected (use config)")
        
        return patterns[:5]  # Limit to top 5 patterns per file
    
    def _detect_python_patterns(self, content: str, lines: List[str]) -> List[str]:
        """Detect Python-specific patterns."""
        patterns = []
        
        # Check for common Python patterns
        has_main = any("__main__" in line for line in lines)
        has_docstring = any('"""' in line or "'''" in line for line in lines[:10])
        has_type_hints = sum(1 for line in lines if ":" in line and not line.strip().startswith("#"))
        
        # Check for imports
        imports = [line for line in lines if line.strip().startswith("import") or line.strip().startswith("from")]
        if len(imports) > 10:
            patterns.append(f"Many imports ({len(imports)}) - consider refactoring")
        
        # Check for class complexity
        class_count = sum(1 for line in lines if line.strip().startswith("class "))
        if class_count > 5:
            patterns.append(f"Multiple classes in one file ({class_count})")
        
        # Check for function length
        in_function = False
        function_lines = 0
        long_functions = 0
        for line in lines:
            if line.strip().startswith("def "):
                in_function = True
                function_lines = 0
            elif in_function:
                function_lines += 1
                if line.strip() and not line.strip().startswith(" ") and not line.strip().startswith("def "):
                    if function_lines > 30:
                        long_functions += 1
                    in_function = False
        
        if long_functions > 0:
            patterns.append(f"{long_functions} functions exceed 30 lines")
        
        return patterns
    
    def _detect_javascript_patterns(self, content: str, lines: List[str]) -> List[str]:
        """Detect JavaScript/TypeScript patterns."""
        patterns = []
        
        # Check for var usage
        var_count = sum(1 for line in lines if re.search(r'\bvar\s+', line))
        if var_count > 0:
            patterns.append(f"Using 'var' ({var_count} times) - prefer const/let")
        
        # Check for any types
        if any("any" in line for line in lines if ":" in line):
            patterns.append("Using 'any' type - consider specific types")
        
        # Check for async/await usage
        has_async = any("async" in line for line in lines)
        has_await = any("await" in line for line in lines)
        if has_async and not has_await:
            patterns.append("Async function without await")
        
        # Check for arrow functions vs function declarations
        arrow_count = sum(1 for line in lines if "=>" in line)
        function_count = sum(1 for line in lines if line.strip().startswith("function "))
        if arrow_count > function_count * 2:
            patterns.append("Prefer function declarations for hoisting")
        
        return patterns
    
    def _detect_csharp_patterns(self, content: str, lines: List[str]) -> List[str]:
        """Detect C# patterns."""
        patterns = []
        
        # Check for public fields (should use properties)
        public_fields = sum(1 for line in lines if re.search(r'public\s+\w+\s+\w+\s*;', line))
        if public_fields > 0:
            patterns.append(f"{public_fields} public fields - consider using properties")
        
        # Check for async without await
        async_count = sum(1 for line in lines if "async" in line)
        await_count = sum(1 for line in lines if "await" in line)
        if async_count > await_count:
            patterns.append("Async methods without await")
        
        return patterns

    def analyze_file_with_llm(self, file_path: str) -> str:
        """Use LOVE's LLM to analyze a specific file and return insights."""
        from pathlib import Path
        try:
            p = Path(file_path)
            if not p.exists():
                return f"File not found: {file_path}"
            if p.stat().st_size > MAX_FILE_SIZE_KB * 1024:
                return f"File too large to analyze: {file_path}"

            content = p.read_text(encoding="utf-8", errors="ignore")
            from core.llm import route_llm
            llm = route_llm("analyze code")
            prompt = f"""Analyze this {p.suffix} file and provide:
1. What it does (1-2 sentences)
2. Any issues or improvements needed (be specific)
3. Key functions/classes

File: {p.name}
---
{content[:3000]}
---
Be concise. Max 150 words."""
            return llm.invoke(prompt)
        except Exception as e:
            return f"Analysis failed: {e}"

    # ──────────────────────────────────────────────
    # PERSISTENCE
    # ──────────────────────────────────────────────

    def _persist(self, data: Dict):
        try:
            with open(INSIGHTS_FILE, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.doc_analyst")

    def _load_persisted(self):
        if INSIGHTS_FILE.exists():
            try:
                with open(INSIGHTS_FILE) as f:
                    data = json.load(f)
                self._insights = data.get("insights", [])
                self._active_project = data.get("active_project")
                self._project_summary = data
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.doc_analyst")


# ──────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────

_analyst: Optional[DocAnalyst] = None


def get_analyst() -> DocAnalyst:
    global _analyst
    if _analyst is None:
        _analyst = DocAnalyst()
    return _analyst


def start_doc_analyst(watch_paths: List[str] = None, interval_seconds: int = 120):
    analyst = get_analyst()
    if watch_paths:
        for p in watch_paths:
            analyst.add_watch_path(p)
    analyst.start(interval_seconds)
    return analyst
