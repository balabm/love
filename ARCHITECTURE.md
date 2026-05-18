# LOVE - End-to-End Architecture

## System Overview

LOVE (Life Orchestrator & Virtual Entity) is an autonomous life companion evolving from a reactive chatbot into a full AGI-level system. It operates as a distributed multi-device ecosystem with proactive intelligence, predictive capabilities, and autonomous decision-making.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOVE ECOSYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│  │  Home PC     │      │  Phone       │      │  Office PC   │              │
│  │  (Server)    │◄────►│  (Companion) │◄────►│  (Agent)     │              │
│  │  Port 8000   │      │  Expo App    │      │  Node.js     │              │
│  └──────────────┘      └──────────────┘      └──────────────┘              │
│         │                      │                      │                    │
│         └──────────────────────┴──────────────────────┘                    │
│                                Tailscale / Direct                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (Python)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         API Layer (FastAPI)                             │ │
│  │  • REST endpoints for all subsystems                                    │ │
│  • WebSocket support for real-time updates                                │
│  • Lifespan event handlers for startup/shutdown                            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Core Intelligence Layer                           │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  AGI-Level Systems (10 modules)                                        │ │
│  │  ✓ Autonomous Agent - Goal generation, planning, execution             │ │
│  │  ✓ Psychological Model - Personality, emotional modeling               │ │
│  │  ✓ Predictive Intelligence - Pattern recognition, needs anticipation    │ │
│  │  ✓ Self-Improvement - Meta-cognition, self-evolution                  │ │
│  │  ✓ Strategic Planning - Long-term goal planning                         │ │
│  │  ✓ Autonomous Actions - Safety checks, approval flow                  │ │
│  │  ✓ World Model - Knowledge representation                              │ │
│  │  ✓ Meta-Cognition - Self-awareness, reflection                        │ │
│  │  ✓ Cross-Domain Reasoning - Holistic insights                          │ │
│  │  ✓ Continuous Learning - Experience integration                        │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  Core Systems                                                           │ │
│  │  ✓ Agent - Main chat interface, LLM integration                        │ │
│  │  ✓ Context Engine - Master fusion of all context sources               │ │
│  │  ✓ Heartbeat - Proactive background scanning                           │ │
│  │  ✓ Memory - ChromaDB vector storage                                    │ │
│  │  ✓ Emotional Intelligence - Emotional tracking                        │ │
│  │  ✓ Executive - Task management, briefings                              │ │
│  │  ✓ Idle Mind - Autonomous exploration                                  │ │
│  │  ✓ Dream Engine - Deep insight generation                              │ │
│  │  ✓ Self-Healing - Error detection and auto-fix                          │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  Jarvis-Level Awareness                                                │ │
│  │  ✓ Awareness - Real-time system monitoring (CPU, RAM, battery, windows) │ │
│  │  ✓ Vision - Desktop screenshot analysis                                 │ │
│  │  ✓ Voice - STT/TTS, wake word detection                                │ │
│  │  ✓ System Control - PC automation (open, type, media, lock)            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Integration Layer                                 │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  ✓ Google Services - Calendar, Gmail, Drive (OAuth2)                  │ │
│  │  ✓ Phone Bridge - KDE Connect, iOS Shortcuts                           │ │
│  │  ✓ Microsoft Bridge - Teams, Outlook, OneDrive (device-code OAuth)    │ │
│  │  ✓ Doc Analyst - Dev folder monitoring, TODO extraction                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      Data Layer                                         │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │  ✓ ChromaDB - Vector embeddings for memory                             │ │
│  │  ✓ JSON Files - Goals, devices, profile, logs                          │ │
│  │  ✓ SQLite - Consolidated memory (optional)                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ Sidebar with ContextPanel (NOW, CONNECTED, DOCS tabs)                   │
│  ✓ Chat interface with mode selection (Talk, Focus, Vent, Plan, Code)       │
│  ✓ Dashboard with lifescore, relationships, tasks                           │
│  ✓ Settings panel for integrations                                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MOBILE COMPANION (React Native)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  Tabs: Chat, Now, Life, Alerts, Calendar, People, Tasks, Emotions,         │
│        Devices, Setup, AGI                                                  │
│  ✓ AGI Panel - Goals, Predictions, Approvals, Meta, Holistic                │
│  ✓ Background sync with heartbeat                                           │
│  ✓ Voice recording and transcription                                        │
│  ✓ Quick actions for PC control                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           OFFICE AGENT (Node.js)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  ✓ Polls LOVE backend for orchestrator interventions                        │
│  ✓ Pushes Teams/Outlook notifications                                       │
│  ✓ Sends device heartbeat                                                  │
│  ✓ Auto-start via Windows Task Scheduler                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Status

### Backend (Python) - ✅ OPERATIONAL

**Core Intelligence**
- ✅ Agent (core/agent.py) - Chat interface with LLM integration, AGI context injection
- ✅ Context Engine (core/context_engine.py) - Master fusion of all context sources
- ✅ Heartbeat (core/heartbeat.py) - Proactive scanning with AGI system integration
- ✅ Memory (core/memory.py) - ChromaDB vector storage with collections

**AGI-Level Systems (10/10 Complete)**
- ✅ Autonomous Agent (core/autonomous_agent.py) - LLM-based goal generation, planning
- ✅ Psychological Model (core/psychological_model.py) - Personality, emotional modeling
- ✅ Predictive Intelligence (core/predictive_intelligence.py) - Pattern recognition, needs anticipation
- ✅ Self-Improvement (core/self_improvement.py) - Meta-cognition, self-evolution
- ✅ Strategic Planning (core/strategic_planning.py) - Long-term goal planning
- ✅ Autonomous Actions (core/autonomous_actions.py) - Safety checks, approval flow
- ✅ World Model (core/world_model.py) - Knowledge representation
- ✅ Meta-Cognition (core/meta_cognition.py) - Self-awareness, reflection, self-improvement suggestions
- ✅ Cross-Domain Reasoning (core/cross_domain_reasoning.py) - Holistic insights
- ✅ Continuous Learning (core/continuous_learning.py) - Experience integration

**Core Systems**
- ✅ Emotional Intelligence (core/emotional.py) - Emotional tracking
- ✅ Executive (core/executive.py) - Task management, briefings
- ✅ Idle Mind (core/idle_mind.py) - Autonomous exploration
- ✅ Dream Engine (core/dream_engine.py) - Deep insight generation
- ✅ Self-Healing (core/self_healing.py) - Error detection and auto-fix

**Jarvis-Level Awareness**
- ✅ Awareness (core/awareness.py) - Real-time system monitoring (CPU, RAM, battery, windows)
- ✅ Vision (core/vision.py) - Desktop screenshot analysis
- ✅ Voice (voice/stt.py, voice/tts.py) - STT/TTS, wake word detection
- ✅ System Control (core/system_control.py) - PC automation

**Integrations**
- ✅ Google Services (integrations/google_services.py) - Calendar, Gmail, Drive
- ✅ Phone Bridge (integrations/phone_bridge.py) - KDE Connect, iOS Shortcuts
- ✅ Microsoft Bridge (integrations/microsoft_bridge.py) - Teams, Outlook, OneDrive
- ✅ Doc Analyst (core/doc_analyst.py) - Dev folder monitoring

**API Layer**
- ✅ FastAPI (api/main.py) - REST endpoints, lifespan event handlers (deprecation fixed)
- ✅ 50+ endpoints covering all subsystems
- ✅ AGI endpoints: /agi/autonomous/*, /agi/predictive/*, /agi/actions/*, /agi/meta-cognition/*, /agi/cross-domain/*

**Data Layer**
- ✅ ChromaDB - Vector embeddings for memory
- ✅ JSON storage - Goals, devices, profile, logs
- ✅ Config (config.yaml) - Settings management

---

### Frontend (React) - ✅ OPERATIONAL

- ✅ Sidebar with ContextPanel (NOW, CONNECTED, DOCS tabs)
- ✅ Chat interface with mode selection
- ✅ Dashboard with lifescore, relationships, tasks
- ✅ Settings panel for integrations

---

### Mobile Companion (React Native) - ✅ ENHANCED WITH AGI

**Tabs (11/11)**
- ✅ Chat (index.jsx) - Main chat interface
- ✅ Now (context.jsx) - Live context
- ✅ Life (dashboard.jsx) - Lifescore dashboard
- ✅ Alerts (notifications.jsx) - Proactive notifications
- ✅ Calendar (calendar.jsx) - Google Calendar
- ✅ People (relationships.jsx) - Relationship tracking
- ✅ Tasks (tasks.jsx) - Task management
- ✅ Emotions (emotions.jsx) - Emotional state
- ✅ Devices (devices.jsx) - Device management
- ✅ Setup (settings.jsx) - Configuration
- ✅ AGI (agi.jsx) - NEW: AGI-level insights and control

**AGI Panel Features**
- ✅ Autonomous Goals - View and generate autonomous goals
- ✅ Predictions - View predictions and anticipate needs
- ✅ Approvals - Approve/reject autonomous actions
- ✅ Meta - Meta-cognitive summary and self-improvement suggestions
- ✅ Holistic - Cross-domain holistic view

**Services**
- ✅ API integration (services/api.js) - All AGI endpoints added
- ✅ Background sync (services/sync.js) - Heartbeat every 60s

---

### Office Agent (Node.js) - ✅ OPERATIONAL

- ✅ Polls LOVE backend for orchestrator interventions
- ✅ Pushes Teams/Outlook notifications
- ✅ Sends device heartbeat
- ✅ Auto-start via Windows Task Scheduler

---

## API Endpoints Summary

### Core Endpoints
- `POST /chat` - Main chat interface
- `GET /context/summary` - Live context summary
- `POST /devices/heartbeat` - Device heartbeat
- `POST /devices/chat` - Chat from device
- `GET /devices` - Device registry

### AGI-Level Endpoints
- `GET /agi/autonomous/goals` - Get autonomous goals
- `POST /agi/autonomous/generate-goals` - Generate autonomous goals
- `GET /agi/predictive/predictions` - Get predictions
- `POST /agi/predictive/anticipate-needs` - Anticipate needs
- `GET /agi/actions/approvals/pending` - Get pending approvals
- `POST /agi/actions/approve` - Approve action
- `POST /agi/actions/reject` - Reject action
- `GET /agi/meta-cognition/summary` - Meta-cognitive summary
- `GET /agi/meta-cognition/improvement-suggestions` - Self-improvement suggestions
- `GET /agi/cross-domain/holistic` - Holistic view

### Integration Endpoints
- `GET /integrations/google/status` - Google services status
- `POST /integrations/google/auth` - Google OAuth
- `GET /integrations/google/calendar/insights` - Calendar insights
- `GET /integrations/phone/status` - Phone bridge status
- `POST /integrations/phone/update` - Phone update webhook
- `GET /integrations/microsoft/status` - Microsoft status
- `POST /integrations/microsoft/auth` - Microsoft OAuth

### System Endpoints
- `GET /awareness` - System awareness
- `POST /system/open` - Open application
- `POST /system/screenshot` - Take screenshot
- `POST /voice/speak` - Text-to-speech
- `POST /voice/loop/start` - Start voice loop
- `POST /voice/loop/stop` - Stop voice loop

---

## Data Flow

### Chat Flow
1. User sends message (Web/Mobile/Device)
2. API receives request with device_id
3. Agent constructs prompt with:
   - User message
   - AGI context block (psychological, predictive, strategic, meta-cognitive, cross-domain)
   - Live context (awareness, calendar, tasks, etc.)
4. LLM generates response
5. Response returned to client
6. Memory stores conversation turn

### Proactive Flow
1. Heartbeat runs every 15 minutes
2. Scans all domains (finance, learning, guardian, wellness, fitness, tasks, memory, dream, context, AGI)
3. Generates triggers based on conditions
4. Notifies via TTS, PWA push, or mobile notification
5. AGI systems generate autonomous goals, predictions, and improvement suggestions

### Autonomous Action Flow
1. Autonomous agent proposes action
2. Safety checks assess risk level
3. SAFE/LOW actions auto-execute
4. MEDIUM/HIGH/CRITICAL actions require approval
5. Pending actions shown in AGI panel
6. User approves/rejects via companion app
7. Action executes or is rejected

---

## Deployment Status

### Home PC (Server)
- ✅ LOVE server running on port 8000
- ✅ All AGI modules operational
- ✅ ChromaDB storage active
- ✅ Background heartbeat running
- ✅ Tailscale for remote access

### Mobile Devices
- ✅ OnePlus phone - love-companion app
- ✅ OnePlus Tab - love-companion app
- ✅ Background sync active
- ✅ AGI panel integrated

### Office Laptop
- ✅ love-agent Node.js script
- ✅ Auto-start via Task Scheduler
- Microsoft integration active

---

## Recent Enhancements (May 2026)

1. **AGI-Level Systems Integration** - All 10 AGI modules integrated into chat context
2. **LLM-Based Goal Generation** - Autonomous goals generated with LLM reasoning
3. **Predictive Intelligence Enhancement** - Pattern recognition with LLM-based needs anticipation
4. **Autonomous Action Approval Flow** - Safety checks with user approval workflow
5. **Cross-Domain Reasoning** - Holistic insights integrated into responses
6. **Proactive Notifications** - Heartbeat-based AGI notifications
7. **Meta-Cognition Self-Improvement** - LLM-based self-improvement suggestions
8. **Mobile AGI Panel** - Full AGI visibility and control from companion app
9. **FastAPI Deprecation Fix** - Modern lifespan event handlers implemented

---

## Configuration

### Environment Variables (.env)
```
REASONING_MODEL=deepseek-r1:7b
CODING_MODEL=qwen2.5-coder:7b
MICROSOFT_CLIENT_ID=<Azure AD Client ID>
```

### Config (config.yaml)
- Awareness settings
- Google integration
- Phone bridge
- Doc analyst
- Work folders

---

## Dependencies

### Backend (Python)
- fastapi, uvicorn
- chromadb
- psutil
- pyyaml
- openai-whisper
- langchain-ollama

### Frontend (React)
- React 18
- Lucide icons
- TailwindCSS

### Mobile (React Native)
- Expo SDK 55
- expo-haptics
- expo-clipboard
- expo-av
- @react-native-async-storage/async-storage

### Office Agent (Node.js)
- @microsoft/microsoft-graph-client
- node-cron

---

## Status Summary

**Overall System Status: ✅ FULLY OPERATIONAL**

- Backend: ✅ All 10 AGI systems integrated and operational
- Frontend: ✅ Web UI functional
- Mobile: ✅ Companion app with AGI panel
- Office Agent: ✅ Running with Microsoft integration
- API: ✅ 50+ endpoints operational
- Data: ✅ ChromaDB storage active
- Integrations: ✅ Google, Phone, Microsoft bridges active

LOVE is now a fully operational AGI-level life companion with autonomous decision-making, predictive intelligence, and multi-device synchronization.
