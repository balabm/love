import { useState, useEffect } from "react";
import api from "../api";

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
      <div style={{ padding: 24, color: "rgba(226,224,238,0.38)" }}>
        Loading swarm data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Swarm Intelligence</h2>
        <p style={{ color: "rgba(226,224,238,0.38)" }}>Swarm offline. Backend not reachable.</p>
      </div>
    );
  }

  const agents = swarm?.agents || [];

  if (agents.length === 0) {
    return (
      <div style={{ padding: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Swarm Intelligence</h2>
        <p style={{ color: "rgba(226,224,238,0.38)" }}>No swarm agents active. The swarm will form as modules come online.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Swarm Intelligence</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 12 }}>
        {agents.map((agent, i) => (
          <div key={i} style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: 12,
            padding: 16,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <span style={{
                width: 8, height: 8, borderRadius: "50%",
                background: agent.active ? "#34d399" : "#6b7280",
                display: "inline-block",
              }} />
              <span style={{ fontWeight: 500 }}>{agent.name || `Agent ${i + 1}`}</span>
            </div>
            <div style={{ fontSize: 13, color: "rgba(226,224,238,0.38)" }}>{agent.role || "swarm node"}</div>
            {agent.load !== undefined && (
              <div style={{ marginTop: 8, fontSize: 11, color: "rgba(226,224,238,0.25)" }}>
                Load: {Math.round(agent.load * 100)}%
              </div>
            )}
          </div>
        ))}
      </div>
      {swarm?.coordinator && (
        <div style={{
          marginTop: 16,
          padding: 12,
          background: "rgba(255,255,255,0.03)",
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,0.06)",
        }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Coordinator</div>
          <div style={{ fontSize: 12, color: "rgba(226,224,238,0.38)" }}>{swarm.coordinator}</div>
        </div>
      )}
    </div>
  );
}
