# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "memory_curation_coach", stats: modernStats.evolution_health?.memory_curation_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "memory_curation_coach", stats: modernStats.evolution_health?.memory_curation_coach },
    { name: "home_repair_coach", stats: modernStats.evolution_health?.home_repair_coach },
    { name: "diy_project_planner", stats: modernStats.evolution_health?.diy_project_planner },
    { name: "maker_mindset_trainer", stats: modernStats.evolution_health?.maker_mindset_trainer },
    { name: "handcraft_joy_cultivator", stats: modernStats.evolution_health?.handcraft_joy_cultivator },
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

old_marker = '"memory_curation_coach",'
new_marker = '"memory_curation_coach", "home_repair_coach", "diy_project_planner", "maker_mindset_trainer", "handcraft_joy_cultivator",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 61 update complete.")
