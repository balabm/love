import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },'
new_block = '''    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },
    { name: "longevity_optimizer", stats: modernStats.evolution_health?.longevity_optimizer },
    { name: "vitality_tracker", stats: modernStats.evolution_health?.vitality_tracker },
    { name: "age_reversal_coach", stats: modernStats.evolution_health?.age_reversal_coach },
    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },'''

if 'life_phase_navigator' not in content:
    # The previous batch didn't add life_phase_navigator, let me find the right marker
    marker = '    { name: "network_weaver", stats: modernStats.evolution_health?.network_weaver },'
    new_block = '''    { name: "network_weaver", stats: modernStats.evolution_health?.network_weaver },
    { name: "longevity_optimizer", stats: modernStats.evolution_health?.longevity_optimizer },
    { name: "vitality_tracker", stats: modernStats.evolution_health?.vitality_tracker },
    { name: "age_reversal_coach", stats: modernStats.evolution_health?.age_reversal_coach },
    { name: "life_phase_navigator", stats: modernStats.evolution_health?.life_phase_navigator },'''
    if marker in content and 'longevity_optimizer' not in content:
        content = content.replace(marker, new_block)
        with open(intel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated IntelligenceDashboard.jsx")
    else:
        print("IntelligenceDashboard.jsx already updated or marker missing")
else:
    print("IntelligenceDashboard.jsx already updated")

# Update SentinelPanel modernModules lists
sentinel_path = os.path.join(BASE, "SentinelPanel.jsx")
with open(sentinel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '"network_weaver"'
new_modules = '"network_weaver", "longevity_optimizer", "vitality_tracker", "age_reversal_coach", "life_phase_navigator"'

if marker in content and 'longevity_optimizer' not in content:
    content = content.replace(marker + ',', new_modules + ',')
    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated SentinelPanel.jsx")
else:
    print("SentinelPanel.jsx already updated or marker missing")
