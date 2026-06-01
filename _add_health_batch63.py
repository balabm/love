api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_end = '            "dress_for_joy_coach": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

new_end = '''            "dress_for_joy_coach": {"available": True},
            "language_immersion_coach": {"available": True},
            "cross_cultural_bridge_builder": {"available": True},
            "conversation_fluency_trainer": {"available": True},
            "vocabulary_growth_coach": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''

if old_end in api:
    api = api.replace(old_end, new_end)
    print("Added 4 engines to health dict (batch 63).")
else:
    print("WARNING: Could not find insertion point.")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
