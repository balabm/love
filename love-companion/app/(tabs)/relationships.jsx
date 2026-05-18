import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { getRelationships } from '../services/api';

export default function RelationshipsScreen() {
  const [relationships, setRelationships] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadRelationships = async () => {
    setLoading(true);
    try {
      const data = await getRelationships();
      setRelationships(data);
    } catch (error) {
      console.error('[Relationships] Error loading:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRelationships();
  }, []);

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#c084fc" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <LinearGradient
        colors={['rgba(192,132,252,0.1)', 'rgba(192,132,252,0.05)', 'transparent']}
        style={styles.header}
      >
        <Text style={styles.title}>Relationships</Text>
        <Text style={styles.subtitle}>
          {relationships?.total_people_tracked || 0} people tracked
        </Text>
      </LinearGradient>

      {relationships?.top_people && relationships.top_people.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Top People</Text>
          {relationships.top_people.map((person, index) => (
            <TouchableOpacity key={index} style={styles.personCard}>
              <View style={styles.personHeader}>
                <View style={styles.avatar}>
                  <Text style={styles.avatarText}>
                    {person.name.charAt(0).toUpperCase()}
                  </Text>
                </View>
                <View style={styles.personInfo}>
                  <Text style={styles.personName}>{person.name}</Text>
                  <Text style={styles.personType}>{person.relationship_type}</Text>
                </View>
                <Text style={styles.mentionCount}>{person.mention_count} mentions</Text>
              </View>
              
              {person.emotional_context && (
                <View style={styles.emotionalContext}>
                  <Text style={styles.emotionalTitle}>Emotional Context:</Text>
                  {Object.entries(person.emotional_context).map(([emotion, count]) => (
                    count > 0 && (
                      <View key={emotion} style={styles.emotionTag}>
                        <Text style={styles.emotionText}>
                          {emotion}: {count}
                        </Text>
                      </View>
                    )
                  ))}
                </View>
              )}
              
              {person.last_mentioned && (
                <Text style={styles.lastMentioned}>
                  Last mentioned: {new Date(person.last_mentioned).toLocaleDateString()}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No relationships tracked yet</Text>
          <Text style={styles.emptySubtext}>
            Relationships will be tracked as you mention people in conversations
          </Text>
        </View>
      )}

      <TouchableOpacity style={styles.refreshButton} onPress={loadRelationships}>
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
  personCard: {
    backgroundColor: 'rgba(192,132,252,0.08)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(192,132,252,0.2)',
  },
  personHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(192,132,252,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#c084fc',
  },
  personInfo: {
    flex: 1,
  },
  personName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#e5e7eb',
  },
  personType: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
  },
  mentionCount: {
    fontSize: 14,
    color: '#c084fc',
    fontWeight: '600',
  },
  emotionalContext: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  emotionalTitle: {
    fontSize: 12,
    color: '#9ca3af',
    marginRight: 8,
  },
  emotionTag: {
    backgroundColor: 'rgba(192,132,252,0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 6,
    marginBottom: 6,
  },
  emotionText: {
    fontSize: 12,
    color: '#c084fc',
  },
  lastMentioned: {
    fontSize: 12,
    color: '#6b7280',
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#9ca3af',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
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
