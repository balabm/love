import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# ── 1. api/evolution_routes.py ──────────────────────────────────────────────
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r") as f:
    lines = f.readlines()

# Find line with contemplation_keeper and insert after it
inserted = False
for i, line in enumerate(lines):
    if 'contemplation_keeper' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"experience_maximizer": {"available": True},\n',
            indent + '"wonder_cultivator": {"available": True},\n',
            indent + '"travel_optimizer": {"available": True},\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w") as f:
        f.writelines(lines)
    print("Wired api/evolution_routes.py")
else:
    print("api/evolution_routes.py: contemplation_keeper marker not found")

# ── 2. core/daily_briefing.py ──────────────────────────────────────────────
p = os.path.join(BASE, "core", "daily_briefing.py")
with open(p, "r") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"contemplation_keeper"' in line:
        # This line ends with a comma, next lines continue the list
        # Find the closing bracket
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        # Insert before the closing bracket line
        new_lines = [
            '                "experience_maximizer", "wonder_cultivator",\n',
            '                "travel_optimizer",\n',
        ]
        lines = lines[:j] + new_lines + lines[j:]
        inserted = True
        break

if inserted:
    with open(p, "w") as f:
        f.writelines(lines)
    print("Wired core/daily_briefing.py")
else:
    print("core/daily_briefing.py: contemplation_keeper marker not found")

# ── 3. core/heartbeat.py ───────────────────────────────────────────────────
p = os.path.join(BASE, "core", "heartbeat.py")
with open(p, "r") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '("contemplation_keeper"' in line:
        indent = '                '
        new_lines = [
            indent + '("experience_maximizer", "Experience Maximizer"),\n',
            indent + '("wonder_cultivator", "Wonder Cultivator"),\n',
            indent + '("travel_optimizer", "Travel Optimizer"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w") as f:
        f.writelines(lines)
    print("Wired core/heartbeat.py")
else:
    print("core/heartbeat.py: contemplation_keeper marker not found")

# ── 4. start_evolution.py ──────────────────────────────────────────────────
p = os.path.join(BASE, "start_evolution.py")
with open(p, "r") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '("Contemplation Keeper"' in line:
        indent = '        '
        new_lines = [
            indent + '("Experience Maximizer", "core.experience_maximizer", "get_experience_maximizer"),\n',
            indent + '("Wonder Cultivator", "core.wonder_cultivator", "get_wonder_cultivator"),\n',
            indent + '("Travel Optimizer", "core.travel_optimizer", "get_travel_optimizer"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
else:
    print("start_evolution.py: Contemplation Keeper marker not found")
