# Building the LOVE Android Companion App

## Prerequisites
- Flutter 3.x+ installed
- Android Studio + Android SDK
- Android device or emulator

## Quick Build

```bash
cd mobile/love_companion
flutter pub get
flutter build apk --release
```

The APK will be at: `build/app/outputs/flutter-apk/app-release.apk`

## Debug Run
```bash
flutter run
```

## Configuration
1. Start LOVE backend: `python service/love_service.py run`  
   (or `uvicorn api.main:app --host 0.0.0.0 --port 8000`)
2. Find your PC's local IP: run `ipconfig` on Windows
3. Open the app → Settings → Enter `http://YOUR_IP:8000`
4. Tap "Save & Connect"

LOVE will now push insights and alerts to your phone in real-time via WebSocket.

## Features
- 💬 Real-time chat with LOVE (markdown rendered)
- 🧠 Thinking trace visible (LOVE's deliberation shown)
- 🔔 Proactive pushes — LOVE messages you without being asked
- 📊 Life dashboard showing insights, patterns, alerts
- ⚡ Auto-reconnect if connection drops
- 🌙 Persists server URL between sessions

## Push Notifications (optional)
To enable native Android push notifications, configure firebase_messaging
and add your google-services.json to android/app/.
