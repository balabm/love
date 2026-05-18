"""
Project LOVE Setup Script
Helps new users configure their Autonomous Life OS.
"""

import os
import sys
import json
from pathlib import Path


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def setup():
    print_header("Project LOVE - Setup")
    
    # Check if settings.yaml exists
    settings_path = Path("settings.yaml")
    if settings_path.exists():
        print("settings.yaml already exists. Skipping setup.")
        return
    
    # Copy config template
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("ERROR: config.yaml template not found.")
        sys.exit(1)
    
    # Get user input
    print("Welcome to Project LOVE — your Autonomous Life OS.\n")
    print("Let's set up your personal configuration.\n")
    
    name = input("Your name (default: User): ").strip() or "User"
    
    print("\nChoose your companion's personality:")
    print("  1. companion - Sharp, caring best friend (default)")
    print("  2. assistant - Professional and efficient")
    print("  3. coach - Accountability partner, pushes you")
    print("  4. mentor - Wise guide, asks questions")
    
    personality_choice = input("\nSelect (1-4) [1]: ").strip() or "1"
    presets = {"1": "companion", "2": "assistant", "3": "coach", "4": "mentor"}
    personality = presets.get(personality_choice, "companion")
    
    work_hours = input("\nDaily work limit in hours (default: 8): ").strip() or "8"
    
    print("\nProject paths (press Enter to skip):")
    work_project = input("Main work project path: ").strip()
    
    # Read template and customize
    with open(config_path, 'r', encoding='utf-8') as f:
        config = f.read()
    
    # Replace defaults
    config = config.replace('name: "User"', f'name: "{name}"')
    config = config.replace('personality_preset: "companion"', f'personality_preset: "{personality}"')
    config = config.replace('daily_limit_hours: 9', f'daily_limit_hours: {work_hours}')
    
    if work_project:
        config = config.replace('work_project: ""', f'work_project: "{work_project}"')
    
    # Write settings
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(config)
    
    print(f"\n✓ settings.yaml created for {name}")
    print(f"✓ Personality: {personality}")
    print(f"✓ Work limit: {work_hours} hours")
    
    print("\nNext steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Start Ollama with your models")
    print("  3. Run: python -m api.main")
    print(f"\nEdit settings.yaml anytime to customize further.\n")


if __name__ == "__main__":
    setup()
