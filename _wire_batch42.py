import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# 1. api/evolution_routes.py
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

inserted = False
for i, line in enumerate(lines):
    if '"humor_cultivator"' in line and 'available' in line:
        indent = '            '
        new_lines = [
            indent + '"civic_engagement_tracker": {"available": True},\n',
            indent + '"mentorship_weaver": {"available": True},\n',
            indent + '"wisdom_keeper": {"available": True},\n',
            indent + '"play_architect": {"available": True},\n',
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
    if '"humor_cultivator"' in line:
        j = i
        while j < len(lines) and ']' not in lines[j]:
            j += 1
        new_lines = [
            '                "civic_engagement_tracker", "mentorship_weaver",\n',
            '                "wisdom_keeper", "play_architect",\n',
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
    if '("humor_cultivator"' in line:
        indent = '                '
        new_lines = [
            indent + '("civic_engagement_tracker", "Civic Engagement Tracker"),\n',
            indent + '("mentorship_weaver", "Mentorship Weaver"),\n',
            indent + '("wisdom_keeper", "Wisdom Keeper"),\n',
            indent + '("play_architect", "Play Architect"),\n',
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
    if '("Humor Cultivator"' in line:
        indent = '        '
        new_lines = [
            indent + '("Civic Engagement Tracker", "core.civic_engagement_tracker", "get_civic_engagement_tracker"),\n',
            indent + '("Mentorship Weaver", "core.mentorship_weaver", "get_mentorship_weaver"),\n',
            indent + '("Wisdom Keeper", "core.wisdom_keeper", "get_wisdom_keeper"),\n',
            indent + '("Play Architect", "core.play_architect", "get_play_architect"),\n',
        ]
        lines = lines[:i+1] + new_lines + lines[i+1:]
        inserted = True
        break

if inserted:
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Wired start_evolution.py")
