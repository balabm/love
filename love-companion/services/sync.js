/**
 * Background sync — Jarvis-level proactive intelligence.
 * Every 60s: heartbeat, battery, location, context check.
 * Proactive alerts: low battery, meeting imminent, missed nudges.
 * LOVE insights: doc analyst, idle mind thoughts, autonomous initiatives.
 */
import * as Battery from 'expo-battery';
import * as Location from 'expo-location';
import * as Device from 'expo-device';
import * as Network from 'expo-network';
import { Platform } from 'react-native';
import { sendHeartbeat, pushEvent, getContext } from './api';

let _syncInterval = null;
let _contextInterval = null;
let _insightsInterval = null;
let _lastBattery = null;
let _lastBatteryAlert = null;
let _locationSub = null;
let _lastMeetingAlert = null;
let _lastContextNudge = null;
let _lastInsightAlert = null;
let _notifReady = false;
let _insightHistory = [];

async function initNotifications() {
  if (_notifReady) return true;
  try {
    const Notifications = require('expo-notifications');
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: false,
        shouldSetBadge: false,
      }),
    });
    const { status } = await Notifications.requestPermissionsAsync();
    _notifReady = status === 'granted';
  } catch {}
  return _notifReady;
}

async function notify(title, body) {
  try {
    const Notifications = require('expo-notifications');
    await Notifications.scheduleNotificationAsync({
      content: { title, body },
      trigger: null,
    });
  } catch {}
}

export async function startSync() {
  if (_syncInterval) return;

  await initNotifications();
  await runSync();
  _syncInterval = setInterval(runSync, 60000);

  // Context awareness check every 3 minutes
  _contextInterval = setInterval(runContextCheck, 180000);

  // LOVE insights check every 5 minutes
  _insightsInterval = setInterval(runInsightsCheck, 300000);

  // Location
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status === 'granted') {
      _locationSub = await Location.watchPositionAsync(
        { accuracy: Location.Accuracy.Balanced, distanceInterval: 300 },
        async (loc) => {
          await pushEvent('location', 'Location update', '', {
            lat: loc.coords.latitude,
            lon: loc.coords.longitude,
            accuracy: loc.coords.accuracy,
          }).catch(() => {});
        }
      );
    }
  } catch {}
}

export function stopSync() {
  if (_syncInterval) { clearInterval(_syncInterval); _syncInterval = null; }
  if (_contextInterval) { clearInterval(_contextInterval); _contextInterval = null; }
  if (_insightsInterval) { clearInterval(_insightsInterval); _insightsInterval = null; }
  if (_locationSub) { _locationSub.remove(); _locationSub = null; }
}

async function runSync() {
  try {
    const [batteryLevel, batteryState, netState] = await Promise.all([
      Battery.getBatteryLevelAsync(),
      Battery.getBatteryStateAsync(),
      Network.getNetworkStateAsync(),
    ]);

    const batteryPct = Math.round(batteryLevel * 100);
    const charging = batteryState === Battery.BatteryState.CHARGING ||
                     batteryState === Battery.BatteryState.FULL;

    // Proactive battery alert — notify once per drop below threshold
    if (!charging && batteryPct <= 15 && _lastBatteryAlert !== 15) {
      _lastBatteryAlert = 15;
      await notify('♡ LOVE — Battery Critical', `Your phone is at ${batteryPct}%. Plug in!`);
      await pushEvent('battery_critical', 'Phone battery critical', `${batteryPct}%`, { battery: batteryPct }).catch(() => {});
    } else if (!charging && batteryPct <= 25 && _lastBatteryAlert !== 25 && _lastBatteryAlert !== 15) {
      _lastBatteryAlert = 25;
      await notify('♡ LOVE — Low Battery', `Phone at ${batteryPct}%. Might want to charge soon.`);
      await pushEvent('battery_low', 'Phone battery low', `${batteryPct}%`, { battery: batteryPct }).catch(() => {});
    } else if (charging || batteryPct > 30) {
      _lastBatteryAlert = null;
    }
    _lastBattery = batteryPct;

    await sendHeartbeat({
      device_name: Device.deviceName || 'OnePlus',
      device_type: Device.deviceType === Device.DeviceType.TABLET ? 'tablet' : 'phone',
      os: `${Platform.OS} ${Platform.Version}`,
      battery: batteryPct,
      charging,
      network: netState.type,
      extra: {
        model: Device.modelName,
        brand: Device.brand,
        sdk: Device.osVersion,
      },
    });
  } catch {}
}

async function runContextCheck() {
  try {
    const ctx = await getContext();
    if (!ctx) return;

    const now = Date.now();

    // Meeting imminent alert (within 5 min)
    if (ctx.next_event && ctx.next_event.minutes_away <= 5 && !ctx.is_in_meeting) {
      const alertKey = ctx.next_event.title + ctx.next_event.time;
      if (_lastMeetingAlert !== alertKey) {
        _lastMeetingAlert = alertKey;
        await notify(
          `♡ Meeting in ${ctx.next_event.minutes_away}min`,
          ctx.next_event.title
        );
      }
    }

    // Proactive LOVE nudge — if there are alerts and last nudge was >30min ago
    if (ctx.alerts?.length > 0) {
      const nudgeCooldown = 30 * 60 * 1000;
      if (!_lastContextNudge || now - _lastContextNudge > nudgeCooldown) {
        _lastContextNudge = now;
        await notify('♡ LOVE Notice', ctx.alerts[0]);
      }
    }

    // PC battery critical nudge
    if (ctx.battery != null && ctx.battery < 10 && !ctx.battery_charging) {
      await notify('♡ PC Battery Critical', `Home PC is at ${ctx.battery.toFixed(0)}%!`);
    }
  } catch {}
}

async function runInsightsCheck() {
  try {
    const ctx = await getContext();
    if (!ctx) return;

    const now = Date.now();
    const insights = [];

    // Doc analyst insights
    if (ctx.doc_insights && ctx.doc_insights.length > 0) {
      ctx.doc_insights.forEach(insight => {
        const key = `doc_${insight}`;
        if (!_lastInsightAlert || _lastInsightAlert[key] !== now) {
          insights.push({ type: 'doc', text: insight, key });
          if (!_lastInsightAlert) _lastInsightAlert = {};
          _lastInsightAlert[key] = now;
        }
      });
    }

    // Active project changes
    if (ctx.active_project && ctx.recent_files && ctx.recent_files.length > 0) {
      const key = `project_${ctx.active_project}`;
      if (!_lastInsightAlert || _lastInsightAlert[key] !== now) {
        insights.push({ 
          type: 'project', 
          text: `Working on: ${ctx.active_project}`, 
          detail: `Recent: ${ctx.recent_files[0]?.name}`,
          key 
        });
        if (!_lastInsightAlert) _lastInsightAlert = {};
        _lastInsightAlert[key] = now;
      }
    }

    // Fitness/work nudges
    if (ctx.fitness_streak === 0) {
      const key = 'fitness_streak';
      if (!_lastInsightAlert || _lastInsightAlert[key] !== now) {
        insights.push({ type: 'fitness', text: 'No workouts this week. Body needs movement!', key });
        if (!_lastInsightAlert) _lastInsightAlert = {};
        _lastInsightAlert[key] = now;
      }
    }

    // Store insights for notification center
    if (insights.length > 0) {
      _insightHistory = [...insights, ..._insightHistory].slice(0, 50);
      
      // Push to LOVE backend for cross-device sync
      for (const insight of insights) {
        await pushEvent('insight', `LOVE Insight: ${insight.type}`, insight.text, {
          type: insight.type,
          detail: insight.detail,
          timestamp: new Date().toISOString()
        }).catch(() => {});
      }

      // Notify on most important insight (with cooldown)
      const cooldown = 60 * 60 * 1000; // 1 hour
      if (!_lastContextNudge || now - _lastContextNudge > cooldown) {
        _lastContextNudge = now;
        const topInsight = insights[0];
        await notify('♡ LOVE Insight', topInsight.text);
      }
    }
  } catch {}
}

export function getInsightHistory() {
  return _insightHistory;
}
