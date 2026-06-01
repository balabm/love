import { useState, useEffect } from "react";
import api from "../api";

export default function SelfEvolutionPanel() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/evolution/metrics")
      .then(r => { if (mounted) setMetrics(r.data); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24, color: "rgba(226,224,238,0.38)" }}>
        Loading evolution metrics...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Self-Evolution Matrix</h2>
        <p style={{ color: "rgba(226,224,238,0.38)" }}>Evolution data unavailable. Backend not reachable.</p>
      </div>
    );
  }

  const experiments = metrics?.experiments || [];
  const deployments = metrics?.deployments || [];

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Self-Evolution Matrix</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 16 }}>
        <MetricCard label="Experiments" value={experiments.length} color="#60a5fa" />
        <MetricCard label="Deployments" value={deployments.length} color="#4ade80" />
        <MetricCard label="Mutations" value={metrics?.mutations || 0} color="#f472b6" />
        <MetricCard label="Gaps" value={metrics?.gaps?.length || 0} color="#fbbf24" />
      </div>
      {experiments.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "rgba(226,224,238,0.6)", marginBottom: 8 }}>Active Experiments</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {experiments.slice(0, 10).map((ex, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                background: "rgba(255,255,255,0.03)",
                borderRadius: 8,
                padding: "8px 12px",
                fontSize: 13,
              }}>
                <span>{ex.name || `Experiment ${i + 1}`}</span>
                <span style={{
                  padding: "2px 8px",
                  borderRadius: 6,
                  fontSize: 11,
                  background: ex.status === "active" ? "rgba(96,165,250,0.12)" : "rgba(255,255,255,0.05)",
                  color: ex.status === "active" ? "#60a5fa" : "rgba(226,224,238,0.38)",
                }}>
                  {ex.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {deployments.length > 0 && (
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "rgba(226,224,238,0.6)", marginBottom: 8 }}>Recent Deployments</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {deployments.slice(0, 10).map((d, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                background: "rgba(255,255,255,0.03)",
                borderRadius: 8,
                padding: "8px 12px",
                fontSize: 13,
              }}>
                <span>{d.name || `Deployment ${i + 1}`}</span>
                <span style={{ fontSize: 11, color: "rgba(226,224,238,0.25)" }}>{d.ts?.slice(0, 16) || ""}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div style={{
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(255,255,255,0.06)",
      borderRadius: 12,
      padding: 12,
      textAlign: "center",
    }}>
      <div style={{ fontSize: 24, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 11, color: "rgba(226,224,238,0.38)" }}>{label}</div>
    </div>
  );
}
