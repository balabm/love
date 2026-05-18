import { useState, useRef, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
  Animated, ScrollView, Pressable,
} from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';
import { Audio } from 'expo-av';
import { sendChat, getContext, visionAnalyze, systemAction, voiceLoopStart, voiceLoopStop, voiceLoopStatus, uploadVoiceForTranscription } from '../../services/api';

const MODES = [
  { key: 'general', label: 'Talk', icon: '♡' },
  { key: 'focus', label: 'Focus', icon: '◎' },
  { key: 'vent', label: 'Vent', icon: '◌' },
  { key: 'plan', label: 'Plan', icon: '◇' },
  { key: 'code', label: 'Code', icon: '⌥' },
];

const QUICK_PROMPTS = [
  { text: "What should I focus on?", mode: 'focus' },
  { text: "How's my life score?", mode: 'general' },
  { text: "Any urgent alerts?", mode: 'general' },
  { text: "Plan my day", mode: 'plan' },
  { text: "I need to vent", mode: 'vent' },
  { text: "Review my code", mode: 'code' },
];

const QUICK_ACTIONS = [
  { label: '🖼', desc: 'Screenshot', action: 'screenshot', data: {} },
  { label: '🌐', desc: 'Chrome', action: 'open', data: { target: 'chrome' } },
  { label: '▶', desc: 'Play/Pause', action: 'media', data: { action: 'play_pause' } },
  { label: '🔒', desc: 'Lock', action: 'lock', data: {} },
  { label: '📸', desc: 'Image', action: 'image', data: {} },
  { label: '🎙', desc: 'Voice', action: 'voice', data: {} },
];

function TypingDots() {
  const dot1 = useRef(new Animated.Value(0.3)).current;
  const dot2 = useRef(new Animated.Value(0.3)).current;
  const dot3 = useRef(new Animated.Value(0.3)).current;
  useEffect(() => {
    const anim = (dot, delay) => Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.timing(dot, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.timing(dot, { toValue: 0.3, duration: 400, useNativeDriver: true }),
      ])
    ).start();
    anim(dot1, 0); anim(dot2, 150); anim(dot3, 300);
  }, []);
  return (
    <View style={{ flexDirection: 'row', gap: 4, paddingVertical: 8 }}>
      {[dot1, dot2, dot3].map((d, i) => (
        <Animated.View key={i} style={{ width: 7, height: 7, borderRadius: 4, backgroundColor: '#c084fc', opacity: d }} />
      ))}
    </View>
  );
}

export default function ChatScreen() {
  const params = useLocalSearchParams();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('general');
  const [ctx, setCtx] = useState(null);
  const [copied, setCopied] = useState(null);
  const [voiceActive, setVoiceActive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingUri, setRecordingUri] = useState(null);
  const recordingRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    loadGreeting();
  }, []);

  // Handle shared text from Android share intent
  useEffect(() => {
    if (params.sharedText) {
      const text = String(params.sharedText);
      setInput(text);
      // Clear the param so it doesn't re-trigger
      // (expo-router keeps params until navigation changes)
    }
  }, [params.sharedText]);

  const loadGreeting = async () => {
    try {
      const data = await getContext();
      setCtx(data);
      const hour = new Date().getHours();
      const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
      const summary = data?.summary || "I'm watching over things.";
      setMessages([{
        id: '0', role: 'love',
        text: `${greeting}, Karthi ♡\n\n${summary}\n\nWhat's on your mind?`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } catch {
      setMessages([{
        id: '0', role: 'love',
        text: "Hey Karthi ♡  I'm right here — server's a bit quiet though. Check your connection in Settings.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    }
  };

  const send = async (text, overrideMode) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const usedMode = overrideMode || mode;

    setMessages(prev => [...prev, {
      id: Date.now().toString(), role: 'user', text: msg,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
    setLoading(true);

    try {
      const res = await sendChat(msg, usedMode);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'love',
        text: res.response || "I'm thinking…",
        mode: usedMode,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'error',
        text: '⚠ Cannot reach LOVE server. Make sure it\'s running and check Settings.',
        time: '',
      }]);
    }
    setLoading(false);
  };

  const handleQuickAction = async (qa) => {
    if (qa.action === 'image') {
      await pickImage();
      return;
    }
    if (qa.action === 'voice') {
      await toggleVoiceLoop();
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setMessages(prev => [...prev, {
      id: Date.now().toString(), role: 'user', text: `[${qa.desc}]`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
    setLoading(true);
    try {
      const res = await systemAction(qa.action, qa.data);
      const msg = res.success
        ? `${qa.desc} done on PC${res.title ? ': ' + res.title : ''}${res.path ? ' (' + res.path + ')' : ''}.`
        : `${qa.desc} failed: ${res.error || 'unknown'}`;
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'love', text: msg,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'error',
        text: `⚠ ${qa.desc} error: ${e.message}`,
        time: '',
      }]);
    }
    setLoading(false);
  };

  const pickImage = async () => {
    try {
      const { launchImageLibraryAsync } = await import('expo-image-picker');
      const result = await launchImageLibraryAsync({
        mediaTypes: 'images',
        allowsEditing: false,
        quality: 0.7,
        base64: true,
      });
      if (result.canceled) return;

      const asset = result.assets[0];
      setMessages(prev => [...prev, {
        id: Date.now().toString(), role: 'user',
        text: `[📸 Image sent from phone]`, image: asset.uri,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      setLoading(true);

      // For now, prompt user with the image path — full upload flow needs file server endpoint
      const res = await sendChat(`I sent you an image from my phone. URI: ${asset.uri}. What do you see?`, mode);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'love',
        text: res.response || "I see the image but can't fully analyze it yet.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      setLoading(false);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'error',
        text: `⚠ Image picker: ${e.message}`,
        time: '',
      }]);
      setLoading(false);
    }
  };

  const toggleVoiceLoop = async () => {
    try {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      if (!voiceActive) {
        await voiceLoopStart();
        setVoiceActive(true);
        setMessages(prev => [...prev, {
          id: Date.now().toString(), role: 'love',
          text: '🎙 Voice loop started on PC. Say "Hey LOVE" to wake me.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]);
      } else {
        await voiceLoopStop();
        setVoiceActive(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(), role: 'love',
          text: '🎙 Voice loop stopped on PC.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(), role: 'error',
        text: `⚠ Voice loop error: ${e.message}`,
        time: '',
      }]);
    }
  };

  // ── Voice Recording ──
  const startRecording = async () => {
    try {
      const perm = await Audio.requestPermissionsAsync();
      if (perm.status !== 'granted') return;
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      setRecording(true);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } catch (e) {
      console.warn('Recording start error:', e);
    }
  };

  const stopRecording = async () => {
    try {
      setRecording(false);
      if (!recordingRef.current) return;
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      if (!uri) return;

      // Transcribe
      setMessages(prev => [...prev, {
        id: Date.now().toString(), role: 'user',
        text: '🎙 Voice message… transcribing…',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
      setLoading(true);

      const result = await uploadVoiceForTranscription(uri);
      const transcription = result?.transcription || '[Could not transcribe]';

      // Replace placeholder with transcription
      setMessages(prev => prev.map(m =>
        m.text === '🎙 Voice message… transcribing…' ? { ...m, text: `🎙 "${transcription}"` } : m
      ));

      // Send transcription as chat
      if (transcription && transcription !== '[Could not transcribe]') {
        await send(transcription, mode);
      }
      setLoading(false);
    } catch (e) {
      setLoading(false);
      setMessages(prev => [...prev, {
        id: Date.now().toString(), role: 'error',
        text: `⚠ Voice error: ${e.message}`,
        time: '',
      }]);
    }
  };

  const copyMsg = async (text, id) => {
    await Clipboard.setStringAsync(text);
    setCopied(id);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setTimeout(() => setCopied(null), 1500);
  };

  const renderMessage = ({ item }) => {
    const isUser = item.role === 'user';
    const isError = item.role === 'error';
    return (
      <View style={[styles.msgRow, isUser && styles.msgRowUser]}>
        {!isUser && (
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>♡</Text>
          </View>
        )}
        <Pressable
          onLongPress={() => !isError && copyMsg(item.text, item.id)}
          style={[styles.bubble, isUser ? styles.bubbleUser : isError ? styles.bubbleError : styles.bubbleLove]}
        >
          <Text style={[styles.bubbleText, isError && styles.errorText]}>{item.text}</Text>
          <View style={styles.bubbleFooter}>
            {item.mode && !isUser && (
              <Text style={styles.modeTag}>{MODES.find(m => m.key === item.mode)?.icon} {item.mode}</Text>
            )}
            {item.time ? <Text style={styles.timeText}>{item.time}</Text> : null}
            {copied === item.id && <Text style={styles.copiedText}>copied</Text>}
          </View>
        </Pressable>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      {/* Context banner */}
      {ctx?.alerts?.length > 0 && (
        <View style={styles.alertBanner}>
          <Text style={styles.alertBannerText}>⚠  {ctx.alerts[0]}</Text>
        </View>
      )}

      {/* Mode selector */}
      <View style={styles.modeRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 12, gap: 6 }}>
          {MODES.map(m => (
            <TouchableOpacity
              key={m.key}
              style={[styles.modeChip, mode === m.key && styles.modeChipActive]}
              onPress={() => { setMode(m.key); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
            >
              <Text style={[styles.modeIcon, mode === m.key && styles.modeIconActive]}>{m.icon}</Text>
              <Text style={[styles.modeLabel, mode === m.key && styles.modeLabelActive]}>{m.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Quick prompts */}
      <View style={styles.quickRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 12, gap: 6 }}>
          {QUICK_PROMPTS.map((q, i) => (
            <TouchableOpacity key={i} style={styles.quickChip} onPress={() => send(q.text, q.mode)}>
              <Text style={styles.quickText}>{q.text}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Messages */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.msgList}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        ListFooterComponent={loading ? (
          <View style={styles.typingRow}>
            <View style={styles.avatar}><Text style={styles.avatarText}>♡</Text></View>
            <View style={styles.typingBubble}><TypingDots /></View>
          </View>
        ) : null}
      />

      {/* Quick actions toolbar */}
      <View style={styles.actionBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 4, gap: 6 }}>
          {QUICK_ACTIONS.map((qa, i) => (
            <TouchableOpacity
              key={i}
              style={[styles.actionChip, qa.action === 'voice' && voiceActive && styles.actionChipActive]}
              onPress={() => handleQuickAction(qa)}
            >
              <Text style={styles.actionChipText}>{qa.label}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Input */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder={`${MODES.find(m => m.key === mode)?.icon} ${mode} mode…`}
          placeholderTextColor="#4b5563"
          multiline
          maxLength={2000}
          returnKeyType="default"
        />
        <TouchableOpacity
          style={[styles.micBtn, recording && styles.micBtnActive]}
          onPressIn={startRecording}
          onPressOut={stopRecording}
          activeOpacity={0.7}
        >
          <Text style={styles.micIcon}>🎙</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
          onPress={() => send()}
          disabled={!input.trim() || loading}
        >
          {loading
            ? <ActivityIndicator size="small" color="#c084fc" />
            : <Text style={styles.sendIcon}>↑</Text>
          }
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  alertBanner: {
    backgroundColor: 'rgba(245,158,11,0.12)', borderBottomWidth: 1,
    borderBottomColor: 'rgba(245,158,11,0.3)', paddingHorizontal: 16, paddingVertical: 8,
  },
  alertBannerText: { color: '#fbbf24', fontSize: 12 },
  modeRow: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: 'rgba(192,132,252,0.08)' },
  modeChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
  },
  modeChipActive: { backgroundColor: 'rgba(192,132,252,0.18)', borderColor: 'rgba(192,132,252,0.4)' },
  modeIcon: { fontSize: 13, color: '#4b5563' },
  modeIconActive: { color: '#c084fc' },
  modeLabel: { color: '#4b5563', fontSize: 11, fontWeight: '600' },
  modeLabelActive: { color: '#c084fc' },
  quickRow: { paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: 'rgba(192,132,252,0.06)' },
  quickChip: {
    backgroundColor: 'rgba(192,132,252,0.07)', borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.15)', borderRadius: 16,
    paddingHorizontal: 10, paddingVertical: 5,
  },
  quickText: { color: '#9ca3af', fontSize: 11 },
  msgList: { padding: 16, paddingBottom: 8 },
  msgRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, marginBottom: 10 },
  msgRowUser: { flexDirection: 'row-reverse' },
  avatar: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: 'rgba(192,132,252,0.2)', alignItems: 'center', justifyContent: 'center',
    marginBottom: 2, flexShrink: 0,
  },
  avatarText: { fontSize: 13, color: '#c084fc' },
  bubble: { maxWidth: '78%', borderRadius: 16, padding: 12 },
  bubbleLove: {
    backgroundColor: 'rgba(192,132,252,0.1)', borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)', borderBottomLeftRadius: 4,
  },
  bubbleUser: { backgroundColor: 'rgba(192,132,252,0.22)', borderBottomRightRadius: 4 },
  bubbleError: {
    backgroundColor: 'rgba(248,113,113,0.08)', borderWidth: 1, borderColor: 'rgba(248,113,113,0.2)',
  },
  bubbleText: { color: '#e5e7eb', fontSize: 15, lineHeight: 23 },
  errorText: { color: '#f87171' },
  bubbleFooter: { flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: 6, marginTop: 4 },
  modeTag: { color: '#6b7280', fontSize: 9, fontStyle: 'italic' },
  timeText: { color: '#374151', fontSize: 10 },
  copiedText: { color: '#34d399', fontSize: 10 },
  typingRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 8, paddingHorizontal: 4 },
  typingBubble: {
    backgroundColor: 'rgba(192,132,252,0.1)', borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)', borderRadius: 16, borderBottomLeftRadius: 4,
    paddingHorizontal: 14, paddingVertical: 4,
  },
  actionBar: {
    paddingVertical: 6, borderTopWidth: 1, borderTopColor: 'rgba(192,132,252,0.08)',
    backgroundColor: '#0d0b18', paddingHorizontal: 8,
  },
  actionChip: {
    backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.15)', borderRadius: 14,
    paddingHorizontal: 10, paddingVertical: 5, minWidth: 38, alignItems: 'center',
  },
  actionChipActive: {
    backgroundColor: 'rgba(192,132,252,0.22)', borderColor: 'rgba(192,132,252,0.5)',
  },
  actionChipText: { fontSize: 16, textAlign: 'center' },
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 8,
    padding: 12, borderTopWidth: 1, borderTopColor: 'rgba(192,132,252,0.12)',
    backgroundColor: '#0d0b18',
  },
  input: {
    flex: 1, backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
    borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10,
    color: '#e5e7eb', fontSize: 15, maxHeight: 120,
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(192,132,252,0.22)', alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.4)',
  },
  sendBtnDisabled: { opacity: 0.35 },
  sendIcon: { color: '#c084fc', fontSize: 20, fontWeight: '700' },
  micBtn: {
    width: 44, height: 44, borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.06)', alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.12)',
  },
  micBtnActive: {
    backgroundColor: 'rgba(248,113,113,0.2)', borderColor: 'rgba(248,113,113,0.5)',
  },
  micIcon: { fontSize: 18 },
});
