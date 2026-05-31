# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "comparison_detoxifier", stats: modernStats.evolution_health?.comparison_detoxifier },\n  ].filter(m => m.stats);'
new_end = '''    { name: "comparison_detoxifier", stats: modernStats.evolution_health?.comparison_detoxifier },
    { name: "money_mindset_coach", stats: modernStats.evolution_health?.money_mindset_coach },
    { name: "scarcity_healer", stats: modernStats.evolution_health?.scarcity_healer },
    { name: "generosity_cultivator", stats: modernStats.evolution_health?.generosity_cultivator },
    { name: "abundance_architect", stats: modernStats.evolution_health?.abundance_architect },
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

old_marker = '"comparison_detoxifier",'
new_marker = '"comparison_detoxifier", "money_mindset_coach", "scarcity_healer", "generosity_cultivator", "abundance_architect",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 49 update complete.")
