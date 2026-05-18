import { useState, useEffect, useRef } from 'react';
import { View, Text, ScrollView, TouchableOpacity, RefreshControl, StyleSheet, Animated } from 'react-native';
import { getContext, getDashboard, getTasks, getPrediction, getEmotionalSummary } from '../../services/api';

function PulseDot({ color = '#34d399' }) {
  const scale = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(scale, { toValue: 1.6, duration: 900, useNativeDriver: true }),
        Animated.timing(scale, { toValue: 1, duration: 900, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return (
    <View style={{ width: 12, height: 12, alignItems: 'center', justifyContent: 'center' }}>
      <Animated.View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: color, transform: [{ scale }] }} />
    </View>
  );
}

function StatCard({ icon, label, value, sub, accent, urgent }) {
  const bg = urgent ? 'rgba(248,113,113,0.08)' : 'rgba(255,255,255,0.03)';
  const border = urgent ? 'rgba(248,113,113,0.25)' : 'rgba(255,255,255,0.07)';
  return (
    <View style={[styles.statCard, { backgroundColor: bg, borderColor: border }]}>
      <Text style={[styles.statIcon, { color: accent || '#c084fc' }]}>{icon}</Text>
      <Text style={[styles.statValue, { color: urgent ? '#f87171' : '#e5e7eb' }]} numberOfLines={1}>{value ?? '—'}</Text>
      {sub ? <Text style={styles.statSub} numberOfLines={1}>{sub}</Text> : null}
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function InfoRow({ icon, label, value, highlight, accent }) {
  if (value === null || value === undefined || value === '') return null;
  return (
    <View style={[styles.row, highlight && styles.rowHighlight]}>
      <Text style={[styles.rowIcon, accent && { color: accent }]}>{icon}</Text>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={[styles.rowValue, highlight && styles.rowValueHighlight]} numberOfLines={2}>{String(value)}</Text>
    </View>
  );
}

function Section({ title, children, accent }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.sectionTitle, accent && { color: accent }]}>{title}</Text>
      {children}
    </View>
  );
}

export default function ContextScreen() {
  const [ctx, setCtx] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [emotional, setEmotional] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('');
  const [error, setError] = useState(false);

  useEffect(() => {
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  const load = async () => {
    try {
      const [ctxData, tk, pr, em] = await Promise.allSettled([
        getContext(), getTasks('today'), getPrediction(), getEmotionalSummary()
      ]);
      if (ctxData.status === 'fulfilled') { setCtx(ctxData.value); setError(false); }
      if (tk.status === 'fulfilled') setTasks(tk.value?.tasks || []);
      if (pr.status === 'fulfilled') setPrediction(pr.value);
      if (em.status === 'fulfilled') setEmotional(em.value);
      setLastUpdate(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch { setError(true); }
  };

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (!ctx && !error) return (
    <View style={styles.center}>
      <PulseDot color="#c084fc" />
      <Text style={[styles.loadingText, { marginTop: 12 }]}>Connecting to LOVE…</Text>
    </View>
  );

  if (error && !ctx) return (
    <View style={styles.center}>
      <Text style={{ fontSize: 24, marginBottom: 12 }}>⚠</Text>
      <Text style={styles.loadingText}>Server unreachable</Text>
      <TouchableOpacity onPress={load} style={styles.retryBtn}>
        <Text style={styles.retryText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );

  const bat = ctx.battery;
  const batColor = !bat ? '#6b7280' : bat < 20 ? '#f87171' : bat < 50 ? '#fbbf24' : '#34d399';
  const phoneBat = ctx.phone_battery;
  const phoneBatColor = !phoneBat ? '#6b7280' : phoneBat < 20 ? '#f87171' : phoneBat < 50 ? '#fbbf24' : '#34d399';
  const inMeeting = ctx.is_in_meeting;
  const nextEvent = ctx.next_event;
  const alerts = ctx.alerts || [];
  const emails = ctx.email_count ?? ctx.unread_emails;
  const location = ctx.location_label || ctx.location;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c084fc" />}
    >
      {/* Live banner */}
      <View style={[styles.banner, inMeeting && styles.bannerMeeting]}>
        <PulseDot color={inMeeting ? '#f87171' : error ? '#f59e0b' : '#34d399'} />
        <Text style={styles.bannerText}>{ctx.summary || 'LOVE is watching…'}</Text>
        {lastUpdate ? <Text style={styles.updated}>{lastUpdate}</Text> : null}
      </View>

      {/* Alert strip */}
      {alerts.length > 0 && (
        <View style={styles.alertStrip}>
          {alerts.map((a, i) => (
            <View key={i} style={styles.alertItem}>
              <Text style={styles.alertIcon}>⚠</Text>
              <Text style={styles.alertText}>{a}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Stat grid */}
      <View style={styles.grid}>
        {bat != null && (
          <StatCard icon={ctx.battery_charging ? '⚡' : '▣'} label="PC BATTERY" value={`${bat.toFixed(0)}%`}
            sub={ctx.battery_charging ? 'charging' : null} accent={batColor} urgent={bat < 15} />
        )}
        {phoneBat != null && (
          <StatCard icon="◱" label="PHONE" value={`${phoneBat}%`} accent={phoneBatColor} urgent={phoneBat < 15} />
        )}
        {emails != null && (
          <StatCard icon="◻" label="UNREAD" value={emails} sub="emails" accent="#60a5fa" urgent={emails > 10} />
        )}
        {ctx.cpu_percent != null && (
          <StatCard icon="◈" label="CPU" value={`${ctx.cpu_percent.toFixed(0)}%`}
            accent={ctx.cpu_percent > 80 ? '#f87171' : '#34d399'} urgent={ctx.cpu_percent > 90} />
        )}
        {ctx.ram_percent != null && (
          <StatCard icon="◫" label="RAM" value={`${ctx.ram_percent.toFixed(0)}%`}
            accent={ctx.ram_percent > 85 ? '#f87171' : '#a78bfa'} />
        )}
        {location && (
          <StatCard icon="◎" label="LOCATION" value={location} accent="#34d399" />
        )}
      </View>

      {/* LOVE's prediction */}
      {prediction?.prediction && (
        <Section title="◈ LOVE PREDICTS" accent="#60a5fa">
          <InfoRow icon="◈" label="Next" value={prediction.prediction.prediction} highlight accent="#60a5fa" />
          <InfoRow icon="→" label="Action" value={prediction.prediction.suggested_action} />
        </Section>
      )}

      {/* Emotional state */}
      {emotional && (
        <Section title="♡ KARTHI'S STATE" accent={emotional.current_stress > 70 ? '#f87171' : '#34d399'}>
          <InfoRow icon="♡" label="Mood" value={emotional.dominant_mood || 'neutral'} highlight={emotional.current_stress > 70} accent={emotional.current_stress > 70 ? '#f87171' : '#34d399'} />
          <InfoRow icon="◈" label="Stress" value={`${emotional.current_stress}/100 (${emotional.trend})`} highlight={emotional.current_stress > 70} accent={emotional.current_stress > 70 ? '#f87171' : '#fbbf24'} />
          {emotional.days_tracked > 1 && <InfoRow icon="◷" label="Tracked" value={`${emotional.days_tracked} days`} />}
        </Section>
      )}

      {/* Today's tasks */}
      {tasks.length > 0 && (
        <Section title="◻ TODAY'S TASKS">
          {tasks.slice(0, 5).map((t, i) => (
            <InfoRow key={t.id || i} icon={t.done ? '✓' : '○'} label={t.done ? 'Done' : 'Todo'} value={t.text} highlight={!t.done} accent={t.deadline ? '#fbbf24' : undefined} />
          ))}
        </Section>
      )}

      {/* Meeting / calendar */}
      {inMeeting ? (
        <Section title="IN MEETING" accent="#f87171">
          <InfoRow icon="🔴" label="Status" value="Currently in a meeting" highlight accent="#f87171" />
          {ctx.current_meeting?.title && <InfoRow icon="◫" label="Meeting" value={ctx.current_meeting.title} />}
        </Section>
      ) : nextEvent ? (
        <Section title="NEXT UP">
          <InfoRow icon="◷" label="Event" value={nextEvent.title} highlight={nextEvent.minutes_away <= 10} />
          <InfoRow icon="⏱" label="In" value={`${nextEvent.minutes_away} min`} highlight={nextEvent.minutes_away <= 5} accent="#fbbf24" />
          {nextEvent.time && <InfoRow icon="◉" label="At" value={nextEvent.time} />}
        </Section>
      ) : null}

      {/* PC awareness */}
      <Section title="PC RIGHT NOW">
        <InfoRow icon="◷" label="Time" value={`${ctx.local_time || ''} · ${ctx.time_of_day || ''}`} />
        {ctx.activity && ctx.activity !== 'idle' && <InfoRow icon="◉" label="Activity" value={ctx.activity} highlight />}
        {ctx.active_window && <InfoRow icon="▣" label="Window" value={ctx.active_window} />}
        {ctx.running_apps?.length > 0 && <InfoRow icon="◈" label="Apps" value={ctx.running_apps.slice(0, 4).join(', ')} />}
        {ctx.network_status && <InfoRow icon="◌" label="Network" value={ctx.network_status} />}
      </Section>

      {/* Recent emails */}
      {ctx.recent_emails?.length > 0 && (
        <Section title="RECENT EMAILS">
          {ctx.recent_emails.slice(0, 3).map((e, i) => (
            <InfoRow key={i} icon="◻" label={e.from || 'Email'} value={e.subject || e.title} />
          ))}
        </Section>
      )}

      {/* Today's events */}
      {ctx.today_events?.length > 0 && (
        <Section title="TODAY'S CALENDAR">
          {ctx.today_events.slice(0, 4).map((e, i) => (
            <InfoRow key={i} icon="◫" label={e.time || ''} value={e.title} highlight={e.minutes_away <= 10} />
          ))}
        </Section>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a0a0f' },
  loadingText: { color: '#6b7280', fontSize: 14 },
  retryBtn: { marginTop: 16, paddingHorizontal: 24, paddingVertical: 10, borderRadius: 20, backgroundColor: 'rgba(192,132,252,0.15)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.3)' },
  retryText: { color: '#c084fc', fontWeight: '600' },
  banner: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 10,
    margin: 12, padding: 14,
    backgroundColor: 'rgba(192,132,252,0.07)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)', borderRadius: 12,
  },
  bannerMeeting: { backgroundColor: 'rgba(248,113,113,0.08)', borderColor: 'rgba(248,113,113,0.3)' },
  bannerText: { color: '#d1d5db', fontSize: 13, lineHeight: 21, flex: 1 },
  updated: { color: '#374151', fontSize: 9, marginTop: 2 },
  alertStrip: { marginHorizontal: 12, marginBottom: 4, gap: 4 },
  alertItem: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', backgroundColor: 'rgba(248,113,113,0.08)', borderWidth: 1, borderColor: 'rgba(248,113,113,0.2)', borderRadius: 8, padding: 10 },
  alertIcon: { color: '#f87171', fontSize: 12, marginTop: 1 },
  alertText: { color: '#fca5a5', fontSize: 12, flex: 1, lineHeight: 18 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 8, gap: 8, marginBottom: 8 },
  statCard: {
    width: '30%', flexGrow: 1, borderRadius: 10, padding: 12,
    borderWidth: 1, alignItems: 'center', gap: 2,
  },
  statIcon: { fontSize: 16, marginBottom: 2 },
  statValue: { fontSize: 16, fontWeight: '700' },
  statSub: { color: '#6b7280', fontSize: 9 },
  statLabel: { color: '#4b5563', fontSize: 8, fontWeight: '700', letterSpacing: 1, marginTop: 2 },
  section: {
    marginHorizontal: 12, marginBottom: 10,
    backgroundColor: 'rgba(255,255,255,0.02)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)', borderRadius: 10, overflow: 'hidden',
  },
  sectionTitle: { fontSize: 9, fontWeight: '700', letterSpacing: 1.5, color: '#c084fc', paddingHorizontal: 14, paddingTop: 10, paddingBottom: 4 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingHorizontal: 14, paddingVertical: 9, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.04)' },
  rowHighlight: { backgroundColor: 'rgba(245,158,11,0.06)', borderLeftWidth: 2, borderLeftColor: '#f59e0b' },
  rowIcon: { fontSize: 12, color: '#c084fc', width: 16, textAlign: 'center' },
  rowLabel: { color: '#6b7280', fontSize: 11, minWidth: 60 },
  rowValue: { color: '#e5e7eb', fontSize: 12, flex: 1, textAlign: 'right' },
  rowValueHighlight: { color: '#fbbf24' },
});
