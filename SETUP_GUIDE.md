# LOVE Setup Guide

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.12+
- 8GB+ RAM recommended
- Ollama (for local LLM)

### Installation

1. **Clone and Install**
```bash
cd love
pip install -r requirements.txt
```

2. **Start Ollama** (if using local LLM)
```bash
ollama serve
```

3. **Run LOVE**
```bash
python -m api.main
```

4. **Access the UI**
- Open browser: `http://localhost:8000`
- Mobile app: Set server URL to your IP address

## Common Issues & Solutions

### Issue: "Nothing happening after startup"
**Solution:** The system is running in background mode. LOVE is:
- Monitoring your system resources
- Scanning for triggers every 15 minutes
- Running background intelligence tasks
- Waiting for user interaction

**To see activity:**
- Open the web UI at `http://localhost:8000`
- Check the "Internal Monologue" section for LOVE's thoughts
- Look at "Swarm Agents" for active processes
- Monitor "Active Monitoring" for system state

### Issue: High RAM usage (86%+)
**Solution:** LOVE is resource-intensive. To reduce usage:
1. Close unnecessary applications
2. Use smaller LLM models (qwen2.5:0.5b instead of larger ones)
3. Disable non-essential modules in `api/main.py`

### Issue: LLM errors (404, 500)
**Solution:** Ollama model not available or wrong endpoint:
```bash
# Check available models
ollama list

# Pull a small model if needed
ollama pull qwen2.5:0.5b
```

### Issue: Module failures at startup
**Solution:** Some modules may fail due to missing dependencies. This is normal. LOVE will continue with available modules.

## UI Guide

### Main Dashboard
- **Left Panel**: Consciousness state, live context, connected devices
- **Center Panel**: Internal monologue, chat interface
- **Right Panel**: Swarm agents, active monitoring, learning insights

### Key Features
1. **Chat Interface**: Talk to LOVE directly
2. **Quick Commands**: One-click actions (Status, Research, Memory, Vision, Focus)
3. **Real-time Updates**: WebSocket connection shows live system state
4. **Monitoring Panels**: See cognitive load, learning progress, system health

### Voice Input
- Click microphone button and speak
- Requires working microphone
- Uses Web Speech API

## Advanced Setup

### Mobile Integration
1. Install LOVE mobile app
2. Set server URL to your computer's IP
3. Enable cross-device sync in settings

### Google Services Integration
1. Create Google Cloud project
2. Enable Calendar and Gmail APIs
3. Download credentials JSON
4. Place in project root as `gcred.json`

### Custom Configuration
Edit `core/settings.py` to customize:
- Work hours limits
- Notification preferences
- Module intervals
- LLM model selection

## Troubleshooting

### Check Logs
```bash
# View main system log
tail -f logs/love_system.log

# View error log
tail -f logs/love_errors.log
```

### Restart LOVE
```bash
# Stop the server (Ctrl+C)
# Then restart
python -m api.main
```

### Reset LOVE State
```bash
# Clear data directory (WARNING: deletes all learning)
rm -rf data/*
```

## Getting Help

- Check logs in `logs/` directory
- Review startup report for module status
- Check system resources (RAM/CPU)
- Ensure Ollama is running if using local LLM

## Next Steps

1. **Explore the UI** - Try the quick commands
2. **Chat with LOVE** - Ask questions, give commands
3. **Set up integrations** - Google services, mobile app
4. **Customize settings** - Adjust work limits, notifications
5. **Monitor learning** - Watch LOVE's adaptation over time

LOVE learns from your interactions. The more you use it, the better it becomes at understanding your needs and preferences.
