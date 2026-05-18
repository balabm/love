/**
 * LOVE Profile Service — persistent user profile.
 * Stores and retrieves Karthi's personal details, routine, and preferences.
 * Also builds a "people database" from contacts seen in notifications.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const PROFILE_KEY = 'love_user_profile';
const PEOPLE_KEY = 'love_people_db';
const ONBOARDED_KEY = 'love_onboarded';

export const DEFAULT_PROFILE = {
  name: '',
  profession: '',
  company: '',
  salary: '',
  location: '',
  routine: {
    wakeTime: '',
    sleepTime: '',
    workStart: '',
    workEnd: '',
    workDays: [],
  },
  goals: [],
  interests: [],
  health: {
    conditions: '',
    fitnessGoal: '',
  },
  devices: [],
  createdAt: null,
  updatedAt: null,
};

export async function getProfile() {
  try {
    const raw = await AsyncStorage.getItem(PROFILE_KEY);
    return raw ? { ...DEFAULT_PROFILE, ...JSON.parse(raw) } : null;
  } catch { return null; }
}

export async function saveProfile(profile) {
  try {
    const existing = await getProfile() || {};
    const updated = {
      ...existing,
      ...profile,
      updatedAt: new Date().toISOString(),
      createdAt: existing.createdAt || new Date().toISOString(),
    };
    await AsyncStorage.setItem(PROFILE_KEY, JSON.stringify(updated));
    return updated;
  } catch { return null; }
}

export async function isOnboarded() {
  try {
    const v = await AsyncStorage.getItem(ONBOARDED_KEY);
    return v === 'true';
  } catch { return false; }
}

export async function setOnboarded() {
  await AsyncStorage.setItem(ONBOARDED_KEY, 'true');
}

export async function resetOnboarding() {
  await AsyncStorage.removeItem(ONBOARDED_KEY);
  await AsyncStorage.removeItem(PROFILE_KEY);
}

// ── People database ─────────────────────────────────────────────────────────
// Builds up over time from notifications, chats, contacts seen.

export async function getPeople() {
  try {
    const raw = await AsyncStorage.getItem(PEOPLE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

export async function upsertPerson(identifier, update) {
  try {
    const people = await getPeople();
    const existing = people[identifier] || { id: identifier, seenCount: 0, firstSeen: new Date().toISOString() };
    people[identifier] = {
      ...existing,
      ...update,
      seenCount: (existing.seenCount || 0) + 1,
      lastSeen: new Date().toISOString(),
    };
    await AsyncStorage.setItem(PEOPLE_KEY, JSON.stringify(people));
    return people[identifier];
  } catch {}
}

export async function getPerson(identifier) {
  const people = await getPeople();
  return people[identifier] || null;
}
