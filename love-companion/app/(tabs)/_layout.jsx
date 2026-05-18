import { Tabs } from 'expo-router';
import { Text } from 'react-native';

function Icon({ emoji, focused }) {
  return (
    <Text style={{ fontSize: 20, opacity: focused ? 1 : 0.4 }}>{emoji}</Text>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarStyle: {
          backgroundColor: '#0f0c19',
          borderTopColor: 'rgba(192,132,252,0.15)',
          height: 60,
          paddingBottom: 8,
        },
        tabBarActiveTintColor: '#c084fc',
        tabBarInactiveTintColor: '#4b5563',
        tabBarLabelStyle: { fontSize: 10, fontWeight: '600', letterSpacing: 0.5 },
        headerStyle: { backgroundColor: '#0a0a0f' },
        headerTintColor: '#c084fc',
        headerTitleStyle: { fontWeight: '700', letterSpacing: 2, fontSize: 14 },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'LOVE',
          tabBarLabel: 'Chat',
          tabBarIcon: ({ focused }) => <Icon emoji="♡" focused={focused} />,
          headerTitle: '♡  LOVE',
        }}
      />
      <Tabs.Screen
        name="context"
        options={{
          title: 'NOW',
          tabBarLabel: 'Now',
          tabBarIcon: ({ focused }) => <Icon emoji="◉" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'LIFE',
          tabBarLabel: 'Life',
          tabBarIcon: ({ focused }) => <Icon emoji="⬡" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'NOTIFICATIONS',
          tabBarLabel: 'Alerts',
          tabBarIcon: ({ focused }) => <Icon emoji="🔔" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="calendar"
        options={{
          title: 'CALENDAR',
          tabBarLabel: 'Calendar',
          tabBarIcon: ({ focused }) => <Icon emoji="�" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="relationships"
        options={{
          title: 'RELATIONSHIPS',
          tabBarLabel: 'People',
          tabBarIcon: ({ focused }) => <Icon emoji="👥" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="tasks"
        options={{
          title: 'TASKS',
          tabBarLabel: 'Tasks',
          tabBarIcon: ({ focused }) => <Icon emoji="✅" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="emotions"
        options={{
          title: 'EMOTIONS',
          tabBarLabel: 'Emotions',
          tabBarIcon: ({ focused }) => <Icon emoji="💜" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="devices"
        options={{
          title: 'DEVICES',
          tabBarLabel: 'Devices',
          tabBarIcon: ({ focused }) => <Icon emoji="◈" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{
          title: 'SETTINGS',
          tabBarLabel: 'Setup',
          tabBarIcon: ({ focused }) => <Icon emoji="⚙" focused={focused} />,
        }}
      />
      <Tabs.Screen
        name="agi"
        options={{
          title: 'AGI',
          tabBarLabel: 'AGI',
          tabBarIcon: ({ focused }) => <Icon emoji="🧠" focused={focused} />,
        }}
      />
    </Tabs>
  );
}
