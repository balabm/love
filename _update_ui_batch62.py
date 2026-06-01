# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "handcraft_joy_cultivator", stats: modernStats.evolution_health?.handcraft_joy_cultivator },\n  ].filter(m => m.stats);'
new_end = '''    { name: "handcraft_joy_cultivator", stats: modernStats.evolution_health?.handcraft_joy_cultivator },
    { name: "style_expression_coach", stats: modernStats.evolution_health?.style_expression_coach },
    { name: "wardrobe_mindfulness_guide", stats: modernStats.evolution_health?.wardrobe_mindfulness_guide },
    { name: "personal_brand_designer", stats: modernStats.evolution_health?.personal_brand_designer },
    { name: "dress_for_joy_coach", stats: modernStats.evolution_health?.dress_for_joy_coach },
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

old_marker = '"handcraft_joy_cultivator",'
new_marker = '"handcraft_joy_cultivator", "style_expression_coach", "wardrobe_mindfulness_guide", "personal_brand_designer", "dress_for_joy_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 62 update complete.")
