/* ─── LOVE Companion App · Wave 13+14 ─────────────────────────────
   Premium PWA JS: WebSocket, Cross-Device Sync, /recall, /vision,
   /swarm commands, infinite memory feed, device roster.
   ─────────────────────────────────────────────────────────────── */

const API_BASE = window.location.origin;
const WS_PROTO = location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL   = `${WS_PROTO}//${location.host}/agi/companion/ws`;

/* ── Device Identity (Mind Sync) ───────────────────────────────── */
const DEVICE_ID = (() => {
  let id = localStorage.getItem('love_device_id');
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('love_device_id', id); }
  return id;
})();
const DEVICE_NAME = (() => {
  const ua = navigator.userAgent;
  if (/iPhone/.test(ua)) return 'iPhone';
  if (/iPad/.test(ua)) return 'iPad';
  if (/Android.*Mobile/.test(ua)) return 'Android Phone';
  if (/Android/.test(ua)) return 'Android Tablet';
  return 'Desktop Browser';
})();
const DEVICE_TYPE = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) ? 'mobile' : 'desktop';

async function registerDevice() {
  try {
    await fetch(`${API_BASE}/agi/sync/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: DEVICE_ID, device_name: DEVICE_NAME, device_type: DEVICE_TYPE })
    });
  } catch { /* non-blocking */ }
}

// Heartbeat every 30s to stay marked online
registerDevice();
setInterval(() => {
  fetch(`${API_BASE}/agi/sync/heartbeat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ device_id: DEVICE_ID })
  }).catch(() => {});
}, 30000);

const $  = id => document.getElementById(id);
const wsStatus      = $('ws-status');
const monologueFeed = $('monologue-feed');
const chatFeed      = $('chat-feed');
const chatInput     = $('chat-input');
const btnSend       = $('btn-send');
const btnVoice      = $('btn-voice');
const contextList   = $('context-list');
const deviceList    = $('device-list');
const memoryFeed    = $('memory-feed');
const deviceCount   = $('device-count');
const memoryCount   = $('memory-count');

/* ── Monitoring & Learning ───────────────────────────────────────── */
const monitorCognitive = $('monitor-cognitive');
const monitorConfidence = $('monitor-confidence');
const monitorHealth = $('monitor-health');
const monitorErrors = $('monitor-errors');
const monitorAlerts = $('monitor-alerts');
const learnExperiences = $('learn-experiences');
const learnPatterns = $('learn-patterns');
const learnAdaptations = $('learn-adaptations');
const learningFeed = $('learning-feed');

/* ── Consciousness Stats ───────────────────────────────────────── */
const valMaturity    = $('val-maturity');
const valEmotion     = $('val-emotion');
const valConvos      = $('val-convos');
const valAge         = $('val-age');
const valBoots       = $('val-boots');
const valPlasticity  = $('val-plasticity');
const plasticityBar  = $('plasticity-bar');

/* ── WebSocket ─────────────────────────────────────────────────── */
let ws, reconnectTimer;

function wsConnect() {
  clearTimeout(reconnectTimer);
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    wsStatus.textContent = 'CONNECTED';
    wsStatus.className = 'value connected';
    console.log('[WS] Connected');
    fetchInitialState();
  };

  ws.onclose = () => {
    wsStatus.textContent = 'RECONNECTING';
    wsStatus.className = 'value disconnected';
    reconnectTimer = setTimeout(wsConnect, 3000);
  };

  ws.onerror = e => console.warn('[WS] Error', e);

  ws.onmessage = ({ data }) => {
    try { handleEvent(JSON.parse(data)); }
    catch (e) { console.error('[WS] Parse error', e); }
  };
}

function wsSend(payload) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(payload));
}

/* ── Event Router ──────────────────────────────────────────────── */
function handleEvent(data) {
  // Show activity indicator on monologue events
  if (data.type === 'monologue' || data.type === 'proactive_nudge') {
    showActivity('LOVE is active');
  }
  
  switch (data.type) {
    case 'state_sync':      handleStateSync(data);      break;
    case 'monologue':       handleMonologue(data);       break;
    case 'chat_response':   addMsg(data.message, 'love'); break;
    case 'memory_flash':    handleMemoryFlash(data);    break;
    case 'device_update':   handleDeviceUpdate(data);   break;
    case 'agent_status':    handleAgentStatus(data);    break;
    case 'monitoring_update': handleMonitoringUpdate(data); break;
    case 'learning_update': handleLearningUpdate(data); break;
  }
}

/* ── State Sync ────────────────────────────────────────────────── */
function handleStateSync(data) {
  if (data.consciousness) {
    const c = data.consciousness;
    const id = c.identity || {};
    const em = c.emotional_state || {};
    valMaturity.textContent  = (id.maturity_level || '—').toUpperCase();
    valEmotion.textContent   = (em.primary_emotion || '—').toUpperCase();
    valConvos.textContent    = id.total_conversations ?? '—';
    valAge.textContent       = id.current_age_days != null ? `${id.current_age_days}d` : '—';
    valBoots.textContent     = id.total_boots ?? '—';
    const plasticity = Math.min(100, (id.total_conversations || 0) * 2);
    valPlasticity.textContent = `${plasticity}%`;
    plasticityBar.style.width = `${plasticity}%`;
  }
  if (data.context) {
    const ctx = data.context;
    contextList.innerHTML = '';
    if (ctx.activity)       addCtx(`Activity: ${ctx.activity}`);
    if (ctx.active_window)  addCtx(`Focus: ${ctx.active_window}`);
    if (ctx.active_app)     addCtx(`App: ${ctx.active_app}`);
    if (ctx.time_of_day)    addCtx(`Time: ${ctx.time_of_day}`);
    if (ctx.battery != null) addCtx(`Battery: ${ctx.battery}%`);
    if (ctx.summary)        addCtx(`${ctx.summary}`);
  }
  if (data.devices) handleDeviceRoster(data.devices);
}

function addCtx(text) {
  const li = document.createElement('li');
  li.textContent = text;
  contextList.appendChild(li);
}

/* ── Monologue Feed ────────────────────────────────────────────── */
function handleMonologue(data) {
  const entry = document.createElement('div');
  entry.className = 'thought-entry';
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  entry.innerHTML = `<span class="timestamp">[${ts}]</span><span>${escapeHtml(data.thought)}</span>`;
  monologueFeed.appendChild(entry);
  monologueFeed.scrollTop = monologueFeed.scrollHeight;
  // Also pulse the visualizer
  pulseVisualizer();
  // Store a memory flash on right panel
  pushMemoryFlash(data.thought);
}

/* ── Memory Flash (right panel) ────────────────────────────────── */
function handleMemoryFlash(data) {
  pushMemoryFlash(data.content, data.tags);
}

function pushMemoryFlash(text, tags) {
  if (!text || text.length < 10) return;
  // Limit to 5 items
  const items = memoryFeed.querySelectorAll('.memory-flash');
  if (items.length >= 5) items[0].remove();

  const div = document.createElement('div');
  div.className = 'memory-flash';
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
  div.innerHTML = `<div>${escapeHtml(text.slice(0, 120))}${text.length > 120 ? '…' : ''}</div><div class="mf-ts">${ts}</div>`;
  memoryFeed.insertBefore(div, memoryFeed.firstChild);
}

/* ── Device Roster (Wave 14) ───────────────────────────────────── */
function handleDeviceRoster(devices) {
  deviceList.innerHTML = '';
  devices.forEach(d => {
    const div = document.createElement('div');
    div.className = 'device-item';
    div.innerHTML = `
      <div class="device-dot ${d.online ? 'online' : 'offline'}"></div>
      <div class="device-name">${escapeHtml(d.name || d.device_id)}</div>
      <div class="device-type badge badge-cyan">${(d.type || 'DEVICE').toUpperCase()}</div>
    `;
    deviceList.appendChild(div);
  });
  deviceCount.textContent = devices.filter(d => d.online).length;
}

function handleDeviceUpdate(data) {
  if (data.devices) handleDeviceRoster(data.devices);
}

/* ── Agent Status ──────────────────────────────────────────────── */
const AGENT_MAP = {
  'jarvis':  'agent-jarvis',
  'ghost':   'agent-ghost',
  'browser': 'agent-browser',
  'vision':  'agent-vision',
  'os':      'agent-os',
};
function handleAgentStatus(data) {
  const el = $(AGENT_MAP[data.agent]);
  if (!el) return;
  const badge = el.querySelector('.agent-state');
  if (!badge) return;
  badge.className = `agent-state ${data.status}`;
  badge.textContent = data.status.toUpperCase();
}

/* ── Monitoring Update ──────────────────────────────────────────── */
function handleMonitoringUpdate(data) {
  if (data.cognitive_load != null) {
    const load = typeof data.cognitive_load === 'object' ? data.cognitive_load.level : data.cognitive_load;
    monitorCognitive.textContent = load ?? '—';
    const score = typeof data.cognitive_load === 'object' ? data.cognitive_load.score : null;
    if (score != null) {
      monitorConfidence.textContent = `${(score * 100).toFixed(0)}%`;
    }
  }
  if (data.system_health != null) {
    monitorHealth.textContent = data.system_health;
  }
  // Map anomalies to alerts if present
  const alerts = data.alerts || (data.anomalies ? data.anomalies.map(a => ({
    severity: a.severity >= 0.7 ? 'error' : a.severity >= 0.5 ? 'warning' : 'info',
    message: a.description || a.type || 'Anomaly detected'
  })) : []);
  if (alerts.length > 0) {
    monitorAlerts.innerHTML = '';
    alerts.forEach(alert => {
      const div = document.createElement('div');
      div.className = `alert-item ${alert.severity || 'info'}`;
      div.textContent = alert.message;
      monitorAlerts.appendChild(div);
    });
  }
}

/* ── Learning Update ────────────────────────────────────────────── */
function handleLearningUpdate(data) {
  if (data.experiences != null) {
    learnExperiences.textContent = data.experiences;
  }
  if (data.patterns != null) {
    learnPatterns.textContent = data.patterns;
  }
  if (data.adaptations != null) {
    learnAdaptations.textContent = data.adaptations;
  }
  if (data.recent_learning) {
    const div = document.createElement('div');
    div.className = 'learning-flash';
    const ts = new Date().toLocaleTimeString('en-GB', { hour12: false });
    div.innerHTML = `<div>${escapeHtml(data.recent_learning.slice(0, 100))}${data.recent_learning.length > 100 ? '…' : ''}</div><div class="mf-ts">${ts}</div>`;
    learningFeed.insertBefore(div, learningFeed.firstChild);
    // Limit to 5 items
    const items = learningFeed.querySelectorAll('.learning-flash');
    if (items.length >= 5) items[items.length - 1].remove();
  }
}

/* ── Chat ──────────────────────────────────────────────────────── */
function addMsg(text, sender) {
  const div = document.createElement('div');
  div.className = `msg ${sender}`;
  const senderName = sender === 'user' ? 'YOU' : 'LOVE';
  div.innerHTML = `<div class="msg-sender">${senderName}</div>${escapeHtml(text)}`;
  chatFeed.appendChild(div);
  chatFeed.scrollTop = chatFeed.scrollHeight;
  return div;
}

function addTypingIndicator() {
  const div = addMsg('Thinking…', 'love');
  div.classList.add('typing');
  div.id = 'typing-indicator';
  return div;
}
function removeTypingIndicator() {
  const el = $('typing-indicator');
  if (el) el.remove();
}

/* ── Command Router ────────────────────────────────────────────── */
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text) return;
  addMsg(text, 'user');
  chatInput.value = '';

  const lower = text.toLowerCase();

  /* ── /swarm <task> ── */
  if (lower.startsWith('/swarm ')) {
    const task = text.substring(7).trim();
    const typing = addTypingIndicator();
    try {
      const res = await fetch(`${API_BASE}/agi/swarm/coordinate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, required_agents: [], context: '' })
      });
      const data = await res.json();
      typing.remove();
      if (data.success && data.synthesis) {
        let msg = `🤖 Coordinated Swarm Complete\n`;
        msg += `Agents: ${data.selected_agents.join(', ')}\n`;
        if (data.conflicts && data.conflicts.length > 0) {
          msg += `⚠️ ${data.conflicts.length} conflict(s) resolved\n`;
        }
        msg += `\n${data.synthesis}`;
        addMsg(msg, 'love');
      } else {
        addMsg('Swarm coordination completed but no synthesis returned.', 'love');
      }
    } catch (e) { console.error('[UI] swarm failed:', e); typing.remove(); addMsg('⚠️ Swarm link severed.', 'love'); }
    return;
  }

  /* ── /recall <query> ── */
  if (lower.startsWith('/recall ')) {
    const query = text.substring(8).trim();
    const typing = addTypingIndicator();
    try {
      const res = await fetch(`${API_BASE}/agi/memory/recall`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, type: 'episodic' })
      });
      const data = await res.json();
      typing.remove();
      if (data.results && data.results.length > 0) {
        const summary = data.results.map((r, i) => `${i + 1}. ${r.content.slice(0, 150)}…`).join('\n');
        addMsg(`🧠 Memory Recall:\n${summary}`, 'love');
      } else {
        addMsg('No memories found for that query.', 'love');
      }
    } catch { typing.remove(); addMsg('⚠️ Memory retrieval failed.', 'love'); }
    return;
  }

  /* ── /vision ── */
  if (lower === '/vision' || lower.startsWith('/vision')) {
    const typing = addTypingIndicator();
    try {
      const res = await fetch(`${API_BASE}/agi/vision/snapshot`);
      const data = await res.json();
      typing.remove();
      addMsg(`👁️ Screen Analysis:\n${data.analysis || data.description || 'Captured your screen. Analyzing context…'}`, 'love');
    } catch { typing.remove(); addMsg('⚠️ Vision cortex unavailable.', 'love'); }
    return;
  }

  /* ── /devices ── */
  if (lower === '/devices') {
    try {
      const res = await fetch(`${API_BASE}/agi/sync/devices`);
      const data = await res.json();
      const list = (data.devices || []).map(d => `• ${d.name || d.device_id} (${d.type}) — ${d.online ? '🟢 Online' : '⚫ Offline'}`).join('\n');
      addMsg(`📱 Connected Devices:\n${list || 'No devices registered.'}`, 'love');
    } catch { addMsg('⚠️ Device sync unavailable.', 'love'); }
    return;
  }

  /* ── /help ── */
  if (lower === '/help') {
    addMsg(
`🤖 LOVE Command Reference:
/swarm <task>   — Coordinated multi-agent swarm (dynamic selection, parallel execution)
/recall <query> — Search infinite memory
/vision         — Capture + analyse screen
/devices        — List connected devices
/help           — Show this guide

Or just talk naturally — LOVE understands context.`, 'love');
    return;
  }

  /* ── Default: Natural Language Chat ── */
  const typing = addTypingIndicator();
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, mode: 'general' })
    });
    const data = await res.json();
    typing.remove();
    addMsg(data.response || '…', 'love');
  } catch { typing.remove(); addMsg('⚠️ Link severed.', 'love'); }
}

function quickCmd(text) {
  chatInput.value = text;
  sendMessage();
}

/* ── Visualizer Pulse ──────────────────────────────────────────── */
function pulseVisualizer() {
  const bars = document.querySelectorAll('.bar');
  bars.forEach(b => {
    const h = 20 + Math.random() * 80;
    b.style.height = `${h}%`;
    setTimeout(() => { b.style.height = ''; }, 500);
  });
}

/* ── Initial State Fetch ───────────────────────────────────────── */
async function fetchInitialState() {
  try {
    const res = await fetch(`${API_BASE}/agi/consciousness`);
    const data = await res.json();
    if (!data.error) handleStateSync({ consciousness: data });
  } catch (e) { console.error('[UI] consciousness fetch failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/context/summary`);
    const data = await res.json();
    if (!data.error) handleStateSync({ context: data });
  } catch (e) { console.error('[UI] context summary fetch failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/agi/sync/devices`);
    const data = await res.json();
    if (data.devices) handleDeviceRoster(data.devices);
  } catch (e) { console.error('[UI] devices fetch failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/agi/memory/count`);
    const data = await res.json();
    if (data.count != null) memoryCount.textContent = data.count.toLocaleString();
  } catch (e) { console.error('[UI] memory count fetch failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/neural/monitoring/status`);
    const data = await res.json();
    if (!data.error) handleMonitoringUpdate(data);
  } catch (e) { console.error('[UI] monitoring fetch failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/neural/learning/status`);
    const data = await res.json();
    if (!data.error) handleLearningUpdate(data);
  } catch (e) { console.error('[UI] learning fetch failed:', e); }
}

/* ── Voice Input (Web Speech API) ─────────────────────────────── */
let recognition;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SR();
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = e => {
    chatInput.value = e.results[0][0].transcript;
    btnVoice.classList.remove('recording');
    sendMessage();
  };
  recognition.onerror = () => btnVoice.classList.remove('recording');
  recognition.onend   = () => btnVoice.classList.remove('recording');
}

btnVoice.addEventListener('click', () => {
  if (!recognition) { addMsg('Voice not supported in this browser.', 'love'); return; }
  if (btnVoice.classList.contains('recording')) {
    recognition.stop();
    btnVoice.classList.remove('recording');
  } else {
    recognition.start();
    btnVoice.classList.add('recording');
  }
});

/* ── Event Listeners ───────────────────────────────────────────── */
btnSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

/* ── Helpers ───────────────────────────────────────────────────── */
function escapeHtml(str = '') {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Boot ──────────────────────────────────────────────────────── */
wsConnect();

// Periodic polling for monitoring and learning updates (every 30 seconds)
setInterval(async () => {
  try {
    const res = await fetch(`${API_BASE}/context/summary`);
    const data = await res.json();
    if (!data.error) handleStateSync({ context: data });
  } catch (e) { console.error('[UI] context poll failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/neural/monitoring/status`);
    const data = await res.json();
    if (!data.error) handleMonitoringUpdate(data);
  } catch (e) { console.error('[UI] monitoring poll failed:', e); }

  try {
    const res = await fetch(`${API_BASE}/neural/learning/status`);
    const data = await res.json();
    if (!data.error) handleLearningUpdate(data);
  } catch (e) { console.error('[UI] learning poll failed:', e); }
}, 30000);

/* ── Coordinated Swarm Panel ───────────────────────────────────── */
const swarmInput = $('swarm-input');
const swarmLaunchBtn = $('swarm-launch');
const swarmStatus = $('swarm-status');
const swarmActiveAgents = $('swarm-active-agents');
const swarmSynthesis = $('swarm-synthesis');
const swarmConflicts = $('swarm-conflicts');

async function launchCoordinatedSwarm() {
  const task = swarmInput.value.trim();
  if (!task) return;

  swarmLaunchBtn.disabled = true;
  swarmStatus.textContent = 'COORDINATOR: Analyzing task & selecting agents…';
  swarmActiveAgents.innerHTML = '';
  swarmSynthesis.classList.remove('visible');
  swarmSynthesis.textContent = '';
  swarmConflicts.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/agi/swarm/coordinate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, required_agents: [], context: '' })
    });
    const data = await res.json();
    if (!data.success) {
      swarmStatus.textContent = `ERROR: ${data.error || 'Unknown error'}`;
      swarmLaunchBtn.disabled = false;
      return;
    }

    swarmStatus.textContent = `COORDINATOR: Selected ${data.selected_agents.join(', ')} — ${data.coordinator_reasoning}`;

    // Render agent result cards
    const results = data.agent_results || {};
    Object.entries(results).forEach(([name, r]) => {
      const card = document.createElement('div');
      card.className = `swarm-agent-card ${r.status}`;
      card.innerHTML = `
        <div class="swarm-agent-header">
          <div>
            <span class="swarm-agent-name">${escapeHtml(r.agent_name)}</span>
            <span class="swarm-agent-role">${escapeHtml(r.agent_role)}</span>
          </div>
          <span class="swarm-agent-dur">${r.duration_sec ? r.duration_sec.toFixed(1) + 's' : ''}</span>
        </div>
        <div class="swarm-agent-output">${escapeHtml(r.output).substring(0, 300)}</div>
      `;
      swarmActiveAgents.appendChild(card);
    });

    // Show synthesis
    if (data.synthesis) {
      swarmSynthesis.textContent = data.synthesis;
      swarmSynthesis.classList.add('visible');
    }

    // Show conflicts if any
    if (data.conflicts && data.conflicts.length > 0) {
      data.conflicts.forEach(c => {
        const div = document.createElement('div');
        div.className = 'swarm-conflict-item';
        div.innerHTML = `<span class="swarm-conflict-sev">[SEV ${(c.severity * 100).toFixed(0)}%]</span> ${escapeHtml(c.topic)} — ${escapeHtml(c.summary)}`;
        swarmConflicts.appendChild(div);
      });
      swarmStatus.textContent += ` | ${data.conflicts.length} conflict(s) detected & resolved`;
    } else {
      swarmStatus.textContent += ' | No conflicts — full consensus';
    }

    // Also post to chat
    addToChat('system', `🤖 Swarm completed: ${task.substring(0, 60)}…\n\n${escapeHtml(data.synthesis).substring(0, 500)}`);

  } catch (e) {
    console.error('[UI] swarm launch failed:', e);
    swarmStatus.textContent = 'ERROR: Swarm coordination failed. Check console.';
  } finally {
    swarmLaunchBtn.disabled = false;
  }
}

if (swarmLaunchBtn && swarmInput) {
  swarmLaunchBtn.addEventListener('click', launchCoordinatedSwarm);
  swarmInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') launchCoordinatedSwarm();
  });
}

/* ── Onboarding Overlay ───────────────────────────────────────────── */
const onboardingOverlay = $('onboarding-overlay');
const skipOnboarding = $('skip-onboarding');
const nextOnboarding = $('next-onboarding');
const startUsing = $('start-using');
const activityIndicator = $('activity-indicator');
const activityText = $('activity-text');

let currentStep = 1;
const totalSteps = 3;

function showOnboarding() {
  const hasSeenOnboarding = localStorage.getItem('love_onboarding_seen');
  if (!hasSeenOnboarding && onboardingOverlay) {
    onboardingOverlay.style.display = 'flex';
  }
}

function hideOnboarding() {
  if (onboardingOverlay) {
    onboardingOverlay.style.display = 'none';
    localStorage.setItem('love_onboarding_seen', 'true');
  }
}

function updateStep(step) {
  currentStep = step;
  
  // Update step visibility
  document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
  const activeStep = document.querySelector(`.step[data-step="${step}"]`);
  if (activeStep) activeStep.classList.add('active');
  
  // Update buttons
  if (step === totalSteps) {
    nextOnboarding.style.display = 'none';
    startUsing.style.display = 'inline-block';
  } else {
    nextOnboarding.style.display = 'inline-block';
    startUsing.style.display = 'none';
  }
}

if (skipOnboarding) {
  skipOnboarding.addEventListener('click', hideOnboarding);
}

if (nextOnboarding) {
  nextOnboarding.addEventListener('click', () => {
    if (currentStep < totalSteps) {
      updateStep(currentStep + 1);
    }
  });
}

if (startUsing) {
  startUsing.addEventListener('click', hideOnboarding);
}

/* ── Activity Indicator ──────────────────────────────────────────── */
let activityTimeout;

function showActivity(message = 'LOVE is thinking...') {
  if (activityText) activityText.textContent = message;
  if (activityIndicator) {
    activityIndicator.classList.add('visible');
    clearTimeout(activityTimeout);
    activityTimeout = setTimeout(() => {
      activityIndicator.classList.remove('visible');
    }, 5000);
  }
}

function hideActivity() {
  if (activityIndicator) {
    activityIndicator.classList.remove('visible');
  }
}

// Initialize onboarding on page load
document.addEventListener('DOMContentLoaded', showOnboarding);
