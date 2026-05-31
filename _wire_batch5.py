import re

# 1. api/evolution_routes.py
with open('api/evolution_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"reflection_prompt_generator": {"available": True},\n            "overall": "healthy"',
    '"reflection_prompt_generator": {"available": True},\n            "proactive_preparation_engine": {"available": True},\n            "context_switching_minimizer": {"available": True},\n            "task_batch_optimizer": {"available": True},\n            "meeting_optimizer": {"available": True},\n            "overall": "healthy"'
)
with open('api/evolution_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated api/evolution_routes.py')

# 2. start_evolution.py docstring
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '- Reflection Prompt Generator (self-awareness catalyst)\n\nUsage:',
    '- Reflection Prompt Generator (self-awareness catalyst)\n- Proactive Preparation Engine (anticipatory intelligence)\n- Context Switching Minimizer (flow state protector)\n- Task Batch Optimizer (task clustering engine)\n- Meeting Optimizer (meeting intelligence)\n\nUsage:'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py docstring')

# 3. start_evolution.py modern_modules list
with open('start_evolution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("Reflection Prompt Generator", "core.reflection_prompt_generator", "get_reflection_prompt_generator"),\n    ]',
    '("Reflection Prompt Generator", "core.reflection_prompt_generator", "get_reflection_prompt_generator"),\n        ("Proactive Preparation Engine", "core.proactive_preparation_engine", "get_proactive_preparation_engine"),\n        ("Context Switching Minimizer", "core.context_switching_minimizer", "get_context_switching_minimizer"),\n        ("Task Batch Optimizer", "core.task_batch_optimizer", "get_task_batch_optimizer"),\n        ("Meeting Optimizer", "core.meeting_optimizer", "get_meeting_optimizer"),\n    ]'
)
with open('start_evolution.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated start_evolution.py modern_modules list')

# 4. daily_briefing.py
with open('core/daily_briefing.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '"time_audit_tool", "reflection_prompt_generator",\n            ]',
    '"time_audit_tool", "reflection_prompt_generator",\n                "proactive_preparation_engine", "context_switching_minimizer",\n                "task_batch_optimizer", "meeting_optimizer",\n            ]'
)
with open('core/daily_briefing.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/daily_briefing.py')

# 5. heartbeat.py
with open('core/heartbeat.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    '("reflection_prompt_generator", "Reflection Prompt Generator"),\n            ]',
    '("reflection_prompt_generator", "Reflection Prompt Generator"),\n                ("proactive_preparation_engine", "Proactive Preparation Engine"),\n                ("context_switching_minimizer", "Context Switching Minimizer"),\n                ("task_batch_optimizer", "Task Batch Optimizer"),\n                ("meeting_optimizer", "Meeting Optimizer"),\n            ]'
)
with open('core/heartbeat.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated core/heartbeat.py')
