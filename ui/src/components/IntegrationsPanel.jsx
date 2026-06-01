import { useState, useEffect, useCallback } from "react";
import api, { API } from "../api";
import "./IntegrationsPanel.css";

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
  device_bridge: "teal",
};

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };
  return (
    <button className="int-copy-btn" onClick={handleCopy} title="Copy">
      {copied ? "Copied!" : label || "Copy"}
    </button>
  );
}

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
  const [tunnel, setTunnel] = useState(null);
  const [polling, setPolling] = useState(false);
  const [lastFetch, setLastFetch] = useState(null);
  const [error, setError] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [intRes, tunRes] = await Promise.allSettled([
        api.get("/neural/integrations/status"),
        api.get("/tunnel/status"),
      ]);
      if (intRes.status === "fulfilled") {
        setData(intRes.value.data);
      }
      if (tunRes.status === "fulfilled") {
        setTunnel(tunRes.value.data);
      }
      setLastFetch(new Date());
      setError(null);
    } catch (e) {
      console.error("[Integrations] status fetch failed:", e);
      setError("Backend offline — is LOVE running?");
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 60000);
    return () => clearInterval(t);
  }, [fetchStatus]);

  const triggerPoll = async () => {
    setPolling(true);
    try {
      await api.post(`/neural/integrations/poll`);
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

      {/* Phone Connection Section */}
      <div className="int-section-label">Phone Connection</div>
      <PhoneConnectCard tunnel={tunnel} />

      {/* Ntfy Connection Section */}
      <div className="int-section-label">Ntfy Notifications</div>
      <NtfyConnectCard data={data} />

      {/* Setup hint */}
      {optional.some(i => !i.configured) && (
        <div className="int-setup-hint">
          Some integrations need credentials. Open the <strong>Setup</strong> tab in the sidebar to connect them.
        </div>
      )}
    </div>
  );
}

function NtfyConnectCard({ data }) {
  const ntfyModule = (data?.integrations || []).find(i => i.id === "ntfy_bridge");
  
  return (
    <div className={`int-phone-card ${ntfyModule?.connected ? "int-phone-live" : "int-phone-missing"}`}>
      <div className="int-phone-header">
        <span className="int-phone-icon">🔔</span>
        <div className="int-phone-title">
          <strong>Ntfy Listener</strong>
          <span className="int-phone-sub">
            {ntfyModule?.connected ? "Listening for push notifications" : "NTFY_TOPIC not configured or listening failed"}
          </span>
        </div>
        <span className={`int-phone-status int-phone-status-${ntfyModule?.connected ? "live" : "missing"}`}>
          {ntfyModule?.connected ? "LIVE" : "MISSING"}
        </span>
      </div>

      <div className="int-phone-steps">
        <details>
          <summary>Setup steps</summary>
          <ol>
            <li>Install the <strong>ntfy</strong> app on your Android or iOS device</li>
            <li>In the app, subscribe to a unique topic (e.g. <code>love_agi_yourname</code>)</li>
            <li>In LOVE's <code>.env</code> file, set <code>NTFY_TOPIC=love_agi_yourname</code></li>
            <li>Restart LOVE. It will automatically connect and listen to that topic.</li>
            <li>(Optional) In ntfy app settings, enable "Forward incoming notifications" to send all your phone notifications to this topic.</li>
          </ol>
        </details>
      </div>
    </div>
  );
}

function PhoneConnectCard({ tunnel }) {
  const [zeroTouch, setZeroTouch] = useState(null);
  const [qr, setQr] = useState(null);

  useEffect(() => {
    const fetchExtras = async () => {
      try {
        const [ztRes, qrRes] = await Promise.allSettled([
          api.get("/learning/zero-touch"),
          api.get("/tunnel/qr"),
        ]);
        if (ztRes.status === "fulfilled") setZeroTouch(ztRes.value.data);
        if (qrRes.status === "fulfilled") setQr(qrRes.value.data);
      } catch (e) {
        console.error("[PhoneConnect] extras fetch failed:", e);
      }
    };
    fetchExtras();
  }, []);

  if (!tunnel) {
    return (
      <div className="int-phone-card int-phone-loading">
        Checking tunnel agent...
      </div>
    );
  }

  const url = tunnel.public_url || tunnel.url || "";
  const webhook = url ? `${url}/device/webhook` : null;
  const binaryOk = tunnel.cloudflared_available !== false;
  const running = tunnel.connected || tunnel.running || tunnel.status === "running";
  const tunnelName = tunnel.tunnel_name || "love";

  return (
    <div className={`int-phone-card ${running ? "int-phone-live" : binaryOk ? "int-phone-ready" : "int-phone-missing"}`}>
      <div className="int-phone-header">
        <span className="int-phone-icon">🌐</span>
        <div className="int-phone-title">
          <strong>Cloudflare Tunnel — {tunnelName}</strong>
          <span className="int-phone-sub">
            {running ? "Tunnel active — phone can connect anywhere" : binaryOk ? "cloudflared available but tunnel not running" : "cloudflared not installed or not authenticated"}
          </span>
        </div>
        <span className={`int-phone-status int-phone-status-${running ? "live" : binaryOk ? "ready" : "missing"}`}>
          {running ? "LIVE" : binaryOk ? "READY" : "MISSING"}
        </span>
      </div>

      {/* Tunnel details */}
      {tunnel.last_started && (
        <div className="int-phone-row">
          <span className="int-phone-label">Last started</span>
          <span className="int-phone-url">{new Date(tunnel.last_started).toLocaleString()}</span>
        </div>
      )}

      {/* URL row */}
      {webhook && (
        <div className="int-phone-row">
          <span className="int-phone-label">Webhook URL</span>
          <code className="int-phone-url">{webhook}</code>
          <CopyButton text={webhook} label="Copy" />
        </div>
      )}

      {/* QR code */}
      {qr?.qr_data && (
        <div className="int-phone-row">
          <span className="int-phone-label">QR Setup</span>
          <code className="int-phone-url int-phone-qr">{qr.qr_data}</code>
          <CopyButton text={qr.qr_data} label="Copy QR" />
        </div>
      )}

      {/* Action buttons */}
      <div className="int-phone-actions">
        {zeroTouch?.tasker_profile_xml && (
          <a
            className="int-phone-btn"
            href={`data:text/xml;charset=utf-8,${encodeURIComponent(zeroTouch.tasker_profile_xml)}`}
            download="love_tasker_profile.xml"
          >
            Download Tasker XML
          </a>
        )}
        {webhook && (
          <a
            className="int-phone-btn int-phone-btn-secondary"
            href={`data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(zeroTouch || {}, null, 2))}`}
            download="love_zero_touch.json"
          >
            Download Config JSON
          </a>
        )}
        {!binaryOk && (
          <div className="int-phone-missing-msg">
            <strong>Install cloudflared:</strong> <code>winget install Cloudflare.cloudflared</code><br/>
            <strong>Login:</strong> <code>cloudflared tunnel login</code> (browser auth)<br/>
            <strong>Then restart LOVE.</strong>
          </div>
        )}
        {binaryOk && !running && (
          <div className="int-phone-missing-msg">
            Tunnel not running. If using a named tunnel, run:<br/>
            <code>cloudflared service install &lt;TOKEN&gt;</code> (PowerShell as Admin)<br/>
            Or quick test: <code>cloudflared tunnel run {tunnelName}</code>
          </div>
        )}
      </div>

      {/* Setup instructions */}
      <div className="int-phone-steps">
        <details>
          <summary>Setup steps</summary>
          <ol>
            <li>Install <strong>cloudflared</strong>: <code>winget install Cloudflare.cloudflared</code></li>
            <li>Authenticate: <code>cloudflared tunnel login</code> (opens browser)</li>
            <li>Run <code>setup_tunnel.bat</code> or create tunnel in Cloudflare dashboard</li>
            <li>Get token from dashboard → <strong>Rotate token</strong></li>
            <li>Install service: <code>cloudflared service install &lt;TOKEN&gt;</code> (Admin PS)</li>
            <li>Restart LOVE — tunnel auto-starts</li>
            <li>Install <strong>Tasker</strong> on Android</li>
            <li>Import the downloaded XML profile, OR create:
              <ul>
                <li>Event → UI → Notification (all apps)</li>
                <li>Action → Net → HTTP Request</li>
                <li>Method: POST | URL: <code>{webhook || "(tunnel not ready)"}</code></li>
                <li>Body: <code>{`{"text":"%ntext","app":"%napp","title":"%ntitle","source":"phone_auto"}`}</code></li>
              </ul>
            </li>
          </ol>
        </details>
      </div>
    </div>
  );
}
