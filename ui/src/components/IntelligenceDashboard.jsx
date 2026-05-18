import { useState, useEffect } from "react";
import axios from "axios";
import "./IntelligenceDashboard.css";

const API = "http://localhost:8000";

const ICON = {
  brain: "◈",
  prediction: "◉",
  insight: "✦",
  gap: "?",
  emotion: "♡",
  world: "◎",
  evolve: "◬",
  clock: "◷",
};

function Card({ title, icon, children, accent }) {
  return (
    <div className={`intel-card intel-${accent}`}>
      <div className="intel-card-header">
        <span className="intel-card-icon">{icon}</span>
        <h3>{title}</h3>
      </div>
      <div className="intel-card-body">{children}</div>
    </div>
  );
}

function PredictionItem({ pred }) {
  const confidence = Math.round((pred.confidence || 0) * 100);
  return (
    <div className="intel-item">
      <div className="intel-item-text">{pred.what}</div>
      <div className="intel-item-meta">
        <span className={`intel-badge intel-badge-${confidence > 70 ? "high" : confidence > 40 ? "med" : "low"}`}>
          {confidence}% confidence
        </span>
        <span className="intel-basis">{pred.basis}</span>
      </div>
    </div>
  );
}

function InsightItem({ text }) {
  return (
    <div className="intel-item">
      <span className="intel-bullet">✦</span>
      <span className="intel-item-text">{text}</span>
    </div>
  );
}

function GapItem({ gap }) {
  return (
    <div className="intel-item">
      <span className="intel-bullet">?</span>
      <span className="intel-item-text">{gap.question || gap.gap_text}</span>
      <span className={`intel-badge intel-badge-${gap.status === "open" ? "low" : "high"}`}>
        {gap.status}
      </span>
    </div>
  );
}

export default function IntelligenceDashboard() {
  const [predictions, setPredictions] = useState({ active: [], accuracy: {} });
  const [dreamInsights, setDreamInsights] = useState({ insights: [], active_predictions: [] });
  const [curiosity, setCuriosity] = useState({ total: 0, open: 0, top_gaps: [] });
  const [emotional, setEmotional] = useState({ current_stress: 0, trend: "stable", dominant_mood: "neutral" });
  const [evolution, setEvolution] = useState({ behavior_state: {}, experiments: {} });
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchAll = async () => {
    try {
      const [predRes, dreamRes, curiousRes, emoRes, evoRes] = await Promise.all([
        axios.get(`${API}/intelligence/predictions`).catch(() => ({ data: {} })),
        axios.get(`${API}/intelligence/dream-insights`).catch(() => ({ data: {} })),
        axios.get(`${API}/intelligence/curiosity-gaps`).catch(() => ({ data: {} })),
        axios.get(`${API}/emotional/state`).catch(() => ({ data: {} })),
        axios.get(`${API}/intelligence/self-evolution`).catch(() => ({ data: {} })),
      ]);
      setPredictions(predRes.data);
      setDreamInsights(dreamRes.data);
      setCuriosity(curiousRes.data);
      setEmotional(emoRes.data);
      setEvolution(evoRes.data);
      setLastRefresh(new Date());
    } catch (e) {
      console.error("Intelligence fetch error:", e);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 30000); // Refresh every 30s
    return () => clearInterval(id);
  }, []);

  const stressColor = emotional.current_stress > 70 ? "high" : emotional.current_stress > 40 ? "med" : "low";

  return (
    <div className="intel-dashboard">
      <div className="intel-header">
        <h2>LOVE's Mind</h2>
        <span className="intel-refresh" onClick={fetchAll}>
          {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : "Loading..."}
        </span>
      </div>

      <div className="intel-grid">
        {/* Predictions */}
        <Card title="Predictions" icon={ICON.prediction} accent="blue">
          {predictions.accuracy?.overall_accuracy !== undefined && (
            <div className="intel-stat">
              Accuracy: {Math.round(predictions.accuracy.overall_accuracy * 100)}%
            </div>
          )}
          {predictions.active?.length === 0 ? (
            <p className="intel-empty">No active predictions yet. LOVE is still learning your patterns.</p>
          ) : (
            predictions.active.map((p, i) => <PredictionItem key={i} pred={p} />)
          )}
        </Card>

        {/* Dream Insights */}
        <Card title="Deep Insights" icon={ICON.insight} accent="purple">
          {dreamInsights.insights?.length === 0 ? (
            <p className="intel-empty">No insights yet. LOVE reflects during idle time.</p>
          ) : (
            dreamInsights.insights.map((ins, i) => <InsightItem key={i} text={ins} />)
          )}
          {dreamInsights.world_model_people > 0 && (
            <div className="intel-footer">
              World model: {dreamInsights.world_model_people} people, {dreamInsights.world_model_routines} routines
            </div>
          )}
        </Card>

        {/* Curiosity Gaps */}
        <Card title="Curiosity" icon={ICON.gap} accent="orange">
          <div className="intel-stat">
            {curiosity.open} open / {curiosity.total} total gaps
          </div>
          {!curiosity.top_gaps || curiosity.top_gaps.length === 0 ? (
            <p className="intel-empty">No knowledge gaps. LOVE knows everything... or does it?</p>
          ) : (
            curiosity.top_gaps.map((g, i) => <GapItem key={i} gap={g} />)
          )}
        </Card>

        {/* Emotional State */}
        <Card title="Emotional State" icon={ICON.emotion} accent="pink">
          <div className={`intel-stress-bar intel-stress-${stressColor}`}>
            <div className="intel-stress-fill" style={{ width: `${emotional.current_stress}%` }} />
            <span className="intel-stress-label">Stress: {Math.round(emotional.current_stress)}/100</span>
          </div>
          <div className="intel-emotion-row">
            <span className="intel-badge">Trend: {emotional.trend}</span>
            <span className="intel-badge">Mood: {emotional.dominant_mood}</span>
          </div>
        </Card>

        {/* Self-Evolution */}
        <Card title="Self-Evolution" icon={ICON.evolve} accent="green">
          {evolution.behavior_state?.active_experiments?.length > 0 ? (
            <>
              <div className="intel-stat">{evolution.behavior_state.active_experiments.length} active experiments</div>
              {evolution.behavior_state.active_experiments.map((exp, i) => (
                <div key={i} className="intel-item">
                  <span className="intel-bullet">◬</span>
                  <span className="intel-item-text">{exp}</span>
                </div>
              ))}
            </>
          ) : (
            <p className="intel-empty">No active experiments. LOVE is stable.</p>
          )}
        </Card>

        {/* World Model */}
        <Card title="World Model" icon={ICON.world} accent="cyan">
          <div className="intel-world-stats">
            <div className="intel-world-stat">
              <span className="intel-world-num">{dreamInsights.world_model_people || 0}</span>
              <span className="intel-world-label">People</span>
            </div>
            <div className="intel-world-stat">
              <span className="intel-world-num">{dreamInsights.world_model_routines || 0}</span>
              <span className="intel-world-label">Routines</span>
            </div>
            <div className="intel-world-stat">
              <span className="intel-world-num">{dreamInsights.active_predictions?.length || 0}</span>
              <span className="intel-world-label">Patterns</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
