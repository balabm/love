import { useState, useEffect } from "react";
import api from "../api";

export default function NotificationDashboard() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    api.get("/notifications/recent")
      .then(r => { if (mounted) setNotifications(r.data?.notifications || []); })
      .catch(e => { if (mounted) setError(e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
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
      {notifications.length === 0 ? (
        <p style={{ color: "rgba(226,224,238,0.38)" }}>No recent notifications.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {notifications.map((n, i) => (
            <div key={i} style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
              borderRadius: 8,
              padding: 12,
              fontSize: 13,
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 500 }}>{n.category || "notification"}</span>
                <span style={{ fontSize: 11, color: "rgba(226,224,238,0.25)" }}>{n.ts?.slice(0, 16) || ""}</span>
              </div>
              <p style={{ color: "rgba(226,224,238,0.6)" }}>{n.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
