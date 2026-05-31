import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },'
new_block = '''    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },
    { name: "home_environment_optimizer", stats: modernStats.evolution_health?.home_environment_optimizer },
    { name: "intergenerational_bridge_builder", stats: modernStats.evolution_health?.intergenerational_bridge_builder },
    { name: "aesthetic_life_designer", stats: modernStats.evolution_health?.aesthetic_life_designer },
    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },'''

if 'home_environment_optimizer' not in content:
    marker = '    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },'
    new_block = '''    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },
    { name: "home_environment_optimizer", stats: modernStats.evolution_health?.home_environment_optimizer },
    { name: "intergenerational_bridge_builder", stats: modernStats.evolution_health?.intergenerational_bridge_builder },
    { name: "aesthetic_life_designer", stats: modernStats.evolution_health?.aesthetic_life_designer },
    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },'''
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

marker = '"comfort_zone_challenger"'
new_modules = '"comfort_zone_challenger", "home_environment_optimizer", "intergenerational_bridge_builder", "aesthetic_life_designer", "comfort_zone_challenger"'

if 'home_environment_optimizer' not in content:
    if marker in content:
        content = content.replace(marker + ',', new_modules + ',')
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
