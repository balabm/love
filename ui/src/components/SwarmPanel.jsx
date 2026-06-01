import { useState, useEffect } from "react";
import api from "../api";
import "./SwarmPanel.css";

export default function SwarmPanel() {
  const [swarm, setSwarm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/evolution/swarms")
      .then(r => { if (mounted) setSwarm(r.data); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <div className="swarm-panel">
        <div className="swarm-empty">Loading swarm data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="swarm-panel">
        <h2 className="swarm-header">Swarm Intelligence</h2>
        <div className="swarm-empty">Swarm offline. Backend not reachable.</div>
      </div>
    );
  }

  const agents = swarm?.agents || [];

  if (agents.length === 0) {
    return (
      <div className="swarm-panel">
        <h2 className="swarm-header">Swarm Intelligence</h2>
        <div className="swarm-empty">No swarm agents active. The swarm will form as modules come online.</div>
      </div>
    );
  }

  return (
    <div className="swarm-panel">
      <h2 className="swarm-header">Swarm Intelligence</h2>
      <div className="swarm-grid">
        {agents.map((agent, i) => (
          <div key={i} className="swarm-agent">
            <div className="swarm-agent-header">
              <span className={`swarm-dot ${agent.active ? 'active' : 'inactive'}`} />
              <span className="swarm-agent-name">{agent.name || `Agent ${i + 1}`}</span>
            </div>
            <div className="swarm-agent-role">{agent.role || "swarm node"}</div>
            {agent.load !== undefined && (
              <div className="swarm-agent-load">
                Load: {Math.round(agent.load * 100)}%
              </div>
            )}
          </div>
        ))}
      </div>
      {swarm?.coordinator && (
        <div className="swarm-coordinator">
          <div className="swarm-coord-title">Coordinator</div>
          <div className="swarm-coord-name">{swarm.coordinator}</div>
        </div>
      )}
    </div>
  );
}
