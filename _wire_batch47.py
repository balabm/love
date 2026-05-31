import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"rejection_resilience_coach"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"storytelling_coach": {"available": True},\n',
            indent + '"voice_finder": {"available": True},\n',
            indent + '"transition_companion": {"available": True},\n',
            indent + '"uncertainty_embracer": {"available": True},\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired api/evolution_routes.py")

# 2. core/daily_briefing.py
p = os.path.join(BASE, "core", "daily_briefing.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"rejection_resilience_coach"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "storytelling_coach", "voice_finder",\n',
            '                "transition_companion", "uncertainty_embracer",\n',
        ]
        lines = lines[:j] + new_lines + lines[j:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired core/daily_briefing.py")

# 3. core/heartbeat.py
p = os.path.join(BASE, "core", "heartbeat.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '("rejection_resilience_coach"' in line:
        indent = '                '
        new_lines = [
            indent + '("storytelling_coach", "Storytelling Coach"),\n',
            indent + '("voice_finder", "Voice Finder"),\n',
            indent + '("transition_companion", "Transition Companion"),\n',
            indent + '("uncertainty_embracer", "Uncertainty Embracer"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired core/heartbeat.py")

# 4. start_evolution.py
p = os.path.join(BASE, "start_evolution.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '("Rejection Resilience Coach"' in line:
        indent = '        '
        new_lines = [
            indent + '("Storytelling Coach", "core.storytelling_coach", "get_storytelling_coach"),\n',
            indent + '("Voice Finder", "core.voice_finder", "get_voice_finder"),\n',
            indent + '("Transition Companion", "core.transition_companion", "get_transition_companion"),\n',
            indent + '("Uncertainty Embracer", "core.uncertainty_embracer", "get_uncertainty_embracer"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
