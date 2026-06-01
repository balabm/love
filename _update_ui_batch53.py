# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "active_listening_master", stats: modernStats.evolution_health?.active_listening_master },\n  ].filter(m => m.stats);'
new_end = '''    { name: "active_listening_master", stats: modernStats.evolution_health?.active_listening_master },
    { name: "body_awareness_trainer", stats: modernStats.evolution_health?.body_awareness_trainer },
    { name: "breath_work_coach", stats: modernStats.evolution_health?.breath_work_coach },
    { name: "movement_intelligence", stats: modernStats.evolution_health?.movement_intelligence },
    { name: "posture_presence_coach", stats: modernStats.evolution_health?.posture_presence_coach },
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

old_marker = '"active_listening_master",'
new_marker = '"active_listening_master", "body_awareness_trainer", "breath_work_coach", "movement_intelligence", "posture_presence_coach",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 53 update complete.")
