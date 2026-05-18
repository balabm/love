/**
 * LOVE Push Notifications Service
 *
 * Handles push notifications from LOVE server with context-aware routing:
 * - Proactive interruptions ("Standup in 5 min")
 * - Task reminders
 * - Alerts (battery critical, etc)
 * - Chat messages from other devices
 * - Context-aware routing based on time, stress, activity
 * 
 * Note: Expo Go doesn't support push notifications from SDK 53+
 * Use development build for full push notification support.
 */

import { Platform } from 'react-native';

let Notifications = null;
let isSetup = false;
let notificationHistory = [];

// Lazy load expo-notifications to avoid errors in Expo Go
async function loadNotifications() {
  if (Notifications) return Notifications;
  try {
    Notifications = await import('expo-notifications');
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
    return Notifications;
  } catch (e) {
    console.warn('[Notifications] expo-notifications not available (Expo Go limitation)');
    return null;
  }
}

// Context-aware notification routing
export async function shouldRouteNotification(notification, context = {}) {
  // Determine if a notification should be shown based on context
  // Returns: { shouldShow: boolean, delay: number, channel: string }
  const { 
    timeOfDay = 'day', 
    stressLevel = 0, 
    inMeeting = false,
    isSleeping = false,
    isDeepWork = false,
    notificationType = 'general'
  } = context;

  // Don't show during sleep
  if (isSleeping) {
    return { shouldShow: false, delay: 0, channel: 'silent' };
  }

  // Don't interrupt deep work for non-critical notifications
  if (isDeepWork && notificationType !== 'critical') {
    return { shouldShow: false, delay: 0, channel: 'silent' };
  }

  // Don't interrupt meetings unless critical
  if (inMeeting && notificationType !== 'critical') {
    return { shouldShow: false, delay: 0, channel: 'silent' };
  }

  // High stress - reduce notification frequency
  if (stressLevel > 7) {
    // Only show critical notifications
    if (notificationType === 'critical') {
      return { shouldShow: true, delay: 0, channel: 'love-alerts' };
    }
    // Delay non-critical notifications
    return { shouldShow: true, delay: 300, channel: 'love-reminders' };
  }

  // Night time - only critical alerts
  if (timeOfDay === 'night') {
    if (notificationType === 'critical') {
      return { shouldShow: true, delay: 0, channel: 'love-alerts' };
    }
    return { shouldShow: false, delay: 0, channel: 'silent' };
  }

  // Default routing based on type
  const channelMap = {
    'critical': 'love-alerts',
    'meeting': 'love-alerts',
    'battery': 'love-alerts',
    'reminder': 'love-reminders',
    'chat': 'love-chat',
    'insight': 'love-reminders',
    'general': 'love-reminders',
  };

  return {
    shouldShow: true,
    delay: 0,
    channel: channelMap[notificationType] || 'love-reminders'
  };
}

export async function sendContextAwareNotification(title, body, context = {}) {
  // Send notification with context-aware routing
  // Automatically determines channel, timing, and whether to show
  const routing = await shouldRouteNotification({
    notificationType: context.type || 'general',
    ...context
  }, context);

  if (!routing.shouldShow) {
    console.log('[Notifications] Notification suppressed by context routing');
    return null;
  }

  const Notifs = await loadNotifications();
  if (!Notifs) return null;

  if (routing.delay > 0) {
    // Schedule delayed notification
    return Notifs.scheduleNotificationAsync({
      content: { title, body, data: { type: context.type || 'general' } },
      trigger: { seconds: routing.delay },
      channel: routing.channel,
    });
  }

  // Show immediately
  return Notifs.scheduleNotificationAsync({
    content: { title, body, data: { type: context.type || 'general' } },
    trigger: null,
    channel: routing.channel,
  });
}

export async function setupNotifications() {
  const Notifs = await loadNotifications();
  if (!Notifs) return null;

  const { status: existingStatus } = await Notifs.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifs.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn('[Notifications] Permission not granted');
    return null;
  }

  // Android channels — safe to call multiple times
  if (Platform.OS === 'android' && !isSetup) {
    await Notifs.setNotificationChannelAsync('love-alerts', {
      name: 'LOVE Alerts',
      importance: Notifs.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#c084fc',
      sound: 'default',
    });
    await Notifs.setNotificationChannelAsync('love-reminders', {
      name: 'LOVE Reminders',
      importance: Notifs.AndroidImportance.DEFAULT,
      vibrationPattern: [0, 100],
    });
    await Notifs.setNotificationChannelAsync('love-chat', {
      name: 'LOVE Chat',
      importance: Notifs.AndroidImportance.DEFAULT,
    });
    await Notifs.setNotificationChannelAsync('love-silent', {
      name: 'LOVE Silent',
      importance: Notifs.AndroidImportance.MIN,
      sound: null,
      vibrate: false,
    });
  }
  isSetup = true;

  try {
    const tokenData = await Notifs.getExpoPushTokenAsync();
    return tokenData.data;
  } catch (e) {
    console.warn('[Notifications] Could not get push token:', e.message);
    return null;
  }
}

export async function scheduleLocalReminder(title, body, triggerSeconds = 60) {
  const Notifs = await loadNotifications();
  if (!Notifs) return null;
  return Notifs.scheduleNotificationAsync({
    content: { title, body, data: { type: 'reminder' } },
    trigger: { seconds: triggerSeconds },
  });
}

export function addNotificationListener(handler) {
  loadNotifications().then(Notifs => {
    if (Notifs) Notifs.addNotificationReceivedListener(handler);
  });
}

export function addResponseListener(handler) {
  loadNotifications().then(Notifs => {
    if (Notifs) Notifs.addNotificationResponseReceivedListener(handler);
  });
}

export async function cancelAllNotifications() {
  const Notifs = await loadNotifications();
  if (!Notifs) return;
  await Notifs.cancelAllScheduledNotificationsAsync();
}
