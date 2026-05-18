"""
LOVE Mind Sync — Wave 14: Cross-Device Intelligence Sharing
Stores device registry and sync state in local JSON files.
Devices discover each other via the shared LOVE API and sync thoughts/memories in real-time.
"""

import json
import time
import uuid
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

SYNC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sync")
DEVICES_FILE = os.path.join(SYNC_DIR, "devices.json")
SYNC_LOG_FILE = os.path.join(SYNC_DIR, "sync_log.json")

def _ensure_dir():
    os.makedirs(SYNC_DIR, exist_ok=True)

def _load_devices() -> Dict[str, Any]:
    _ensure_dir()
    if not os.path.exists(DEVICES_FILE):
        return {}
    try:
        with open(DEVICES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def _save_devices(devices: Dict):
    _ensure_dir()
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)

def register_device(device_id: str, device_name: str, device_type: str, ip: str = "") -> Dict:
    """Register a new device into the LOVE mind sync network."""
    devices = _load_devices()
    devices[device_id] = {
        "device_id": device_id,
        "name": device_name,
        "type": device_type,
        "ip": ip,
        "online": True,
        "last_seen": time.time(),
        "registered_at": devices.get(device_id, {}).get("registered_at", time.time()),
        "session_id": str(uuid.uuid4())[:8],
    }
    _save_devices(devices)
    return {"success": True, "device": devices[device_id]}

def heartbeat_device(device_id: str) -> Dict:
    """Keep a device alive in the sync network."""
    devices = _load_devices()
    if device_id not in devices:
        return {"error": "Device not registered"}
    devices[device_id]["online"] = True
    devices[device_id]["last_seen"] = time.time()
    _save_devices(devices)
    return {"success": True, "device_id": device_id}

def mark_offline() -> int:
    """Mark devices that haven't sent a heartbeat in 60s as offline."""
    devices = _load_devices()
    now = time.time()
    count = 0
    for dev in devices.values():
        if dev.get("online") and (now - dev.get("last_seen", 0)) > 60:
            dev["online"] = False
            count += 1
    if count:
        _save_devices(devices)
    return count

def get_device_roster() -> List[Dict]:
    """Get all registered devices with their online status."""
    mark_offline()
    devices = _load_devices()
    return list(devices.values())

def push_thought(device_id: str, thought: str, metadata: Dict = None) -> Dict:
    """Push a thought/event to the sync log so other devices can pull it."""
    _ensure_dir()
    entry = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "thought": thought,
        "metadata": metadata or {},
        "timestamp": time.time(),
        "iso": datetime.now().isoformat(),
    }
    log = []
    if os.path.exists(SYNC_LOG_FILE):
        try:
            with open(SYNC_LOG_FILE) as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    # Keep last 200 entries
    log = log[-200:]
    with open(SYNC_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
    return {"success": True, "id": entry["id"]}

def pull_thoughts(since: float = 0.0, limit: int = 50) -> List[Dict]:
    """Pull all thoughts/events pushed since a given timestamp."""
    if not os.path.exists(SYNC_LOG_FILE):
        return []
    try:
        with open(SYNC_LOG_FILE) as f:
            log = json.load(f)
        return [e for e in log if e.get("timestamp", 0) > since][-limit:]
    except Exception:
        return []
