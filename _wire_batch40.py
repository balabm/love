import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"network_weaver"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"longevity_optimizer": {"available": True},\n',
            indent + '"vitality_tracker": {"available": True},\n',
            indent + '"age_reversal_coach": {"available": True},\n',
            indent + '"life_phase_navigator": {"available": True},\n',
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
    if '"network_weaver"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "longevity_optimizer", "vitality_tracker",\n',
            '                "age_reversal_coach", "life_phase_navigator",\n',
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
    if '("network_weaver"' in line:
        indent = '                '
        new_lines = [
            indent + '("longevity_optimizer", "Longevity Optimizer"),\n',
            indent + '("vitality_tracker", "Vitality Tracker"),\n',
            indent + '("age_reversal_coach", "Age Reversal Coach"),\n',
            indent + '("life_phase_navigator", "Life Phase Navigator"),\n',
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
    if '("Network Weaver"' in line:
        indent = '        '
        new_lines = [
            indent + '("Longevity Optimizer", "core.longevity_optimizer", "get_longevity_optimizer"),\n',
            indent + '("Vitality Tracker", "core.vitality_tracker", "get_vitality_tracker"),\n',
            indent + '("Age Reversal Coach", "core.age_reversal_coach", "get_age_reversal_coach"),\n',
            indent + '("Life Phase Navigator", "core.life_phase_navigator", "get_life_phase_navigator"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
