import { useState, useEffect } from "react";
import api, { API } from "../api";
import "./ConstellationMap.css";

export default function ConstellationMap({ compact = false }) {
  const [nodes, setNodes] = useState([
    { id: "core", label: "LOVE AGI CORE", type: "core", status: "online", x: 50, y: 50 }
  ]);
  const [loading, setLoading] = useState(true);

  const fetchIntegrations = async () => {
    try {
      const res = await api.get(`/neural/setup/integrations`);
      const mapped = [
        { id: "core", label: "LOVE NEURAL CORE", type: "core", status: "online", x: 50, y: 50 }
      ];

      const ints = res.data.integrations || [];
      const count = ints.length;

      ints.forEach((int, i) => {
        const angle = (i / count) * Math.PI * 2;
        const radius = 25;
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);

        mapped.push({
          id: int.name || 'node-' + i,
          label: (int.name || "unknown").toUpperCase(),
          type: "peripheral",
          status: int.status || "unknown",
          x, y
        });
      });

      setNodes(mapped);
    } catch (e) {
      console.error(e);
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

  return (
    <div className="cm-container">
      <div className="cm-header">
        <h2>DEVICE CONSTELLATION</h2>
        <div className="cm-subtitle">
          Mapping neural peripheral interfaces
        </div>
        <button className="cm-ping-btn-large" onClick={pingNodes} disabled={loading}>
          {loading ? "SCANNING PING..." : "PING ALL INTERFACES"}
        </button>
      </div>

      <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
        <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
          {nodes.filter(n => n.type !== "core").map(n => (
            <line
              key={`line-${n.id}`}
              x1="50%" y1="50%"
              x2={`${n.x}%`} y2={`${n.y}%`}
              stroke={n.status === "connected" ? "rgba(192, 132, 252, 0.4)" : "rgba(255, 255, 255, 0.1)"}
              strokeWidth="2"
              strokeDasharray={n.status === "connected" ? "0" : "5,5"}
            />
          ))}
        </svg>

        {nodes.map(n => {
          const isCore = n.type === "core";
          const isConnected = n.status === "connected" || n.status === "online";

          return (
            <div key={n.id} className={`cm-node ${isCore ? 'core' : 'peripheral'} ${isConnected ? 'connected' : 'disconnected'}`} style={{
              left: `${n.x}%`,
              top: `${n.y}%`,
              zIndex: isCore ? 5 : 2
            }}>
              <div className="cm-node-icon">
                {isCore ? "🧠" : (n.id.includes("phone") ? "📱" : "🔌")}
              </div>
              <div className="cm-node-label">
                <div className="cm-node-name">{n.label}</div>
                <div className={`cm-node-status ${isConnected ? 'online' : 'offline'}`}>
                  {n.status.toUpperCase()}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
