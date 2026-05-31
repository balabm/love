import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"values_alignment_checker": {"available": True},\n            "overall": "healthy"',
    '"values_alignment_checker": {"available": True},\n            "gratitude_tracker": {"available": True},\n            "energy_audit_tool": {"available": True},\n            "time_audit_tool": {"available": True},\n            "reflection_prompt_generator": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Values Alignment Checker (integrity monitor)\n\nUsage:',
    '- Values Alignment Checker (integrity monitor)\n- Gratitude Tracker (appreciation and positivity)\n- Energy Audit Tool (personal energy intelligence)\n- Time Audit Tool (temporal intelligence)\n- Reflection Prompt Generator (self-awareness catalyst)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Values Alignment Checker", "core.values_alignment_checker", "get_values_alignment_checker"),\n    ]',
    '("Values Alignment Checker", "core.values_alignment_checker", "get_values_alignment_checker"),\n        ("Gratitude Tracker", "core.gratitude_tracker", "get_gratitude_tracker"),\n        ("Energy Audit Tool", "core.energy_audit_tool", "get_energy_audit_tool"),\n        ("Time Audit Tool", "core.time_audit_tool", "get_time_audit_tool"),\n        ("Reflection Prompt Generator", "core.reflection_prompt_generator", "get_reflection_prompt_generator"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"mood_journal", "values_alignment_checker",\n            ]',
    '"mood_journal", "values_alignment_checker",\n                "gratitude_tracker", "energy_audit_tool",\n                "time_audit_tool", "reflection_prompt_generator",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("values_alignment_checker", "Values Alignment Checker"),\n            ]',
    '("values_alignment_checker", "Values Alignment Checker"),\n                ("gratitude_tracker", "Gratitude Tracker"),\n                ("energy_audit_tool", "Energy Audit Tool"),\n                ("time_audit_tool", "Time Audit Tool"),\n                ("reflection_prompt_generator", "Reflection Prompt Generator"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
