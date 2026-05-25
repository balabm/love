import { useState, useEffect } from "react";
import axios from "axios";
import "./GuardianWidget.css";

const API = "http://localhost:8000";

export default function GuardianWidget() {
  const [status, setStatus] = useState(null);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    fetch();
    const t = setInterval(fetch, 60000);
    return () => clearInterval(t);
  }, []);

  const fetch = async () => {
    try {
      const res = await axios.get(`${API}/guardian/work-status`);
      setStatus(res.data);
    } catch (e) { console.error("[Guardian] fetch failed:", e); }
  };

  const hardStop = async () => {
    if (!window.confirm("Hard stop — LOVE will save and lock. Sure?")) return;
    try {
      await axios.post(`${API}/guardian/hard-stop`);
      setStatus(s => s ? { ...s, message: "Hard stop triggered. Good call." } : s);
    } catch (e) { console.error("[Guardian] hard-stop failed:", e); }
  };

  if (!status) return null;

  const hours_worked = status?.hours_worked ?? 0;
  const daily_limit = status?.work_limit ?? status?.daily_limit ?? 9;
  const percent = daily_limit > 0 ? (hours_worked / daily_limit) * 100 : 0;
  const wstatus = status?.status;
  const message = status?.love_message ?? status?.message;
  const over = percent >= 100;
  const warn = percent >= 80 && !over;
  const barColor = over ? "#f87171" : warn ? "#fbbf24" : "#34d399";
  const barPct = Math.min(percent, 100);

  return (
    <div className={`gw${over ? " gw-over" : warn ? " gw-warn" : ""}`}>
      <div className="gw-header" onClick={() => setOpen(o => !o)}>
        <span className="gw-icon">⬡</span>
        <span className="gw-title">Work Guard</span>
        <span className="gw-time">{hours_worked.toFixed(1)}h</span>
        <span className="gw-chevron">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <>
          <div className="gw-bar-bg">
            <div className="gw-bar" style={{ width: `${barPct}%`, background: barColor }} />
          </div>
          <div className="gw-meta">
            <span style={{ color: barColor }}>{percent.toFixed(0)}%</span>
            <span className="gw-limit">of {daily_limit}h</span>
            {over && <span className="gw-badge">OVER LIMIT</span>}
            {warn && <span className="gw-badge warn">NEAR LIMIT</span>}
          </div>
          {message && <div className="gw-msg">{message}</div>}
          {(over || warn) && (
            <button className="gw-stop" onClick={hardStop}>
              Hard Stop
            </button>
          )}
        </>
      )}
    </div>
  );
}
