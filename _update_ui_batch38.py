import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Add new modules to IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "death_awareness_coach", stats: modernStats.evolution_health?.death_awareness_coach },'
new_block = '''    { name: "death_awareness_coach", stats: modernStats.evolution_health?.death_awareness_coach },
    { name: "experience_maximizer", stats: modernStats.evolution_health?.experience_maximizer },
    { name: "wonder_cultivator", stats: modernStats.evolution_health?.wonder_cultivator },
    { name: "travel_optimizer", stats: modernStats.evolution_health?.travel_optimizer },'''

if marker in content and 'experience_maximizer' not in content:
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

marker = '"death_awareness_coach"'
new_modules = '"death_awareness_coach", "experience_maximizer", "wonder_cultivator", "travel_optimizer"'

if marker in content and 'experience_maximizer' not in content:
    content = content.replace(marker + ',', new_modules + ',')
    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated SentinelPanel.jsx")
else:
    print("SentinelPanel.jsx already updated or marker missing")
