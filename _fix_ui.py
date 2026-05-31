import os

BASE = r"c:/Users/balab/OneDrive/Documents/Projects/LLove/love/ui/src/components"

# Fix IntelligenceDashboard
intel_path = os.path.join(BASE, "IntelligenceDashboard.jsx")
with open(intel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },\n    { name: "flow_state_coach", stats: modernStats.evolution_health?.flow_state_coach },'
new_block = '''    { name: "comfort_zone_challenger", stats: modernStats.evolution_health?.comfort_zone_challenger },
    { name: "conflict_resolution_coach", stats: modernStats.evolution_health?.conflict_resolution_coach },
    { name: "forgiveness_facilitator", stats: modernStats.evolution_health?.forgiveness_facilitator },
    { name: "celebration_architect", stats: modernStats.evolution_health?.celebration_architect },
    { name: "rest_designer", stats: modernStats.evolution_health?.rest_designer },
    { name: "boundary_coach", stats: modernStats.evolution_health?.boundary_coach },
    { name: "emotional_literacy_trainer", stats: modernStats.evolution_health?.emotional_literacy_trainer },
    { name: "hope_cultivator", stats: modernStats.evolution_health?.hope_cultivator },
    { name: "attention_steward", stats: modernStats.evolution_health?.attention_steward },
    { name: "flow_state_coach", stats: modernStats.evolution_health?.flow_state_coach },'''

if marker in content:
    content = content.replace(marker, new_block)
    with open(intel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated IntelligenceDashboard.jsx")
else:
    print("IntelligenceDashboard marker not found")

# Fix SentinelPanel
sentinel_path = os.path.join(BASE, "SentinelPanel.jsx")
with open(sentinel_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = '"comfort_zone_challenger",\n                "flow_state_coach"'
new_block = '''"comfort_zone_challenger",
                "conflict_resolution_coach", "forgiveness_facilitator", "celebration_architect", "rest_designer",
                "boundary_coach", "emotional_literacy_trainer", "hope_cultivator", "attention_steward",
                "flow_state_coach"'''

if marker in content:
    content = content.replace(marker, new_block)
    with open(sentinel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated SentinelPanel.jsx")
else:
    print("SentinelPanel marker not found")
