/**
 * Notification Intelligence Layer
 *
 * Listens to incoming notifications, classifies them, filters noise,
 * extracts sender identity, pushes important ones to LOVE server memory.
 *
 * Classification:
 *   IMPORTANT  — WhatsApp, Teams, SMS, Gmail personal, Slack, Signal
 *   WORK       — Calendar, Jira, GitHub, Azure DevOps
 *   SYSTEM     — Battery, app updates, phone alerts
 *   NOISE      — Ads, promotions, delivery spam, gaming (filtered out)
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { pushEvent, sendNotifToMemory } from './api';
import { upsertPerson } from './profile';

const SEEN_KEY = 'love_seen_notifs';

// Apps that carry meaningful social/work signals
const IMPORTANT_APPS = [
  'com.whatsapp', 'com.whatsapp.w4b',
  'com.microsoft.teams', 'com.microsoft.teams.new',
  'com.slack', 'com.discord',
  'com.google.android.gm',
  'org.telegram.messenger', 'org.telegram.plus',
  'com.google.android.apps.messaging', // SMS
  'com.samsung.android.messaging',
  'com.oneplus.sms',
  'org.thoughtcrime.securesms', // Signal
  'com.instagram.android',
];

const WORK_APPS = [
  'com.microsoft.outlook',
  'com.google.android.calendar',
  'com.atlassian.android.jira.core',
  'com.github.android',
  'com.azure.devops',
  'com.microsoft.office.outlook',
];

// Patterns that indicate spam/ads — skip these
const NOISE_PATTERNS = [
  /offer/i, /sale/i, /discount/i, /% off/i, /deal/i, /coupon/i,
  /promo/i, /free/i, /win/i, /claim/i, /reward/i, /cashback/i,
  /swiggy/i, /zomato/i, /amazon/i, /flipkart/i, /myntra/i,
  /phonepe/i, /paytm/i, /gpay/i, /uber eats/i,
  /ads\b/i, /sponsored/i, /newsletter/i,
];

// App-to-source mapping for display
const APP_LABELS = {
  'com.whatsapp': 'WhatsApp',
  'com.whatsapp.w4b': 'WhatsApp Business',
  'com.microsoft.teams': 'Teams',
  'com.microsoft.teams.new': 'Teams',
  'com.slack': 'Slack',
  'com.discord': 'Discord',
  'com.google.android.gm': 'Gmail',
  'org.telegram.messenger': 'Telegram',
  'org.telegram.plus': 'Telegram',
  'com.google.android.apps.messaging': 'SMS',
  'com.samsung.android.messaging': 'SMS',
  'com.oneplus.sms': 'SMS',
  'org.thoughtcrime.securesms': 'Signal',
  'com.instagram.android': 'Instagram',
  'com.microsoft.outlook': 'Outlook',
  'com.google.android.calendar': 'Calendar',
};

function isNoise(title, body, packageName) {
  const text = `${title} ${body}`;
  return NOISE_PATTERNS.some(p => p.test(text));
}

function extractSender(title, body, app) {
  // WhatsApp: title is usually "Sender Name" or "Sender Name @ Group"
  if (app.includes('whatsapp')) {
    const groupMatch = title.match(/^(.+?)\s*@\s*(.+)$/);
    if (groupMatch) return { name: groupMatch[1].trim(), group: groupMatch[2].trim(), channel: 'WhatsApp' };
    return { name: title.trim(), group: null, channel: 'WhatsApp' };
  }
  // Teams: "Name in Channel" or "Name"
  if (app.includes('teams')) {
    const teamMatch = title.match(/^(.+?)\s+in\s+(.+)$/i);
    if (teamMatch) return { name: teamMatch[1].trim(), group: teamMatch[2].trim(), channel: 'Teams' };
    return { name: title.trim(), group: null, channel: 'Teams' };
  }
  if (app.includes('slack')) return { name: title.trim(), group: null, channel: 'Slack' };
  if (app.includes('telegram')) return { name: title.trim(), group: null, channel: 'Telegram' };
  if (app.includes('signal')) return { name: title.trim(), group: null, channel: 'Signal' };
  if (app.includes('messaging') || app.includes('sms')) return { name: title.trim(), group: null, channel: 'SMS' };
  return { name: title.trim(), group: null, channel: APP_LABELS[app] || app };
}

async function wasSeen(id) {
  try {
    const raw = await AsyncStorage.getItem(SEEN_KEY);
    const seen = raw ? JSON.parse(raw) : [];
    return seen.includes(id);
  } catch { return false; }
}

async function markSeen(id) {
  try {
    const raw = await AsyncStorage.getItem(SEEN_KEY);
    const seen = raw ? JSON.parse(raw) : [];
    seen.push(id);
    // Keep last 200 only
    await AsyncStorage.setItem(SEEN_KEY, JSON.stringify(seen.slice(-200)));
  } catch {}
}

export async function processNotification(notif) {
  try {
    const { title = '', body = '', data = {} } = notif.request?.content || notif;
    const packageName = data?.packageName || data?.sourceApp || '';

    const isImportant = IMPORTANT_APPS.some(a => packageName.includes(a.split('.').pop()));
    const isWork = WORK_APPS.some(a => packageName.includes(a.split('.').pop()));

    // Skip noise aggressively
    if (!isImportant && !isWork) return;
    if (isNoise(title, body, packageName)) return;

    const notifId = `${packageName}:${title}:${body}`.slice(0, 120);
    if (await wasSeen(notifId)) return;
    await markSeen(notifId);

    const sender = extractSender(title, body, packageName);

    // Update person in local people DB
    if (sender.name && sender.name.length > 1) {
      await upsertPerson(sender.name.toLowerCase(), {
        displayName: sender.name,
        channels: [sender.channel],
        lastMessage: body.slice(0, 200),
        lastGroup: sender.group,
      });
    }

    // Push to LOVE server memory
    await pushEvent('notification', `${sender.channel}: ${sender.name}`, body, {
      source_app: packageName,
      channel: sender.channel,
      sender: sender.name,
      group: sender.group,
      raw_title: title,
      raw_body: body,
      importance: isImportant ? 'high' : 'work',
    }).catch(() => {});

  } catch {}
}

let _notifSub = null;

export async function startNotificationListener() {
  if (_notifSub) return;
  try {
    const Notifications = require('expo-notifications');
    _notifSub = Notifications.addNotificationReceivedListener(processNotification);
  } catch {}
}

export function stopNotificationListener() {
  if (_notifSub) {
    try { _notifSub.remove(); } catch {}
    _notifSub = null;
  }
}
