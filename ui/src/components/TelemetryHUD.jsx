export default function TelemetryHUD({ ctx }) {
  if (!ctx) {
    return (
      <div className="glass-panel">
        <h3>System Telemetry</h3>
        <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: 12 }}>
          Establishing neural link...
        </div>
      </div>
    );
  }

  const m = (label, val, state = "") => (
    <div className="metric-row">
      <span className="metric-label">{label}</span>
      <span className={`metric-val ${state}`}>{val}</span>
    </div>
  );

  const formatBattery = () => {
    if (ctx.battery == null) return "UNKNOWN";
    const v = Math.round(ctx.battery);
    return `${v}% ${ctx.battery_charging ? "⚡" : ""}`;
  };

  const isFocusing = ctx.active_window && ctx.active_window !== "unknown" && ctx.active_window !== "N/A";

  return (
    <>
      <div className="glass-panel">
        <h3>Biological Sync</h3>
        {m("Vitals Status", "ONLINE", "low")}
        {m("Local Time", ctx.local_time || "N/A")}
        {m("Phase", ctx.time_of_day?.toUpperCase() || "N/A")}
        {m("Meeting State", ctx.is_in_meeting ? "ENGAGED" : "CLEAR", ctx.is_in_meeting ? "med" : "low")}
      </div>

      <div className="glass-panel">
        <h3>Workstation Node</h3>
        {m("Active App", ctx.active_app?.toUpperCase() || "IDLE", isFocusing ? "med" : "low")}
        <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--text-muted)", marginBottom: 12, wordBreak: "break-all" }}>
          {ctx.active_window || "NO WINDOW DETECTED"}
        </div>
        {m("Power Core", formatBattery(), ctx.battery < 20 && !ctx.battery_charging ? "high" : "low")}
        {m("System Load", ctx.activity?.toUpperCase() || "IDLE")}
      </div>

      <div className="glass-panel">
        <h3>Cognitive Load</h3>
        {m("Unread Comms", ctx.unread_important || 0, ctx.unread_important > 0 ? "med" : "low")}
        {m("Tasks Due", ctx.tasks_due_today || 0, ctx.tasks_due_today > 0 ? "med" : "low")}
        {m("Overdue", ctx.tasks_overdue || 0, ctx.tasks_overdue > 0 ? "high" : "low")}
        {m("Cycles Logged", `${(ctx.hours_worked || 0).toFixed(1)}H`)}
      </div>

      {ctx.suggested_action && (
        <div className="glass-panel" style={{ borderColor: "var(--core-accent)" }}>
          <h3 style={{ color: "var(--core-accent)" }}>Suggested Vector</h3>
          <div style={{ color: "#fff", fontSize: 14 }}>{ctx.suggested_action}</div>
        </div>
      )}
    </>
  );
}
