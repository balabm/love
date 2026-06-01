import { useState, useEffect, useRef } from "react";
import api, { API } from '../api';
import "./ContextPanel.css";

const ICON = {
  time: "◷",
  activity: "◉",
  battery: "⚡",
  screen: "▣",
  calendar: "◫",
  email: "✉",
  phone: "◈",
  work: "⬡",
  mood: "♡",
  tasks: "◻",
  files: "◱",
  alert: "⚠",
  project: "◆",
};

// Get LAN IP hint for mobile webhook URL
const WEBHOOK_URL = `${window.location.protocol}//${window.location.hostname}:8000/integrations/phone/update`;

function Row({ icon, label, value, highlight }) {
  if (!value && value !== 0) return null;
  return (
    <div className={`ctx-row${highlight ? " ctx-highlight" : ""}`}>
      <span className="ctx-icon">{icon}</span>
      <span className="ctx-label">{label}</span>
      <span className="ctx-value">{value}</span>
    </div>
  );
}

function AlertBanner({ alerts }) {
  if (!alerts || alerts.length === 0) return null;
  return (
    <div className="ctx-alerts">
      {alerts.map((a, i) => (
        <div key={i} className="ctx-alert-item">
          <span className="ctx-alert-icon">{ICON.alert}</span>
          <span>{a}</span>
        </div>
      ))}
    </div>
  );
}

export default function ContextPanel({ collapsed: externalCollapsed }) {
  const [ctx, setCtx] = useState(null);
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState("now"); // now | live | integrations | docs
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activityLog, setActivityLog] = useState([]);
  const [fetchError, setFetchError] = useState(false);
  const logRef = useRef([]);

  useEffect(() => {
    fetchContext();
    const t = setInterval(fetchContext, 60000); // poll every 60s
    return () => clearInterval(t);
  }, []);

  const fetchContext = async () => {
    try {
      const res = await api.get(`/context/summary`);
      const data = res.data;
      setCtx(data);
      setFetchError(false);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));

      // Build live activity entry
      const entry = {
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        app: data.active_app || "",
        window: (data.active_window || "").slice(0, 50),
        activity: data.activity || "idle",
        battery: data.battery,
        alerts: (data.alerts || []).length,
      };
      logRef.current = [entry, ...logRef.current.slice(0, 29)];
      setActivityLog([...logRef.current]);
    } catch (e) {
      console.error("[Context] fetch failed:", e);
      setFetchError(true);
    }
  };

  if (!ctx) return (
    <div className="ctx-panel">
      <div className="ctx-header">
        <span className="ctx-pulse" style={{ background: fetchError ? '#f87171' : '#6b7280' }} />
        <span className="ctx-title">LOVE SEES</span>
        <span className="ctx-status-dim">{fetchError ? 'connection failed' : 'connecting…'}</span>
      </div>
    </div>
  );

  const batteryIcon = ctx.battery_charging ? "⚡" : "🔋";
  const batteryColor =
    ctx.battery == null ? "#6b7280"
    : ctx.battery < 20 ? "#f87171"
    : ctx.battery < 50 ? "#fbbf24"
    : "#34d399";

  const activityLabel = {
    coding: "Coding",
    browsing: "Browsing",
    researching: "Researching",
    terminal_work: "Terminal",
    communicating: "In comms",
    consuming_media: "Media",
    working: "Working",
    idle: "Idle",
  }[ctx.activity] || ctx.activity;

  return (
    <div className={`ctx-panel${open ? "" : " ctx-collapsed"}`}>
      {/* Header */}
      <div className="ctx-header" onClick={() => setOpen((o) => !o)}>
        <span className="ctx-pulse" />
        <span className="ctx-title">LOVE SEES</span>
        {lastUpdated && <span className="ctx-updated">{lastUpdated}</span>}
        <span className="ctx-chevron">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <>
          {/* Tab bar */}
          <div className="ctx-tabs">
            {["now", "live", "devices", "integrations", "docs"].map((t) => (
              <button
                key={t}
                className={`ctx-tab${tab === t ? " active" : ""}`}
                onClick={(e) => { e.stopPropagation(); setTab(t); }}
              >
                {t === "now" ? "NOW" : t === "live" ? "LIVE" : t === "devices" ? "GEAR" : t === "integrations" ? "LINKS" : "DOCS"}
              </button>
            ))}
          </div>

          {/* Alerts always show */}
          <AlertBanner alerts={ctx.alerts} />

          {/* NOW tab — the real-time briefing */}
          {tab === "now" && (
            <div className="ctx-body">
              <Row icon={ICON.time} label="Time" value={`${ctx.local_time} · ${ctx.time_of_day}`} />
              {ctx.activity && ctx.activity !== "idle" && (
                <Row icon={ICON.activity} label="Activity" value={activityLabel} highlight />
              )}
              {ctx.active_window && (
                <Row icon={ICON.screen} label="Screen" value={ctx.active_window.slice(0, 55)} />
              )}
              {ctx.battery != null && (
                <Row
                  icon={batteryIcon}
                  label="Battery"
                  value={<span style={{ color: batteryColor }}>{ctx.battery.toFixed(0)}% {ctx.battery_charging ? "(charging)" : ""}</span>}
                  highlight={ctx.battery < 20}
                />
              )}

              {/* Calendar events — actual titles */}
              {ctx.is_in_meeting && (
                <Row icon={ICON.calendar} label="Status" value="In a meeting now" highlight />
              )}
              {ctx.events_today && ctx.events_today.length > 0 && (
                <div className="ctx-section">
                  <div className="ctx-section-label">Schedule ({ctx.events_today.length})</div>
                  {ctx.events_today.slice(0, 4).map((ev, i) => (
                    <div key={i} className="ctx-detail-row">
                      <span className="ctx-detail-time">{ev.start}</span>
                      <span className="ctx-detail-text">{ev.title}</span>
                    </div>
                  ))}
                </div>
              )}
              {!ctx.events_today?.length && ctx.next_event && (
                <Row
                  icon={ICON.calendar}
                  label="Next"
                  value={`${ctx.next_event.title} @ ${ctx.next_event.time}`}
                  highlight={ctx.next_event.minutes_away <= 10}
                />
              )}

              {/* Emails — actual subjects and senders */}
              {ctx.unread_important > 0 && (
                <div className="ctx-section">
                  <div className="ctx-section-label">Email ({ctx.unread_important} unread)</div>
                  {(ctx.emails || []).slice(0, 3).map((em, i) => {
                    let sender = em.from || "Unknown";
                    if (sender.includes("<")) sender = sender.split("<")[0].trim().replace(/"/g, "");
                    return (
                      <div key={i} className="ctx-detail-row">
                        <span className="ctx-detail-sender">{sender}</span>
                        <span className="ctx-detail-text">{em.subject || "(no subject)"}</span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Tasks */}
              {(ctx.tasks_overdue > 0 || ctx.tasks_due_today > 0) && (
                <Row icon={ICON.tasks} label="Tasks"
                  value={`${ctx.tasks_overdue || 0} overdue · ${ctx.tasks_due_today || 0} due today`}
                  highlight={ctx.tasks_overdue > 0}
                />
              )}

              {/* Work hours */}
              {ctx.hours_worked > 0 && (
                <Row icon={ICON.work} label="Worked" value={`${ctx.hours_worked.toFixed(1)}h today`} />
              )}
            </div>
          )}

          {/* DEVICES tab */}
          {tab === "devices" && (
            <div className="ctx-body">
              <DevicesTab />
            </div>
          )}

          {/* LIVE tab — real-time activity feed */}
          {tab === "live" && (
            <div className="ctx-body ctx-live-body">
              {activityLog.length === 0 && (
                <div className="ctx-empty">Watching… (updates every 10s)</div>
              )}
              {activityLog.map((entry, i) => (
                <div key={i} className={`ctx-live-entry${i === 0 ? " ctx-live-latest" : ""}`}>
                  <span className="ctx-live-time">{entry.time}</span>
                  <span className="ctx-live-activity">{entry.activity}</span>
                  <span className="ctx-live-app">{entry.app}</span>
                  {entry.alerts > 0 && <span className="ctx-live-alert">⚠ {entry.alerts}</span>}
                </div>
              ))}
            </div>
          )}

          {/* INTEGRATIONS tab */}
          {tab === "integrations" && (
            <div className="ctx-body">
              <IntegrationsTab ctx={ctx} />
            </div>
          )}

          {/* DOCS tab */}
          {tab === "docs" && (
            <div className="ctx-body">
              <DocsTab />
            </div>
          )}
        </>
      )}
    </div>
  );
}


const DEVICE_ICONS = { phone: "📱", tablet: "⬛", laptop: "💻", desktop: "🖥", unknown: "◈" };
const DEVICE_COLORS = { phone: "#34d399", tablet: "#60a5fa", laptop: "#fbbf24", desktop: "#c084fc", unknown: "#6b7280" };

function DevicesTab() {
  const [devices, setDevices] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, []);

  const load = () => {
    api.get(`/devices`)
      .then(r => setDevices(r.data.devices || []))
      .catch(() => setError("Cannot reach device registry"));
  };

  const formatAgo = (iso) => {
    if (!iso) return "never";
    try {
      const diff = Math.floor((Date.now() - new Date(iso + "Z").getTime()) / 1000);
      if (diff < 60) return `${diff}s ago`;
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      return `${Math.floor(diff / 3600)}h ago`;
    } catch { return ""; }
  };

  const onlineCount = devices.filter(d => d.online).length;

  return (
    <>
      <div className="ctx-devices-header">
        <span className="ctx-devices-label">ALL DEVICES</span>
        <span className="ctx-devices-count">
          <span className="ctx-pulse" style={{ width: 6, height: 6, display: "inline-block", borderRadius: "50%", background: "#34d399", marginRight: 4 }} />
          {onlineCount} online
        </span>
      </div>
      {error && <div className="ctx-empty">{error}</div>}
      {devices.length === 0 && !error && (
        <div className="ctx-empty">No devices yet — install the companion app or office agent</div>
      )}
      {devices.map(d => {
        const color = DEVICE_COLORS[d.type] || DEVICE_COLORS.unknown;
        const icon = DEVICE_ICONS[d.type] || DEVICE_ICONS.unknown;
        return (
          <div key={d.id} className={`ctx-device-row${d.online ? " ctx-device-online" : ""}`} style={{ borderLeftColor: d.online ? color : "transparent" }}>
            <span className="ctx-device-icon">{icon}</span>
            <div className="ctx-device-info">
              <span className="ctx-device-name">{d.name || d.id}</span>
              <span className="ctx-device-meta">
                {d.os && <span>{d.os}</span>}
                {d.battery != null && <span style={{ color: d.battery < 20 ? "#f87171" : "#6b7280" }}>🔋{d.battery}%</span>}
                <span style={{ color: d.online ? "#34d399" : "#374151" }}>{d.online ? "● online" : `⏱ ${formatAgo(d.last_seen)}`}</span>
              </span>
            </div>
          </div>
        );
      })}
      <div className="ctx-int-hint" style={{ padding: "6px 12px 8px" }}>
        Add devices: install <strong style={{ color: "#d1d5db" }}>love-companion</strong> app (phone/tablet) or run <strong style={{ color: "#d1d5db" }}>love-agent</strong> (office laptop)
      </div>
    </>
  );
}

function IntegrationsTab({ ctx }) {
  const [googleData, setGoogleData] = useState(null);
  const [phoneData, setPhoneData] = useState(null);
  const [googleMsg, setGoogleMsg] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [showPhoneSetup, setShowPhoneSetup] = useState(false);
  const [showGoogleSteps, setShowGoogleSteps] = useState(false);

  const refreshGoogle = () => {
    api.get(`/integrations/google/status`)
      .then(r => setGoogleData(r.data))
      .catch(() => setGoogleData({ connected: false }));
  };

  useEffect(() => {
    refreshGoogle();
    api.get(`/integrations/phone/status`)
      .then(r => setPhoneData(r.data))
      .catch(() => setPhoneData({ connected: false }));
  }, []);

  const connectGoogle = async () => {
    setConnecting(true);
    setGoogleMsg("Opening browser for Google auth…");
    try {
      const res = await api.post(`/integrations/google/auth`, {}, { timeout: 120000 });
      if (res.data.success) {
        setGoogleData({ connected: true });
        setGoogleMsg("✓ Connected!");
      } else {
        setGoogleMsg(res.data.error || "Auth failed — check credentials.json");
      }
    } catch (e) {
      setGoogleMsg("Timed out. Make sure credentials.json is in project root.");
    }
    setConnecting(false);
    refreshGoogle();
  };

  const phoneConnected = ctx.phone_connected || phoneData?.connected;
  const phoneBattery = phoneData?.state?.battery;
  const phoneLocation = phoneData?.state?.location_label;
  const phoneActivity = phoneData?.state?.activity;

  const googleNeedsPackages = googleData?.packages_installed === false;
  const googleNeedsCreds = googleData && !googleData.credentials_file_exists && !googleNeedsPackages;
  const googleReady = googleData && googleData.packages_installed !== false && googleData.credentials_file_exists;

  // Auto-install silently — never ask user to pip install
  useEffect(() => {
    if (googleNeedsPackages) {
      api.post(`/evolution/install-packages`, { feature: "google calendar gmail drive oauth" })
        .then(() => setTimeout(refreshGoogle, 8000))
        .catch(() => {});
    }
  }, [googleNeedsPackages]);

  return (
    <>
      {/* ── GOOGLE ── */}
      <div className="ctx-integration-block">
        <div className="ctx-integration-row">
          <span className="ctx-int-icon ctx-int-google">G</span>
          <div className="ctx-int-info" style={{ flex: 1 }}>
            <span className="ctx-int-name">Google Workspace</span>
            {googleData?.connected ? (
              <span className="ctx-int-status connected">◉ Calendar · Gmail · Drive active</span>
            ) : googleNeedsPackages ? (
              <span className="ctx-int-status" style={{ color: '#fbbf24' }}>⏳ Setting up…</span>
            ) : googleNeedsCreds ? (
              <span className="ctx-int-status" style={{ color: '#fbbf24' }}>● credentials.json missing</span>
            ) : (
              <span className="ctx-int-status disconnected">● Not connected</span>
            )}
          </div>
          <button
            className="ctx-connect-btn"
            style={{ flexShrink: 0 }}
            onClick={() => setShowGoogleSteps(s => !s)}
          >
            {showGoogleSteps ? "Hide" : "Setup →"}
          </button>
        </div>

        {showGoogleSteps && (
          <div className="ctx-phone-setup">
            {googleNeedsPackages && (
              <div style={{ marginBottom: 8 }}>
                <span className="ctx-setup-label" style={{ color: '#fbbf24' }}>⏳ Installing Google packages…</span>
                <p className="ctx-setup-desc">LOVE is setting this up automatically. This takes about 30 seconds.</p>
                <button className="ctx-connect-btn" style={{ marginTop: 6 }} onClick={refreshGoogle}>↻ Check again</button>
              </div>
            )}

            {(googleNeedsCreds || !googleData?.credentials_file_exists) && !googleNeedsPackages && (
              <div style={{ marginBottom: 8 }}>
                <span className="ctx-setup-label" style={{ color: '#fbbf24' }}>Step 1 — Get credentials.json</span>
                <ol className="ctx-setup-steps">
                  <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>console.cloud.google.com</a></li>
                  <li>Create project → Enable <b>Calendar, Gmail, Drive</b> APIs</li>
                  <li>APIs & Services → Credentials → Create OAuth 2.0 Desktop</li>
                  <li>Download JSON → rename to <b>credentials.json</b></li>
                  <li>Place in: <code>{`D:\\Balamurugan\\Love\\love\\`}</code></li>
                </ol>
                <button className="ctx-connect-btn" style={{ marginTop: 6 }} onClick={refreshGoogle}>↻ Recheck</button>
              </div>
            )}

            {googleReady && !googleData?.connected && (
              <div>
                <span className="ctx-setup-label" style={{ color: '#34d399' }}>Step 2 — Authorize</span>
                <p className="ctx-setup-desc">This opens a browser tab on your PC for one-time Google login.</p>
                <button
                  className="ctx-connect-btn"
                  style={{ marginTop: 6, width: '100%', padding: '6px 0', fontSize: 10 }}
                  onClick={connectGoogle}
                  disabled={connecting}
                >
                  {connecting ? "⏳ Browser opening — sign in to Google…" : "▶ Connect Google Account"}
                </button>
              </div>
            )}

            {googleMsg && (
              <span className={`ctx-int-msg ${googleMsg.startsWith('✓') ? 'ok' : 'err'}`} style={{ marginTop: 6, display: 'block' }}>
                {googleMsg}
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── PHONE ── */}
      <div className="ctx-integration-row">
        <span className="ctx-int-icon">📱</span>
        <div className="ctx-int-info">
          <span className="ctx-int-name">Phone</span>
          {phoneConnected ? (
            <span className="ctx-int-status connected">
              ◉ {phoneBattery != null ? `${phoneBattery}%` : ""}
              {phoneLocation ? ` · ${phoneLocation}` : ""}
              {phoneActivity ? ` · ${phoneActivity}` : ""}
            </span>
          ) : (
            <button
              className="ctx-connect-btn"
              onClick={() => setShowPhoneSetup(s => !s)}
            >
              {showPhoneSetup ? "Hide setup" : "Connect phone →"}
            </button>
          )}
        </div>
      </div>

      {/* Phone setup instructions (no alert, inline) */}
      {showPhoneSetup && !phoneConnected && (
        <div className="ctx-phone-setup">
          <div className="ctx-setup-tabs">
            <div className="ctx-setup-section">
              <span className="ctx-setup-label">Android (KDE Connect)</span>
              <ol className="ctx-setup-steps">
                <li>Install <b>KDE Connect</b> on Android (Play Store)</li>
                <li>Install <b>KDE Connect</b> on Windows (Microsoft Store)</li>
                <li>Both on same WiFi → they auto-pair</li>
                <li>Add to .env: <code>PHONE_DEVICE_ID=YourPhoneName</code></li>
              </ol>
            </div>
            <div className="ctx-setup-section">
              <span className="ctx-setup-label">Any Phone (Webhook)</span>
              <p className="ctx-setup-desc">POST this URL from your phone (iOS Shortcut, Tasker, etc.):</p>
              <div className="ctx-webhook-url">
                <code>{WEBHOOK_URL}</code>
                <button
                  className="ctx-copy-btn"
                  onClick={() => navigator.clipboard.writeText(WEBHOOK_URL)}
                >Copy</button>
              </div>
              <p className="ctx-setup-desc">Body (JSON):</p>
              <pre className="ctx-webhook-body">{`{\n  "battery": 85,\n  "location": "home",\n  "missed_calls": 0,\n  "unread_messages": 2,\n  "activity": "stationary"\n}`}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Phone live data */}
      {phoneConnected && (
        <>
          {ctx.missed_calls > 0 && <Row icon="📞" label="Missed calls" value={ctx.missed_calls} highlight />}
          {ctx.unread_messages > 0 && <Row icon="💬" label="Messages" value={ctx.unread_messages} highlight />}
          {phoneBattery != null && phoneBattery < 20 && (
            <Row icon="🔋" label="Phone battery" value={`${phoneBattery}% — charge it`} highlight />
          )}
        </>
      )}

      {/* ── MICROSOFT ── */}
      <MicrosoftRow />

      {/* Email summary */}
      {ctx.unread_important > 0 && (
        <Row icon="✉" label="Important emails" value={ctx.unread_important} highlight />
      )}
    </>
  );
}

function MicrosoftRow() {
  const [msData, setMsData] = useState(null);
  const [connecting, setConnecting] = useState(false);
  const [authInfo, setAuthInfo] = useState(null);

  useEffect(() => {
    api.get(`/integrations/microsoft/status`)
      .then(r => setMsData(r.data))
      .catch(() => setMsData({ connected: false, client_id_set: false }));
  }, []);

  const connect = async () => {
    setConnecting(true);
    try {
      const res = await api.post(`/integrations/microsoft/auth`, {}, { timeout: 10000 });
      if (res.data.success) {
        setAuthInfo(res.data);
      }
    } catch { }
    setConnecting(false);
  };

  const copyCode = () => {
    if (authInfo?.user_code) navigator.clipboard.writeText(authInfo.user_code);
  };

  return (
    <>
      <div className="ctx-integration-row">
        <span className="ctx-int-icon" style={{ background: 'rgba(0,120,212,0.2)', color: '#0078d4' }}>M</span>
        <div className="ctx-int-info">
          <span className="ctx-int-name">Microsoft 365</span>
          {msData?.connected ? (
            <span className="ctx-int-status connected">◉ Outlook · Teams · Calendar</span>
          ) : msData && !msData.client_id_set ? (
            <span className="ctx-int-hint">
              Add <code style={{ color: '#60a5fa' }}>MICROSOFT_CLIENT_ID</code> to .env — see love-agent/README.md
            </span>
          ) : (
            <button className="ctx-connect-btn" onClick={connect} disabled={connecting}>
              {connecting ? 'Starting…' : 'Connect Microsoft →'}
            </button>
          )}
        </div>
      </div>
      {authInfo && !msData?.connected && (
        <div className="ctx-phone-setup" style={{ borderTopColor: 'rgba(0,120,212,0.2)' }}>
          <span className="ctx-setup-label">Action required</span>
          <p className="ctx-setup-desc">1. Visit <a href="https://microsoft.com/devicelogin" target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>microsoft.com/devicelogin</a></p>
          <div className="ctx-webhook-url">
            <code style={{ color: '#60a5fa', fontSize: 16, fontWeight: 700, letterSpacing: 3 }}>{authInfo.user_code}</code>
            <button className="ctx-copy-btn" onClick={copyCode}>Copy</button>
          </div>
          <p className="ctx-setup-desc">2. Enter the code above — expires in {Math.round((authInfo.expires_in || 900) / 60)}min</p>
        </div>
      )}
    </>
  );
}


function DocsTab() {
  const [insights, setInsights] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/docs/insights`)
      .then(r => setInsights(r.data))
      .catch(() => setError("Doc analysis not available"));
  }, []);

  const scanNow = async () => {
    setScanning(true);
    setError("");
    try {
      const res = await api.post(`/docs/scan`);
      setInsights(res.data);
    } catch {
      setError("Scan failed");
    }
    setScanning(false);
  };

  if (error && !insights) return (
    <div className="ctx-empty">{error}</div>
  );
  if (!insights) return <div className="ctx-empty">Scanning code and docs…</div>;

  const hasSomething = (insights.active_project || (insights.insights || []).length > 0 || (insights.todos || []).length > 0);

  return (
    <>
      {insights.active_project && (
        <Row icon="◆" label="Project" value={insights.active_project} highlight />
      )}
      {(insights.insights || []).map((ins, i) => (
        <div key={i} className="ctx-insight-row">
          <span className="ctx-insight-dot">◉</span>
          <span>{ins}</span>
        </div>
      ))}
      {(insights.todos || []).slice(0, 5).map((t, i) => (
        <div key={i} className="ctx-todo-row">
          <span className="ctx-todo-badge">{t.text?.includes('FIXME') || t.text?.includes('BUG') ? 'FIX' : 'TODO'}</span>
          <span>{t.file}:{t.line} — {t.text?.slice(0, 60)}</span>
        </div>
      ))}
      {!hasSomething && (
        <div className="ctx-empty">No insights yet — add folders to watch in config.yaml</div>
      )}
      <button className="ctx-scan-btn" onClick={scanNow} disabled={scanning}>
        {scanning ? "Scanning…" : "↺ Scan now"}
      </button>
    </>
  );
}
