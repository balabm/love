# LOVE Companion — APK Build Guide

## Prerequisites
```
npm install -g @expo/eas-cli
eas login   # your Expo account
```

## Step 1 — Set your Tailscale IP
Edit `eas.json` — replace `YOUR_TAILSCALE_IP` with your PC's Tailscale IP:
```json
"EXPO_PUBLIC_API_URL": "http://100.64.x.x:8000"
```
Find your Tailscale IP: https://login.tailscale.com/admin/machines

## Step 2 — Build APK (free, no paid plan needed)
```bash
# Local debug APK (fastest, no EAS account needed):
npx expo run:android --variant debug

# OR: EAS cloud APK (no Android Studio needed):
eas build --platform android --profile preview
```

The `preview` profile produces an installable `.apk` file.
The `production` profile produces an `.aab` for Play Store.

## Step 3 — Install on phone
```bash
# Via ADB (USB cable):
adb install love-companion.apk

# OR: Download from EAS dashboard and side-load
```

## Step 4 — Tailscale setup (for remote access from anywhere)
1. Install Tailscale on Windows: https://tailscale.com/download/windows
2. Install Tailscale on Android: Play Store → "Tailscale"
3. Sign in to the **same Tailscale account** on both
4. Check PC's Tailscale IP: `tailscale ip -4` in PowerShell
5. Set that IP in the app's Settings tab or in `eas.json` before building

## Step 5 — Push notifications
After installing the APK, open Settings tab in the app → Save Settings.
This auto-registers the device for push notifications from LOVE.

## Local build without EAS (requires Android Studio)
```bash
npx expo prebuild --platform android
cd android && ./gradlew assembleRelease
# APK at: android/app/build/outputs/apk/release/app-release.apk
```
