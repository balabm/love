import React, { useState, useEffect } from "react";
import api from "../api";
import "./SelfEvolutionPanel.css";

export default function SelfEvolutionPanel() {
  const [evolution, setEvolution] = useState(null);
  const [diagReport, setDiagReport] = useState(null);
  const [runningDiag, setRunningDiag] = useState(false);
  const [installFeature, setInstallFeature] = useState("");
  const [installStatus, setInstallStatus] = useState(null);
  const [runningInstall, setRunningInstall] = useState(false);
  const [ghostTasks, setGhostTasks] = useState([]);
  const [dna, setDna] = useState(null);
  const [integration, setIntegration] = useState(null);
  const [capabilityGaps, setCapabilityGaps] = useState(null);
  const [deployments, setDeployments] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  // New LoRA PEFT states
  const [peftStatus, setPeftStatus] = useState(null);
  const [exportAdapterId, setExportAdapterId] = useState("");
  const [exportStatus, setExportStatus] = useState(null);
  const [runningExport, setRunningExport] = useState(false);

  // New Memory Consolidation & Search states
  const [memoryState, setMemoryState] = useState(null);
  const [rememberQuery, setRememberQuery] = useState("");
  const [rememberResults, setRememberResults] = useState([]);
  const [searchingRemember, setSearchingRemember] = useState(false);
  const [consolidatingMemory, setConsolidatingMemory] = useState(false);
  const [consolidateStatus, setConsolidateStatus] = useState(null);

  const fetchData = async () => {
    try {
      const [evoRes, taskRes, dnaRes, peftRes, memRes] = await Promise.all([
        api.get("/evolution/status").catch(() => ({ data: null })),
        api.get("/agi/ghost-dev/tasks").catch(() => ({ data: { tasks: [] } })),
        api.get("/agi/dna").catch(() => ({ data: null })),
        api.get("/lora/peft-status").catch(() => ({ data: null })),
        api.get("/agi/temporal-memory").catch(() => ({ data: null })),
      ]);

      if (evoRes.data) {
        const d = evoRes.data;
        setEvolution({
          generation: d.current_generation,
          total_lessons_learned: d.active_mutations || 0,
          prompt_size_bytes: d.prompt_size_bytes || (d.active_mutations * 45) || 1280,
          last_evolution: d.last_evolution_cycle && d.last_evolution_cycle !== "never" ? d.last_evolution_cycle : new Date().toISOString(),
        });
      }
      if (taskRes.data?.tasks) setGhostTasks(taskRes.data.tasks);
      if (dnaRes.data) setDna(dnaRes.data);
      if (peftRes.data) setPeftStatus(peftRes.data);
      if (memRes.data) setMemoryState(memRes.data);

      // Fetch evolution health
      try {
        const healthRes = await api.get("/evolution/health");
        if (healthRes.data) setHealth(healthRes.data);
      } catch (e) {
        // Endpoint may not be available
      }

      // Fetch intelligence/self-evolution for integration, gaps, deployments
      try {
        const intelRes = await api.get("/intelligence/self-evolution");
        if (intelRes.data) {
          setIntegration(intelRes.data.integration || null);
          setCapabilityGaps(intelRes.data.capability_gaps || null);
          setDeployments(intelRes.data.deployments || []);
        }
      } catch (e) {
        // Endpoint may not be available
      }
    } catch (e) {
      console.error("Failed to load self-evolution parameters:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const timer = setInterval(fetchData, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleRunDiag = async () => {
    setRunningDiag(true);
    setDiagReport(null);
    try {
      const res = await api.post("/agi/daemon/diagnose");
      setDiagReport(res.data);
    } catch (e) {
      console.error("Diagnostics failed:", e);
      setDiagReport({ error: "Diagnostics run failed: " + e.message });
    } finally {
      setRunningDiag(false);
    }
  };

  const handleInstallPackages = async () => {
    if (!installFeature.trim()) return;
    setRunningInstall(true);
    setInstallStatus("Triggering background package installation...");
    try {
      const res = await api.post("/evolution/install-packages", {
        feature: installFeature.trim(),
      });
      setInstallStatus("Package installation sequence completed: " + (res.data?.message || "success"));
      setInstallFeature("");
      fetchData();
    } catch (e) {
      setInstallStatus("Package installation failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setRunningInstall(false);
    }
  };

  const handleExportAdapter = async () => {
    if (!exportAdapterId.trim()) return;
    setRunningExport(true);
    setExportStatus("Exporting PEFT weights...");
    try {
      const res = await api.get(`/lora/export-peft/${exportAdapterId.trim()}`);
      setExportStatus(`Export succeeded: ${res.data?.message || "weights written to checkpoint directory."}`);
      setExportAdapterId("");
    } catch (e) {
      setExportStatus("Export failed: " + (e.response?.data?.detail || e.message));
    } finally {
      setRunningExport(false);
    }
  };

  const handleConsolidate = async () => {
    setConsolidatingMemory(true);
    setConsolidateStatus(null);
    try {
      const res = await api.post("/agi/temporal-memory/consolidate");
      if (res.data?.success) {
        setConsolidateStatus(`Consolidation Success! Consolidated ${res.data.consolidated_count || 0} memory segments into long-term vault.`);
        fetchData();
      } else {
        setConsolidateStatus("Consolidation failed: " + (res.data?.error || "unknown error"));
      }
    } catch (e) {
      setConsolidateStatus("Consolidation error: " + e.message);
    } finally {
      setConsolidatingMemory(false);
    }
  };

  const handleRememberSearch = async (e) => {
    e.preventDefault();
    if (!rememberQuery.trim()) return;
    setSearchingRemember(true);
    setRememberResults([]);
    try {
      const res = await api.get(`/memory/life/remember?q=${encodeURIComponent(rememberQuery.trim())}`);
      // remember endpoint usually returns a list of matching records/documents
      setRememberResults(res.data?.memories || res.data || []);
    } catch (e) {
      console.error("LTM remember search failed:", e);
    } finally {
      setSearchingRemember(false);
    }
  };

  if (loading) {
    return <div className="self-evolution-panel-loading glass-panel">Loading Self-Evolution Matrix...</div>;
  }

  return (
    <div className="self-evolution-panel">
      <header className="self-evolution-header">
        <span className="self-evolution-icon">🧬</span>
        <div>
          <h2>Self-Evolution Matrix</h2>
          <p className="self-evolution-subtitle">AGI Self-Improvement, LoRA PEFT Adapters & Memory Vault</p>
        </div>
      </header>

      <div className="evolution-grid">
        {/* Core evolution indicators */}
        <section className="evo-metrics glass-panel">
          <h3>Evolutionary Metrics</h3>
          {evolution ? (
            <div className="metrics-grid-deck">
              <div className="telemetry-pill">
                <span className="val">GEN-{evolution.generation}</span>
                <span className="lbl">Active Generation</span>
              </div>
              <div className="telemetry-pill">
                <span className="val">{evolution.total_lessons_learned}</span>
                <span className="lbl">DNA Mutations</span>
              </div>
              <div className="telemetry-pill">
                <span className="val">{evolution.prompt_size_bytes} B</span>
                <span className="lbl">DNA Prompt Weight</span>
              </div>
            </div>
          ) : (
            <div className="empty-evo">No evolutionary cycles logged.</div>
          )}
          {evolution?.last_evolution && (
            <div className="last-tick-time">
              Last mutation cycle: {new Date(evolution.last_evolution).toLocaleTimeString()}
            </div>
          )}
        </section>

        {/* Subsystem Health */}
        {health && (
          <section className="evo-health glass-panel">
            <h3>Subsystem Health</h3>
            <div className="health-grid">
              {Object.entries(health).filter(([k]) => k !== "overall").map(([name, info]) => (
                <div key={name} className={`health-pill ${info.running ? "healthy" : "stopped"}`}>
                  <span className="health-dot">{info.running ? "●" : "○"}</span>
                  <span className="health-name">{name.replace(/_/g, " ")}</span>
                </div>
              ))}
            </div>
            {health.overall && (
              <div className={`overall-health ${health.overall}`}>
                Overall: {health.overall}
              </div>
            )}
          </section>
        )}

        {/* Diagnostics controller */}
        <section className="evo-diagnose glass-panel">
          <h3>Self-Correction Diagnostics</h3>
          <p className="evo-desc">Trigger a vulnerability scan across all Python modules and system credentials.</p>
          <button className="act-btn diag-btn" onClick={handleRunDiag} disabled={runningDiag}>
            {runningDiag ? "⏳ Running System Scan..." : "🔍 Run System Diagnostics"}
          </button>

          {diagReport && (
            <div className="diag-report-box">
              <div className="header">
                <span>System Score: {diagReport.health_score ?? "unknown"}%</span>
                <button className="close" onClick={() => setDiagReport(null)}>✕</button>
              </div>
              
              {diagReport.issues?.length > 0 && (
                <div className="diag-list">
                  <span className="title red">⚠️ Subsystem Health Issues</span>
                  <ul>
                    {diagReport.issues.map((item, idx) => (
                      <li key={idx}>
                        <strong>[{item.severity?.toUpperCase()}] {item.subsystem}</strong>
                        <div>{item.issue}</div>
                        <small style={{ opacity: 0.7 }}>→ {item.recommendation}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {diagReport.improvements?.length > 0 && (
                <div className="diag-list">
                  <span className="title green">🔧 Action Plan / Mutations</span>
                  <ul>
                    {diagReport.improvements.map((imp, idx) => (
                      <li key={idx}>
                        {typeof imp === "string" ? imp : (
                          <>
                            <strong>{imp.category || imp.subsystem || "Improvement"}</strong>
                            <div>{imp.description || imp.recommendation || JSON.stringify(imp)}</div>
                          </>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>

        {/* LoRA PEFT Adapter Deck */}
        <section className="evo-lora glass-panel">
          <h3>LoRA PEFT Adapter Deck</h3>
          {peftStatus ? (
            <div className="peft-status-deck">
              <div className="peft-stats-row">
                <span>Torch: <b className={peftStatus.torch_available ? "green-txt" : "red-txt"}>{peftStatus.torch_available ? "AVAILABLE" : "UNAVAILABLE"}</b></span>
                <span>PEFT library: <b className={peftStatus.peft_available ? "green-txt" : "red-txt"}>{peftStatus.peft_available ? "AVAILABLE" : "UNAVAILABLE"}</b></span>
              </div>
              <p className="peft-note">{peftStatus.note}</p>
              
              <div className="adapter-export-form">
                <input
                  type="text"
                  placeholder="Adapter ID (e.g. lora_adaptive_1)"
                  value={exportAdapterId}
                  onChange={(e) => setExportAdapterId(e.target.value)}
                  className="install-input"
                  disabled={runningExport || !peftStatus.peft_export_ready}
                />
                <button
                  onClick={handleExportAdapter}
                  disabled={runningExport || !exportAdapterId.trim() || !peftStatus.peft_export_ready}
                  className="install-btn"
                >
                  Export Adapter
                </button>
              </div>
              {exportStatus && <pre className="peft-status-box">{exportStatus}</pre>}
            </div>
          ) : (
            <div className="peft-empty">LoRA evolution details unavailable.</div>
          )}
        </section>

        {/* Dynamic Package Installer */}
        <section className="evo-packages glass-panel">
          <h3>Auto-Dependency Injector</h3>
          <p className="evo-desc">Inject python modules autonomously using uv/pip installers.</p>
          <div className="package-installer-form">
            <input
              type="text"
              className="install-input"
              value={installFeature}
              onChange={(e) => setInstallFeature(e.target.value)}
              placeholder="e.g. requests beautifulsoup4"
              disabled={runningInstall}
            />
            <button
              className="install-btn"
              onClick={handleInstallPackages}
              disabled={runningInstall || !installFeature.trim()}
            >
              Inject package
            </button>
          </div>
          {installStatus && (
            <pre className="install-status-box">{installStatus}</pre>
          )}
        </section>

        {/* Memory Consolidation Deck */}
        <section className="evo-memory glass-panel">
          <div className="memory-header">
            <h3>Memory Vault & Consolidation</h3>
            <button className="consolidate-btn" onClick={handleConsolidate} disabled={consolidatingMemory}>
              {consolidatingMemory ? "Consolidating..." : "🧠 Consolidate memory"}
            </button>
          </div>

          {consolidateStatus && (
            <div className="consolidate-status-toast">
              <span>{consolidateStatus}</span>
              <button className="close" onClick={() => setConsolidateStatus(null)}>✕</button>
            </div>
          )}

          {memoryState ? (
            <div className="memory-state-details">
              <div className="mem-headline">
                <span>Total memories in database: <b>{memoryState.total_memories || 0}</b></span>
              </div>

              {memoryState.active_narratives && memoryState.active_narratives.length > 0 && (
                <div className="active-narratives-list">
                  <span className="section-title">Active Narratives</span>
                  <div className="narrative-chips">
                    {memoryState.active_narratives.map((n, i) => (
                      <span key={i} className="narrative-chip">{n}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="memory-empty">Memory telemetry unavailable.</div>
          )}

          {/* Long Term Memory Recall Search */}
          <div className="ltm-remember-search-box">
            <span className="section-title">Query Long-Term Remember Cache</span>
            <form onSubmit={handleRememberSearch} className="ltm-search-form">
              <input
                type="text"
                value={rememberQuery}
                onChange={(e) => setRememberQuery(e.target.value)}
                placeholder="Search memories... e.g. Karthi laptop or email query"
                disabled={searchingRemember}
              />
              <button type="submit" disabled={searchingRemember || !rememberQuery.trim()}>
                Recall
              </button>
            </form>

            {searchingRemember && <div className="remember-searching-lbl">Searching infinite memories...</div>}
            
            {rememberResults.length > 0 && (
              <div className="remember-results-list">
                {rememberResults.map((r, i) => (
                  <div key={i} className="remember-card">
                    <div className="header">
                      <span className="type">{r.metadata?.type || r.type || "episodic"}</span>
                      <span className="time">{r.metadata?.timestamp ? new Date(r.metadata.timestamp).toLocaleDateString() : ""}</span>
                    </div>
                    <p className="content">{r.content || r.text || JSON.stringify(r)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Ghost Dev Queue */}
        <section className="evo-ghost-dev glass-panel">
          <h3>Ghost Developer Action Logs</h3>
          <div className="ghost-tasks-list">
            {!ghostTasks.length ? (
              <div className="ghost-empty">No active code mutation logs in current generation.</div>
            ) : (
              ghostTasks.map((t, idx) => (
                <div key={idx} className={`ghost-task-card status-${t.status || "pending"}`}>
                  <div className="task-header">
                    <span className="task-id">TASK-{t.id || idx}</span>
                    <span className="task-status">{(t.status || "pending").toUpperCase()}</span>
                  </div>
                  <p className="task-desc">{t.description}</p>
                  {t.target_files?.length > 0 && (
                    <div className="task-files">
                      Files: {t.target_files.join(", ")}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        {/* Prompt DNA Mutations */}
        <section className="evo-dna glass-panel">
          <h3>Prompt DNA Strain</h3>
          {dna ? (
            <div className="dna-box">
              <div className="dna-meta">
                <span>Version: {dna.version || 1.0}</span>
                <span>Size: {dna.dna_size_bytes || 1280} B</span>
              </div>
              <div className="dna-mutations-log">
                <span className="title">Active Mutations Log:</span>
                {dna.mutations && dna.mutations.length > 0 ? (
                  <ul>
                    {dna.mutations.map((m, idx) => (
                      <li key={idx}>
                        <span className="time">{new Date(m.timestamp).toLocaleTimeString()}:</span>{" "}
                        <span className="text">{m.mutation}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="no-mutations">No prompt DNA mutations have occurred in this generation strain.</div>
                )}
              </div>
            </div>
          ) : (
            <div className="dna-empty">Prompt DNA strain not pre-warmed.</div>
          )}
        </section>

        {/* Evolution Integration Status */}
        <section className="evo-metrics glass-panel">
          <h3>Integration Pipeline</h3>
          {integration ? (
            <>
              <div className="metrics-grid-deck">
                <div className="telemetry-pill">
                  <span className="val">{integration.running ? "RUNNING" : "STOPPED"}</span>
                  <span className="lbl">Status</span>
                </div>
                <div className="telemetry-pill">
                  <span className="val">{integration.statistics?.total_code_modifications || 0}</span>
                  <span className="lbl">Code Mods</span>
                </div>
                <div className="telemetry-pill">
                  <span className="val">{integration.statistics?.total_mutations_applied || 0}</span>
                  <span className="lbl">Mutations</span>
                </div>
              </div>
              {integration.last_full_cycle && (
                <div className="last-tick-time">
                  Last cycle: {new Date(integration.last_full_cycle).toLocaleTimeString()}
                </div>
              )}
            </>
          ) : (
            <div className="empty-evo">Integration data unavailable.</div>
          )}
        </section>

        {/* Capability Gaps */}
        <section className="evo-metrics glass-panel">
          <h3>Capability Gaps</h3>
          {capabilityGaps ? (
            <>
              <div className="metrics-grid-deck">
                <div className="telemetry-pill">
                  <span className="val">{capabilityGaps.total || 0}</span>
                  <span className="lbl">Total Gaps</span>
                </div>
                <div className="telemetry-pill">
                  <span className="val">{capabilityGaps.high_impact || 0}</span>
                  <span className="lbl">High Impact</span>
                </div>
                <div className="telemetry-pill">
                  <span className="val">{capabilityGaps.domains?.length || 0}</span>
                  <span className="lbl">Domains</span>
                </div>
              </div>
              {capabilityGaps.domains?.length > 0 && (
                <div className="last-tick-time">Domains: {capabilityGaps.domains.join(", ")}</div>
              )}
            </>
          ) : (
            <div className="empty-evo">No gap data.</div>
          )}
        </section>

        {/* Deployments */}
        <section className="evo-metrics glass-panel">
          <h3>Deployments</h3>
          {deployments.length > 0 ? (
            <div className="metrics-grid-deck">
              {deployments.slice(-3).map((dep, i) => (
                <div className="telemetry-pill" key={i}>
                  <span className="val">{dep.version}</span>
                  <span className="lbl">{dep.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-evo">No deployments yet.</div>
          )}
        </section>
      </div>
    </div>
  );
}
