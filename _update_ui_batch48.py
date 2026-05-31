import re

# --- IntelligenceDashboard.jsx ---
dash_path = "ui/src/components/IntelligenceDashboard.jsx"
with open(dash_path, "r", encoding="utf-8") as f:
    dash = f.read()

# Update engine count
for old, new in [
    ("{/* Intelligence Dashboard — 216 Modern AI Engines */}", "{/* Intelligence Dashboard — 220 Modern AI Engines */}"),
    ("Intelligence Dashboard — 216 Modern AI Engines", "Intelligence Dashboard — 220 Modern AI Engines"),
]:
    dash = dash.replace(old, new)

# Insert after Uncertainty Embracer
new_engines = '''
    { name: "Shadow Integrator", category: "Shadow Work" },
    { name: "Inner Critic Tamer", category: "Self-Acceptance" },
    { name: "Perfectionism Healer", category: "Self-Acceptance" },
    { name: "Comparison Detoxifier", category: "Contentment" },
'''

if "Shadow Integrator" not in dash:
    marker = '{ name: "Uncertainty Embracer", category: "Resilience" }'
    dash = dash.replace(marker, marker + ",\n" + new_engines.strip())

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(dash)

print("IntelligenceDashboard updated.")

# --- SentinelPanel.jsx ---
panel_path = "ui/src/components/SentinelPanel.jsx"
with open(panel_path, "r", encoding="utf-8") as f:
    panel = f.read()

for old, new in [
    ("{/* Sentinel Panel — 216 Modern AI Engines */}", "{/* Sentinel Panel — 220 Modern AI Engines */}"),
    ("Sentinel Panel — 216 Modern AI Engines", "Sentinel Panel — 220 Modern AI Engines"),
]:
    panel = panel.replace(old, new)

if "Shadow Integrator" not in panel:
    marker = '{ name: "Uncertainty Embracer", category: "Resilience" }'
    panel = panel.replace(marker, marker + ",\n" + new_engines.strip())

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("SentinelPanel updated.")
print("UI Batch 48 update complete.")
