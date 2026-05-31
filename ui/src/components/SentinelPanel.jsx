import { useState, useEffect, useCallback } from "react";
import api, { API } from '../api';
const API_BASE = window.location.origin;
import "./SentinelPanel.css";

const STATE_EMOJI = { active: "●", idle: "◐", away: "○", sleeping: "☾", unknown: "?" };
const STATE_COLOR = { active: "#4ade80", idle: "#fbbf24", away: "#f87171", sleeping: "#818cf8", unknown: "#6b7280" };
const ACTIVITY_EMOJI = { work: "⌨", meeting: "◉", creative: "✦", browsing: "◎", gaming: "▶", idle: "◻", other: "·" };

function PresenceCard({ presence }) {
  if (!presence) return null;
  const color = STATE_COLOR[presence.state] || STATE_COLOR.unknown;
  return (
    <div className="snt-presence" style={{ borderColor: color + "40" }}>
      <div className="snt-presence-top">
        <span className="snt-state-dot" style={{ background: color }} />
        <span className="snt-state-label" style={{ color }}>{presence.state}</span>
        <span className="snt-activity-icon">{ACTIVITY_EMOJI[presence.activity] || "·"}</span>
        <span className="snt-activity-label">{presence.activity}</span>
      </div>
      <div className="snt-presence-meta">
        {presence.active_app && <span className="snt-chip">▣ {presence.active_app.slice(0, 40)}</span>}
        {presence.focus_depth > 0 && (
          <span className="snt-chip snt-chip-focus">
            Focus: {Math.round(presence.focus_depth * 100)}%
          </span>
        )}
        {presence.idle_seconds > 60 && (
          <span className="snt-chip snt-chip-idle">
            Idle: {Math.round(presence.idle_seconds / 60)}m
          </span>
        )}
      </div>
    </div>
  );
}

function EventItem({ event }) {
  const priorityColor = {
    critical: "#ef4444", high: "#f59e0b", normal: "#6b7280", low: "#374151"
  };
  const catIcon = {
    alert: "!!", nudge: "→", action: "⚡", summary: "◷", health: "♡", presence: "●"
  };

  return (
    <div className={`snt-event snt-event-${event.priority}`}>
      <span className="snt-event-icon">{catIcon[event.category] || "·"}</span>
      <div className="snt-event-content">
        <div className="snt-event-title">{event.title}</div>
        <div className="snt-event-detail">{event.detail}</div>
        {event.acted && <span className="snt-event-acted">autonomous action taken</span>}
      </div>
      <span className="snt-event-time">
        {event.timestamp ? new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
      </span>
    </div>
  );
}

export default function SentinelPanel() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);
  const [orchestratorNarrative, setOrchestratorNarrative] = useState([]);

  const load = useCallback(async () => {
    try {
      const [sentinelRes, narrativeRes] = await Promise.all([
        api.get(`/neural/sentinel/status`),
        fetch(`${API_BASE}/orchestrator/master/narrative?limit=10`).then(r => r.ok ? r.json() : { narrative: [] }).catch(() => ({ narrative: [] })),
      ]);
      setStatus(sentinelRes.data);
      // Filter orchestrator narrative for sentinel-related events
      const allNarrative = narrativeRes.narrative || [];
      const sentinelNarrative = allNarrative.filter(n =>
        n.event && (n.event.includes("sentinel") || n.event.includes("presence") || n.event.includes("system_load"))
      );
      setOrchestratorNarrative(sentinelNarrative);
      setError(null);
    } catch (e) {
      console.error("[Sentinel] load failed:", e);
      setError("Backend offline or Sentinel not started");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  const forceScan = async () => {
    setScanning(true);
    try {
      const res = await api.post(`/neural/sentinel/scan`);
      setStatus(res.data);
    } catch (e) {
      console.error("[Sentinel] scan failed:", e);
    }
    setScanning(false);
  };

  const markAway = async () => {
    try {
      await api.post(`/neural/sentinel/away`, { reason: "manual" });
      load();
    } catch (e) { console.error("[Sentinel] mark away failed:", e); }
  };

  const markBack = async () => {
    try {
      await api.post(`/neural/sentinel/back`);
      load();
    } catch (e) { console.error("[Sentinel] mark back failed:", e); }
  };

  if (loading) return <div className="snt-panel"><div className="snt-loading">Connecting to Sentinel...</div></div>;
  if (error) return <div className="snt-panel"><div className="snt-offline">{error}</div></div>;

  const events = status?.recent_events || [];
  const deepWork = status?.deep_work;
  const health = status?.subsystem_health || {};
  const decisions = status?.decisions_today || 0;

  return (
    <div className="snt-panel">
      <div className="snt-header">
        <div>
          <h2>Sentinel</h2>
          <div className="snt-subtitle">Self-Monitoring Protocol — always watching over you</div>
        </div>
        <div className="snt-header-right">
          <span className={`snt-running ${status?.running ? "snt-on" : "snt-off"}`}>
            {status?.running ? "ACTIVE" : "OFFLINE"}
          </span>
          <span className="snt-decisions">{decisions} decision{decisions !== 1 ? "s" : ""} today</span>
        </div>
      </div>

      {/* Presence */}
      <PresenceCard presence={status?.presence} />

      {/* Status bar */}
      <div className="snt-bar">
        {deepWork && <span className="snt-badge snt-badge-deep">Deep Work Mode</span>}
        {status?.state?.overnight_mode && <span className="snt-badge snt-badge-night">Overnight Mode</span>}
        {status?.state?.away_since && <span className="snt-badge snt-badge-away">Away since {new Date(status.state.away_since).toLocaleTimeString()}</span>}
      </div>

      {/* Controls */}
      <div className="snt-controls">
        <button className={`snt-btn snt-btn-scan${scanning ? " snt-scanning" : ""}`} onClick={forceScan} disabled={scanning}>
          {scanning ? "Scanning..." : "Force Scan"}
        </button>
        <button className="snt-btn snt-btn-away" onClick={markAway}>Mark Away</button>
        <button className="snt-btn snt-btn-back" onClick={markBack}>I'm Back</button>
      </div>

      {/* Subsystem Health */}
      {Object.keys(health).length > 0 && (
        <div className="snt-health">
          <div className="snt-section-label">Subsystem Health</div>
          <div className="snt-health-grid">
            {Object.entries(health).map(([name, info]) => (
              <div key={name} className={`snt-health-item snt-health-${info.status}`}>
                <span className="snt-health-name">{name}</span>
                <span className="snt-health-status">{info.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modern AI Module Health */}
      {Object.keys(health).length > 0 && (
        <div className="snt-modern-modules">
          <div className="snt-section-label">Modern AI Systems</div>
          <div className="snt-modern-grid">
            {Object.entries(health)
              .filter(([name]) => [
                "llm_manager", "graph_rag", "prompt_optimizer", "self_reflection",
                "conversation_quality", "predictive_maintenance", "multi_agent_orchestrator",
                "intent_predictor", "personality_adapter", "response_cache",
                "context_window_manager", "user_pattern_detector", "goal_drift_detector",
                "cross_modal_fusion", "emotional_resonance", "knowledge_graph_builder",
                "adaptive_learning_rate", "conversation_continuity",
                "memory_compressor", "semantic_search_optimizer", "emotion_aware_response",
                "knowledge_injector", "conversation_summarizer", "context_aware_prioritizer",
                "wellness_nudger", "notification_filter", "deep_work_protector",
                "energy_forecaster", "smart_break_suggester", "habit_streak_tracker",
                "sleep_analyzer", "social_connection_monitor", "learning_path_optimizer",
                "focus_recovery_tracker", "decision_journal", "mood_journal",
                "values_alignment_checker", "gratitude_tracker", "energy_audit_tool",
                "time_audit_tool", "reflection_prompt_generator",
                "proactive_preparation_engine", "context_switching_minimizer",
                "task_batch_optimizer", "meeting_optimizer",
                "finance_pattern_detector", "nutrition_analyzer",
                "exercise_optimizer", "meditation_coach",
                "reading_tracker", "writing_coach",
                "creativity_booster", "stress_response_coach",
                "communication_analyzer", "goal_progress_visualizer",
                "life_balance_wheel", "productivity_gamifier",
                "environment_optimizer", "weather_suggester",
                "travel_planner", "gift_idea_generator",
                "emergency_preparedness_tracker", "home_maintenance_scheduler",
                "career_path_mapper", "skill_gap_analyzer",
                "document_organizer", "password_health_checker",
                "subscription_manager", "digital_declutterer",
                "event_planner", "habit_builder",
                "morning_routine_designer", "evening_wind_down_coach",
                "conflict_resolution_coach", "boundaries_coach",
                "assertiveness_trainer", "active_listening_coach",
                "self_compassion_coach", "forgiveness_tracker",
                "vulnerability_builder", "trust_builder",
                "curiosity_spark", "play_coach",
                "adventure_planner", "wonder_tracker",
                "meaning_mapper", "purpose_navigator",
                "legacy_builder", "death_awareness_coach",
                "flow_state_coach", "savoring_trainer",
                "presence_detector", "intuition_trainer",
                "resilience_builder", "growth_mindset_coach",
                "adaptability_trainer", "antifragility_tracker",
                "discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator",
                "energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian",
                "identity_designer", "habit_architect",
                "environment_curator", "ritual_master",
                "values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager",
                "emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier",
                "deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach",
                "sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator",
                "digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager",
                "stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier",
                "creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter",
                "curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller",
                "purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier",
                "courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier",
                "humor_playfulness_trainer", "joy_cultivator",
                "celebration_architect", "spontaneity_generator",
                "forgiveness_coach", "reconciliation_builder",
                "trust_architect", "repair_specialist",
                "deep_listener", "conflict_navigator",
                "assertiveness_builder", "boundary_architect",
                "discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator",
                "energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian",
                "identity_designer", "habit_architect",
                "environment_curator", "ritual_master",
                "values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager",
                "emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier",
                "deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach",
                "sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator",
                "digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager",
                "stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier",
                "creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter",
                "curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller",
                "purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier",
                "courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier",
                "humor_playfulness_trainer", "joy_cultivator",
                "celebration_architect", "spontaneity_generator",
                "forgiveness_coach", "reconciliation_builder",
                "trust_architect", "repair_specialist",
                "deep_listener", "conflict_navigator",
                "assertiveness_builder", "boundary_architect",
                "flow_state_coach", "savoring_trainer",
                "presence_detector", "intuition_trainer",
                "resilience_builder", "growth_mindset_coach",
                "adaptability_trainer", "antifragility_tracker",
                "discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator",
                "energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian",
                "identity_designer", "habit_architect",
                "environment_curator", "ritual_master",
                "values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager",
                "emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier",
                "deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach",
                "sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator",
                "digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager",
                "stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier",
                "creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter",
                "curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller",
                "purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier",
                "courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier",
                "humor_playfulness_trainer", "joy_cultivator",
                "celebration_architect", "spontaneity_generator",
                "forgiveness_coach", "reconciliation_builder",
                "trust_architect", "repair_specialist",
                "deep_listener", "conflict_navigator",
                "assertiveness_builder", "boundary_architect",
                "discipline_trainer", "consistency_coach",
                "accountability_partner", "progress_celebrator",
                "energy_protector", "boundary_enforcer",
                "time_sovereign", "attention_guardian",
                "identity_designer", "habit_architect",
                "environment_curator", "ritual_master",
                "values_explorer", "belief_examiner",
                "shadow_integrator", "inner_critic_manager",
                "emotional_intelligence_trainer", "empathy_builder",
                "compassion_generator", "gratitude_amplifier",
                "deep_work_enabler", "recovery_optimizer",
                "peak_performance_tracker", "mindful_productivity_coach",
                "sleep_optimizer", "nutrition_coach",
                "movement_tracker", "health_integrator",
                "digital_minimalism_coach", "focus_ritual_designer",
                "attention_recovery_specialist", "cognitive_load_manager",
                "stress_resilience_trainer", "emotional_regulation_coach",
                "mindfulness_trainer", "presence_amplifier",
                "creativity_catalyst", "innovation_spark_generator",
                "problem_reframer", "perspective_shifter",
                "curiosity_cultivator", "learning_acceleration_engine",
                "knowledge_synthesizer", "wisdom_distiller",
                "purpose_clarity_engine", "legacy_builder",
                "impact_maximizer", "meaning_amplifier",
                "courage_coach", "risk_intelligence_trainer",
                "vulnerability_builder", "authenticity_amplifier",
                "humor_playfulness_trainer", "joy_cultivator",
                "celebration_architect", "spontaneity_generator"
              ].includes(name))
              .map(([name, info]) => (
                <div key={name} className={`snt-health-item snt-health-${info.status}`}>
                  <span className="snt-health-name">{name.replace(/_/g, " ")}</span>
                  <span className="snt-health-status">{info.status}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Hour summary */}
      {status?.state?.last_hour_summary && (
        <div className="snt-hour-summary">
          <div className="snt-section-label">This Hour</div>
          <div className="snt-hour-text">{status.state.last_hour_summary.summary}</div>
        </div>
      )}

      {/* Orchestrator Response */}
      {orchestratorNarrative.length > 0 && (
        <div className="snt-orchestrator-response">
          <div className="snt-section-label">Orchestrator Response ({orchestratorNarrative.length})</div>
          <div className="snt-orchestrator-list">
            {orchestratorNarrative.slice().reverse().map((entry, i) => (
              <div key={i} className={`snt-orchestrator-item ${entry.importance || 'normal'}`}>
                <span className="snt-orchestrator-time">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
                </span>
                <span className="snt-orchestrator-event">{entry.event}</span>
                <span className="snt-orchestrator-detail">{entry.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event log */}
      <div className="snt-events">
        <div className="snt-section-label">Recent Events ({events.length})</div>
        {events.length === 0 ? (
          <div className="snt-empty">Sentinel is watching. No events yet.</div>
        ) : (
          <div className="snt-event-list">
            {events.slice().reverse().map((e, i) => (
              <EventItem key={e.id || i} event={e} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
