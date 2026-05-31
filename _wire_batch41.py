import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"life_phase_navigator"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"parenting_coach": {"available": True},\n',
            indent + '"family_harmony_builder": {"available": True},\n',
            indent + '"grief_support_companion": {"available": True},\n',
            indent + '"humor_cultivator": {"available": True},\n',
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
    if '"life_phase_navigator"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "parenting_coach", "family_harmony_builder",\n',
            '                "grief_support_companion", "humor_cultivator",\n',
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
    if '("life_phase_navigator"' in line:
        indent = '                '
        new_lines = [
            indent + '("parenting_coach", "Parenting Coach"),\n',
            indent + '("family_harmony_builder", "Family Harmony Builder"),\n',
            indent + '("grief_support_companion", "Grief Support Companion"),\n',
            indent + '("humor_cultivator", "Humor Cultivator"),\n',
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
    if '("Life Phase Navigator"' in line:
        indent = '        '
        new_lines = [
            indent + '("Parenting Coach", "core.parenting_coach", "get_parenting_coach"),\n',
            indent + '("Family Harmony Builder", "core.family_harmony_builder", "get_family_harmony_builder"),\n',
            indent + '("Grief Support Companion", "core.grief_support_companion", "get_grief_support_companion"),\n',
            indent + '("Humor Cultivator", "core.humor_cultivator", "get_humor_cultivator"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
