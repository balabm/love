api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_end = '            "urban_gardening_coach": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

new_end = '''            "urban_gardening_coach": {"available": True},
            "voice_presence_coach": {"available": True},
            "stage_confidence_builder": {"available": True},
            "audience_connection_trainer": {"available": True},
            "speech_craft_coach": {"available": True},
            "photo_memory_keeper": {"available": True},
            "visual_storytelling_coach": {"available": True},
            "mindful_photography_guide": {"available": True},
            "memory_curation_coach": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''

if old_end in api:
    api = api.replace(old_end, new_end)
    print("Added 8 engines to health dict (batches 59-60).")
else:
    print("WARNING: Could not find insertion point.")
    # Try to find the line number of the overall key
    lines = api.split('\n')
    for i, line in enumerate(lines):
        if '"overall": "healthy"' in line:
            print(f"Found 'overall' at line {i+1}")
            # Show surrounding lines
            start = max(0, i-5)
            end = min(len(lines), i+2)
            print("Context:")
            for j in range(start, end):
                print(f"  {j+1}: {lines[j]}")
            break

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
