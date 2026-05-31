import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },\n    { name: "flow_state_coach"'
new_block = '''    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },
    { name: "identity_explorer", stats: modernStats.evolution_health?.identity_explorer },
    { name: "values_navigator", stats: modernStats.evolution_health?.values_navigator },
    { name: "belonging_builder", stats: modernStats.evolution_health?.belonging_builder },
    { name: "rejection_resilience_coach", stats: modernStats.evolution_health?.rejection_resilience_coach },
    { name: "flow_state_coach"'''

if 'identity_explorer' not in content:
    if marker in content:
        content = content.replace(marker, new_block)
        with open(intel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated IntelligenceDashboard.jsx")
    else:
        print("IntelligenceDashboard.jsx marker missing")
else:
    print("IntelligenceDashboard.jsx already updated")

# Update SentinelPanel modernModules lists
sentinel_path = os.path.join(BASE, "SentinelPanel.jsx")
with open(sentinel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '"attention_steward",\n                "flow_state_coach"'
new_modules = '"attention_steward",\n                "identity_explorer", "values_navigator", "belonging_builder", "rejection_resilience_coach",\n                "flow_state_coach"'

if 'identity_explorer' not in content:
    if marker in content:
        content = content.replace(marker, new_modules)
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
