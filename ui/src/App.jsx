import { useState, useRef, useEffect, useCallback } from "react";
import api, { API } from "./api";
import Dashboard from "./components/Dashboard";
import ContextPanel from "./components/ContextPanel";
import GuardianWidget from "./components/GuardianWidget";
import EmotionalPanel from "./components/EmotionalPanel";
import ErrorBoundary from "./components/ErrorBoundary";
import FleetStatusWidget from "./components/FleetStatusWidget";
import MindPanel from "./components/MindPanel";
import SentinelPanel from "./components/SentinelPanel";
import SettingsManager from "./components/SettingsManager";
import SupervisorPanel from "./components/SupervisorPanel";
import TerminalPanel from "./components/TerminalPanel";



function ts() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDuration(ms) {
  const sec = Math.floor(ms / 1000);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function UptimeDisplay() {
  const [uptime, setUptime] = useState(0);
  const start = useRef(Date.now());
  useEffect(() => {
    const id = setInterval(() => setUptime(Date.now() - start.current), 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="uptime-pill">⏱ {formatDuration(uptime)}</span>;
}

function buildContextOverride(ctx) {
  if (!ctx) return "";
  const lines = [
    `Local time: ${ctx.local_time || "unknown"} (${ctx.time_of_day || "unknown"})`,
    `Activity: ${ctx.activity || "unknown"}`,
    `Active app: ${ctx.active_app || "unknown"}`,
    `Window: ${ctx.active_window || "unknown"}`,
    `Battery: ${ctx.battery != null ? `${Math.round(ctx.battery)}%` : "unknown"}`,
    `Work hours today: ${ctx.hours_worked ?? 0}`,
    `Overdue tasks: ${ctx.tasks_overdue ?? 0}`,
    `Tasks due today: ${ctx.tasks_due_today ?? 0}`,
    `Important unread emails: ${ctx.unread_important ?? 0}`,
    `In meeting: ${Boolean(ctx.is_in_meeting)}`,
    `Suggested action: ${ctx.suggested_action || "none"}`,
  ];
  if (ctx.alerts?.length) {
    lines.push(`Alerts: ${ctx.alerts.slice(0, 5).join(" | ")}`);
  }
  return `UI LIVE SNAPSHOT:\n${lines.join("\n")}`;
}

function ThinkingDot({ thinking }) {
  const [open, setOpen] = useState(false);
  if (!thinking) return null;
  return (
    <div className="thinking-wrap">
      <button className="thinking-toggle" onClick={() => setOpen(o => !o)}>
        ◈ {open ? "hide reasoning" : "show reasoning"}
      </button>
      {open && <pre className="thinking-body">{thinking}</pre>}
    </div>
  );
}

function ScorePill({ score }) {
  if (!score) return null;
  const color = score >= 70 ? "#34d399" : score >= 50 ? "#fbbf24" : "#f87171";
  return (
    <div className="score-pill" style={{ color, borderColor: color + "40" }}>
      <span className="score-num">{score}</span>
      <span className="score-lbl">life</span>
    </div>
  );
}

const QUICK = [
  { label: "What should I focus on right now?", icon: "◈" },
  { label: "How am I doing today?", icon: "♡" },
  { label: "What tasks are overdue?", icon: "◻" },
  { label: "Summarize my day so far", icon: "◷" },
];

export default function App() {
  const [view, setView] = useState("chat"); // chat | mind | dashboard | terminal | sentinel | supervisor
  const [messages, setMessages] = useState([{
    role: "love",
    text: "Hey Karthi. I'm watching everything — your PC, your schedule, your patterns. Just talk to me.",
    time: ts(),
    thinking: "",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("checking");
  const [wsStatus, setWsStatus] = useState("disconnected"); // connected | disconnected
  const [lifeScore, setLifeScore] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [ctx, setCtx] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);

  const wsRef = useRef(null);

  const connectWS = useCallback(() => {
    const wsUrl = API.replace(/^http/, "ws") + "/agi/companion/ws";
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        // Proactive push — inject into chat as a LOVE message
        if (msg.type === "THOUGHT" || msg.type === "PUSH" || msg.type === "NUDGE" || msg.type === "nudge" || msg.message) {
          const text = msg.message || msg.body || msg.content || JSON.stringify(msg);
          setMessages(p => [...p, { role: "love", text, time: ts(), push: true, thinking: "" }]);
        }
        // Alerts / interventions refresh
        if (msg.type === "alert" || msg.type === "device_update") {
          loadLive();
        }
      } catch {}
    };

    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => {
      setWsStatus("disconnected");
      // Auto-reconnect after 5s
      setTimeout(() => { if (wsRef.current === ws) connectWS(); }, 5000);
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    ping();
    loadLive();
    connectWS();
    const t = setInterval(loadLive, 30000);
    return () => {
      clearInterval(t);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  const ping = async () => {
    try { await api.get(`${API}/health`); setStatus("online"); }
    catch { setStatus("offline"); }
  };

  const loadLive = async () => {
    try {
      const [scoreRes, intRes, ctxRes] = await Promise.allSettled([
        api.get(`${API}/lifescore`),
        api.get(`${API}/orchestrator/interventions`),
        api.get(`${API}/context/summary`),
      ]);
      if (scoreRes.status === "fulfilled") setLifeScore(scoreRes.value.data.score);
      if (intRes.status === "fulfilled") setAlerts(intRes.value.data.interventions || []);
      if (ctxRes.status === "fulfilled") setCtx(ctxRes.value.data);
    } catch (e) { /* best-effort poll */ }
  };

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setMessages(p => [...p, { role: "user", text: msg, time: ts() }]);
    setInput("");
    setLoading(true);
    setView("chat");
    try {
      const contextOverride = buildContextOverride(ctx);
      const res = await api.post(`${API}/chat`, {
        text: msg,
        mode: "general",
        context_override: contextOverride,
        include_live_context: true,
      });
      setMessages(p => [...p, {
        role: "love",
        text: res.data.response,
        thinking: res.data.thinking || "",
        time: ts(),
      }]);
    } catch {
      setMessages(p => [...p, { role: "love", text: "Can't reach the backend. Is LOVE running?", time: ts() }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading, ctx]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const dismissAlert = async (id) => {
    try { await api.post(`${API}/orchestrator/dismiss/${id}`); }
    catch {}
    setAlerts(p => p.filter(a => a.id !== id));
  };

  const triggerAutoHeal = async () => {
    try {
      await api.post(`${API}/evolution/install-packages`, { feature: "google calendar gmail drive" });
      setMessages(p => [...p, { role: "love", text: "Installing Google packages now. I'll let you know when done.", time: ts() }]);
    } catch (e) { console.error("[LOVE] auto-heal failed:", e); }
  };

  return (
    <div className="app">
      <div className="orb orb1" /><div className="orb orb2" />

      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        {/* Identity */}
        <div className="logo">
          <span className="logo-heart">♥</span>
          <span className="logo-text">LOVE</span>
          <div className={`dot dot-${status}`} title={status} />
        </div>

        <div className="sidebar-meta">
          <UptimeDisplay />
        </div>

        <ScorePill score={lifeScore} />

        {/* Proactive alerts — LOVE speaks up */}
        {alerts.slice(0, 3).map(a => (
          <div key={a.id} className={`alert-card prio-${a.priority}`}>
            <span className="alert-text">{a.message}</span>
            <button className="alert-dismiss" onClick={() => dismissAlert(a.id)}>✕</button>
          </div>
        ))}

        {/* Context panel — LOVE SEES */}
        <ContextPanel />

        {/* Nav */}
        <nav className="nav">
          <button className={`nav-btn${view === "chat" ? " active" : ""}`} onClick={() => setView("chat")}>
            <span>◈</span> Chat
          </button>
          <button className={`nav-btn${view === "mind" ? " active" : ""}`} onClick={() => setView("mind")}>
            <span>🧠</span> Mind
          </button>
          <button className={`nav-btn${view === "dashboard" ? " active" : ""}`} onClick={() => setView("dashboard")}>
            <span>⊞</span> Pulse
          </button>
          <button className={`nav-btn${view === "terminal" ? " active" : ""}`} onClick={() => setView("terminal")}>
            <span>📟</span> Terminal
          </button>
          <button className={`nav-btn${view === "sentinel" ? " active" : ""}`} onClick={() => setView("sentinel")}>
            <span>◉</span> Sentinel
          </button>
          <button className={`nav-btn${view === "supervisor" ? " active" : ""}`} onClick={() => setView("supervisor")}>
            <span>🛡️</span> Supervisor
          </button>
          <button className={`nav-btn${view === "settings" ? " active" : ""}`} onClick={() => setView("settings")}>
            <span>⚙️</span> Settings
          </button>
        </nav>

        {/* Live context digest */}
        {ctx && (
          <div className="ctx-digest">
            {ctx.active_app && <span className="ctx-chip">▣ {ctx.active_app}</span>}
            {ctx.battery != null && <span className="ctx-chip">⚡ {ctx.battery}%</span>}
            {ctx.activity && <span className="ctx-chip">◉ {ctx.activity}</span>}
          </div>
        )}

        {/* Fleet status mini-widget */}
        <FleetStatusWidget onOpenSupervisor={() => setView("supervisor")} />

        {/* Work Guardian widget */}
        <GuardianWidget />

        {/* Emotional state */}
        <EmotionalPanel />
      </aside>

      {/* ── MAIN ── */}
      <main className="main">
        {view === "chat" && (
          <>
            {/* Messages */}
            <div className="messages" ref={null}>
              {messages.length === 1 && (
                <div className="quick-grid">
                  {QUICK.map((q, i) => (
                    <button key={i} className="quick-btn" onClick={() => send(q.label)}>
                      <span className="quick-icon">{q.icon}</span>
                      <span>{q.label}</span>
                    </button>
                  ))}
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className={`msg-row ${m.role}`}>
                  {m.role === "love" && <div className="avatar">♥</div>}
                  <div className="bubble-wrap">
                    {m.push && <div className="push-indicator">◉ proactive</div>}
                    <div className="bubble">{m.text}</div>
                    <div className="msg-meta">{m.time}</div>
                    <ThinkingDot thinking={m.thinking} />
                  </div>
                </div>
              ))}

              {loading && (
                <div className="msg-row love">
                  <div className="avatar">♥</div>
                  <div className="bubble-wrap">
                    <div className="bubble typing"><span /><span /><span /></div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="input-bar">
              <textarea
                ref={(el) => { textareaRef.current = el; inputRef.current = el; }}
                className="input-field"
                placeholder="Talk to LOVE…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                rows={1}
                autoComplete="off"
                autoCorrect="off"
                spellCheck="false"
                data-gramm="false"
              />
              <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>↑</button>
            </div>
          </>
        )}

        {view === "mind" && (
          <ErrorBoundary name="Mind"><div className="view-scroll"><MindPanel /></div></ErrorBoundary>
        )}

        {view === "dashboard" && (
          <ErrorBoundary name="Dashboard"><div className="view-scroll"><Dashboard /></div></ErrorBoundary>
        )}

        {view === "sentinel" && (
          <ErrorBoundary name="Sentinel"><div className="view-scroll"><SentinelPanel /></div></ErrorBoundary>
        )}

        {view === "terminal" && (
          <ErrorBoundary name="Terminal"><div className="view-scroll"><TerminalPanel /></div></ErrorBoundary>
        )}

        {view === "supervisor" && (
          <ErrorBoundary name="Supervisor"><div className="view-scroll"><SupervisorPanel /></div></ErrorBoundary>
        )}

        {view === "settings" && (
          <ErrorBoundary name="Settings"><div className="view-scroll"><SettingsManager /></div></ErrorBoundary>
        )}
      </main>
    </div>
  );
}
