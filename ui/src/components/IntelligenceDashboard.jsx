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
  circuit: "◍",
  pattern: "◇",
  cache: "◐",
  context: "⬡",
  graph: "◯",
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

function ModernModuleItem({ name, stats }) {
  const isUp = stats && (stats.available || stats.running || stats.total_calls !== undefined || stats.active_agents !== undefined);
  return (
    <div className="intel-item">
      <span className="intel-bullet">{isUp ? "●" : "○"}</span>
      <span className="intel-item-text">{name.replace(/_/g, " ")}</span>
      {stats && (
        <span className={`intel-badge ${isUp ? "intel-badge-high" : "intel-badge-low"}`}>
          {isUp ? "active" : "offline"}
        </span>
      )}
    </div>
  );
}

export default function IntelligenceDashboard() {
  const [predictions, setPredictions] = useState({ active: [], accuracy: {} });
  const [dreamInsights, setDreamInsights] = useState({ insights: [], active_predictions: [] });
  const [curiosity, setCuriosity] = useState({ total: 0, open: 0, top_gaps: [] });
  const [emotional, setEmotional] = useState({ current_stress: 0, trend: "stable", dominant_mood: "neutral" });
  const [evolution, setEvolution] = useState({ behavior_state: {}, experiments: {} });
  const [modernStats, setModernStats] = useState({});
  const [patternInsights, setPatternInsights] = useState([]);
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

      // Fetch modern module stats
      const modernPromises = [
        api.get(`/modern/patterns/insights`).catch(() => ({ data: {} })),
        api.get(`/modern/context/stats`).catch(() => ({ data: {} })),
        api.get(`/modern/cache/stats`).catch(() => ({ data: {} })),
        api.get(`/modern/kg/stats`).catch(() => ({ data: {} })),
      ];
      const [patRes, ctxRes, cacheRes, kgRes] = await Promise.all(modernPromises);
      if (patRes.data?.insights) setPatternInsights(patRes.data.insights);
      setModernStats({
        context_window: ctxRes.data || {},
        response_cache: cacheRes.data || {},
        knowledge_graph: kgRes.data || {},
        evolution_health: evoRes.data?.health || {},
      });

      setLastRefresh(new Date());
    } catch (e) {
      console.error("Intelligence fetch error:", e);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 30000);
    return () => clearInterval(id);
  }, []);

  const stressColor = emotional.current_stress > 70 ? "high" : emotional.current_stress > 40 ? "med" : "low";

  const modernModules = [
    { name: "llm_manager", stats: modernStats.evolution_health?.llm_manager },
    { name: "graph_rag", stats: modernStats.evolution_health?.graph_rag },
    { name: "prompt_optimizer", stats: modernStats.evolution_health?.prompt_optimizer },
    { name: "self_reflection", stats: modernStats.evolution_health?.self_reflection },
    { name: "conversation_quality", stats: modernStats.evolution_health?.conversation_quality },
    { name: "predictive_maintenance", stats: modernStats.evolution_health?.predictive_maintenance },
    { name: "multi_agent_orchestrator", stats: modernStats.evolution_health?.multi_agent_orchestrator },
    { name: "intent_predictor", stats: modernStats.evolution_health?.intent_predictor },
    { name: "personality_adapter", stats: modernStats.evolution_health?.personality_adapter },
    { name: "response_cache", stats: modernStats.evolution_health?.response_cache },
    { name: "context_window_manager", stats: modernStats.evolution_health?.context_window_manager },
    { name: "user_pattern_detector", stats: modernStats.evolution_health?.user_pattern_detector },
    { name: "goal_drift_detector", stats: modernStats.evolution_health?.goal_drift_detector },
    { name: "cross_modal_fusion", stats: modernStats.evolution_health?.cross_modal_fusion },
    { name: "emotional_resonance", stats: modernStats.evolution_health?.emotional_resonance },
    { name: "knowledge_graph_builder", stats: modernStats.evolution_health?.knowledge_graph_builder },
    { name: "adaptive_learning_rate", stats: modernStats.evolution_health?.adaptive_learning_rate },
    { name: "conversation_continuity", stats: modernStats.evolution_health?.conversation_continuity },
    { name: "memory_compressor", stats: modernStats.evolution_health?.memory_compressor },
    { name: "semantic_search_optimizer", stats: modernStats.evolution_health?.semantic_search_optimizer },
    { name: "emotion_aware_response", stats: modernStats.evolution_health?.emotion_aware_response },
    { name: "knowledge_injector", stats: modernStats.evolution_health?.knowledge_injector },
    { name: "conversation_summarizer", stats: modernStats.evolution_health?.conversation_summarizer },
    { name: "context_aware_prioritizer", stats: modernStats.evolution_health?.context_aware_prioritizer },
    { name: "wellness_nudger", stats: modernStats.evolution_health?.wellness_nudger },
    { name: "notification_filter", stats: modernStats.evolution_health?.notification_filter },
    { name: "deep_work_protector", stats: modernStats.evolution_health?.deep_work_protector },
    { name: "energy_forecaster", stats: modernStats.evolution_health?.energy_forecaster },
    { name: "smart_break_suggester", stats: modernStats.evolution_health?.smart_break_suggester },
    { name: "habit_streak_tracker", stats: modernStats.evolution_health?.habit_streak_tracker },
    { name: "sleep_analyzer", stats: modernStats.evolution_health?.sleep_analyzer },
    { name: "social_connection_monitor", stats: modernStats.evolution_health?.social_connection_monitor },
    { name: "learning_path_optimizer", stats: modernStats.evolution_health?.learning_path_optimizer },
    { name: "focus_recovery_tracker", stats: modernStats.evolution_health?.focus_recovery_tracker },
    { name: "decision_journal", stats: modernStats.evolution_health?.decision_journal },
    { name: "mood_journal", stats: modernStats.evolution_health?.mood_journal },
    { name: "values_alignment_checker", stats: modernStats.evolution_health?.values_alignment_checker },
    { name: "gratitude_tracker", stats: modernStats.evolution_health?.gratitude_tracker },
    { name: "energy_audit_tool", stats: modernStats.evolution_health?.energy_audit_tool },
    { name: "time_audit_tool", stats: modernStats.evolution_health?.time_audit_tool },
    { name: "reflection_prompt_generator", stats: modernStats.evolution_health?.reflection_prompt_generator },
    { name: "proactive_preparation_engine", stats: modernStats.evolution_health?.proactive_preparation_engine },
    { name: "context_switching_minimizer", stats: modernStats.evolution_health?.context_switching_minimizer },
    { name: "task_batch_optimizer", stats: modernStats.evolution_health?.task_batch_optimizer },
    { name: "meeting_optimizer", stats: modernStats.evolution_health?.meeting_optimizer },
    { name: "finance_pattern_detector", stats: modernStats.evolution_health?.finance_pattern_detector },
    { name: "nutrition_analyzer", stats: modernStats.evolution_health?.nutrition_analyzer },
    { name: "exercise_optimizer", stats: modernStats.evolution_health?.exercise_optimizer },
    { name: "meditation_coach", stats: modernStats.evolution_health?.meditation_coach },
    { name: "reading_tracker", stats: modernStats.evolution_health?.reading_tracker },
    { name: "writing_coach", stats: modernStats.evolution_health?.writing_coach },
    { name: "creativity_booster", stats: modernStats.evolution_health?.creativity_booster },
    { name: "stress_response_coach", stats: modernStats.evolution_health?.stress_response_coach },
    { name: "communication_analyzer", stats: modernStats.evolution_health?.communication_analyzer },
    { name: "goal_progress_visualizer", stats: modernStats.evolution_health?.goal_progress_visualizer },
    { name: "life_balance_wheel", stats: modernStats.evolution_health?.life_balance_wheel },
    { name: "productivity_gamifier", stats: modernStats.evolution_health?.productivity_gamifier },
    { name: "environment_optimizer", stats: modernStats.evolution_health?.environment_optimizer },
    { name: "weather_suggester", stats: modernStats.evolution_health?.weather_suggester },
    { name: "travel_planner", stats: modernStats.evolution_health?.travel_planner },
    { name: "gift_idea_generator", stats: modernStats.evolution_health?.gift_idea_generator },
    { name: "emergency_preparedness_tracker", stats: modernStats.evolution_health?.emergency_preparedness_tracker },
    { name: "home_maintenance_scheduler", stats: modernStats.evolution_health?.home_maintenance_scheduler },
    { name: "career_path_mapper", stats: modernStats.evolution_health?.career_path_mapper },
    { name: "skill_gap_analyzer", stats: modernStats.evolution_health?.skill_gap_analyzer },
    { name: "document_organizer", stats: modernStats.evolution_health?.document_organizer },
    { name: "password_health_checker", stats: modernStats.evolution_health?.password_health_checker },
    { name: "subscription_manager", stats: modernStats.evolution_health?.subscription_manager },
    { name: "digital_declutterer", stats: modernStats.evolution_health?.digital_declutterer },
    { name: "event_planner", stats: modernStats.evolution_health?.event_planner },
    { name: "habit_builder", stats: modernStats.evolution_health?.habit_builder },
    { name: "morning_routine_designer", stats: modernStats.evolution_health?.morning_routine_designer },
    { name: "evening_wind_down_coach", stats: modernStats.evolution_health?.evening_wind_down_coach },
    { name: "conflict_resolution_coach", stats: modernStats.evolution_health?.conflict_resolution_coach },
    { name: "boundaries_coach", stats: modernStats.evolution_health?.boundaries_coach },
    { name: "assertiveness_trainer", stats: modernStats.evolution_health?.assertiveness_trainer },
    { name: "active_listening_coach", stats: modernStats.evolution_health?.active_listening_coach },
    { name: "self_compassion_coach", stats: modernStats.evolution_health?.self_compassion_coach },
    { name: "forgiveness_tracker", stats: modernStats.evolution_health?.forgiveness_tracker },
    { name: "vulnerability_builder", stats: modernStats.evolution_health?.vulnerability_builder },
    { name: "trust_builder", stats: modernStats.evolution_health?.trust_builder },
  ].filter(m => m.stats);

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
        </Card>

        {/* Modern Systems */}
        <Card title="Modern Systems" icon={ICON.circuit} accent="cyan">
          {modernModules.length === 0 ? (
            <p className="intel-empty">Loading modern module status...</p>
          ) : (
            <>
              <div className="intel-stat">{modernModules.length} active modern modules</div>
              <div className="intel-health-grid">
                {modernModules.map((mod) => (
                  <span key={mod.name} className="intel-health-chip up">
                    ● {mod.name.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </>
          )}
        </Card>

        {/* Pattern Insights */}
        <Card title="Pattern Insights" icon={ICON.pattern} accent="purple">
          {patternInsights.length === 0 ? (
            <p className="intel-empty">No patterns detected yet. LOVE is observing your routines.</p>
          ) : (
            patternInsights.slice(0, 5).map((insight, i) => (
              <div key={i} className="intel-item">
                <span className="intel-bullet">◇</span>
                <span className="intel-item-text">{insight.insight || insight.description || insight.text}</span>
                {insight.confidence && (
                  <span className={`intel-badge intel-badge-${insight.confidence > 0.5 ? "high" : "med"}`}>
                    {Math.round(insight.confidence * 100)}%
                  </span>
                )}
              </div>
            ))
          )}
        </Card>

        {/* Context & Cache Stats */}
        <Card title="System Metrics" icon={ICON.cache} accent="blue">
          {modernStats.context_window?.total_optimizations !== undefined && (
            <div className="intel-stat">
              Context optimizations: {modernStats.context_window.total_optimizations}
            </div>
          )}
          {modernStats.response_cache?.total_requests !== undefined && (
            <div className="intel-stat">
              Cache hit rate: {Math.round((modernStats.response_cache.cache_hits / Math.max(modernStats.response_cache.total_requests, 1)) * 100)}%
            </div>
          )}
          {modernStats.knowledge_graph?.total_entities !== undefined && (
            <div className="intel-stat">
              Knowledge graph: {modernStats.knowledge_graph.total_entities} entities, {modernStats.knowledge_graph.total_relations} relations
            </div>
          )}
          {modernStats.context_window?.total_optimizations === undefined &&
           modernStats.response_cache?.total_requests === undefined &&
           modernStats.knowledge_graph?.total_entities === undefined && (
            <p className="intel-empty">Metrics loading...</p>
          )}
        </Card>

        {/* Daily Briefing Placeholder */}
        <Card title="Today" icon={ICON.clock} accent="orange">
          <p className="intel-empty">
            {lastRefresh
              ? `Last updated at ${lastRefresh.toLocaleTimeString()}`
              : "Loading daily summary..."}
          </p>
        </Card>
      </div>
    </div>
  );
}
