import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"travel_optimizer"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"community_builder": {"available": True},\n',
            indent + '"social_impact_tracker": {"available": True},\n',
            indent + '"volunteer_coordinator": {"available": True},\n',
            indent + '"network_weaver": {"available": True},\n',
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
    if '"travel_optimizer"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "community_builder", "social_impact_tracker",\n',
            '                "volunteer_coordinator", "network_weaver",\n',
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
    if '("travel_optimizer"' in line:
        indent = '                '
        new_lines = [
            indent + '("community_builder", "Community Builder"),\n',
            indent + '("social_impact_tracker", "Social Impact Tracker"),\n',
            indent + '("volunteer_coordinator", "Volunteer Coordinator"),\n',
            indent + '("network_weaver", "Network Weaver"),\n',
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
    if '("Travel Optimizer"' in line:
        indent = '        '
        new_lines = [
            indent + '("Community Builder", "core.community_builder", "get_community_builder"),\n',
            indent + '("Social Impact Tracker", "core.social_impact_tracker", "get_social_impact_tracker"),\n',
            indent + '("Volunteer Coordinator", "core.volunteer_coordinator", "get_volunteer_coordinator"),\n',
            indent + '("Network Weaver", "core.network_weaver", "get_network_weaver"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
