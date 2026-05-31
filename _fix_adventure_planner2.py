p = r'c:/Users/balab/OneDrive/Documents/Projects/LLove/love/core/adventure_planner.py'
with open(p, 'r') as f:
    content = f.read()

old = '        selected = suggestions.get(edge, suggestions["general"])\n\n        if capacity < 0.3:'
new = '        selected = suggestions.get(edge, suggestions["general"])\n\n        # Backward-compat: old API passed string risk levels for capacity\n        if isinstance(capacity, str):\n            risk_map = {"low": 0.2, "micro": 0.1, "medium": 0.5, "high": 0.8, "extreme": 0.95}\n            capacity = risk_map.get(capacity.lower(), 0.5)\n\n        if capacity < 0.3:'

if old in content:
    content = content.replace(old, new)
    with open(p, 'w') as f:
        f.write(content)
    print('Fixed')
else:
    print('Old block not found')
