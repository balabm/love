import re

api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

# Find all the modern engine imports that were incorrectly inserted inside get_evolution_health()
# These are unindented 'from core.xxx import' lines that appear between the try block and the actual code
modern_imports = []

# The corrupted imports start with "from core." at column 0, inside the function
# We need to extract them and remove them from the function body
# Then add them at the module level

lines = api.split("\n")
new_lines = []
i = 0
corrupted_imports = []
in_corrupted_section = False

while i < len(lines):
    line = lines[i]
    # Detect the start of corrupted imports: unindented "from core." inside the function
    # After line 446 (from core.mcp_host import...) which IS properly indented inside try
    # The corrupted ones start at line 448 with no indentation
    if line.startswith("from core.") and not line.startswith("        ") and not line.startswith("    "):
        # This is a module-level import that got placed wrong
        # Check if we're inside the get_evolution_health function (after try block)
        corrupted_imports.append(line)
        in_corrupted_section = True
        i += 1
        continue
    
    # Skip blank lines in corrupted section
    if in_corrupted_section and line.strip() == "":
        i += 1
        continue
    
    in_corrupted_section = False
    new_lines.append(line)
    i += 1

# Rebuild the file
fixed_api = "\n".join(new_lines)

# Now insert the corrupted imports at the proper module-level location
# After: router = APIRouter(prefix="/evolution", tags=["evolution"])
insert_point = fixed_api.find("router = APIRouter")
insert_point = fixed_api.find("\n", insert_point) + 1

imports_block = "\n".join(corrupted_imports) + "\n"
fixed_api = fixed_api[:insert_point] + "\n" + imports_block + fixed_api[insert_point:]

with open(api_path, "w", encoding="utf-8") as f:
    f.write(fixed_api)

print(f"Fixed API routes. Extracted {len(corrupted_imports)} corrupted imports.")
for imp in corrupted_imports:
    print(f"  - {imp}")
