import { useState, useEffect, useCallback } from "react";
import api from "../api";
import "./LifeDomains.css";

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function StreakBadge({ count, label }) {
  if (!count) return null;
  return (
    <span className="ld-streak" title={`${count}-day streak`}>
      ◉ {count}d
    </span>
  );
}

function ScoreRing({ pct, size = 56, color = "#60a5fa", label }) {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const filled = (pct / 100) * circ;
  return (
    <div className="ld-ring-wrap" title={`${pct}%`}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} className="ld-ring-bg" />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          className="ld-ring-fill"
          style={{
            stroke: color,
            strokeDasharray: `${filled} ${circ}`,
            strokeDashoffset: 0,
            transform: `rotate(-90deg)`,
            transformOrigin: "50% 50%",
          }}
        />
        <text x="50%" y="50%" className="ld-ring-text" dominantBaseline="middle" textAnchor="middle">
          {Math.round(pct)}
        </text>
      </svg>
      {label && <div className="ld-ring-label">{label}</div>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Hydration Panel
// ─────────────────────────────────────────────────────────────────────────────

function HydrationPanel({ data, streak, onRefresh }) {
  const [logging, setLogging] = useState(false);
  const [ml, setMl] = useState("");

  const logGlass = async (count) => {
    setLogging(true);
    try {
      await api.post("/life/hydration/log", { count, ml: ml ? parseInt(ml) : null });
      setMl("");
      onRefresh();
    } finally {
      setLogging(false);
    }
  };

  const pct = data?.pct || 0;
  const total = data?.total_ml || 0;
  const goal = data?.goal_ml || 2500;
  const glasses = data?.total_glasses || 0;

  return (
    <div className="ld-domain-card hydration">
      <div className="ld-domain-header">
        <span className="ld-domain-icon">💧</span>
        <span className="ld-domain-title">Hydration</span>
        <StreakBadge count={streak} />
        {data?.needs_nudge && <span className="ld-nudge-dot" title="Action needed" />}
      </div>
      <div className="ld-domain-body">
        <ScoreRing pct={pct} color="#38bdf8" label="%" />
        <div className="ld-domain-stats">
          <div className="ld-stat">
            <span className="ld-stat-val">{total}ml</span>
            <span className="ld-stat-lbl">consumed</span>
          </div>
          <div className="ld-stat">
            <span className="ld-stat-val">{glasses}</span>
            <span className="ld-stat-lbl">glasses</span>
          </div>
          <div className="ld-stat">
            <span className="ld-stat-val">{goal - total > 0 ? goal - total : 0}ml</span>
            <span className="ld-stat-lbl">remaining</span>
          </div>
        </div>
      </div>
      <div className="ld-bar-wrap">
        <div className="ld-bar" style={{ width: `${Math.min(100, pct)}%`, background: pct >= 100 ? "#34d399" : "#38bdf8" }} />
      </div>
      <div className="ld-domain-actions">
        <button className="ld-btn" disabled={logging} onClick={() => logGlass(1)}>+1 glass</button>
        <button className="ld-btn" disabled={logging} onClick={() => logGlass(2)}>+2 glasses</button>
        <div className="ld-custom-ml">
          <input
            className="ld-input" type="number" placeholder="ml"
            value={ml} onChange={e => setMl(e.target.value)}
            onKeyDown={e => e.key === "Enter" && ml && logGlass(0)}
          />
          <button className="ld-btn-sm" disabled={logging || !ml} onClick={() => logGlass(0)}>Log</button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sleep Panel
// ─────────────────────────────────────────────────────────────────────────────

function SleepPanel({ data, streak, onRefresh }) {
  const [logging, setLogging] = useState(false);
  const [bedtime, setBedtime] = useState("23:00");
  const [waketime, setWaketime] = useState("07:00");
  const [quality, setQuality] = useState(7);
  const [expanded, setExpanded] = useState(false);

  const logSleep = async () => {
    setLogging(true);
    try {
      await api.post("/life/sleep/log", { bedtime, wake_time: waketime, quality });
      setExpanded(false);
      onRefresh();
    } finally {
      setLogging(false);
    }
  };

  const hours = data?.hours || 0;
  const goal = data?.goal_hours || 7.5;
  const pct = Math.min(100, (hours / goal) * 100);
  const logged = data?.logged;

  return (
    <div className="ld-domain-card sleep">
      <div className="ld-domain-header">
        <span className="ld-domain-icon">🌙</span>
        <span className="ld-domain-title">Sleep</span>
        <StreakBadge count={streak} />
        {data?.needs_nudge && <span className="ld-nudge-dot" title="Action needed" />}
      </div>
      <div className="ld-domain-body">
        <ScoreRing pct={logged ? pct : 0} color="#818cf8" label="%" />
        <div className="ld-domain-stats">
          {logged ? (
            <>
              <div className="ld-stat">
                <span className="ld-stat-val">{hours}h</span>
                <span className="ld-stat-lbl">slept</span>
              </div>
              <div className="ld-stat">
                <span className="ld-stat-val">{data?.quality}/10</span>
                <span className="ld-stat-lbl">quality</span>
              </div>
              <div className="ld-stat">
                <span className="ld-stat-val">{data?.bedtime}→{data?.wake_time}</span>
                <span className="ld-stat-lbl">window</span>
              </div>
            </>
          ) : (
            <div className="ld-not-logged">Not logged yet today</div>
          )}
        </div>
      </div>
      {!expanded ? (
        <button className="ld-btn ld-btn-full" onClick={() => setExpanded(true)}>
          {logged ? "Update sleep" : "Log last night's sleep"}
        </button>
      ) : (
        <div className="ld-log-form">
          <div className="ld-form-row">
            <label>Bedtime</label>
            <input type="time" className="ld-input" value={bedtime} onChange={e => setBedtime(e.target.value)} />
          </div>
          <div className="ld-form-row">
            <label>Wake</label>
            <input type="time" className="ld-input" value={waketime} onChange={e => setWaketime(e.target.value)} />
          </div>
          <div className="ld-form-row">
            <label>Quality</label>
            <div className="ld-quality-row">
              {[1,2,3,4,5,6,7,8,9,10].map(n => (
                <button key={n} className={`ld-q-btn${quality === n ? " active" : ""}`} onClick={() => setQuality(n)}>{n}</button>
              ))}
            </div>
          </div>
          <div className="ld-form-btns">
            <button className="ld-btn" disabled={logging} onClick={logSleep}>Save</button>
            <button className="ld-btn ld-btn-ghost" onClick={() => setExpanded(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Nutrition Panel
// ─────────────────────────────────────────────────────────────────────────────

const MEAL_TYPES = ["breakfast", "lunch", "dinner", "snack"];
const MEAL_ICONS = { breakfast: "☀️", lunch: "🌤", dinner: "🌙", snack: "⚡" };

function NutritionPanel({ data, streak, onRefresh }) {
  const [logging, setLogging] = useState(false);
  const [mealType, setMealType] = useState("breakfast");
  const [desc, setDesc] = useState("");
  const [quality, setQuality] = useState(6);
  const [expanded, setExpanded] = useState(false);

  const logMeal = async () => {
    if (!desc.trim()) return;
    setLogging(true);
    try {
      await api.post("/life/nutrition/log", { meal_type: mealType, description: desc, quality });
      setDesc("");
      setExpanded(false);
      onRefresh();
    } finally {
      setLogging(false);
    }
  };

  const logged = data?.types_logged || [];
  const meals = data?.meals || [];
  const missing = data?.missing_meals || [];

  return (
    <div className="ld-domain-card nutrition">
      <div className="ld-domain-header">
        <span className="ld-domain-icon">🥗</span>
        <span className="ld-domain-title">Nutrition</span>
        <StreakBadge count={streak} />
        {data?.needs_nudge && <span className="ld-nudge-dot" title="Action needed" />}
      </div>
      <div className="ld-domain-body">
        <ScoreRing pct={Math.min(100, (meals.length / 3) * 100)} color="#34d399" label="meals" />
        <div className="ld-meal-types">
          {MEAL_TYPES.map(t => (
            <div key={t} className={`ld-meal-chip ${logged.includes(t) ? "done" : "missing"}`}>
              {MEAL_ICONS[t]} {t}
            </div>
          ))}
        </div>
      </div>
      {meals.length > 0 && (
        <div className="ld-meal-list">
          {meals.slice(-3).map((m, i) => (
            <div key={i} className="ld-meal-entry">
              <span className="ld-meal-type-tag">{m.type}</span>
              <span className="ld-meal-desc">{m.description}</span>
              <span className="ld-meal-q">{m.quality}/10</span>
            </div>
          ))}
        </div>
      )}
      {!expanded ? (
        <button className="ld-btn ld-btn-full" onClick={() => setExpanded(true)}>
          + Log meal
        </button>
      ) : (
        <div className="ld-log-form">
          <div className="ld-meal-type-select">
            {MEAL_TYPES.map(t => (
              <button key={t} className={`ld-chip${mealType === t ? " active" : ""}`} onClick={() => setMealType(t)}>
                {MEAL_ICONS[t]} {t}
              </button>
            ))}
          </div>
          <input
            className="ld-input ld-input-full" placeholder="What did you eat?"
            value={desc} onChange={e => setDesc(e.target.value)}
            onKeyDown={e => e.key === "Enter" && logMeal()}
          />
          <div className="ld-form-row">
            <label>Quality</label>
            <div className="ld-quality-row">
              {[1,2,3,4,5,6,7,8,9,10].map(n => (
                <button key={n} className={`ld-q-btn${quality === n ? " active" : ""}`} onClick={() => setQuality(n)}>{n}</button>
              ))}
            </div>
          </div>
          <div className="ld-form-btns">
            <button className="ld-btn" disabled={logging || !desc.trim()} onClick={logMeal}>Save</button>
            <button className="ld-btn ld-btn-ghost" onClick={() => setExpanded(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Skincare Panel
// ─────────────────────────────────────────────────────────────────────────────

const ROUTINE_STEPS = {
  morning: ["cleanser", "toner", "serum", "moisturizer", "spf"],
  evening: ["cleanser", "toner", "serum", "moisturizer", "treatment"],
};

function SkincarePanel({ data, streak, onRefresh }) {
  const [logging, setLogging] = useState(false);
  const [routineType, setRoutineType] = useState("morning");
  const [stepsSelected, setStepsSelected] = useState([]);
  const [feeling, setFeeling] = useState(7);
  const [skinNotes, setSkinNotes] = useState("");
  const [expanded, setExpanded] = useState(false);

  const toggleStep = (s) =>
    setStepsSelected(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]);

  const logRoutine = async () => {
    setLogging(true);
    try {
      await api.post("/life/skincare/routine", {
        routine_type: routineType,
        steps_done: stepsSelected,
        skin_notes: skinNotes,
        feeling,
      });
      setStepsSelected([]);
      setSkinNotes("");
      setExpanded(false);
      onRefresh();
    } finally {
      setLogging(false);
    }
  };

  const morning = data?.morning_done;
  const evening = data?.evening_done;
  const score = data?.daily_score || 0;

  return (
    <div className="ld-domain-card skincare">
      <div className="ld-domain-header">
        <span className="ld-domain-icon">✨</span>
        <span className="ld-domain-title">Skincare</span>
        <StreakBadge count={streak} />
        {data?.needs_nudge && <span className="ld-nudge-dot" title="Action needed" />}
      </div>
      <div className="ld-domain-body">
        <ScoreRing pct={score} color="#f9a8d4" label="%" />
        <div className="ld-routine-status">
          <div className={`ld-routine-chip ${morning ? "done" : "pending"}`}>
            ☀️ Morning {morning ? "✓" : "○"}
          </div>
          <div className={`ld-routine-chip ${evening ? "done" : "pending"}`}>
            🌙 Evening {evening ? "✓" : "○"}
          </div>
        </div>
      </div>
      {!expanded ? (
        <div className="ld-routine-btns">
          <button className="ld-btn" onClick={() => { setRoutineType("morning"); setExpanded(true); }}>
            {morning ? "Update morning" : "Log morning"}
          </button>
          <button className="ld-btn" onClick={() => { setRoutineType("evening"); setExpanded(true); }}>
            {evening ? "Update evening" : "Log evening"}
          </button>
        </div>
      ) : (
        <div className="ld-log-form">
          <div className="ld-routine-type-select">
            {["morning", "evening"].map(t => (
              <button key={t} className={`ld-chip${routineType === t ? " active" : ""}`} onClick={() => setRoutineType(t)}>
                {t === "morning" ? "☀️" : "🌙"} {t}
              </button>
            ))}
          </div>
          <div className="ld-steps-grid">
            {ROUTINE_STEPS[routineType].map(s => (
              <button key={s} className={`ld-step-btn${stepsSelected.includes(s) ? " active" : ""}`} onClick={() => toggleStep(s)}>
                {s}
              </button>
            ))}
          </div>
          <div className="ld-form-row">
            <label>Skin feeling</label>
            <div className="ld-quality-row">
              {[1,2,3,4,5,6,7,8,9,10].map(n => (
                <button key={n} className={`ld-q-btn${feeling === n ? " active" : ""}`} onClick={() => setFeeling(n)}>{n}</button>
              ))}
            </div>
          </div>
          <input
            className="ld-input ld-input-full" placeholder="Any skin notes? (optional)"
            value={skinNotes} onChange={e => setSkinNotes(e.target.value)}
          />
          <div className="ld-form-btns">
            <button className="ld-btn" disabled={logging} onClick={logRoutine}>Save</button>
            <button className="ld-btn ld-btn-ghost" onClick={() => setExpanded(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main LifeDomains View
// ─────────────────────────────────────────────────────────────────────────────

export default function LifeDomains() {
  const [dashboard, setDashboard] = useState(null);
  const [streaks, setStreaks] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("today");

  const load = useCallback(async () => {
    try {
      const [dash, str] = await Promise.all([
        api.get("/life/dashboard"),
        api.get("/life/streaks"),
      ]);
      setDashboard(dash.data);
      setStreaks(str.data);
    } catch (e) {
      console.error("LifeDomains load error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000);
    return () => clearInterval(t);
  }, [load]);

  const nudges = dashboard?.nudges || [];
  const lifeScore = dashboard?.life_score || 0;

  const scoreColor = lifeScore >= 80 ? "#34d399" : lifeScore >= 50 ? "#fbbf24" : "#f87171";

  return (
    <div className="ld-root">
      {/* Header */}
      <div className="ld-header">
        <div className="ld-title-row">
          <h2 className="ld-title">Life Domains</h2>
          <div className="ld-life-score" style={{ borderColor: scoreColor }}>
            <span className="ld-score-val" style={{ color: scoreColor }}>{Math.round(lifeScore)}</span>
            <span className="ld-score-lbl">today</span>
          </div>
        </div>

        {nudges.length > 0 && (
          <div className="ld-nudge-bar">
            {nudges.map((n, i) => (
              <div key={i} className="ld-nudge-item">
                <span className="ld-nudge-dot-inline">◉</span>
                {n}
              </div>
            ))}
          </div>
        )}

        <div className="ld-tabs">
          <button className={`ld-tab${activeTab === "today" ? " active" : ""}`} onClick={() => setActiveTab("today")}>Today</button>
          <button className={`ld-tab${activeTab === "insights" ? " active" : ""}`} onClick={() => setActiveTab("insights")}>7-Day</button>
        </div>
      </div>

      {loading ? (
        <div className="ld-loading">Loading life domains...</div>
      ) : activeTab === "today" ? (
        <div className="ld-grid">
          <HydrationPanel data={dashboard?.hydration} streak={streaks.hydration} onRefresh={load} />
          <SleepPanel data={dashboard?.sleep} streak={streaks.sleep} onRefresh={load} />
          <NutritionPanel data={dashboard?.nutrition} streak={streaks.nutrition} onRefresh={load} />
          <SkincarePanel data={dashboard?.skincare} streak={streaks.skincare} onRefresh={load} />
        </div>
      ) : (
        <WeeklyInsights />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Weekly Insights Tab
// ─────────────────────────────────────────────────────────────────────────────

function WeeklyInsights() {
  const [insights, setInsights] = useState(null);
  const [correlations, setCorrelations] = useState(null);
  const [goals, setGoals] = useState(null);

  useEffect(() => {
    api.get("/life/insights").then(r => setInsights(r.data)).catch(() => {});
    api.get("/life/correlations").then(r => setCorrelations(r.data)).catch(() => {});
    api.get("/life/coach/goals").then(r => setGoals(r.data)).catch(() => {});
  }, []);

  if (!insights) return <div className="ld-loading">Loading insights...</div>;

  return (
    <div className="ld-insights">
      <InsightCard
        icon="💧" title="Hydration"
        stats={[
          { label: "Avg/day", val: `${insights.hydration.avg_ml}ml` },
          { label: "Goal days", val: `${insights.hydration.days_goal_met}/7` },
          { label: "Streak", val: `${insights.hydration.streak}d` },
        ]}
        history={insights.hydration.history}
        barKey="total_ml"
        barMax={insights.hydration.goal_ml}
        color="#38bdf8"
      />
      <InsightCard
        icon="🌙" title="Sleep"
        stats={[
          { label: "Avg hours", val: `${insights.sleep.avg_hours}h` },
          { label: "Avg quality", val: `${insights.sleep.avg_quality}/10` },
          { label: "Goal days", val: `${insights.sleep.days_goal_met}/7` },
        ]}
        history={insights.sleep.history}
        barKey="hours"
        barMax={insights.sleep.goal_hours}
        color="#818cf8"
      />
      <InsightCard
        icon="🥗" title="Nutrition"
        stats={[
          { label: "Avg meals", val: insights.nutrition.avg_meals_per_day },
          { label: "Avg quality", val: `${insights.nutrition.avg_quality}/10` },
          { label: "Streak", val: `${insights.nutrition.streak}d` },
        ]}
        history={insights.nutrition.history}
        barKey="meals"
        barMax={3}
        color="#34d399"
      />
      <InsightCard
        icon="✨" title="Skincare"
        stats={[
          { label: "Morning %", val: `${insights.skincare.morning_consistency}%` },
          { label: "Evening %", val: `${insights.skincare.evening_consistency}%` },
          { label: "Streak", val: `${insights.skincare.streak}d` },
        ]}
        history={insights.skincare.history}
        barKey="score"
        barMax={100}
        color="#f9a8d4"
      />

      {/* Cross-domain intelligence */}
      {correlations && (correlations.correlations?.length > 0 || correlations.warnings?.length > 0 || correlations.positives?.length > 0) && (
        <div className="ld-insight-card ld-correlations-card">
          <div className="ld-insight-header">
            <span>⚡</span>
            <span className="ld-insight-title">Cross-Domain Patterns</span>
          </div>
          {correlations.positives?.map((p, i) => (
            <div key={`p${i}`} className="ld-corr-item ld-corr-positive">◉ {p}</div>
          ))}
          {correlations.correlations?.map((c, i) => (
            <div key={`c${i}`} className="ld-corr-item ld-corr-insight">◈ {c}</div>
          ))}
          {correlations.warnings?.map((w, i) => (
            <div key={`w${i}`} className="ld-corr-item ld-corr-warning">△ {w}</div>
          ))}
        </div>
      )}

      {/* Adaptive goals */}
      {goals && !goals.error && (
        <div className="ld-insight-card ld-goals-card">
          <div className="ld-insight-header">
            <span>◎</span>
            <span className="ld-insight-title">Today’s Adaptive Goals</span>
          </div>
          {Object.entries(goals).filter(([k]) => k !== "error").map(([domain, g]) => (
            <div key={domain} className="ld-goal-item">
              <span className="ld-goal-domain">{domain}</span>
              <span className="ld-goal-msg">{g.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InsightCard({ icon, title, stats, history, barKey, barMax, color }) {
  return (
    <div className="ld-insight-card">
      <div className="ld-insight-header">
        <span>{icon}</span>
        <span className="ld-insight-title">{title}</span>
      </div>
      <div className="ld-insight-stats">
        {stats.map((s, i) => (
          <div key={i} className="ld-insight-stat">
            <span className="ld-insight-stat-val">{s.val}</span>
            <span className="ld-insight-stat-lbl">{s.label}</span>
          </div>
        ))}
      </div>
      <div className="ld-mini-chart">
        {history.map((r, i) => {
          const val = r[barKey] || 0;
          const h = Math.min(100, (val / barMax) * 100);
          return (
            <div key={i} className="ld-chart-col" title={`${r.date}: ${val}`}>
              <div className="ld-chart-bar" style={{ height: `${h}%`, background: color }} />
              <span className="ld-chart-day">{r.date?.slice(5)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
