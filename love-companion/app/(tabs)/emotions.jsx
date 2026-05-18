import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getEmotionalState } from '../services/api';

export default function EmotionsScreen() {
  const [emotionalData, setEmotionalData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadEmotionalData = async () => {
    setLoading(true);
    try {
      const data = await getEmotionalState();
      setEmotionalData(data);
    } catch (error) {
      console.error('[Emotions] Error loading:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEmotionalData();
  }, []);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#c084fc" />
      </View>
    );
  }

  const currentStress = emotionalData?.current_stress || 0;
  const trend = emotionalData?.trend || 'stable';
  const history = emotionalData?.history || [];
  const moodDistribution = emotionalData?.mood_distribution || {};

  const getStressColor = (level) => {
    if (level < 3) return '#10b981'; // green
    if (level < 6) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  const getStressLabel = (level) => {
    if (level < 3) return 'Low Stress';
    if (level < 6) return 'Moderate Stress';
    return 'High Stress';
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return '↗️';
      case 'decreasing': return '↘️';
      default: return '➡️';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['rgba(192,132,252,0.1)', 'rgba(192,132,252,0.05)', 'transparent']}
        style={styles.header}
      >
        <Text style={styles.title}>Emotional Trends</Text>
        <Text style={styles.subtitle}>
          Track your emotional state over time
        </Text>
      </LinearGradient>

      {/* Current Stress Level */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Current Stress Level</Text>
        <View style={styles.stressCard}>
          <View style={styles.stressIndicator}>
            <View style={[styles.stressBar, { width: `${currentStress * 10}%`, backgroundColor: getStressColor(currentStress) }]} />
          </View>
          <View style={styles.stressInfo}>
            <Text style={[styles.stressValue, { color: getStressColor(currentStress) }]}>
              {currentStress.toFixed(1)}/10
            </Text>
            <Text style={styles.stressLabel}>{getStressLabel(currentStress)}</Text>
            <Text style={styles.trendText}>
              Trend: {getTrendIcon(trend)} {trend}
            </Text>
          </View>
        </View>
      </View>

      {/* Stress History */}
      {history.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Stress History (Last 10)</Text>
          <View style={styles.historyContainer}>
            {history.map((entry, index) => (
              <View key={index} style={styles.historyItem}>
                <Text style={styles.historyTime}>
                  {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Text>
                <View style={[styles.historyBar, { width: `${entry.level * 10}%`, backgroundColor: getStressColor(entry.level) }]} />
                <Text style={styles.historyValue}>{entry.level.toFixed(1)}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Mood Distribution */}
      {Object.keys(moodDistribution).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Mood Distribution</Text>
          {Object.entries(moodDistribution).map(([mood, count]) => (
            <View key={mood} style={styles.moodItem}>
              <Text style={styles.moodName}>{mood}</Text>
              <View style={styles.moodBarContainer}>
                <View style={[styles.moodBar, { width: `${count * 10}%` }]} />
              </View>
              <Text style={styles.moodCount}>{count}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Insights */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Insights</Text>
        {currentStress > 7 && (
          <View style={styles.insightCard}>
            <Text style={styles.insightTitle}>High Stress Detected</Text>
            <Text style={styles.insightText}>
              Consider taking a break, practicing mindfulness, or reducing your workload.
            </Text>
          </View>
        )}
        {trend === 'increasing' && currentStress > 5 && (
          <View style={styles.insightCard}>
            <Text style={styles.insightTitle}>Stress Rising</Text>
            <Text style={styles.insightText}>
              Your stress level has been increasing. Try to identify and address the sources.
            </Text>
          </View>
        )}
        {trend === 'decreasing' && (
          <View style={[styles.insightCard, styles.insightPositive]}>
            <Text style={[styles.insightTitle, styles.insightPositiveTitle]}>Improving</Text>
            <Text style={[styles.insightText, styles.insightPositiveText]}>
              Your stress level is trending downward. Keep up the good work!
            </Text>
          </View>
        )}
      </View>

      <TouchableOpacity style={styles.refreshButton} onPress={loadEmotionalData}>
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
  stressCard: {
    backgroundColor: 'rgba(192,132,252,0.08)',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)',
  },
  stressIndicator: {
    height: 12,
    backgroundColor: 'rgba(192,132,252,0.1)',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 16,
  },
  stressBar: {
    height: '100%',
    borderRadius: 6,
  },
  stressInfo: {
    alignItems: 'center',
  },
  stressValue: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  stressLabel: {
    fontSize: 16,
    color: '#9ca3af',
    marginBottom: 8,
  },
  trendText: {
    fontSize: 14,
    color: '#6b7280',
  },
  historyContainer: {
    backgroundColor: 'rgba(192,132,252,0.05)',
    borderRadius: 12,
    padding: 16,
  },
  historyItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  historyTime: {
    fontSize: 12,
    color: '#9ca3af',
    width: 60,
  },
  historyBar: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    marginHorizontal: 12,
  },
  historyValue: {
    fontSize: 14,
    color: '#e5e7eb',
    width: 40,
    textAlign: 'right',
  },
  moodItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  moodName: {
    fontSize: 14,
    color: '#e5e7eb',
    width: 100,
  },
  moodBarContainer: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(192,132,252,0.1)',
    borderRadius: 4,
    marginHorizontal: 12,
  },
  moodBar: {
    height: '100%',
    backgroundColor: '#c084fc',
    borderRadius: 4,
  },
  moodCount: {
    fontSize: 14,
    color: '#9ca3af',
    width: 40,
    textAlign: 'right',
  },
  insightCard: {
    backgroundColor: 'rgba(239,68,68,0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
  },
  insightPositive: {
    backgroundColor: 'rgba(16,185,129,0.1)',
    borderColor: 'rgba(16,185,129,0.3)',
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ef4444',
    marginBottom: 8,
  },
  insightPositiveTitle: {
    color: '#10b981',
  },
  insightText: {
    fontSize: 14,
    color: '#9ca3af',
    lineHeight: 20,
  },
  insightPositiveText: {
    color: '#6b7280',
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
