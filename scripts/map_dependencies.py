import ast
import os
from pathlib import Path


def trace_imports_from_file(file_path: Path) -> set:
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def recursive_trace(entry_file: Path, project_root: Path, depth: int = 0) -> set:
    if depth > 5:
        return set()
    imported = trace_imports_from_file(entry_file)
    all_imports = set(imported)
    for module in imported:
        module_path = project_root / f"{module.replace('.', '/')}.py"
        if module_path.exists():
            all_imports.update(recursive_trace(module_path, project_root, depth + 1))
    return all_imports


def find_all_py_files(project_root: Path) -> set:
    dirs = ['core', 'agents', 'integrations', 'tools']
    modules = set()
    for d in dirs:
        dir_path = project_root / d
        if dir_path.exists():
            for py_file in dir_path.rglob('*.py'):
                rel_path = py_file.relative_to(project_root)
                modules.add(str(rel_path.with_suffix('')).replace('\\', '.'))
    return modules


def map_dependencies():
    project_root = Path(__file__).parent.parent
    entry_file = project_root / 'api' / 'main.py'
    imported_modules = recursive_trace(entry_file, project_root)
    all_modules = find_all_py_files(project_root)
    orphaned = all_modules - imported_modules
    print(f"Active Modules: {len(imported_modules)}")
    print(f"Orphaned Modules: {len(orphaned)}")
    for module in sorted(orphaned):
        print(f"  - {module}")
    return {"active": sorted(imported_modules), "orphaned": sorted(orphaned)}


if __name__ == "__main__":
    map_dependencies()
