import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import "./NeuralMesh.css";

const API = "http://localhost:8000";

/**
 * NeuralMesh - The living brain visualization
 * Shows LOVE's real-time neural activity: events flowing, connections forming,
 * learning happening, research completing — all animated.
 */

function EventPulse({ event }) {
  const domainColors = {
    learning: "#a78bfa",
    research: "#60a5fa",
    self_evolution: "#34d399",
    emotion: "#f472b6",
    device: "#fbbf24",
    user: "#818cf8",
    teaching: "#fb923c",
    prediction: "#2dd4bf",
    health: "#f87171",
  };
  const color = domainColors[event.domain] || "#94a3b8";

  return (
    <div className="neural-event-pulse" style={{ borderLeftColor: color }}>
      <div className="neural-event-header">
        <span className="neural-event-domain" style={{ color }}>{event.domain}</span>
        <span className="neural-event-type">{event.event_type}</span>
        <span className="neural-event-time">
          {new Date(event.iso_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
      {event.payload && (
        <div className="neural-event-payload">
          {Object.entries(event.payload).slice(0, 2).map(([k, v]) => (
            <span key={k} className="neural-event-kv">
              <span className="neural-kv-key">{k}:</span> {typeof v === 'string' ? v.slice(0, 60) : JSON.stringify(v).slice(0, 60)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function ResearchCard({ research }) {
  return (
    <div className="neural-research-card">
      <div className="neural-research-header">
        <span className="neural-research-icon">&#9673;</span>
        <span className="neural-research-topic">{research.topic}</span>
        <span className={`neural-research-status status-${research.status}`}>{research.status}</span>
      </div>
      {research.synthesis && (
        <p className="neural-research-synthesis">{research.synthesis.slice(0, 150)}...</p>
      )}
      {research.confidence > 0 && (
        <div className="neural-research-confidence">
          <div className="confidence-bar" style={{ width: `${research.confidence * 100}%` }} />
          <span>{Math.round(research.confidence * 100)}% confident</span>
        </div>
      )}
    </div>
  );
}

function GrowthJournal({ entries }) {
  if (!entries || entries.length === 0) return null;

  return (
    <div className="neural-growth-journal">
      <h4>Growth Journal</h4>
      {entries.slice(0, 5).map((entry, i) => (
        <div key={i} className="neural-growth-entry">
          <span className="growth-category">{entry.category}</span>
          <span className="growth-what">{entry.what_changed}</span>
          <span className="growth-why">{entry.why}</span>
        </div>
      ))}
    </div>
  );
}

function EcosystemMap({ devices }) {
  if (!devices || devices.length === 0) return null;

  return (
    <div className="neural-ecosystem-map">
      <h4>Ecosystem</h4>
      <div className="ecosystem-devices">
        {devices.map((dev) => (
          <div key={dev.id} className={`ecosystem-device ${dev.online ? "online" : "offline"} ${dev.user_present ? "active" : ""}`}>
            <div className="device-indicator" />
            <span className="device-name">{dev.name}</span>
            <span className="device-role">{dev.role}</span>
            {dev.battery != null && (
              <span className={`device-battery ${dev.battery < 20 ? "low" : ""}`}>
                {Math.round(dev.battery)}%
              </span>
            )}
            {dev.activity && dev.activity !== "idle" && (
              <span className="device-activity">{dev.activity}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function TeachingQueue({ lessons }) {
  if (!lessons || lessons.length === 0) return null;

  return (
    <div className="neural-teaching">
      <h4>Ready to Share</h4>
      {lessons.slice(0, 3).map((lesson, i) => (
        <div key={i} className="neural-teaching-item">
          <span className="teaching-type">{lesson.type}</span>
          <span className="teaching-title">{lesson.title}</span>
        </div>
      ))}
    </div>
  );
}

function LearningRules({ rules }) {
  if (!rules || rules.length === 0) return null;

  return (
    <div className="neural-rules">
      <h4>Learned Behaviors</h4>
      {rules.slice(0, 5).map((rule, i) => (
        <div key={i} className="neural-rule-item">
          <span className="rule-condition">When {rule.condition}</span>
          <span className="rule-action">{rule.action}</span>
        </div>
      ))}
    </div>
  );
}

export default function NeuralMesh() {
  const [events, setEvents] = useState([]);
  const [research, setResearch] = useState({ queue_size: 0, knowledge_entries: 0 });
  const [growth, setGrowth] = useState({ journal_entries: [], total_modifications: 0 });
  const [ecosystem, setEcosystem] = useState({ devices: [], online_count: 0 });
  const [teaching, setTeaching] = useState({ queued: 0, total_lessons: 0 });
  const [patterns, setPatterns] = useState([]);
  const [busStats, setBusStats] = useState({});
  const [activeTab, setActiveTab] = useState("intelligence");
  // Wave 17 state
  const [intelligence, setIntelligence] = useState(null);
  const [evolution, setEvolution] = useState(null);
  const [metacognition, setMetacognition] = useState(null);
  const [constitution, setConstitution] = useState(null);
  const [memory, setMemory] = useState(null);
  // Live Feed + Goals state
  const [liveFeed, setLiveFeed] = useState([]);
  const [toastNotification, setToastNotification] = useState({ message: '', visible: false, priority: 'normal' });
  const [goals, setGoals] = useState([]);
  const wsRef = useRef(null);
  const feedEndRef = useRef(null);

  const fetchAll = async () => {
    try {
      const [eventsRes, researchRes, growthRes, ecoRes, teachRes, patternsRes, statsRes,
             intelRes, evoRes, metaRes, constRes, memRes] = await Promise.allSettled([
        axios.get(`${API}/neural/events?limit=20`),
        axios.get(`${API}/neural/research/status`),
        axios.get(`${API}/neural/growth?days=7`),
        axios.get(`${API}/neural/ecosystem`),
        axios.get(`${API}/neural/teaching/status`),
        axios.get(`${API}/neural/patterns`),
        axios.get(`${API}/neural/bus/stats`),
        // Wave 17
        axios.get(`${API}/neural/intelligence`),
        axios.get(`${API}/neural/evolution`),
        axios.get(`${API}/neural/metacognition`),
        axios.get(`${API}/neural/constitution`),
        axios.get(`${API}/neural/memory`),
      ]);

      if (eventsRes.status === "fulfilled") setEvents(eventsRes.value.data.events || []);
      if (researchRes.status === "fulfilled") setResearch(researchRes.value.data);
      if (growthRes.status === "fulfilled") setGrowth(growthRes.value.data);
      if (ecoRes.status === "fulfilled") setEcosystem(ecoRes.value.data);
      if (teachRes.status === "fulfilled") setTeaching(teachRes.value.data);
      if (patternsRes.status === "fulfilled") setPatterns(patternsRes.value.data.patterns || []);
      if (statsRes.status === "fulfilled") setBusStats(statsRes.value.data);
      // Wave 17
      if (intelRes.status === "fulfilled") setIntelligence(intelRes.value.data);
      if (evoRes.status === "fulfilled") setEvolution(evoRes.value.data);
      if (metaRes.status === "fulfilled") setMetacognition(metaRes.value.data);
      if (constRes.status === "fulfilled") setConstitution(constRes.value.data);
      if (memRes.status === "fulfilled") setMemory(memRes.value.data);
    } catch (e) {
      console.error("NeuralMesh fetch error:", e);
    }
  };

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 5000); // Refresh every 5s - it's a living system
    return () => clearInterval(id);
  }, []);

  // WebSocket for proactive pushes
  useEffect(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//localhost:8000/agi/companion/ws`;
    let ws = null;
    let reconnectTimer = null;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('[NeuralMesh] WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'proactive_push') {
              // Add to live feed
              setLiveFeed(prev => [{
                id: Date.now(),
                category: data.category || 'THOUGHT',
                message: data.message || data.content || '',
                priority: data.priority || 'normal',
                timestamp: new Date().toISOString()
              }, ...prev].slice(0, 50));

              // Show toast notification
              setToastNotification({
                message: `[${data.category || 'LOVE'}] ${data.message || data.content || ''}`,
                priority: data.priority || 'normal',
                visible: true
              });
              setTimeout(() => setToastNotification(n => ({...n, visible: false})), 5000);
            }
          } catch (e) {
            // Non-JSON message (like "pong"), ignore
          }
        };

        ws.onclose = () => {
          console.log('[NeuralMesh] WebSocket disconnected, reconnecting...');
          reconnectTimer = setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (e) {
        reconnectTimer = setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  // Fetch goals
  useEffect(() => {
    const fetchGoals = async () => {
      try {
        const res = await axios.get(`${API}/agi/goals/tree`);
        if (res.data && !res.data.error) {
          // Parse goal tree into flat list with progress
          const goalList = [];
          const parseTree = (node, depth = 0) => {
            if (!node) return;
            if (node.title) {
              goalList.push({
                id: node.id || node.title,
                title: node.title,
                description: node.description || '',
                priority: node.priority || 0.5,
                progress: node.progress || 0,
                status: node.status || 'active',
                depth
              });
            }
            if (node.children) {
              node.children.forEach(c => parseTree(c, depth + 1));
            }
            if (node.goals) {
              node.goals.forEach(g => parseTree(g, depth));
            }
          };
          parseTree(res.data);
          if (goalList.length === 0 && Array.isArray(res.data)) {
            res.data.forEach(g => parseTree(g, 0));
          }
          setGoals(goalList);
        }
      } catch (e) {
        console.error("[NeuralMesh] goals fetch failed:", e);
      }
    };
    fetchGoals();
    const id = setInterval(fetchGoals, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="neural-mesh">
      <div className="neural-header">
        <div className="neural-title">
          <span className="neural-pulse-dot" />
          <h2>Neural Mesh</h2>
          <span className="neural-subtitle">
            {intelligence ? `${intelligence.systems_online}/${intelligence.systems_total} systems | ${intelligence.overall_health}` : "Living Brain Activity"}
          </span>
        </div>
        <div className="neural-stats-bar">
          <span className="neural-stat">
            <span className="stat-num">{busStats.events_published || 0}</span>
            <span className="stat-label">events</span>
          </span>
          <span className="neural-stat">
            <span className="stat-num">{evolution?.generation || 0}</span>
            <span className="stat-label">gen</span>
          </span>
          <span className="neural-stat">
            <span className="stat-num">{constitution?.stats?.total_principles || 0}</span>
            <span className="stat-label">principles</span>
          </span>
          <span className="neural-stat">
            <span className="stat-num">{memory?.total || 0}</span>
            <span className="stat-label">memories</span>
          </span>
          <span className="neural-stat">
            <span className="stat-num">{ecosystem.online_count || 0}</span>
            <span className="stat-label">devices</span>
          </span>
        </div>
      </div>

      <nav className="neural-tabs">
        {[
          { id: "intelligence", label: "Intelligence" },
          { id: "live", label: "Live" },
          { id: "goals", label: "Goals" },
          { id: "evolution", label: "Evolution" },
          { id: "memory", label: "Memory" },
          { id: "constitution", label: "Constitution" },
          { id: "activity", label: "Activity" },
          { id: "research", label: "Research" },
          { id: "ecosystem", label: "Ecosystem" },
        ].map(tab => (
          <button
            key={tab.id}
            className={`neural-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <div className="neural-content">
        {/* === WAVE 17: Intelligence Dashboard === */}
        {activeTab === "intelligence" && (
          <div className="neural-intelligence">
            {intelligence ? (
              <>
                <div className="intel-health-bar">
                  <span className={`intel-health-badge ${intelligence.overall_health}`}>
                    {intelligence.overall_health?.toUpperCase()}
                  </span>
                  <span className="intel-systems">
                    {intelligence.systems_online}/{intelligence.systems_total} systems online
                  </span>
                </div>
                <div className="intel-grid">
                  {/* Wave 16 Systems */}
                  {Object.entries(intelligence.wave16 || {}).map(([key, val]) => (
                    <div key={key} className={`intel-card ${val ? 'online' : 'offline'}`}>
                      <span className="intel-card-dot" />
                      <span className="intel-card-name">{key.replace('_', ' ')}</span>
                      <span className="intel-card-wave">W16</span>
                    </div>
                  ))}
                  {/* Wave 17 Systems */}
                  {Object.entries(intelligence.wave17 || {}).map(([key, val]) => (
                    <div key={key} className={`intel-card w17 ${val ? 'online' : 'offline'}`}>
                      <span className="intel-card-dot" />
                      <span className="intel-card-name">{key.replace('_', ' ')}</span>
                      <span className="intel-card-wave">W17</span>
                    </div>
                  ))}
                </div>
                {/* Metacognitive summary */}
                {metacognition && (
                  <div className="intel-metacog">
                    <h4>Self-Awareness</h4>
                    {metacognition.load && <span className="metacog-load">Cognitive Load: {metacognition.load.level}</span>}
                    {metacognition.weakness && <span className="metacog-item weakness">Improving: {metacognition.weakness}</span>}
                    {metacognition.strength && <span className="metacog-item strength">Strong at: {metacognition.strength}</span>}
                  </div>
                )}
              </>
            ) : (
              <p className="neural-empty">Intelligence dashboard loading...</p>
            )}
          </div>
        )}

        {/* === LIVE FEED — Real-time proactive pushes === */}
        {activeTab === "live" && (
          <div className="neural-live-feed">
            <div className="live-feed-header">
              <h4>Live Stream</h4>
              <span className="live-feed-count">{liveFeed.length} messages</span>
              {liveFeed.length > 0 && (
                <button className="live-feed-clear" onClick={() => setLiveFeed([])}>Clear</button>
              )}
            </div>
            <div className="live-feed-container">
              {liveFeed.length === 0 ? (
                <div className="neural-empty">
                  <p>Waiting for proactive pushes...</p>
                  <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                    LOVE will push thoughts, alerts, insights, and nudges here in real-time via WebSocket.
                  </span>
                </div>
              ) : (
                liveFeed.map(item => (
                  <div key={item.id} className={`live-feed-item ${item.category}`}>
                    <div className="feed-category">{item.category}</div>
                    <div className="feed-message">{item.message}</div>
                    <div className="feed-time">
                      {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </div>
                  </div>
                ))
              )}
              <div ref={feedEndRef} />
            </div>
          </div>
        )}

        {/* === GOALS — Active life goals with progress === */}
        {activeTab === "goals" && (
          <div className="neural-goals">
            <div className="goals-header-bar">
              <h4>Active Goals</h4>
              <span className="goals-count">{goals.length} goals tracked</span>
            </div>
            <div className="goals-list">
              {goals.length === 0 ? (
                <div className="neural-empty">
                  <p>No goals set yet.</p>
                  <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>
                    Set goals via chat: "LOVE, my goal is to..." or use the /agi/goals/set API.
                  </span>
                </div>
              ) : (
                goals.map(goal => (
                  <div key={goal.id} className="goal-item">
                    <div className="goal-header">
                      <span className="goal-title">{goal.title}</span>
                      <span className={`goal-priority ${goal.priority >= 0.8 ? 'critical' : goal.priority >= 0.6 ? 'high' : goal.priority >= 0.4 ? 'medium' : 'low'}`}>
                        {goal.priority >= 0.8 ? 'Critical' : goal.priority >= 0.6 ? 'High' : goal.priority >= 0.4 ? 'Medium' : 'Low'}
                      </span>
                    </div>
                    {goal.description && (
                      <div className="goal-description">{goal.description}</div>
                    )}
                    <div className="goal-progress-bar">
                      <div className="goal-progress-fill" style={{ width: `${Math.round(goal.progress * 100)}%` }} />
                    </div>
                    <div className="goal-meta">
                      {Math.round(goal.progress * 100)}% complete
                      {goal.status && goal.status !== 'active' && ` · ${goal.status}`}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* === WAVE 17: Evolution === */}
        {activeTab === "evolution" && (
          <div className="neural-evolution">
            {evolution ? (
              <>
                <div className="evo-header">
                  <span className="evo-gen">Generation {evolution.generation || 0}</span>
                  <span className={`evo-status ${evolution.status?.evolving ? 'active' : ''}`}>
                    {evolution.status?.evolving ? 'Evolving' : 'Stable'}
                  </span>
                </div>
                {evolution.genome && Object.keys(evolution.genome).length > 0 && (
                  <div className="evo-genome">
                    <h4>Active Genome</h4>
                    {Object.entries(evolution.genome).map(([key, val]) => val && (
                      <div key={key} className="evo-gene">
                        <span className="gene-point">{key}</span>
                        <span className="gene-value">{typeof val === 'string' ? val.slice(0, 100) : JSON.stringify(val).slice(0, 100)}</span>
                      </div>
                    ))}
                  </div>
                )}
                {evolution.active_mutations && evolution.active_mutations.length > 0 && (
                  <div className="evo-mutations">
                    <h4>Active Mutations</h4>
                    {evolution.active_mutations.map((m, i) => (
                      <div key={i} className="evo-mutation">
                        <span className="mutation-type">{m.type || m.mutation_type || 'unknown'}</span>
                        <span className="mutation-desc">{m.description || m.params?.description || ''}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="neural-empty">Evolution engine loading...</p>
            )}
          </div>
        )}

        {/* === WAVE 17: Memory === */}
        {activeTab === "memory" && (
          <div className="neural-memory">
            {memory ? (
              <>
                <div className="mem-stats">
                  <span className="mem-stat"><span className="stat-num">{memory.total || 0}</span> memories</span>
                  <span className="mem-stat">Health: {typeof memory.consolidation_health === 'number' ? `${Math.round(memory.consolidation_health * 100)}%` : 'N/A'}</span>
                </div>
                {memory.per_tier && (
                  <div className="mem-tiers">
                    <h4>Memory Tiers</h4>
                    {typeof memory.per_tier === 'object' && Object.entries(memory.per_tier).map(([tier, count]) => (
                      <div key={tier} className="mem-tier">
                        <span className="tier-name">{tier}</span>
                        <div className="tier-bar">
                          <div className="tier-fill" style={{ width: `${Math.min(100, (count / Math.max(1, memory.total)) * 100)}%` }} />
                        </div>
                        <span className="tier-count">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <p className="neural-empty">Memory architect loading...</p>
            )}
          </div>
        )}

        {/* === WAVE 17: Constitution === */}
        {activeTab === "constitution" && (
          <div className="neural-constitution">
            {constitution ? (
              <>
                <div className="const-stats">
                  <span>{constitution.stats?.total_principles || 0} principles</span>
                  <span>Drift: {constitution.stats?.last_drift_score?.toFixed(2) || '0.00'}</span>
                  <span>Violations: {constitution.stats?.total_violations || 0}</span>
                </div>
                {constitution.stats?.categories && (
                  <div className="const-categories">
                    <h4>Principle Categories</h4>
                    {Object.entries(constitution.stats.categories).map(([cat, count]) => (
                      <div key={cat} className="const-category">
                        <span className="const-cat-name">{cat}</span>
                        <span className="const-cat-count">{count}</span>
                      </div>
                    ))}
                  </div>
                )}
                {constitution.character && (
                  <div className="const-character">
                    <h4>Character</h4>
                    <p>{constitution.character.slice(0, 300)}</p>
                  </div>
                )}
              </>
            ) : (
              <p className="neural-empty">Constitution loading...</p>
            )}
          </div>
        )}

        {/* Wave 16 tabs */}
        {activeTab === "activity" && (
          <div className="neural-activity">
            <div className="neural-events-stream">
              {events.length === 0 ? (
                <p className="neural-empty">Neural bus is quiet. LOVE is resting.</p>
              ) : (
                events.map((evt, i) => <EventPulse key={i} event={evt} />)
              )}
            </div>
            {patterns.length > 0 && (
              <div className="neural-patterns">
                <h4>Detected Patterns</h4>
                {patterns.map((p, i) => (
                  <div key={i} className="neural-pattern">
                    <span className="pattern-seq">{p.sequence}</span>
                    <span className="pattern-count">{p.count}x</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "research" && (
          <div className="neural-research">
            <div className="research-stats">
              <span>Queue: {research.queue_size || 0}</span>
              <span>In Progress: {research.in_progress || 0}</span>
              <span>Knowledge: {research.knowledge_entries || 0}</span>
              <span>Monitored: {research.monitored_topics || 0}</span>
            </div>
            {research.recent_completions && research.recent_completions.map((r, i) => (
              <ResearchCard key={i} research={r} />
            ))}
          </div>
        )}

        {activeTab === "ecosystem" && (
          <div className="neural-eco">
            <EcosystemMap devices={ecosystem.devices} />
            {ecosystem.user_presence && (
              <div className="eco-presence">
                <h4>User Presence</h4>
                <span className={`presence-status ${ecosystem.user_presence.present ? "present" : "away"}`}>
                  {ecosystem.user_presence.present ? `Active on ${ecosystem.user_presence.active_device_name}` : "Away"}
                </span>
                {ecosystem.user_presence.likely_activity && (
                  <span className="presence-activity">{ecosystem.user_presence.likely_activity}</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast Notification for Proactive Pushes */}
      <div className={`love-toast ${toastNotification.visible ? 'visible' : ''} ${toastNotification.priority}`}>
        <div className="love-toast-label">LOVE Push</div>
        <div className="love-toast-message">{toastNotification.message}</div>
      </div>
    </div>
  );
}
