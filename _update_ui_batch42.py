import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },'
new_block = '''    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },
    { name: "civic_engagement_tracker", stats: modernStats.evolution_health?.civic_engagement_tracker },
    { name: "mentorship_weaver", stats: modernStats.evolution_health?.mentorship_weaver },
    { name: "wisdom_keeper", stats: modernStats.evolution_health?.wisdom_keeper },
    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },'''

if 'civic_engagement_tracker' not in content:
    marker = '    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },'
    new_block = '''    { name: "humor_cultivator", stats: modernStats.evolution_health?.humor_cultivator },
    { name: "civic_engagement_tracker", stats: modernStats.evolution_health?.civic_engagement_tracker },
    { name: "mentorship_weaver", stats: modernStats.evolution_health?.mentorship_weaver },
    { name: "wisdom_keeper", stats: modernStats.evolution_health?.wisdom_keeper },
    { name: "play_architect", stats: modernStats.evolution_health?.play_architect },'''
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

marker = '"play_architect"'
new_modules = '"play_architect", "civic_engagement_tracker", "mentorship_weaver", "wisdom_keeper", "play_architect"'

if 'civic_engagement_tracker' not in content:
    if marker in content:
        content = content.replace(marker + ',', new_modules + ',')
        with open(sentinel_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated SentinelPanel.jsx")
    else:
        print("SentinelPanel.jsx marker missing")
else:
    print("SentinelPanel.jsx already updated")
