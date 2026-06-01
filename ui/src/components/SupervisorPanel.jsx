import { useState, useEffect, useCallback, useMemo } from "react";
import api from "../api";
import "./SupervisorPanel.css";

const STATE_ICONS = {
  ready: "✅",
  degraded: "⚠️",
  failed: "❌",
  starting: "⏳",
  stopped: "🛑",
  registered: "📋",
};

const STATE_COLORS = {
  ready: "#34d399",
  degraded: "#fbbf24",
  failed: "#f87171",
  starting: "#60a5fa",
  stopped: "#9ca3af",
  registered: "#a78bfa",
};

const WAVE_NAMES = {
  0: "Foundation",
  1: "Awareness",
  2: "Cognition",
  3: "Neural Mesh",
  4: "Evolution",
  5: "Swarm & Goals",
  6: "Sentinel & Test",
};

export default function SupervisorPanel() {
  const [loading, setLoading] = useState(true);
  const [modules, setModules] = useState({});
  const [supervisor, setSupervisor] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [filter, setFilter] = useState("");
  const [waveFilter, setWaveFilter] = useState("all");
  const [expandedWaves, setExpandedWaves] = useState({ 0: true, 1: true, 2: true, 3: true, 4: true, 5: true, 6: true });
  const [restarting, setRestarting] = useState({});
  const [ticking, setTicking] = useState(false);
  const [error, setError] = useState(null);
  const [stateFilter, setStateFilter] = useState("all");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedModule, setExpandedModule] = useState(null);
  const [bulkRestarting, setBulkRestarting] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [modRes, supRes, polRes] = await Promise.all([
        api.get("/agi/modules/status").catch(() => ({ data: null })),
        api.get("/agi/autonomy-supervisor/status").catch(() => ({ data: null })),
        api.get("/agi/autonomy-policy").catch(() => ({ data: null })),
      ]);
      if (modRes.data?.modules) setModules(modRes.data.modules);
      if (supRes.data) setSupervisor(supRes.data);
      if (polRes.data) setPolicy(polRes.data);
      setError(null);
    } catch (e) {
      setError("Backend offline — is LOVE running?");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    if (!autoRefresh) return;
    const id = setInterval(fetchAll, 60000);
    return () => clearInterval(id);
  }, [fetchAll, autoRefresh]);

  const stats = useMemo(() => {
    const values = Object.values(modules);
    const total = values.length;
    const ready = values.filter((m) => m.state === "ready").length;
    const degraded = values.filter((m) => m.state === "degraded").length;
    const failed = values.filter((m) => m.state === "failed").length;
    const starting = values.filter((m) => m.state === "starting").length;
    return { total, ready, degraded, failed, starting };
  }, [modules]);

  const grouped = useMemo(() => {
    const groups = {};
    Object.entries(modules).forEach(([name, m]) => {
      if (!groups[m.wave]) groups[m.wave] = [];
      groups[m.wave].push({ name, ...m });
    });
    return groups;
  }, [modules]);

  const filtered = useMemo(() => {
    const text = filter.toLowerCase();
    const result = {};
    Object.entries(grouped).forEach(([wave, list]) => {
      if (waveFilter !== "all" && String(wave) !== waveFilter) return;
      let filteredList = list.filter(
        (m) =>
          m.name.toLowerCase().includes(text) ||
          (m.error && m.error.toLowerCase().includes(text))
      );
      if (stateFilter !== "all") {
        filteredList = filteredList.filter((m) => m.state === stateFilter);
      }
      if (filteredList.length) result[wave] = filteredList;
    });
    return result;
  }, [grouped, filter, waveFilter, stateFilter]);

  const handleRestart = async (name) => {
    setRestarting((r) => ({ ...r, [name]: true }));
    try {
      await api.post("/agi/modules/restart", { name });
      await fetchAll();
    } catch (e) {
      console.error("Restart failed:", e);
    } finally {
      setRestarting((r) => ({ ...r, [name]: false }));
    }
  };

  const handleTick = async () => {
    setTicking(true);
    try {
      await api.post("/agi/autonomy-supervisor/tick");
      await fetchAll();
    } catch (e) {
      console.error("Tick failed:", e);
    } finally {
      setTicking(false);
    }
  };

  const handleIntelligence = async () => {
    setTicking(true);
    try {
      await api.post("/agi/autonomy-supervisor/intelligence");
      await fetchAll();
    } catch (e) {
      console.error("Intelligence run failed:", e);
    } finally {
      setTicking(false);
    }
  };

  const handleRestartAllFailed = async () => {
    setBulkRestarting(true);
    const failed = Object.entries(modules).filter(([, m]) => m.state === "failed");
    for (const [name] of failed) {
      try {
        await api.post("/agi/modules/restart", { name });
      } catch (e) {
        console.error(`Restart ${name} failed:`, e);
      }
    }
    await fetchAll();
    setBulkRestarting(false);
  };

  const handleRestartAllDegraded = async () => {
    setBulkRestarting(true);
    const degraded = Object.entries(modules).filter(([, m]) => m.state === "degraded");
    for (const [name] of degraded) {
      try {
        await api.post("/agi/modules/restart", { name });
      } catch (e) {
        console.error(`Restart ${name} failed:`, e);
      }
    }
    await fetchAll();
    setBulkRestarting(false);
  };

  const exportReport = () => {
    const report = {
      timestamp: new Date().toISOString(),
      supervisor: supervisor || {},
      modules: modules,
      stats: stats,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `love-fleet-report-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const setMode = async (mode) => {
    try {
      await api.post("/agi/autonomy-policy/mode", { mode });
      await fetchAll();
    } catch (e) {
      console.error("Set mode failed:", e);
    }
  };

  const toggleWave = (wave) => {
    setExpandedWaves((w) => ({ ...w, [wave]: !w[wave] }));
  };

  if (loading) return <div className="supervisor-loading">Loading fleet status...</div>;
  if (error) return <div className="supervisor-error">{error}</div>;

  return (
    <div className="supervisor-panel">
      {/* Header */}
      <div className="supervisor-header">
        <div className="supervisor-title">
          <span className="supervisor-icon">🛡️</span>
          <div>
            <h2>Autonomy Supervisor</h2>
            <p className="supervisor-subtitle">
              {stats.total} modules monitored · {stats.ready} ready · {stats.degraded} degraded · {stats.failed} failed
              {supervisor?.intelligence_active && (
                <span className="supervisor-agi-badge"> · AGI active</span>
              )}
            </p>
          </div>
        </div>
        <div className="supervisor-actions">
          <button className={`supervisor-tick-btn ${ticking ? "ticking" : ""}`} onClick={handleTick} disabled={ticking || bulkRestarting}>
            {ticking ? "⏳ Running tick..." : "▶ Run Tick"}
          </button>
          <button className="supervisor-intel-btn" onClick={handleIntelligence} disabled={ticking || bulkRestarting} title="Force-run AGI intelligence loop immediately">
            {ticking ? "⏳ Thinking..." : "🧠 Run AGI"}
          </button>
          <button className="supervisor-export-btn" onClick={exportReport} title="Export fleet report as JSON">
            📥 Export
          </button>
          <span className="supervisor-uptime">
            {supervisor?.ticks ? `Ticks: ${supervisor.ticks}` : ""}
          </span>
        </div>
      </div>

      {/* Health Score */}
      {supervisor?.health_score !== undefined && (
        <div className="supervisor-health-bar">
          <div className="supervisor-health-track">
            <div
              className="supervisor-health-fill"
              style={{
                width: `${supervisor.health_score}%`,
                background: supervisor.health_score >= 80 ? "#34d399" : supervisor.health_score >= 50 ? "#fbbf24" : "#f87171",
              }}
            />
          </div>
          <span className="supervisor-health-score">
            Fleet Health: {supervisor.health_score}%
          </span>
        </div>
      )}

      {/* Stats Bar */}
      <div className="supervisor-stats-bar">
        <div className="supervisor-stat ready">
          <span className="supervisor-stat-value">{stats.ready}</span>
          <span className="supervisor-stat-label">Ready</span>
        </div>
        <div className="supervisor-stat degraded">
          <span className="supervisor-stat-value">{stats.degraded}</span>
          <span className="supervisor-stat-label">Degraded</span>
        </div>
        <div className="supervisor-stat failed">
          <span className="supervisor-stat-value">{stats.failed}</span>
          <span className="supervisor-stat-label">Failed</span>
        </div>
        <div className="supervisor-stat starting">
          <span className="supervisor-stat-value">{stats.starting}</span>
          <span className="supervisor-stat-label">Starting</span>
        </div>
        <div className="supervisor-stat total">
          <span className="supervisor-stat-value">{stats.total}</span>
          <span className="supervisor-stat-label">Total</span>
        </div>
      </div>

      {/* Policy Mode */}
      <div className="supervisor-policy">
        <span className="supervisor-policy-label">Policy Mode:</span>
        {["safe", "balanced", "aggressive"].map((m) => (
          <button
            key={m}
            className={`supervisor-mode-btn ${policy?.mode === m ? "active" : ""} mode-${m}`}
            onClick={() => setMode(m)}
          >
            {m === "safe" ? "🛡️" : m === "balanced" ? "⚖️" : "🚀"} {m}
          </button>
        ))}
      </div>

      {/* Bulk Actions */}
      <div className="supervisor-bulk-actions">
        <button className="supervisor-bulk-btn bulk-failed" onClick={handleRestartAllFailed} disabled={bulkRestarting || stats.failed === 0}>
          {bulkRestarting ? "⏳" : "🛠️"} Restart All Failed ({stats.failed})
        </button>
        <button className="supervisor-bulk-btn bulk-degraded" onClick={handleRestartAllDegraded} disabled={bulkRestarting || stats.degraded === 0}>
          {bulkRestarting ? "⏳" : "🔧"} Restart All Degraded ({stats.degraded})
        </button>
        <label className="supervisor-refresh-toggle">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
          />
          <span>Auto-refresh</span>
        </label>
      </div>

      {/* State Filter Pills */}
      <div className="supervisor-state-filters">
        {[
          { key: "all", label: "All", count: stats.total },
          { key: "ready", label: "Ready", count: stats.ready },
          { key: "degraded", label: "Degraded", count: stats.degraded },
          { key: "failed", label: "Failed", count: stats.failed },
          { key: "starting", label: "Starting", count: stats.starting },
        ].map((s) => (
          <button
            key={s.key}
            className={`supervisor-state-pill ${stateFilter === s.key ? "active" : ""}`}
            onClick={() => setStateFilter(stateFilter === s.key ? "all" : s.key)}
          >
            {s.label} <span className="supervisor-pill-count">{s.count}</span>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="supervisor-filters">
        <input
          className="supervisor-search"
          placeholder="🔍 Search modules..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <select className="supervisor-wave-select" value={waveFilter} onChange={(e) => setWaveFilter(e.target.value)}>
          <option value="all">All Waves</option>
          {Object.entries(WAVE_NAMES).map(([w, name]) => (
            <option key={w} value={w}>Wave {w}: {name}</option>
          ))}
        </select>
      </div>

      {/* Module Groups */}
      <div className="supervisor-modules">
        {Object.keys(filtered).length === 0 && (
          <div className="supervisor-empty">No modules match the current filters.</div>
        )}
        {Object.entries(filtered)
          .sort(([a], [b]) => Number(a) - Number(b))
          .map(([wave, list]) => {
            const waveReady = list.filter((m) => m.state === "ready").length;
            const waveDegraded = list.filter((m) => m.state === "degraded").length;
            const waveFailed = list.filter((m) => m.state === "failed").length;
            const isExpanded = expandedWaves[wave];
            return (
              <div key={wave} className="supervisor-wave">
                <div className="supervisor-wave-header" onClick={() => toggleWave(wave)}>
                  <span className="supervisor-wave-toggle">{isExpanded ? "▼" : "▶"}</span>
                  <span className="supervisor-wave-name">
                    Wave {wave} · {WAVE_NAMES[wave] || "Unknown"}
                  </span>
                  <span className="supervisor-wave-count">
                    {waveReady}/{list.length} ready
                    {waveDegraded > 0 && <span className="wave-badge degraded">{waveDegraded} degraded</span>}
                    {waveFailed > 0 && <span className="wave-badge failed">{waveFailed} failed</span>}
                  </span>
                </div>
                {isExpanded && (
                  <div className="supervisor-wave-body">
                    <table className="supervisor-table">
                      <thead>
                        <tr>
                          <th>Status</th>
                          <th>Module</th>
                          <th>Deps</th>
                          <th>Startup</th>
                          <th>Info</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {list
                          .sort((a, b) => a.name.localeCompare(b.name))
                          .map((m) => (
                            <>
                            <tr
                              key={m.name}
                              className={`supervisor-row state-${m.state} ${expandedModule === m.name ? "expanded" : ""}`}
                              onClick={() => setExpandedModule(expandedModule === m.name ? null : m.name)}
                            >
                              <td>
                                <span className="supervisor-state-badge" style={{ color: STATE_COLORS[m.state] || "#fff" }}>
                                  {STATE_ICONS[m.state] || "◌"} {m.state}
                                </span>
                              </td>
                              <td>
                                <code className="supervisor-mod-name">{m.name}</code>
                                {m.optional && <span className="supervisor-optional-tag">optional</span>}
                                <span className="supervisor-expand-hint">{expandedModule === m.name ? "▲" : "▼"}</span>
                              </td>
                              <td>
                                {m.depends_on?.length ? (
                                  m.depends_on.map((d) => (
                                    <code key={d} className="supervisor-dep-tag">{d}</code>
                                  ))
                                ) : (
                                  <span className="supervisor-no-deps">—</span>
                                )}
                              </td>
                              <td className="supervisor-elapsed">
                                {m.elapsed_ms ? `${m.elapsed_ms.toFixed(1)}ms` : "—"}
                              </td>
                              <td className="supervisor-info" title={m.error || ""}>
                                {m.error ? (
                                  <span className="supervisor-error-text">{m.error}</span>
                                ) : (
                                  <span className="supervisor-ok-text">Operating normally</span>
                                )}
                              </td>
                              <td>
                                <button
                                  className="supervisor-restart-btn"
                                  onClick={(e) => { e.stopPropagation(); handleRestart(m.name); }}
                                  disabled={restarting[m.name]}
                                >
                                  {restarting[m.name] ? "⏳" : "🛠️"} Restart
                                </button>
                              </td>
                            </tr>
                            {expandedModule === m.name && (
                              <tr className="supervisor-detail-row">
                                <td colSpan={6}>
                                  <div className="supervisor-detail">
                                    <div className="supervisor-detail-grid">
                                      <div>
                                        <strong>Wave:</strong> {m.wave} · {WAVE_NAMES[m.wave]}
                                      </div>
                                      <div>
                                        <strong>Optional:</strong> {m.optional ? "Yes" : "No"}
                                      </div>
                                      <div>
                                        <strong>State:</strong> <span style={{ color: STATE_COLORS[m.state] }}>{m.state}</span>
                                      </div>
                                      <div>
                                        <strong>Startup time:</strong> {m.elapsed_ms ? `${m.elapsed_ms.toFixed(2)}ms` : "N/A"}
                                      </div>
                                    </div>
                                    {m.error && (
                                      <div className="supervisor-detail-error">
                                        <strong>Error:</strong>
                                        <pre>{m.error}</pre>
                                      </div>
                                    )}
                                    {m.depends_on?.length > 0 && (
                                      <div className="supervisor-detail-deps">
                                        <strong>Dependencies:</strong> {m.depends_on.join(", ")}
                                      </div>
                                    )}
                                    {m.health && (
                                      <div className="supervisor-detail-health">
                                        <strong>Health check:</strong> <pre>{JSON.stringify(m.health, null, 2)}</pre>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            )}
                            </>
                          ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
      </div>

      {/* Recent Actions */}
      {supervisor?.last_actions?.length > 0 && (
        <div className="supervisor-actions-log">
          <h4>Recent Supervisor Actions</h4>
          <div className="supervisor-actions-list">
            {supervisor.last_actions.slice().reverse().map((a, i) => (
              <div key={i} className={`supervisor-action-item action-${a.action}`}>
                <span className="supervisor-action-comp">{a.component}</span>
                <span className="supervisor-action-verb">{a.action}</span>
                {a.result && <span className="supervisor-action-result">→ {a.result}</span>}
                {a.error && <span className="supervisor-action-error">⚠ {a.error}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cooldowns */}
      {supervisor?.cooldowns && Object.keys(supervisor.cooldowns).length > 0 && (
        <div className="supervisor-cooldowns">
          <h4>Active Cooldowns</h4>
          {Object.entries(supervisor.cooldowns).map(([name, secs]) => (
            <div key={name} className="supervisor-cooldown-row">
              <span>{name}</span>
              <span className="supervisor-cooldown-timer">{secs}s</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
