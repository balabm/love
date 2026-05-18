import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getCalendarInsights } from '../services/api';

export default function CalendarScreen() {
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      const data = await getCalendarInsights();
      setCalendarData(data);
    } catch (error) {
      console.error('[Calendar] Error loading:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCalendarData();
  }, []);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#c084fc" />
      </View>
    );
  }

  const insights = calendarData?.insights || [];
  const suggestions = calendarData?.suggestions || [];
  const freeSlots = calendarData?.free_slots || [];
  const meetingCount = calendarData?.meeting_count || 0;
  const totalHours = calendarData?.total_meeting_hours || 0;

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['rgba(192,132,252,0.1)', 'rgba(192,132,252,0.05)', 'transparent']}
        style={styles.header}
      >
        <Text style={styles.title}>Calendar Insights</Text>
        <Text style={styles.subtitle}>
          Smart suggestions for your schedule
        </Text>
      </LinearGradient>

      {/* Meeting Summary */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Today's Schedule</Text>
        <View style={styles.summaryCard}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>{meetingCount}</Text>
            <Text style={styles.summaryLabel}>Meetings</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={styles.summaryValue}>{totalHours}h</Text>
            <Text style={styles.summaryLabel}>Total Time</Text>
          </View>
        </View>
      </View>

      {/* Free Time Slots */}
      {freeSlots.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Free Time Opportunities</Text>
          {freeSlots.map((slot, index) => (
            <View key={index} style={styles.freeSlotCard}>
              <Text style={styles.freeSlotEmoji}>⏰</Text>
              <Text style={styles.freeSlotText}>{slot}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Insights</Text>
          {insights.map((insight, index) => (
            <View key={index} style={styles.insightCard}>
              <Text style={styles.insightEmoji}>💡</Text>
              <Text style={styles.insightText}>{insight}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Smart Suggestions</Text>
          {suggestions.map((suggestion, index) => (
            <View key={index} style={styles.suggestionCard}>
              <Text style={styles.suggestionEmoji}>✨</Text>
              <Text style={styles.suggestionText}>{suggestion}</Text>
            </View>
          ))}
        </View>
      )}

      <TouchableOpacity style={styles.refreshButton} onPress={loadCalendarData}>
        <Text style={styles.refreshButtonText}>Refresh</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0f',
  },
  header: {
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#c084fc',
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#e5e7eb',
    marginBottom: 16,
    letterSpacing: 1,
  },
  summaryCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(192,132,252,0.08)',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#c084fc',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  summaryDivider: {
    width: 1,
    backgroundColor: 'rgba(192,132,252,0.2)',
  },
  freeSlotCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(16,185,129,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.3)',
  },
  freeSlotEmoji: {
    fontSize: 20,
    marginRight: 12,
  },
  freeSlotText: {
    flex: 1,
    fontSize: 14,
    color: '#e5e7eb',
  },
  insightCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(192,132,252,0.05)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  insightEmoji: {
    fontSize: 20,
    marginRight: 12,
  },
  insightText: {
    flex: 1,
    fontSize: 14,
    color: '#9ca3af',
    lineHeight: 20,
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(245,158,11,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.3)',
  },
  suggestionEmoji: {
    fontSize: 20,
    marginRight: 12,
  },
  suggestionText: {
    flex: 1,
    fontSize: 14,
    color: '#e5e7eb',
    lineHeight: 20,
  },
  refreshButton: {
    backgroundColor: 'rgba(192,132,252,0.2)',
    margin: 20,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.4)',
  },
  refreshButtonText: {
    color: '#c084fc',
    fontSize: 16,
    fontWeight: '600',
  },
});
