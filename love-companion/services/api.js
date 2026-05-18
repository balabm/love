import AsyncStorage from '@react-native-async-storage/async-storage';

// EXPO_PUBLIC_API_URL is injected at build time via eas.json env.
// Falls back to Tailscale IP if not set. Override in Settings tab anytime.
const DEFAULT_HOST =
  process.env.EXPO_PUBLIC_API_URL ||
  'http://100.93.81.95:8000'; // Tailscale IP — works from anywhere over 4G

export const DEVICE_ID = 'oneplus-karthi'; // Override in settings

export async function getServerUrl() {
  const saved = await AsyncStorage.getItem('love_server_url');
  return saved || DEFAULT_HOST;
}

export async function setServerUrl(url) {
  await AsyncStorage.setItem('love_server_url', url);
}

export async function getDeviceId() {
  const saved = await AsyncStorage.getItem('love_device_id');
  return saved || DEVICE_ID;
}

async function fetchWithTimeout(url, options, timeoutMs = 8000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (e) {
    clearTimeout(id);
    throw e;
  }
}

async function base(path, options = {}) {
  const url = await getServerUrl();
  const res = await fetchWithTimeout(`${url}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Chat ──
export async function sendChat(text, mode = 'general') {
  const deviceId = await getDeviceId();
  return base('/devices/chat', {
    method: 'POST',
    body: JSON.stringify({ text, device_id: deviceId, mode }),
  });
}

// ── Device heartbeat ──
export async function sendHeartbeat(info) {
  const deviceId = await getDeviceId();
  return base('/devices/heartbeat', {
    method: 'POST',
    body: JSON.stringify({ device_id: deviceId, ...info }),
  });
}

// ── Push event ──
export async function pushEvent(type, title, body, extra = {}) {
  const deviceId = await getDeviceId();
  return base('/devices/push', {
    method: 'POST',
    body: JSON.stringify({ device_id: deviceId, type, title, body, ...extra }),
  });
}

// ── Context summary ──
export async function getContext() {
  return base('/context/summary');
}

// ── LOVE insights ──
export async function getInsights() {
  return base('/insights');
}

// ── Orchestrator interventions ──
export async function getOrchestratorInterventions() {
  return base('/orchestrator/interventions');
}

// ── All devices ──
export async function getDevices() {
  return base('/devices');
}

// ── Dashboard ──
export async function getDashboard() {
  return base('/dashboard');
}

// ── Lifescore ──
export async function getLifescore() {
  return base('/lifescore');
}

// ── Voice speak ──
export async function speakOnPC(text) {
  return base('/voice/speak', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

// ── Profile sync — sends user profile to LOVE server memory ──
export async function syncProfile(profile) {
  return base('/profile/sync', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

// ── Emotional relationships ──
export async function getRelationships() {
  return base('/emotional/relationships');
}

// ── Evolution cycle trigger ──
export async function triggerEvolutionCycle() {
  return base('/evolution/trigger-cycle', {
    method: 'POST',
  });
}

// ── Evolution behavior state ──
export async function getBehaviorState() {
  return await fetchAPI('/evolution/behavior-state');
}

// ── Evolution performance metrics ──
export async function getEvolutionPerformance() {
  return await fetchAPI('/evolution/performance');
}

export async function getEmotionalState() {
  return await fetchAPI('/emotional/state');
}

export async function getCalendarInsights() {
  return await fetchAPI('/integrations/google/calendar/insights');
}

export async function getTaskSmartSuggestions(count = 3) {
  return await fetchAPI(`/tasks/smart-suggestions?count=${count}`);
}

export async function getDocPatterns() {
  return await fetchAPI('/docs/patterns');
}

// ── Push notification content to LOVE memory ──
export async function sendNotifToMemory(payload) {
  return base('/memory/ingest', {
    method: 'POST',
    body: JSON.stringify({ type: 'notification', ...payload }),
  });
}

// ── Ask LOVE about a person ──
export async function askAboutPerson(name) {
  return sendChat(`Who is ${name}? What do I know about them from our history?`, 'general');
}

// ── Get recent memories ──
export async function getMemories(limit = 10) {
  return base(`/memory/recent?limit=${limit}`);
}

// ── Vision — analyze image from device ──
export async function visionAnalyze(imagePath, question = "") {
  return base('/vision/analyze', {
    method: 'POST',
    body: JSON.stringify({ image_path: imagePath, question }),
  });
}

// ── System control — ask LOVE to do something on PC ──
export async function systemAction(action, data = {}) {
  const endpoints = {
    open: '/system/open',
    screenshot: '/system/screenshot',
    type: '/system/type',
    key: '/system/key',
    media: '/system/media',
    lock: '/system/lock',
    windows: '/system/windows',
    focus: '/system/focus',
    shell: '/system/shell',
  };
  const path = endpoints[action];
  if (!path) throw new Error(`Unknown system action: ${action}`);
  if (action === 'windows' || action === 'lock') {
    return base(path, { method: action === 'windows' ? 'GET' : 'POST' });
  }
  return base(path, { method: 'POST', body: JSON.stringify(data) });
}

// ── Voice loop ──
export async function voiceLoopStart() {
  return base('/voice/loop/start', { method: 'POST' });
}
export async function voiceLoopStop() {
  return base('/voice/loop/stop', { method: 'POST' });
}
export async function voiceLoopStatus() {
  return base('/voice/loop/status');
}

export async function uploadVoiceForTranscription(audioUri) {
  const formData = new FormData();
  formData.append('file', {
    uri: audioUri,
    type: 'audio/m4a',
    name: 'recording.m4a',
  });
  return base('/voice/transcribe-upload', {
    method: 'POST',
    body: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

// ── Predictive — what LOVE thinks Karthi needs ──
export async function getPrediction() {
  return base('/love/predict');
}

// ── Executive — tasks, brief, reminders ──
export async function getTasks(filter = 'active') {
  return base(`/executive/tasks?filter=${filter}`);
}
export async function addTask(text, deadline, source = 'companion') {
  return base('/executive/tasks', {
    method: 'POST',
    body: JSON.stringify({ text, deadline, source }),
  });
}
export async function completeTask(taskId) {
  return base('/executive/tasks/complete', {
    method: 'POST',
    body: JSON.stringify({ task_id: taskId }),
  });
}
export async function getBrief() {
  return base('/executive/brief');
}
export async function addReminder(text, triggerAt) {
  return base('/executive/reminder', {
    method: 'POST',
    body: JSON.stringify({ text, trigger_at: triggerAt }),
  });
}

// ── Emotional ──
export async function getEmotionalSummary() {
  return base('/emotional/summary');
}

// ── Long-term Memory ──
export async function remember(query, limit = 5) {
  return base(`/memory/life/remember?q=${encodeURIComponent(query)}&limit=${limit}`);
}
export async function getLifeSummary(period = 'week') {
  return base(`/memory/life/summary?period=${period}`);
}
export async function getProfile() {
  return base('/memory/life/profile');
}

// ── System Control ──
export async function getSystemInfo() {
  return base('/system/info');
}
export async function getActiveWindow() {
  return base('/system/active_window');
}
export async function getClipboard() {
  return base('/system/clipboard');
}
export async function searchFiles(query) {
  return base(`/system/search_files?query=${encodeURIComponent(query)}`);
}

// ── AGI-Level Systems ──
export async function getAutonomousGoals() {
  return base('/agi/autonomous/goals');
}

export async function generateAutonomousGoals() {
  return base('/agi/autonomous/generate-goals', { method: 'POST' });
}

export async function getPredictions() {
  return base('/agi/predictive/predictions');
}

export async function anticipateNeeds() {
  return base('/agi/predictive/anticipate-needs', { method: 'POST' });
}

export async function getPendingApprovals() {
  return base('/agi/actions/approvals/pending');
}

export async function approveAction(actionId) {
  return base('/agi/actions/approve', {
    method: 'POST',
    body: JSON.stringify({ action_id: actionId }),
  });
}

export async function rejectAction(actionId) {
  return base('/agi/actions/reject', {
    method: 'POST',
    body: JSON.stringify({ action_id: actionId }),
  });
}

export async function getMetaCognitiveSummary() {
  return base('/agi/meta-cognition/summary');
}

export async function getSelfImprovementSuggestions() {
  return base('/agi/meta-cognition/improvement-suggestions');
}

export async function getHolisticView() {
  return base('/agi/cross-domain/holistic');
}
