import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "rejection_resilience_coach", stats: modernStats.evolution_health?.rejection_resilience_coach },\n    { name: "flow_state_coach"'
new_block = '''    { name: "rejection_resilience_coach", stats: modernStats.evolution_health?.rejection_resilience_coach },
    { name: "storytelling_coach", stats: modernStats.evolution_health?.storytelling_coach },
    { name: "voice_finder", stats: modernStats.evolution_health?.voice_finder },
    { name: "transition_companion", stats: modernStats.evolution_health?.transition_companion },
    { name: "uncertainty_embracer", stats: modernStats.evolution_health?.uncertainty_embracer },
    { name: "flow_state_coach"'''

if 'storytelling_coach' not in content:
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

marker = '"rejection_resilience_coach",\n                "flow_state_coach"'
new_modules = '"rejection_resilience_coach",\n                "storytelling_coach", "voice_finder", "transition_companion", "uncertainty_embracer",\n                "flow_state_coach"'

if 'storytelling_coach' not in content:
    if marker in content:
        content = content.replace(marker, new_modules)
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
