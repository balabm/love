import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "travel_optimizer", stats: modernStats.evolution_health?.travel_optimizer },'
new_block = '''    { name: "travel_optimizer", stats: modernStats.evolution_health?.travel_optimizer },
    { name: "community_builder", stats: modernStats.evolution_health?.community_builder },
    { name: "social_impact_tracker", stats: modernStats.evolution_health?.social_impact_tracker },
    { name: "volunteer_coordinator", stats: modernStats.evolution_health?.volunteer_coordinator },
    { name: "network_weaver", stats: modernStats.evolution_health?.network_weaver },'''

if marker in content and 'community_builder' not in content:
    content = content.replace(marker, new_block)
    with open(intel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated IntelligenceDashboard.jsx")
else:
    print("IntelligenceDashboard.jsx already updated or marker missing")

# Update SentinelPanel modernModules lists
sentinel_path = os.path.join(BASE, "SentinelPanel.jsx")
with open(sentinel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '"travel_optimizer"'
new_modules = '"travel_optimizer", "community_builder", "social_impact_tracker", "volunteer_coordinator", "network_weaver"'

if marker in content and 'community_builder' not in content:
    content = content.replace(marker + ',', new_modules + ',')
    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated SentinelPanel.jsx")
else:
    print("SentinelPanel.jsx already updated or marker missing")
