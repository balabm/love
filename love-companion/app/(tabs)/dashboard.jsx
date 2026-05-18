import { useState, useEffect, useRef } from 'react';
import {
  View, Text, ScrollView, RefreshControl, StyleSheet,
  TouchableOpacity, Animated, Pressable,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import {
  getLifescore, getDashboard, sendChat, getPrediction,
  getTasks, getBrief, getEmotionalSummary, getLifeSummary,
  systemAction, getSystemInfo, completeTask, remember,
} from '../../services/api';

const DOMAIN_META = {
  fitness:   { icon: '◎', color: '#34d399', label: 'Fitness' },
  finance:   { icon: '◇', color: '#fbbf24', label: 'Finance' },
  wellness:  { icon: '♡', color: '#f472b6', label: 'Wellness' },
  learning:  { icon: '◈', color: '#60a5fa', label: 'Learning' },
  work_life: { icon: '◉', color: '#a78bfa', label: 'Work/Life' },
  tasks:     { icon: '◻', color: '#fb923c', label: 'Tasks' },
  social:    { icon: '◌', color: '#38bdf8', label: 'Social' },
  sleep:     { icon: '◫', color: '#818cf8', label: 'Sleep' },
};

function ScoreRing({ score }) {
  const spinAnim = useRef(new Animated.Value(0)).current;
  const color = score >= 70 ? '#34d399' : score >= 40 ? '#fbbf24' : '#f87171';
  const state = score >= 70 ? 'THRIVING' : score >= 50 ? 'STABLE' : score >= 30 ? 'COASTING' : 'NEEDS CARE';
  return (
    <View style={styles.ringWrap}>
      <View style={[styles.ringOuter, { borderColor: color + '40' }]}>
        <View style={[styles.ringInner, { borderColor: color }]}>
          <Text style={[styles.ringScore, { color }]}>{score}</Text>
          <Text style={styles.ringLabel}>LIFE SCORE</Text>
        </View>
      </View>
      <Text style={[styles.stateChip, { color, borderColor: color + '40', backgroundColor: color + '12' }]}>{state}</Text>
    </View>
  );
}

function DomainCard({ domainKey, value }) {
  const meta = DOMAIN_META[domainKey] || { icon: '◈', color: '#6b7280', label: domainKey };
  const pct = typeof value === 'number' ? value : 50;
  const color = pct >= 70 ? meta.color : pct >= 40 ? '#fbbf24' : '#f87171';
  return (
    <View style={styles.domainCard}>
      <Text style={[styles.domainIcon, { color: meta.color }]}>{meta.icon}</Text>
      <Text style={styles.domainName}>{meta.label}</Text>
      <View style={styles.domainBar}>
        <View style={[styles.domainFill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
      <Text style={[styles.domainPct, { color }]}>{pct}</Text>
    </View>
  );
}

const QUICK_ACTIONS = [
  { label: 'Log workout', prompt: 'Log a workout session for today', icon: '◎' },
  { label: "Today's plan", prompt: "What's my plan for today?", icon: '◇' },
  { label: 'How am I doing?', prompt: 'Give me an honest life score review', icon: '♡' },
  { label: 'What to improve?', prompt: 'What single thing should I improve this week?', icon: '◈' },
];

export default function DashboardScreen() {
  const [lifescore, setLifescore] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [brief, setBrief] = useState(null);
  const [emotional, setEmotional] = useState(null);
  const [sysInfo, setSysInfo] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [actionResult, setActionResult] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [expandedTask, setExpandedTask] = useState(null);
  const [memories, setMemories] = useState([]);

  useEffect(() => { load(); const t = setInterval(load, 30000); return () => clearInterval(t); }, []);

  const load = async () => {
    try {
      const [ls, db, pr, tk, br, em, si] = await Promise.allSettled([
        getLifescore(), getDashboard(), getPrediction(),
        getTasks('active'), getBrief(), getEmotionalSummary(), getSystemInfo()
      ]);
      if (ls.status === 'fulfilled') setLifescore(ls.value);
      try { const m = await remember('recent events', 5); setMemories(m?.episodic || []); } catch {}
      if (db.status === 'fulfilled') setDashboard(db.value);
      if (pr.status === 'fulfilled') setPrediction(pr.value);
      if (tk.status === 'fulfilled') setTasks(tk.value?.tasks || []);
      if (br.status === 'fulfilled') setBrief(br.value);
      if (em.status === 'fulfilled') setEmotional(em.value);
      if (si.status === 'fulfilled') setSysInfo(si.value);
    } catch {}
  };

  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const toggleTask = async (task) => {
    if (task.done) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await completeTask(task.id);
      setTasks(prev => prev.map(t => t.id === task.id ? { ...t, done: true } : t));
    } catch {}
  };

  const runAction = async (prompt) => {
    if (actionLoading) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setActionLoading(true);
    setActionResult(null);
    try {
      const res = await sendChat(prompt, 'general');
      setActionResult(res.response);
    } catch { setActionResult('Could not reach LOVE server.'); }
    setActionLoading(false);
  };

  const doSystemAction = async (action, data = {}) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await systemAction(action, data);
    } catch {}
  };

  const stressColor = emotional?.current_stress > 70 ? '#f87171' : emotional?.current_stress > 40 ? '#fbbf24' : '#34d399';
  const stressLabel = emotional?.current_stress > 70 ? 'HIGH STRESS' : emotional?.current_stress > 40 ? 'MODERATE' : 'CALM';

  if (!lifescore) return (
    <View style={styles.center}>
      <Text style={styles.loadingText}>Loading your life…</Text>
    </View>
  );

  const breakdown = lifescore.breakdown || {};
  const recs = lifescore.recommendations || [];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c084fc" />}
    >
      {/* Hero: Score + Prediction + Emotional State */}
      <View style={styles.hero}>
        <ScoreRing score={lifescore.score || 0} />
        <View style={{ flex: 1, gap: 8 }}>
          {prediction?.prediction && (
            <View style={[styles.card, { borderColor: 'rgba(96,165,250,0.25)', backgroundColor: 'rgba(96,165,250,0.06)' }]}>
              <Text style={[styles.cardTitle, { color: '#60a5fa' }]}>◈ LOVE PREDICTS</Text>
              <Text style={[styles.cardText, { color: '#93c5fd' }]}>{prediction.prediction.prediction}</Text>
              <Text style={[styles.cardSub, { color: '#60a5fa' }]}>→ {prediction.prediction.suggested_action}</Text>
            </View>
          )}
          {emotional && (
            <View style={[styles.card, { borderColor: stressColor + '30', backgroundColor: stressColor + '08' }]}>
              <Text style={[styles.cardTitle, { color: stressColor }]}>♡ KARTHI'S STATE</Text>
              <Text style={[styles.cardText, { color: stressColor }]}>{stressLabel} — stress {emotional.current_stress}/100</Text>
              <Text style={styles.cardSub}>trend: {emotional.trend} · {emotional.dominant_mood || 'neutral'}</Text>
            </View>
          )}
          {recs.length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>LOVE SAYS</Text>
              {recs.slice(0, 2).map((r, i) => (
                <Text key={i} style={styles.cardText}>◉ {r}</Text>
              ))}
            </View>
          )}
        </View>
      </View>

      {/* Daily Brief */}
      {brief?.sections?.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>◈ TODAY'S BRIEF</Text>
          {brief.sections.map((s, i) => (
            <Text key={i} style={styles.briefLine}>{s}</Text>
          ))}
        </View>
      )}

      {/* Tasks */}
      <View style={styles.section}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <Text style={styles.sectionTitle}>◻ TASKS ({tasks.filter(t => !t.done).length})</Text>
          <TouchableOpacity onPress={() => runAction('What are my overdue tasks?')}>
            <Text style={{ color: '#c084fc', fontSize: 11 }}>See all →</Text>
          </TouchableOpacity>
        </View>
        {tasks.slice(0, 5).map(t => (
          <View key={t.id} style={[styles.taskRow, t.done && styles.taskDone]}>
            <TouchableOpacity onPress={() => toggleTask(t)}>
              <Text style={[styles.taskCheck, t.done && { color: '#34d399' }]}>{t.done ? '✓' : '○'}</Text>
            </TouchableOpacity>
            <View style={{ flex: 1 }}>
              <Text style={[styles.taskText, t.done && { textDecorationLine: 'line-through', color: '#4b5563' }]}>{t.text}</Text>
              {expandedTask === t.id && t.deadline && (
                <Text style={styles.taskMeta}>Due: {t.deadline} · from {t.source}</Text>
              )}
            </View>
            {t.deadline && <Text style={styles.taskDue}>{t.deadline.slice(5)}</Text>}
          </View>
        ))}
        {tasks.length === 0 && <Text style={styles.emptyText}>No active tasks. Ask LOVE to plan your day.</Text>}
      </View>

      {/* Domain breakdown */}
      {Object.keys(breakdown).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>LIFE DOMAINS</Text>
          {Object.entries(breakdown).map(([k, v]) => (
            <DomainCard key={k} domainKey={k} value={v} />
          ))}
        </View>
      )}

      {/* System Health */}
      {sysInfo?.success && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>◈ PC HEALTH</Text>
          <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
            <View style={styles.sysPill}>
              <Text style={styles.sysVal}>{sysInfo.cpu_percent}%</Text>
              <Text style={styles.sysLabel}>CPU</Text>
            </View>
            <View style={styles.sysPill}>
              <Text style={styles.sysVal}>{sysInfo.memory.percent}%</Text>
              <Text style={styles.sysLabel}>RAM</Text>
            </View>
            <View style={styles.sysPill}>
              <Text style={styles.sysVal}>{sysInfo.disk.percent}%</Text>
              <Text style={styles.sysLabel}>DISK</Text>
            </View>
          </View>
        </View>
      )}

      {/* Quick PC Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚡ QUICK PC ACTIONS</Text>
        <View style={styles.actionGrid}>
          {[
            { label: 'Screenshot', icon: '🖼', action: 'screenshot' },
            { label: 'Chrome', icon: '🌐', action: 'open', data: { target: 'chrome' } },
            { label: 'Play/Pause', icon: '▶', action: 'media', data: { action: 'play_pause' } },
            { label: 'Lock', icon: '🔒', action: 'lock' },
          ].map((a, i) => (
            <TouchableOpacity key={i} style={styles.actionBtn} onPress={() => doSystemAction(a.action, a.data || {})}>
              <Text style={styles.actionIcon}>{a.icon}</Text>
              <Text style={styles.actionLabel}>{a.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Quick chat actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>QUICK ACTIONS</Text>
        <View style={styles.actionGrid}>
          {QUICK_ACTIONS.map((a, i) => (
            <TouchableOpacity key={i} style={styles.actionBtn} onPress={() => runAction(a.prompt)}>
              <Text style={styles.actionIcon}>{a.icon}</Text>
              <Text style={styles.actionLabel}>{a.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {actionLoading && <Text style={styles.actionLoading}>LOVE is thinking…</Text>}
        {actionResult && (
          <View style={styles.actionResult}>
            <Text style={styles.actionResultText}>{actionResult}</Text>
          </View>
        )}
      </View>

      {/* Stats row */}
      <View style={styles.statsRow}>
        {dashboard?.tasks_pending != null && (
          <View style={styles.statPill}>
            <Text style={styles.statPillVal}>{dashboard.tasks_pending}</Text>
            <Text style={styles.statPillLabel}>pending tasks</Text>
          </View>
        )}
        {dashboard?.memories_count != null && (
          <View style={styles.statPill}>
            <Text style={styles.statPillVal}>{dashboard.memories_count}</Text>
            <Text style={styles.statPillLabel}>memories</Text>
          </View>
        )}
        {dashboard?.streak_days != null && (
          <View style={styles.statPill}>
            <Text style={[styles.statPillVal, { color: '#fbbf24' }]}>{dashboard.streak_days}d</Text>
            <Text style={styles.statPillLabel}>streak</Text>
          </View>
        )}
      </View>

      {/* Memories */}
      {memories.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✨ RECENT MEMORIES</Text>
          {memories.map((m, i) => (
            <View key={i} style={styles.memoryRow}>
              <Text style={styles.memoryIcon}>{m.emotion ? '♡' : '◈'}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.memoryText}>{m.summary}</Text>
                {m.detail && <Text style={styles.memoryDetail}>{m.detail}</Text>}
                <Text style={styles.memoryMeta}>{m.timestamp?.slice(0,10) || ''} · {m.location || ''}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0a0a0f' },
  loadingText: { color: '#6b7280', fontSize: 14 },
  hero: {
    padding: 16, borderBottomWidth: 1, borderBottomColor: 'rgba(192,132,252,0.1)',
    flexDirection: 'row', gap: 14, alignItems: 'flex-start',
  },
  card: {
    borderWidth: 1, borderRadius: 10, padding: 10, gap: 3,
    backgroundColor: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.08)',
  },
  cardTitle: { color: '#c084fc', fontSize: 9, fontWeight: '700', letterSpacing: 1 },
  cardText: { color: '#d1d5db', fontSize: 12, lineHeight: 17 },
  cardSub: { color: '#6b7280', fontSize: 10 },
  section: {
    margin: 12, padding: 14,
    backgroundColor: 'rgba(255,255,255,0.02)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.06)', borderRadius: 12,
  },
  sectionTitle: { color: '#c084fc', fontSize: 9, fontWeight: '700', letterSpacing: 1.5, marginBottom: 10 },
  briefLine: { color: '#9ca3af', fontSize: 12, lineHeight: 20, marginBottom: 2 },
  taskRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, paddingVertical: 8, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.04)' },
  taskDone: { opacity: 0.5 },
  taskCheck: { color: '#c084fc', fontSize: 14, marginTop: 1 },
  taskText: { color: '#d1d5db', fontSize: 13, flex: 1 },
  taskMeta: { color: '#6b7280', fontSize: 10, marginTop: 2 },
  taskDue: { color: '#fbbf24', fontSize: 10 },
  emptyText: { color: '#4b5563', fontSize: 12, fontStyle: 'italic', textAlign: 'center', paddingVertical: 12 },
  ringWrap: { alignItems: 'center', gap: 8 },
  ringOuter: { width: 90, height: 90, borderRadius: 45, borderWidth: 5, alignItems: 'center', justifyContent: 'center' },
  ringInner: { width: 74, height: 74, borderRadius: 37, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
  ringScore: { fontSize: 26, fontWeight: '800' },
  ringLabel: { color: '#4b5563', fontSize: 7, fontWeight: '700', letterSpacing: 1 },
  stateChip: { fontSize: 8, fontWeight: '700', letterSpacing: 1.5, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 8, borderWidth: 1 },
  domainCard: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 },
  domainIcon: { fontSize: 13, width: 16, textAlign: 'center' },
  domainName: { color: '#9ca3af', fontSize: 11, width: 68 },
  domainBar: { flex: 1, height: 5, backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 3 },
  domainFill: { height: 5, borderRadius: 3 },
  domainPct: { fontSize: 11, fontWeight: '700', width: 26, textAlign: 'right' },
  sysPill: {
    flex: 1, alignItems: 'center', paddingVertical: 10,
    backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)', borderRadius: 8,
  },
  sysVal: { color: '#c084fc', fontSize: 18, fontWeight: '700' },
  sysLabel: { color: '#4b5563', fontSize: 9, fontWeight: '600', marginTop: 2 },
  actionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  actionBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
    backgroundColor: 'rgba(192,132,252,0.08)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
  },
  actionIcon: { color: '#c084fc', fontSize: 12 },
  actionLabel: { color: '#d1d5db', fontSize: 12 },
  actionLoading: { color: '#6b7280', fontSize: 12, marginTop: 10, textAlign: 'center' },
  actionResult: { marginTop: 10, padding: 12, backgroundColor: 'rgba(192,132,252,0.07)', borderRadius: 10, borderWidth: 1, borderColor: 'rgba(192,132,252,0.15)' },
  actionResultText: { color: '#d1d5db', fontSize: 13, lineHeight: 20 },
  statsRow: { flexDirection: 'row', justifyContent: 'center', gap: 12, marginHorizontal: 12, marginBottom: 4 },
  statPill: {
    flex: 1, alignItems: 'center', paddingVertical: 12,
    backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)', borderRadius: 10,
  },
  statPillVal: { color: '#c084fc', fontSize: 20, fontWeight: '800' },
  statPillLabel: { color: '#4b5563', fontSize: 9, fontWeight: '600', letterSpacing: 0.5, marginTop: 2 },
  memoryRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, paddingVertical: 8, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.04)' },
  memoryIcon: { fontSize: 13, color: '#c084fc', marginTop: 2 },
  memoryText: { color: '#d1d5db', fontSize: 12, lineHeight: 18 },
  memoryDetail: { color: '#6b7280', fontSize: 11, lineHeight: 16, marginTop: 2 },
  memoryMeta: { color: '#4b5563', fontSize: 9, marginTop: 3 },
});
