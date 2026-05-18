/**
 * LOVE Office Laptop Agent
 * 
 * Runs on your office laptop (Windows/Mac/Linux).
 * - Polls Microsoft Graph for Outlook emails, Teams messages, Calendar
 * - Pushes everything to the LOVE server every 60s
 * - Sends device heartbeat so LOVE knows this laptop is online
 * - Shows Windows notifications for urgent LOVE alerts
 * 
 * Setup:
 *   1. Copy config.example.json -> config.json and fill in values
 *   2. npm install
 *   3. node agent.js
 *   4. First run: opens browser for Microsoft login (once only)
 * 
 * Auto-start on Windows boot:
 *   node install-service.js
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const fetch = require('node-fetch');

// ── Config ──────────────────────────────────────────────

const CONFIG_FILE = path.join(__dirname, 'config.json');
const TOKEN_FILE = path.join(__dirname, '.ms_token.json');

function loadConfig() {
  if (!fs.existsSync(CONFIG_FILE)) {
    const example = {
      love_server: "http://192.168.1.100:8000",
      device_id: "office-laptop",
      device_name: "Office Laptop",
      microsoft_client_id: "",
      sync_interval_seconds: 60,
      notify_on_alerts: true,
    };
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(example, null, 2));
    console.log('[LOVE Agent] Created config.json — please fill in your values and restart.');
    process.exit(0);
  }
  return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
}

const config = loadConfig();
const LOVE_SERVER = config.love_server;
const DEVICE_ID = config.device_id || 'office-laptop';
const DEVICE_NAME = config.device_name || `Office-${os.hostname()}`;
const MS_CLIENT_ID = config.microsoft_client_id;
const INTERVAL = (config.sync_interval_seconds || 60) * 1000;

// ── LOVE API helpers ─────────────────────────────────────

async function lovePost(path, body) {
  try {
    const res = await fetch(`${LOVE_SERVER}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      timeout: 10000,
    });
    return res.json();
  } catch (e) {
    // server unreachable
    return null;
  }
}

async function loveGet(path) {
  try {
    const res = await fetch(`${LOVE_SERVER}${path}`, { timeout: 10000 });
    return res.json();
  } catch {
    return null;
  }
}

// ── Device heartbeat ─────────────────────────────────────

async function sendHeartbeat() {
  await lovePost('/devices/heartbeat', {
    device_id: DEVICE_ID,
    device_name: DEVICE_NAME,
    device_type: 'laptop',
    os: `${os.platform()} ${os.release()}`,
    ip: getLocalIP(),
    extra: { hostname: os.hostname(), user: os.userInfo().username },
  });
}

function getLocalIP() {
  const ifaces = os.networkInterfaces();
  for (const iface of Object.values(ifaces)) {
    for (const addr of iface) {
      if (addr.family === 'IPv4' && !addr.internal) return addr.address;
    }
  }
  return '';
}

// ── Microsoft Graph ──────────────────────────────────────

let msToken = null;

function loadToken() {
  if (fs.existsSync(TOKEN_FILE)) {
    try {
      msToken = JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8'));
    } catch {}
  }
}

function saveToken(token) {
  msToken = token;
  fs.writeFileSync(TOKEN_FILE, JSON.stringify(token, null, 2));
}

async function getAccessToken() {
  if (!MS_CLIENT_ID) return null;

  // Check cached token
  if (msToken && msToken.access_token) {
    const expiresAt = msToken.expires_at || 0;
    if (Date.now() / 1000 < expiresAt - 60) {
      return msToken.access_token;
    }
    // Try refresh
    if (msToken.refresh_token) {
      const refreshed = await refreshToken(msToken.refresh_token);
      if (refreshed) return refreshed;
    }
  }

  // Start device code flow via LOVE backend
  console.log('[LOVE Agent] Starting Microsoft auth via LOVE server...');
  const authRes = await lovePost('/integrations/microsoft/auth', {});
  if (!authRes || !authRes.success) {
    console.log('[LOVE Agent] Microsoft auth failed:', authRes?.error);
    return null;
  }

  console.log('\n' + '='.repeat(60));
  console.log('[LOVE Agent] MICROSOFT LOGIN REQUIRED');
  console.log(`Visit: ${authRes.verification_uri}`);
  console.log(`Enter code: ${authRes.user_code}`);
  console.log('='.repeat(60) + '\n');

  // Try to open browser automatically
  try {
    const { exec } = require('child_process');
    exec(`start ${authRes.verification_uri}`);
  } catch {}

  // Poll for completion via LOVE backend status
  const deadline = Date.now() + (authRes.expires_in || 900) * 1000;
  while (Date.now() < deadline) {
    await sleep(5000);
    const status = await loveGet('/integrations/microsoft/status');
    if (status?.connected) {
      console.log('[LOVE Agent] Microsoft connected!');
      // Token is stored in LOVE backend — we'll use LOVE's endpoints from now on
      saveToken({ via_love: true, connected: true, expires_at: Date.now() / 1000 + 3600 });
      return 'via_love';
    }
  }
  return null;
}

async function refreshToken(refreshToken) {
  try {
    const params = new URLSearchParams({
      client_id: MS_CLIENT_ID,
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      scope: 'Mail.Read Calendars.Read Chat.Read Files.Read.All User.Read Presence.Read',
    });
    const res = await fetch(
      'https://login.microsoftonline.com/common/oauth2/v2.0/token',
      { method: 'POST', body: params, headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    const data = await res.json();
    if (data.access_token) {
      data.expires_at = Date.now() / 1000 + (data.expires_in || 3600);
      saveToken(data);
      return data.access_token;
    }
  } catch {}
  return null;
}

async function graphGet(path, token) {
  if (token === 'via_love') return null; // will use LOVE endpoints
  try {
    const res = await fetch(`https://graph.microsoft.com/v1.0${path}`, {
      headers: { Authorization: `Bearer ${token}`, Accept: 'application/json' },
      timeout: 10000,
    });
    return res.json();
  } catch {
    return null;
  }
}

// ── Main sync loop ────────────────────────────────────────

let _prevUnread = 0;
let _prevTeams = 0;

async function syncMicrosoft(token) {
  try {
    if (token === 'via_love') {
      // Delegate to LOVE backend — it has the token
      const emailData = await loveGet('/integrations/microsoft/email');
      const calData = await loveGet('/integrations/microsoft/calendar');
      const teamsData = await loveGet('/integrations/microsoft/teams');

      const unread = emailData?.unread_count || 0;
      const teamsMessages = teamsData?.messages?.length || 0;
      const nextEvent = calData?.next_event;

      // Push summary to LOVE device events
      if (unread > _prevUnread) {
        await lovePost('/devices/push', {
          device_id: DEVICE_ID,
          type: 'outlook_email',
          title: 'New Outlook emails',
          body: `${unread} unread emails`,
          extra: { unread_count: unread },
        });
        notify('New Outlook emails', `${unread} unread`);
      }
      if (teamsMessages > _prevTeams) {
        await lovePost('/devices/push', {
          device_id: DEVICE_ID,
          type: 'teams_message',
          title: 'New Teams messages',
          body: `${teamsMessages} new messages`,
        });
        notify('Teams', `${teamsMessages} new messages`);
      }
      _prevUnread = unread;
      _prevTeams = teamsMessages;

      console.log(`[LOVE Agent] Synced — ${unread} emails, ${teamsMessages} Teams, next: ${nextEvent?.title || 'none'}`);
    }
  } catch (e) {
    console.error('[LOVE Agent] Sync error:', e.message);
  }
}

// ── Windows notifications ─────────────────────────────────

function notify(title, message) {
  if (!config.notify_on_alerts) return;
  try {
    const notifier = require('node-notifier');
    notifier.notify({ title: `LOVE — ${title}`, message, appName: 'LOVE Agent' });
  } catch {}
}

// ── Poll for LOVE alerts (proactive interventions) ────────

async function pollLoveAlerts() {
  try {
    const data = await loveGet('/orchestrator/interventions');
    const interventions = data?.interventions || [];
    for (const inv of interventions) {
      if (inv.urgency === 'critical' || inv.urgency === 'high') {
        notify('LOVE Alert', inv.message);
      }
    }
  } catch {}
}

// ── Util ──────────────────────────────────────────────────

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Main ─────────────────────────────────────────────────

async function main() {
  console.log('[LOVE Agent] Starting...');
  console.log(`[LOVE Agent] Server: ${LOVE_SERVER}`);
  console.log(`[LOVE Agent] Device: ${DEVICE_NAME} (${DEVICE_ID})`);

  loadToken();

  // Initial heartbeat
  await sendHeartbeat();
  console.log('[LOVE Agent] Heartbeat sent');

  // Auth Microsoft if client ID configured
  let msAccessToken = null;
  if (MS_CLIENT_ID) {
    msAccessToken = await getAccessToken();
  } else {
    console.log('[LOVE Agent] No MICROSOFT_CLIENT_ID — Teams/Outlook sync disabled');
    console.log('[LOVE Agent] Add microsoft_client_id to config.json to enable');
  }

  if (msAccessToken) {
    await syncMicrosoft(msAccessToken);
  }

  // Main loop
  setInterval(async () => {
    await sendHeartbeat();
    if (msAccessToken) {
      // Re-check token freshness
      msAccessToken = await getAccessToken();
      if (msAccessToken) await syncMicrosoft(msAccessToken);
    }
    await pollLoveAlerts();
  }, INTERVAL);

  console.log(`[LOVE Agent] Running — syncing every ${INTERVAL / 1000}s`);
  console.log('[LOVE Agent] Keep this terminal open, or run: node install-service.js');
}

main().catch(console.error);
