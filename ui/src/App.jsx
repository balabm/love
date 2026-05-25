import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import Dashboard from "./components/Dashboard";
import ContextPanel from "./components/ContextPanel";
import IntelligenceDashboard from "./components/IntelligenceDashboard";
import GuardianWidget from "./components/GuardianWidget";
import EmotionalPanel from "./components/EmotionalPanel";
import RitualView from "./components/RitualView";
import FocusMode from "./components/FocusMode";
import NeuralMesh from "./components/NeuralMesh";
import IntegrationsPanel from "./components/IntegrationsPanel";
import AgentLoopPanel from "./components/AgentLoopPanel";
import BriefingPanel from "./components/BriefingPanel";

const API = "http://localhost:8000";

function ts() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
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
  const [view, setView] = useState("chat"); // chat | mind | dashboard | ritual | focus | neural | integrations | agent | briefing
  const [messages, setMessages] = useState([{
    role: "love",
    text: "Hey Karthi. I'm watching everything — your PC, your schedule, your patterns. Just talk to me.",
    time: ts(),
    thinking: "",
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("checking");
  const [lifeScore, setLifeScore] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [ctx, setCtx] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    ping();
    loadLive();
    const t = setInterval(loadLive, 30000);
    return () => clearInterval(t);
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
    try { await axios.get(`${API}/health`); setStatus("online"); }
    catch { setStatus("offline"); }
  };

  const loadLive = async () => {
    try {
      const [scoreRes, intRes, ctxRes] = await Promise.allSettled([
        axios.get(`${API}/lifescore`),
        axios.get(`${API}/orchestrator/interventions`),
        axios.get(`${API}/context/summary`),
      ]);
      if (scoreRes.status === "fulfilled") setLifeScore(scoreRes.value.data.score);
      if (intRes.status === "fulfilled") setAlerts(intRes.value.data.interventions || []);
      if (ctxRes.status === "fulfilled") setCtx(ctxRes.value.data);
    } catch {}
  };

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setMessages(p => [...p, { role: "user", text: msg, time: ts() }]);
    setInput("");
    setLoading(true);
    setView("chat");
    try {
      const res = await axios.post(`${API}/chat`, { text: msg, mode: "general" });
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
  }, [input, loading]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const dismissAlert = async (id) => {
    try { await axios.post(`${API}/orchestrator/dismiss/${id}`); }
    catch {}
    setAlerts(p => p.filter(a => a.id !== id));
  };

  const triggerAutoHeal = async () => {
    try {
      await axios.post(`${API}/evolution/install-packages`, { feature: "google calendar gmail drive" });
      setMessages(p => [...p, { role: "love", text: "Installing Google packages now. I'll let you know when done.", time: ts() }]);
    } catch {}
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
          <button className={`nav-btn${view === "ritual" ? " active" : ""}`} onClick={() => setView("ritual")}>
            <span>◎</span> Ritual
          </button>
          <button className={`nav-btn${view === "focus" ? " active" : ""}`} onClick={() => setView("focus")}>
            <span>▶</span> Focus
          </button>
          <button className={`nav-btn${view === "mind" ? " active" : ""}`} onClick={() => setView("mind")}>
            <span>◉</span> Mind
          </button>
          <button className={`nav-btn${view === "neural" ? " active" : ""}`} onClick={() => setView("neural")}>
            <span>⬡</span> Neural
          </button>
          <button className={`nav-btn${view === "dashboard" ? " active" : ""}`} onClick={() => setView("dashboard")}>
            <span>⊞</span> Dashboard
          </button>
          <button className={`nav-btn${view === "integrations" ? " active" : ""}`} onClick={() => setView("integrations")}>
            <span>⬡</span> Integrations
          </button>
          <button className={`nav-btn${view === "agent" ? " active" : ""}`} onClick={() => setView("agent")}>
            <span>◈</span> Agent
          </button>
          <button className={`nav-btn${view === "briefing" ? " active" : ""}`} onClick={() => setView("briefing")}>
            <span>◷</span> Brief
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
              />
              <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>↑</button>
            </div>
          </>
        )}

        {view === "mind" && (
          <div className="view-scroll"><IntelligenceDashboard /></div>
        )}
        {view === "neural" && (
          <div className="view-scroll"><NeuralMesh /></div>
        )}

        {view === "dashboard" && (
          <div className="view-scroll"><Dashboard /></div>
        )}

        {view === "ritual" && (
          <div className="view-scroll view-ritual"><RitualView /></div>
        )}

        {view === "focus" && (
          <div className="view-scroll view-focus"><FocusMode /></div>
        )}

        {view === "integrations" && (
          <div className="view-scroll"><IntegrationsPanel /></div>
        )}

        {view === "agent" && (
          <div className="view-scroll"><AgentLoopPanel /></div>
        )}

        {view === "briefing" && (
          <div className="view-scroll"><BriefingPanel /></div>
        )}
      </main>
    </div>
  );
}
