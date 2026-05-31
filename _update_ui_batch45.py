import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },'
new_block = '''    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },
    { name: "boundary_coach", stats: modernStats.evolution_health?.boundary_coach },
    { name: "emotional_literacy_trainer", stats: modernStats.evolution_health?.emotional_literacy_trainer },
    { name: "hope_cultivator", stats: modernStats.evolution_health?.hope_cultivator },
    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },'''

if 'boundary_coach' not in content:
    marker = '    { name: "rest_designer", stats: modernStats.evolution_health?.rest_designer },'
    new_block = '''    { name: "rest_designer", stats: modernStats.evolution_health?.rest_designer },
    { name: "boundary_coach", stats: modernStats.evolution_health?.boundary_coach },
    { name: "emotional_literacy_trainer", stats: modernStats.evolution_health?.emotional_literacy_trainer },
    { name: "hope_cultivator", stats: modernStats.evolution_health?.hope_cultivator },
    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },'''
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

marker = '"attention_steward"'
new_modules = '"attention_steward", "boundary_coach", "emotional_literacy_trainer", "hope_cultivator", "attention_steward"'

if 'boundary_coach' not in content:
    if marker in content:
        content = content.replace(marker + ',', new_modules + ',')
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
