import { useState, useRef, useEffect } from 'react';
import api, { API } from '../api';
import './TerminalPanel.css';

const QUICK_COMMANDS = [
  { label: "UniProt Insulin", cmd: "python tools/bio_query.py uniprot insulin", icon: "🧬" },
  { label: "PubMed CRISPR", cmd: "python tools/bio_query.py pubmed CRISPR", icon: "📚" },
  { label: "ChEMBL Aspirin", cmd: "python tools/bio_query.py chembl aspirin", icon: "🧪" },
  { label: "Swarm Test", cmd: "python test_swarm.py", icon: "🐝" },
  { label: "System Info", cmd: "systeminfo | findstr /B /C:\"OS Name\" /C:\"OS Version\"", icon: "💻" },
  { label: "Active Ports", cmd: "netstat -ano | findstr LISTENING", icon: "🔌" },
  { label: "Git Status", cmd: "git status", icon: "🐙" },
  { label: "Workspace Files", cmd: "dir /B", icon: "📁" }
];

export default function TerminalPanel() {
  const [history, setHistory] = useState([
    { type: 'info', text: 'Welcome to LOVE AGI Neural Terminal v2.0.0' },
    { type: 'info', text: 'Type a command or choose a quick shortcut below to interact with the environment.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const terminalEndRef = useRef(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const executeCommand = async (cmdText) => {
    const trimmed = cmdText.trim();
    if (!trimmed) return;

    setHistory(prev => [...prev, { type: 'input', text: trimmed }]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post(`${API}/neural/terminal/run`, { command: trimmed });
      const output = res.data.output || '[No output returned]';
      setHistory(prev => [...prev, { type: 'output', text: output }]);
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Execution error';
      setHistory(prev => [...prev, { type: 'error', text: errMsg }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      executeCommand(input);
    }
  };

  const clearTerminal = () => {
    setHistory([
      { type: 'info', text: 'Terminal cleared. READY.' }
    ]);
  };

  return (
    <div className="terminal-panel">
      <header className="terminal-header">
        <div className="terminal-header-title">
          <span className="terminal-icon">📟</span>
          <h2>AGI Neural Terminal</h2>
        </div>
        <button className="clear-btn" onClick={clearTerminal}>Clear</button>
      </header>

      {/* Terminal Output */}
      <div className="terminal-output">
        {history.map((h, i) => (
          <div key={i} className={`terminal-line ${h.type}`}>
            {h.type === 'input' && <span className="prompt">&gt; </span>}
            <span className="line-content">{h.text}</span>
          </div>
        ))}
        {loading && (
          <div className="terminal-line loading-indicator">
            <span className="spinner">◷</span> Executing remote command...
          </div>
        )}
        <div ref={terminalEndRef} />
      </div>

      {/* Terminal Input */}
      <div className="terminal-input-bar">
        <span className="prompt">&gt;</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type command (e.g. dir, pip list)..."
          disabled={loading}
        />
        <button onClick={() => executeCommand(input)} disabled={loading || !input.trim()}>
          Run
        </button>
      </div>

      {/* Quick shortcuts */}
      <div className="terminal-quick-shortcuts">
        <h3>Quick AGI & Skill Commands</h3>
        <div className="shortcuts-grid">
          {QUICK_COMMANDS.map((qc, i) => (
            <button
              key={i}
              className="shortcut-btn"
              onClick={() => executeCommand(qc.cmd)}
              disabled={loading}
            >
              <span className="btn-icon">{qc.icon}</span>
              <span className="btn-label">{qc.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
