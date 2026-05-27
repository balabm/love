import { useState, useEffect, useCallback } from "react";
import api from "../api";
import "./WaveEngine.css";

const PRIORITY_COLOR = { high: "#f87171", medium: "#fbbf24", low: "#34d399" };
const STATUS_BADGE = { proposed: "pending", executed: "done" };

export default function WaveEngine() {
  const [status, setStatus] = useState(null);
  const [waves, setWaves] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [gaps, setGaps] = useState(null);
  const [tab, setTab] = useState("waves"); // waves | gaps

  const load = useCallback(async () => {
    try {
      const [s, w] = await Promise.all([
        api.get("/wave/status"),
        api.get("/wave/all"),
      ]);
      setStatus(s.data);
      setWaves(w.data || []);
    } catch (e) {
      console.error("WaveEngine load:", e);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const runScan = async () => {
    setScanning(true);
    try {
      const r = await api.post("/wave/scan");
      setGaps(r.data?.scan || null);
      await load();
      setTab("waves");
    } catch (e) {
      console.error("Scan error:", e);
    } finally {
      setScanning(false);
    }
  };

  const loadGaps = async () => {
    try {
      const r = await api.get("/wave/gaps");
      setGaps(r.data);
      setTab("gaps");
    } catch (e) {
      console.error("Gaps error:", e);
    }
  };

  const markExecuted = async (waveNum) => {
    try {
      await api.post(`/wave/execute/${waveNum}`);
      await load();
    } catch (e) {
      console.error("Execute error:", e);
    }
  };

  const proposed = waves.filter(w => w.status === "proposed");
  const executed = waves.filter(w => w.status === "executed");

  return (
    <div className="we-root">
      <div className="we-header">
        <div className="we-title-row">
          <h2 className="we-title">Wave Engine</h2>
          <div className="we-status-pills">
            <span className="we-pill">{waves.length} waves</span>
            <span className="we-pill we-pill-proposed">{proposed.length} proposed</span>
            <span className="we-pill we-pill-executed">{executed.length} executed</span>
          </div>
        </div>
        <p className="we-subtitle">
          LOVE's autonomous evolution loop — scans gaps, proposes the next Wave, tracks execution.
        </p>
        <div className="we-actions">
          <button className="we-btn we-btn-primary" onClick={runScan} disabled={scanning}>
            {scanning ? "Scanning..." : "Scan + Propose"}
          </button>
          <button className="we-btn" onClick={loadGaps}>View Gaps</button>
        </div>
        <div className="we-tabs">
          <button className={`we-tab${tab === "waves" ? " active" : ""}`} onClick={() => setTab("waves")}>Waves</button>
          <button className={`we-tab${tab === "gaps" ? " active" : ""}`} onClick={() => setTab("gaps")}>Gap Scan</button>
        </div>
      </div>

      {tab === "waves" && (
        <div className="we-waves">
          {waves.length === 0 && (
            <div className="we-empty">
              No waves yet. Hit "Scan + Propose" to let LOVE figure out what to build next.
            </div>
          )}
          {[...waves].reverse().map((w, i) => (
            <WaveCard key={i} wave={w} onExecute={markExecuted} />
          ))}
        </div>
      )}

      {tab === "gaps" && (
        <GapView gaps={gaps} />
      )}
    </div>
  );
}

function WaveCard({ wave, onExecute }) {
  const [expanded, setExpanded] = useState(false);
  const isProposed = wave.status === "proposed";

  return (
    <div className={`we-card ${wave.status}`}>
      <div className="we-card-header" onClick={() => setExpanded(e => !e)}>
        <div className="we-card-title-row">
          <span className={`we-card-status ${wave.status}`}>
            {wave.status === "proposed" ? "◉" : "✓"}
          </span>
          <span className="we-card-title">{wave.title}</span>
          <span className="we-card-priority" style={{ color: PRIORITY_COLOR[wave.priority] || "#94a3b8" }}>
            {wave.priority}
          </span>
        </div>
        <div className="we-card-meta">
          <span>Triggered by: {wave.trigger_category?.replace(/_/g, " ")}</span>
          <span>Gap score: {((wave.overall_gap_score || 0) * 100).toFixed(0)}%</span>
          <span>{new Date(wave.proposed_at).toLocaleDateString()}</span>
        </div>
      </div>

      {expanded && (
        <div className="we-card-body">
          <p className="we-card-desc">{wave.description}</p>
          <div className="we-features">
            <h4>Features</h4>
            <ul>
              {(wave.features || []).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
          {wave.trigger_gaps?.length > 0 && (
            <div className="we-trigger-gaps">
              <h4>Trigger Gaps</h4>
              {wave.trigger_gaps.map((g, i) => (
                <div key={i} className="we-gap-line">{g}</div>
              ))}
            </div>
          )}
          {isProposed && (
            <button className="we-btn we-btn-sm" onClick={() => onExecute(wave.wave_number)}>
              Mark as Executed
            </button>
          )}
          {wave.executed_at && (
            <div className="we-executed-info">
              Executed: {new Date(wave.executed_at).toLocaleString()} — {wave.outcome}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GapView({ gaps }) {
  if (!gaps) {
    return <div className="we-empty">No gap scan data. Click "View Gaps" or "Scan + Propose" first.</div>;
  }

  const gapList = gaps.gaps || [];
  const gapScore = ((gaps.overall_gap_score || 0) * 100).toFixed(0);
  const scores = gaps.scores || {};

  return (
    <div className="we-gap-view">
      <div className="we-gap-header">
        <div className="we-gap-score">
          <span className="we-gap-score-val">{gapScore}%</span>
          <span className="we-gap-score-lbl">overall gap</span>
        </div>
        <div className="we-domain-scores">
          {Object.entries(scores).map(([k, v]) => (
            <div key={k} className="we-domain-score">
              <span className="we-ds-val">{typeof v === "number" ? Math.round(v) : v}</span>
              <span className="we-ds-lbl">{k.replace(/_/g, " ")}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="we-gap-list">
        {gapList.length === 0 && <div className="we-empty">No gaps detected — looking good.</div>}
        {gapList.map((g, i) => (
          <div key={i} className="we-gap-item">
            <div className="we-gap-item-header">
              <span className="we-gap-domain">{g.domain}</span>
              <span className="we-gap-category">{g.category?.replace(/_/g, " ")}</span>
              <span className="we-gap-severity" style={{
                color: g.severity > 0.6 ? "#f87171" : g.severity > 0.3 ? "#fbbf24" : "#34d399"
              }}>
                {(g.severity * 100).toFixed(0)}%
              </span>
            </div>
            <p className="we-gap-desc">{g.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
