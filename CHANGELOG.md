# CHANGELOG

Historical development snapshots for Project LOVE.  
For current architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).  
For honest capability assessment, see [GAP_TO_AGI.md](GAP_TO_AGI.md).

---

## Wave 28 (May 2026) — Planning Calibration Depth + PEFT Adapter Export

### 28A: Query-Category-Aware Calibration
- `core/rollout_planner.py`: keyword-based query classifier (casual/emotional/technical/task)
- Per-category style accuracy tracking (`casual:empathetic`, `technical:analytical`, etc.)
- Graduated directives now use category-specific accuracy when available
- `GET /planner/category-stats` — per-category accuracy dashboard
- `POST /planner/detect-category` — query classification endpoint

### 28B: Real PEFT Adapter Export
- `core/lora_evolution.py`: `save_as_checkpoint()` produces proper PEFT format
- `adapter_config.json` with standard PEFT keys (peft_type, r, lora_alpha, target_modules)
- `adapter_model.bin` with PyTorch state_dict using standard PEFT weight keys
- `adapter_model.safetensors` if safetensors available
- `GET /lora/export-peft/{adapter_id}` — export any adapter as PEFT checkpoint
- `GET /lora/peft-status` — torch/peft availability check
- Added `get_adapter(id)` for retrieving adapters by ID

## Wave 27 (May 2026) — Active Planning + Focus-Aware Heartbeat

### 27A: Active Model Predictive Control
- `core/rollout_planner.py` upgraded: passive hint → active directive
- `plan_active()` samples 6 response styles, simulates 4-step MLP rollout each
- Graduated enforcement based on calibration confidence (strong/prefer/consider)
- Wired into `core/agent.py` via `get_planning_context()`

### 27B: Focus-Aware Heartbeat Gating
- `core/heartbeat.py` `_filter_triggers()` now checks `_is_focus_mode()`
- During focus: only critical/warning triggers pass; info/celebration queued
- Queued nudges stored in `data/suppressed_nudges.json`, delivered post-focus
- Reads from `focus_session.json` and `work_tracker` for focus state

### 27C: Planning Outcome Learning
- `verify_outcome()` embeds LLM response, computes actual FE trajectory
- Compares predicted vs actual FE → calibration confidence (EMA-updated)
- Per-style accuracy tracked (last 20 outcomes per style)
- Outcomes persisted to `data/planner/outcomes.jsonl`
- Wired into `core/agent.py` post-response pipeline

### New API endpoints
- `GET /planner/snapshot` — full planner telemetry + outcome stats
- `POST /planner/plan_active` — run active planning for a query
- `GET /planner/calibration` — planning confidence and accuracy
- `GET /heartbeat/focus-status` — focus mode state + suppressed nudge queue

## Wave 26 (May 2026) — Ritual Integration + Push

- `RitualView.jsx` enhanced with body status sections (morning + evening)
- Life Coach nudges wired into heartbeat cycle
- WebSocket push for real-time UI updates
- `HomeostasisPanel.jsx` for living substrate vitals

## Wave 25 — Proactive Life Coach

- `core/life_coach.py` — time-windowed nudges, adaptive goals from 7-day rolling averages
- Focus mode detection to avoid interrupting deep work
- Coach nudges and adaptive goals surfaced in Ritual view

## Wave 24 — Cross-Domain Intelligence

- `core/cross_domain_intelligence.py` — correlates sleep/hydration/mood/productivity
- Compound deficit and streak momentum detection
- Wired into daily briefing data gathering

## Wave 23 — Wave Evolution Engine

- `core/wave_engine.py` — GapScanner + WaveProposer
- LOVE detects its own capability gaps and proposes what to build next
- UI: `WaveEngine.jsx` showing gap analysis and Wave proposals

## Wave 22 — Life Domains Engine

- `core/life_domains.py` — tracking hydration, sleep, nutrition, skincare
- Streaks, adaptive goals, proactive nudges
- 20+ API routes under `/life/`
- UI: `LifeDomains.jsx` with 4-card grid, SVG rings, inline forms

## Waves 19-21 — Self-Modification Pipeline

- Self-modification pipeline with diff → apply → test
- BPTT-inspired temporal learning scaffold
- LoRA evolution scaffold
- User-aligned fitness scoring for evolution

## Wave 18 — Error Boundaries + UI Hardening

- `ErrorBoundary.jsx` wrapping all panels
- Graceful degradation when backend is unreachable
- CSS hardening across all components

## Wave 17 — Evolution Dashboard + Sentinel

- `EvolutionPanel.jsx` — evolution system dashboard
- `SentinelPanel.jsx` — system health monitor
- `core/sentinel.py` — always-on watchdog

## Wave 16 — Neural Mesh + Living Substrate

- `core/neural_bus.py` — event-driven inter-module communication
- `core/living_substrate.py` — world model + SSM + MoE + homeostasis
- `core/consciousness.py` — Global Workspace Theory implementation
- `NeuralMesh.jsx` — neural bus visualization
- `HomeostasisPanel.jsx` — substrate vitals

## Wave 15 — Daily Briefing + Setup Wizard

- `core/daily_briefing.py` — LLM-generated morning briefing
- `SetupWizard.jsx` — first-run credential setup
- `BriefingPanel.jsx` — daily brief UI

## Waves 12-14 — Agent Loop + Integrations

- `core/agent_loop.py` — main agent execution loop
- `integrations/google_services.py` — Calendar, Gmail, Drive (OAuth2)
- `integrations/microsoft_bridge.py` — Outlook, Teams, OneDrive
- `integrations/github_monitor.py` — notifications, PR activity
- `IntegrationsPanel.jsx`, `AgentLoopPanel.jsx`

## Waves 9-11 — Context Engine + Intelligence Hub

- `core/context_engine.py` — real-time context assembly
- `core/intelligence_hub.py` — cross-source intelligence fusion
- `core/awareness.py` — system monitoring
- `IntelligenceDashboard.jsx`, `ContextPanel.jsx`

## Waves 7-8 — Self-Healing + Ghost Developer

- `core/self_healing.py` — crash detection and auto-fix
- `core/ghost_dev.py` — auto-generate tests and boilerplate
- `core/autonomous_self_improvement.py` — A/B tested self-modification

## Waves 1-6 — Foundation

- Companion chat with personality presets
- ChromaDB vector memory
- Work-life guardian with hour tracking
- Finance sentinel with portfolio tracking
- Multi-device sync
- Voice interface (STT/TTS)
- Self-healing and optimization

---

## Archived Summaries

The following point-in-time summaries existed as separate files and have been consolidated here.
They document the state of the system at the time they were written, not the current state.

### AGI Architecture (pre-Wave 22)

Documented 5 AGI systems: Ontological Engine, Free Energy Principle, Active Inference,
Global Workspace Theory, and Consciousness Bus. These are now part of the neural substrate
in `core/consciousness.py`, `core/living_substrate.py`, and `core/cognitive_architecture.py`.

### Autopoietic Auditor (pre-Wave 22)

1,345-line self-monitoring system detecting semantic, logical, performance, output, and
error drift across modules. Now integrated into `core/sentinel.py` and `core/metacognitive_monitor.py`.

### Axiological + Teleological Systems (pre-Wave 22)

Axiological Engine evaluates actions against 8 core life tenets. Teleological Feedback Loop
for outcome-vs-prediction learning. Now in `core/constitution.py` and `core/feedback_collector.py`.

### Critical Fixes (point-in-time)

5 tactical fixes addressing 70.8% import success rate: Intelligence Hub repairs, missing
logging, type annotation fixes, silent error handling. All fixes applied to codebase.

### Evolution System (pre-Wave 22)

10 self-improvement systems: Meta-Evolution, Swarm Evolution, Self-Coder, Cross-Instance
Learning, etc. Now spread across `core/evolution_engine.py`, `core/self_coder.py`,
`core/swarm_evolution.py`, `core/meta_evolution.py`, and related modules.

### Liquid Neural Enhancements (pre-Wave 22)

Enhanced AST manipulation engine for recursive self-transcendence with morphological
freedom. Now part of `core/self_modification_pipeline.py` and `core/self_coder.py`.

### Module Inspection Report (pre-Wave 22)

Audit showing 107 modules, 70.8% import success, 290+ endpoints, 16 React components.
System has since grown to 120 modules, 443 endpoints, 20 components with higher stability.

### Initialization Status (point-in-time)

Snapshot from 2026-05-27 confirming Python 3.12.10, dependencies installed, configuration
validated. Superseded by current system state.
