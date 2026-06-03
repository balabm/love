"""
Bulk audit script: replaces all `except: pass` and `except Exception: pass`
patterns across core/, cognition/, api/, kernel/ with proper error logging.

Deterministic. Atomic. No silent failures.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TARGET_DIRS = [PROJECT_ROOT / d for d in ("core", "cognition", "api", "kernel", "integrations", "agents", "tools", "voice", "service", "evolution", "scratch")]
# Also audit root-level .py files
ROOT_PY_FILES = list(PROJECT_ROOT.glob("*.py"))
IMPORT_LINE = "from core.execution_guard import log_error\n"


def module_name_from_path(path: Path) -> str:
    rel = path.relative_to(PROJECT_ROOT)
    return str(rel.with_suffix("")).replace("\\", ".").replace("/", ".")


def fix_file(path: Path) -> int:
    code = path.read_text(encoding="utf-8")
    original = code
    changes = 0

    # Skip files that are part of the guard itself or bootstrap
    if path.name in ("execution_guard.py", "safe_print.py"):
        return 0

    lines = code.splitlines(keepends=True)
    new_lines = []
    i = 0
    added_import = False
    has_import = IMPORT_LINE.strip() in code

    while i < len(lines):
        line = lines[i]

        # Detect:  except Exception:\n    pass
        # Detect:  except:\n    pass
        # Detect:  except ValueError:\n    pass
        # Detect:  except (A, B):\n    pass
        # Detect:  except json.JSONDecodeError:\n    pass  # comment
        m = re.match(r"^(\s*)except\s*(?:[A-Za-z_][A-Za-z0-9_\.\(\),\s]*)?\s*:\s*(?:\r?\n)", line)
        if m and i + 1 < len(lines):
            indent = m.group(1)
            next_line = lines[i + 1]
            if next_line.strip().startswith("pass"):
                # Replace with proper logging
                mod = module_name_from_path(path)
                new_lines.append(f"{indent}except Exception as e:\n")
                new_lines.append(f"{indent}    from core.execution_guard import log_error\n")
                new_lines.append(f"{indent}    log_error(e, module=\"{mod}\")\n")
                i += 2
                changes += 1
                continue

        new_lines.append(line)
        i += 1

    if changes == 0:
        return 0

    # Add import at top if not present
    final_code = "".join(new_lines)
    if not has_import and "log_error" in final_code:
        # Insert after any __future__ imports or after first docstring
        lines_for_import = final_code.splitlines(keepends=True)
        insert_idx = 0
        for idx, l in enumerate(lines_for_import):
            if l.startswith("from __future__") or l.startswith("import ") or l.startswith("from "):
                insert_idx = idx + 1
        lines_for_import.insert(insert_idx, IMPORT_LINE)
        final_code = "".join(lines_for_import)

    if final_code != original:
        path.write_text(final_code, encoding="utf-8")

    return changes


def main():
    total_files = 0
    total_changes = 0
    all_files = list(ROOT_PY_FILES)
    for target_dir in TARGET_DIRS:
        if target_dir.exists():
            all_files.extend(target_dir.rglob("*.py"))

    for py_file in all_files:
        changes = fix_file(py_file)
        if changes:
            total_files += 1
            total_changes += changes
            print(f"  [FIXED] {py_file.relative_to(PROJECT_ROOT)} ({changes} replacements)")

    print(f"\nAudit complete: {total_changes} `except: pass` patterns fixed across {total_files} files.")
    if total_changes == 0:
        print("All clear — no silent failures remaining in target directories.")


if __name__ == "__main__":
    main()
