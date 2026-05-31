import re

# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

# Find the end of modernModules array and insert new engines
old_end = '    { name: "contemplation_keeper", stats: modernStats.evolution_health?.contemplation_keeper },\n  ].filter(m => m.stats);'
new_end = '''    { name: "contemplation_keeper", stats: modernStats.evolution_health?.contemplation_keeper },
    { name: "inner_critic_tamer", stats: modernStats.evolution_health?.inner_critic_tamer },
    { name: "perfectionism_healer", stats: modernStats.evolution_health?.perfectionism_healer },
    { name: "comparison_detoxifier", stats: modernStats.evolution_health?.comparison_detoxifier },
  ].filter(m => m.stats);'''

if old_end in dash:
    dash = dash.replace(old_end, new_end)
    print("IntelligenceDashboard.jsx updated.")
else:
    print("WARNING: Could not find insertion point in IntelligenceDashboard.jsx")
    # Try to find the line
    for i, line in enumerate(dash.split('\n')):
        if 'contemplation_keeper' in line:
            print(f"  Found contemplation_keeper at line {i+1}: {repr(line)}")
        if '].filter(m => m.stats)' in line:
            print(f"  Found array end at line {i+1}: {repr(line)}")

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(dash)

# --- SentinelPanel.jsx ---
panel_path = "ui/src/components/SentinelPanel.jsx"
with open(panel_path, "r", encoding="utf-8") as f:
    panel = f.read()

if old_end in panel:
    panel = panel.replace(old_end, new_end)
    print("SentinelPanel.jsx updated.")
else:
    print("WARNING: Could not find insertion point in SentinelPanel.jsx")
    for i, line in enumerate(panel.split('\n')):
        if 'contemplation_keeper' in line:
            print(f"  Found contemplation_keeper at line {i+1}: {repr(line)}")
        if '].filter(m => m.stats)' in line:
            print(f"  Found array end at line {i+1}: {repr(line)}")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("Done.")
