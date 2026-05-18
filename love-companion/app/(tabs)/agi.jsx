import { useState, useEffect } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  ActivityIndicator, RefreshControl, Modal,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import {
  getAutonomousGoals, generateAutonomousGoals, getPredictions,
  getPendingApprovals, approveAction, rejectAction,
  getMetaCognitiveSummary, getSelfImprovementSuggestions,
  getHolisticView, anticipateNeeds,
} from '../../services/api';

export default function AGIScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [goals, setGoals] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [metaSummary, setMetaSummary] = useState(null);
  const [improvements, setImprovements] = useState([]);
  const [holisticView, setHolisticView] = useState(null);
  const [selectedTab, setSelectedTab] = useState('goals');

  const tabs = [
    { key: 'goals', label: 'Goals', icon: '🎯' },
    { key: 'predictions', label: 'Predictions', icon: '🔮' },
    { key: 'approvals', label: 'Approvals', icon: '✓' },
    { key: 'meta', label: 'Meta', icon: '🧠' },
    { key: 'holistic', label: 'Holistic', icon: '🌐' },
  ];

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadGoals(),
        loadPredictions(),
        loadApprovals(),
        loadMetaSummary(),
        loadImprovements(),
        loadHolisticView(),
      ]);
    } catch (e) {
      console.error('Error loading AGI data:', e);
    }
    setLoading(false);
  };

  const loadGoals = async () => {
    try {
      const data = await getAutonomousGoals();
      setGoals(data.goals || []);
    } catch (e) {
      console.error('Error loading goals:', e);
    }
  };

  const loadPredictions = async () => {
    try {
      const data = await getPredictions();
      setPredictions(data.predictions || []);
    } catch (e) {
      console.error('Error loading predictions:', e);
    }
  };

  const loadApprovals = async () => {
    try {
      const data = await getPendingApprovals();
      setApprovals(data.approvals || []);
    } catch (e) {
      console.error('Error loading approvals:', e);
    }
  };

  const loadMetaSummary = async () => {
    try {
      const data = await getMetaCognitiveSummary();
      setMetaSummary(data);
    } catch (e) {
      console.error('Error loading meta summary:', e);
    }
  };

  const loadImprovements = async () => {
    try {
      const data = await getSelfImprovementSuggestions();
      setImprovements(data.suggestions || []);
    } catch (e) {
      console.error('Error loading improvements:', e);
    }
  };

  const loadHolisticView = async () => {
    try {
      const data = await getHolisticView();
      setHolisticView(data);
    } catch (e) {
      console.error('Error loading holistic view:', e);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadAllData();
    setRefreshing(false);
  };

  const handleGenerateGoals = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      await generateAutonomousGoals();
      await loadGoals();
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e) {
      console.error('Error generating goals:', e);
    }
  };

  const handleAnticipateNeeds = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const data = await anticipateNeeds();
      setPredictions(data.predictions || []);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e) {
      console.error('Error anticipating needs:', e);
    }
  };

  const handleApprove = async (actionId) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await approveAction(actionId);
      await loadApprovals();
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e) {
      console.error('Error approving action:', e);
    }
  };

  const handleReject = async (actionId) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      await rejectAction(actionId);
      await loadApprovals();
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e) {
      console.error('Error rejecting action:', e);
    }
  };

  const renderGoals = () => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Autonomous Goals</Text>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleGenerateGoals}
        >
          <Text style={styles.actionButtonText}>Generate</Text>
        </TouchableOpacity>
      </View>
      {goals.length === 0 ? (
        <Text style={styles.emptyText}>No active goals. Tap "Generate" to create autonomous goals.</Text>
      ) : (
        goals.map((goal, i) => (
          <View key={i} style={styles.card}>
            <Text style={styles.cardTitle}>{goal.title}</Text>
            <Text style={styles.cardDescription}>{goal.description}</Text>
            <View style={styles.cardFooter}>
              <Text style={[styles.priorityBadge, { backgroundColor: getPriorityColor(goal.priority) }]}>
                {goal.priority}
              </Text>
              <Text style={styles.statusText}>{goal.status}</Text>
            </View>
          </View>
        ))
      )}
    </View>
  );

  const renderPredictions = () => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Predictions</Text>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleAnticipateNeeds}
        >
          <Text style={styles.actionButtonText}>Anticipate Needs</Text>
        </TouchableOpacity>
      </View>
      {predictions.length === 0 ? (
        <Text style={styles.emptyText}>No predictions. Tap "Anticipate Needs" to generate predictions.</Text>
      ) : (
        predictions.map((pred, i) => (
          <View key={i} style={styles.card}>
            <Text style={styles.cardTitle}>{pred.description}</Text>
            <Text style={styles.cardDescription}>Confidence: {(pred.confidence * 100).toFixed(0)}%</Text>
            <View style={styles.cardFooter}>
              <Text style={styles.statusText}>{pred.timeframe}</Text>
              <Text style={styles.impactBadge}>{pred.impact}</Text>
            </View>
          </View>
        ))
      )}
    </View>
  );

  const renderApprovals = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Pending Approvals</Text>
      {approvals.length === 0 ? (
        <Text style={styles.emptyText}>No actions pending approval.</Text>
      ) : (
        approvals.map((approval, i) => (
          <View key={i} style={styles.card}>
            <Text style={styles.cardTitle}>{proposal.action}</Text>
            <Text style={styles.cardDescription}>{proposal.description}</Text>
            <View style={styles.cardFooter}>
              <Text style={[styles.priorityBadge, { backgroundColor: getPriorityColor(proposal.risk_level) }]}>
                {proposal.risk_level}
              </Text>
            </View>
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.approveButton, styles.rejectButton]}
                onPress={() => handleReject(approval.id)}
              >
                <Text style={styles.buttonText}>Reject</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.approveButton, styles.acceptButton]}
                onPress={() => handleApprove(approval.id)}
              >
                <Text style={styles.buttonText}>Approve</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}
    </View>
  );

  const renderMeta = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Meta-Cognition</Text>
      {metaSummary ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Cognitive State: {metaSummary.cognitive_state}</Text>
          <Text style={styles.cardDescription}>Active Processes: {metaSummary.active_processes}</Text>
          <Text style={styles.cardDescription}>
            Confidence: {metaSummary.latest_self_assessment?.overall_confidence?.toFixed(2) || 'N/A'}
          </Text>
          <Text style={styles.cardDescription}>
            Cognitive Load: {metaSummary.latest_self_assessment?.cognitive_load?.toFixed(2) || 'N/A'}
          </Text>
        </View>
      ) : (
        <Text style={styles.emptyText}>No meta-cognitive data available.</Text>
      )}
      
      <Text style={[styles.sectionTitle, { marginTop: 20 }]}>Self-Improvement Suggestions</Text>
      {improvements.length === 0 ? (
        <Text style={styles.emptyText}>No improvement suggestions available.</Text>
      ) : (
        improvements.map((imp, i) => (
          <View key={i} style={styles.card}>
            <Text style={styles.cardTitle}>{imp.suggestion}</Text>
            <Text style={styles.cardDescription}>{imp.action}</Text>
            <View style={styles.cardFooter}>
              <Text style={[styles.priorityBadge, { backgroundColor: getPriorityColor(imp.priority) }]}>
                {imp.priority}
              </Text>
            </View>
          </View>
        ))
      )}
    </View>
  );

  const renderHolistic = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Holistic View</Text>
      {holisticView ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Domain Insights</Text>
          {Object.entries(holisticView.domains || {}).map(([domain, data]) => (
            <View key={domain} style={styles.domainItem}>
              <Text style={styles.domainName}>{domain}</Text>
              <Text style={styles.domainValue}>{JSON.stringify(data, null, 2)}</Text>
            </View>
          ))}
        </View>
      ) : (
        <Text style={styles.emptyText}>No holistic view data available.</Text>
      )}
    </View>
  );

  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'rgba(248,113,113,0.3)',
      high: 'rgba(245,158,11,0.3)',
      medium: 'rgba(192,132,252,0.3)',
      low: 'rgba(52,211,153,0.3)',
    };
    return colors[priority] || colors.medium;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#c084fc" />
        <Text style={styles.loadingText}>Loading AGI systems...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Tab selector */}
      <View style={styles.tabBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 4 }}>
          {tabs.map(tab => (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tab, selectedTab === tab.key && styles.tabActive]}
              onPress={() => {
                setSelectedTab(tab.key);
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              }}
            >
              <Text style={styles.tabIcon}>{tab.icon}</Text>
              <Text style={[styles.tabLabel, selectedTab === tab.key && styles.tabLabelActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c084fc" />
        }
      >
        {selectedTab === 'goals' && renderGoals()}
        {selectedTab === 'predictions' && renderPredictions()}
        {selectedTab === 'approvals' && renderApprovals()}
        {selectedTab === 'meta' && renderMeta()}
        {selectedTab === 'holistic' && renderHolistic()}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0f' },
  loadingContainer: {
    flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0a0a0f',
  },
  loadingText: { color: '#9ca3af', marginTop: 12, fontSize: 14 },
  tabBar: {
    flexDirection: 'row', paddingVertical: 12, paddingHorizontal: 8,
    borderBottomWidth: 1, borderBottomColor: 'rgba(192,132,252,0.12)',
    backgroundColor: '#0d0b18',
  },
  tab: {
    flexDirection: 'column', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 8,
    borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)', minWidth: 70,
  },
  tabActive: {
    backgroundColor: 'rgba(192,132,252,0.18)', borderColor: 'rgba(192,132,252,0.4)',
  },
  tabIcon: { fontSize: 18, marginBottom: 4 },
  tabLabel: { color: '#6b7280', fontSize: 11, fontWeight: '600' },
  tabLabelActive: { color: '#c084fc' },
  content: { flex: 1 },
  section: { padding: 16 },
  sectionHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: { color: '#e5e7eb', fontSize: 18, fontWeight: '700' },
  actionButton: {
    backgroundColor: 'rgba(192,132,252,0.22)', paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 8, borderWidth: 1, borderColor: 'rgba(192,132,252,0.4)',
  },
  actionButtonText: { color: '#c084fc', fontSize: 12, fontWeight: '600' },
  card: {
    backgroundColor: 'rgba(255,255,255,0.04)', borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.15)', borderRadius: 12, padding: 14,
    marginBottom: 10,
  },
  cardTitle: { color: '#e5e7eb', fontSize: 15, fontWeight: '600', marginBottom: 6 },
  cardDescription: { color: '#9ca3af', fontSize: 13, lineHeight: 20, marginBottom: 8 },
  cardFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  priorityBadge: {
    paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, fontSize: 11,
    fontWeight: '600', textTransform: 'uppercase',
  },
  statusText: { color: '#6b7280', fontSize: 11 },
  impactBadge: {
    backgroundColor: 'rgba(192,132,252,0.2)', paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 6, fontSize: 11, fontWeight: '600', color: '#c084fc',
  },
  actionButtons: { flexDirection: 'row', gap: 8, marginTop: 10 },
  approveButton: { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
  rejectButton: { backgroundColor: 'rgba(248,113,113,0.2)', borderWidth: 1, borderColor: 'rgba(248,113,113,0.4)' },
  acceptButton: { backgroundColor: 'rgba(52,211,153,0.2)', borderWidth: 1, borderColor: 'rgba(52,211,153,0.4)' },
  buttonText: { fontSize: 13, fontWeight: '600' },
  emptyText: { color: '#6b7280', fontSize: 13, textAlign: 'center', paddingVertical: 20 },
  domainItem: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.08)' },
  domainName: { color: '#c084fc', fontSize: 14, fontWeight: '600', marginBottom: 4 },
  domainValue: { color: '#9ca3af', fontSize: 12, fontFamily: 'monospace' },
});
