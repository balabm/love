# LOVE — Agent Notes

## Test Commands

```bash
# Evolution system tests (39 tests)
python -m pytest tests/test_evolution_systems.py -v --tb=short

# API startup
cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Key Architecture

- **Master Orchestrator** (`core/master_orchestrator.py`): Central brain, life pulse reports evolution activity
- **AGI Spine** (`core/agi_spine.py`): Bridges all modules, counts all systems dynamically
- **Heartbeat** (`core/heartbeat.py`): Triggers evolution self-improvement during idle periods
- **Daily Briefing** (`core/daily_briefing.py`): Morning brief includes overnight evolution activity
- **Sentinel** (`core/sentinel.py`): User presence + system monitoring

### Evolution Ecosystem (Fully Closed Loop)

- **Evolution Engine** (`core/evolution_engine.py`): Base self-improvement
- **Meta-Evolution** (`core/meta_evolution.py`): Applies best strategies as real hypotheses
- **Swarm Evolution** (`core/swarm_evolution.py`): Evaluates swarms, creates mutations for winners
- **Cross-Instance** (`core/cross_instance_learning.py`): Shares/adopts peer mutations
- **Self-Coder** (`core/self_coder.py`): Generates modifications from file analysis, tests in sandbox
- **Gap Detector** (`core/capability_gap_detector.py`): Detects gaps, triggers self-coder for high-impact ones
- **Autonomous CI/CD** (`core/autonomous_cicd.py`): Auto-approves low-risk mods, deploys, auto-rollback on failure
- **Evolution Integration** (`core/evolution_integration.py`): Coordinates all subsystems, reports to orchestrator

## Closed Loop Flow

```
Generate (Self-Coder) -> Test (Sandbox) -> Auto-Approve (CI/CD for low-risk)
  -> Deploy (CI/CD) -> Report (Integration -> Orchestrator -> User)
```

All subsystems produce actual improvements and report to the orchestrator.

## UI Views

- **Chat**: Main interaction stream
- **Swarm**: Coordinated multi-agent view
- **Autonomy (Mind)**: Wave Engine / Fleet Supervisor / Sentinel Monitor / Orchestrator / Intelligence Dashboard
- **Evolution**: SelfEvolutionPanel + TerminalPanel + Static Dashboard link + Orchestrator evolution metrics
- **Pulse**: Life domains / Focus mode / Rituals
- **Finance**: Finance guardian
- **Cosmos**: Device topology

## Static Assets

- Evolution dashboard HTML: `/static/evolution_dashboard.html`
  - Shows: integration status, active experiments, mutation timeline, swarm performance, capability gaps, deployments

## Important Files

- `EVOLUTION_SYSTEM.md`: Full evolution system design documentation
- `integrate_evolution_startup.py`: Integration guide (marked COMPLETE)
- `start_evolution.py`: Standalone evolution system startup script

Generated with [Devin](https://cli.devin.ai/docs)
