# Project LOVE — Autonomous Life OS

> *Not a chatbot. A local-first, self-evolving AI companion that tracks your body, protects your energy, manages your work, and builds itself while you sleep.*

**95,000+ lines of Python | 128 core modules | 460+ API endpoints | 23 UI panels**

---

## What This Actually Is

LOVE is a full-stack autonomous system that runs entirely on your machine. It combines:

- A **companion AI** that knows you, not just answers questions
- A **life tracking engine** (sleep, hydration, nutrition, skincare) with cross-domain intelligence
- A **work guardian** that enforces limits and prevents burnout
- A **proactive coach** that nudges at the right time, not randomly
- A **self-evolving substrate** that detects its own gaps and proposes improvements
- A **neural mesh** of 34 interconnected modules with event-driven communication

It runs on local Ollama models (deepseek-r1:7b for reasoning, qwen2.5-coder:7b for code). No cloud. No subscriptions. Your data never leaves your machine.

---

## Quick Start

```bash
git clone https://github.com/balabm/love.git
cd love

# Backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
cp config.yaml settings.yaml   # Edit with your name + preferences

# Frontend
cd ui && npm install && cd ..

# Run (needs Ollama running on localhost:11434)
start.bat                      # Windows — starts backend + frontend + Ollama
# Or manually:
# uvicorn api.main:app --host 0.0.0.0 --port 8000
# cd ui && npm run dev
```

**Backend**: http://localhost:8000  
**Frontend**: http://localhost:5173  
**Health check**: http://localhost:8000/health

### Required Models

```bash
ollama pull deepseek-r1:7b        # Reasoning
ollama pull qwen2.5-coder:7b      # Code generation
ollama pull nomic-embed-text       # Embeddings
```

---

## System Architecture

```
love/
├── core/                 # 120 modules — the brain
│   ├── Life Tracking
│   │   ├── life_domains.py        # Hydration, sleep, nutrition, skincare
│   │   ├── life_coach.py          # Time-aware proactive nudge scheduler
│   │   ├── cross_domain_intelligence.py  # Correlation detection across domains
│   │   └── daily_briefing.py      # LLM-generated morning brief
│   │
│   ├── Autonomous Evolution
│   │   ├── autonomy_supervisor.py       # 5-phase AGI intelligence tick loop
│   │   ├── wave_engine.py               # Gap scan → Wave proposal → execution
│   │   ├── self_improvement_daemon.py   # Self-diagnostic + auto-improvement
│   │   ├── autonomous_goal_engine.py    # Context-aware goal execution
│   │   ├── research_engine.py           # Multi-hop web research + synthesis
│   │   ├── ghost_dev.py               # Autonomous background coder
│   │   ├── proactive_push.py          # Proactive insight delivery
│   │   ├── activity_log.py            # Centralized action recorder
│   │   ├── autonomous_self_improvement.py  # A/B tested self-modification
│   │   ├── self_coder.py              # Writes and applies its own code patches
│   │   ├── evolution_engine.py        # Multi-strategy evolution with fitness
│   │   ├── capability_gap_detector.py  # Cross-domain gap detection
│   │   └── self_healing.py            # Auto-detect and fix crashes
│   │
│   ├── Neural Substrate
│   │   ├── neural_bus.py          # Event-driven inter-module communication
│   │   ├── consciousness.py       # Global Workspace Theory implementation
│   │   ├── living_substrate.py    # World model + SSM + MoE + homeostasis
│   │   ├── cognitive_architecture.py  # Predictive hierarchy + attention
│   │   ├── heartbeat.py           # 15-min scan cycle across all domains
│   │   └── ignition_daemon.py     # Proactive push from internal state
│   │
│   ├── Intelligence
│   │   ├── llm.py                 # Ollama routing (reasoning vs coding)
│   │   ├── context_engine.py      # Real-time context assembly
│   │   ├── intelligence_hub.py    # Cross-source intelligence fusion
│   │   ├── memory.py              # ChromaDB vector memory
│   │   ├── memory_architect.py    # Infinite memory with consolidation
│   │   └── knowledge_graph.py     # Semantic knowledge structure
│   │
│   ├── Companion
│   │   ├── agent.py               # Personality, chat flow, tone
│   │   ├── emotional.py           # Mood tracking + stress detection
│   │   ├── personality.py         # Configurable companion presets
│   │   └── conversation_flow.py   # Multi-turn conversation management
│   │
│   └── Safety
│       ├── constitution.py        # Ethical guardrails
│       ├── sentinel.py            # Always-on system watchdog
│       └── sandbox.py             # Code execution sandboxing
│
├── agents/               # Specialized domain agents
│   ├── emotional_agent.py         # Wellness check-ins + mood patterns
│   ├── fitness_agent.py           # Workout tracking + suggestions
│   ├── learning_agent.py          # Skill tracking + learning plans
│   ├── task_agent.py              # Task management + prioritization
│   └── file_explorer.py           # Codebase analysis
│
├── tools/                # Proactive tools (not just reactive)
│   ├── guardian.py                # Work-life balance enforcement
│   ├── finance.py                 # Portfolio + market signals
│   └── bio_query.py               # Biometric data queries
│
├── integrations/         # External service bridges
│   ├── google_services.py         # Calendar, Gmail, Drive
│   ├── microsoft_bridge.py        # Outlook, Teams, OneDrive
│   ├── github_monitor.py          # Notifications, PR activity
│   ├── finance_intelligence.py    # Crypto/stock prices + alerts
│   ├── phone_bridge.py            # Mobile sync
│   └── browser_monitor.py         # Tab/activity awareness
│
├── api/                  # FastAPI backend — 443 endpoints
│   ├── main.py                    # 327 routes (5,500+ lines)
│   ├── neural_routes.py           # 107 neural mesh routes
│   └── evolution_routes.py        # 9 evolution dashboard routes
│
└── ui/                   # React frontend — 23 panels
    └── src/components/
        ├── Dashboard.jsx            # System overview + AGI activity
        ├── MindPanel.jsx            # 🧠 Real-time AGI thought stream + activity log
        ├── LifeDomains.jsx          # Body tracking (4 domains)
        ├── WaveEngine.jsx           # Self-evolution status
        ├── RitualView.jsx           # Morning/evening rituals
        ├── FocusMode.jsx            # Deep work timer
        ├── EmotionalPanel.jsx       # Mood + stress tracking
        ├── BriefingPanel.jsx        # Daily AI briefing
        ├── GuardianWidget.jsx       # Work limit sidebar
        ├── NeuralMesh.jsx           # Neural bus visualization
        ├── EvolutionPanel.jsx       # Evolution system dashboard
        ├── SentinelPanel.jsx        # System health monitor
        ├── SupervisorPanel.jsx      # Autonomy supervisor control
        ├── IntegrationsPanel.jsx    # Google/Microsoft/GitHub status
        ├── AgentLoopPanel.jsx       # Agent execution viewer
        ├── SettingsManager.jsx      # ⚙️ Unified settings + device management
        ├── IntelligenceDashboard.jsx # Intelligence hub
        ├── ContextPanel.jsx         # Real-time context
        ├── TerminalPanel.jsx        # In-browser terminal
        ├── SetupWizard.jsx          # Credential setup
        ├── HomeostasisPanel.jsx     # Living substrate vitals
        ├── VoiceInterface.jsx       # Voice I/O
        └── ErrorBoundary.jsx        # Error isolation
```

---

## Key Features

### Life Domains (Wave 22)
Track hydration, sleep, nutrition, and skincare with streaks, adaptive goals, and proactive nudges.

```
GET  /life/dashboard          # Full today snapshot + life score + nudges
POST /life/hydration/log      # Log water intake
POST /life/sleep/log          # Log last night's sleep
POST /life/nutrition/log      # Log a meal
POST /life/skincare/routine   # Log skincare routine
GET  /life/insights           # 7-day trends across all domains
GET  /life/streaks            # Current streaks
```

### Cross-Domain Intelligence (Wave 24)
Detects patterns the user can't see: poor sleep after low hydration days, compound deficits, streak momentum.

```
GET  /life/correlations       # Sleep vs focus, hydration vs stress, etc.
GET  /life/report             # Full life report with insights
```

### Proactive Life Coach (Wave 25)
Time-aware nudges — breakfast reminder at 8am, bedtime at 10pm. Adapts goals to your 7-day average. Respects focus mode.

```
GET  /life/coach/nudges       # What LOVE should say right now
GET  /life/coach/goals        # Adaptive daily goals
```

### AGI Intelligence & Action (Wave 27)
LOVE doesn't just monitor — it thinks, plans, and acts. A 5-phase intelligence tick runs every 5 minutes:
1. **Special systems** — restarts failed daemons (heartbeat, self-improvement, goal engine, wave engine)
2. **Lifecycle scan** — full module health check with auto-heal
3. **Self-diagnostics** — runs improvement daemon diagnostics
4. **Mission queue** — processes blocked missions
5. **Intelligence loop** — gathers context, triggers real actions:
   - **Self-build** — auto-assigns Ghost Dev to blocked missions
   - **Goal execution** — deep work on active goals (research, plan, execute, monitor)
   - **Proactive research** — queues web research on failed modules
   - **Proactive insights** — pushes contextual alerts to user
   - **Wave execution** — auto-builds proposed waves via Ghost Dev

All actions are logged to a centralized **Activity Log** — fully observable.

```
POST /agi/autonomy-supervisor/tick           # Run one tick
POST /agi/autonomy-supervisor/intelligence   # Force-run intelligence loop
GET  /agi/autonomy-supervisor/status          # Supervisor status
GET  /agi/activity                            # Recent activity log
GET  /agi/activity/stats                      # Activity statistics
GET  /agi/activity/daily-report               # Today's action summary
```

### Mind Panel — Watch LOVE Think
Real-time dashboard showing LOVE's internal monologue, autonomous actions, system health, and a **🧠 Run AGI** button to force intelligence immediately.

Navigate to the **🧠 Mind** tab in the UI to see:
- Activity stats bar (actions today, per-component, trend)
- Activity log feed (everything LOVE does, color-coded by importance)
- Internal monologue stream (consciousness thoughts)
- Intelligence actions (ghost dev, research, goals, waves)
- System health (self-improvement daemon, wave engine, AGI goals, supervisor)
- Ghost Developer tasks, research queue, missions

### Wave Evolution Engine (Wave 23)
LOVE detects its own capability gaps and proposes what to build next.

```
POST /wave/scan               # Run gap scan + propose next Wave
GET  /wave/status             # Engine status
GET  /wave/gaps               # Current detected gaps
GET  /wave/all                # All Wave proposals
```

### Work-Life Guardian
Tracks hours, enforces limits, suggests recovery. Proactive — warns before you hit the wall.

```
GET  /guardian/work-status    # Current hours + limit + overflow
GET  /guardian/check-in       # Morning work assessment
POST /guardian/hard-stop      # Force stop with auto-save
```

### Daily Briefing
LLM-generated morning brief from all connected sources — calendar, email, finance, body status, goals.

```
GET  /neural/briefing/today   # Today's AI-written brief
POST /neural/briefing/generate # Force regenerate
```

### Settings & Ecosystem Management
Centralized preference editing with live persistence to `settings.yaml`. Manage user profile, companion personality, work limits, finance watchlists, AI models, voice, evolution, and privacy — all in one place.

Device ecosystem management: register phones, tablets, workstations, and edge devices. Real-time presence detection shows which device you're actively using. Health monitoring tracks battery, CPU, and connectivity per device.

```
GET  /settings                 # Full settings from settings.yaml
PUT  /settings                 # Update any section
POST /settings/reload          # Reload from disk
GET  /ecosystem/status         # Full ecosystem overview
GET  /ecosystem/devices        # All registered devices
GET  /ecosystem/devices/health # Device health check
POST /ecosystem/devices/register # Add new device
POST /ecosystem/devices/heartbeat # Keep device online
GET  /ecosystem/presence       # User presence detection
```

### Companion Chat
Memory-aware, personality-driven conversation with reasoning transparency.

```
POST /chat                    # Main chat (streaming supported)
GET  /modes                   # Available personality modes
```

### Full API Reference

460+ endpoints across 44 prefixes. Key groups:

| Prefix | Endpoints | Purpose |
|--------|-----------|---------|
| `/agi` | 55 | AGI substrate (supervisor, goals, research, ghost dev, activity log) |
| `/neural` | 107 | Neural mesh (bus, memory, cognition, evolution, integrations) |
| `/settings` | 3 | Centralized preference management (read, write, reload) |
| `/ecosystem` | 6 | Multi-device ecosystem (register, heartbeat, health, presence) |
| `/life` | 20+ | Life domains, coaching, correlations |
| `/love` | 23 | Core companion features |
| `/integrations` | 15 | Google, Microsoft, GitHub, finance |
| `/system` | 13 | System control + monitoring |
| `/evolution` | 20 | Self-improvement + evolution dashboard |
| `/guardian` | 7 | Work-life balance |
| `/finance` | 7 | Portfolio + market signals |
| `/wave` | 6 | Autonomous Wave evolution |
| `/voice` | 6 | Speech I/O |
| `/memory` | 7 | Vector memory + recall |

---

## Configuration

### Environment Variables

Control LOVE's autonomous behavior with these environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LOVE_SUPERVISOR_INTERVAL_SEC` | 300 | Supervisor tick interval in seconds (5 min) |
| `LOVE_INTELLIGENCE_TICKS` | 2 | Run intelligence loop every N ticks |
| `LOVE_DAEMON_INTERVAL_MIN` | 10 | Self-improvement daemon interval (minutes) |
| `LOVE_GOAL_INTERVAL_SEC` | 600 | Goal engine cycle interval (seconds) |
| `LOVE_WAVE_INTERVAL_H` | 4 | Wave engine cycle interval (hours) |
| `LOVE_SELF_WORK_ON_TICK` | true | Enable self-diagnostics on each tick |
| `LOVE_RESEARCH_INTERVAL_MIN` | 10 | Research engine cycle interval (minutes) |

### settings.yaml

```yaml
user:
  name: "Karthi"
  timezone: "Asia/Kolkata"

work:
  daily_limit_hours: 8
  warning_threshold: 0.8
  hard_stop_enabled: true
  dev_folders:
    - "C:/Users/you/Projects"

models:
  reasoning: "deepseek-r1:7b"
  coding: "qwen2.5-coder:7b"
  embedding: "nomic-embed-text"
  base_url: "http://localhost:11434"

finance:
  watchlist: ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
  risk_profile: "moderate"
```

---

## Wave History

| Wave | What Landed |
|------|-------------|
| 1-8 | Core companion, memory, finance, sync, voice, self-healing, ghost dev |
| 9-11 | Context engine, intelligence hub, awareness |
| 12-14 | Agent loop, integrations (Google, Microsoft, GitHub) |
| 15 | Daily briefing, credential setup wizard |
| 16 | Neural mesh, living substrate, consciousness |
| 17 | Evolution dashboard, sentinel watchdog |
| 18 | Error boundaries, UI hardening |
| 19-21 | Self-modification pipeline, BPTT, LoRA scaffold, user-aligned fitness |
| **22** | **Life Domains engine (hydration, sleep, nutrition, skincare)** |
| **23** | **Autonomous Wave Evolution engine (gap scan + proposal)** |
| **24** | **Cross-domain intelligence (pattern correlation)** |
| **25** | **Proactive Life Coach (time-aware nudges, adaptive goals)** |
| **26** | **Ritual integration + push notifications via Life Coach** |
| **27** | **AGI Intelligence & Action (5-phase tick, activity log, MindPanel, self-improvement daemon learns from its own behavior)** |

---

## Safety & Privacy

- **100% local** — all data in `data/` on your machine, never uploaded
- **No telemetry** — zero tracking, zero phone-home
- **Constitutional guardrails** — ethical constraints baked into the core
- **Sentinel watchdog** — continuous system health monitoring
- **A/B revert** — self-modifications auto-revert if quality degrades
- **Open source** — audit every line

---

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + Uvicorn
- **Frontend**: React + Vite
- **LLM**: Ollama (deepseek-r1:7b, qwen2.5-coder:7b)
- **Memory**: ChromaDB (vector) + JSON (structured)
- **Integrations**: Google APIs, Microsoft Graph, GitHub API

---

> *"The goal isn't to build a better chatbot. It's to build something that genuinely gives a damn about how your day goes."*
