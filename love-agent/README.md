# LOVE Office Laptop Agent

Runs on your **office laptop** to connect Teams, Outlook and Calendar to LOVE.

## Quick Start

```bash
cd love-agent
npm install
node agent.js
```

First run creates `config.json`. Fill in your values:

```json
{
  "love_server": "http://192.168.1.100:8000",
  "device_id": "office-laptop",
  "device_name": "Work Laptop",
  "microsoft_client_id": "your-azure-app-client-id",
  "sync_interval_seconds": 60,
  "notify_on_alerts": true
}
```

## Get your Microsoft Client ID

1. Go to [portal.azure.com](https://portal.azure.com) → App registrations → New
2. Name: `LOVE Assistant` | Accounts: Personal + Work/School
3. Authentication → Add platform → Mobile/Desktop → tick `urn:ietf:wg:oauth:2.0:oob`
4. API Permissions → Add: `Mail.Read`, `Calendars.Read`, `Chat.Read`, `Files.Read.All`, `User.Read`, `Presence.Read` (all Delegated)
5. Grant admin consent
6. Copy the **Application (client) ID** → paste into `config.json`

## Auto-start on Windows boot

```bash
node install-service.js
```

Runs as: Administrator → adds to Windows Task Scheduler.

## What it syncs

| Source | Data |
|--------|------|
| Outlook | Unread email count + notifications |
| Calendar | Today's events + next meeting |
| Teams | Unread messages + presence status |
| Device | Battery, IP, OS, online status |

## Remote access (away from office WiFi)

Use [Tailscale](https://tailscale.com) — install on home PC + office laptop.
Set `love_server` to the Tailscale IP of your home PC.
