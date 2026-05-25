import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./IntegrationsPanel.css";

const API = "http://localhost:8000";

const ACCENT = {
  system:    "cyan",
  browser:   "blue",
  clipboard: "purple",
  finance:   "green",
  google:    "red",
  microsoft: "blue",
  github:    "orange",
  phone:     "pink",
  telegram:  "purple",
};

function StatusDot({ connected, configured }) {
  const state = connected ? "connected" : configured ? "configured" : "missing";
  return <span className={`int-dot int-dot-${state}`} title={state} />;
}

function EnvHint({ envKeys }) {
  if (!envKeys || envKeys.length === 0) return null;
  return (
    <div className="int-env-hint">
      {envKeys.map(k => (
        <code key={k} className="int-env-key">{k}</code>
      ))}
      <span className="int-env-label">required in .env</span>
    </div>
  );
}

function IntCard({ item, onPoll }) {
  const accent = ACCENT[item.id] || "blue";
  const stateClass = item.connected ? "int-card-connected"
                   : item.configured ? "int-card-configured"
                   : "int-card-missing";

  return (
    <div className={`int-card int-card-${accent} ${stateClass}`}>
      <div className="int-card-top">
        <span className="int-card-icon">{item.icon}</span>
        <div className="int-card-info">
          <div className="int-card-name">
            {item.label}
            <StatusDot connected={item.connected} configured={item.configured} />
          </div>
          <div className="int-card-desc">{item.description}</div>
        </div>
        <div className="int-card-badge">
          {item.connected
            ? <span className="int-badge int-badge-on">live</span>
            : item.always_on
              ? <span className="int-badge int-badge-warn">offline</span>
              : item.configured
                ? <span className="int-badge int-badge-warn">no data</span>
                : <span className="int-badge int-badge-off">not set</span>
          }
        </div>
      </div>

      {item.summary && (
        <div className="int-card-summary">{item.summary}</div>
      )}

      {!item.configured && !item.always_on && (
        <EnvHint envKeys={item.envKeys} />
      )}
    </div>
  );
}

function AlertBanner({ alerts }) {
  if (!alerts || alerts.length === 0) return null;
  return (
    <div className="int-alerts">
      {alerts.slice(0, 4).map((a, i) => (
        <div key={i} className="int-alert-row">
          <span className="int-alert-bullet">!!</span>
          <span className="int-alert-text">{a}</span>
        </div>
      ))}
    </div>
  );
}

export default function IntegrationsPanel() {
  const [data, setData] = useState(null);
  const [polling, setPolling] = useState(false);
  const [lastFetch, setLastFetch] = useState(null);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/neural/integrations/status`);
      setData(res.data);
      setLastFetch(new Date());
      setError(null);
    } catch (e) {
      console.error("[Integrations] status fetch failed:", e);
      setError("Backend offline — is LOVE running?");
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 30000);
    return () => clearInterval(t);
  }, [fetchStatus]);

  const triggerPoll = async () => {
    setPolling(true);
    try {
      await axios.post(`${API}/neural/integrations/poll`);
      await fetchStatus();
    } catch (e) {
      console.error("[Integrations] poll failed:", e);
    } finally {
      setPolling(false);
    }
  };

  if (error) {
    return (
      <div className="int-panel">
        <div className="int-offline">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="int-panel">
        <div className="int-loading">Checking integrations...</div>
      </div>
    );
  }

  const connected = data.connected_count || 0;
  const total = data.total || 0;
  const pct = total > 0 ? Math.round((connected / total) * 100) : 0;

  // Group: always-on vs needs credentials
  const alwaysOn = (data.integrations || []).filter(i => i.always_on);
  const optional = (data.integrations || []).filter(i => !i.always_on);

  return (
    <div className="int-panel">
      <div className="int-header">
        <div className="int-header-left">
          <h2>Integrations</h2>
          <div className="int-counter">
            <span className="int-counter-num" style={{ color: pct >= 70 ? "#4ade80" : pct >= 40 ? "#fbbf24" : "#f87171" }}>
              {connected}/{total}
            </span>
            <span className="int-counter-label">sources live</span>
          </div>
        </div>
        <div className="int-header-right">
          {lastFetch && (
            <span className="int-last-poll" onClick={fetchStatus} title="click to refresh">
              {lastFetch.toLocaleTimeString()}
            </span>
          )}
          <button
            className={`int-poll-btn${polling ? " int-polling" : ""}`}
            onClick={triggerPoll}
            disabled={polling}
          >
            {polling ? "Polling..." : "Poll Now"}
          </button>
        </div>
      </div>

      {/* Cross-source alerts from the hub */}
      <AlertBanner alerts={data.hub_alerts} />

      {/* Progress bar */}
      <div className="int-progress-wrap">
        <div className="int-progress-bar">
          <div
            className="int-progress-fill"
            style={{ width: `${pct}%`, background: pct >= 70 ? "#4ade80" : pct >= 40 ? "#fbbf24" : "#f87171" }}
          />
        </div>
        <span className="int-progress-label">{pct}% connected</span>
      </div>

      {/* Always-on sources */}
      <div className="int-section-label">Always-on</div>
      <div className="int-grid">
        {alwaysOn.map(item => (
          <IntCard key={item.id} item={item} />
        ))}
      </div>

      {/* Credential-gated integrations */}
      <div className="int-section-label">Account Integrations</div>
      <div className="int-grid">
        {optional.map(item => (
          <IntCard key={item.id} item={item} />
        ))}
      </div>

      {/* Setup hint */}
      {optional.some(i => !i.configured) && (
        <div className="int-setup-hint">
          Some integrations need credentials. Open the <strong>Setup</strong> tab in the sidebar to connect them.
        </div>
      )}
    </div>
  );
}
