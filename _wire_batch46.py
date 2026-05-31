import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"attention_steward"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"identity_explorer": {"available": True},\n',
            indent + '"values_navigator": {"available": True},\n',
            indent + '"belonging_builder": {"available": True},\n',
            indent + '"rejection_resilience_coach": {"available": True},\n',
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
    if '"attention_steward"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "identity_explorer", "values_navigator",\n',
            '                "belonging_builder", "rejection_resilience_coach",\n',
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
    if '("attention_steward"' in line:
        indent = '                '
        new_lines = [
            indent + '("identity_explorer", "Identity Explorer"),\n',
            indent + '("values_navigator", "Values Navigator"),\n',
            indent + '("belonging_builder", "Belonging Builder"),\n',
            indent + '("rejection_resilience_coach", "Rejection Resilience Coach"),\n',
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
    if '("Attention Steward"' in line:
        indent = '        '
        new_lines = [
            indent + '("Identity Explorer", "core.identity_explorer", "get_identity_explorer"),\n',
            indent + '("Values Navigator", "core.values_navigator", "get_values_navigator"),\n',
            indent + '("Belonging Builder", "core.belonging_builder", "get_belonging_builder"),\n',
            indent + '("Rejection Resilience Coach", "core.rejection_resilience_coach", "get_rejection_resilience_coach"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
