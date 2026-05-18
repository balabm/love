import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getTaskSmartSuggestions } from '../services/api';

export default function TasksScreen() {
  const [taskSuggestions, setTaskSuggestions] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadTaskSuggestions = async () => {
    setLoading(true);
    try {
      const data = await getTaskSmartSuggestions(5);
      setTaskSuggestions(data);
    } catch (error) {
      console.error('[Tasks] Error loading:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTaskSuggestions();
  }, []);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#c084fc" />
      </View>
    );
  }

  const suggestions = taskSuggestions?.suggestions || [];

  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'stress_relief': return '🌿';
      case 'deep_work': return '🎯';
      case 'quick_win': return '⚡';
      case 'deadline': return '⏰';
      case 'ai_prioritized': return '🤖';
      default: return '📋';
    }
  };

  const getSuggestionColor = (type) => {
    switch (type) {
      case 'stress_relief': return 'rgba(16,185,129,0.1)';
      case 'deep_work': return 'rgba(192,132,252,0.1)';
      case 'quick_win': return 'rgba(245,158,11,0.1)';
      case 'deadline': return 'rgba(239,68,68,0.1)';
      case 'ai_prioritized': return 'rgba(59,130,246,0.1)';
      default: return 'rgba(192,132,252,0.05)';
    }
  };

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['rgba(192,132,252,0.1)', 'rgba(192,132,252,0.05)', 'transparent']}
        style={styles.header}
      >
        <Text style={styles.title}>Smart Task Suggestions</Text>
        <Text style={styles.subtitle}>
          AI-powered recommendations based on your context
        </Text>
      </LinearGradient>

      {suggestions.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>📝</Text>
          <Text style={styles.emptyTitle}>No Active Tasks</Text>
          <Text style={styles.emptyText}>
            Add some tasks to get smart suggestions
          </Text>
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {suggestions.length} Task Suggestions
          </Text>
          {suggestions.map((suggestion, index) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.suggestionCard,
                { backgroundColor: getSuggestionColor(suggestion.type) }
              ]}
            >
              <Text style={styles.suggestionIcon}>
                {getSuggestionIcon(suggestion.type)}
              </Text>
              <View style={styles.suggestionContent}>
                <Text style={styles.suggestionTitle}>
                  {suggestion.task?.title || 'Unknown Task'}
                </Text>
                <Text style={styles.suggestionReason}>
                  {suggestion.reason}
                </Text>
                {suggestion.task?.estimated_minutes && (
                  <Text style={styles.suggestionMeta}>
                    ⏱ {suggestion.task.estimated_minutes} min
                  </Text>
                )}
                {suggestion.task?.due_date && (
                  <Text style={styles.suggestionMeta}>
                    📅 Due: {new Date(suggestion.task.due_date).toLocaleDateString()}
                  </Text>
                )}
              </View>
              <View style={styles.suggestionArrow}>
                <Text style={styles.arrowText}>→</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Context Factors</Text>
        <View style={styles.contextCard}>
          <View style={styles.contextItem}>
            <Text style={styles.contextEmoji}>⏰</Text>
            <Text style={styles.contextLabel}>Time of Day</Text>
            <Text style={styles.contextValue}>Current</Text>
          </View>
          <View style={styles.contextItem}>
            <Text style={styles.contextEmoji}>🔋</Text>
            <Text style={styles.contextLabel}>Energy</Text>
            <Text style={styles.contextValue}>Detected</Text>
          </View>
          <View style={styles.contextItem}>
            <Text style={styles.contextEmoji}>📊</Text>
            <Text style={contextLabel}>Stress</Text>
            <Text style={styles.contextValue}>Considered</Text>
          </View>
          <View style={styles.contextItem}>
            <Text style={styles.contextEmoji}>📅</Text>
            <Text style={styles.contextLabel}>Deadlines</Text>
            <Text style={styles.contextValue}>Prioritized</Text>
          </View>
        </View>
      </View>

      <TouchableOpacity style={styles.refreshButton} onPress={loadTaskSuggestions}>
        <Text style={styles.refreshButtonText}>Refresh Suggestions</Text>
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
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
  },
  emptyEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#e5e7eb',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)',
  },
  suggestionIcon: {
    fontSize: 28,
    marginRight: 16,
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#e5e7eb',
    marginBottom: 4,
  },
  suggestionReason: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 8,
  },
  suggestionMeta: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 2,
  },
  suggestionArrow: {
    marginLeft: 12,
  },
  arrowText: {
    fontSize: 20,
    color: '#c084fc',
  },
  contextCard: {
    backgroundColor: 'rgba(192,132,252,0.05)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)',
  },
  contextItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  contextEmoji: {
    fontSize: 20,
    marginRight: 12,
  },
  contextLabel: {
    flex: 1,
    fontSize: 14,
    color: '#9ca3af',
  },
  contextValue: {
    fontSize: 14,
    color: '#c084fc',
    fontWeight: '600',
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
