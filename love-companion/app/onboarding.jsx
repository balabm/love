/**
 * LOVE Onboarding — First-run personal interview.
 * Asks Karthi about himself in a conversational style.
 * Saves to profile, syncs to server, then redirects to main app.
 */
import { useState, useRef, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, KeyboardAvoidingView, Platform, Animated,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { router } from 'expo-router';
import { saveProfile, setOnboarded } from '../services/profile';
import { syncProfile } from '../services/api';

const STEPS = [
  {
    key: 'welcome',
    type: 'info',
    love: "Hey there ♡\n\nI'm LOVE — your personal life companion. Before we begin, I want to know you properly.\n\nThis will only take 2 minutes. Everything stays private on your server.",
    cta: "Let's go →",
  },
  {
    key: 'name',
    type: 'text',
    love: "What should I call you?",
    placeholder: "Your name…",
    field: 'name',
  },
  {
    key: 'profession',
    type: 'text',
    love: (p) => `Nice to meet you, ${p.name}\n\nWhat do you do for a living?`,
    placeholder: "e.g. Software Engineer, Designer, Student…",
    field: 'profession',
  },
  {
    key: 'company',
    type: 'text',
    love: "Which company or place?",
    placeholder: "e.g. Google, startup, freelance, college…",
    field: 'company',
    optional: true,
  },
  {
    key: 'location',
    type: 'text',
    love: "Where are you based?",
    placeholder: "City, Country…",
    field: 'location',
  },
  {
    key: 'wakeTime',
    type: 'text',
    love: "What time do you usually wake up?",
    placeholder: "e.g. 7:00 AM",
    field: 'wakeTime',
    group: 'routine',
  },
  {
    key: 'workHours',
    type: 'text',
    love: "Work hours?",
    placeholder: "e.g. 9 AM – 6 PM",
    field: 'workHours',
    group: 'routine',
  },
  {
    key: 'goals',
    type: 'multitext',
    love: "What are your top 1-3 goals right now? (one per line)",
    placeholder: "e.g. Get fit\nSave money\nBuild a product",
    field: 'goals',
  },
  {
    key: 'interests',
    type: 'text',
    love: "What's on your mind? Hobbies, passions, things that matter to you?",
    placeholder: "e.g. coding, music, gym, chess, anime…",
    field: 'interests',
  },
  {
    key: 'health',
    type: 'text',
    love: "Any health things I should know? (fitness goals, conditions, diet — totally optional)",
    placeholder: "e.g. want to lose 5kg, diabetic, vegetarian…",
    field: 'health',
    optional: true,
  },
  {
    key: 'done',
    type: 'done',
    love: (p) => `Got it, ${p.name} ♡\n\nI've built your profile. From now on I'll watch over everything — your calendar, devices, notifications, health, and goals.\n\nLet's go.`,
    cta: 'Enter LOVE →',
  },
];

export default function OnboardingScreen() {
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState({});
  const [input, setInput] = useState('');
  const [saving, setSaving] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;

  const current = STEPS[step];

  useEffect(() => {
    fadeAnim.setValue(0);
    Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
  }, [step]);

  const getLoveText = () => {
    if (typeof current.love === 'function') return current.love(profile);
    return current.love;
  };

  const advance = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    if (current.type === 'info') {
      setStep(s => s + 1);
      return;
    }

    if (current.type === 'done') {
      setSaving(true);
      await finishOnboarding();
      return;
    }

    const val = input.trim();
    if (!val && !current.optional) return;

    let newProfile = { ...profile };
    if (current.group === 'routine') {
      newProfile.routine = { ...(newProfile.routine || {}), [current.field]: val };
    } else if (current.type === 'multitext') {
      newProfile[current.field] = val.split('\n').map(l => l.trim()).filter(Boolean);
    } else if (current.field === 'interests') {
      newProfile[current.field] = val.split(',').map(l => l.trim()).filter(Boolean);
    } else {
      newProfile[current.field] = val;
    }

    setProfile(newProfile);
    setInput('');
    setStep(s => s + 1);
  };

  const finishOnboarding = async () => {
    try {
      const saved = await saveProfile(profile);
      await setOnboarded();
      await syncProfile(saved).catch(() => {});
    } catch {}
    setSaving(false);
    router.replace('/(tabs)');
  };

  const progress = step / (STEPS.length - 1);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {/* Progress bar */}
      <View style={styles.progressTrack}>
        <Animated.View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
      </View>

      <ScrollView contentContainerStyle={styles.inner} keyboardShouldPersistTaps="handled">
        <Animated.View style={{ opacity: fadeAnim, flex: 1 }}>
          {/* LOVE avatar */}
          <View style={styles.avatarWrap}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>♡</Text>
            </View>
            <Text style={styles.avatarLabel}>LOVE</Text>
          </View>

          {/* Message */}
          <View style={styles.bubble}>
            <Text style={styles.bubbleText}>{getLoveText()}</Text>
          </View>

          {/* Input or CTA */}
          {(current.type === 'text' || current.type === 'multitext') && (
            <TextInput
              style={[styles.input, current.type === 'multitext' && styles.inputMulti]}
              value={input}
              onChangeText={setInput}
              placeholder={current.placeholder}
              placeholderTextColor="#374151"
              multiline={current.type === 'multitext'}
              numberOfLines={current.type === 'multitext' ? 4 : 1}
              autoFocus
              returnKeyType="done"
              onSubmitEditing={current.type !== 'multitext' ? advance : undefined}
            />
          )}

          <TouchableOpacity
            style={[styles.btn, saving && { opacity: 0.5 }]}
            onPress={advance}
            disabled={saving || (
              current.type !== 'info' &&
              current.type !== 'done' &&
              !current.optional &&
              !input.trim()
            )}
          >
            <Text style={styles.btnText}>
              {saving ? 'Saving…'
                : current.type === 'info' || current.type === 'done' ? (current.cta || 'Continue →')
                : current.optional && !input.trim() ? 'Skip →'
                : 'Continue →'}
            </Text>
          </TouchableOpacity>

          {/* Step indicator */}
          <Text style={styles.stepText}>{step + 1} / {STEPS.length}</Text>
        </Animated.View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  progressTrack: { height: 2, backgroundColor: 'rgba(192,132,252,0.15)', width: '100%' },
  progressFill: { height: 2, backgroundColor: '#c084fc' },
  inner: { flexGrow: 1, padding: 24, paddingTop: 60, justifyContent: 'center' },
  avatarWrap: { alignItems: 'center', marginBottom: 32 },
  avatar: {
    width: 60, height: 60, borderRadius: 30,
    backgroundColor: 'rgba(192,132,252,0.15)',
    borderWidth: 2, borderColor: 'rgba(192,132,252,0.4)',
    alignItems: 'center', justifyContent: 'center', marginBottom: 8,
  },
  avatarText: { fontSize: 28, color: '#c084fc' },
  avatarLabel: { color: '#c084fc', fontSize: 11, fontWeight: '700', letterSpacing: 2 },
  bubble: {
    backgroundColor: 'rgba(192,132,252,0.08)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
    borderRadius: 16, borderTopLeftRadius: 4,
    padding: 18, marginBottom: 24,
  },
  bubbleText: { color: '#e5e7eb', fontSize: 16, lineHeight: 26 },
  input: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.3)',
    borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14,
    color: '#e5e7eb', fontSize: 16, marginBottom: 16,
  },
  inputMulti: { height: 120, textAlignVertical: 'top' },
  btn: {
    backgroundColor: 'rgba(192,132,252,0.2)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.5)',
    borderRadius: 12, paddingVertical: 16, alignItems: 'center', marginBottom: 16,
  },
  btnText: { color: '#c084fc', fontSize: 16, fontWeight: '700', letterSpacing: 1 },
  stepText: { color: '#1f2937', fontSize: 11, textAlign: 'center' },
});
