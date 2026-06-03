import re, os, json

# Extract API routes from main.py and all router files
routes = set()
for pyfile in ['api/main.py'] + [f'api/{f}' for f in os.listdir('api') if f.endswith('_routes.py')]:
    if not os.path.exists(pyfile):
        continue
    router_prefix = ""
    with open(pyfile, encoding='utf-8') as f:
        content = f.read()
        # Find router prefix
        pm = re.search(r'APIRouter\(.*prefix="([^"]+)"', content)
        if pm:
            router_prefix = pm.group(1)
        for line in content.splitlines():
            m = re.search(r'@(app|router)\.(get|post|put|delete)\("([^"]+)"', line)
            if m:
                route = m.group(3)
                route = re.sub(r'/\{[^}]+\}', '', route)
                if m.group(1) == 'router' and router_prefix:
                    route = router_prefix + route
                routes.add(route)

# Extract API calls from UI components
ui_calls = {}
for root, dirs, files in os.walk('ui/src/components'):
    for fname in files:
        if fname.endswith('.jsx'):
            path = os.path.join(root, fname)
            with open(path, encoding='utf-8') as f:
                content = f.read()
            calls = re.findall(r'api\.(get|post)\("([^"]+)"', content)
            calls += re.findall(r"api\.(get|post)\(`([^`]+)`", content)
            for method, call in calls:
                call_norm = re.sub(r'\?.*$', '', call)
                call_norm = re.sub(r'\$\{[^}]+\}', '', call_norm)
                call_norm = call_norm.rstrip('/')
                if call_norm not in ui_calls:
                    ui_calls[call_norm] = []
                ui_calls[call_norm].append(fname)

# Find missing routes
missing = []
for call, files in sorted(ui_calls.items()):
    found = False
    for route in routes:
        if call == route or call.startswith(route + '/'):
            found = True
            break
    if not found:
        missing.append((call, files))

print('=== MISSING ENDPOINTS (UI calls but API does not define) ===')
for call, files in missing:
    print(f'{call}  called by: {", ".join(set(files))}')

print()
print('=== TOTAL UI CALLS:', len(ui_calls), 'MISSING:', len(missing))
