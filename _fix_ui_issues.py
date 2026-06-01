import re

# Fix 1: Rename shadowed /evolution/health endpoint in main.py
main_path = "api/main.py"
with open(main_path, "r", encoding="utf-8") as f:
    main = f.read()

# Replace the shadow endpoint
main = main.replace(
    '@app.get("/evolution/health")\nasync def evolution_health():',
    '@app.get("/evolution/core-health")\nasync def evolution_core_health():'
)

# Also update the docstring
main = main.replace(
    '"""Health check for Self-Evolution Core."""',
    '"""Health check for Self-Evolution Core (separate from full evolution health)."""'
)

with open(main_path, "w", encoding="utf-8") as f:
    f.write(main)

print("Fixed shadowed /evolution/health endpoint in main.py")

# Fix 2: Fix SentinelPanel.jsx API_BASE to use the same base as axios
panel_path = "ui/src/components/SentinelPanel.jsx"
with open(panel_path, "r", encoding="utf-8") as f:
    panel = f.read()

# Change: const API_BASE = window.location.origin;
# To use the same API base as the axios instance
panel = panel.replace(
    'const API_BASE = window.location.origin;',
    'const API_BASE = "http://localhost:8000";'
)

with open(panel_path, "w", encoding="utf-8") as f:
    f.write(panel)

print("Fixed SentinelPanel.jsx API_BASE")

# Fix 3: Add Vite proxy for dev mode
vite_path = "ui/vite.config.js"
with open(vite_path, "r", encoding="utf-8") as f:
    vite = f.read()

vite = vite.replace(
    """export default defineConfig({
  plugins: [react()],
})""",
    """export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/evolution': 'http://localhost:8000',
      '/neural': 'http://localhost:8000',
      '/intelligence': 'http://localhost:8000',
      '/emotional': 'http://localhost:8000',
      '/modern': 'http://localhost:8000',
      '/orchestrator': 'http://localhost:8000',
      '/voice': 'http://localhost:8000',
      '/settings': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    }
  }
})"""
)

with open(vite_path, "w", encoding="utf-8") as f:
    f.write(vite)

print("Added Vite proxy for dev mode")
print("All UI fixes applied.")
