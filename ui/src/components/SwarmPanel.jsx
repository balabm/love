import { useState, useEffect } from "react";
import api from "../api";
import "./SwarmPanel.css";

export default function SwarmPanel() {
  const [swarms, setSwarms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/evolution/swarms")
      .then(r => { if (mounted) setSwarms(Array.isArray(r.data) ? r.data : []); })
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

  if (swarms.length === 0) {
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
        {swarms.map((swarm, i) => (
          <div key={i} className="swarm-agent">
            <div className="swarm-agent-header">
              <span className={`swarm-dot ${swarm.status === 'active' ? 'active' : 'inactive'}`} />
              <span className="swarm-agent-name">{swarm.id || `Swarm ${i + 1}`}</span>
            </div>
            <div className="swarm-agent-role">{swarm.hypothesis || "evolving hypothesis"}</div>
            {swarm.collective_score !== undefined && (
              <div className="swarm-agent-load">
                Score: {Math.round(swarm.collective_score * 100)}% · Agents: {swarm.agents_count || 0}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
