import { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, ScrollView, TouchableOpacity, StyleSheet,
  RefreshControl, ActivityIndicator, Dimensions, Animated,
  LinearGradient, Pressable, Modal, TextInput,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { getInsightHistory } from '../../services/sync';
import { getContext, getOrchestratorInterventions, sendChat } from '../../services/api';
import * as Haptics from 'expo-haptics';

const { width, height } = Dimensions.get('window');
const CARD_WIDTH = width - 40;

const INSIGHT_ICONS = {
  doc: '📄',
  project: '🚀',
  fitness: '💪',
  calendar: '📅',
  email: '📧',
  alert: '⚠️',
  initiative: '♡',
  heartbeat: '💓',
};

const INSIGHT_COLORS = {
  doc: '#c084fc',
  project: '#38bdf8',
  fitness: '#4ade80',
  calendar: '#fbbf24',
  email: '#f87171',
  alert: '#f97316',
  initiative: '#ec4899',
  heartbeat: '#a78bfa',
};

export default function NotificationsScreen() {
  const [insights, setInsights] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [chatModalVisible, setChatModalVisible] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [sendingChat, setSendingChat] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [localInsights, ctx, intervs] = await Promise.all([
        Promise.resolve(getInsightHistory()),
        getContext(),
        getOrchestratorInterventions(),
      ]);
      
      setInsights(localInsights || []);
      setContext(ctx);
      setInterventions(intervs?.interventions || []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, []);

  const handleInsightPress = (insight) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setSelectedInsight(insight);
    setChatModalVisible(true);
  };

  const handleSendChat = async () => {
    if (!chatMessage.trim()) return;
    setSendingChat(true);
    try {
      await sendChat(`Tell me more about: ${selectedInsight.text}\n\n${chatMessage}`);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setChatModalVisible(false);
      setChatMessage('');
      setSelectedInsight(null);
    } catch (error) {
      console.error('Failed to send chat:', error);
    } finally {
      setSendingChat(false);
    }
  };

  const filteredInsights = insights.filter(insight => 
    selectedFilter === 'all' || insight.type === selectedFilter
  );

  const filters = [
    { key: 'all', label: 'All', icon: '🔮' },
    { key: 'doc', label: 'Docs', icon: '📄' },
    { key: 'project', label: 'Projects', icon: '🚀' },
    { key: 'fitness', label: 'Fitness', icon: '💪' },
    { key: 'initiative', label: 'LOVE', icon: '♡' },
  ];

  const InsightCard = ({ insight, index }) => {
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const scaleAnim = useRef(new Animated.Value(1)).current;
    
    useEffect(() => {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        delay: index * 50,
        useNativeDriver: true,
      }).start();
    }, []);

    const handlePressIn = () => {
      Animated.spring(scaleAnim, {
        toValue: 0.98,
        useNativeDriver: true,
      }).start();
    };

    const handlePressOut = () => {
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
      }).start();
    };

    return (
      <Pressable
        onPress={() => handleInsightPress(insight)}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
      >
        <Animated.View
          style={[
            styles.insightCard,
            { 
              opacity: fadeAnim, 
              transform: [{ scale: scaleAnim }],
              borderLeftColor: INSIGHT_COLORS[insight.type] || '#888'
            }
          ]}
        >
          <View style={styles.insightHeader}>
            <Text style={styles.insightIcon}>{INSIGHT_ICONS[insight.type] || '💡'}</Text>
            <View style={styles.insightMeta}>
              <Text style={styles.insightType}>{insight.type.toUpperCase()}</Text>
              <Text style={styles.insightTime}>
                {insight.timestamp ? new Date(insight.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now'}
              </Text>
            </View>
            <Text style={styles.tapIndicator}>→</Text>
          </View>
          <Text style={styles.insightText}>{insight.text}</Text>
          {insight.detail && (
            <Text style={styles.insightDetail}>{insight.detail}</Text>
          )}
        </Animated.View>
      </Pressable>
    );
  };

  const InterventionCard = ({ intervention, index }) => {
    return (
      <View style={[styles.interventionCard, { borderLeftColor: intervention.urgency === 'high' ? '#f87171' : '#38bdf8' }]}>
        <View style={styles.interventionHeader}>
          <Text style={styles.interventionIcon}>{intervention.urgency === 'high' ? '🔴' : '🔵'}</Text>
          <Text style={styles.interventionTitle}>{intervention.title}</Text>
        </View>
        <Text style={styles.interventionDesc}>{intervention.description}</Text>
        {intervention.suggested_action && (
          <TouchableOpacity style={styles.actionButton}>
            <Text style={styles.actionButtonText}>{intervention.suggested_action}</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>LOVE Insights</Text>
        <Text style={styles.headerSubtitle}>What's happening in your world</Text>
      </View>

      {/* Context Summary */}
      {context && (
        <LinearGradient
          colors={['#1a1a2e', '#2d2d44']}
          style={styles.contextBanner}
        >
          <View style={styles.contextRow}>
            <Text style={styles.contextLabel}>Active Project:</Text>
            <Text style={styles.contextValue}>{context.active_project || 'None'}</Text>
          </View>
          <View style={styles.contextRow}>
            <Text style={styles.contextLabel}>Mood:</Text>
            <Text style={styles.contextValue}>{context.mood_score ? `${Math.round(context.mood_score * 100)}%` : 'N/A'}</Text>
          </View>
          <View style={styles.contextRow}>
            <Text style={context.urgent_emails?.length > 0 ? styles.contextLabelUrgent : styles.contextLabel}>
              Urgent Emails:
            </Text>
            <Text style={styles.contextValue}>{context.urgent_emails?.length || 0}</Text>
          </View>
        </LinearGradient>
      )}

      {/* Filter Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterContainer}>
        {filters.map((filter) => (
          <TouchableOpacity
            key={filter.key}
            style={[
              styles.filterChip,
              selectedFilter === filter.key && styles.filterChipActive
            ]}
            onPress={() => setSelectedFilter(filter.key)}
          >
            <Text style={styles.filterIcon}>{filter.icon}</Text>
            <Text style={[
              styles.filterLabel,
              selectedFilter === filter.key && styles.filterLabelActive
            ]}>
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#c084fc" />
        }
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#c084fc" />
            <Text style={styles.loadingText}>Loading LOVE insights...</Text>
          </View>
        ) : (
          <>
            {/* Interventions */}
            {interventions.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Recommended Actions</Text>
                {interventions.map((intervention, index) => (
                  <InterventionCard key={index} intervention={intervention} index={index} />
                ))}
              </View>
            )}

            {/* Insights */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Recent Insights</Text>
              <Text style={styles.sectionSubtitle}>Tap any insight to discuss with LOVE</Text>
              {filteredInsights.length > 0 ? (
                filteredInsights.map((insight, index) => (
                  <InsightCard key={index} insight={insight} index={index} />
                ))
              ) : (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyIcon}>🔮</Text>
                  <Text style={styles.emptyText}>No insights yet</Text>
                  <Text style={styles.emptySubtext}>LOVE is watching and learning</Text>
                </View>
              )}
            </View>
          </>
        )}
      </ScrollView>

      {/* Chat Modal */}
      <Modal
        visible={chatModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setChatModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Discuss with LOVE</Text>
              <TouchableOpacity onPress={() => setChatModalVisible(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>
            
            {selectedInsight && (
              <View style={styles.modalInsight}>
                <Text style={styles.modalInsightIcon}>{INSIGHT_ICONS[selectedInsight.type] || '💡'}</Text>
                <Text style={styles.modalInsightText}>{selectedInsight.text}</Text>
              </View>
            )}

            <TextInput
              style={styles.chatInput}
              placeholder="Ask LOVE about this insight..."
              placeholderTextColor="#666"
              multiline
              value={chatMessage}
              onChangeText={setChatMessage}
              autoFocus
            />

            <TouchableOpacity
              style={[styles.sendButton, sendingChat && styles.sendButtonDisabled]}
              onPress={handleSendChat}
              disabled={sendingChat}
            >
              {sendingChat ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.sendButtonText}>Send to LOVE</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0f',
  },
  header: {
    padding: 20,
    paddingTop: 10,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#888',
    marginTop: 4,
  },
  contextBanner: {
    backgroundColor: '#1a1a2e',
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 16,
    borderRadius: 16,
  },
  contextRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  contextLabel: {
    fontSize: 13,
    color: '#888',
  },
  contextLabelUrgent: {
    fontSize: 13,
    color: '#f87171',
    fontWeight: '600',
  },
  contextValue: {
    fontSize: 13,
    color: '#fff',
    fontWeight: '600',
  },
  filterContainer: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    backgroundColor: '#1a1a2e',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#333',
  },
  filterChipActive: {
    backgroundColor: '#c084fc',
    borderColor: '#c084fc',
  },
  filterIcon: {
    fontSize: 16,
    marginRight: 6,
  },
  filterLabel: {
    fontSize: 13,
    color: '#888',
    fontWeight: '600',
  },
  filterLabelActive: {
    color: '#fff',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  loadingText: {
    color: '#888',
    marginTop: 12,
    fontSize: 14,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
    letterSpacing: -0.3,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
  },
  insightCard: {
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  insightHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  insightIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  insightMeta: {
    flex: 1,
  },
  insightType: {
    fontSize: 11,
    color: '#c084fc',
    fontWeight: '700',
    letterSpacing: 1,
  },
  insightTime: {
    fontSize: 11,
    color: '#666',
    marginTop: 2,
  },
  insightText: {
    fontSize: 15,
    color: '#fff',
    lineHeight: 22,
    fontWeight: '500',
  },
  insightDetail: {
    fontSize: 13,
    color: '#888',
    marginTop: 8,
    fontStyle: 'italic',
  },
  tapIndicator: {
    fontSize: 16,
    color: '#c084fc',
    opacity: 0.6,
  },
  interventionCard: {
    backgroundColor: '#1a1a2e',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  interventionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  interventionIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  interventionTitle: {
    fontSize: 15,
    color: '#fff',
    fontWeight: '700',
  },
  interventionDesc: {
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
    marginBottom: 12,
  },
  actionButton: {
    backgroundColor: '#c084fc',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
  emptyState: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyText: {
    fontSize: 16,
    color: '#fff',
    fontWeight: '600',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 13,
    color: '#666',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#1a1a2e',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  modalClose: {
    fontSize: 24,
    color: '#888',
    padding: 8,
  },
  modalInsight: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2d2d44',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  modalInsightIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  modalInsightText: {
    flex: 1,
    fontSize: 14,
    color: '#ccc',
    lineHeight: 20,
  },
  chatInput: {
    backgroundColor: '#2d2d44',
    color: '#fff',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    minHeight: 120,
    marginBottom: 16,
    textAlignVertical: 'top',
  },
  sendButton: {
    backgroundColor: '#c084fc',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#4a4a6a',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
});
