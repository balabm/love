api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

old_imports = """        from core.mcp_host import get_mcp_host

        integration = get_evolution_integration()"""

new_imports = """        from core.mcp_host import get_mcp_host
        from core.observability import get_observability_engine
        from core.llm_manager import get_llm_manager

        integration = get_evolution_integration()"""

if old_imports in api:
    api = api.replace(old_imports, new_imports)
    print("Added missing imports: get_observability_engine, get_llm_manager")
else:
    print("WARNING: Could not find insertion point for missing imports")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
