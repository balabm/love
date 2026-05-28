import { useState, useEffect } from "react";
import api, { API } from "../api";
import "./EmotionalPanel.css";

const MOOD_COLORS = {
  happy: "#34d399", focused: "#60a5fa", calm: "#a78bfa",
  anxious: "#fbbf24", stressed: "#f87171", tired: "#9ca3af",
  sad: "#6b7280", excited: "#f59e0b", neutral: "#6b7280",
};

const MOOD_EMOJI = {
  happy: "◉", focused: "◈", calm: "◎", anxious: "△",
  stressed: "⚠", tired: "◌", sad: "◯", excited: "★", neutral: "○",
};

export default function EmotionalPanel() {
  const [state, setState] = useState(null);
  const [summary, setSummary] = useState(null);
  const [moodInput, setMoodInput] = useState("");
  const [logging, setLogging] = useState(false);
  const [open, setOpen] = useState(true);

  useEffect(() => {
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const load = async () => {
    try {
      const [stateRes, sumRes] = await Promise.allSettled([
        api.get(`/emotional/state`),
        api.get(`/emotional/summary`),
      ]);
      if (stateRes.status === "fulfilled") setState(stateRes.value.data);
      if (sumRes.status === "fulfilled") setSummary(sumRes.value.data);
    } catch (e) { console.error("[Emotional] load failed:", e); }
  };

  const logMood = async (mood) => {
    if (!mood) return;
    setLogging(true);
    try {
      await api.post(`/emotional/record`, { emotion: mood, intensity: 0.7 });
      setMoodInput("");
      await load();
    } catch (e) { console.error("[Emotional] log mood failed:", e); }
    setLogging(false);
  };

  const quickMoods = ["focused", "calm", "tired", "stressed", "happy"];

  if (!state && !summary) return (
    <div className="ep-empty">
      <span className="ep-empty-icon">♡</span>
      <span>Emotional state loading…</span>
    </div>
  );

  const current = state?.current_emotion || state?.dominant || "neutral";
  const color = MOOD_COLORS[current] || "#6b7280";
  const icon = MOOD_EMOJI[current] || "○";

  return (
    <div className="ep">
      <div className="ep-header" onClick={() => setOpen(o => !o)}>
        <span className="ep-icon" style={{ color }}>♡</span>
        <span className="ep-title">Emotional State</span>
        <span className="ep-mood" style={{ color }}>{icon} {current}</span>
        <span className="ep-chevron">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <>
          {/* Quick mood log */}
          <div className="ep-quick">
            {quickMoods.map(m => (
              <button
                key={m}
                className="ep-mood-btn"
                style={{ borderColor: `${MOOD_COLORS[m]}40`, color: MOOD_COLORS[m] }}
                onClick={() => logMood(m)}
                disabled={logging}
              >
                {MOOD_EMOJI[m]} {m}
              </button>
            ))}
          </div>

          {/* Summary */}
          {summary && (
            <div className="ep-summary">
              {summary.trend && (
                <div className="ep-row">
                  <span className="ep-row-label">Trend</span>
                  <span className="ep-row-val">{summary.trend}</span>
                </div>
              )}
              {summary.message && (
                <div className="ep-note">{summary.message}</div>
              )}
              {summary.avg_mood != null && (
                <div className="ep-row">
                  <span className="ep-row-label">Avg mood (7d)</span>
                  <span className="ep-row-val">{summary.avg_mood.toFixed(1)}</span>
                </div>
              )}
            </div>
          )}

          {/* Relationships */}
          {state?.relationships && Object.keys(state.relationships).length > 0 && (
            <div className="ep-section-label">People radar</div>
          )}
        </>
      )}
    </div>
  );
}
