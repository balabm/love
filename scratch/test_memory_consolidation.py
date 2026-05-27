import sys
import os
import time
import json
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx

async def main():
    print("--- STEP 1: VERIFY/CLEAN OLD LOGS ---")
    log_file = PROJECT_ROOT / "data" / "conversations.jsonl"
    if log_file.exists():
        try:
            log_file.unlink()
            print("Cleaned old conversations.jsonl")
        except Exception as e:
            print(f"Could not delete conversations.jsonl: {e}")

    last_file = PROJECT_ROOT / "data" / "last_consolidation.txt"
    if last_file.exists():
        try:
            last_file.unlink()
            print("Cleaned old last_consolidation.txt")
        except Exception as e:
            print(f"Could not delete last_consolidation.txt: {e}")

    print("\n--- STEP 2: SIMULATE CHAT TURNS ---")
    # Simulate a chat turn via HTTP
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("Sending chat turn 1...")
        try:
            r1 = await client.post("http://127.0.0.1:8000/chat", json={
                "text": "I really love coding in Python and building AGI systems. I want to build a self-improving assistant.",
                "mode": "general"
            })
            print(f"Response: {r1.json().get('response')}")
        except Exception as e:
            print(f"Chat turn 1 request failed: {repr(e)}")

        print("Sending chat turn 2...")
        try:
            r2 = await client.post("http://127.0.0.1:8000/chat", json={
                "text": "I am feeling stressed today because I have an upcoming standup meeting, and I did not sleep well last night.",
                "mode": "general"
            })
            print(f"Response: {r2.json().get('response')}")
        except Exception as e:
            print(f"Chat turn 2 request failed: {repr(e)}")

    # Check if conversations.jsonl exists and has turns
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        print(f"\nCreated conversations.jsonl with {len(lines)} turns:")
        for line in lines:
            print(f"  - {line[:120]}")
    else:
        print("\nERROR: conversations.jsonl was not created!")
        return

    print("\n--- STEP 3: TRIGGER DAEMON DIAGNOSTICS & CONSOLIDATE ---")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Trigger diagnostics
        print("Running diagnostics scan...")
        diag_res = await client.post("http://127.0.0.1:8000/agi/daemon/diagnose")
        diag_data = diag_res.json()
        print(f"Diagnostics health score: {diag_data.get('health_score')}")
        print("Detected issues:")
        for issue in diag_data.get("issues", []):
            print(f"  - [{issue['subsystem']}] {issue['issue']} | Rec: {issue['recommendation']}")

        # Look for the memory_consolidation improvement
        improvements = diag_data.get("improvements", [])
        print("Recommended improvements:")
        has_consolidation = False
        for imp in improvements:
            print(f"  - [{imp['category']}] {imp['action']} (auto: {imp['auto_execute']})")
            if imp['category'] == "memory_consolidation":
                has_consolidation = True

        if has_consolidation:
            print("\nDiagnostics correctly identified the need for memory consolidation!")
        else:
            print("\nWARNING: Diagnostics did not recommend memory consolidation.")

        # Let's force execute memory consolidation to verify it writes episodic memories
        print("\nConsolidating memory...")
        # We trigger the daemon diagnostics execution, or call the endpoint
        from core.self_improvement_daemon import get_improvement_daemon
        daemon = get_improvement_daemon()
        # Create a report object
        from core.self_improvement_daemon import DiagnosticReport
        report = DiagnosticReport(
            timestamp=diag_data.get("timestamp"),
            health_score=diag_data.get("health_score"),
            issues=diag_data.get("issues"),
            improvements=diag_data.get("improvements"),
            strengths=diag_data.get("strengths")
        )
        res = daemon.execute_improvements(report)
        print(f"Improvements execution result: {res}")

    # Check temporal memories database
    from core.long_term_memory import _db
    try:
        with _db() as conn:
            episodic = conn.execute("SELECT * FROM episodic_memories").fetchall()
            semantic = conn.execute("SELECT * FROM semantic_memories").fetchall()
            print(f"\nSQLite Long-Term Memory Stats:")
            print(f"  - Episodic memories count: {len(episodic)}")
            for ep in episodic[:3]:
                print(f"    * [{ep['date']}] {ep['summary']}")
            print(f"  - Semantic memories count: {len(semantic)}")
            for sem in semantic[:3]:
                print(f"    * {sem['subject']} {sem['predicate']} {sem['obj']}")
    except Exception as e:
        print(f"Could not read long term memory db: {e}")

if __name__ == "__main__":
    asyncio.run(main())
