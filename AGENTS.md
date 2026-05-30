# LOVE — Agent Notes

## Test Commands

```bash
# Evolution system tests (39 tests)
python -m pytest tests/test_evolution_systems.py -v --tb=short

# API startup
cd api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Key Architecture

- **Master Orchestrator** (`core/master_orchestrator.py`): Central brain
- **AGI Spine** (`core/agi_spine.py`): Bridges all modules
- **Evolution Engine** (`core/evolution_engine.py`): Base self-improvement
- **Meta-Evolution** (`core/meta_evolution.py`): Strategy application
- **Swarm Evolution** (`core/swarm_evolution.py`): Hypothesis validation
- **Cross-Instance** (`core/cross_instance_learning.py`): Peer mutation sharing
- **Self-Coder** (`core/self_coder.py`): Code modification generation
- **Gap Detector** (`core/capability_gap_detector.py`): Detects + triggers fixes
- **Autonomous CI/CD** (`core/autonomous_cicd.py`): Deployment + rollback
- **Sentinel** (`core/sentinel.py`): User presence + system monitoring

## Evolution Closed Loop

All subsystems report to orchestrator and produce actual improvements:

1. Meta-evolution applies best strategies as real hypotheses
2. Swarm evolution evaluates swarms, creates mutations for winners
3. Cross-instance shares/adopts peer mutations
4. Self-coder generates modifications from file analysis
5. Gap detector triggers self-coder for high-impact gaps
6. CI/CD monitors deployments, auto-rollback on failure

## UI Views

- **Chat**: Main interaction stream
- **Swarm**: Coordinated multi-agent view
- **Autonomy (Mind)**: Wave Engine / Fleet Supervisor / Sentinel Monitor / Orchestrator / Intelligence Dashboard
- **Evolution**: SelfEvolutionPanel + TerminalPanel + Static Dashboard link
- **Pulse**: Life domains / Focus mode / Rituals
- **Finance**: Finance guardian
- **Cosmos**: Device topology

## Static Assets

- Evolution dashboard HTML: `/static/evolution_dashboard.html`
