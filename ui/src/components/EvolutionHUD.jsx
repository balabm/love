export default function EvolutionHUD({ evolution, predictions }) {
  const m = (label, val, state = "") => (
    <div className="metric-row">
      <span className="metric-label">{label}</span>
      <span className={`metric-val ${state}`}>{val}</span>
    </div>
  );

  return (
    <>
      <div className="glass-panel">
        <h3>Cognitive Evolution</h3>
        {!evolution ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>Awaiting metrics...</div>
        ) : (
          <>
            {m("Generation", `GEN-${evolution.generation}`)}
            {m("Total Lessons", evolution.total_lessons_learned)}
            {m("Base Memory", `${evolution.prompt_size_bytes} B`)}
            <div style={{ marginTop: 12, fontSize: 13, color: "var(--text-muted)", fontStyle: "italic" }}>
              Last updated: {new Date(evolution.last_evolution).toLocaleTimeString()}
            </div>
          </>
        )}
      </div>

      <div className="glass-panel">
        <h3>Neural Predictions</h3>
        {!predictions?.active?.length ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>No active predictions in matrix.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {predictions.active.slice(0, 3).map((p, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.05)", padding: 12, borderRadius: 6 }}>
                <div style={{ fontSize: 13, color: "#fff", marginBottom: 6 }}>{p.prediction}</div>
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)" }}>
                  <span>Conf: {Math.round(p.confidence * 100)}%</span>
                  <span>{new Date(p.expires_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="glass-panel">
        <h3>Predictive Accuracy</h3>
        {!predictions?.accuracy ? (
          <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>Awaiting data...</div>
        ) : (
          <>
            {m("Total Resolved", predictions.accuracy.total_resolved)}
            {m("Correct Hits", predictions.accuracy.correct, "low")}
            {m("Accuracy Rate", `${Math.round(predictions.accuracy.accuracy_rate * 100)}%`, predictions.accuracy.accuracy_rate > 0.7 ? "low" : "med")}
          </>
        )}
      </div>
    </>
  );
}
