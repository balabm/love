"""
LOVE Ghost Developer Engine (Wave 5)
A fully autonomous background coder.

Ghost Dev can be assigned a coding task. It will:
1. Read the relevant files.
2. Formulate an implementation plan.
3. Use the LLM to generate code modifications.
4. Apply those modifications directly to the file system.
5. Notify the user when the feature is done.

It acts exactly like a junior developer you can delegate work to.
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.llm import get_coding_llm, get_reasoning_llm
from core.consciousness import get_consciousness

DATA_DIR = Path(__file__).parent.parent / "data"
GHOST_DEV_TASKS = DATA_DIR / "ghost_dev_tasks.json"

class GhostDevTask:
    def __init__(self, task_id: str, description: str, target_files: List[str]):
        self.task_id = task_id
        self.description = description
        self.target_files = target_files
        self.status = "pending"  # pending, working, review, completed, failed
        self.logs = []
        self.created_at = time.time()
        self.completed_at = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "description": self.description,
            "target_files": self.target_files,
            "status": self.status,
            "logs": self.logs,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data):
        t = cls(data["task_id"], data["description"], data["target_files"])
        t.status = data.get("status", "pending")
        t.logs = data.get("logs", [])
        t.created_at = data.get("created_at", time.time())
        t.completed_at = data.get("completed_at")
        return t

class GhostDeveloper:
    def __init__(self):
        self.tasks: Dict[str, GhostDevTask] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._load_tasks()

    def _load_tasks(self):
        if GHOST_DEV_TASKS.exists():
            try:
                data = json.loads(GHOST_DEV_TASKS.read_text())
                for k, v in data.items():
                    self.tasks[k] = GhostDevTask.from_dict(v)
            except Exception:
                pass

    def _save_tasks(self):
        with self._lock:
            try:
                data = {k: v.to_dict() for k, v in self.tasks.items()}
                GHOST_DEV_TASKS.write_text(json.dumps(data, indent=2))
            except Exception:
                pass

    def assign_task(self, description: str, target_files: List[str]) -> str:
        task_id = f"task_{int(time.time())}"
        task = GhostDevTask(task_id, description, target_files)
        self.tasks[task_id] = task
        self._save_tasks()
        
        try:
            get_consciousness().think(f"Received new Ghost Dev task: {description}")
        except Exception:
            pass

        return task_id

    def _read_file(self, path: str) -> str:
        try:
            return Path(path).read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading {path}: {e}"

    def _write_file(self, path: str, content: str) -> bool:
        try:
            Path(path).write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def _execute_task(self, task: GhostDevTask):
        task.status = "working"
        task.logs.append(f"[{time.time()}] Started working on task.")
        self._save_tasks()

        llm = get_coding_llm()
        reasoning = get_reasoning_llm()

        try:
            # 1. Read files
            file_contents = {}
            for fpath in task.target_files:
                task.logs.append(f"[{time.time()}] Reading {fpath}...")
                file_contents[fpath] = self._read_file(fpath)
            
            # 2. Plan
            plan_prompt = f"""You are LOVE Ghost Developer.
Task: {task.description}
Files provided:
{chr(10).join(f'- {k}' for k in file_contents.keys())}

File Contents:
"""
            for k, v in file_contents.items():
                plan_prompt += f"\n--- {k} ---\n{v}\n"
                
            plan_prompt += "\nCreate a step-by-step implementation plan to achieve this task."
            task.logs.append(f"[{time.time()}] Generating implementation plan...")
            plan = str(reasoning.invoke(plan_prompt))
            task.logs.append(f"[{time.time()}] Plan: {plan[:200]}...")

            # 3. Code Generation & Application
            for fpath, content in file_contents.items():
                if "Error reading" in content:
                    continue
                    
                code_prompt = f"""You are LOVE Ghost Developer. You write pristine code.
Task: {task.description}
File: {fpath}

Current Content:
```
{content}
```

Plan:
{plan}

Provide the FULL updated content for {fpath}. Output ONLY the code, nothing else. No markdown blocks, just the raw code.
"""
                task.logs.append(f"[{time.time()}] Generating code for {fpath}...")
                new_code = str(llm.invoke(code_prompt))
                
                # Clean up markdown if present
                if new_code.startswith("```"):
                    lines = new_code.split(chr(10))
                    if len(lines) > 2:
                        new_code = chr(10).join(lines[1:-1])

                success = self._write_file(fpath, new_code)
                if success:
                    task.logs.append(f"[{time.time()}] Successfully wrote to {fpath}.")
                else:
                    task.logs.append(f"[{time.time()}] Failed to write to {fpath}.")

            task.status = "review"
            task.completed_at = time.time()
            task.logs.append(f"[{time.time()}] Task moved to review phase.")
            
            try:
                get_consciousness().think(f"Ghost Dev finished task: {task.description}. Waiting for user review.")
            except Exception:
                pass

        except Exception as e:
            task.status = "failed"
            task.logs.append(f"[{time.time()}] Error: {str(e)}")
            
        self._save_tasks()

    def _daemon_loop(self):
        while self._running:
            try:
                pending_tasks = [t for t in self.tasks.values() if t.status == "pending"]
                if pending_tasks:
                    # Execute the first pending task
                    self._execute_task(pending_tasks[0])
            except Exception as e:
                print(f"[GhostDev] Loop error: {e}")
            
            time.sleep(10)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._daemon_loop, daemon=True, name="LOVE-GhostDev")
        self._thread.start()
        print("[AGI] * Ghost Developer engine started.")

    def stop(self):
        self._running = False

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        return None

# Singleton
_ghost_dev = None

def get_ghost_dev() -> GhostDeveloper:
    global _ghost_dev
    if _ghost_dev is None:
        _ghost_dev = GhostDeveloper()
    return _ghost_dev
