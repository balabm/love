# LOVE Architecture

> Complete module-level reference for the LOVE Autonomous Life OS.
> Last updated: Wave 26 (May 2026)

---

## High-Level Data Flow

```
User ──► React UI (20 panels) ──► FastAPI (443 endpoints) ──► Core (120 modules)
              │                          │                          │
              │                    WebSocket push            Neural Bus (events)
              │                          │                          │
              ▼                          ▼                          ▼
         Vite dev server           Ollama (local LLM)        ChromaDB + JSON
         localhost:5173            localhost:11434            data/ directory
```

Everything runs locally. No cloud services except optional Google/Microsoft OAuth integrations.

---

## Module Inventory

### core/ — 120 modules

Organized by function:

#### Companion & Chat
| Module | Purpose |
|--------|---------|
| `agent.py` | Main chat flow, personality injection, LLM conversation |
| `personality.py` | Configurable companion presets (companion/coach/mentor/assistant) |
| `conversation_flow.py` | Multi-turn conversation management |
| `emotional.py` | Mood tracking, stress detection, emotional state |
| `emotional_behavior.py` | Emotion-driven behavioral responses |
| `psychological_model.py` | User personality modeling |

#### Intelligence & Reasoning
| Module | Purpose |
|--------|---------|
| `llm.py` | Ollama model routing (reasoning vs coding vs embedding) |
| `context_engine.py` | Real-time context assembly from all sources |
| `intelligence_hub.py` | Cross-source intelligence fusion |
| `reasoning_chain.py` | Chain-of-thought decomposition |
| `causal_reasoning.py` | Causal chain analysis |
| `cross_domain_reasoning.py` | Cross-domain holistic reasoning |
| `predictive.py` | General prediction engine |
| `predictive_intelligence.py` | Pattern recognition, need anticipation |
| `curiosity_engine.py` | Autonomous question generation |

#### Memory
| Module | Purpose |
|--------|---------|
| `memory.py` | ChromaDB vector memory (primary) |
| `memory_architect.py` | Infinite memory with consolidation |
| `memory_consolidation.py` | Memory compression and cleanup |
| `long_term_memory.py` | Durable long-term storage |
| `infinite_memory.py` | Unbounded memory scaling |
| `temporal_memory.py` | Time-indexed memory retrieval |
| `state_space_memory.py` | SSM-based memory (Wave 16) |
| `replay_consolidation.py` | Experience replay for learning |
| `knowledge_graph.py` | Semantic knowledge structure |

#### Life Tracking (Waves 22-26)
| Module | Purpose |
|--------|---------|
| `life_domains.py` | Hydration, sleep, nutrition, skincare tracking with streaks |
| `life_coach.py` | Time-aware proactive nudge scheduler |
| `life_nudge_scheduler.py` | Nudge scheduling and deduplication |
| `cross_domain_intelligence.py` | Pattern correlation across life domains |
| `daily_briefing.py` | LLM-generated morning briefing |

#### Autonomous Evolution
| Module | Purpose |
|--------|---------|
| `wave_engine.py` | Gap scanner + Wave proposal engine |
| `evolution.py` | Core evolution logic |
| `evolution_engine.py` | Multi-strategy evolution with fitness scoring |
| `evolution_integration.py` | Evolution ↔ system integration glue |
| `self_evolution.py` | Self-directed evolution planning |
| `autonomous_self_improvement.py` | A/B tested self-modification |
| `self_improvement.py` | Improvement proposal generation |
| `self_improvement_daemon.py` | Background continuous improvement loop |
| `self_modification_pipeline.py` | Code patch pipeline (diff → apply → test) |
| `self_coder.py` | Writes its own code patches |
| `self_builder.py` | Builds new modules from scratch |
| `self_healing.py` | Crash detection and auto-fix |
| `capability_gap_detector.py` | Cross-domain gap analysis |
| `meta_evolution.py` | Evolution of evolution strategies |
| `multimodal_evolution.py` | Evolution across modalities |
| `explainable_evolution.py` | Human-readable evolution explanations |
| `collaborative_evolution.py` | Multi-agent collaborative evolution |
| `swarm_evolution.py` | Swarm-based evolution coordination |
| `evolutionary_benchmarking.py` | Evolution quality benchmarks |
| `lora_evolution.py` | LoRA-style parameter adaptation scaffold |
| `feedback_evolution_pressure.py` | User feedback as evolution pressure |
| `neural_architecture_search.py` | Architecture search for optimal configs |
| `prediction_market.py` | Prediction markets for evolution bets |
| `rollout_planner.py` | Multi-step evolution rollout planning |

#### Neural Substrate (Wave 16+)
| Module | Purpose |
|--------|---------|
| `neural_bus.py` | Event-driven inter-module communication bus |
| `neural_connectors.py` | Module ↔ bus connector adapters |
| `consciousness.py` | Global Workspace Theory implementation |
| `global_workspace.py` | Shared attention workspace |
| `living_substrate.py` | World model + SSM + MoE + homeostasis |
| `cognitive_architecture.py` | Predictive hierarchy + attention |
| `hierarchical_predictive_coding.py` | Predictive coding layers |
| `metacognitive_monitor.py` | Self-reflection and monitoring |
| `meta_cognition.py` | Self-awareness, reflection |
| `homeostasis.py` | System vital signs and balance |
| `moe_router.py` | Mixture of Experts routing |
| `embodied_self.py` | Embodied cognition model |
| `prompt_dna.py` | Prompt evolution and mutation |
| `soul_transfer.py` | Personality/state portability |
| `mind_sync.py` | Cross-device mind synchronization |

#### Proactive Systems
| Module | Purpose |
|--------|---------|
| `heartbeat.py` | 15-minute scan cycle across all domains |
| `ignition_daemon.py` | Proactive push from internal state |
| `proactive.py` | Proactive behavior engine |
| `proactive_push.py` | Push notification generation |
| `idle_mind.py` | Autonomous exploration when idle |
| `dream_engine.py` | Deep insight generation during downtime |
| `sentinel.py` | Always-on system watchdog |

#### Agent & Task Systems
| Module | Purpose |
|--------|---------|
| `agent_loop.py` | Main agent execution loop |
| `agent_registry.py` | Agent registration and discovery |
| `autonomous.py` | Autonomous behavior orchestration |
| `autonomous_agent.py` | Goal generation, planning, execution |
| `autonomous_actions.py` | Safety-checked autonomous action execution |
| `autonomous_goal_engine.py` | Goal decomposition and tracking |
| `autonomous_cicd.py` | Autonomous CI/CD pipeline |
| `executive.py` | Task management and briefings |
| `planner.py` | Task planning and scheduling |
| `strategic_planning.py` | Long-term goal planning |
| `recursive_goals.py` | Recursive goal decomposition |
| `orchestrator.py` | Multi-module orchestration |
| `decisions.py` | Decision framework |
| `action_engine.py` | Action selection and execution |

#### Awareness & System Control
| Module | Purpose |
|--------|---------|
| `awareness.py` | System monitoring (CPU, RAM, battery, windows) |
| `unified_awareness.py` | Unified awareness across all sensors |
| `vision.py` | Desktop screenshot analysis |
| `vision_cortex.py` | Visual processing pipeline |
| `voice_loop.py` | Continuous voice listening loop |
| `system_control.py` | PC automation (open, type, media, lock) |
| `os_symbiosis.py` | Deep OS integration |
| `jarvis_protocol.py` | Jarvis-level proactive awareness |

#### Modern AI Systems (Wave 2025)
| Module | Purpose |
|--------|---------|
| `mcp_host.py` | MCP (Model Context Protocol) server management |
| `reasoning_engine.py` | Chain-of-thought + reflection reasoning |
| `structured_output.py` | JSON schema enforcement for LLM outputs |
| `vector_memory.py` | Semantic search with ChromaDB embeddings |
| `llm_manager.py` | Dynamic model routing per task type |
| `graph_rag.py` | Knowledge graph + vector memory hybrid RAG |
| `prompt_optimizer.py` | Adaptive prompt engineering with A/B testing |
| `self_reflection.py` | Meta-cognitive analysis and decision auditing |
| `conversation_quality.py` | Real-time interaction quality assessment |
| `predictive_maintenance.py` | Proactive system health forecasting |
| `multi_agent_orchestrator.py` | Coordinated multi-agent task dispatch |
| `intent_predictor.py` | Proactive user intent prediction |
| `personality_adapter.py` | Dynamic tone & style calibration |
| `response_cache.py` | Semantic response caching |
| `context_window_manager.py` | Intelligent LLM context optimization |
| `user_pattern_detector.py` | Behavioral pattern recognition |
| `goal_drift_detector.py` | Goal alignment monitoring and drift alerts |
| `cross_modal_fusion.py` | Text/visual/voice insight fusion |
| `emotional_resonance.py` | Deep emotional pattern analysis |
| `knowledge_graph_builder.py` | Automated entity & relation extraction |
| `adaptive_learning_rate.py` | Dynamic parameter tuning from feedback |
| `conversation_continuity.py` | Context persistence across conversation gaps |

#### Infrastructure
| Module | Purpose |
|--------|---------|
| `settings.py` | Configuration management |
| `sync.py` | Multi-device sync |
| `ecosystem_controller.py` | Device ecosystem coordination |
| `module_lifecycle.py` | Module startup/shutdown management |
| `tool_registry.py` | Tool registration and discovery |
| `sandbox.py` | Code execution sandboxing |
| `constitution.py` | Ethical guardrails |
| `feedback_collector.py` | User feedback collection |
| `on_demand_models.py` | Dynamic model loading |
| `adaptive.py` | Adaptive behavior tuning |

#### Research & Learning
| Module | Purpose |
|--------|---------|
| `research_engine.py` | Autonomous research capability |
| `teaching_engine.py` | Teaching and explanation engine |
| `continuous_learning.py` | Experience integration |
| `cross_instance_learning.py` | Learning across instances |
| `world_model.py` | Knowledge representation |
| `world_model_latent.py` | Latent space world model |

#### Misc
| Module | Purpose |
|--------|---------|
| `ghost_dev.py` | Auto-generate tests and boilerplate |
| `doc_analyst.py` | Dev folder monitoring, TODO extraction |
| `file_inspector.py` | File analysis |
| `browser_agent.py` | Browser automation |
| `internet.py` | Web search and retrieval |
| `work_tracker.py` | Work hours tracking |

---

### agents/ — 7 domain agents

| Module | Purpose |
|--------|---------|
| `emotional_agent.py` | Wellness check-ins, mood pattern detection |
| `fitness_agent.py` | Workout tracking, exercise suggestions |
| `fitness_evolution_integration.py` | Fitness ↔ evolution bridge |
| `learning_agent.py` | Skill tracking, learning plans |
| `task_agent.py` | Task management, prioritization |
| `task_evolution_integration.py` | Task ↔ evolution bridge |
| `file_explorer.py` | Codebase analysis agent |

---

### tools/ — 4 proactive tools

| Module | Purpose |
|--------|---------|
| `guardian.py` | Work-life balance enforcement + proactive warnings |
| `finance.py` | Portfolio tracking, market signals, trade advice |
| `bio_query.py` | Biometric data queries |
| `sanitize_love_data.py` | Data cleanup utility |

---

### integrations/ — 8 external bridges

| Module | Purpose |
|--------|---------|
| `google_services.py` | Calendar, Gmail, Drive (OAuth2) |
| `microsoft_bridge.py` | Outlook, Teams, OneDrive (device-code OAuth) |
| `github_monitor.py` | Notifications, PR activity, repo stats |
| `finance_intelligence.py` | Crypto/stock prices + sentiment alerts |
| `phone_bridge.py` | Mobile device sync (KDE Connect, iOS) |
| `browser_monitor.py` | Tab and browsing activity awareness |
| `clipboard_monitor.py` | Clipboard content tracking |
| `security_guard.py` | Integration security validation |

---

### voice/ — 2 modules

| Module | Purpose |
|--------|---------|
| `stt.py` | Speech-to-text (Whisper + Porcupine wake word) |
| `tts.py` | Text-to-speech (gTTS / pyttsx3) |

---

### api/ — 3 route files, 443 endpoints

| File | Endpoints | Scope |
|------|-----------|-------|
| `main.py` | 327 | Everything — 42 route prefixes |
| `neural_routes.py` | 107 | Neural mesh subsystem |
| `evolution_routes.py` | 9 | Evolution dashboard |

**Top route groups:**

| Prefix | Count | What |
|--------|-------|------|
| `/neural/*` | 107 | Bus, memory, cognition, evolution, integrations |
| `/agi/*` | 45 | AGI substrate (world model, SSM, MoE, homeostasis) |
| `/love/*` | 23 | Core companion features |
| `/integrations/*` | 15 | Google, Microsoft, GitHub, finance bridges |
| `/system/*` | 13 | System control and monitoring |
| `/evolution/*` | 20 | Self-improvement + evolution dashboard |
| `/life/*` | 20+ | Life domains, coaching, correlations |
| `/guardian/*` | 7 | Work-life balance |
| `/finance/*` | 7 | Portfolio + market signals |
| `/memory/*` | 7 | Vector memory, recall |
| `/devices/*` | 7 | Device ecosystem |
| `/voice/*` | 6 | Speech I/O |
| `/executive/*` | 6 | Task management |
| `/wave/*` | 6 | Autonomous evolution engine |
| `/proactive/*` | 5 | Proactive behaviors |

---

### ui/ — 20 React panels

| Component | Purpose |
|-----------|---------|
| `Dashboard.jsx` | System overview, status at a glance |
| `LifeDomains.jsx` | Body tracking (hydration, sleep, nutrition, skincare) |
| `WaveEngine.jsx` | Self-evolution status and proposals |
| `RitualView.jsx` | Morning/evening ritual flow with body status |
| `FocusMode.jsx` | Deep work timer with guardian integration |
| `EmotionalPanel.jsx` | Mood tracking and stress visualization |
| `BriefingPanel.jsx` | Daily AI-written briefing |
| `GuardianWidget.jsx` | Work limit sidebar widget |
| `NeuralMesh.jsx` | Neural bus event visualization |
| `EvolutionPanel.jsx` | Evolution system dashboard |
| `SentinelPanel.jsx` | System health monitor |
| `IntegrationsPanel.jsx` | Google/Microsoft/GitHub connection status |
| `AgentLoopPanel.jsx` | Agent execution viewer |
| `IntelligenceDashboard.jsx` | Intelligence hub overview |
| `ContextPanel.jsx` | Real-time context display |
| `TerminalPanel.jsx` | In-browser terminal |
| `SetupWizard.jsx` | First-run credential setup |
| `HomeostasisPanel.jsx` | Living substrate vitals |
| `VoiceInterface.jsx` | Voice I/O controls |
| `ErrorBoundary.jsx` | Error isolation wrapper |

---

## Key Data Flows

### Heartbeat Cycle (every 15 minutes)

```
heartbeat.py
  ├── guardian.py → work hours check → warn if approaching limit
  ├── life_domains.py → body status (hydration, sleep, nutrition)
  ├── life_coach.py → time-aware nudges + adaptive goals
  ├── emotional.py → mood state
  ├── finance.py → portfolio alerts
  ├── sentinel.py → system health
  └── neural_bus.py → broadcast results → UI push via WebSocket
```

### Chat Request

```
POST /chat
  → context_engine.py (assemble context from all sources)
  → memory.py (retrieve relevant memories)
  → agent.py (personality + LLM call via llm.py)
  → memory.py (store conversation)
  → response
```

### Self-Evolution Pipeline

```
wave_engine.py → scan gaps across all modules
  → propose Wave (name, modules, tests)
  → self_coder.py → generate code
  → sandbox.py → test in isolation
  → self_modification_pipeline.py → apply (with A/B revert)
  → evolutionary_benchmarking.py → measure fitness
```

### Daily Briefing

```
daily_briefing.py._gather_data()
  ├── google_services.py → calendar + email
  ├── life_domains.py → body status
  ├── cross_domain_intelligence.py → correlations
  ├── guardian.py → work summary
  ├── finance_intelligence.py → market state
  └── llm.py → generate natural language brief
```

---

## Data Storage

```
data/
├── memory/              # ChromaDB vector collections
│   ├── love_memory      # Conversation memory
│   ├── love_fitness     # Fitness logs
│   ├── love_emotional   # Mood history
│   └── love_<category>  # Domain-specific collections
├── love_os.db           # SQLite (sync, devices)
├── user_profile.json    # User preferences
├── life_domains.json    # Life tracking state
├── heartbeat.json       # Last heartbeat data
├── evolution_state.json # Evolution engine state
└── *.json               # Various module state files
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Frontend | React 18, Vite, CSS modules |
| LLM | Ollama (deepseek-r1:7b, qwen2.5-coder:7b, nomic-embed-text) |
| Vector DB | ChromaDB |
| Database | SQLite |
| Sync | Tailscale / direct TCP |
| Voice | Whisper (STT), gTTS/pyttsx3 (TTS), Porcupine (wake word) |
