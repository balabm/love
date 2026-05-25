import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "./FocusMode.css";

const API = "http://localhost:8000";

const PRESETS = [
  { label: "Deep Work", duration: 90, icon: "◈", color: "#c084fc" },
  { label: "Pomodoro",  duration: 25, icon: "◎", color: "#34d399" },
  { label: "Sprint",    duration: 45, icon: "▶", color: "#60a5fa" },
  { label: "Review",    duration: 15, icon: "◱", color: "#fbbf24" },
];

const STATES = { idle: "idle", running: "running", break: "break", done: "done" };

function formatTime(secs) {
  const m = Math.floor(secs / 60).toString().padStart(2, "0");
  const s = (secs % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export default function FocusMode() {
  const [preset, setPreset] = useState(PRESETS[0]);
  const [sessionState, setSessionState] = useState(STATES.idle);
  const [secsLeft, setSecsLeft] = useState(preset.duration * 60);
  const [task, setTask] = useState("");
  const [log, setLog] = useState([]); // { label, duration, completed, ts }
  const [loveNote, setLoveNote] = useState("");
  const [noteLoading, setNoteLoading] = useState(false);
  const intervalRef = useRef(null);
  const startTimeRef = useRef(null);

  // Reset timer when preset changes and session is idle
  useEffect(() => {
    if (sessionState === STATES.idle) {
      setSecsLeft(preset.duration * 60);
    }
  }, [preset, sessionState]);

  const start = useCallback(() => {
    setSessionState(STATES.running);
    startTimeRef.current = Date.now();
    intervalRef.current = setInterval(() => {
      setSecsLeft(s => {
        if (s <= 1) {
          clearInterval(intervalRef.current);
          setSessionState(STATES.done);
          onComplete();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
  }, [preset, task]);

  const pause = useCallback(() => {
    clearInterval(intervalRef.current);
    setSessionState(STATES.idle);
  }, []);

  const reset = useCallback(() => {
    clearInterval(intervalRef.current);
    setSessionState(STATES.idle);
    setSecsLeft(preset.duration * 60);
    setLoveNote("");
  }, [preset]);

  const onComplete = useCallback(async () => {
    const entry = {
      label: preset.label,
      duration: preset.duration,
      task: task || "—",
      completed: true,
      ts: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setLog(l => [entry, ...l.slice(0, 9)]);

    // Ask LOVE for a note
    setNoteLoading(true);
    try {
      const res = await axios.post(`${API}/chat`, {
        text: `I just completed a ${preset.duration}-minute ${preset.label} session${task ? ` working on: ${task}` : ""}. Give me a one-sentence acknowledgement — sharp, real, no fluff.`,
        mode: "general",
      });
      setLoveNote(res.data?.response || "");
    } catch { /* silent */ }
    setNoteLoading(false);
  }, [preset, task]);

  const pct = 1 - secsLeft / (preset.duration * 60);
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - pct);

  const running = sessionState === STATES.running;
  const done = sessionState === STATES.done;

  return (
    <div className="fm">
      {/* Header */}
      <div className="fm-header">
        <span className="fm-title">Focus Mode</span>
        <div className="fm-presets">
          {PRESETS.map(p => (
            <button
              key={p.label}
              className={`fm-preset${preset.label === p.label ? " active" : ""}`}
              style={preset.label === p.label ? { borderColor: `${p.color}50`, color: p.color } : {}}
              onClick={() => { if (!running) setPreset(p); }}
              disabled={running}
            >
              {p.icon} {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Timer ring */}
      <div className="fm-ring-wrap">
        <svg className="fm-ring" viewBox="0 0 120 120" width="120" height="120">
          <circle cx="60" cy="60" r={radius} className="fm-ring-bg" />
          <circle
            cx="60" cy="60" r={radius}
            className="fm-ring-fg"
            stroke={done ? "#34d399" : preset.color}
            strokeDasharray={circumference}
            strokeDashoffset={running || done ? strokeDashoffset : circumference}
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div className="fm-ring-inner">
          {done ? (
            <div className="fm-done-icon" style={{ color: "#34d399" }}>✓</div>
          ) : (
            <div className="fm-time" style={{ color: done ? "#34d399" : preset.color }}>
              {formatTime(secsLeft)}
            </div>
          )}
          <div className="fm-preset-label">{preset.label}</div>
        </div>
      </div>

      {/* Task input (idle/done only) */}
      {!running && (
        <input
          className="fm-task-input"
          placeholder="What are you working on? (optional)"
          value={task}
          onChange={e => setTask(e.target.value)}
        />
      )}
      {running && task && (
        <div className="fm-active-task">◈ {task}</div>
      )}

      {/* Controls */}
      <div className="fm-controls">
        {!running && !done && (
          <button className="fm-btn primary" style={{ background: preset.color }} onClick={start}>
            ▶ Start
          </button>
        )}
        {running && (
          <>
            <button className="fm-btn" onClick={pause}>⏸ Pause</button>
            <button className="fm-btn danger" onClick={reset}>✕ Cancel</button>
          </>
        )}
        {done && (
          <>
            <button className="fm-btn primary" style={{ background: preset.color }} onClick={() => { reset(); }}>
              ↺ New Session
            </button>
          </>
        )}
      </div>

      {/* LOVE's note on completion */}
      {done && (
        <div className="fm-love-note">
          {noteLoading ? (
            <span className="fm-note-loading">♥ thinking…</span>
          ) : loveNote ? (
            <>
              <span className="fm-note-heart">♥</span>
              <span>{loveNote}</span>
            </>
          ) : null}
        </div>
      )}

      {/* Session log */}
      {log.length > 0 && (
        <div className="fm-log">
          <div className="fm-log-title">Today's sessions</div>
          {log.map((l, i) => (
            <div key={i} className="fm-log-row">
              <span className="fm-log-time">{l.ts}</span>
              <span className="fm-log-label">{l.label} · {l.duration}m</span>
              {l.task !== "—" && <span className="fm-log-task">{l.task}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
