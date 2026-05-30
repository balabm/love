import React, { useState, useEffect } from 'react';
import './OrchestratorPanel.css';

/**
 * OrchestratorPanel — LOVE's brain status visible to the user.
 *
 * Shows:
 * - Module health (ready / degraded / failed)
 * - System state (load, focus mode, consciousness)
 * - Recent narrative (what LOVE has been doing)
 * - Recent decisions
 * - User communication log
 */

const OrchestratorPanel = () => {
  const [status, setStatus] = useState(null);
  const [narrative, setNarrative] = useState([]);
  const [comms, setComms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [command, setCommand] = useState('');
  const [evolution, setEvolution] = useState(null);

  const API_BASE = window.location.origin;

  const fetchAll = async () => {
    try {
      setLoading(true);
      const [statusRes, narrativeRes, commsRes] = await Promise.all([
        fetch(`${API_BASE}/orchestrator/master/status`).then(r => r.json()),
        fetch(`${API_BASE}/orchestrator/master/narrative?limit=20`).then(r => r.json()),
        fetch(`${API_BASE}/orchestrator/master/comms?limit=20`).then(r => r.json()),
      ]);
      setStatus(statusRes);
      setNarrative(narrativeRes.narrative || []);
      setComms(commsRes.comms || []);
      setError(null);
      
      // Fetch evolution data
      try {
        const evoRes = await fetch(`${API_BASE}/intelligence/self-evolution`);
        if (evoRes.ok) {
          const evoData = await evoRes.json();
          setEvolution(evoData);
        }
      } catch (e) {
        // Evolution endpoint may not be available
      }
    } catch (e) {
      setError('Could not connect to orchestrator');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000);
    return () => clearInterval(interval);
  }, []);

  const sendCommand = async () => {
    if (!command.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/orchestrator/master/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: command }),
      });
      const data = await res.json();
      alert(`LOVE: ${data.response || data.error}`);
      setCommand('');
      fetchAll();
    } catch (e) {
      alert('Failed to send command');
    }
  };

  const moduleStates = status?.system_summary?.states || {};
  const total = status?.system_summary?.total_modules || 0;
  const ready = moduleStates.ready || 0;
  const degraded = moduleStates.degraded || 0;
  const failed = moduleStates.failed || 0;

  return (
    <div className="orchestrator-panel">
      <div className="panel-header">
        <h2>LOVE's Brain</h2>
        <span className={`status-badge ${status?.running ? 'alive' : 'offline'}`}>
          {status?.running ? 'ALIVE' : 'OFFLINE'}
        </span>
      </div>

      {loading && <div className="loading">Syncing with LOVE...</div>}
      {error && <div className="error">{error}</div>}

      {!loading && status && (
        <>
          {/* System Summary */}
          <div className="summary-grid">
            <div className="summary-card">
              <div className="metric">{total}</div>
              <div className="label">Modules</div>
            </div>
            <div className="summary-card ready">
              <div className="metric">{ready}</div>
              <div className="label">Ready</div>
            </div>
            <div className="summary-card degraded">
              <div className="metric">{degraded}</div>
              <div className="label">Degraded</div>
            </div>
            <div className="summary-card failed">
              <div className="metric">{failed}</div>
              <div className="label">Failed</div>
            </div>
          </div>

          {/* System State */}
          <div className="state-bar">
            <div className="state-item">
              <span className="state-label">Load:</span>
              <span className={`state-value ${status.system_summary?.system_under_load ? 'alert' : 'ok'}`}>
                {status.system_summary?.system_under_load ? 'HIGH' : 'Normal'}
              </span>
            </div>
            <div className="state-item">
              <span className="state-label">Focus:</span>
              <span className={`state-value ${status.system_summary?.focus_mode ? 'alert' : 'ok'}`}>
                {status.system_summary?.focus_mode ? 'ON' : 'Off'}
              </span>
            </div>
            <div className="state-item">
              <span className="state-label">Consciousness:</span>
              <span className="state-value">{status.system_summary?.consciousness_maturity}</span>
            </div>
            <div className="state-item">
              <span className="state-label">Age:</span>
              <span className="state-value">{status.system_summary?.consciousness_age_days} days</span>
            </div>
          </div>

          {/* Evolution Activity */}
          {evolution && (
            <div className="section evolution-section">
              <h3>Evolution Activity</h3>
              <div className="evo-metrics-grid">
                {evolution.integration && (
                  <>
                    <div className="evo-metric">
                      <span className="evo-metric-val">{evolution.integration.statistics?.total_code_modifications || 0}</span>
                      <span className="evo-metric-lbl">Code Mods</span>
                    </div>
                    <div className="evo-metric">
                      <span className="evo-metric-val">{evolution.integration.statistics?.total_mutations_applied || 0}</span>
                      <span className="evo-metric-lbl">Mutations</span>
                    </div>
                    <div className="evo-metric">
                      <span className="evo-metric-val">{evolution.integration.statistics?.successful_cross_adoptions || 0}</span>
                      <span className="evo-metric-lbl">Adoptions</span>
                    </div>
                  </>
                )}
                {evolution.capability_gaps && (
                  <div className="evo-metric">
                    <span className="evo-metric-val">{evolution.capability_gaps.total || 0}</span>
                    <span className="evo-metric-lbl">Gaps</span>
                  </div>
                )}
                {evolution.deployments && evolution.deployments.length > 0 && (
                  <div className="evo-metric">
                    <span className="evo-metric-val">{evolution.deployments.length}</span>
                    <span className="evo-metric-lbl">Deployments</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Command Input */}
          <div className="command-section">
            <input
              type="text"
              className="command-input"
              placeholder="Ask LOVE what it's doing, or say 'restart module_name'..."
              value={command}
              onChange={e => setCommand(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendCommand()}
            />
            <button className="command-btn" onClick={sendCommand}>
              Send
            </button>
          </div>

          {/* Narrative */}
          <div className="section">
            <h3>Recent Activity</h3>
            <div className="narrative-list">
              {narrative.length === 0 && <div className="empty">No activity yet.</div>}
              {narrative.slice().reverse().map((entry, i) => (
                <div key={i} className={`narrative-item ${entry.importance}`}>
                  <span className="narrative-time">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="narrative-event">{entry.event}</span>
                  <span className="narrative-detail">{entry.detail}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Communications */}
          <div className="section">
            <h3>Communications</h3>
            <div className="comms-list">
              {comms.length === 0 && <div className="empty">No recent messages.</div>}
              {comms.slice().reverse().map((msg, i) => (
                <div key={i} className={`comm-item ${msg.direction}`}>
                  <span className="comm-time">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="comm-dir">{msg.direction === 'to_user' ? 'LOVE -> You' : 'You -> LOVE'}</span>
                  <span className="comm-content">{msg.content}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default OrchestratorPanel;
