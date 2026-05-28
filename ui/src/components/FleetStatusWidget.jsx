import { useState, useEffect } from "react";
import api from "../api";
import "./FleetStatusWidget.css";

export default function FleetStatusWidget({ onOpenSupervisor }) {
  const [status, setStatus] = useState(null);
  const [modules, setModules] = useState({});

  useEffect(() => {
    const fetch = async () => {
      try {
        const [s, m] = await Promise.all([
          api.get("/agi/autonomy-supervisor/status").catch(() => ({ data: null })),
          api.get("/agi/modules/status").catch(() => ({ data: null })),
        ]);
        if (s.data) setStatus(s.data);
        if (m.data?.modules) setModules(m.data.modules);
      } catch (e) {
        // silent fail
      }
    };
    fetch();
    const id = setInterval(fetch, 15000);
    return () => clearInterval(id);
  }, []);

  if (!status) return null;

  const total = Object.keys(modules).length;
  const ready = Object.values(modules).filter((m) => m.state === "ready").length;
  const degraded = Object.values(modules).filter((m) => m.state === "degraded").length;
  const failed = Object.values(modules).filter((m) => m.state === "failed").length;
  const health = status.health_score ?? 0;

  const healthColor = health >= 80 ? "#34d399" : health >= 50 ? "#fbbf24" : "#f87171";
  const healthLabel = health >= 80 ? "Healthy" : health >= 50 ? "Warning" : "Critical";

  return (
    <div className="fleet-widget">
      <div className="fleet-header" onClick={onOpenSupervisor}>
        <span className="fleet-dot" style={{ background: healthColor }} />
        <span className="fleet-title">Fleet Status</span>
        <span className={`fleet-run-indicator ${status?.running ? "running" : "paused"}`}>
          {status?.running ? "● live" : "○ paused"}
        </span>
        <span className="fleet-health">{health}%</span>
      </div>
      <div className="fleet-counts">
        <span className="fleet-count ready">{ready} ready</span>
        {degraded > 0 && <span className="fleet-count degraded">{degraded} deg</span>}
        {failed > 0 && <span className="fleet-count failed">{failed} fail</span>}
        <span className="fleet-count total">{total} total</span>
        {status?.intelligence_active && (
          <span className="fleet-count agi">AGI active</span>
        )}
      </div>
      {failed > 0 && (
        <button className="fleet-quick-fix" onClick={async () => {
          const names = Object.entries(modules).filter(([, m]) => m.state === "failed").map(([n]) => n);
          for (const name of names) {
            try { await api.post("/agi/modules/restart", { name }); } catch (e) {}
          }
        }}>
          🛠️ Restart {failed} failed
        </button>
      )}

      {status?.last_actions && status.last_actions.length > 0 && (
        <div className="fleet-recent-actions">
          {status.last_actions.slice(-2).reverse().map((a, i) => (
            <div key={i} className="fleet-action">
              <span className="fleet-action-comp">{a.component}</span>
              <span className={`fleet-action-verb action-${a.action}`}>{a.action}</span>
              {a.result && <span className="fleet-action-res">→ {a.result}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
