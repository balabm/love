# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "food_as_medicine_coach", stats: modernStats.evolution_health?.food_as_medicine_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "food_as_medicine_coach", stats: modernStats.evolution_health?.food_as_medicine_coach },
    { name: "pet_bonding_coach", stats: modernStats.evolution_health?.pet_bonding_coach },
    { name: "animal_empathy_trainer", stats: modernStats.evolution_health?.animal_empathy_trainer },
    { name: "pet_loss_support", stats: modernStats.evolution_health?.pet_loss_support },
    { name: "human_animal_connection_guide", stats: modernStats.evolution_health?.human_animal_connection_guide },
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

old_marker = '"food_as_medicine_coach",'
new_marker = '"food_as_medicine_coach", "pet_bonding_coach", "animal_empathy_trainer", "pet_loss_support", "human_animal_connection_guide",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 57 update complete.")
