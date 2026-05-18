import { useEffect, useState } from 'react';
import { Stack, router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import * as Linking from 'expo-linking';
import { startSync } from '../services/sync';
import { startNotificationListener } from '../services/notif-reader';
import { isOnboarded } from '../services/profile';
import { setupNotifications, addResponseListener } from '../services/notifications';

export default function RootLayout() {
  const [checked, setChecked] = useState(false);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  useEffect(() => {
    (async () => {
      const onboarded = await isOnboarded();
      setNeedsOnboarding(!onboarded);
      setChecked(true);
      startSync();
      startNotificationListener();

      // Push notifications
      const pushToken = await setupNotifications();
      if (pushToken) {
        // TODO: Send pushToken to LOVE server via /devices/push-register endpoint
        console.log('[Push] Token:', pushToken.slice(0, 20) + '…');
      }

      // Handle notification taps
      addResponseListener(response => {
        const data = response.notification.request.content.data;
        if (data?.type === 'chat' || data?.screen === 'chat') {
          router.push('/(tabs)/');
        } else if (data?.screen === 'now') {
          router.push('/(tabs)/context');
        }
      });

      // Deep links / share intents
      const handleUrl = (event) => {
        const url = event.url;
        if (url?.startsWith('love://share?text=')) {
          const text = decodeURIComponent(url.split('text=')[1]);
          router.push({ pathname: '/(tabs)/', params: { sharedText: text } });
        }
      };
      const sub = Linking.addEventListener('url', handleUrl);
      Linking.getInitialURL().then(handleUrl);
      return () => sub.remove();
    })();
  }, []);

  if (!checked) return null;

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#0a0a0f' },
          headerTintColor: '#c084fc',
          headerTitleStyle: { fontWeight: '700', letterSpacing: 1 },
          contentStyle: { backgroundColor: '#0a0a0f' },
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="onboarding"
          options={{
            headerShown: false,
            gestureEnabled: false,
          }}
        />
      </Stack>
      {needsOnboarding && <OnboardingRedirect />}
    </>
  );
}

function OnboardingRedirect() {
  useEffect(() => {
    router.replace('/onboarding');
  }, []);
  return null;
}
