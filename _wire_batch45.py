import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"rest_designer"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"boundary_coach": {"available": True},\n',
            indent + '"emotional_literacy_trainer": {"available": True},\n',
            indent + '"hope_cultivator": {"available": True},\n',
            indent + '"attention_steward": {"available": True},\n',
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
    if '"rest_designer"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "boundary_coach", "emotional_literacy_trainer",\n',
            '                "hope_cultivator", "attention_steward",\n',
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
    if '("rest_designer"' in line:
        indent = '                '
        new_lines = [
            indent + '("boundary_coach", "Boundary Coach"),\n',
            indent + '("emotional_literacy_trainer", "Emotional Literacy Trainer"),\n',
            indent + '("hope_cultivator", "Hope Cultivator"),\n',
            indent + '("attention_steward", "Attention Steward"),\n',
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
    if '("Rest Designer"' in line:
        indent = '        '
        new_lines = [
            indent + '("Boundary Coach", "core.boundary_coach", "get_boundary_coach"),\n',
            indent + '("Emotional Literacy Trainer", "core.emotional_literacy_trainer", "get_emotional_literacy_trainer"),\n',
            indent + '("Hope Cultivator", "core.hope_cultivator", "get_hope_cultivator"),\n',
            indent + '("Attention Steward", "core.attention_steward", "get_attention_steward"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
