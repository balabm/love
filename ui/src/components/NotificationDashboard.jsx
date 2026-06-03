import { useState, useEffect } from "react";
import api from "../api";

const CATEGORY_COLORS = {
  financial: "#fbbf24",
  work: "#60a5fa",
  social: "#f472b6",
  urgent: "#f87171",
  promotional: "#a78bfa",
  system: "#34d399",
  general: "#9ca3af",
};

const PRIORITY_BADGES = {
  high: { bg: "rgba(248,113,113,0.12)", color: "#f87171", label: "HIGH" },
  normal: { bg: "rgba(96,165,250,0.12)", color: "#60a5fa", label: "NORM" },
  low: { bg: "rgba(156,163,175,0.12)", color: "#9ca3af", label: "LOW" },
};

export default function NotificationDashboard() {
  const [notifications, setNotifications] = useState([]);
  const [actionable, setActionable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    const fetchAll = () => {
      api.get("/notifications/recent")
        .then(r => { if (mounted) setNotifications(r.data?.notifications || []); })
        .catch(e => { if (mounted) setError(e.message); })
        .finally(() => { if (mounted) setLoading(false); });
      api.get("/notifications/actionable")
        .then(r => { if (mounted) setActionable(r.data?.actionable || []); })
        .catch(() => {});
    };
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24, color: "rgba(226,224,238,0.38)" }}>
        Loading notifications...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Notifications</h2>
        <p style={{ color: "rgba(226,224,238,0.38)" }}>Notification service offline.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Notifications</h2>

      {/* Actionable Items */}
      {actionable.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ fontSize: 12, fontWeight: 600, color: "#fbbf24", marginBottom: 8, letterSpacing: 1 }}>
            ACTIONABLE ({actionable.length})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {actionable.slice(0, 5).map((n, i) => (
              <div key={`a-${i}`} style={{
                background: "rgba(251,191,36,0.06)",
                border: "1px solid rgba(251,191,36,0.15)",
                borderRadius: 8,
                padding: "10px 12px",
                fontSize: 12,
              }}>
                <span style={{ color: "#fbbf24", fontWeight: 500 }}>{n.text?.slice(0, 100) || "Actionable item"}</span>
                <span style={{ fontSize: 10, color: "rgba(226,224,238,0.3)", marginLeft: 8 }}>{n.source}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Notifications */}
      {notifications.length === 0 ? (
        <p style={{ color: "rgba(226,224,238,0.38)" }}>No recent notifications.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {notifications.map((n, i) => {
            const badge = PRIORITY_BADGES[n.priority] || PRIORITY_BADGES.low;
            const catColor = CATEGORY_COLORS[n.category] || CATEGORY_COLORS.general;
            return (
              <div key={i} style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: 8,
                padding: 12,
                fontSize: 13,
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 500, color: catColor }}>{n.category || "notification"}</span>
                    <span style={{
                      fontSize: 9, fontWeight: 600, letterSpacing: 0.5,
                      padding: "2px 5px", borderRadius: 4,
                      background: badge.bg, color: badge.color,
                    }}>{badge.label}</span>
                    {n.source && (
                      <span style={{ fontSize: 10, color: "rgba(226,224,238,0.25)" }}>{n.source}</span>
                    )}
                  </div>
                  <span style={{ fontSize: 11, color: "rgba(226,224,238,0.25)" }}>{n.ts?.slice(0, 16) || ""}</span>
                </div>
                <p style={{ color: "rgba(226,224,238,0.6)", margin: 0 }}>{n.message}</p>
                {typeof n.signal_score === "number" && (
                  <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
                    <div style={{
                      height: 3, flex: 1, background: "rgba(255,255,255,0.06)", borderRadius: 2, maxWidth: 80,
                    }}>
                      <div style={{
                        height: 3, width: `${Math.min(100, n.signal_score)}%`,
                        background: n.signal_score >= 60 ? "#34d399" : n.signal_score >= 30 ? "#fbbf24" : "#f87171",
                        borderRadius: 2,
                      }} />
                    </div>
                    <span style={{ fontSize: 10, color: "rgba(226,224,238,0.25)" }}>{n.signal_score}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
