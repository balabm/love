#!/usr/bin/env python3
"""Verify configuration files are valid."""

import yaml
import json
from pathlib import Path

print("\n" + "="*60)
print("  LOVE Configuration Verification")
print("="*60 + "\n")

# Check settings.yaml
try:
    with open('settings.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("✓ settings.yaml is valid YAML")
    print(f"  User: {config.get('user', {}).get('name', 'N/A')}")
    print(f"  Timezone: {config.get('user', {}).get('timezone', 'N/A')}")
    print(f"  Companion name: {config.get('companion', {}).get('name', 'N/A')}")
    print(f"  Personality: {config.get('companion', {}).get('personality_preset', 'N/A')}")
    print(f"  Work daily limit: {config.get('work', {}).get('daily_limit_hours', 'N/A')} hours")
except Exception as e:
    print(f"✗ Error loading settings.yaml: {e}")

print()

# Check data directory
data_dir = Path('data')
if data_dir.exists():
    files = list(data_dir.glob('*.json'))
    print(f"✓ Data directory exists with {len(files)} files")
else:
    print("! Data directory not found - will be created on first run")

print()

# Check logs directory
logs_dir = Path('logs')
if logs_dir.exists():
    print(f"✓ Logs directory exists")
else:
    print("! Logs directory not found")

print()

# Check core modules
print("Checking core module imports...")
try:
    from core.agent import Agent
    print("✓ core.agent module loads")
except Exception as e:
    print(f"✗ core.agent error: {e}")

try:
    from core.awareness import Awareness
    print("✓ core.awareness module loads")
except Exception as e:
    print(f"✗ core.awareness error: {e}")

print("\n" + "="*60)
print("  Initialization Complete!")
print("="*60 + "\n")
print("Next steps:")
print("1. Start the API server: python -m api.main")
print("2. Or use uvicorn: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
print()
