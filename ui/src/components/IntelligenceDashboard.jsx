import { useState, useEffect } from "react";
import api, { API } from '../api';
import "./IntelligenceDashboard.css";

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
        api.get(`/intelligence/predictions`).catch(() => ({ data: {} })),
        api.get(`/intelligence/dream-insights`).catch(() => ({ data: {} })),
        api.get(`/intelligence/curiosity-gaps`).catch(() => ({ data: {} })),
        api.get(`/emotional/state`).catch(() => ({ data: {} })),
        api.get(`/intelligence/self-evolution`).catch(() => ({ data: {} })),
      ]);
      if (predRes.data?.active) setPredictions(p => ({ ...p, ...predRes.data }));
      if (dreamRes.data?.insights) setDreamInsights(p => ({ ...p, ...dreamRes.data }));
      if (curiousRes.data?.top_gaps !== undefined) setCuriosity(p => ({ ...p, ...curiousRes.data }));
      if (emoRes.data?.dominant_mood) setEmotional(p => ({ ...p, ...emoRes.data }));
      if (evoRes.data?.behavior_state) setEvolution(p => ({ ...p, ...evoRes.data }));
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
          {!predictions.active || predictions.active.length === 0 ? (
            <p className="intel-empty">No active predictions yet. LOVE is still learning your patterns.</p>
          ) : (
            (predictions.active || []).map((p, i) => <PredictionItem key={i} pred={p} />)
          )}
        </Card>

        {/* Dream Insights */}
        <Card title="Deep Insights" icon={ICON.insight} accent="purple">
          {!dreamInsights.insights || dreamInsights.insights.length === 0 ? (
            <p className="intel-empty">No insights yet. LOVE reflects during idle time.</p>
          ) : (
            (dreamInsights.insights || []).map((ins, i) => <InsightItem key={i} text={ins} />)
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
            (curiosity.top_gaps || []).map((g, i) => <GapItem key={i} gap={g} />)
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

          {/* Evolution Integration */}
          {evolution.integration && (
            <div className="intel-subsection">
              <div className="intel-subtitle">Integration</div>
              <div className="intel-stat">
                {evolution.integration.running ? (
                  <span className="intel-loop-active">Loop Active</span>
                ) : (
                  "Stopped"
                )}
                {evolution.integration.last_full_cycle && ` — ${new Date(evolution.integration.last_full_cycle).toLocaleTimeString()}`}
              </div>
              {evolution.integration.statistics && (
                <div className="intel-micro-stats">
                  <span>{evolution.integration.statistics.total_code_modifications || 0} code mods</span>
                  <span>{evolution.integration.statistics.total_mutations_applied || 0} mutations</span>
                  <span>{evolution.integration.statistics.successful_cross_adoptions || 0} adoptions</span>
                </div>
              )}
              {evolution.health && (
                <div className="intel-subsection">
                  <div className="intel-subtitle">Health</div>
                  <div className="intel-health-grid">
                    {Object.entries(evolution.health).filter(([k]) => k !== "overall").map(([name, info]) => {
                      const isUp = info.running || info.available;
                      return (
                        <span key={name} className={`intel-health-chip ${isUp ? "up" : "down"}`}>
                          {isUp ? "●" : "○"} {name.replace(/_/g, " ")}
                        </span>
                      );
                    })}
                  </div>
                  {evolution.health.overall && (
                    <div className={`intel-overall-${evolution.health.overall}`}>
                      Overall: {evolution.health.overall}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Capability Gaps */}
          {evolution.capability_gaps && (
            <div className="intel-subsection">
              <div className="intel-subtitle">Capability Gaps</div>
              <div className="intel-stat">
                {evolution.capability_gaps.high_impact || 0} high-impact / {evolution.capability_gaps.total || 0} total
              </div>
              {evolution.capability_gaps.domains?.length > 0 && (
                <div className="intel-micro-stats">
                  {evolution.capability_gaps.domains.map((d, i) => (
                    <span key={i}>{d}</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Deployments */}
          {evolution.deployments && evolution.deployments.length > 0 && (
            <div className="intel-subsection">
              <div className="intel-subtitle">Deployments</div>
              {evolution.deployments.slice(-3).map((dep, i) => (
                <div key={i} className="intel-item">
                  <span className="intel-bullet">◈</span>
                  <span className="intel-item-text">{dep.version} — {dep.status}</span>
                </div>
              ))}
            </div>
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
