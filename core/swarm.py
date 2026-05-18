"""
Agent Swarm / Distributed Intelligence Network for LOVE
Enables LOVE to spin up specialized sub-agents to tackle complex problems in parallel.
This implements Phase 10/11 from the AGI roadmap.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from core.llm import get_reasoning_llm, get_coding_llm
from core.tool_registry import get_tool_registry

@dataclass
class SwarmAgent:
    name: str
    role: str
    system_prompt: str
    tools: List[str]
    model_type: str = "reasoning"  # "reasoning" or "coding"

class AgentSwarm:
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.tool_registry = get_tool_registry()
        self._register_default_agents()

    def _register_default_agents(self):
        self.register_agent(
            name="ResearchAgent",
            role="Deep Researcher",
            system_prompt="You are a meticulous researcher. Your goal is to gather facts, synthesize information, and avoid hallucinations. You can browse the web and read files.",
            tools=["browser_search", "browser_navigate", "read_file"]
        )
        self.register_agent(
            name="BrowserAgent",
            role="Web Surfer",
            system_prompt="You are a web surfing agent. You search the internet for exact answers to questions, navigate into the top links, and extract the exact information required.",
            tools=["browser_search", "browser_navigate"]
        )
        self.register_agent(
            name="CodeAgent",
            role="Senior Developer",
            system_prompt="You are a senior developer. You write clean, robust code. You have access to the terminal and can write files.",
            tools=["read_file", "write_file", "execute_terminal_command", "list_directory"],
            model_type="coding"
        )
        self.register_agent(
            name="TerminalAgent",
            role="OS Operator",
            system_prompt="You are an OS operator. You run terminal commands to manage the system, install dependencies, or build software.",
            tools=["execute_terminal_command", "list_directory", "read_file"]
        )

    def register_agent(self, name: str, role: str, system_prompt: str, tools: List[str], model_type: str = "reasoning"):
        self.agents[name] = SwarmAgent(name, role, system_prompt, tools, model_type)

    def delegate_task(self, task: str, required_agents: List[str]) -> Dict[str, str]:
        """
        Coordinates a complex task by delegating parts to different agents.
        Returns the individual agent outputs and a final synthesis.
        """
        results = {}
        # Execute agents sequentially (or could be parallelized with asyncio)
        for agent_name in required_agents:
            if agent_name not in self.agents:
                results[agent_name] = "Error: Agent not found."
                continue
                
            agent = self.agents[agent_name]
            print(f"[Swarm] Delegating to {agent.name} ({agent.role})...")
            
            # Prepare context for the agent
            llm = get_coding_llm() if agent.model_type == "coding" else get_reasoning_llm()
            
            # Fetch tools schema for the agent
            tools_schema = []
            for t_name in agent.tools:
                if t_name in self.tool_registry.tools:
                    tools_schema.append({
                        "name": t_name,
                        "description": self.tool_registry.tools[t_name]["description"],
                        "parameters": self.tool_registry.tools[t_name]["parameters"]
                    })
            
            agent_prompt = f"""{agent.system_prompt}

TASK:
{task}

PREVIOUS AGENT OUTPUTS:
{json.dumps(results, indent=2)}

You have access to the following tools:
{json.dumps(tools_schema, indent=2)}

INSTRUCTIONS:
You must think step-by-step. If you need to use a tool, output a JSON block like this:
```json
{{
    "tool_name": "name_of_tool",
    "parameters": {{ "arg1": "value" }}
}}
```
Do NOT output anything else when calling a tool. Wait for the tool result.
If you have finished the task and do not need any more tools, output your final answer wrapped in:
<FINAL_ANSWER>
...your answer...
</FINAL_ANSWER>
"""
            
            # ReAct Loop
            max_iterations = 10
            iteration = 0
            current_prompt = agent_prompt
            
            while iteration < max_iterations:
                try:
                    response_text = str(llm.invoke(current_prompt))
                    
                    # Check for final answer
                    if "<FINAL_ANSWER>" in response_text:
                        start_idx = response_text.find("<FINAL_ANSWER>") + len("<FINAL_ANSWER>")
                        end_idx = response_text.find("</FINAL_ANSWER>")
                        if end_idx != -1:
                            final_answer = response_text[start_idx:end_idx].strip()
                        else:
                            final_answer = response_text[start_idx:].strip()
                        results[agent_name] = final_answer
                        break
                        
                    # Check for tool call
                    start_json = response_text.find("```json")
                    end_json = response_text.find("```", start_json + 7)
                    if start_json != -1 and end_json != -1:
                        json_str = response_text[start_json+7:end_json].strip()
                        try:
                            tool_call = json.loads(json_str)
                            t_name = tool_call.get("tool_name")
                            t_params = tool_call.get("parameters", {})
                            
                            print(f"[{agent.name}] 🛠️ Calling tool: {t_name}")
                            if t_name in agent.tools:
                                tool_result = self.tool_registry.execute_tool(t_name, t_params)
                            else:
                                tool_result = f"Error: Tool {t_name} is not allowed for this agent."
                                
                            # Feed result back
                            current_prompt += f"\n\nAssistant Tool Call: {json_str}\n\nTool Result:\n{tool_result}\n\nWhat is your next step?"
                        except Exception as e:
                            current_prompt += f"\n\nAssistant generated invalid JSON tool call. Error: {str(e)}. Please try again."
                    else:
                        # Agent didn't use a tool and didn't provide final answer, ask it to finalize
                        current_prompt += f"\n\nAssistant response: {response_text}\n\nYou must use a tool or provide <FINAL_ANSWER>."
                        
                    iteration += 1
                except Exception as e:
                    results[agent_name] = f"Error during execution: {str(e)}"
                    break
                    
            if agent_name not in results:
                results[agent_name] = "Error: Agent reached max iterations without a <FINAL_ANSWER>."
                
                
        # Final Synthesis
        synthesis_prompt = f"""You are LOVE, the Master Orchestrator.
You delegated a complex task to your swarm of expert agents.

ORIGINAL TASK:
{task}

AGENT RESULTS:
{json.dumps(results, indent=2)}

Synthesize these results into a single, comprehensive, high-quality final answer or plan.
"""
        try:
            llm = get_reasoning_llm()
            synthesis_result = str(llm.invoke(synthesis_prompt))
            results["FINAL_SYNTHESIS"] = synthesis_result
        except Exception as e:
            results["FINAL_SYNTHESIS"] = f"Error during synthesis: {str(e)}"
            
        return results

# Singleton
_swarm = None

def get_agent_swarm() -> AgentSwarm:
    global _swarm
    if _swarm is None:
        _swarm = AgentSwarm()
    return _swarm
