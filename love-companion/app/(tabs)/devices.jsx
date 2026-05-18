import { useState, useEffect } from 'react';
import { View, Text, ScrollView, RefreshControl, StyleSheet, TouchableOpacity, TextInput, Alert } from 'react-native';
import * as Haptics from 'expo-haptics';
import { getDevices, speakOnPC, pushEvent } from '../../services/api';

const DEVICE_ICONS = {
  phone: '📱',
  tablet: '⬛',
  laptop: '💻',
  desktop: '🖥',
  unknown: '◈',
};

const TYPE_COLORS = {
  phone: '#34d399',
  tablet: '#60a5fa',
  laptop: '#fbbf24',
  desktop: '#c084fc',
  unknown: '#6b7280',
};

function formatSeen(iso) {
  if (!iso) return 'never';
  try {
    const d = new Date(iso + 'Z');
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}min ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  } catch { return ''; }
}

function DeviceCard({ device, onSpeak, onPing }) {
  const online = device.online;
  const color = TYPE_COLORS[device.type] || TYPE_COLORS.unknown;
  const icon = DEVICE_ICONS[device.type] || DEVICE_ICONS.unknown;
  const batColor = !device.battery ? '#6b7280'
    : device.battery < 20 ? '#f87171'
    : device.battery < 50 ? '#fbbf24' : '#34d399';
  const isPC = device.type === 'desktop' || device.type === 'laptop';

  return (
    <View style={[styles.card, online && { borderColor: color + '35' }]}>
      <View style={[styles.cardAccent, { backgroundColor: online ? color : '#1f2937' }]} />
      <View style={styles.cardBody}>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleRow}>
            <Text style={styles.cardIcon}>{icon}</Text>
            <Text style={styles.cardName}>{device.name || device.id}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: online ? 'rgba(52,211,153,0.12)' : 'rgba(55,65,81,0.4)' }]}>
            <View style={[styles.dot, { backgroundColor: online ? '#34d399' : '#374151' }]} />
            <Text style={[styles.badgeText, { color: online ? '#34d399' : '#4b5563' }]}>
              {online ? 'online' : 'offline'}
            </Text>
          </View>
        </View>
        <View style={styles.cardMeta}>
          {device.os && <Text style={styles.metaTag}>{device.os}</Text>}
          {device.battery != null && (
            <Text style={[styles.metaTag, { color: batColor }]}>◱ {device.battery}%</Text>
          )}
          {device.network && <Text style={styles.metaTag}>◌ {device.network}</Text>}
          <Text style={styles.metaTag}>⏱ {formatSeen(device.last_seen)}</Text>
        </View>
        {online && (
          <View style={styles.cardActions}>
            <TouchableOpacity style={styles.actionBtn} onPress={() => onPing(device)}>
              <Text style={styles.actionBtnText}>◉ Ping</Text>
            </TouchableOpacity>
            {isPC && (
              <TouchableOpacity style={[styles.actionBtn, styles.actionBtnPrimary]} onPress={() => onSpeak(device)}>
                <Text style={[styles.actionBtnText, { color: '#c084fc' }]}>♪ Speak on PC</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </View>
    </View>
  );
}

export default function DevicesScreen() {
  const [devices, setDevices] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [speakText, setSpeakText] = useState('');
  const [speakLoading, setSpeakLoading] = useState(false);
  const [speakResult, setSpeakResult] = useState('');

  useEffect(() => { load(); const t = setInterval(load, 15000); return () => clearInterval(t); }, []);

  const load = async () => {
    try { const res = await getDevices(); setDevices(res.devices || []); } catch {}
  };

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const handleSpeak = async (device) => {
    if (!speakText.trim()) {
      Alert.alert('Speak on PC', 'Type a message in the box below, then tap Speak on PC on any online desktop device.');
      return;
    }
    setSpeakLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      await speakOnPC(speakText.trim());
      setSpeakResult('✓ Speaking on PC…');
      setSpeakText('');
      setTimeout(() => setSpeakResult(''), 3000);
    } catch { setSpeakResult('⚠ Could not reach PC'); }
    setSpeakLoading(false);
  };

  const handlePing = async (device) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await pushEvent('ping', 'Ping from phone', `Ping from phone to ${device.name || device.id}`, {});
    } catch {}
  };

  const onlineCount = devices.filter(d => d.online).length;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c084fc" />}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>CONNECTED DEVICES</Text>
        <View style={styles.countBadge}>
          <View style={[styles.dot, { backgroundColor: '#34d399' }]} />
          <Text style={styles.countText}>{onlineCount} / {devices.length} online</Text>
        </View>
      </View>

      {/* Speak on PC panel */}
      <View style={styles.speakBox}>
        <Text style={styles.speakLabel}>♪  SPEAK ON PC</Text>
        <View style={styles.speakRow}>
          <TextInput
            style={styles.speakInput}
            value={speakText}
            onChangeText={setSpeakText}
            placeholder="Type something for LOVE to say…"
            placeholderTextColor="#374151"
          />
          <TouchableOpacity
            style={[styles.speakBtn, (!speakText.trim() || speakLoading) && { opacity: 0.4 }]}
            onPress={() => handleSpeak()}
            disabled={!speakText.trim() || speakLoading}
          >
            <Text style={styles.speakBtnText}>{speakLoading ? '…' : '▶'}</Text>
          </TouchableOpacity>
        </View>
        {speakResult ? <Text style={styles.speakResult}>{speakResult}</Text> : null}
      </View>

      {/* Device list */}
      {devices.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No devices yet</Text>
          <Text style={styles.emptyHint}>This phone registers automatically. Run the office agent to add your laptop.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {devices.map(d => (
            <DeviceCard key={d.id} device={d} onSpeak={handleSpeak} onPing={handlePing} />
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: 'rgba(192,132,252,0.1)',
  },
  headerTitle: { color: '#c084fc', fontSize: 11, fontWeight: '700', letterSpacing: 1.5 },
  countBadge: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  countText: { color: '#34d399', fontSize: 11 },
  speakBox: {
    margin: 12, padding: 14,
    backgroundColor: 'rgba(192,132,252,0.06)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)', borderRadius: 12,
  },
  speakLabel: { color: '#c084fc', fontSize: 9, fontWeight: '700', letterSpacing: 1.5, marginBottom: 10 },
  speakRow: { flexDirection: 'row', gap: 8 },
  speakInput: {
    flex: 1, backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, color: '#e5e7eb', fontSize: 13,
  },
  speakBtn: {
    width: 40, borderRadius: 10, backgroundColor: 'rgba(192,132,252,0.2)',
    alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(192,132,252,0.3)',
  },
  speakBtnText: { color: '#c084fc', fontSize: 16 },
  speakResult: { color: '#34d399', fontSize: 11, marginTop: 8 },
  list: { padding: 12, gap: 10 },
  card: {
    flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)', borderRadius: 12, overflow: 'hidden',
  },
  cardAccent: { width: 3 },
  cardBody: { flex: 1, padding: 12 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  cardTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  cardIcon: { fontSize: 18 },
  cardName: { color: '#e5e7eb', fontSize: 14, fontWeight: '600' },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: 10 },
  badgeText: { fontSize: 10, fontWeight: '600' },
  cardMeta: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', marginBottom: 8 },
  metaTag: { color: '#6b7280', fontSize: 11 },
  cardActions: { flexDirection: 'row', gap: 8, marginTop: 4 },
  actionBtn: {
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)',
  },
  actionBtnPrimary: { backgroundColor: 'rgba(192,132,252,0.1)', borderColor: 'rgba(192,132,252,0.3)' },
  actionBtnText: { color: '#9ca3af', fontSize: 11, fontWeight: '600' },
  empty: { padding: 30, alignItems: 'center' },
  emptyText: { color: '#6b7280', fontSize: 15, marginBottom: 8 },
  emptyHint: { color: '#374151', fontSize: 12, textAlign: 'center', lineHeight: 18 },
});
