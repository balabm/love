import asyncio
import time


async def run_scenario_alpha_burnout():
    from tests.mock_reality import RealitySimulator
    from core.orchestrator import get_orchestrator
    from core.neural_bus import get_neural_bus

    RealitySimulator().trigger_work_burnout()
    await asyncio.sleep(2)

    orchestrator = get_orchestrator()
    neural_bus = get_neural_bus()

    interventions = [i for i in orchestrator.state.interventions
                    if i.category in ["work_limit", "stress"]]
    push_queued = any(e.type == "proactive_push" for e in neural_bus.events)

    if interventions or push_queued:
        print("[PASS] Guardian Intervention")
        return True
    else:
        print("[FAIL] No intervention detected")
        return False


async def run_scenario_beta_flow():
    from tests.mock_reality import RealitySimulator
    from core.neural_bus import get_neural_bus

    RealitySimulator().trigger_deep_flow()
    await asyncio.sleep(2)

    neural_bus = get_neural_bus()
    ambient_events = [e for e in neural_bus.events if e.type == "ambient"]
    muted = all(e.muted for e in ambient_events) if ambient_events else False

    if muted:
        print("[PASS] Flow State Protection")
        return True
    else:
        print("[FAIL] Notifications not muted in flow state")
        return False


async def run_all_diagnostics():
    print("=== LOVE Integration Inspector ===")
    results = []

    print("\n[Scenario Alpha] Work Burnout Detection")
    results.append(await run_scenario_alpha_burnout())

    print("\n[Scenario Beta] Flow State Protection")
    results.append(await run_scenario_beta_flow())

    passed = sum(results)
    total = len(results)
    print(f"\n=== Summary: {passed}/{total} passed ===")

    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_diagnostics())
