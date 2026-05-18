import requests
import json
import time

API_URL = "http://127.0.0.setup:8000" # fallback port

def test_swarm():
    print("🤖 Triggering Agent Swarm for Complex Code Review...")
    
    payload = {
        "task": "Review the core/agent.py file for any security vulnerabilities or inefficiencies, and suggest an optimization plan.",
        "required_agents": ["ResearchAgent", "CodeAgent", "ReviewAgent"]
    }

    try:
        response = requests.post("http://127.0.0.1:8000/agi/swarm/delegate", json=payload)
        data = response.json()
        
        if data.get("success"):
            print("\n✅ Swarm Task Completed Successfully!\n")
            
            results = data.get("results", {})
            for agent, output in results.items():
                if agent != "FINAL_SYNTHESIS":
                    print(f"[{agent.upper()}]:\n{output}\n" + "-"*40)
                    
            print(f"🧠 [FINAL SYNTHESIS (Master Orchestrator)]:\n{results.get('FINAL_SYNTHESIS')}")
        else:
            print("❌ Swarm Task Failed:", data)
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to LOVE API. Make sure the server is running (python -m api.main)")

if __name__ == "__main__":
    test_swarm()
