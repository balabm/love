import { useState, useEffect } from "react";
import api, { API } from "../api";

export default function ConstellationMap() {
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
        // Distribute around the core in a circle
        const angle = (i / count) * Math.PI * 2;
        const radius = 25; // % from center
        const x = 50 + radius * Math.cos(angle);
        const y = 50 + radius * Math.sin(angle);
        
        mapped.push({
          id: int.name,
          label: int.name.toUpperCase(),
          type: "peripheral",
          status: int.status, // "connected", "not configured", etc.
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

  return (
    <div style={{ flex: 1, position: "relative", width: "100%", height: "100%", padding: 32 }}>
      <div style={{ position: "absolute", top: 24, left: 24, zIndex: 10 }}>
        <h2 style={{ margin: 0, color: "#fff", letterSpacing: 2, fontSize: 20 }}>DEVICE CONSTELLATION</h2>
        <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12, marginTop: 4 }}>
          Mapping neural peripheral interfaces
        </div>
        <button onClick={pingNodes} disabled={loading} style={{
          marginTop: 16, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
          color: "#fff", padding: "8px 16px", borderRadius: 4, cursor: "pointer", fontFamily: "var(--font-mono)", fontSize: 12
        }}>
          {loading ? "SCANNING PING..." : "PING ALL INTERFACES"}
        </button>
      </div>

      <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
        {/* Draw lines from core to peripherals */}
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

        {/* Draw Nodes */}
        {nodes.map(n => {
          const isCore = n.type === "core";
          const isConnected = n.status === "connected" || n.status === "online";
          
          return (
            <div key={n.id} style={{
              position: "absolute",
              left: `${n.x}%`,
              top: `${n.y}%`,
              transform: "translate(-50%, -50%)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 8,
              zIndex: isCore ? 5 : 2
            }}>
              <div style={{
                width: isCore ? 60 : 40,
                height: isCore ? 60 : 40,
                borderRadius: "50%",
                background: isConnected ? (isCore ? "rgba(192, 132, 252, 0.2)" : "rgba(74, 222, 128, 0.1)") : "rgba(255, 255, 255, 0.05)",
                border: `2px solid ${isConnected ? (isCore ? "#c084fc" : "#4ade80") : "rgba(255,255,255,0.2)"}`,
                boxShadow: isConnected ? `0 0 20px ${isCore ? "rgba(192,132,252,0.5)" : "rgba(74, 222, 128, 0.3)"}` : "none",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.3s ease",
              }}>
                {isCore ? "🧠" : (n.id.includes("phone") ? "📱" : "🔌")}
              </div>
              <div style={{
                background: "rgba(0,0,0,0.8)",
                padding: "4px 8px",
                borderRadius: 4,
                border: "1px solid rgba(255,255,255,0.1)",
                textAlign: "center"
              }}>
                <div style={{ color: "#fff", fontSize: 11, fontWeight: "bold", letterSpacing: 1 }}>{n.label}</div>
                <div style={{ color: isConnected ? "#4ade80" : "#f87171", fontFamily: "var(--font-mono)", fontSize: 9, marginTop: 2 }}>
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
