# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

old_end = '    { name: "vocabulary_growth_coach", stats: modernStats.evolution_health?.vocabulary_growth_coach },\n  ].filter(m => m.stats);'
new_end = '''    { name: "vocabulary_growth_coach", stats: modernStats.evolution_health?.vocabulary_growth_coach },
    { name: "daily_writing_coach", stats: modernStats.evolution_health?.daily_writing_coach },
    { name: "publishing_navigator", stats: modernStats.evolution_health?.publishing_navigator },
    { name: "blog_craft_coach", stats: modernStats.evolution_health?.blog_craft_coach },
    { name: "newsletter_creator", stats: modernStats.evolution_health?.newsletter_creator },
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

old_marker = '"vocabulary_growth_coach",'
new_marker = '"vocabulary_growth_coach", "daily_writing_coach", "publishing_navigator", "blog_craft_coach", "newsletter_creator",'

count = panel.count(old_marker)
if count == 3:
    panel = panel.replace(old_marker, new_marker)
    print(f"SentinelPanel.jsx updated ({count} occurrences).")
else:
    print(f"WARNING: Found {count} occurrences of marker, expected 3.")

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("UI Batch 64 update complete.")
