import { useState, useEffect } from "react";
import api, { API } from '../api';
import "./RitualView.css";

function Section({ title, children }) {
  return (
    <div className="rv-section">
      <div className="rv-section-title">{title}</div>
      {children}
    </div>
  );
}

function Pill({ label, color = "#6b7280" }) {
  return (
    <span className="rv-pill" style={{ borderColor: `${color}40`, color }}>
      {label}
    </span>
  );
}

export default function RitualView() {
  const [brief, setBrief] = useState(null);
  const [daySummary, setDaySummary] = useState(null);
  const [guardian, setGuardian] = useState(null);
  const [checkin, setCheckin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState("morning"); // morning | evening

  const hour = new Date().getHours();
  const isEvening = hour >= 17;

  useEffect(() => {
    setMode(isEvening ? "evening" : "morning");
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    const calls = [
      api.get(`/guardian/check-in`).catch(e => { console.error("[Ritual] load failed:", e); return null; }),
      api.get(`/day-summary`).catch(e => { console.error("[Ritual] load failed:", e); return null; }),
      api.get(`/guardian/work-status`).catch(e => { console.error("[Ritual] load failed:", e); return null; }),
      api.get(`/wellness/checkin`).catch(e => { console.error("[Ritual] load failed:", e); return null; }),
    ];
    const [b, d, g, c] = await Promise.all(calls);
    if (b) setBrief(b.data);
    if (d) setDaySummary(d.data);
    if (g) setGuardian(g.data);
    if (c) setCheckin(c.data);
    setLoading(false);
  };

  if (loading) return (
    <div className="rv-loading">
      <div className="rv-loading-heart">♥</div>
      <div>Preparing your {isEvening ? "evening" : "morning"} briefing…</div>
    </div>
  );

  return (
    <div className="rv">
      {/* Header */}
      <div className="rv-header">
        <div className="rv-tabs">
          <button
            className={`rv-tab${mode === "morning" ? " active" : ""}`}
            onClick={() => setMode("morning")}
          >
            ◎ Morning
          </button>
          <button
            className={`rv-tab${mode === "evening" ? " active" : ""}`}
            onClick={() => setMode("evening")}
          >
            ◑ Evening
          </button>
        </div>
        <button className="rv-refresh" onClick={loadAll} title="Refresh">↺</button>
      </div>

      {mode === "morning" && (
        <div className="rv-body">
          {/* Greeting */}
          <div className="rv-greeting">
            <span className="rv-heart">♥</span>
            <div>
              <div className="rv-greeting-title">
                {hour < 12 ? "Good morning" : "Good afternoon"}, Karthi.
              </div>
              <div className="rv-greeting-sub">
                {brief?.message || "Here's what today looks like."}
              </div>
            </div>
          </div>

          {/* Work status */}
          {guardian && (
            <Section title="Work Status">
              <div className="rv-work-row">
                <div className="rv-stat">
                  <span className="rv-stat-num">{(guardian.hours_worked || 0).toFixed(1)}h</span>
                  <span className="rv-stat-lbl">worked</span>
                </div>
                <div className="rv-stat">
                  <span className="rv-stat-num">{guardian.work_limit ?? guardian.daily_limit ?? 9}h</span>
                  <span className="rv-stat-lbl">limit</span>
                </div>
                <div className="rv-stat">
                  <span
                    className="rv-stat-num"
                    style={{
                      color: ((guardian.hours_worked ?? 0) >= (guardian.work_limit ?? guardian.daily_limit ?? 9)) ? "#f87171"
                           : ((guardian.hours_worked ?? 0) >= (guardian.work_limit ?? guardian.daily_limit ?? 9) * 0.8)  ? "#fbbf24"
                           : "#34d399"
                    }}
                  >
                    {(guardian.hours_worked && (guardian.work_limit ?? guardian.daily_limit ?? 9) ? ((guardian.hours_worked / (guardian.work_limit ?? guardian.daily_limit ?? 9)) * 100) : 0).toFixed(0)}%
                  </span>
                  <span className="rv-stat-lbl">used</span>
                </div>
              </div>
            </Section>
          )}

          {/* Tasks due today */}
          {daySummary?.tasks_due_today?.length > 0 && (
            <Section title={`Tasks today (${daySummary.tasks_due_today.length})`}>
              <div className="rv-task-list">
                {daySummary.tasks_due_today.slice(0, 5).map((t, i) => (
                  <div key={i} className="rv-task">
                    <span className="rv-task-check">◻</span>
                    <span className="rv-task-name">{t.title || t.name || t}</span>
                    {t.priority && (
                      <Pill
                        label={t.priority}
                        color={t.priority === "critical" ? "#f87171" : t.priority === "high" ? "#fb923c" : "#6b7280"}
                      />
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Events */}
          {daySummary?.events?.length > 0 && (
            <Section title="Schedule">
              {daySummary.events.slice(0, 4).map((ev, i) => (
                <div key={i} className="rv-event">
                  <span className="rv-event-time">{ev.start || ev.time}</span>
                  <span className="rv-event-title">{ev.title || ev.summary}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Wellness check-in prompt */}
          {checkin && (
            <Section title="How are you?">
              <div className="rv-checkin-msg">{checkin.message || checkin.prompt}</div>
            </Section>
          )}

          {/* LOVE's focus suggestion */}
          {brief?.focus_suggestion && (
            <Section title="LOVE suggests">
              <div className="rv-suggestion">{brief.focus_suggestion}</div>
            </Section>
          )}
        </div>
      )}

      {mode === "evening" && (
        <div className="rv-body">
          {/* Evening header */}
          <div className="rv-greeting">
            <span className="rv-heart">♥</span>
            <div>
              <div className="rv-greeting-title">Evening, Karthi.</div>
              <div className="rv-greeting-sub">
                {daySummary?.summary || "Let's close out the day properly."}
              </div>
            </div>
          </div>

          {/* Day stats */}
          {guardian && (
            <Section title="Today's work">
              <div className="rv-work-row">
                <div className="rv-stat">
                  <span
                    className="rv-stat-num"
                    style={{ color: ((guardian.hours_worked ?? 0) >= (guardian.work_limit ?? guardian.daily_limit ?? 9)) ? "#f87171" : "#34d399" }}
                  >
                    {(guardian.hours_worked || 0).toFixed(1)}h
                  </span>
                  <span className="rv-stat-lbl">worked</span>
                </div>
                <div className="rv-stat">
                  <span className="rv-stat-num">{guardian.work_limit ?? guardian.daily_limit ?? 9}h</span>
                  <span className="rv-stat-lbl">limit</span>
                </div>
              </div>
              {((guardian.hours_worked ?? 0) >= (guardian.work_limit ?? guardian.daily_limit ?? 9)) && (
                <div className="rv-over-limit">You went over your limit. Rest matters — protect tomorrow.</div>
              )}
            </Section>
          )}

          {/* What got done */}
          {daySummary?.completed_today?.length > 0 && (
            <Section title={`Completed (${daySummary.completed_today.length})`}>
              <div className="rv-task-list">
                {daySummary.completed_today.slice(0, 5).map((t, i) => (
                  <div key={i} className="rv-task done">
                    <span className="rv-task-check">✓</span>
                    <span className="rv-task-name">{t.title || t.name || t}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Still open */}
          {daySummary?.open_tasks?.length > 0 && (
            <Section title={`Still open (${daySummary.open_tasks.length})`}>
              <div className="rv-task-list">
                {daySummary.open_tasks.slice(0, 4).map((t, i) => (
                  <div key={i} className="rv-task">
                    <span className="rv-task-check">◻</span>
                    <span className="rv-task-name">{t.title || t.name || t}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* LOVE's wind-down note */}
          <Section title="Wind down">
            <div className="rv-winddown">
              {daySummary?.wind_down_message ||
                "Close the tabs. Drink water. You did enough for today."}
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}
