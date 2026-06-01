# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "posture_presence_coach", stats: modernStats.evolution_health?.posture_presence_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "posture_presence_coach", stats: modernStats.evolution_health?.posture_presence_coach },
    { name: "intimacy_coach", stats: modernStats.evolution_health?.intimacy_coach },
    { name: "sensory_awareness_trainer", stats: modernStats.evolution_health?.sensory_awareness_trainer },
    { name: "passion_cultivator", stats: modernStats.evolution_health?.passion_cultivator },
    { name: "deep_connection_coach", stats: modernStats.evolution_health?.deep_connection_coach },
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

old_marker = '"posture_presence_coach",'
new_marker = '"posture_presence_coach", "intimacy_coach", "sensory_awareness_trainer", "passion_cultivator", "deep_connection_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 54 update complete.")
