import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./AgentLoopPanel.css";

const API = "http://localhost:8000";

function ToolBadge({ name }) {
  const colors = {
    web_search: "blue",
    http_get: "blue",
    memory_recall: "purple",
    get_intelligence: "cyan",
    execute_shell: "orange",
    execute_terminal_command: "orange",
    write_file: "red",
    read_file: "green",
    list_directory: "green",
    send_notification: "pink",
    calculate: "teal",
    get_current_time: "gray",
    get_current_context: "cyan",
  };
  const color = colors[name] || "gray";
  return <span className={`agl-tool-badge agl-tool-${color}`}>{name}</span>;
}

function StepCard({ step, isLast }) {
  const [open, setOpen] = useState(isLast);

  return (
    <div className={`agl-step${isLast ? " agl-step-last" : ""}`}>
      <div className="agl-step-header" onClick={() => setOpen(o => !o)}>
        <span className="agl-step-num">Step {step.step}</span>
        {step.tool_name && <ToolBadge name={step.tool_name} />}
        <span className="agl-step-dur">{step.duration_ms}ms</span>
        <span className="agl-step-chevron">{open ? "▲" : "▼"}</span>
      </div>

      {open && (
        <div className="agl-step-body">
          {step.thought && (
            <div className="agl-thought">
              <div className="agl-label">Thought</div>
              <div className="agl-thought-text">{step.thought}</div>
            </div>
          )}
          {step.tool_name && (
            <div className="agl-action">
              <div className="agl-label">Action → {step.tool_name}</div>
              {Object.keys(step.tool_params || {}).length > 0 && (
                <pre className="agl-params">{JSON.stringify(step.tool_params, null, 2)}</pre>
              )}
            </div>
          )}
          {step.observation && step.observation !== "[final answer]" && (
            <div className="agl-obs">
              <div className="agl-label">Observation</div>
              <pre className="agl-obs-text">{step.observation}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ToolCard({ tool }) {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [params, setParams] = useState({});

  const paramKeys = Object.keys(tool.parameters || {});

  const runTool = async () => {
    setRunning(true);
    setResult(null);
    try {
      const res = await axios.post(`${API}/neural/agent/tool/run`, {
        tool_name: tool.name,
        params,
      });
      setResult(res.data.result || res.data.error || "no output");
    } catch {
      setResult("Request failed");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="agl-tool-card">
      <div className="agl-tool-name">{tool.name}</div>
      <div className="agl-tool-desc">{tool.description}</div>
      {paramKeys.length > 0 && (
        <div className="agl-tool-params-form">
          {paramKeys.map(k => (
            <input
              key={k}
              className="agl-param-input"
              placeholder={k}
              value={params[k] || ""}
              onChange={e => setParams(p => ({ ...p, [k]: e.target.value }))}
            />
          ))}
        </div>
      )}
      <button
        className={`agl-run-btn${running ? " agl-running" : ""}`}
        onClick={runTool}
        disabled={running}
      >
        {running ? "Running..." : "Run"}
      </button>
      {result && (
        <pre className="agl-tool-result">{result.slice(0, 500)}{result.length > 500 ? "\n…" : ""}</pre>
      )}
    </div>
  );
}

export default function AgentLoopPanel() {
  const [tab, setTab] = useState("loop"); // loop | tools
  const [query, setQuery] = useState("");
  const [maxSteps, setMaxSteps] = useState(6);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [tools, setTools] = useState([]);
  const [toolSearch, setToolSearch] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    if (tab === "tools" && tools.length === 0) {
      axios.get(`${API}/neural/agent/tools`)
        .then(r => setTools(r.data.tools || []))
        .catch(() => {});
    }
  }, [tab]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [result]);

  const runLoop = async () => {
    if (!query.trim() || running) return;
    setRunning(true);
    setResult(null);
    try {
      const res = await axios.post(`${API}/neural/agent/run`, {
        query: query.trim(),
        max_steps: maxSteps,
      });
      setResult(res.data);
    } catch (e) {
      setResult({ success: false, error: "Backend unreachable", steps: [] });
    } finally {
      setRunning(false);
    }
  };

  const filteredTools = tools.filter(t =>
    t.name.includes(toolSearch) || t.description.toLowerCase().includes(toolSearch.toLowerCase())
  );

  return (
    <div className="agl-panel">
      <div className="agl-header">
        <h2>Agent Loop</h2>
        <div className="agl-tabs">
          <button className={`agl-tab${tab === "loop" ? " active" : ""}`} onClick={() => setTab("loop")}>
            ReAct Loop
          </button>
          <button className={`agl-tab${tab === "tools" ? " active" : ""}`} onClick={() => setTab("tools")}>
            Tool Belt ({tools.length})
          </button>
        </div>
      </div>

      {tab === "loop" && (
        <>
          <div className="agl-input-row">
            <textarea
              className="agl-query-input"
              rows={3}
              placeholder="Give LOVE a task that needs real tools... e.g. 'Search for the current BTC price and compare to yesterday' or 'List the files in my project root'"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) runLoop(); }}
            />
            <div className="agl-input-controls">
              <label className="agl-steps-label">
                Max steps
                <input
                  type="number"
                  className="agl-steps-input"
                  min={1} max={15}
                  value={maxSteps}
                  onChange={e => setMaxSteps(parseInt(e.target.value) || 6)}
                />
              </label>
              <button
                className={`agl-go-btn${running ? " agl-running" : ""}`}
                onClick={runLoop}
                disabled={running || !query.trim()}
              >
                {running ? "Running..." : "Run Loop"}
              </button>
            </div>
          </div>

          {running && (
            <div className="agl-working">
              <span className="agl-pulse" /> LOVE is thinking and calling tools...
            </div>
          )}

          {result && (
            <div className="agl-result">
              {/* Summary bar */}
              <div className={`agl-result-bar${result.success ? " agl-ok" : " agl-err"}`}>
                <span>{result.success ? "Done" : "Failed"}</span>
                <span>{result.total_steps} steps</span>
                <span>{result.total_ms}ms</span>
                <span className="agl-reason">{result.stopped_reason}</span>
                {result.error && <span className="agl-err-msg">{result.error}</span>}
              </div>

              {/* Step trace */}
              {(result.steps || []).length > 0 && (
                <div className="agl-steps">
                  <div className="agl-section-label">Trace</div>
                  {result.steps.map((s, i) => (
                    <StepCard key={i} step={s} isLast={i === result.steps.length - 1} />
                  ))}
                </div>
              )}

              {/* Final answer */}
              {result.final_answer && (
                <div className="agl-final">
                  <div className="agl-section-label">Final Answer</div>
                  <div className="agl-final-text">{result.final_answer}</div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </>
      )}

      {tab === "tools" && (
        <>
          <input
            className="agl-tool-search"
            placeholder="Filter tools..."
            value={toolSearch}
            onChange={e => setToolSearch(e.target.value)}
          />
          <div className="agl-tools-grid">
            {filteredTools.map(t => (
              <ToolCard key={t.name} tool={t} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
