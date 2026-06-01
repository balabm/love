api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_end = '            "memory_curation_coach": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

new_end = '''            "memory_curation_coach": {"available": True},
            "home_repair_coach": {"available": True},
            "diy_project_planner": {"available": True},
            "maker_mindset_trainer": {"available": True},
            "handcraft_joy_cultivator": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''

if old_end in api:
    api = api.replace(old_end, new_end)
    print("Added 4 engines to health dict (batch 61).")
else:
    print("WARNING: Could not find insertion point.")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
