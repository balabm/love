# LOVE Companion App

Mobile app for OnePlus phone + OnePlus Tab. Chat with LOVE, see live context, manage devices.

## Run on your phone (development)

```bash
# Install Expo Go on your phone from Play Store
cd love-companion
npm install
npx expo start
# Scan QR code with Expo Go app
```

## Build APK (install permanently)

```bash
npm install -g eas-cli
eas login
eas build --platform android --profile apk
# Download APK → install on phone + tablet
```

## First-time setup

1. Open the app → go to **Setup** tab
2. Enter your home PC's IP address: `http://192.168.1.X:8000`
   - Find your PC's IP: run `ipconfig` in terminal → look for IPv4 under your WiFi adapter
3. Tap **Test Connection** — should say ✓ Connected
4. Set your Device ID: `oneplus-karthi`
5. Tap **Save Settings**

## Remote access (away from home WiFi)

Install **Tailscale** on home PC and phone (free):
- Home PC gets IP like `100.x.x.x`
- Use that Tailscale IP in Settings instead of local IP
- Works over 4G/5G too

## What each tab does

| Tab | Purpose |
|-----|---------|
| **Chat** | Talk to LOVE — same as desktop, quick prompts |
| **Now** | What LOVE currently sees — your context live |
| **Life** | Life score, domain breakdown, recommendations |
| **Devices** | All connected devices — home PC, office laptop, etc. |
| **Setup** | Server URL, device ID, webhook URL, remote access help |

## Automatic background sync

The app sends to LOVE every 60 seconds:
- Battery level (alerts LOVE when < 20%)
- Location updates (every 200m movement)
- Device online status

## Automation (Tasker / Bixby)

Use the webhook URL from the Setup tab to push data automatically:
- Missed calls
- SMS/WhatsApp count
- App usage
- Screen on/off
