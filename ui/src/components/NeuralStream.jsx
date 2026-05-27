import { useState } from "react";

function ThinkingDot({ thinking }) {
  const [open, setOpen] = useState(false);
  if (!thinking) return null;
  return (
    <div className="thinking-wrap">
      <button className="thinking-toggle" onClick={() => setOpen(o => !o)}>
        ◈ {open ? "COLLAPSE REASONING MATRIX" : "EXPAND REASONING MATRIX"}
      </button>
      {open && <div className="thinking-body">{thinking}</div>}
    </div>
  );
}

export default function NeuralStream({ messages, bottomRef, loading }) {
  return (
    <div className="hud-stream">
      {messages.map((m, i) => {
        const isUser = m.role === "user";
        return (
          <div key={i} className={`stream-event ${isUser ? "user" : "love"}`}>
            <div className="stream-meta">
              <span className="stream-role">{isUser ? "OPERATOR" : "LOVE_AGI"}</span>
              <span className="stream-time">{m.time}</span>
              {m.push && <span style={{color: "var(--core-accent)"}}> [AUTONOMOUS SIGNAL]</span>}
            </div>
            
            <div className={`stream-bubble ${m.push ? "push-event" : ""}`}>
              {m.text}
            </div>
            
            {!isUser && m.thinking && <ThinkingDot thinking={m.thinking} />}
          </div>
        );
      })}
      
      {loading && (
        <div className="stream-event love">
          <div className="stream-meta">
            <span className="stream-role">LOVE_AGI</span>
          </div>
          <div className="stream-bubble" style={{ opacity: 0.5 }}>
            Processing neural pathways...
          </div>
        </div>
      )}
      
      <div ref={bottomRef} style={{ height: 40 }} />
    </div>
  );
}
