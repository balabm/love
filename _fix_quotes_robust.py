import os
import re

path = r'c:/Users/balab/OneDrive/Documents/Projects/LLove/love/tests/test_modern_engines.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Fix [''key'] -> ["key"]
content = re.sub(r"\[''([^'\]]+)'\]", r'[\"\1\"]', content)

# Step 2: Fix all remaining '' to "
content = content.replace("''", '"')

# Step 3: Fix any mixed quotes like ["key'] -> ["key"]
content = re.sub(r'\["([^"\']+)'\]', r'["\1"]', content)

# Step 4: Fix any remaining single quotes that should be double in assert statements
content = re.sub(r"assert (\w+)\['([^'\]]+)'\]", r'assert \1["\2"]', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed test quotes robustly')

os.remove(__file__)
