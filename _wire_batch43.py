import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"play_architect"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"home_environment_optimizer": {"available": True},\n',
            indent + '"intergenerational_bridge_builder": {"available": True},\n',
            indent + '"aesthetic_life_designer": {"available": True},\n',
            indent + '"comfort_zone_challenger": {"available": True},\n',
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
    if '"play_architect"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "home_environment_optimizer", "intergenerational_bridge_builder",\n',
            '                "aesthetic_life_designer", "comfort_zone_challenger",\n',
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
    if '("play_architect"' in line:
        indent = '                '
        new_lines = [
            indent + '("home_environment_optimizer", "Home Environment Optimizer"),\n',
            indent + '("intergenerational_bridge_builder", "Intergenerational Bridge Builder"),\n',
            indent + '("aesthetic_life_designer", "Aesthetic Life Designer"),\n',
            indent + '("comfort_zone_challenger", "Comfort Zone Challenger"),\n',
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
    if '("Play Architect"' in line:
        indent = '        '
        new_lines = [
            indent + '("Home Environment Optimizer", "core.home_environment_optimizer", "get_home_environment_optimizer"),\n',
            indent + '("Intergenerational Bridge Builder", "core.intergenerational_bridge_builder", "get_intergenerational_bridge_builder"),\n',
            indent + '("Aesthetic Life Designer", "core.aesthetic_life_designer", "get_aesthetic_life_designer"),\n',
            indent + '("Comfort Zone Challenger", "core.comfort_zone_challenger", "get_comfort_zone_challenger"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
