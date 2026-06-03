import { useState, useEffect } from "react";
import api from "../api";

export default function SelfEvolutionPanel() {
  const [status, setStatus] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    Promise.allSettled([
      api.get("/evolution/status"),
      api.get("/evolution/experiments"),
      api.get("/intelligence/curiosity-gaps"),
    ]).then(([statusRes, expRes, gapsRes]) => {
      if (!mounted) return;
      if (statusRes.status === "fulfilled") setStatus(statusRes.value.data);
      if (expRes.status === "fulfilled") setExperiments(expRes.value.data || []);
      if (gapsRes.status === "fulfilled") setGaps(gapsRes.value.data?.top_gaps || []);
      setLoading(false);
    }).catch(e => {
      if (mounted) setError(e.message);
      setLoading(false);
    });
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

  const mutationCount = status?.active_mutations || 0;
  const experimentCount = status?.active_experiments || 0;

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Self-Evolution Matrix</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12, marginBottom: 16 }}>
        <MetricCard label="Experiments" value={experimentCount} color="#60a5fa" />
        <MetricCard label="Deployments" value={0} color="#4ade80" />
        <MetricCard label="Mutations" value={mutationCount} color="#f472b6" />
        <MetricCard label="Gaps" value={gaps.length} color="#fbbf24" />
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
                <span>{ex.hypothesis || ex.id || `Experiment ${i + 1}`}</span>
                <span style={{
                  padding: "2px 8px",
                  borderRadius: 6,
                  fontSize: 11,
                  background: ex.status === "running" ? "rgba(96,165,250,0.12)" : "rgba(255,255,255,0.05)",
                  color: ex.status === "running" ? "#60a5fa" : "rgba(226,224,238,0.38)",
                }}>
                  {ex.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      {gaps.length > 0 && (
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 600, color: "rgba(226,224,238,0.6)", marginBottom: 8 }}>Capability Gaps</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {gaps.slice(0, 10).map((g, i) => (
              <div key={i} style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                background: "rgba(255,255,255,0.03)",
                borderRadius: 8,
                padding: "8px 12px",
                fontSize: 13,
              }}>
                <span>{g.subject || g.id || `Gap ${i + 1}`}</span>
                <span style={{ fontSize: 11, color: "rgba(226,224,238,0.25)" }}>{g.priority}</span>
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
