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
            system_prompt="You are a meticulous researcher. Your goal is to gather facts, synthesize information, and avoid hallucinations. Cite your steps.",
            tools=["web_search", "read_file"]
        )
        self.register_agent(
            name="CodeAgent",
            role="Senior Developer",
            system_prompt="You are a senior developer. You write clean, robust, and optimized code. You always think about edge cases.",
            tools=["read_file"],
            model_type="coding"
        )
        self.register_agent(
            name="ReviewAgent",
            role="Critical Reviewer",
            system_prompt="You are a harsh but fair reviewer. You look for logic flaws, security vulnerabilities, and inefficiencies in the work of others.",
            tools=[]
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
            
            agent_prompt = f"""{agent.system_prompt}

TASK:
{task}

PREVIOUS AGENT OUTPUTS:
{json.dumps(results, indent=2)}

Please provide your expert contribution to this task.
"""
            try:
                # Assuming the LLM object has an invoke or generate method from langchain_ollama
                response = llm.invoke(agent_prompt)
                results[agent_name] = str(response)
            except Exception as e:
                results[agent_name] = f"Error during execution: {str(e)}"
                
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
