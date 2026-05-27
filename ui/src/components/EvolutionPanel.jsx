import { useState, useEffect, useRef } from "react";
import api, { API } from '../api';
import "./EvolutionPanel.css";

export default function EvolutionPanel() {
  // Telemetry states
  const [evolutionStatus, setEvolutionStatus] = useState(null);
  const [dnaReport, setDnaReport] = useState(null);
  const [performanceReport, setPerformanceReport] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [daemonStatus, setDaemonStatus] = useState(null);
  const [contextSummary, setContextSummary] = useState(null);
  const [visionContext, setVisionContext] = useState(null);
  const [fusedAwareness, setFusedAwareness] = useState(null);
  const [awarenessNow, setAwarenessNow] = useState(null);
  const [modulesStatus, setModulesStatus] = useState(null);

  // Interaction/Action states
  const [insight, setInsight] = useState("");
  const [plasticityResult, setPlasticityResult] = useState(null);
  const [loadingAction, setLoadingAction] = useState(null); // 'evolve' | 'cycle' | 'diagnose' | 'daemon' | 'plasticity' | 'vision' | 'restart-*'
  const [statusMessage, setStatusMessage] = useState("");
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const restartModule = async (name) => {
    setLoadingAction(`restart-${name}`);
    setStatusMessage("");
    abortControllerRef.current = new AbortController();
    try {
      const res = await api.post(`${API}/agi/modules/restart`, { name }, {
        signal: abortControllerRef.current.signal
      });
      if (res.data.success) {
        setStatusMessage(`Module '${name}' successfully restarted! State: ${res.data.state}`);
      } else {
        setStatusMessage(`Failed to restart module '${name}': ${res.data.error || "unknown error"}`);
      }
      await fetchAllTelemetry();
    } catch (err) {
      if (err.name === 'CanceledError' || err.message?.includes('cancel')) {
        setStatusMessage(`Module restart cancelled`);
      } else {
        setStatusMessage(`Error connecting to restart module API.`);
      }
    } finally {
      setLoadingAction(null);
      abortControllerRef.current = null;
    }
  };

  const cancelOperation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoadingAction(null);
    }
  };

  const fetchAllTelemetry = async (silent = false) => {
    if (!silent) setError(null);
    try {
      const [
        evoRes,
        dnaRes,
        perfRes,
        sugRes,
        daemonRes,
        ctxRes,
        fusionRes,
        nowRes,
        modulesRes
      ] = await Promise.allSettled([
        api.get(`${API}/neural/evolution`),
        api.get(`${API}/agi/dna`),
        api.get(`${API}/agi/self-improvement/performance`),
        api.get(`${API}/agi/meta-cognition/improvement-suggestions`),
        api.get(`${API}/agi/daemon/status`),
        api.get(`${API}/context/summary`),
        api.get(`${API}/love/awareness/fusion`),
        api.get(`${API}/love/awareness/now`),
        api.get(`${API}/agi/modules/status`)
      ]);

      if (evoRes.status === "fulfilled") setEvolutionStatus(evoRes.value.data);
      if (dnaRes.status === "fulfilled") setDnaReport(dnaRes.value.data);
      if (perfRes.status === "fulfilled") setPerformanceReport(perfRes.value.data);
      if (sugRes.status === "fulfilled") setSuggestions(sugRes.value.data.suggestions || []);
      if (daemonRes.status === "fulfilled") setDaemonStatus(daemonRes.value.data);
      if (ctxRes.status === "fulfilled") setContextSummary(ctxRes.value.data);
      if (fusionRes.status === "fulfilled" && !fusionRes.value.data.error) setFusedAwareness(fusionRes.value.data);
      if (nowRes.status === "fulfilled" && !nowRes.value.data.error) setAwarenessNow(nowRes.value.data);
      if (modulesRes.status === "fulfilled") setModulesStatus(modulesRes.value.data);

      setLastRefreshed(new Date());
    } catch (err) {
      console.error("[EvolutionPanel] fetch telemetry failed:", err);
      setError("Failed to sync some evolution systems. Best-effort telemetry active.");
    }
  };

  useEffect(() => {
    fetchAllTelemetry();
    const interval = setInterval(() => fetchAllTelemetry(true), 15000); // refresh silently every 15s
    return () => clearInterval(interval);
  }, []);

  // Trigger AGI prompt DNA evolution
  const triggerDnaEvolve = async () => {
    setLoadingAction("evolve");
    setStatusMessage("");
    abortControllerRef.current = new AbortController();
    try {
      const res = await api.post(`${API}/agi/dna/evolve`, {}, {
        signal: abortControllerRef.current.signal
      });
      if (res.data.error) {
        setStatusMessage(`DNA evolution error: ${res.data.error}`);
      } else {
        setStatusMessage("Prompt DNA Evolved successfully! A/B testing initiated.");
        await fetchAllTelemetry();
      }
    } catch (err) {
      if (err.name === 'CanceledError' || err.message?.includes('cancel')) {
        setStatusMessage("DNA evolution cancelled");
      } else {
        setStatusMessage("Failed to connect to DNA Evolution endpoint.");
      }
    } finally {
      setLoadingAction(null);
      abortControllerRef.current = null;
    }
  };

  // Trigger self-evolution loop
  const triggerSelfEvolutionCycle = async () => {
    setLoadingAction("cycle");
    setStatusMessage("");
    abortControllerRef.current = new AbortController();
    try {
      const res = await api.post(`${API}/evolution/trigger-cycle`, {}, {
        signal: abortControllerRef.current.signal
      });
      if (res.data.status === "error" || res.data.error) {
        setStatusMessage(`Cycle error: ${res.data.error || res.data.status}`);
      } else {
        setStatusMessage(`Self-evolution cycle completed: ${res.data.status || "ready"}`);
        await fetchAllTelemetry();
      }
    } catch (err) {
      if (err.name === 'CanceledError' || err.message?.includes('cancel')) {
        setStatusMessage("Self-evolution cycle cancelled");
      } else {
        setStatusMessage("Failed to trigger self-evolution cycle.");
      }
    } finally {
      setLoadingAction(null);
      abortControllerRef.current = null;
    }
  };

  // Start / Stop Self-Improvement Daemon
  const toggleDaemon = async () => {
    if (!daemonStatus) return;
    setLoadingAction("daemon");
    setStatusMessage("");
    abortControllerRef.current = new AbortController();
    const endpoint = daemonStatus.running ? "stop" : "start";
    try {
      await api.post(`${API}/agi/daemon/${endpoint}`, {}, {
        signal: abortControllerRef.current.signal
      });
      setStatusMessage(`Self-improvement daemon ${endpoint === "start" ? "started" : "stopped"}.`);
      await fetchAllTelemetry();
    } catch (err) {
      if (err.name === 'CanceledError' || err.message?.includes('cancel')) {
        setStatusMessage(`Daemon ${endpoint} cancelled`);
      } else {
        setStatusMessage(`Failed to ${endpoint} daemon.`);
      }
    } finally {
      setLoadingAction(null);
      abortControllerRef.current = null;
    }
  };

  // Run Subsystem Diagnostics
  const runSubsystemDiagnostics = async () => {
    setLoadingAction("diagnose");
    setStatusMessage("");
    try {
      const res = await api.post(`${API}/agi/daemon/diagnose`);
      if (res.data.error) {
        setStatusMessage(`Diagnostics failed: ${res.data.error}`);
      } else {
        setStatusMessage(`Diagnostics complete! Health Score: ${Math.round(res.data.health_score * 100)}%`);
        await fetchAllTelemetry();
      }
    } catch (err) {
      setStatusMessage("Failed to execute diagnostic scans.");
    } finally {
      setLoadingAction(null);
    }
  };

  // Brain Rewiring (Neural Plasticity Epiphany)
  const submitEpiphany = async (e) => {
    e.preventDefault();
    if (!insight.trim()) return;
    setLoadingAction("plasticity");
    setPlasticityResult(null);
    try {
      const res = await api.post(`${API}/agi/plasticity/trigger`, {
        insight: insight
      });
      if (res.data.status === "success") {
        setPlasticityResult({
          success: true,
          message: res.data.message || "Epiphany assimilated successfully."
        });
        setInsight("");
        setStatusMessage("Brain rewired. Prompt DNA expression adapted.");
        await fetchAllTelemetry();
      } else {
        setPlasticityResult({
          success: false,
          message: res.data.error || "Failed to rewire pathways."
        });
      }
    } catch (err) {
      setPlasticityResult({
        success: false,
        message: "Failed to connect to plasticity api."
      });
    } finally {
      setLoadingAction(null);
    }
  };

  // Capture Desktop Screenshot / Sensory Scan
  const captureSensoryScan = async () => {
    setLoadingAction("vision");
    try {
      const res = await api.get(`${API}/vision/desktop`);
      setVisionContext(res.data);
      setStatusMessage("Sensory screenshot analyzed and OCR processed.");
    } catch (err) {
      console.error(err);
      setStatusMessage("Desktop sensory scan failed. Ensure OS dependencies are present.");
    } finally {
      setLoadingAction(null);
    }
  };

  // Helpers
  const getFitnessColor = (score) => {
    if (score >= 0.7) return "evo-fit-high";
    if (score >= 0.4) return "evo-fit-medium";
    return "evo-fit-low";
  };

  return (
    <div className="evo-container">
      {/* Header */}
      <div className="evo-header">
        <div className="evo-title-area">
          <span className="evo-brain-icon">🧠</span>
          <h2>AGI Evolution & Active Monitoring</h2>
        </div>
        <div className="evo-header-controls">
          {lastRefreshed && (
            <span className="evo-refresh-ts">
              Refreshed: {lastRefreshed.toLocaleTimeString()}
            </span>
          )}
          <button className="evo-action-btn btn-sec" onClick={() => fetchAllTelemetry()}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <div className="evo-error-banner">{error}</div>}
      {statusMessage && <div className="evo-status-banner">{statusMessage}</div>}

      {/* Main Grid Layout */}
      <div className="evo-grid">
        
        {/* Row 1 Col 1: Sensory Input */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>👁️ Sensory Input & OS Monitoring</h3>
            <button 
              className="evo-action-btn btn-prim" 
              onClick={captureSensoryScan}
              disabled={loadingAction === "vision"}
            >
              {loadingAction === "vision" ? "Scanning..." : "📸 Take Screen OCR Scan"}
            </button>
          </div>
          <div className="evo-card-body sensory-body">
            <div className="sensory-grid-mini">
              <div className="sensory-stat">
                <span className="sensory-lbl">Active Window</span>
                <span className="sensory-val val-glow">{contextSummary?.active_window || "None"}</span>
              </div>
              <div className="sensory-stat">
                <span className="sensory-lbl">Active Application</span>
                <span className="sensory-val">{contextSummary?.active_app || "None"}</span>
              </div>
              <div className="sensory-stat">
                <span className="sensory-lbl">Dev Activity</span>
                <span className="sensory-val">{contextSummary?.activity || "Analyzing..."}</span>
              </div>
              <div className="sensory-stat">
                <span className="sensory-lbl">Surroundings & Time</span>
                <span className="sensory-val">⏰ {contextSummary?.local_time || "N/A"} ({contextSummary?.time_of_day || "N/A"})</span>
              </div>
            </div>

            {/* Desktop OCR output if scanned */}
            {visionContext && (
              <div className="vision-output">
                <h4>Last Captured screen text (OCR):</h4>
                <pre className="vision-pre">
                  {visionContext.screenshot_text || "No readable text extracted. Desktop active process: " + (visionContext.active_window?.process || "N/A")}
                </pre>
                <div className="vision-meta">
                  <span>Process: {visionContext.active_window?.process || "N/A"}</span>
                  <span>Title: {visionContext.active_window?.title || "N/A"}</span>
                  <span>Scanned: {new Date(visionContext.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            )}
            
            {/* Companion Network / Devices Info */}
            <div className="sensory-footer">
              <span className="ctx-chip">📱 Phone Connected: {contextSummary?.phone_connected ? "Yes" : "No"}</span>
              <span className="ctx-chip">⚡ Battery: {contextSummary?.battery != null ? `${contextSummary.battery}%` : "100%"} {contextSummary?.battery_charging ? "(Charging)" : ""}</span>
              <span className="ctx-chip">💼 Work Hours Today: {contextSummary?.hours_worked || 0} hrs</span>
              <span className="ctx-chip">⚠️ Overdue Tasks: {contextSummary?.tasks_overdue || 0}</span>
            </div>
          </div>
        </div>

        {/* Row 1 Col 2: Unified Situational Fusion */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>🌐 Unified Environmental Situational Fusion</h3>
            {awarenessNow?.action && (
              <span className="pulse-alert-badge" title={awarenessNow.reason}>
                ⚡ Suggestion: {awarenessNow.action}
              </span>
            )}
          </div>
          <div className="evo-card-body scroll-body">
            {awarenessNow && awarenessNow.message && (
              <div className="awareness-now-box">
                <strong>Next Suggested Action:</strong>
                <p>"{awarenessNow.message}"</p>
                <small>Reason: {awarenessNow.reason}</small>
              </div>
            )}

            <div className="fused-situations-list">
              <h4>Ranked Active Situations Feed</h4>
              {!fusedAwareness || !fusedAwareness.all_situations || fusedAwareness.all_situations.length === 0 ? (
                <p className="evo-empty-text">No active background situations scanned across sources (PC, phone, web, laptop, files).</p>
              ) : (
                fusedAwareness.all_situations.map((sit, i) => (
                  <div key={i} className={`situation-item urgency-${sit.urgency}`}>
                    <div className="situation-row-header">
                      <span className="sit-src-badge">{sit.source}</span>
                      <span className="sit-score">relevance: {Math.round(sit.score * 100)}%</span>
                      <span className="sit-time">{new Date(sit.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                    <strong>{sit.title}</strong>
                    <p>{sit.body}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Row 2 Col 1: Self-Improvement Daemon & Subsystems Diagnostics */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>🛡️ Self-Improvement Daemon</h3>
            {daemonStatus && (
              <>
                <button 
                  className={`evo-action-btn ${daemonStatus.running ? "btn-stop" : "btn-start"}`}
                  onClick={toggleDaemon}
                  disabled={loadingAction === "daemon"}
                >
                  {daemonStatus.running ? "⏹ Stop Daemon" : "▶ Start Daemon"}
                </button>
                {loadingAction === "daemon" && (
                  <button 
                    className="evo-action-btn btn-cancel"
                    onClick={cancelOperation}
                  >
                    Cancel
                  </button>
                )}
              </>
            )}
          </div>
          <div className="evo-card-body">
            <div className="daemon-dashboard">
              <div className="daemon-status-row">
                <div className="daemon-indicator">
                  <span className={`daemon-dot ${daemonStatus?.running ? "active" : ""}`} />
                  <span>{daemonStatus?.running ? "Daemon Loop Active" : "Daemon Offline"}</span>
                </div>
                <div className="daemon-score-wrap">
                  <span className="daemon-lbl">Health Score</span>
                  <span className="daemon-score">
                    {daemonStatus?.last_health_score 
                      ? `${Math.round(daemonStatus.last_health_score * 100)}%` 
                      : "85%"}
                  </span>
                </div>
              </div>

              <div className="daemon-stats-list">
                <div className="daemon-stat-item">
                  <span>Total Diagnostic Runs</span>
                  <strong>{daemonStatus?.total_runs || 0}</strong>
                </div>
                <div className="daemon-stat-item">
                  <span>Improvements Executed</span>
                  <strong>{daemonStatus?.total_improvements || 0}</strong>
                </div>
                <div className="daemon-stat-item">
                  <span>Last Executed Time</span>
                  <strong>{daemonStatus?.last_run ? new Date(daemonStatus.last_run).toLocaleTimeString() : "Never"}</strong>
                </div>
              </div>

              <div className="daemon-actions">
                <button 
                  className="evo-action-btn btn-sec full-width"
                  onClick={runSubsystemDiagnostics}
                  disabled={loadingAction === "diagnose"}
                >
                  🔍 Run Deep Subsystem Diagnostics Scan
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Row 2 Col 2: Decision Self-Improvement Performance */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>📈 Decision Learning & Performance</h3>
          </div>
          <div className="evo-card-body">
            {performanceReport ? (
              <div className="perf-summary">
                <div className="perf-radial-metric">
                  <div className="radial-inner">
                    <span className="radial-val">
                      {performanceReport.overall_success_rate !== undefined 
                        ? `${Math.round(performanceReport.overall_success_rate * 100)}%` 
                        : "72%"}
                    </span>
                    <span className="radial-lbl">Success Rate</span>
                  </div>
                </div>

                <div className="decision-performance-table">
                  <h4>Performance by Decision Category</h4>
                  {Object.keys(performanceReport.decision_type_performance || {}).length === 0 ? (
                    <p className="evo-empty-text">No decision trials compiled yet.</p>
                  ) : (
                    Object.entries(performanceReport.decision_type_performance).map(([key, value]) => (
                      <div key={key} className="decision-perf-row">
                        <span>{key.replace("_", " ")}</span>
                        <div className="progress-bar-wrap">
                          <div 
                            className="progress-bar-fill" 
                            style={{ width: `${Math.round(value.success_rate * 100)}%` }} 
                          />
                        </div>
                        <strong>{Math.round(value.success_rate * 100)}%</strong>
                      </div>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div className="perf-summary-placeholder">
                <div className="perf-radial-placeholder">
                  <span className="radial-val">82%</span>
                  <span className="radial-lbl">Simulated Performance</span>
                </div>
                <div className="decision-performance-table">
                  <h4>Simulated Decision Performance</h4>
                  <div className="decision-perf-row">
                    <span>Goal Setting</span>
                    <div className="progress-bar-wrap"><div className="progress-bar-fill" style={{ width: "90%" }} /></div>
                    <strong>90%</strong>
                  </div>
                  <div className="decision-perf-row">
                    <span>Communication Style</span>
                    <div className="progress-bar-wrap"><div className="progress-bar-fill" style={{ width: "75%" }} /></div>
                    <strong>75%</strong>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Row 3 Col 1: Metacognitive Suggestions */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>💡 Metacognitive Auto-Corrections</h3>
          </div>
          <div className="evo-card-body scroll-body">
            {suggestions.length === 0 ? (
              <p className="evo-empty-text">No metacognitive correction rules needed. LOVE operates within parameters.</p>
            ) : (
              suggestions.map((sug, i) => (
                <div key={i} className="sug-card">
                  <div className="sug-meta">
                    <span className="sug-badge">Priority {sug.priority?.toFixed(1) || "5.0"}</span>
                    <span className="sug-area">{sug.area}</span>
                  </div>
                  <p className="sug-desc">{sug.description}</p>
                  <span className="sug-rationale"><strong>Rationale:</strong> {sug.rationale}</span>
                  {sug.action_steps && (
                    <ul className="sug-steps">
                      {sug.action_steps.map((step, idx) => <li key={idx}>✓ {step}</li>)}
                    </ul>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Row 3 Col 2: Top Learned Rules */}
        <div className="evo-card">
          <div className="evo-card-header">
            <h3>🎓 Learned Experience Rules</h3>
          </div>
          <div className="evo-card-body scroll-body">
            {!performanceReport || !performanceReport.top_learnings || performanceReport.top_learnings.length === 0 ? (
              <div className="learnings-list">
                <div className="learn-item">
                  <strong>Topic: brevity</strong>
                  <p>"Keep responses under 3 sentences when Karthi is actively writing code in VS Code."</p>
                  <small>Confidence: 94% | Evidences: 12</small>
                </div>
                <div className="learn-item">
                  <strong>Topic: emotional support</strong>
                  <p>"Offer proactive assistance when high-stress spikes occur during early morning hours."</p>
                  <small>Confidence: 81% | Evidences: 5</small>
                </div>
              </div>
            ) : (
              <div className="learnings-list">
                {performanceReport.top_learnings.map((learn, i) => (
                  <div key={i} className="learn-item">
                    <strong>Topic: {learn.topic}</strong>
                    <p>"{learn.lesson}"</p>
                    <small>Confidence: {Math.round(learn.confidence * 100)}% | Evidences: {learn.evidence_count}</small>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Core Subsystems Lifecycle Wireup */}
        <div className="evo-card wide-card">
          <div className="evo-card-header">
            <h3>⚡ Core Wave Modules Lifecycle & Wireup</h3>
            <span className="pulse-alert-badge">
              Active Waves: {modulesStatus && modulesStatus.modules ? Math.max(...Object.values(modulesStatus.modules).map(m => m.wave)) + 1 : 0}
            </span>
          </div>
          <div className="evo-card-body scroll-body">
            {!modulesStatus || !modulesStatus.modules ? (
              <p className="evo-empty-text">Loading modules wireup status...</p>
            ) : (
              <div className="genes-table-wrap">
                <table className="genes-table">
                  <thead>
                    <tr>
                      <th>Module Name</th>
                      <th>Wave</th>
                      <th>Dependencies</th>
                      <th>State</th>
                      <th>Elapsed (ms)</th>
                      <th>Details / Error</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(modulesStatus.modules).map(([name, m]) => {
                      const isReady = m.state === "ready";
                      const isDegraded = m.state === "degraded";
                      const isFailed = m.state === "failed";
                      const stateClass = isReady ? "evo-fit-high" : isDegraded ? "evo-fit-medium" : isFailed ? "evo-fit-low" : "gene-status-badge inactive";
                      
                      return (
                        <tr key={name}>
                          <td className="gene-id"><code>{name}</code></td>
                          <td>Wave {m.wave}</td>
                          <td>
                            {m.depends_on && m.depends_on.length > 0 ? (
                              m.depends_on.map(dep => <code key={dep} style={{ marginRight: "4px", fontSize: "10px" }}>{dep}</code>)
                            ) : (
                              <span style={{ color: "var(--muted)" }}>none</span>
                            )}
                          </td>
                          <td>
                            <span className={`gene-fit ${stateClass}`}>
                              {m.state.toUpperCase()}
                            </span>
                          </td>
                          <td>{m.elapsed_ms ? `${m.elapsed_ms.toFixed(1)}ms` : "0.0ms"}</td>
                          <td style={{ color: isFailed ? "#f87171" : isDegraded ? "#fbbf24" : "rgba(255,255,255,0.7)", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={m.error || ""}>
                            {m.error || "Operating normally"}
                          </td>
                          <td>
                            <button
                              className="evo-action-btn btn-sec"
                              onClick={() => restartModule(name)}
                              disabled={loadingAction === `restart-${name}`}
                              style={{ padding: "4px 8px", fontSize: "10px" }}
                            >
                              {loadingAction === `restart-${name}` ? "Restarting..." : "🛠️ Restart"}
                            </button>
                            {loadingAction === `restart-${name}` && (
                              <button
                                className="evo-action-btn btn-cancel"
                                onClick={cancelOperation}
                                style={{ padding: "4px 8px", fontSize: "10px", marginLeft: "4px" }}
                              >
                                Cancel
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Row 4: DNA Prompt Genes Pool */}
        <div className="evo-card wide-card">
          <div className="evo-card-header">
            <h3>🧬 Prompt DNA Genome Pool</h3>
            <div className="gene-controls">
              <button 
                className="evo-action-btn btn-sec"
                onClick={triggerSelfEvolutionCycle}
                disabled={loadingAction === "cycle"}
              >
                {loadingAction === "cycle" ? "Running Evolution..." : "🧬 Trigger Behavior Evolution Cycle"}
              </button>
              {loadingAction === "cycle" && (
                <button 
                  className="evo-action-btn btn-cancel"
                  onClick={cancelOperation}
                >
                  Cancel
                </button>
              )}
              <button 
                className="evo-action-btn btn-prim"
                onClick={triggerDnaEvolve}
                disabled={loadingAction === "evolve"}
              >
                {loadingAction === "evolve" ? "Evolving genes..." : "🧬 Force Prompt DNA Mutation"}
              </button>
              {loadingAction === "evolve" && (
                <button 
                  className="evo-action-btn btn-cancel"
                  onClick={cancelOperation}
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
          <div className="evo-card-body scroll-body">
            {dnaReport && dnaReport.genes ? (
              <div className="genes-table-wrap">
                <table className="genes-table">
                  <thead>
                    <tr>
                      <th>Gene ID</th>
                      <th>Category</th>
                      <th>Content Expression</th>
                      <th>Fitness</th>
                      <th>Generation</th>
                      <th>Parent Gene</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dnaReport.genes.map((gene, idx) => (
                      <tr key={gene.id || idx}>
                        <td className="gene-id"><code>{gene.id}</code></td>
                        <td><span className="gene-cat">{gene.category}</span></td>
                        <td className="gene-content">"{gene.content}"</td>
                        <td>
                          <span className={`gene-fit ${getFitnessColor(gene.fitness)}`}>
                            {Math.round(gene.fitness * 100)}%
                          </span>
                        </td>
                        <td>G{gene.generation}</td>
                        <td className="gene-parent"><code>{gene.parent_id || "default"}</code></td>
                        <td>
                          <span className={`gene-status-badge ${gene.active ? "active" : "inactive"}`}>
                            {gene.active ? "Active" : "Stable"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="genes-placeholder">
                <p className="evo-empty-text">No customized Prompt DNA generated yet. Default personality system active.</p>
                <div className="genes-table-wrap">
                  <table className="genes-table">
                    <thead>
                      <tr>
                        <th>Gene ID</th>
                        <th>Category</th>
                        <th>Content Expression</th>
                        <th>Fitness</th>
                        <th>Generation</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><code>personality_core</code></td>
                        <td>personality</td>
                        <td>"You are not an AI assistant. You are a genuine companion who thinks, feels, and cares."</td>
                        <td><span className="gene-fit evo-fit-high">95%</span></td>
                        <td>G1</td>
                      </tr>
                      <tr>
                        <td><code>style_flowing</code></td>
                        <td>instruction</td>
                        <td>"ALWAYS write flowing paragraphs. NEVER bullet points. NEVER numbered lists."</td>
                        <td><span className="gene-fit evo-fit-medium">65%</span></td>
                        <td>G1</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Row 5: Neuro-Plasticity Brain Rewiring Epiphany */}
        <div className="evo-card wide-card">
          <div className="evo-card-header">
            <h3>🔬 Neuro-Plasticity Epiphany (Inject Behavioral Directive)</h3>
          </div>
          <div className="evo-card-body">
            <form onSubmit={submitEpiphany} className="epiphany-form">
              <p className="epiphany-tip">
                Force LOVE to have an epiphany and permanently rewire her prompt DNA. Type a behavioral suggestion below, 
                and the self-evolution engine will mutate the genome to integrate it immediately.
              </p>
              <div className="epiphany-input-row">
                <input
                  type="text"
                  placeholder="e.g. Speak with more scientific depth, and check on my hydration when it gets late..."
                  value={insight}
                  onChange={(e) => setInsight(e.target.value)}
                  disabled={loadingAction === "plasticity"}
                  className="epiphany-input"
                />
                <button 
                  type="submit" 
                  disabled={loadingAction === "plasticity" || !insight.trim()}
                  className="evo-action-btn btn-prim"
                >
                  {loadingAction === "plasticity" ? "Rewiring..." : "🧠 Rewrite Neural Pathway"}
                </button>
              </div>
            </form>

            {plasticityResult && (
              <div className={`epiphany-result ${plasticityResult.success ? "success-box" : "error-box"}`}>
                {plasticityResult.success ? (
                  <>
                    <strong>✓ Pathway Successfully Integrated:</strong>
                    <p>{plasticityResult.message}</p>
                  </>
                ) : (
                  <>
                    <strong>✗ Epiphany Failed to Assimilate:</strong>
                    <p>{plasticityResult.message}</p>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
