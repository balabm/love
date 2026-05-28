import { useState, useEffect, useCallback } from "react";
import api from "../api";
import "./MindPanel.css";

function TimeAgo({ iso }) {
  if (!iso) return <span className="mp-time">—</span>;
  const then = new Date(iso);
  const now = new Date();
  const diffSec = Math.max(0, Math.floor((now - then) / 1000));
  let text;
  if (diffSec < 60) text = `${diffSec}s ago`;
  else if (diffSec < 3600) text = `${Math.floor(diffSec / 60)}m ago`;
  else text = `${Math.floor(diffSec / 3600)}h ago`;
  return <span className="mp-time" title={iso}>{text}</span>;
}

export default function MindPanel() {
  const [thoughts, setThoughts] = useState([]);
  const [supervisor, setSupervisor] = useState(null);
  const [missions, setMissions] = useState(null);
  const [ghostTasks, setGhostTasks] = useState([]);
  const [research, setResearch] = useState(null);
  const [godView, setGodView] = useState(null);
  const [activities, setActivities] = useState([]);
  const [activityStats, setActivityStats] = useState(null);
  const [runningIntel, setRunningIntel] = useState(false);
  const [intelResult, setIntelResult] = useState(null);
  const [daemonStatus, setDaemonStatus] = useState(null);
  const [waveStatus, setWaveStatus] = useState(null);
  const [autonomousGoals, setAutonomousGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    try {
      const [t, s, m, g, r, gv, act, ast, d, w, ag] = await Promise.all([
        api.get("/agi/consciousness/thoughts").catch(() => ({ data: { thoughts: [] } })),
        api.get("/agi/autonomy-supervisor/status").catch(() => ({ data: null })),
        api.get("/agi/missions/status").catch(() => ({ data: null })),
        api.get("/agi/ghost-dev/tasks").catch(() => ({ data: { tasks: [] } })),
        api.get("/agi/research/status").catch(() => ({ data: null })),
        api.get("/dashboard/god-view").catch(() => ({ data: null })),
        api.get("/agi/activity?hours=24&limit=50").catch(() => ({ data: { activities: [] } })),
        api.get("/agi/activity/stats").catch(() => ({ data: null })),
        api.get("/agi/daemon/status").catch(() => ({ data: null })),
        api.get("/wave/status").catch(() => ({ data: null })),
        api.get("/agi/goals/active").catch(() => ({ data: { goals: [] } })),
      ]);
      setThoughts(t.data?.thoughts || []);
      setSupervisor(s.data);
      setMissions(m.data);
      setGhostTasks(g.data?.tasks || []);
      setResearch(r.data);
      setGodView(gv.data);
      setActivities(act.data?.activities || []);
      setActivityStats(ast.data);
      setDaemonStatus(d.data);
      setWaveStatus(w.data);
      setAutonomousGoals(ag.data?.goals || []);
      setError(null);
    } catch (e) {
      setError("Backend offline — is LOVE running?");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRunAGI = async () => {
    setRunningIntel(true);
    setIntelResult(null);
    try {
      const res = await api.post("/agi/autonomy-supervisor/intelligence");
      const actions = res.data?.actions || [];
      const intelActions = actions.filter(
        (a) => ["ghost_dev", "goal_engine", "research_engine", "proactive_push", "wave_engine", "intelligence"].includes(a.component)
      );
      setIntelResult({
        success: true,
        count: intelActions.length,
        actions: intelActions.slice(0, 5),
        timestamp: new Date().toISOString(),
      });
      await fetchAll();
    } catch (e) {
      console.error("Run AGI failed:", e);
      setIntelResult({ success: false, error: e.message });
    } finally {
      setRunningIntel(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 8000);
    return () => clearInterval(id);
  }, [fetchAll]);

  const intelActions = (supervisor?.last_actions || []).filter(
    (a) => ["ghost_dev", "goal_engine", "research_engine", "proactive_push", "wave_engine", "intelligence"].includes(a.component)
  );

  const activeGoals = godView?.life_score?.active_interventions || [];

  if (loading) return <div className="mind-loading">Loading LOVE's mind...</div>;
  if (error) return <div className="mind-error">{error}</div>;

  return (
    <div className="mind-panel">
      <header className="mind-header">
        <span className="mind-icon">🧠</span>
        <div>
          <h2>LOVE's Mind</h2>
          <p className="mind-subtitle">
            {thoughts.length} recent thoughts · {intelActions.length} intelligence actions · {ghostTasks.length} coding tasks
            {supervisor?.last_intelligence_at && (
              <span> · Last intel: <TimeAgo iso={supervisor.last_intelligence_at} /></span>
            )}
          </p>
        </div>
        <div className="mind-header-actions">
          <button
            className={`mind-run-agi-btn ${runningIntel ? "running" : ""}`}
            onClick={handleRunAGI}
            disabled={runningIntel}
            title="Force-run AGI intelligence cycle immediately"
          >
            {runningIntel ? "⏳ Thinking..." : "🧠 Run AGI"}
          </button>
          {supervisor?.intelligence_active && <span className="mind-agi-pill">AGI Active</span>}
        </div>
      </header>

      {/* Intelligence Result Toast */}
      {intelResult && intelResult.success && (
        <div className="intel-toast">
          <div className="intel-toast-header">
            <span>✅ Intelligence cycle complete — {intelResult.count} autonomous action{intelResult.count === 1 ? "" : "s"} taken</span>
            <button className="intel-toast-close" onClick={() => setIntelResult(null)}>×</button>
          </div>
          <div className="intel-toast-actions">
            {intelResult.actions.map((a, i) => (
              <span key={i} className={`intel-toast-tag tag-${a.component}`}>
                {a.component}: {a.action}
              </span>
            ))}
          </div>
        </div>
      )}
      {intelResult && !intelResult.success && (
        <div className="intel-toast intel-toast-error">
          <span>❌ Intelligence cycle failed: {intelResult.error}</span>
          <button className="intel-toast-close" onClick={() => setIntelResult(null)}>×</button>
        </div>
      )}

      {/* Activity Stats Bar */}
      {activityStats && (
        <div className="mind-stats-bar">
          <div className={`mind-stat trend-${activityStats.trend}`}>
            <span className="ms-val">{activityStats.total}</span>
            <span className="ms-label">actions today</span>
          </div>
          {Object.entries(activityStats.by_component || {}).slice(0, 4).map(([k, v]) => (
            <div key={k} className="mind-stat">
              <span className="ms-val">{v}</span>
              <span className="ms-label">{k.replace(/_/g, " ")}</span>
            </div>
          ))}
          <div className="mind-stat">
            <span className="ms-val">{activityStats.trend}</span>
            <span className="ms-label">trend</span>
          </div>
        </div>
      )}

      <div className="mind-grid">
        {/* Activity Log */}
        <div className="mind-card activity-card">
          <h3>Activity Log</h3>
          <div className="activity-stream">
            {activities.length === 0 && <p className="mind-empty">No activity yet. LOVE is just waking up.</p>}
            {activities.map((a, i) => (
              <div key={i} className={`activity-item imp-${a.importance || "normal"}`}>
                <div className="activity-header">
                  <span className="activity-comp">{a.component}</span>
                  <span className="activity-action">{a.action}</span>
                  <TimeAgo iso={a.timestamp} />
                </div>
                <span className="activity-desc">{a.description}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Thoughts Stream */}
        <div className="mind-card thoughts-card">
          <h3>Internal Monologue</h3>
          <div className="thoughts-stream">
            {thoughts.length === 0 && <p className="mind-empty">No thoughts yet. LOVE is quiet.</p>}
            {[...thoughts].reverse().map((t, i) => (
              <div key={i} className="thought-item">
                <span className="thought-text">{t.thought}</span>
                <TimeAgo iso={t.timestamp} />
              </div>
            ))}
          </div>
        </div>

        {/* Intelligence Actions */}
        <div className="mind-card actions-card">
          <h3>Intelligence Actions</h3>
          <div className="actions-stream">
            {intelActions.length === 0 && <p className="mind-empty">No intelligence actions yet.</p>}
            {[...intelActions].reverse().map((a, i) => (
              <div key={i} className={`action-item action-${a.action}`}>
                <span className="action-comp">{a.component}</span>
                <span className="action-verb">{a.action}</span>
                {a.goal && <span className="action-detail">{a.goal}</span>}
                {a.domain && <span className="action-detail">{a.domain}</span>}
                {a.wave && <span className="action-detail">{a.wave}</span>}
                {a.insights && <span className="action-detail">{a.insights.join("; ")}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Goals & Interventions */}
        <div className="mind-card goals-card">
          <h3>Active Interventions</h3>
          <div className="goals-stream">
            {activeGoals.length === 0 && <p className="mind-empty">No active interventions.</p>}
            {activeGoals.map((g, i) => (
              <div key={i} className="goal-item">
                <span className={`goal-priority ${g.priority}`}>{g.priority}</span>
                <span className="goal-message">{g.message}</span>
                {g.action && <span className="goal-action">→ {g.action}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* System Health */}
        <div className="mind-card health-card">
          <h3>System Health</h3>
          <div className="health-stream">
            {daemonStatus && (
              <div className="health-row">
                <span className="health-label">Self-Improvement</span>
                <span className={`health-value ${daemonStatus.last_health_score < 0.5 ? "warn" : "ok"}`}>
                  {daemonStatus.last_health_score !== undefined ? `${(daemonStatus.last_health_score * 100).toFixed(0)}%` : "—"}
                </span>
                <span className="health-meta">{daemonStatus.activity_today || 0} actions today</span>
              </div>
            )}
            {waveStatus && (
              <div className="health-row">
                <span className="health-label">Wave Engine</span>
                <span className="health-value ok">{waveStatus.total_waves || 0} waves</span>
                <span className="health-meta">{waveStatus.last_wave?.slice(0, 30) || "—"}</span>
              </div>
            )}
            {autonomousGoals.length > 0 && (
              <div className="health-row">
                <span className="health-label">AGI Goals</span>
                <span className="health-value ok">{autonomousGoals.length} active</span>
                <span className="health-meta">{autonomousGoals.filter(g => g.progress_pct > 0).length} in progress</span>
              </div>
            )}
            {supervisor && (
              <div className="health-row">
                <span className="health-label">Supervisor</span>
                <span className={`health-value ${supervisor.health_score > 70 ? "ok" : "warn"}`}>
                  {supervisor.health_score || 0}% health
                </span>
                <span className="health-meta">{supervisor.ticks || 0} ticks</span>
              </div>
            )}
          </div>
        </div>

        {/* Missions */}
        <div className="mind-card missions-card">
          <h3>Missions</h3>
          <div className="missions-stream">
            {!missions && <p className="mind-empty">Mission queue unavailable.</p>}
            {missions?.active?.length === 0 && <p className="mind-empty">No active missions.</p>}
            {(missions?.active || []).slice(0, 6).map((m, i) => (
              <div key={i} className={`mission-item status-${m.status}`}>
                <span className="mission-title">{m.title}</span>
                <span className="mission-meta">{m.domain} · {m.attempts || 0} attempts</span>
              </div>
            ))}
          </div>
        </div>

        {/* Ghost Dev */}
        <div className="mind-card ghost-card">
          <h3>Ghost Developer</h3>
          <div className="ghost-stream">
            {ghostTasks.length === 0 && <p className="mind-empty">No coding tasks assigned.</p>}
            {[...ghostTasks].sort((a, b) => b.created_at - a.created_at).slice(0, 6).map((t, i) => (
              <div key={i} className={`ghost-item status-${t.status}`}>
                <span className="ghost-desc">{t.description}</span>
                <span className="ghost-meta">{t.status} · {t.target_files?.length || 0} files</span>
              </div>
            ))}
          </div>
        </div>

        {/* Research */}
        <div className="mind-card research-card">
          <h3>Research Queue</h3>
          <div className="research-stream">
            {!research && <p className="mind-empty">Research engine unavailable.</p>}
            <div className="research-stats">
              {research && (
                <>
                  <span>{research.queued || 0} queued</span>
                  <span>{research.in_progress || 0} in progress</span>
                  <span>{research.completed || 0} completed</span>
                </>
              )}
            </div>
            {(research?.tasks || []).slice(0, 5).map((t, i) => (
              <div key={i} className={`research-item status-${t.status}`}>
                <span className="research-topic">{t.topic}</span>
                <span className="research-status">{t.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
