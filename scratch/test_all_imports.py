import os
import sys
import subprocess
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

core_dir = project_root / "core"
py_files = sorted([f.stem for f in core_dir.glob("*.py") if f.name != "__init__.py"])

print("--- Testing Core Imports with Subprocesses ---")
failures = []
successes = []

for mod in py_files:
    mod_name = f"core.{mod}"
    # Run a python command to import this module
    cmd = [sys.executable, "-c", f"import sys; sys.path.insert(0, r'{project_root}'); import {mod_name}"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            successes.append(mod_name)
            print(f"[ OK ] {mod_name}")
        else:
            err = res.stderr.strip() or res.stdout.strip()
            failures.append((mod_name, f"Exit code {res.returncode}: {err}"))
            print(f"[FAIL] {mod_name}: {err.splitlines()[-1] if err.splitlines() else 'Unknown error'}")
    except subprocess.TimeoutExpired:
        failures.append((mod_name, "Import timed out (5s)"))
        print(f"[TIME] {mod_name}: Import timed out (5s)")
    except Exception as e:
        failures.append((mod_name, str(e)))
        print(f"[ERR ] {mod_name}: {e}")

print("\n--- Summary ---")
print(f"Total: {len(py_files)}")
print(f"Success: {len(successes)}")
print(f"Failed: {len(failures)}")

if failures:
    print("\nDetailed Failures:")
    for mod, err in failures:
         print(f"- {mod}: {err}")
