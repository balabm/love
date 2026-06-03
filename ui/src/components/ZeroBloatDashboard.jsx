/**
 * Zero-Bloat Telemetry Dashboard
 *
 * The UI consists ONLY of:
 *  1. Terminal (Chat)
 *  2. Live Life Score (0-100)
 *  3. 9-Hour Work Guardian
 *  4. Sentinel Health Logs
 *
 * No templates. No empty screens. WebSocket-first reactive mirror.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import api, { API } from "../api";

function ts() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function ZeroBloatDashboard({
  initialMessages = [],
  apiBase = API,
}) {
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const wsRetryCount = useRef(0);
  const wsRetryTimer = useRef(null);

  // Core telemetry
  const [lifeScore, setLifeScore] = useState(null);
  const [workHours, setWorkHours] = useState(0);
  const [workLimit, setWorkLimit] = useState(9);
  const [tradingLocked, setTradingLocked] = useState(false);
  const [sentinelHealth, setSentinelHealth] = useState([]);
  const [interventions, setInterventions] = useState([]);

  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const wsRef = useRef(null);
  const chatTimeoutRef = useRef(null);

  // ── WebSocket (telemetry-first) ───────────────────────────────────────────
  const connectWS = useCallback(() => {
    const apiKey = import.meta.env.VITE_API_KEY || "love-dev-key";
    const sep = apiBase.includes("?") ? "&" : "?";
    const wsUrl = apiBase.replace(/^http/, "ws") + "/telemetry" + sep + "api_key=" + apiKey;
    setWsStatus("connecting");
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "intervention") {
          setInterventions((prev) => [
            { id: Date.now(), text: msg.data?.description || JSON.stringify(msg.data), ts: ts() },
            ...prev.slice(0, 4),
          ]);
        }
        if (msg.type === "health_update") {
          setSentinelHealth((prev) => [msg, ...prev.slice(0, 19)]);
        }
        if (msg.type === "connection_established") {
          wsRetryCount.current = 0;
        }
      } catch {
        // ignore malformed
      }
    };

    ws.onopen = () => {
      setWsStatus("connected");
      wsRetryCount.current = 0;
      ws.send("ping");
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
  }, [apiBase]);

  // ── Polling for score + work hours (fallback) ───────────────────────────
  const loadTelemetry = useCallback(async () => {
    try {
      const [scoreRes, workRes, healthRes, tradeRes] = await Promise.allSettled([
        api.get(`${apiBase}/lifescore`),
        api.get(`${apiBase}/guardian/work-status`),
        api.get(`${apiBase}/agi/health/sentinel`),
        api.get(`${apiBase}/guardian/trading-status`),
      ]);
      if (scoreRes.status === "fulfilled") setLifeScore(scoreRes.value.data?.score ?? null);
      if (workRes.status === "fulfilled") {
        setWorkHours(workRes.value.data?.hours_worked ?? 0);
        setWorkLimit(workRes.value.data?.work_limit_hours ?? 9);
      }
      if (tradeRes.status === "fulfilled") {
        setTradingLocked(tradeRes.value.data?.locked ?? false);
      }
      if (healthRes.status === "fulfilled" && Array.isArray(healthRes.value.data)) {
        setSentinelHealth(healthRes.value.data.slice(0, 20));
      }
    } catch {
      // best-effort
    }
  }, [apiBase]);

  useEffect(() => {
    loadTelemetry();
    connectWS();
    const t = setInterval(loadTelemetry, 30000);
    return () => {
      clearInterval(t);
      if (wsRef.current) wsRef.current.close();
    };
  }, [loadTelemetry, connectWS]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [input]);

  // ── Chat ────────────────────────────────────────────────────────────────
  const send = useCallback(async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setMessages((p) => [...p, { role: "user", text: msg, time: ts() }]);
    setInput("");
    setLoading(true);
    // Client-side safety timeout: if backend hangs, clear loading after 35s
    chatTimeoutRef.current = setTimeout(() => {
      setLoading(false);
      setMessages((p) => [
        ...p,
        { role: "love", text: "Response timed out — backend may be overloaded. Try again.", time: ts() },
      ]);
    }, 35000);
    try {
      const res = await api.post(`${apiBase}/chat`, {
        text: msg,
        mode: "general",
        include_live_context: true,
      });
      clearTimeout(chatTimeoutRef.current);
      setMessages((p) => [
        ...p,
        { role: "love", text: res.data?.response || "...", time: ts() },
      ]);
    } catch {
      clearTimeout(chatTimeoutRef.current);
      setMessages((p) => [
        ...p,
        { role: "love", text: "Can't reach the backend. Is LOVE running?", time: ts() },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, apiBase]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  // ── Render ────────────────────────────────────────────────────────────
  const scoreColor =
    lifeScore == null ? "#9ca3af" : lifeScore >= 70 ? "#34d399" : lifeScore >= 40 ? "#fbbf24" : "#f87171";

  const workPct = Math.min(100, (workHours / Math.max(1, workLimit)) * 100);
  const workColor = workPct >= 100 ? "#f87171" : workPct >= 75 ? "#fbbf24" : "#34d399";

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0b0f19", color: "#e2e8f0", fontFamily: "system-ui, sans-serif" }}>
      {/* Top bar */}
      <header style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 16px", borderBottom: "1px solid #1e293b", background: "#0f172a" }}>
        <div style={{ fontWeight: 700, fontSize: 18, color: "#f472b6" }}>LOVE</div>
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase" }}>Life Score</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: scoreColor }}>{lifeScore ?? "—"}</div>
          </div>
          <div style={{ textAlign: "center", minWidth: 80 }}>
            <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase" }}>Work</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: workColor }}>
              {workHours.toFixed(1)}h / {workLimit}h
            </div>
            <div style={{ height: 4, background: "#1e293b", borderRadius: 2, marginTop: 4 }}>
              <div style={{ height: 4, width: `${workPct}%`, background: workColor, borderRadius: 2, transition: "width 0.5s" }} />
            </div>
          </div>
          {tradingLocked && (
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#f87171", textTransform: "uppercase" }}>Trading</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f87171" }}>LOCKED</div>
            </div>
          )}
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: wsStatus === "connected" ? "#34d399" : "#f87171" }} title={wsStatus} />
        </div>
      </header>

      {/* Interventions banner */}
      {interventions.length > 0 && (
        <div style={{ padding: "8px 16px", background: "#7f1d1d", fontSize: 13 }}>
          {interventions.map((i) => (
            <div key={i.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span>🛑</span>
              <span>{i.text}</span>
              <button style={{ marginLeft: "auto", background: "none", border: "none", color: "#fca5a5", cursor: "pointer" }} onClick={() => setInterventions((p) => p.filter((x) => x.id !== i.id))}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Main area: Chat */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ flex: 1, overflowY: "auto", padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          {messages.map((m, idx) => (
            <div key={idx} style={{ alignSelf: m.role === "user" ? "flex-end" : "flex-start", maxWidth: "80%", padding: "8px 12px", borderRadius: 10, background: m.role === "user" ? "#1e3a8a" : "#1e293b", fontSize: 14, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
              <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 4 }}>{m.role === "user" ? "You" : "LOVE"} · {m.time}</div>
              {m.text}
            </div>
          ))}
          {loading && (
            <div style={{ alignSelf: "flex-start", padding: "8px 12px", borderRadius: 10, background: "#1e293b", fontSize: 14, color: "#94a3b8" }}>
              Thinking...
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ display: "flex", gap: 8, padding: 12, borderTop: "1px solid #1e293b", background: "#0f172a" }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Talk to LOVE..."
            style={{ flex: 1, resize: "none", padding: 10, borderRadius: 8, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0", fontSize: 14, outline: "none" }}
            rows={1}
          />
          <button onClick={send} disabled={loading} style={{ padding: "0 16px", borderRadius: 8, border: "none", background: "#db2777", color: "#fff", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1 }}>
            Send
          </button>
        </div>
      </main>

      {/* Sentinel Health footer */}
      <footer style={{ padding: "8px 16px", borderTop: "1px solid #1e293b", background: "#0f172a", maxHeight: 120, overflowY: "auto" }}>
        <div style={{ fontSize: 10, color: "#94a3b8", textTransform: "uppercase", marginBottom: 6 }}>Sentinel Health</div>
        {sentinelHealth.length === 0 ? (
          <div style={{ fontSize: 12, color: "#64748b" }}>No health logs yet.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {sentinelHealth.slice(0, 10).map((h, i) => (
              <div key={i} style={{ fontSize: 12, color: "#cbd5e1", fontFamily: "monospace" }}>
                <span style={{ color: "#64748b" }}>{new Date(h.timestamp || Date.now()).toLocaleTimeString([], {hour: "2-digit", minute:"2-digit", second:"2-digit"})}</span>{" "}
                {h.event_type || h.type}: {JSON.stringify(h.data || h.payload || {}).slice(0, 80)}
              </div>
            ))}
          </div>
        )}
      </footer>
    </div>
  );
}
