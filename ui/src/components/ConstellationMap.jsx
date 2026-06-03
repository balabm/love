import { useState, useEffect } from "react";
import api from "../api";
import "./ConstellationMap.css";

const DEFAULT_CORE = { id: "core", label: "LOVE AGI CORE", type: "core", status: "online", x: 50, y: 50 };

function safeNum(v, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export default function ConstellationMap({ compact = false }) {
  const [nodes, setNodes] = useState([DEFAULT_CORE]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  const fetchIntegrations = async () => {
    setErr(null);
    try {
      const res = await api.get("/devices/live-status");
      const payload = res && typeof res.data === "object" && res.data !== null ? res.data : {};
      const devices = Array.isArray(payload.devices) ? payload.devices : [];

      const mapped = [DEFAULT_CORE];
      const count = Math.max(1, devices.length);

      devices.forEach((dev, i) => {
        if (!dev || typeof dev !== "object") return;
        const angle = (i / count) * Math.PI * 2;
        const radius = 25;
        const x = safeNum(50 + radius * Math.cos(angle), 50);
        const y = safeNum(50 + radius * Math.sin(angle), 50);
        const id = String(dev.id || `node-${i}`);
        const name = String(dev.name || "unknown").toUpperCase();
        const status = String(dev.status || "unknown");

        mapped.push({ id, label: name, type: "peripheral", status, x, y });
      });

      setNodes(mapped);
    } catch (e) {
      console.error("[ConstellationMap] fetch error:", e);
      setErr("Could not load device status");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const pingNodes = async () => {
    setLoading(true);
    await fetchIntegrations();
  };

  if (compact) {
    const peripheralCount = nodes.filter(n => n.type !== "core").length;
    const connectedCount = nodes.filter(n => n.type !== "core" && (n.status === "connected" || n.status === "online")).length;
    return (
      <div className="cm-compact">
        <div className="cm-compact-core">
          <div className="cm-compact-icon">🧠</div>
          <div className="cm-compact-label">LOVE AGI CORE</div>
        </div>
        <div className="cm-compact-stats">
          {connectedCount}/{peripheralCount} peripherals online
        </div>
        <button className="cm-ping-btn" onClick={pingNodes} disabled={loading}>
          {loading ? "Scanning..." : "Ping"}
        </button>
      </div>
    );
  }

  const peripherals = nodes.filter(n => n.type !== "core");

  return (
    <div className="cm-container">
      <div className="cm-header">
        <h2>DEVICE CONSTELLATION</h2>
        <div className="cm-subtitle">
          Mapping neural peripheral interfaces
        </div>
        {err && <div style={{ color: "#f87171", fontSize: 12, marginTop: 8 }}>{err}</div>}
        <button className="cm-ping-btn-large" onClick={pingNodes} disabled={loading} style={{ marginTop: err ? 8 : 16 }}>
          {loading ? "SCANNING PING..." : "PING ALL INTERFACES"}
        </button>
      </div>

      <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
        <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
          {peripherals.map(n => (
            <line
              key={`line-${n.id}`}
              x1="50%" y1="50%"
              x2={`${safeNum(n.x, 50)}%`} y2={`${safeNum(n.y, 50)}%`}
              stroke={n.status === "connected" ? "rgba(192, 132, 252, 0.4)" : "rgba(255, 255, 255, 0.1)"}
              strokeWidth="2"
              strokeDasharray={n.status === "connected" ? "0" : "5,5"}
            />
          ))}
        </svg>

        {nodes.map(n => {
          const isCore = n.type === "core";
          const isConnected = n.status === "connected" || n.status === "online";
          const x = safeNum(n.x, 50);
          const y = safeNum(n.y, 50);
          const label = n.label || "UNKNOWN";
          const statusText = typeof n.status === "string" ? n.status.toUpperCase() : "UNKNOWN";
          const nodeId = String(n.id || "node");

          return (
            <div key={nodeId} className={`cm-node ${isCore ? 'core' : 'peripheral'} ${isConnected ? 'connected' : 'disconnected'}`} style={{
              left: `${x}%`,
              top: `${y}%`,
              zIndex: isCore ? 5 : 2
            }}>
              <div className="cm-node-icon">
                {isCore ? "🧠" : (nodeId.includes("phone") ? "📱" : "🔌")}
              </div>
              <div className="cm-node-label">
                <div className="cm-node-name">{label}</div>
                <div className={`cm-node-status ${isConnected ? 'online' : 'offline'}`}>
                  {statusText}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
