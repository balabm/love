import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love"

# ── 1. api/evolution_routes.py ──────────────────────────────────────────────
p = os.path.join(BASE, "api", "evolution_routes.py")
with open(p, "r") as f:
    txt = f.read()

marker = '"contemplation_keeper": {"available": True},'
if marker in txt and '"adventure_planner"' not in txt:
    txt = txt.replace(
        marker,
        marker + "\n            \"adventure_planner\": {\"available\": True},\n            \"experience_maximizer\": {\"available\": True},\n            \"wonder_cultivator\": {\"available\": True},\n            \"travel_optimizer\": {\"available\": True},",
    )
    with open(p, "w") as f:
        f.write(txt)
    print("Wired api/evolution_routes.py")
else:
    print("api/evolution_routes.py already wired or marker missing")

# ── 2. core/daily_briefing.py ──────────────────────────────────────────────
p = os.path.join(BASE, "core", "daily_briefing.py")
with open(p, "r") as f:
    txt = f.read()

marker = '"sacred_ritual_designer", "contemplation_keeper",'
new_marker = '"sacred_ritual_designer", "contemplation_keeper",\n                "adventure_planner", "experience_maximizer",\n                "wonder_cultivator", "travel_optimizer",'
if marker in txt and '"adventure_planner"' not in txt:
    txt = txt.replace(marker, new_marker)
    with open(p, "w") as f:
        f.write(txt)
    print("Wired core/daily_briefing.py")
else:
    print("core/daily_briefing.py already wired or marker missing")

# ── 3. core/heartbeat.py ───────────────────────────────────────────────────
p = os.path.join(BASE, "core", "heartbeat.py")
with open(p, "r") as f:
    txt = f.read()

marker = '("contemplation_keeper", "Contemplation Keeper"),'
new_marker = '("contemplation_keeper", "Contemplation Keeper"),\n                ("adventure_planner", "Adventure Planner"),\n                ("experience_maximizer", "Experience Maximizer"),\n                ("wonder_cultivator", "Wonder Cultivator"),\n                ("travel_optimizer", "Travel Optimizer"),'
if marker in txt and '"adventure_planner"' not in txt:
    txt = txt.replace(marker, new_marker)
    with open(p, "w") as f:
        f.write(txt)
    print("Wired core/heartbeat.py")
else:
    print("core/heartbeat.py already wired or marker missing")

# ── 4. start_evolution.py ──────────────────────────────────────────────────
p = os.path.join(BASE, "start_evolution.py")
with open(p, "r") as f:
    txt = f.read()

marker = '("Contemplation Keeper", "core.contemplation_keeper", "get_contemplation_keeper"),'
new_marker = '("Contemplation Keeper", "core.contemplation_keeper", "get_contemplation_keeper"),\n        ("Adventure Planner", "core.adventure_planner", "get_adventure_planner"),\n        ("Experience Maximizer", "core.experience_maximizer", "get_experience_maximizer"),\n        ("Wonder Cultivator", "core.wonder_cultivator", "get_wonder_cultivator"),\n        ("Travel Optimizer", "core.travel_optimizer", "get_travel_optimizer"),'
if marker in txt and '"Adventure Planner"' not in txt:
    txt = txt.replace(marker, new_marker)
    with open(p, "w") as f:
        f.write(txt)
    print("Wired start_evolution.py")
else:
    print("start_evolution.py already wired or marker missing")
