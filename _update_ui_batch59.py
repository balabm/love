# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "urban_gardening_coach", stats: modernStats.evolution_health?.urban_gardening_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "urban_gardening_coach", stats: modernStats.evolution_health?.urban_gardening_coach },
    { name: "voice_presence_coach", stats: modernStats.evolution_health?.voice_presence_coach },
    { name: "stage_confidence_builder", stats: modernStats.evolution_health?.stage_confidence_builder },
    { name: "audience_connection_trainer", stats: modernStats.evolution_health?.audience_connection_trainer },
    { name: "speech_craft_coach", stats: modernStats.evolution_health?.speech_craft_coach },
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

old_marker = '"urban_gardening_coach",'
new_marker = '"urban_gardening_coach", "voice_presence_coach", "stage_confidence_builder", "audience_connection_trainer", "speech_craft_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 59 update complete.")
