# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "systems_thinking_coach", stats: modernStats.evolution_health?.systems_thinking_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "systems_thinking_coach", stats: modernStats.evolution_health?.systems_thinking_coach },
    { name: "authentic_expression_coach", stats: modernStats.evolution_health?.authentic_expression_coach },
    { name: "vulnerable_communication_trainer", stats: modernStats.evolution_health?.vulnerable_communication_trainer },
    { name: "difficult_conversation_navigator", stats: modernStats.evolution_health?.difficult_conversation_navigator },
    { name: "active_listening_master", stats: modernStats.evolution_health?.active_listening_master },
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

old_marker = '"systems_thinking_coach",'
new_marker = '"systems_thinking_coach", "authentic_expression_coach", "vulnerable_communication_trainer", "difficult_conversation_navigator", "active_listening_master",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 52 update complete.")
