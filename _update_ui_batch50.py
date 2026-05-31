# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "abundance_architect", stats: modernStats.evolution_health?.abundance_architect },\n  ].filter(m => m.stats);'
new_end = '''    { name: "abundance_architect", stats: modernStats.evolution_health?.abundance_architect },
    { name: "decision_quality_tracker", stats: modernStats.evolution_health?.decision_quality_tracker },
    { name: "optionality_maximizer", stats: modernStats.evolution_health?.optionality_maximizer },
    { name: "expected_value_coach", stats: modernStats.evolution_health?.expected_value_coach },
    { name: "regret_minimizer", stats: modernStats.evolution_health?.regret_minimizer },
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

old_marker = '"abundance_architect",'
new_marker = '"abundance_architect", "decision_quality_tracker", "optionality_maximizer", "expected_value_coach", "regret_minimizer",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 50 update complete.")
