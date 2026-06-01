import { useState, useEffect } from "react";
import api from "../api";

export default function AutonomyPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/evolution/status")
      .then(r => { if (mounted) setStatus(r.data); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24, color: "rgba(226,224,238,0.38)" }}>
        Loading autonomy data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Autonomy Supervisor</h2>
        <p style={{ color: "rgba(226,224,238,0.38)" }}>Autonomy data unavailable. Backend not reachable.</p>
      </div>
    );
  }

  const systems = status?.systems || [];
  const ready = systems.filter(s => s.status === "ready").length;
  const failed = systems.filter(s => s.status === "failed").length;

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Autonomy Supervisor</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 12,
          padding: 12,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#34d399" }}>{ready}</div>
          <div style={{ fontSize: 11, color: "rgba(226,224,238,0.38)" }}>Ready</div>
        </div>
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 12,
          padding: 12,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#fbbf24" }}>{systems.length - ready - failed}</div>
          <div style={{ fontSize: 11, color: "rgba(226,224,238,0.38)" }}>Other</div>
        </div>
        <div style={{
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 12,
          padding: 12,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#f87171" }}>{failed}</div>
          <div style={{ fontSize: 11, color: "rgba(226,224,238,0.38)" }}>Failed</div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {systems.slice(0, 20).map((s, i) => {
          const isReady = s.status === "ready";
          const isFailed = s.status === "failed";
          return (
            <div key={i} style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              background: "rgba(255,255,255,0.03)",
              borderRadius: 8,
              padding: "8px 12px",
              fontSize: 13,
            }}>
              <span style={{ fontWeight: 500 }}>{s.name || s.module || `Module ${i + 1}`}</span>
              <span style={{
                padding: "2px 8px",
                borderRadius: 6,
                fontSize: 11,
                background: isReady ? "rgba(52,211,153,0.12)" : isFailed ? "rgba(248,113,113,0.12)" : "rgba(255,255,255,0.05)",
                color: isReady ? "#34d399" : isFailed ? "#f87171" : "rgba(226,224,238,0.38)",
              }}>
                {s.status}
              </span>
            </div>
          );
        })}
        {systems.length > 20 && (
          <div style={{ textAlign: "center", fontSize: 11, color: "rgba(226,224,238,0.25)" }}>
            + {systems.length - 20} more modules
          </div>
        )}
      </div>
    </div>
  );
}
