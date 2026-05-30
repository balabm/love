# LOVE Evolution System

## Closed-Loop Self-Improvement (v3)

LOVE operates a fully closed-loop self-improvement ecosystem.

### Data Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Meta-Evolution │────▶│ Evolution Engine │────▶│  Self-Coder  │
│   (strategies)  │     │  (hypotheses)    │     │ (modifications)
└─────────────────┘     └──────────────────┘     └──────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Cap-Gap-Det.   │────▶│  Autonomous CI/CD│◀────│   (tests)    │
│  (missions)     │     │  (deployments)   │     └──────────────┘
└─────────────────┘     └──────────────────┘              │
         │                                                  │
         ▼                                                  ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Swarm Evolution│────▶│ Cross-Instance   │────▶│  Orchestrator│
│  (validation)   │     │   Learning       │     │  (narrative) │
└─────────────────┘     └──────────────────┘     └──────────────┘
```

### Key Behaviors

| Subsystem | Action Every Cycle | Reports To |
|-----------|-------------------|------------|
| Meta-Evolution | Applies best strategy as hypothesis | Orchestrator |
| Swarm Evolution | Evaluates swarms, creates mutations for winners | Orchestrator |
| Cross-Instance | Shares local mutations, adopts peer mutations | Orchestrator |
| Self-Coder | Generates modifications from file analysis | Orchestrator |
| Gap Detector | Creates missions, triggers self-coder | Orchestrator + Mission Queue |
| CI/CD | Monitors deployments, auto-rollback on failure | Orchestrator |
| Integration | Runs full cycle, publishes to neural bus | Orchestrator |

### Closed Loop Flow

```
Generate -> Test -> Auto-Approve -> Deploy -> Report
```

1. **Self-Coder** generates modifications from file analysis
2. **Self-Coder** tests modifications in sandbox
3. **Autonomous CI/CD** auto-approves low-risk modifications that passed tests
4. **Autonomous CI/CD** deploys approved modifications
5. **Evolution Integration** reports activity to orchestrator
6. **Orchestrator** includes evolution activity in life pulse messages to user

### UI Visibility

- **Intelligence Dashboard**: Shows integration status, capability gaps, deployments
- **Sentinel Panel**: Shows orchestrator narrative filtered for sentinel events
- **Evolution View**: SelfEvolutionPanel shows integration pipeline + gaps + deployments
- **Orchestrator Panel**: Shows real-time evolution metrics (mods, mutations, adoptions, gaps, deployments)
- **Static Dashboard**: `/static/evolution_dashboard.html` for full Chart.js analytics

### API Endpoints

| Endpoint | Data |
|----------|------|
| `/evolution/status` | Meta, swarm, self-coder, cross-instance status |
| `/evolution/metrics` | Satisfaction, quality, hypothesis success rates |
| `/evolution/experiments` | Active and completed experiments |
| `/evolution/swarms` | Active swarm intelligence units |
| `/evolution/history` | Evolution event timeline |
| `/evolution/health` | Health status of all 7 evolution subsystems |
| `/intelligence/self-evolution` | Integration + gaps + deployments + active experiments |

### Startup

```bash
# Standalone evolution startup
python start_evolution.py

# Or via main LOVE API (evolution systems auto-start)
cd api && uvicorn main:app --host 0.0.0.0 --port 8000
```

Generated with [Devin](https://cli.devin.ai/docs)
