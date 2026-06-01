# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "rhythmic_living_coach", stats: modernStats.evolution_health?.rhythmic_living_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "rhythmic_living_coach", stats: modernStats.evolution_health?.rhythmic_living_coach },
    { name: "mindful_eating_coach", stats: modernStats.evolution_health?.mindful_eating_coach },
    { name: "cooking_joy_cultivator", stats: modernStats.evolution_health?.cooking_joy_cultivator },
    { name: "meal_ritual_designer", stats: modernStats.evolution_health?.meal_ritual_designer },
    { name: "food_as_medicine_coach", stats: modernStats.evolution_health?.food_as_medicine_coach },
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

old_marker = '"rhythmic_living_coach",'
new_marker = '"rhythmic_living_coach", "mindful_eating_coach", "cooking_joy_cultivator", "meal_ritual_designer", "food_as_medicine_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 56 update complete.")
