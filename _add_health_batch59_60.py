api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_end = '            "memory_curation_coach": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

# Check if already added
if '"voice_presence_coach"' in api:
    print("Already added.")
else:
    new_entries = '''            "memory_curation_coach": {"available": True},
            "voice_presence_coach": {"available": True},
            "stage_confidence_builder": {"available": True},
            "audience_connection_trainer": {"available": True},
            "speech_craft_coach": {"available": True},
            "photo_memory_keeper": {"available": True},
            "visual_storytelling_coach": {"available": True},
            "mindful_photography_guide": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''
    api = api.replace(old_end, new_entries)
    print("Added 8 engines to health dict (batches 59-60).")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
