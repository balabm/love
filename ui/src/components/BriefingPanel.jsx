import { useState, useEffect } from "react";
import api, { API } from "../api";
import "./BriefingPanel.css";

function TimeInput({ value, onChange }) {
  return (
    <input
      type="time"
      className="brf-time-input"
      value={value}
      onChange={e => onChange(e.target.value)}
    />
  );
}

export default function BriefingPanel() {
  const [brief, setBrief] = useState(null);
  const [status, setStatus] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [briefTime, setBriefTime] = useState("08:00");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const loadStatus = async () => {
    try {
      const [statusRes, briefRes] = await Promise.allSettled([
        api.get(`${API}/neural/briefing/status`),
        api.get(`${API}/neural/briefing/latest`),
      ]);
      if (statusRes.status === "fulfilled") {
        const s = statusRes.value.data;
        setStatus(s);
        if (s.brief_time) setBriefTime(s.brief_time);
      }
      if (briefRes.status === "fulfilled") {
        const b = briefRes.value.data;
        if (b.available) setBrief(b);
      }
    } catch (e) {
      console.error("[Briefing] status load failed:", e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const generate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await api.post(`${API}/neural/briefing/generate?force=true`);
      if (res.data.success) {
        setBrief(res.data);
      } else {
        setError(res.data.error || "Generation failed");
      }
    } catch {
      setError("Backend unreachable");
    } finally {
      setGenerating(false);
    }
  };

  const saveTime = async () => {
    setSaving(true);
    try {
      await api.post(`${API}/neural/briefing/set-time`, { time: briefTime });
      await loadStatus();
    } catch (e) {
      console.error("[Briefing] save time failed:", e);
    }
    setSaving(false);
  };

  const formatDate = (iso) => {
    if (!iso) return "";
    try {
      return new Date(iso).toLocaleString([], {
        weekday: "short", month: "short", day: "numeric",
        hour: "2-digit", minute: "2-digit",
      });
    } catch { return iso; }
  };

  return (
    <div className="brf-panel">
      <div className="brf-header">
        <h2>Morning Brief</h2>
        <div className="brf-header-right">
          <div className="brf-status-dot" title={status?.running ? "scheduler running" : "scheduler off"}>
            <span className={`brf-dot ${status?.running ? "brf-dot-on" : "brf-dot-off"}`} />
            <span className="brf-status-label">{status?.running ? "Scheduled" : "Offline"}</span>
          </div>
        </div>
      </div>

      {/* Schedule config */}
      <div className="brf-schedule">
        <span className="brf-schedule-label">Daily at</span>
        <TimeInput value={briefTime} onChange={setBriefTime} />
        <button
          className={`brf-save-btn${saving ? " brf-saving" : ""}`}
          onClick={saveTime}
          disabled={saving}
        >
          {saving ? "Saving..." : "Set"}
        </button>
        <span className="brf-last-run">
          {status?.last_brief_date
            ? `Last: ${status.last_brief_date}`
            : "No brief yet"}
        </span>
      </div>

      {/* Generate button */}
      <button
        className={`brf-gen-btn${generating ? " brf-generating" : ""}`}
        onClick={generate}
        disabled={generating}
      >
        {generating ? (
          <><span className="brf-spinner" /> Generating brief from all sources...</>
        ) : (
          "Generate Now"
        )}
      </button>

      {error && <div className="brf-error">{error}</div>}

      {/* Brief content */}
      {brief ? (
        <div className="brf-content">
          <div className="brf-meta">
            {brief.date && <span className="brf-date">{brief.date}</span>}
            {brief.generated_at && (
              <span className="brf-generated">Generated {formatDate(brief.generated_at)}</span>
            )}
            {brief.cached && <span className="brf-cached">cached</span>}
          </div>
          <div className="brf-text">{brief.text}</div>

          {/* Data sources that fed this brief */}
          {brief.data && (
            <div className="brf-sources">
              <div className="brf-sources-label">Sources used</div>
              <div className="brf-sources-chips">
                {brief.data.google_event_count > 0 && (
                  <span className="brf-chip brf-chip-green">
                    {brief.data.google_event_count} Calendar events
                  </span>
                )}
                {(brief.data.gmail_unread > 0) && (
                  <span className="brf-chip brf-chip-red">
                    {brief.data.gmail_unread} Gmail unread
                  </span>
                )}
                {brief.data.ms_unread > 0 && (
                  <span className="brf-chip brf-chip-blue">
                    {brief.data.ms_unread} Outlook unread
                  </span>
                )}
                {brief.data.finance_prices && Object.keys(brief.data.finance_prices).length > 0 && (
                  <span className="brf-chip brf-chip-cyan">
                    Finance: {Object.keys(brief.data.finance_prices).slice(0, 3).join(", ")}
                  </span>
                )}
                {brief.data.github_notifications > 0 && (
                  <span className="brf-chip brf-chip-orange">
                    {brief.data.github_notifications} GitHub notifications
                  </span>
                )}
                {brief.data.goals_active > 0 && (
                  <span className="brf-chip brf-chip-purple">
                    {brief.data.goals_active} active goals
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="brf-empty">
          <div className="brf-empty-icon">◷</div>
          <div className="brf-empty-text">
            No brief yet. Hit "Generate Now" to get your morning brief from all connected sources.
          </div>
        </div>
      )}
    </div>
  );
}
