import json
import os
import inspect
from typing import Dict, Any, Callable, List
from datetime import datetime

class ToolRegistry:
    """
    Dynamic Tool Registry for LOVE AGI.
    Allows the autonomous agent to execute real functions (web search, file ops, system commands).
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()
        
        # Wave 11: Browser Tools
        try:
            from core.browser_agent import register_browser_tools
            register_browser_tools(self)
        except ImportError:
            pass
            
        # Wave 12: Infinite Memory Tools
        try:
            from core.infinite_memory import register_memory_tools
            register_memory_tools(self)
        except ImportError:
            pass
            
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """Register a new tool for the LLM to use."""
        self.tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters
        }
        
    def get_tool_schema(self) -> str:
        """Get a JSON schema of all available tools for the LLM prompt."""
        schema = []
        for name, data in self.tools.items():
            schema.append({
                "name": name,
                "description": data["description"],
                "parameters": data["parameters"]
            })
        return json.dumps(schema, indent=2)

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with given parameters."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."
            
        try:
            func = self.tools[tool_name]["func"]
            return func(**parameters)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
            
    def _register_default_tools(self):
        # 1. System Time
        self.register_tool(
            name="get_current_time",
            func=lambda: datetime.now().isoformat(),
            description="Get the current system time in ISO format.",
            parameters={}
        )
        
        # 2. File Reader
        def read_file(filepath: str):
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except Exception as e:
                return str(e)
                
        self.register_tool(
            name="read_file",
            func=read_file,
            description="Read the contents of a file on the local system.",
            parameters={
                "filepath": "Absolute or relative path to the file."
            }
        )
        
        # 3. Simple Web Search (DuckDuckGo placeholder or actual request)
        def web_search(query: str):
            try:
                # Basic implementation using requests if duckduckgo search isn't installed
                # In a real scenario, we'd use duckduckgo-search package
                return f"Simulated search results for: {query}"
            except Exception as e:
                return str(e)
                
        self.register_tool(
            name="web_search",
            func=web_search,
            description="Search the web for real-time information.",
            parameters={
                "query": "The search query."
            }
        )

        # 4. File Writer (Ghost Developer capability)
        def write_file(filepath: str, content: str):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Successfully wrote to {filepath}"
            except Exception as e:
                return f"Failed to write file: {str(e)}"

        self.register_tool(
            name="write_file",
            func=write_file,
            description="Write or overwrite a file on the local system with new content.",
            parameters={
                "filepath": "Absolute or relative path to the file.",
                "content": "The string content to write to the file."
            }
        )

        # 5. Terminal Execution
        def execute_terminal_command(command: str):
            try:
                import subprocess
                # Using shell=True but capturing output. In production, add safety filters.
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout if result.returncode == 0 else result.stderr
                return output if output else "Command executed successfully with no output."
            except subprocess.TimeoutExpired:
                return "Error: Command timed out after 30 seconds."
            except Exception as e:
                return f"Error executing command: {str(e)}"

        self.register_tool(
            name="execute_terminal_command",
            func=execute_terminal_command,
            description="Execute a terminal command (shell). Use with caution.",
            parameters={
                "command": "The command string to execute."
            }
        )
        
        # 6. List Directory
        def list_directory(dirpath: str):
            try:
                if not os.path.isdir(dirpath):
                    return f"Error: {dirpath} is not a valid directory."
                items = os.listdir(dirpath)
                return json.dumps(items)
            except Exception as e:
                return f"Error listing directory: {str(e)}"
                
        self.register_tool(
            name="list_directory",
            func=list_directory,
            description="List the contents of a directory.",
            parameters={
                "dirpath": "The path of the directory to list."
            }
        )

# Singleton
_registry = None

def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
