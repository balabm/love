import re

def clean_ui_file(filepath, list_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if list_name == 'modernModules':
        # match modernModules = [ ... ]
        pattern = re.compile(r'const modernModules = \[\n(.*?)\n  \]\.filter\(m => m\.stats\);', re.DOTALL)
        match = pattern.search(content)
        if not match:
            print(f"Could not find modernModules in {filepath}")
            return
        
        inner = match.group(1)
        # extract all { name: "...", stats: ... }
        items = re.findall(r'\{\s*name:\s*"([^"]+)",\s*stats:\s*modernStats\.evolution_health\?\.([^}]+)\s*\}', inner)
        
        unique_items = []
        seen = set()
        for name, stats in items:
            if name not in seen:
                seen.add(name)
                unique_items.append((name, stats))
        
        print(f"File {filepath}: {len(items)} total, {len(unique_items)} unique")
        
        new_inner = ""
        for name, stats in unique_items:
            new_inner += f'    {{ name: "{name}", stats: modernStats.evolution_health?.{stats} }},\n'
        
        new_content = content[:match.start(1)] + new_inner + content[match.end(1):]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    elif list_name == 'sentinel':
        # match  "string", "string", ... ] inside health filter
        pattern = re.compile(r'\.filter\(\(\[name\]\) => \[\n(.*?)\]\.includes\(name\)\)', re.DOTALL)
        match = pattern.search(content)
        if not match:
            print(f"Could not find sentinel array in {filepath}")
            return
            
        inner = match.group(1)
        items = re.findall(r'"([^"]+)"', inner)
        
        unique_items = []
        seen = set()
        for name in items:
            if name not in seen:
                seen.add(name)
                unique_items.append(name)
                
        print(f"File {filepath}: {len(items)} total, {len(unique_items)} unique")
        
        # format into nice lines
        new_inner = "                "
        for i, name in enumerate(unique_items):
            new_inner += f'"{name}"'
            if i < len(unique_items) - 1:
                new_inner += ", "
                if (i + 1) % 4 == 0:
                    new_inner += "\n                "
        new_inner += "\n              "
        
        new_content = content[:match.start(1)] + new_inner + content[match.end(1):]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

clean_ui_file('ui/src/components/IntelligenceDashboard.jsx', 'modernModules')
clean_ui_file('ui/src/components/SentinelPanel.jsx', 'sentinel')
