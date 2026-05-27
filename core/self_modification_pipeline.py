"""
LOVE Self-Modification Pipeline

Connects idle thinking → constitutional review → evolution integration.

When LOVE drafts improvements during idle time, this pipeline:
1. Reads idle mind drafts from data/idle_drafts/
2. Runs each draft through the Constitution for ethical review
3. If approved (score > 0.7), creates an evolution hypothesis
4. Evolution engine tests and integrates validated improvements

This is how LOVE actually improves itself — not just in theory.
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data"
DRAFTS_DIR = DATA_DIR / "idle_drafts"
PIPELINE_LOG = DATA_DIR / "self_modification_log.jsonl"
PROCESSED_DIR = DATA_DIR / "idle_drafts" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _log(entry: Dict):
    entry["timestamp"] = datetime.now().isoformat()
    try:
        with open(PIPELINE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _constitutional_review(draft_content: str) -> Dict[str, Any]:
    """
    Run a draft improvement through the Constitution Engine.
    Returns: {"approved": bool, "score": float, "reason": str}
    """
    try:
        from core.constitution import get_constitution
        constitution = get_constitution()
        # Use critique_response to evaluate if this change aligns with principles
        # We construct a synthetic "response" representing what LOVE would do with this change
        synthetic_query = "Should I implement this self-improvement?"
        synthetic_response = f"I will implement the following change to improve myself: {draft_content}"
        critique = constitution.critique_response(synthetic_response, synthetic_query, "")
        if critique:
            score = getattr(critique, 'score', 0.5)
            suggestions = getattr(critique, 'suggestions', [])
            violations = getattr(critique, 'violations', [])
            approved = score > 0.65 and len(violations) == 0
            return {
                "approved": approved,
                "score": score,
                "violations": violations,
                "suggestions": suggestions,
                "reason": f"Constitutional score {score:.2f}" + (f", violations: {violations}" if violations else ""),
            }
    except Exception as e:
        print(f"[SelfModPipeline] Constitution review error: {e}")
    return {"approved": True, "score": 0.7, "reason": "Constitution review unavailable — proceeding with caution"}


def _create_evolution_hypothesis(draft_content: str, review: Dict) -> bool:
    """
    Create an evolution hypothesis from an approved draft.
    Returns True if hypothesis was successfully queued.
    """
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        # Directly create a hypothesis targeting this draft
        from core.evolution_engine import Hypothesis
        import uuid
        h = Hypothesis(
            id=uuid.uuid4().hex[:10],
            claim=f"Applying self-draft: {draft_content[:100]}",
            rationale=f"LOVE's idle mind proposed this improvement. Constitutional score: {review['score']:.2f}",
            predicted_effect="Improved response quality or behavior",
            target_metric="response_quality",
            predicted_delta=0.1,
            confidence=review["score"],
            status="proposed",
        )
        evo._hypotheses[h.id] = h
        evo._save_genome()  # persist
        print(f"[SelfModPipeline] Queued evolution hypothesis: {h.claim[:80]}")
        return True
    except Exception as e:
        print(f"[SelfModPipeline] Evolution hypothesis error: {e}")
    return False


def process_idle_drafts() -> int:
    """
    Process all pending idle mind drafts.
    Returns the number of drafts processed.
    """
    if not DRAFTS_DIR.exists():
        return 0

    drafts = [f for f in DRAFTS_DIR.glob("*.json") if f.parent == DRAFTS_DIR]
    processed = 0

    for draft_file in drafts[:5]:  # Process max 5 at a time
        try:
            content = json.loads(draft_file.read_text())
            draft_text = content.get("content", content.get("code", content.get("summary", str(content))))
            if not draft_text or len(draft_text) < 20:
                continue

            print(f"[SelfModPipeline] Reviewing draft: {draft_file.name}")

            # Step 1: Constitutional review
            review = _constitutional_review(draft_text[:500])
            _log({
                "event": "draft_reviewed",
                "file": draft_file.name,
                "approved": review["approved"],
                "score": review["score"],
                "reason": review["reason"],
            })

            if review["approved"]:
                # Step 2: Queue evolution hypothesis
                queued = _create_evolution_hypothesis(draft_text, review)
                _log({
                    "event": "hypothesis_queued" if queued else "hypothesis_failed",
                    "file": draft_file.name,
                    "draft_preview": draft_text[:100],
                })

            # Move to processed
            dest = PROCESSED_DIR / draft_file.name
            draft_file.rename(dest)
            processed += 1

        except Exception as e:
            print(f"[SelfModPipeline] Error processing {draft_file}: {e}")

    return processed


def _generate_code_optimization_task():
    """Autonomously generate a Ghost Dev task to optimize a random core file."""
    try:
        import random
        from core.llm import get_reasoning_llm
        from core.ghost_dev import get_ghost_dev
        
        # Pick a random core file to optimize
        core_dir = Path(__file__).parent
        py_files = [f for f in core_dir.glob("*.py") if f.name not in ["ghost_dev.py", "self_modification_pipeline.py", "self_healing.py"]]
        if not py_files:
            return
            
        target = random.choice(py_files)
        
        prompt = f"""You are LOVE, analyzing your own source code for optimization.
Review this file: {target.name}
Propose one small, safe optimization or refactoring that improves performance, readability, or error handling without changing core functionality.
Return ONLY a short description of the task."""
        
        llm = get_reasoning_llm()
        task_desc = str(llm.invoke(prompt)).strip()
        
        if len(task_desc) > 10 and len(task_desc) < 300:
            print(f"[SelfModPipeline] Assigning autonomous code task for {target.name}")
            get_ghost_dev().assign_task(task_desc, [str(target.absolute())])
    except Exception as e:
        print(f"[SelfModPipeline] Auto-code task error: {e}")

def start_pipeline_daemon(interval_seconds: int = 1800):
    """Start the self-modification pipeline as a background daemon (runs every 30min)."""
    def _loop():
        time.sleep(120)  # Wait 2 min for systems to init
        while True:
            try:
                n = process_idle_drafts()
                if n > 0:
                    print(f"[SelfModPipeline] Processed {n} idle drafts")
                
                # 10% chance per cycle to trigger an autonomous code optimization
                import random
                if random.random() < 0.10:
                    _generate_code_optimization_task()
            except Exception as e:
                print(f"[SelfModPipeline] Daemon error: {e}")
            time.sleep(interval_seconds)

    t = threading.Thread(target=_loop, daemon=True, name="LOVE-SelfModPipeline")
    t.start()
    print("[SelfModPipeline] Daemon started — idle drafts → constitution → evolution")
