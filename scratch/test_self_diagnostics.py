import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from core.module_lifecycle import get_lifecycle, ModuleDescriptor, ModuleState
from core.self_improvement_daemon import get_improvement_daemon
from core.adaptive import _load_state, _save_state

async def main():
    print("--- STEP 1: INITIAL SYSTEM LIFECYCLE ---")
    lifecycle = get_lifecycle()
    
    # Register a mock module that fails
    def mock_start():
        raise ValueError("Mock hardware failure!")
        
    mock_descriptor = ModuleDescriptor(
        name="mock_faulty_module",
        wave=3,
        start_fn=mock_start,
        optional=True,
        description="A mock module that fails on startup"
    )
    
    lifecycle.register(mock_descriptor)
    
    # Start it (it will fail)
    try:
        if asyncio.iscoroutinefunction(mock_descriptor.start_fn):
            await mock_descriptor.start_fn()
        else:
            mock_descriptor.start_fn()
        mock_descriptor.state = ModuleState.READY
    except Exception as e:
        mock_descriptor.state = ModuleState.FAILED
        mock_descriptor.error = str(e)
        
    print(f"Mock module status: {mock_descriptor.state} | error: {mock_descriptor.error}")
    
    print("\n--- STEP 2: INDUCE FRUSTRATION ---")
    state = _load_state()
    original_frust = state.get("frustration_signals", 0)
    original_total = state.get("total_interactions", 0)
    
    state["frustration_signals"] = 10
    state["total_interactions"] = 20  # 50% frustration rate
    _save_state(state)
    print(f"Induced frustration signals: {state['frustration_signals']}/{state['total_interactions']}")
    
    try:
        print("\n--- STEP 3: RUN DAEMON DIAGNOSTICS ---")
        daemon = get_improvement_daemon()
        report = daemon.run_diagnostics()
        
        print(f"Diagnostics Health Score: {report.health_score}")
        print("Detected Issues:")
        for issue in report.issues:
            print(f"  - [{issue['subsystem']}] {issue['issue']} | Rec: {issue['recommendation']}")
            
        print("Recommended Improvements:")
        for imp in report.improvements:
            print(f"  - [{imp['category']}] {imp['action']} | Priority: {imp['priority']} | Auto: {imp['auto_execute']}")
            
        print("\n--- STEP 4: MOCK REPAIR & RESTART ---")
        # Change mock start function to succeed on restart
        def mock_restart_ok():
            print("  -> Mock start succeeded!")
            return {"status": "ready"}
            
        mock_descriptor.start_fn = mock_restart_ok
        
        # Execute improvements
        print("Executing improvements...")
        res = daemon.execute_improvements(report)
        print(f"Executed: {res['executed']} | Failed: {res['failed']}")
        
        # Yield to event loop to allow the scheduled restart tasks to run
        await asyncio.sleep(0.1)
        print(f"New mock module state: {mock_descriptor.state} | error: {mock_descriptor.error}")
        
    finally:
        # Restore original state
        state = _load_state()
        state["frustration_signals"] = original_frust
        state["total_interactions"] = original_total
        _save_state(state)
        print("\n--- CLEANUP COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(main())
