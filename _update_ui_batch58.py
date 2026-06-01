# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "human_animal_connection_guide", stats: modernStats.evolution_health?.human_animal_connection_guide },\n  ].filter(m => m.stats);'
new_end = '''    { name: "human_animal_connection_guide", stats: modernStats.evolution_health?.human_animal_connection_guide },
    { name: "garden_therapy_coach", stats: modernStats.evolution_health?.garden_therapy_coach },
    { name: "plant_parenting_guide", stats: modernStats.evolution_health?.plant_parenting_guide },
    { name: "seasonal_garden_planner", stats: modernStats.evolution_health?.seasonal_garden_planner },
    { name: "urban_gardening_coach", stats: modernStats.evolution_health?.urban_gardening_coach },
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

old_marker = '"human_animal_connection_guide",'
new_marker = '"human_animal_connection_guide", "garden_therapy_coach", "plant_parenting_guide", "seasonal_garden_planner", "urban_gardening_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 58 update complete.")
