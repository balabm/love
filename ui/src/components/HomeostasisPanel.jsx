import { useState, useEffect, useCallback, useRef } from "react";
import api from "../api";
import "./HomeostasisPanel.css";

const PHASE_META = {
  wake:      { icon: "◎", label: "Wake",      color: "#fbbf24", desc: "Morning boot — sensors active, catching up on overnight events" },
  focus:     { icon: "◈", label: "Focus",     color: "#c084fc", desc: "Peak hours — deep work mode, sustained attention" },
  wind_down: { icon: "◑", label: "Wind Down", color: "#38bdf8", desc: "Winding down — lower intensity, reflection, prep for tomorrow" },
  sleep:     { icon: "☾", label: "Sleep",     color: "#818cf8", desc: "Sleep cycle — memory consolidation, evolution, dreaming" },
};

const DRIVE_META = {
  hunger:          { icon: "◻", color: "#fbbf24", desc: "Input hunger — how long since fresh data arrived" },
  fatigue:         { icon: "◐", color: "#f87171", desc: "Cognitive load — based on world-model free energy" },
  boredom:         { icon: "—", color: "#6b7280", desc: "Low surprise — LOVE needs something interesting" },
  curiosity:       { icon: "✦", color: "#a78bfa", desc: "Peak attention channel — something worth exploring" },
  loneliness:      { icon: "♡", color: "#ec4899", desc: "Time since user contact — proactive ping threshold" },
  dissatisfaction: { icon: "↓", color: "#f97316", desc: "Reward signal dropping — evolution cycle may trigger" },
};

function DriveBar({ name, value, dominant }) {
  const meta = DRIVE_META[name] || {};
  const pct = Math.round((value || 0) * 100);
  const isHigh = pct > 65;
  const isDom = dominant === name;
  return (
    <div className={`hms-drive ${isDom ? "hms-drive-dominant" : ""}`} title={meta.desc}>
      <div className="hms-drive-header">
        <span className="hms-drive-icon" style={{ color: meta.color }}>{meta.icon}</span>
        <span className="hms-drive-name">{name.replace("_", " ")}</span>
        {isDom && <span className="hms-dom-badge">dominant</span>}
        {isHigh && !isDom && <span className="hms-high-badge">high</span>}
        <span className="hms-drive-pct" style={{ color: isHigh ? meta.color : undefined }}>{pct}%</span>
      </div>
      <div className="hms-drive-track">
        <div
          className="hms-drive-fill"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${meta.color}66, ${meta.color})`,
            boxShadow: isHigh ? `0 0 8px ${meta.color}80` : "none",
          }}
        />
      </div>
    </div>
  );
}

function EnergyAccount({ name, account }) {
  if (!account) return null;
  const budget = account.budget_seconds_per_day || 600;
  const spent = account.spent_today || 0;
  const pct = Math.min(100, Math.round((spent / budget) * 100));
  const isThrottled = account.throttled;
  return (
    <div className={`hms-energy-row ${isThrottled ? "hms-throttled" : ""}`}>
      <div className="hms-energy-name">
        {isThrottled && <span className="hms-throttle-icon">⊘</span>}
        <span>{name}</span>
      </div>
      <div className="hms-energy-bar-wrap">
        <div className="hms-energy-bar">
          <div
            className="hms-energy-fill"
            style={{
              width: `${pct}%`,
              background: pct > 90 ? "#f87171" : pct > 70 ? "#fbbf24" : "#4ade80",
            }}
          />
        </div>
        <span className="hms-energy-pct">{pct}%</span>
      </div>
      <div className="hms-energy-numbers">
        {Math.round(spent)}s / {Math.round(budget)}s
      </div>
    </div>
  );
}

export default function HomeostasisPanel() {
  const [data, setData] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [overriding, setOverriding] = useState(false);
  const [tab, setTab] = useState("drives");
  const pollRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const [snap, hist] = await Promise.all([
        api.get("/homeostasis/snapshot"),
        api.get("/homeostasis/drives/history?hours=2").catch(() => ({ data: { entries: [] } })),
      ]);
      setData(snap.data);
      setHistory(hist.data?.entries || []);
    } catch (e) {
      console.error("HomeostasisPanel:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    pollRef.current = setInterval(load, 15000); // refresh every 15s
    return () => clearInterval(pollRef.current);
  }, [load]);

  const overridePhase = async (phase) => {
    setOverriding(true);
    try {
      await api.post("/homeostasis/circadian/override", { phase });
      await load();
    } catch (e) {
      console.error("Phase override failed:", e);
    } finally {
      setOverriding(false);
    }
  };

  const preserveModule = async (name) => {
    try {
      await api.delete(`/homeostasis/autophagy/${name}`);
      await load();
    } catch (e) {
      console.error("Preserve failed:", e);
    }
  };

  if (loading) return <div className="hms-loading">◌ Loading biological state...</div>;
  if (!data || data.error) return (
    <div className="hms-offline">
      <div className="hms-offline-icon">◎</div>
      <div>Homeostasis engine offline</div>
      <div className="hms-offline-hint">It starts automatically with the backend — check logs</div>
    </div>
  );

  const phase = PHASE_META[data.circadian_phase] || PHASE_META.wake;
  const drives = data.drives || {};
  const dominant = data.dominant_drive;
  const accounts = data.energy_accounts || {};
  const autophagyCandidates = data.autophagy_candidates || [];
  const autophagyReady = data.autophagy_ready || [];

  // Build sparkline data from history
  const sparkDrives = ["hunger", "fatigue", "loneliness", "dissatisfaction"];
  const sparkPoints = history.slice(-20).map(e => e.drives || {});

  return (
    <div className="hms-panel">
      {/* Header */}
      <div className="hms-header">
        <div>
          <h2 className="hms-title">Homeostasis</h2>
          <div className="hms-subtitle">LOVE's biological self-regulation</div>
        </div>
        <div className="hms-phase-badge" style={{ borderColor: phase.color + "60", color: phase.color }}>
          <span className="hms-phase-icon">{phase.icon}</span>
          <div>
            <div className="hms-phase-name">{phase.label}</div>
            <div className="hms-phase-desc">{phase.desc}</div>
          </div>
        </div>
      </div>

      {/* Phase override buttons */}
      <div className="hms-phase-row">
        <span className="hms-section-label">Override phase:</span>
        {Object.entries(PHASE_META).map(([key, m]) => (
          <button
            key={key}
            className={`hms-phase-btn ${data.circadian_phase === key ? "hms-phase-btn-active" : ""}`}
            style={data.circadian_phase === key ? { borderColor: m.color, color: m.color } : {}}
            onClick={() => overridePhase(key)}
            disabled={overriding}
          >
            {m.icon} {m.label}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="hms-tabs">
        {["drives", "energy", "autophagy"].map(t => (
          <button key={t} className={`hms-tab ${tab === t ? "hms-tab-active" : ""}`} onClick={() => setTab(t)}>
            {t === "drives" ? "◎ Drives" : t === "energy" ? "⚡ Energy" : "⊘ Autophagy"}
          </button>
        ))}
      </div>

      {/* Drives tab */}
      {tab === "drives" && (
        <div className="hms-drives-grid">
          {Object.entries(drives).map(([name, value]) => (
            <DriveBar key={name} name={name} value={value} dominant={dominant} />
          ))}
          {history.length > 0 && (
            <div className="hms-sparklines">
              <div className="hms-section-label">Drive trends (last 2h)</div>
              {sparkDrives.map(d => {
                const vals = sparkPoints.map(p => (p[d] || 0) * 100);
                if (!vals.length) return null;
                const max = Math.max(...vals, 1);
                const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * 160},${28 - (v / max) * 24}`).join(" ");
                const meta = DRIVE_META[d] || {};
                return (
                  <div key={d} className="hms-spark-row">
                    <span className="hms-spark-label" style={{ color: meta.color }}>{d}</span>
                    <svg viewBox="0 0 160 30" className="hms-sparkline">
                      <polyline points={pts} fill="none" stroke={meta.color} strokeWidth="1.5" strokeLinecap="round" />
                    </svg>
                    <span className="hms-spark-cur" style={{ color: meta.color }}>
                      {Math.round((drives[d] || 0) * 100)}%
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Energy tab */}
      {tab === "energy" && (
        <div className="hms-energy-section">
          <div className="hms-section-label">Daily compute budget per module (seconds)</div>
          {Object.keys(accounts).length === 0 ? (
            <div className="hms-empty">No modules registered yet. Modules register themselves on first use.</div>
          ) : (
            Object.entries(accounts).map(([name, acc]) => (
              <EnergyAccount key={name} name={name} account={acc} />
            ))
          )}
        </div>
      )}

      {/* Autophagy tab */}
      {tab === "autophagy" && (
        <div className="hms-autophagy-section">
          <div className="hms-section-label">Module deprecation candidates</div>
          {autophagyCandidates.length === 0 ? (
            <div className="hms-empty">No deprecation candidates. All modules are active.</div>
          ) : (
            autophagyCandidates.map(name => {
              const ready = autophagyReady.includes(name);
              return (
                <div key={name} className={`hms-autophagy-row ${ready ? "hms-autophagy-ready" : ""}`}>
                  <div className="hms-autophagy-info">
                    <span className="hms-autophagy-icon">{ready ? "⊘" : "◌"}</span>
                    <span className="hms-autophagy-name">{name}</span>
                    {ready && <span className="hms-autophagy-badge">ready to archive</span>}
                  </div>
                  <button className="hms-preserve-btn" onClick={() => preserveModule(name)}>
                    Preserve
                  </button>
                </div>
              );
            })
          )}
          {autophagyCandidates.length > 0 && (
            <div className="hms-autophagy-hint">
              Modules not invoked for 14+ days with low reward are flagged. Grace period: 7 days before archiving.
            </div>
          )}
        </div>
      )}

      {/* Running indicator */}
      <div className={`hms-running ${data.running ? "hms-running-live" : "hms-running-off"}`}>
        <span className="hms-running-dot" />
        {data.running ? "Homeostasis engine running" : "Engine not running — check backend startup"}
      </div>
    </div>
  );
}
