# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "dress_for_joy_coach", stats: modernStats.evolution_health?.dress_for_joy_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "dress_for_joy_coach", stats: modernStats.evolution_health?.dress_for_joy_coach },
    { name: "language_immersion_coach", stats: modernStats.evolution_health?.language_immersion_coach },
    { name: "cross_cultural_bridge_builder", stats: modernStats.evolution_health?.cross_cultural_bridge_builder },
    { name: "conversation_fluency_trainer", stats: modernStats.evolution_health?.conversation_fluency_trainer },
    { name: "vocabulary_growth_coach", stats: modernStats.evolution_health?.vocabulary_growth_coach },
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

old_marker = '"dress_for_joy_coach",'
new_marker = '"dress_for_joy_coach", "language_immersion_coach", "cross_cultural_bridge_builder", "conversation_fluency_trainer", "vocabulary_growth_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 63 update complete.")
