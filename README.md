# Project LOVE — Autonomous Life OS

> *"An AI companion that lives in your terminal, knows your goals, and actively works to make them happen."*

Project LOVE is an open-source, local-first Autonomous Life OS. It runs entirely on your machine, remembers everything, manages your work-life balance, helps with code, tracks your finances, and speaks to you like a real companion — not a chatbot.

## Philosophy

- **Local-first**: All your data stays on your machine. No cloud. No subscriptions.
- **Proactive, not reactive**: LOVE doesn't wait for prompts. It checks on you, suggests actions, enforces limits.
- **Companion, not assistant**: It has opinions, calls you out, celebrates wins, and genuinely knows you.
- **Self-improving**: It heals its own crashes, optimizes its own code, and learns from every interaction.

## Features

| Pillar | What It Does |
|--------|-------------|
| **Companion Chat** | Contextual, memory-aware conversations with personality |
| **Work-Life Guardian** | Tracks hours, enforces work limits, prevents burnout |
| **Finance Sentinel** | Portfolio tracking, market signals, predictive trade advice |
| **Neural Sync** | Multi-device memory and personality synchronization |
| **Self-Healing** | Auto-detects crashes, analyzes root cause, applies fixes |
| **Continuous Improvement** | Weekly self-refactoring for better performance |
| **Ghost Developer** | Auto-generates tests and architecture boilerplate |
| **Environment Intelligence** | Hardware-aware power profiles and launch sequences |
| **Alpha Sentinel** | News sentiment analysis correlated with portfolio |
| **Hard Stop Enforcer** | Physical work limit enforcement with auto-save |
| **Voice Interface** | Wake word detection, speech-to-text, text-to-speech |

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) running locally (or compatible API)
- Windows 10+/macOS/Linux
- Git (optional, for auto-commit features)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/project-love.git
cd project-love

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure your settings
cp config.yaml settings.yaml
# Edit settings.yaml with your name, work hours, and preferences
```

### Configure

Edit `settings.yaml`:

```yaml
user:
  name: "Your Name"
  timezone: "UTC"

work:
  daily_limit_hours: 8
  dev_folders:
    - "C:/Users/You/Projects"

finance:
  watchlist:
    - "BTCUSDT"
    - "ETHUSDT"
  risk_profile: "moderate"

models:
  reasoning: "deepseek-r1:7b"
  coding: "qwen2.5-coder:7b"
```

### Run

```bash
# Start the API server
python -m api.main

# Or with uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Chat
- `POST /chat` — Main companion chat endpoint

### Guardian (Work-Life Balance)
- `GET /guardian/check-in` — Morning work summary
- `GET /guardian/work-status` — Current work hours and status
- `POST /guardian/hard-stop` — Enforce work limit (auto-save, lock)
- `GET /guardian/day-summary` — Today's work summary

### Ghost Developer
- `GET /ghost/suggestions` — Get code staging suggestions
- `GET /ghost/scan/{project_path}` — Scan project for missing tests/architecture

### Finance
- `GET /finance/signal/{symbol}` — AI trading signal
- `GET /finance/portfolio` — Portfolio overview
- `GET /finance/advice/{symbol}` — Predictive trade advice with sentiment
- `GET /finance/alpha-scan` — High-confidence opportunities

### Environment
- `GET /environment/hardware` — Hardware detection and power profile
- `POST /environment/launch-work` — Launch work sequence (IDE, backend, docs)

### Evolution (Self-Healing)
- `GET /evolution/crash-check` — Check for system errors
- `POST /evolution/propose-fix` — Propose fix for crash
- `GET /evolution/run-optimization` — Trigger code optimization

### Sync (Multi-Device)
- `POST /sync/register` — Register new device
- `POST /sync/heartbeat` — Device heartbeat
- `GET /sync/device-types` — Available device types

### Voice
- `GET /voice/status` — Voice system availability
- `POST /voice/speak` — Text-to-speech
- `GET /voice/listen` — Speech-to-text (5 second capture)

## Personality Presets

Choose your companion's personality in `settings.yaml`:

- **companion** (default): Sharp, caring best friend. Blunt, warm, real.
- **assistant**: Professional, efficient, helpful.
- **coach**: Accountability partner. Pushes you to be better.
- **mentor**: Wise guide. Asks questions, shares experience.

Or create a custom personality with `custom_traits`.

## Architecture

```
love/
├── core/
│   ├── agent.py          # Companion personality & chat flow
│   ├── llm.py            # Model routing (reasoning vs coding)
│   ├── memory.py         # ChromaDB vector memory
│   ├── sync.py           # Multi-device sync & hardware detection
│   ├── evolution.py      # Self-healing & self-optimization
│   └── settings.py       # Configuration management
├── tools/
│   ├── guardian.py       # Work-life balance & hard-stop
│   ├── finance.py        # Portfolio & market analysis
│   └── .gitkeep
├── voice/
│   ├── stt.py            # Speech-to-text (Whisper + Porcupine)
│   └── tts.py            # Text-to-speech (gTTS / pyttsx3)
├── api/
│   └── main.py           # FastAPI server (35+ endpoints)
├── data/
│   ├── memory/           # ChromaDB storage
│   ├── love_os.db        # SQLite sync database
│   └── user_profile.json # User preferences
├── config.yaml           # Default configuration template
└── settings.yaml         # Your personal settings (gitignored)
```

## Customization

### Power Profiles

Define hardware-specific behavior in `settings.yaml`:

```yaml
devices:
  power_profiles:
    desktop:
      llm_temperature: 0.4
      llm_max_tokens: 2048
      market_scan_interval: 5
      gpu_acceleration: true
    
    laptop:
      llm_temperature: 0.5
      llm_max_tokens: 1024
      market_scan_interval: 15
      use_quantized: true
```

### Work Limit

Set your daily limit and warning threshold:

```yaml
work:
  daily_limit_hours: 8
  warning_threshold: 0.8  # Warn at 80% (6.4 hours)
  hard_stop_enabled: true
```

### Models

Works with any Ollama-compatible model:

```yaml
models:
  reasoning: "llama3.1:8b"
  coding: "codellama:7b"
  embedding: "nomic-embed-text"
  base_url: "http://localhost:11434"
```

## Safety & Privacy

- **100% local**: All data stays on your machine
- **No telemetry**: We don't track usage
- **Open source**: Audit every line of code
- **Optional cloud**: Only if you explicitly enable sync
- **Model-agnostic**: Use your own local models

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas that need help
- Voice wake word training for custom names
- Wearable device integrations (smart glasses, watches)
- More finance exchange integrations
- Additional personality presets
- macOS/Linux hard-stop screen dimming
- Docker/container deployment

## Roadmap

- [x] Phase 1-6: Core companion, memory, finance, sync, voice
- [x] Phase 7-8: Self-healing, self-optimization, ghost developer
- [ ] Phase 9: Wearable integration, smart glasses
- [ ] Phase 10: Advanced reasoning chains, agent networks
- [ ] Phase 11: Distributed intelligence, swarm coordination

## License

MIT License — see [LICENSE](LICENSE)

## Acknowledgments

Built with ❤️ using:
- [LangChain](https://github.com/langchain-ai/langchain) for LLM orchestration
- [ChromaDB](https://github.com/chroma-core/chroma) for vector memory
- [FastAPI](https://github.com/tiangolo/fastapi) for the API layer
- [Ollama](https://ollama.ai/) for local LLM inference

---

> *"The goal isn't to build a better chatbot. It's to build something that genuinely cares about your life."*
