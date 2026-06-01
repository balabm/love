# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "deep_connection_coach", stats: modernStats.evolution_health?.deep_connection_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "deep_connection_coach", stats: modernStats.evolution_health?.deep_connection_coach },
    { name: "music_mood_regulator", stats: modernStats.evolution_health?.music_mood_regulator },
    { name: "sound_healing_guide", stats: modernStats.evolution_health?.sound_healing_guide },
    { name: "playlist_therapist", stats: modernStats.evolution_health?.playlist_therapist },
    { name: "rhythmic_living_coach", stats: modernStats.evolution_health?.rhythmic_living_coach },
  ].filter(m => m.stats);'''

if old_end in dash:
    dash = dash.replace(old_end, new_end)
    print("IntelligenceDashboard.jsx updated.")
else:
    print("WARNING: Could not find insertion point in IntelligenceDashboard.jsx")

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(dash)

# --- SentinelPanel.jsx ---
panel_path = "ui/src/components/SentinelPanel.jsx"
with open(panel_path, "r", encoding="utf-8") as f:
    panel = f.read()

old_marker = '"deep_connection_coach",'
new_marker = '"deep_connection_coach", "music_mood_regulator", "sound_healing_guide", "playlist_therapist", "rhythmic_living_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 55 update complete.")
