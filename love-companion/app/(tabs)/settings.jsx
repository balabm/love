import { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, Alert, ActivityIndicator, Platform,
} from 'react-native';
import * as Clipboard from 'expo-clipboard';
import { getServerUrl, setServerUrl, getDeviceId } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setupNotifications } from '../../services/notifications';

export default function SettingsScreen() {
  const [serverUrl, setServerUrlState] = useState('');
  const [deviceId, setDeviceIdState] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState('');
  const [saved, setSaved] = useState(false);
  const [pushToken, setPushToken] = useState('');

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    const url = await getServerUrl();
    const id = await getDeviceId();
    const name = await AsyncStorage.getItem('love_device_name') || '';
    const token = await AsyncStorage.getItem('love_push_token') || '';
    setServerUrlState(url);
    setDeviceIdState(id);
    setDeviceName(name);
    setPushToken(token);
  };

  const save = async () => {
    await setServerUrl(serverUrl.trim());
    await AsyncStorage.setItem('love_device_id', deviceId.trim());
    await AsyncStorage.setItem('love_device_name', deviceName.trim());
    // Auto-register push token with new server URL
    await registerPush(serverUrl.trim(), deviceId.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const registerPush = async (url, id) => {
    try {
      const token = await setupNotifications();
      if (!token) return;
      await AsyncStorage.setItem('love_push_token', token);
      setPushToken(token);
      await fetch(`${url}/devices/push-register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          device_id: id || deviceId,
          token,
          platform: Platform.OS,
        }),
      });
    } catch { }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult('');
    try {
      const res = await fetch(`${serverUrl.trim()}/health`, { timeout: 5000 });
      const data = await res.json();
      setTestResult('✓ Connected to LOVE');
    } catch (e) {
      setTestResult('✗ Cannot reach server. Check IP and port.');
    }
    setTesting(false);
  };

  const copyWebhookUrl = async () => {
    const url = `${serverUrl}/integrations/phone/update`;
    await Clipboard.setStringAsync(url);
    Alert.alert('Copied!', 'Webhook URL copied to clipboard.\nUse this in Tasker or iOS Shortcuts.');
  };

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      {/* Server connection */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>LOVE SERVER</Text>
        <Text style={styles.hint}>
          Enter your home PC's local IP address. Both devices must be on the same WiFi
          OR you can use a tunneling service like Tailscale/ngrok for remote access.
        </Text>

        <Text style={styles.label}>Server URL</Text>
        <TextInput
          style={styles.input}
          value={serverUrl}
          onChangeText={setServerUrlState}
          placeholder="http://192.168.1.100:8000"
          placeholderTextColor="#374151"
          autoCapitalize="none"
          keyboardType="url"
        />

        <View style={styles.row}>
          <TouchableOpacity
            style={[styles.btn, styles.btnSecondary]}
            onPress={testConnection}
            disabled={testing}
          >
            {testing ? (
              <ActivityIndicator size="small" color="#c084fc" />
            ) : (
              <Text style={styles.btnTextSecondary}>Test Connection</Text>
            )}
          </TouchableOpacity>
        </View>

        {testResult ? (
          <Text style={[styles.testResult, testResult.startsWith('✓') ? styles.ok : styles.err]}>
            {testResult}
          </Text>
        ) : null}
      </View>

      {/* Device identity */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>THIS DEVICE</Text>

        <Text style={styles.label}>Device ID</Text>
        <TextInput
          style={styles.input}
          value={deviceId}
          onChangeText={setDeviceIdState}
          placeholder="oneplus-karthi"
          placeholderTextColor="#374151"
          autoCapitalize="none"
        />

        <Text style={styles.label}>Device Name (shown in LOVE)</Text>
        <TextInput
          style={styles.input}
          value={deviceName}
          onChangeText={setDeviceName}
          placeholder="OnePlus Phone"
          placeholderTextColor="#374151"
        />
      </View>

      {/* Save */}
      <TouchableOpacity style={[styles.btn, styles.btnPrimary]} onPress={save}>
        <Text style={styles.btnText}>{saved ? '✓ Saved!' : 'Save Settings'}</Text>
      </TouchableOpacity>

      {/* Webhook */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>WEBHOOK URL</Text>
        <Text style={styles.hint}>
          Use this URL in Tasker (Android), iOS Shortcuts, or any automation
          to push battery/location/notifications to LOVE automatically.
        </Text>
        <View style={styles.webhookBox}>
          <Text style={styles.webhookUrl} numberOfLines={2}>
            {serverUrl}/integrations/phone/update
          </Text>
          <TouchableOpacity style={styles.copyBtn} onPress={copyWebhookUrl}>
            <Text style={styles.copyText}>Copy</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.hint}>
          POST JSON body: {`{ battery, location, missed_calls, unread_messages, activity }`}
        </Text>
      </View>

      {/* Push notifications */}
      {pushToken ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PUSH NOTIFICATIONS</Text>
          <Text style={[styles.hint, { color: '#34d399' }]}>✓ Registered — LOVE can send alerts to this device</Text>
          <Text style={[styles.hint, { fontSize: 10, color: '#4b5563', marginTop: 2 }]} numberOfLines={2}>{pushToken}</Text>
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PUSH NOTIFICATIONS</Text>
          <Text style={styles.hint}>Not registered yet. Save settings to register this device for push alerts.</Text>
        </View>
      )}

      {/* Remote access hint */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>REMOTE ACCESS (TAILSCALE)</Text>
        <Text style={styles.hint}>
          To reach LOVE from anywhere over 4G:{'\n\n'}
          <Text style={styles.bold}>1.</Text> Install Tailscale on Windows PC → tailscale.com{'\n'}
          <Text style={styles.bold}>2.</Text> Install Tailscale on this phone (Play Store){'\n'}
          <Text style={styles.bold}>3.</Text> Sign in to same account on both{'\n'}
          <Text style={styles.bold}>4.</Text> Get PC's Tailscale IP from tailscale admin panel{'\n'}
          <Text style={styles.bold}>5.</Text> Set Server URL to: http://100.x.x.x:8000{'\n\n'}
          Tailscale is free, encrypted, and works even through NAT/4G.
        </Text>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  bold: { color: '#c084fc', fontWeight: '700' },
  container: { flex: 1, backgroundColor: '#0a0a0f', padding: 16 },
  section: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.07)',
    borderRadius: 12, padding: 14, marginBottom: 14,
  },
  sectionTitle: {
    color: '#c084fc', fontSize: 9, fontWeight: '700', letterSpacing: 1.5, marginBottom: 8,
  },
  hint: { color: '#6b7280', fontSize: 12, lineHeight: 18, marginBottom: 10 },
  label: { color: '#9ca3af', fontSize: 11, marginBottom: 4, marginTop: 4 },
  input: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
    borderRadius: 8, padding: 10,
    color: '#e5e7eb', fontSize: 14, marginBottom: 10,
  },
  row: { flexDirection: 'row', gap: 10 },
  btn: {
    borderRadius: 10, padding: 14, alignItems: 'center', marginBottom: 14,
  },
  btnPrimary: { backgroundColor: 'rgba(192,132,252,0.2)', borderWidth: 1, borderColor: 'rgba(192,132,252,0.4)' },
  btnSecondary: { flex: 1, backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)' },
  btnText: { color: '#c084fc', fontWeight: '700', fontSize: 14 },
  btnTextSecondary: { color: '#9ca3af', fontSize: 13 },
  testResult: { fontSize: 13, marginBottom: 4 },
  ok: { color: '#34d399' },
  err: { color: '#f87171' },
  webhookBox: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderWidth: 1, borderColor: 'rgba(192,132,252,0.2)',
    borderRadius: 8, padding: 10, marginBottom: 8,
  },
  webhookUrl: { color: '#a5b4fc', fontSize: 11, flex: 1 },
  copyBtn: {
    backgroundColor: 'rgba(192,132,252,0.15)',
    borderRadius: 6, paddingHorizontal: 10, paddingVertical: 6,
  },
  copyText: { color: '#c084fc', fontSize: 11, fontWeight: '600' },
  bold: { color: '#d1d5db', fontWeight: '600' },
});
