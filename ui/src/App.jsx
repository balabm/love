import { useState, useRef, useEffect, useCallback } from "react";
import api, { API } from "./api";
import Dashboard from "./components/Dashboard";
import ErrorBoundary from "./components/ErrorBoundary";
import SettingsManager from "./components/SettingsManager";
import TelemetryHUD from "./components/TelemetryHUD";
import NeuralStream from "./components/NeuralStream";
import ConstellationMap from "./components/ConstellationMap";
import EvolutionHUD from "./components/EvolutionHUD";

// Import New Panel Components
import SwarmPanel from "./components/SwarmPanel";
import AutonomyPanel from "./components/AutonomyPanel";
import SelfEvolutionPanel from "./components/SelfEvolutionPanel";

// Import Additional AGI Components
import FinanceManager from "./components/FinanceManager";
import VoiceInterface from "./components/VoiceInterface";
import SupervisorPanel from "./components/SupervisorPanel";
import SentinelPanel from "./components/SentinelPanel";
import OrchestratorPanel from "./components/OrchestratorPanel";
import IntelligenceDashboard from "./components/IntelligenceDashboard";
import FocusMode from "./components/FocusMode";
import RitualView from "./components/RitualView";
import NotificationDashboard from "./components/NotificationDashboard";
import TerminalPanel from "./components/TerminalPanel";
import HomeostasisPanel from "./components/HomeostasisPanel";
import IntegrationsPanel from "./components/IntegrationsPanel";
import SetupWizard from "./components/SetupWizard";
import ZeroBloatDashboard from "./components/ZeroBloatDashboard";

// Orphaned panels — now integrated
import LifeDomains from "./components/LifeDomains";
import BriefingPanel from "./components/BriefingPanel";
import EvolutionPanel from "./components/EvolutionPanel";
import NeuralMesh from "./components/NeuralMesh";
import MindPanel from "./components/MindPanel";
import WaveEngine from "./components/WaveEngine";
import ContextPanel from "./components/ContextPanel";
import EmotionalPanel from "./components/EmotionalPanel";
import AgentLoopPanel from "./components/AgentLoopPanel";
import FleetStatusWidget from "./components/FleetStatusWidget";
import GuardianWidget from "./components/GuardianWidget";

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

const QUICK = [
  { label: "What should I focus on right now?", icon: "◈" },
  { label: "How am I doing today?", icon: "♡" },
  { label: "What tasks are overdue?", icon: "◻" },
  { label: "Summarize my day so far", icon: "◷" },
];

export default function App() {
  const [view, setView] = useState("chat");
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [messages, setMessages] = useState([{
    role: "love",
    text: "Hey Karthi. I'm watching everything — your PC, your schedule, your patterns. Just talk to me.",
    time: ts(),
    thinking: "",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("checking");
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [lifeScore, setLifeScore] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [ctx, setCtx] = useState(null);
  const [evolution, setEvolution] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [consciousness, setConsciousness] = useState(null);
  const [autonomyMode, setAutonomyMode] = useState("balanced");
  const [zeroBloat, setZeroBloat] = useState(true);

  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);
  const wsRef = useRef(null);
  const voiceRef = useRef(null);
  const chatTimeoutRef = useRef(null);
  const wsRetryCount = useRef(0);
  const wsRetryTimer = useRef(null);

  // Sub-view states for modular dashboards
  const [autonomySubView, setAutonomySubView] = useState("wave"); // wave | supervisor | sentinel | orchestrator | intelligence | consciousness | emotions | context | mesh
  const [pulseSubView, setPulseSubView] = useState("lifelog"); // lifelog | domains | focus | ritual | briefing | homeostasis
  const [cosmosSubView, setCosmosSubView] = useState("map"); // map | notifications | integrations
  const [evolutionSubView, setEvolutionSubView] = useState("matrix"); // matrix | advanced | terminal
  const [swarmSubView, setSwarmSubView] = useState("swarm"); // swarm | agents

  const connectWS = useCallback(() => {
    const apiKey = import.meta.env.VITE_API_KEY || "love-dev-key";
    const sep = API.includes("?") ? "&" : "?";
    const wsUrl = API.replace(/^http/, "ws") + "/agi/companion/ws" + sep + "api_key=" + apiKey;
    setWsStatus("connecting");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "THOUGHT" || msg.type === "PUSH" || msg.type === "NUDGE" || msg.type === "nudge" || msg.message) {
          const text = msg.message || msg.body || msg.content || JSON.stringify(msg);
          setMessages(p => [...p, { role: "love", text, time: ts(), push: true, thinking: "" }]);
        }
        if (msg.type === "monologue") {
          // Do not spam the main chat with internal monologues.
        }
        if (msg.type === "state_sync") {
          if (msg.context) {
            setCtx(prev => ({
              ...prev,
              active_app: msg.context.activity || prev?.active_app,
              active_window: msg.context.active_window || prev?.active_window,
              system_cpu: msg.context.cpu_percent || prev?.system_cpu,
              stress_score: msg.context.stress_score || prev?.stress_score,
            }));
          }
          if (msg.consciousness) {
            setConsciousness(msg.consciousness);
          }
        }
        if (msg.type === "alert" || msg.type === "device_update") {
          loadLive();
        }
        if (msg.type === "connection_established") {
          wsRetryCount.current = 0;
        }
      } catch {}
    };

    ws.onopen = () => {
      setWsStatus("connected");
      wsRetryCount.current = 0;
    };
    ws.onclose = () => {
      setWsStatus("disconnected");
      if (wsRetryTimer.current) clearTimeout(wsRetryTimer.current);
      const backoff = Math.min(30000, 2000 * Math.pow(2, wsRetryCount.current));
      wsRetryCount.current += 1;
      wsRetryTimer.current = setTimeout(() => {
        if (wsRef.current === ws && wsRetryCount.current < 20) connectWS();
      }, backoff);
    };
    ws.onerror = () => {
      if (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    ping();
    loadLive();
    connectWS();
    const t = setInterval(loadLive, 60000); // Poll every 60s to reduce backend load
    return () => {
      clearInterval(t);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
      const [scoreRes, intRes, ctxRes, evoRes, predRes, conRes, polRes] = await Promise.allSettled([
        api.get(`${API}/lifescore`),
        api.get(`${API}/orchestrator/interventions`),
        api.get(`${API}/context/summary`),
        api.get(`${API}/evolution/status`),
        api.get(`${API}/intelligence/predictions`),
        api.get(`${API}/agi/consciousness`),
        api.get(`${API}/agi/autonomy-policy`),
      ]);
      if (scoreRes.status === "fulfilled") setLifeScore(scoreRes.value.data.score);
      if (intRes.status === "fulfilled") setAlerts(intRes.value.data.interventions || []);
      if (ctxRes.status === "fulfilled") setCtx(ctxRes.value.data);
      if (conRes.status === "fulfilled" && !conRes.value.data.error) setConsciousness(conRes.value.data);
      if (polRes.status === "fulfilled" && !polRes.value.data.error) setAutonomyMode(polRes.value.data.mode);
      if (evoRes.status === "fulfilled") {
        const d = evoRes.value.data;
        setEvolution({
          generation: d.current_generation,
          total_lessons_learned: d.active_mutations || 0,
          prompt_size_bytes: d.prompt_size_bytes || (d.active_mutations * 45) || 1280,
          last_evolution: d.last_evolution_cycle && d.last_evolution_cycle !== "never" ? d.last_evolution_cycle : new Date().toISOString(),
        });
      }
      if (predRes.status === "fulfilled") setPredictions(predRes.value.data);
    } catch (e) { /* best-effort poll */ }
  };

  const changeAutonomyPolicy = async (mode) => {
    try {
      await api.post(`${API}/agi/autonomy-policy/mode`, { mode });
      setAutonomyMode(mode);
    } catch (e) {
      console.error("Failed to change policy mode:", e);
    }
  };

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setMessages(p => [...p, { role: "user", text: msg, time: ts() }]);
    setInput("");
    setLoading(true);
    setView("chat");
    chatTimeoutRef.current = setTimeout(() => {
      setLoading(false);
      setMessages(p => [...p, { role: "love", text: "Response timed out — backend may be overloaded. Try again.", time: ts() }]);
    }, 35000);
    try {
      const contextOverride = buildContextOverride(ctx);
      const res = await api.post(`${API}/chat`, {
        text: msg,
        mode: "general",
        context_override: contextOverride,
        include_live_context: true,
      });
      clearTimeout(chatTimeoutRef.current);
      setMessages(p => [...p, {
        role: "love",
        text: res.data.response,
        thinking: res.data.thinking || "",
        time: ts(),
      }]);
      if (res.data?.response) {
        voiceRef.current?.speakText(res.data.response);
      }
    } catch {
      clearTimeout(chatTimeoutRef.current);
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

  return (
    <div className="app-container">
      <div className="orb orb1" />
      <div className="orb orb2" />

      {/* ── HORIZON TOP NAVIGATION BAR ── */}
      <header className="horizon-nav">
        {/* Identity & Status */}
        <div className="logo-group">
          <div className="logo">
            <span className="logo-heart">♥</span>
            <span className="logo-text">LLOVE</span>
            <span className="logo-sub">AGI</span>
            <div className={`dot dot-${status}`} title={status} />
          </div>
        </div>

        {/* Global HUD Stats */}
        <div className="global-hud-stats">
          <div className="stat-capsule policy-capsule">
            <span className="lbl">Mode</span>
            <select
              value={autonomyMode}
              onChange={(e) => changeAutonomyPolicy(e.target.value)}
              className={`policy-select ${autonomyMode}`}
            >
              <option value="safe">SAFE</option>
              <option value="balanced">BALANCED</option>
              <option value="aggressive">AGGRESSIVE</option>
            </select>
          </div>

          <div className="stat-capsule">
            <span className="val-glowing">
              {consciousness?.emotional_state?.primary_emotion?.toUpperCase() || "STANDBY"}
            </span>
          </div>

          <div className="stat-capsule score-capsule">
            <span className="val-glowing pink">{lifeScore ?? "—"}</span>
          </div>

          <div className="stat-capsule hidden-mobile">
            <UptimeDisplay />
          </div>

          <div className="stat-capsule ws-capsule" title={wsStatus === "connected" ? "WebSocket Connected" : "WebSocket Disconnected"}>
            <span className={`ws-dot ${wsStatus === "connected" ? "online" : "offline"}`} />
          </div>
          <button
            className="stat-capsule"
            onClick={() => setZeroBloat(z => !z)}
            title={zeroBloat ? "Switch to Full UI" : "Switch to Zero-Bloat Telemetry"}
            style={{ opacity: 0.7, cursor: "pointer", background: "rgba(255,255,255,0.04)" }}
          >
            {zeroBloat ? "⛶" : "◈"}
          </button>
        </div>

        {/* Navigation Tabs */}
        <nav className="horizon-tabs">
          <button className={`nav-tab-btn ${view === "chat" ? "active" : ""}`} onClick={() => setView("chat")} title="Commands Stream">
            ◈ {zeroBloat ? "TERMINAL" : "STREAM"}
          </button>
          <button className={`nav-tab-btn ${view === "swarm" ? "active" : ""}`} onClick={() => setView("swarm")} title="Coordinated Multi-Agent Swarm">
            🐝 SWARM
          </button>
          <button className={`nav-tab-btn ${view === "mind" ? "active" : ""}`} onClick={() => setView("mind")} title="Autonomy & Mind Supervisor">
            🧠 AUTONOMY
          </button>
          <button className={`nav-tab-btn ${view === "evolution" ? "active" : ""}`} onClick={() => setView("evolution")} title="DNA Prompt Evolution & Self Improvement">
            🧬 EVOLUTION
          </button>
          <button className={`nav-tab-btn ${view === "biometrics" ? "active" : ""}`} onClick={() => setView("biometrics")} title="Wellness & Physiological Homeostasis">
            ⊞ Pulse
          </button>
          <button className={`nav-tab-btn ${view === "finance" ? "active" : ""}`} onClick={() => setView("finance")} title="Finance Guardian & Autonomous Trading">
            💸 FINANCE
          </button>
          <button className={`nav-tab-btn ${view === "constellation" ? "active" : ""}`} onClick={() => setView("constellation")} title="Connected Device topology">
            🔌 COSMOS
          </button>
          <button className={`nav-tab-btn ${view === "setup" ? "active" : ""}`} onClick={() => setView("setup")} title="Setup Wizard — Connect integrations">
            🔧 SETUP
          </button>
          <button className={`nav-tab-btn ${view === "settings" ? "active" : ""}`} onClick={() => setView("settings")} title="Settings Controller">
            ⚙️ SETTINGS
          </button>
        </nav>
      </header>

      {/* ── DENSE 3-PANE HUD CONTENT AREA ── */}
      <div className={`hud-content-container ${leftCollapsed ? 'left-collapsed' : ''} ${rightCollapsed ? 'right-collapsed' : ''}`}>
        {/* Left Wing */}
        <aside className={`hud-wing left-wing ${leftCollapsed ? 'collapsed' : ''}`}>
          <button
            className="wing-toggle"
            onClick={() => setLeftCollapsed(c => !c)}
            title={leftCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {leftCollapsed ? '▶' : '◀'}
          </button>
          {!leftCollapsed && (
            <>
              {alerts.length > 0 && (
                <div className="glass-panel alerts-panel">
                  <h3 style={{ color: "#f87171", marginBottom: 8 }}>Vitals Alerts</h3>
                  {alerts.slice(0, 2).map(a => (
                    <div key={a.id} className={`alert-card prio-${a.priority}`} style={{ marginBottom: 6 }}>
                      <span className="alert-text">{a.message}</span>
                      <button className="alert-dismiss" onClick={() => dismissAlert(a.id)}>✕</button>
                    </div>
                  ))}
                </div>
              )}
              <FleetStatusWidget onOpenSupervisor={() => { setView("mind"); setAutonomySubView("supervisor"); }} />
              <GuardianWidget />
              <TelemetryHUD ctx={ctx} consciousness={consciousness} />
            </>
          )}
          {leftCollapsed && (
            <div className="wing-collapsed-indicators">
              <div className="wci-dot" title="Consciousness">🧠</div>
              <div className="wci-dot" title="Context">📡</div>
              <div className="wci-dot" title="Work">⏱️</div>
              <div className="wci-dot" title="Finance">💰</div>
            </div>
          )}
        </aside>

        {/* Center Stage (Dynamic workspace switcher) */}
        <main className="hud-center-stage">
          {view === "chat" && zeroBloat && (
            <ZeroBloatDashboard
              initialMessages={messages}
              apiBase={API}
            />
          )}
          {view === "chat" && !zeroBloat && (
            <>
              {messages.length === 1 && (
                <div className="quick-grid" style={{ padding: "16px 24px 0 24px" }}>
                  {QUICK.map((q, i) => (
                    <button key={i} className="quick-btn" onClick={() => send(q.label)}>
                      <span className="quick-icon">{q.icon}</span>
                      <span>{q.label}</span>
                    </button>
                  ))}
                </div>
              )}

              <NeuralStream messages={messages} bottomRef={bottomRef} loading={loading} />

              <div className="input-bar">
                <VoiceInterface compact={true} ref={voiceRef} onTranscript={(text) => send(text)} />
                <textarea
                  ref={(el) => { textareaRef.current = el; inputRef.current = el; }}
                  className="input-field"
                  placeholder="Enter request or AGI command queries..."
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

          {view === "swarm" && (
            <ErrorBoundary name="Swarm">
              <div className="sub-view-layout">
                <div className="sub-nav-header">
                  <button className={`sub-nav-btn ${swarmSubView === "swarm" ? "active" : ""}`} onClick={() => setSwarmSubView("swarm")}>
                    🐝 SWARM
                  </button>
                  <button className={`sub-nav-btn ${swarmSubView === "agents" ? "active" : ""}`} onClick={() => setSwarmSubView("agents")}>
                    🤖 AGENT LOOP
                  </button>
                </div>
                <div className="view-scroll">
                  {swarmSubView === "swarm" && <SwarmPanel />}
                  {swarmSubView === "agents" && <AgentLoopPanel />}
                </div>
              </div>
            </ErrorBoundary>
          )}

          {view === "mind" && (
            <ErrorBoundary name="Mind">
              <div className="sub-view-layout">
                <div className="sub-nav-header">
                  <button className={`sub-nav-btn ${autonomySubView === "consciousness" ? "active" : ""}`} onClick={() => setAutonomySubView("consciousness")}>
                    🧠 CONSCIOUSNESS
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "wave" ? "active" : ""}`} onClick={() => setAutonomySubView("wave")}>
                    🌊 WAVE ENGINE
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "supervisor" ? "active" : ""}`} onClick={() => setAutonomySubView("supervisor")}>
                    🛡️ FLEET SUPERVISOR
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "sentinel" ? "active" : ""}`} onClick={() => setAutonomySubView("sentinel")}>
                    👁️ SENTINEL MONITOR
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "orchestrator" ? "active" : ""}`} onClick={() => setAutonomySubView("orchestrator")}>
                    🎛️ ORCHESTRATOR
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "intelligence" ? "active" : ""}`} onClick={() => setAutonomySubView("intelligence")}>
                    🧬 INTELLIGENCE
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "mesh" ? "active" : ""}`} onClick={() => setAutonomySubView("mesh")}>
                    🕸️ NEURAL MESH
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "emotions" ? "active" : ""}`} onClick={() => setAutonomySubView("emotions")}>
                    ♥ EMOTIONS
                  </button>
                  <button className={`sub-nav-btn ${autonomySubView === "context" ? "active" : ""}`} onClick={() => setAutonomySubView("context")}>
                    📡 CONTEXT
                  </button>
                </div>
                <div className="view-scroll">
                  {autonomySubView === "consciousness" && <MindPanel />}
                  {autonomySubView === "wave" && <WaveEngine />}
                  {autonomySubView === "supervisor" && <SupervisorPanel />}
                  {autonomySubView === "sentinel" && <SentinelPanel />}
                  {autonomySubView === "orchestrator" && <OrchestratorPanel />}
                  {autonomySubView === "intelligence" && <IntelligenceDashboard />}
                  {autonomySubView === "mesh" && <NeuralMesh />}
                  {autonomySubView === "emotions" && <EmotionalPanel />}
                  {autonomySubView === "context" && <ContextPanel />}
                </div>
              </div>
            </ErrorBoundary>
          )}

          {view === "evolution" && (
            <ErrorBoundary name="Evolution">
              <div className="sub-view-layout">
                <div className="sub-nav-header">
                  <button className={`sub-nav-btn ${evolutionSubView === "matrix" ? "active" : ""}`} onClick={() => setEvolutionSubView("matrix")}>
                    🧬 EVOLUTION MATRIX
                  </button>
                  <button className={`sub-nav-btn ${evolutionSubView === "advanced" ? "active" : ""}`} onClick={() => setEvolutionSubView("advanced")}>
                    🧪 DNA & DAEMON
                  </button>
                  <button className={`sub-nav-btn ${evolutionSubView === "terminal" ? "active" : ""}`} onClick={() => setEvolutionSubView("terminal")}>
                    📟 NEURAL TERMINAL
                  </button>
                  <a className="sub-nav-btn" href="/static/evolution_dashboard.html" target="_blank" rel="noopener noreferrer">
                    📊 DASHBOARD
                  </a>
                </div>
                <div className="view-scroll">
                  {evolutionSubView === "matrix" && <SelfEvolutionPanel />}
                  {evolutionSubView === "advanced" && <EvolutionPanel />}
                  {evolutionSubView === "terminal" && <TerminalPanel />}
                </div>
              </div>
            </ErrorBoundary>
          )}

          {view === "biometrics" && (
            <ErrorBoundary name="Dashboard">
              <div className="sub-view-layout">
                <div className="sub-nav-header">
                  <button className={`sub-nav-btn ${pulseSubView === "lifelog" ? "active" : ""}`} onClick={() => setPulseSubView("lifelog")}>
                    📊 LIFE DOMAINS
                  </button>
                  <button className={`sub-nav-btn ${pulseSubView === "domains" ? "active" : ""}`} onClick={() => setPulseSubView("domains")}>
                    💪 TRACKER
                  </button>
                  <button className={`sub-nav-btn ${pulseSubView === "focus" ? "active" : ""}`} onClick={() => setPulseSubView("focus")}>
                    ⏱️ FOCUS MODE
                  </button>
                  <button className={`sub-nav-btn ${pulseSubView === "ritual" ? "active" : ""}`} onClick={() => setPulseSubView("ritual")}>
                    ♥ RITUAL BRIEFINGS
                  </button>
                  <button className={`sub-nav-btn ${pulseSubView === "briefing" ? "active" : ""}`} onClick={() => setPulseSubView("briefing")}>
                    📰 DAILY BRIEF
                  </button>
                  <button className={`sub-nav-btn ${pulseSubView === "homeostasis" ? "active" : ""}`} onClick={() => setPulseSubView("homeostasis")}>
                    ♻️ HOMEOSTASIS
                  </button>
                </div>
                <div className="view-scroll">
                  {pulseSubView === "lifelog" && <Dashboard />}
                  {pulseSubView === "domains" && <LifeDomains />}
                  {pulseSubView === "focus" && <FocusMode />}
                  {pulseSubView === "ritual" && <RitualView />}
                  {pulseSubView === "briefing" && <BriefingPanel />}
                  {pulseSubView === "homeostasis" && <HomeostasisPanel />}
                </div>
              </div>
            </ErrorBoundary>
          )}

          {view === "finance" && (
            <ErrorBoundary name="Finance"><div className="view-scroll"><FinanceManager /></div></ErrorBoundary>
          )}

          {view === "constellation" && (
            <ErrorBoundary name="Constellation">
              <div className="sub-view-layout">
                <div className="sub-nav-header">
                  <button className={`sub-nav-btn ${cosmosSubView === "map" ? "active" : ""}`} onClick={() => setCosmosSubView("map")}>
                    🔌 DEVICE MAP
                  </button>
                  <button className={`sub-nav-btn ${cosmosSubView === "notifications" ? "active" : ""}`} onClick={() => setCosmosSubView("notifications")}>
                    📲 NOTIFICATION LOGS & INSIGHTS
                  </button>
                  <button className={`sub-nav-btn ${cosmosSubView === "integrations" ? "active" : ""}`} onClick={() => setCosmosSubView("integrations")}>
                    🌐 INTEGRATIONS
                  </button>
                </div>
                <div className="view-scroll">
                  {cosmosSubView === "map" && <ConstellationMap />}
                  {cosmosSubView === "notifications" && <NotificationDashboard />}
                  {cosmosSubView === "integrations" && <IntegrationsPanel />}
                </div>
              </div>
            </ErrorBoundary>
          )}

          {view === "setup" && (
            <ErrorBoundary name="Setup"><div className="view-scroll"><SetupWizard /></div></ErrorBoundary>
          )}

          {view === "settings" && (
            <ErrorBoundary name="Settings"><div className="view-scroll"><SettingsManager /></div></ErrorBoundary>
          )}
        </main>

        {/* Right Wing */}
        <aside className={`hud-wing right-wing ${rightCollapsed ? 'collapsed' : ''}`}>
          <button
            className="wing-toggle"
            onClick={() => setRightCollapsed(c => !c)}
            title={rightCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {rightCollapsed ? '◀' : '▶'}
          </button>
          {!rightCollapsed && (
            <>
              <EvolutionHUD evolution={evolution} predictions={predictions} />
              {view !== "constellation" && (
                <div className="glass-panel" style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 120, padding: 8 }}>
                  <h3 style={{ margin: "0 0 8px 0" }}>Cosmos Topology Map</h3>
                  <div style={{ flex: 1, position: "relative", overflow: "hidden", borderRadius: 8, background: "rgba(0,0,0,0.2)", border: "1px solid rgba(255,255,255,0.03)" }}>
                    <ConstellationMap compact />
                  </div>
                </div>
              )}
            </>
          )}
          {rightCollapsed && (
            <div className="wing-collapsed-indicators">
              <div className="wci-dot" title="Predictions">🔮</div>
              <div className="wci-dot" title="Evolution">🧬</div>
              <div className="wci-dot" title="Topology">🔌</div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
