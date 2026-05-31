import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },'
new_block = '''    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },
    { name: "parenting_coach", stats: modernStats.evolution_health?.parenting_coach },
    { name: "family_harmony_builder", stats: modernStats.evolution_health?.family_harmony_builder },
    { name: "grief_support_companion", stats: modernStats.evolution_health?.grief_support_companion },
    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },'''

if 'parenting_coach' not in content:
    marker = '    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },'
    new_block = '''    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },
    { name: "parenting_coach", stats: modernStats.evolution_health?.parenting_coach },
    { name: "family_harmony_builder", stats: modernStats.evolution_health?.family_harmony_builder },
    { name: "grief_support_companion", stats: modernStats.evolution_health?.grief_support_companion },
    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },'''
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

marker = '"humor_cultivator"'
new_modules = '"humor_cultivator", "parenting_coach", "family_harmony_builder", "grief_support_companion", "humor_cultivator"'

if 'parenting_coach' not in content:
    if marker in content:
        content = content.replace(marker + ',', new_modules + ',')
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
