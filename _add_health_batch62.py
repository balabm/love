api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_end = '            "handcraft_joy_cultivator": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

new_end = '''            "handcraft_joy_cultivator": {"available": True},
            "style_expression_coach": {"available": True},
            "wardrobe_mindfulness_guide": {"available": True},
            "personal_brand_designer": {"available": True},
            "dress_for_joy_coach": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''

if old_end in api:
    api = api.replace(old_end, new_end)
    print("Added 4 engines to health dict (batch 62).")
else:
    print("WARNING: Could not find insertion point.")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
