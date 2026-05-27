"""
Neural Sync (Multi-Device Synchronization)
Central SQLite database for cross-device sync between ROG Ally and Legion.
With Environment Intelligence for hardware-aware resource allocation.
"""

import os
import json
import sqlite3
import threading
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass

from core.memory import save_log
# Neural Bus import for hardware shift events
try:
    from core.neural_bus import NeuralBus, EventPriority, EventDomain
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False


PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SYNC_DB_PATH = DATA_DIR / "love_os.db"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Device type constants - these are generic, users can define their own in settings
DEVICE_MOBILE = "mobile"          # Mobile/Portable mode (battery conscious)
DEVICE_DESKTOP = "desktop"        # Desktop/Workstation mode (high performance)
DEVICE_GAMING = "gaming"          # Gaming mode (high performance)
DEVICE_LAPTOP = "laptop"          # Laptop mode (balanced)

# Legacy aliases for backward compatibility
DEVICE_ROG_ALLY = DEVICE_MOBILE
DEVICE_LEGION = DEVICE_DESKTOP


class SyncDatabase:
    """Central SQLite database for Neural Sync."""
    
    def __init__(self, db_path: Path = SYNC_DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(str(self.db_path))
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Device heartbeat tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_heartbeats (
                    device_id TEXT PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    device_name TEXT,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    current_mode TEXT DEFAULT 'unknown',
                    ip_address TEXT,
                    sync_enabled BOOLEAN DEFAULT 1
                )
            """)
            
            # Synced memory entries
            conn.execute("""
                CREATE TABLE IF NOT EXISTS synced_memory (
                    id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_devices TEXT DEFAULT '[]',
                    deleted BOOLEAN DEFAULT 0
                )
            """)
            
            # User state snapshot
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    device_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sync_priority INTEGER DEFAULT 5
                )
            """)
            
            # Sync log for debugging
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Mood/Context for personality switching
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_context (
                    device_id TEXT PRIMARY KEY,
                    personality_mode TEXT DEFAULT 'balanced',
                    active_context TEXT,
                    work_hours_today REAL DEFAULT 0,
                    last_activity TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES device_heartbeats(device_id)
                )
            """)
            
            conn.commit()
    
    def log_sync(self, device_id: str, action: str, details: str = None):
        """Log a sync action."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO sync_log (device_id, action, details) VALUES (?, ?, ?)",
                (device_id, action, details)
            )
            conn.commit()


class HeartbeatManager:
    """Manages device heartbeats and presence detection."""
    
    def __init__(self, db: SyncDatabase = None):
        self.db = db or SyncDatabase()
    
    def register_device(self, device_id: str, device_type: str, device_name: str = None, ip_address: str = None):
        """Register or update a device."""
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO device_heartbeats (device_id, device_type, device_name, ip_address, last_seen)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    device_type = excluded.device_type,
                    device_name = excluded.device_name,
                    ip_address = excluded.ip_address,
                    last_seen = excluded.last_seen
            """, (device_id, device_type, device_name, ip_address, datetime.now().isoformat()))
            conn.commit()
        
        self.db.log_sync(device_id, "device_registered", f"Type: {device_type}")
        save_log('device_register', {
            'device_id': device_id,
            'device_type': device_type,
            'timestamp': datetime.now().isoformat()
        })
    
    def heartbeat(self, device_id: str, current_mode: str = None) -> Dict[str, Any]:
        """Update device heartbeat."""
        now = datetime.now().isoformat()
        
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE device_heartbeats
                SET last_seen = ?, current_mode = COALESCE(?, current_mode)
                WHERE device_id = ?
            """, (now, current_mode, device_id))
            conn.commit()
        
        # Get active device info
        active_device = self.get_active_device()
        
        return {
            "status": "ok",
            "device_id": device_id,
            "timestamp": now,
            "active_device": active_device
        }
    
    def get_active_device(self) -> Optional[Dict[str, Any]]:
        """Get the currently most active device."""
        cutoff = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT device_id, device_type, device_name, current_mode, last_seen
                FROM device_heartbeats
                WHERE last_seen > ? AND sync_enabled = 1
                ORDER BY last_seen DESC
                LIMIT 1
            """, (cutoff,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "device_id": row["device_id"],
                    "device_type": row["device_type"],
                    "device_name": row["device_name"],
                    "current_mode": row["current_mode"],
                    "last_seen": row["last_seen"]
                }
        return None
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all registered devices."""
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT device_id, device_type, device_name, current_mode, last_seen
                FROM device_heartbeats
                WHERE sync_enabled = 1
                ORDER BY last_seen DESC
            """)
            
            return [
                {
                    "device_id": row["device_id"],
                    "device_type": row["device_type"],
                    "device_name": row["device_name"],
                    "current_mode": row["current_mode"],
                    "last_seen": row["last_seen"]
                }
                for row in cursor.fetchall()
            ]
    
    def set_device_mode(self, device_id: str, mode: str):
        """Set the current mode for a device."""
        with self.db._get_connection() as conn:
            conn.execute(
                "UPDATE device_heartbeats SET current_mode = ? WHERE device_id = ?",
                (mode, device_id)
            )
            conn.commit()
        
        self.db.log_sync(device_id, "mode_change", f"Mode: {mode}")


class SyncMemory:
    """Synchronized memory across devices."""
    
    def __init__(self, db: SyncDatabase = None):
        self.db = db or SyncDatabase()
    
    def sync_entry(self, device_id: str, category: str, content: str, metadata: Dict = None) -> str:
        """Add a synchronized memory entry."""
        entry_id = f"{device_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO synced_memory (id, device_id, category, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry_id,
                device_id,
                category,
                content,
                json.dumps(metadata or {}),
                datetime.now().isoformat()
            ))
            conn.commit()
        
        self.db.log_sync(device_id, "memory_sync", f"Category: {category}")
        
        return entry_id
    
    def get_unsynced_entries(self, device_id: str, since: str = None) -> List[Dict[str, Any]]:
        """Get entries that haven't been synced to this device."""
        since = since or (datetime.now() - timedelta(days=1)).isoformat()
        
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, device_id, category, content, metadata, timestamp
                FROM synced_memory
                WHERE timestamp > ?
                AND deleted = 0
                AND (
                    synced_to_devices IS NULL 
                    OR json_extract(synced_to_devices, '$') NOT LIKE ?
                )
                ORDER BY timestamp ASC
            """, (since, f'%"{device_id}"%'))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    "id": row["id"],
                    "device_id": row["device_id"],
                    "category": row["category"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"] or '{}'),
                    "timestamp": row["timestamp"]
                })
            
            return entries
    
    def mark_synced(self, entry_id: str, device_id: str):
        """Mark an entry as synced to a device."""
        with self.db._get_connection() as conn:
            # Get current synced devices
            cursor = conn.execute(
                "SELECT synced_to_devices FROM synced_memory WHERE id = ?",
                (entry_id,)
            )
            row = cursor.fetchone()
            
            if row:
                synced = json.loads(row["synced_to_devices"] or '[]')
                if device_id not in synced:
                    synced.append(device_id)
                
                conn.execute(
                    "UPDATE synced_memory SET synced_to_devices = ? WHERE id = ?",
                    (json.dumps(synced), entry_id)
                )
                conn.commit()
    
    def get_entries_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent entries by category."""
        with self.db._get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, device_id, category, content, metadata, timestamp
                FROM synced_memory
                WHERE category = ? AND deleted = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (category, limit))
            
            return [
                {
                    "id": row["id"],
                    "device_id": row["device_id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"] or '{}'),
                    "timestamp": row["timestamp"]
                }
                for row in cursor.fetchall()
            ]


class UserStateSync:
    """Synchronize user state across devices."""
    
    def __init__(self, db: SyncDatabase = None):
        self.db = db or SyncDatabase()
    
    def set_state(self, key: str, value: Any, device_id: str = None, priority: int = 5):
        """Set a user state value."""
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_state (key, value, device_id, timestamp, sync_priority)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    device_id = excluded.device_id,
                    timestamp = excluded.timestamp,
                    sync_priority = excluded.sync_priority
            """, (key, json.dumps(value), device_id, datetime.now().isoformat(), priority))
            conn.commit()
    
    def get_state(self, key: str) -> Optional[Any]:
        """Get a user state value."""
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT value FROM user_state WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
        return None
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get all user state."""
        with self.db._get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM user_state")
            return {row["key"]: json.loads(row["value"]) for row in cursor.fetchall()}
    
    def get_recent_changes(self, since: str) -> Dict[str, Any]:
        """Get state changes since a timestamp."""
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT key, value FROM user_state WHERE timestamp > ?",
                (since,)
            )
            return {row["key"]: json.loads(row["value"]) for row in cursor.fetchall()}


class PersonalityAdapter:
    """Adapts LOVE's personality based on device context."""
    
    def __init__(self, db: SyncDatabase = None):
        self.db = db or SyncDatabase()
    
    def update_context(self, device_id: str, mode: str = None, context: str = None, work_hours: float = None):
        """Update device context."""
        now = datetime.now().isoformat()
        
        with self.db._get_connection() as conn:
            conn.execute("""
                INSERT INTO device_context (device_id, personality_mode, active_context, work_hours_today, last_activity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    personality_mode = COALESCE(?, personality_mode),
                    active_context = COALESCE(?, active_context),
                    work_hours_today = COALESCE(?, work_hours_today),
                    last_activity = ?
            """, (device_id, mode, context, work_hours, now, mode, context, work_hours, now))
            conn.commit()
    
    def get_personality_for_device(self, device_id: str) -> Dict[str, Any]:
        """Get personality settings for a device."""
        # Get device type
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT device_type, current_mode FROM device_heartbeats WHERE device_id = ?",
                (device_id,)
            )
            device_row = cursor.fetchone()
            
            cursor = conn.execute(
                "SELECT personality_mode, active_context, work_hours_today FROM device_context WHERE device_id = ?",
                (device_id,)
            )
            context_row = cursor.fetchone()
        
        if not device_row:
            return {"personality": "balanced", "modifications": []}
        
        device_type = device_row["device_type"]
        current_mode = device_row["current_mode"]
        
        # Determine personality modifications
        modifications = []
        
        if device_type == DEVICE_ROG_ALLY or current_mode == "personal":
            modifications = [
                "More casual and playful tone",
                "Gaming references welcome",
                "Relaxed boundaries on humor",
                "Entertainment suggestions OK"
            ]
            base_personality = "relaxed"
        elif device_type == DEVICE_LEGION or current_mode == "work":
            modifications = [
                "More concise and direct",
                "Focus on productivity",
                "Work context prioritized",
                "Less small talk"
            ]
            base_personality = "focused"
        else:
            base_personality = "balanced"
        
        # Add work hours warning if applicable
        if context_row and context_row["work_hours_today"]:
            hours = context_row["work_hours_today"]
            if hours >= 9:
                modifications.append("STRICT: User has exceeded 9-hour limit. Force recovery mode.")
            elif hours >= 7:
                modifications.append(f"Warning: User at {hours}/9 hours. Start winding down.")
        
        return {
            "device_type": device_type,
            "current_mode": current_mode,
            "personality": base_personality,
            "modifications": modifications,
            "active_context": context_row["active_context"] if context_row else None
        }


# Global instances
_sync_db = None
_heartbeat_mgr = None
_sync_memory = None
_user_state = None
_personality_adapter = None
_handoff_mgr = None

def get_sync_db() -> SyncDatabase:
    """Get singleton sync database."""
    global _sync_db
    if _sync_db is None:
        _sync_db = SyncDatabase()
    return _sync_db

def get_heartbeat_manager() -> HeartbeatManager:
    """Get singleton heartbeat manager."""
    global _heartbeat_mgr
    if _heartbeat_mgr is None:
        _heartbeat_mgr = HeartbeatManager(get_sync_db())
    return _heartbeat_mgr

def get_sync_memory() -> SyncMemory:
    """Get singleton sync memory."""
    global _sync_memory
    if _sync_memory is None:
        _sync_memory = SyncMemory(get_sync_db())
    return _sync_memory

def get_user_state() -> UserStateSync:
    """Get singleton user state sync."""
    global _user_state
    if _user_state is None:
        _user_state = UserStateSync(get_sync_db())
    return _user_state

def get_personality_adapter() -> PersonalityAdapter:
    """Get singleton personality adapter."""
    global _personality_adapter
    if _personality_adapter is None:
        _personality_adapter = PersonalityAdapter(get_sync_db())
    return _personality_adapter

def get_handoff_manager() -> DeviceHandoffManager:
    """Get singleton device handoff manager."""
    global _handoff_mgr
    if _handoff_mgr is None:
        _handoff_mgr = DeviceHandoffManager(get_sync_db())
    return _handoff_mgr


@dataclass
class PowerProfile:
    """Hardware resource allocation profile."""
    device_type: str
    llm_temperature: float
    llm_max_tokens: int
    market_scan_interval_min: int
    use_quantized_models: bool
    background_tasks_enabled: bool
    gpu_acceleration: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_type": self.device_type,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "market_scan_interval": self.market_scan_interval_min,
            "use_quantized_models": self.use_quantized_models,
            "background_tasks": self.background_tasks_enabled,
            "gpu_acceleration": self.gpu_acceleration
        }


class HardwareResourceManager:
    """Manages hardware detection and power profiles."""
    
    # Predefined profiles for known devices
    PROFILES = {
        DEVICE_LEGION: PowerProfile(
            device_type=DEVICE_LEGION,
            llm_temperature=0.4,
            llm_max_tokens=2048,
            market_scan_interval_min=5,
            use_quantized_models=False,
            background_tasks_enabled=True,
            gpu_acceleration=True
        ),
        DEVICE_ROG_ALLY: PowerProfile(
            device_type=DEVICE_ROG_ALLY,
            llm_temperature=0.5,
            llm_max_tokens=1024,
            market_scan_interval_min=15,
            use_quantized_models=True,
            background_tasks_enabled=False,
            gpu_acceleration=False
        )
    }
    
    @staticmethod
    def detect_hardware() -> Dict[str, Any]:
        """Detect current hardware capabilities."""
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "gpu": None,
            "battery": None,
            "is_laptop": False
        }
        
        # Detect GPU on Windows
        if platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    gpu_lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and 'Name' not in line]
                    info["gpu"] = gpu_lines[0] if gpu_lines else None
                    # Check for RTX
                    info["has_rtx"] = any('RTX' in line for line in gpu_lines)
            except Exception:
                pass
            
            # Check battery (laptop indicator)
            try:
                result = subprocess.run(
                    ["powershell", "-Command", "Get-WmiObject -Class BatteryStatus"],
                    capture_output=True, text=True, timeout=5
                )
                info["is_laptop"] = result.returncode == 0
                
                # Get battery percentage if available
                result = subprocess.run(
                    ["powershell", "-Command", "(Get-WmiObject -Class BatteryStatus).PowerOnLine"],
                    capture_output=True, text=True, timeout=5
                )
                info["ac_power"] = "True" in result.stdout
            except Exception:
                pass
        
        # Infer device type from hardware
        if info.get("has_rtx") and not info.get("is_laptop"):
            info["inferred_type"] = DEVICE_LEGION
        elif info.get("is_laptop") and not info.get("ac_power"):
            info["inferred_type"] = DEVICE_ROG_ALLY  # Likely on battery
        else:
            info["inferred_type"] = DEVICE_LEGION  # Default to power
        
        return info
    
    @classmethod
    def get_power_profile(cls, device_type: str = None) -> PowerProfile:
        """Get appropriate power profile for device."""
        if device_type and device_type in cls.PROFILES:
            return cls.PROFILES[device_type]
        
        # Auto-detect if not specified
        hw_info = cls.detect_hardware()
        inferred = hw_info.get("inferred_type", DEVICE_LEGION)
        return cls.PROFILES.get(inferred, cls.PROFILES[DEVICE_LEGION])
    
    @staticmethod
    def get_llm_params(profile: PowerProfile) -> Dict[str, Any]:
        """Get LLM parameters based on power profile."""
        return {
            "temperature": profile.llm_temperature,
            "max_tokens": profile.llm_max_tokens,
            "use_quantized": profile.use_quantized_models
        }
    
    @classmethod
    def emit_hardware_shift_event(cls, to_device_id: str, to_device_type: str):
        """
        Emit a NeuralBus event when shifting to a new device.
        This triggers the LLM router to switch models and pause heavy tasks.
        """
        if not NEURAL_BUS_AVAILABLE:
            print(f"[HardwareManager] NeuralBus not available, skipping hardware shift event")
            return
        
        try:
            bus = NeuralBus()
            
            # Determine the mode based on device type
            if to_device_type == DEVICE_ROG_ALLY or to_device_type == DEVICE_MOBILE:
                mode = "power_saver"
            elif to_device_type == DEVICE_LEGION or to_device_type == DEVICE_DESKTOP:
                mode = "high_performance"
            else:
                mode = "balanced"
            
            # Emit the hardware shift event
            event_id = bus.publish(
                domain="device",
                event_type="hardware_shift",
                payload={
                    "mode": mode,
                    "to_device_id": to_device_id,
                    "to_device_type": to_device_type,
                    "timestamp": datetime.now().isoformat()
                },
                source_module="sync",
                priority=EventPriority.HIGH,
                propagate=True
            )
            
            print(f"[HardwareManager] Emitted hardware_shift event: {event_id} -> mode: {mode}")
            save_log('hardware_shift', {
                'event_id': event_id,
                'mode': mode,
                'to_device_id': to_device_id,
                'to_device_type': to_device_type,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"[HardwareManager] Failed to emit hardware shift event: {e}")
            save_log('hardware_shift_error', {
                'error': str(e),
                'to_device_id': to_device_id,
                'timestamp': datetime.now().isoformat()
            })


class DeviceHandoffManager:
    """
    Manages cross-device handoff - the "Follow Me" protocol.
    
    When a user switches from one device to another, this manager:
    1. Packages the SensoryBuffer (last 5 minutes of context/chat/state)
    2. Pushes it to the new device
    3. Triggers hardware shift events for ROG Ally
    4. Ensures seamless context transfer
    """
    
    def __init__(self, db: SyncDatabase = None):
        self.db = db or SyncDatabase()
        self.heartbeat_mgr = HeartbeatManager(self.db)
        self.sync_memory = SyncMemory(self.db)
        self.user_state = UserStateSync(self.db)
    
    def _is_rog_ally(self, device_id: str, device_type: str = None) -> bool:
        """
        Identify if the target device is a ROG Ally.
        Checks by device type, device ID patterns, or battery characteristics.
        """
        # Check by device type
        if device_type == DEVICE_ROG_ALLY or device_type == DEVICE_MOBILE:
            return True
        
        # Check by device ID patterns (common ROG Ally identifiers)
        rog_patterns = ['rog', 'ally', 'handheld', 'portable']
        device_id_lower = device_id.lower()
        if any(pattern in device_id_lower for pattern in rog_patterns):
            return True
        
        # Check device info from heartbeat
        device_info = self._get_device_info(device_id)
        if device_info:
            # If it's a laptop/mobile type and not on AC power, likely ROG Ally
            if device_info.get("device_type") in [DEVICE_MOBILE, DEVICE_LAPTOP]:
                hw_info = HardwareResourceManager.detect_hardware()
                if hw_info.get("is_laptop") and not hw_info.get("ac_power"):
                    return True
        
        return False
    
    def _get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information from heartbeat database."""
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT device_type, device_name, current_mode FROM device_heartbeats WHERE device_id = ?",
                (device_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "device_id": device_id,
                    "device_type": row["device_type"],
                    "device_name": row["device_name"],
                    "current_mode": row["current_mode"]
                }
        return None
    
    def _package_sensory_buffer(self, from_device_id: str, minutes: int = 5) -> Dict[str, Any]:
        """
        Package the last N minutes of context/chat/state from the active device.
        This includes:
        - Recent chat/conversation history
        - Working memory items
        - User state
        - Device context
        """
        cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        # Get recent synced memory entries (chat, context, etc.)
        recent_entries = self.sync_memory.get_unsynced_entries(
            device_id=from_device_id,
            since=cutoff
        )
        
        # Get all user state
        user_state = self.user_state.get_all_state()
        
        # Get device context
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT personality_mode, active_context, work_hours_today FROM device_context WHERE device_id = ?",
                (from_device_id,)
            )
            row = cursor.fetchone()
            device_context = {
                "personality_mode": row["personality_mode"] if row else "balanced",
                "active_context": row["active_context"] if row else None,
                "work_hours_today": row["work_hours_today"] if row else 0.0
            } if row else {}
        
        # Package everything
        context_package = {
            "from_device_id": from_device_id,
            "packaged_at": datetime.now().isoformat(),
            "time_window_minutes": minutes,
            "recent_entries": recent_entries,
            "user_state": user_state,
            "device_context": device_context,
            "entry_count": len(recent_entries)
        }
        
        return context_package
    
    def _push_context_to_device(self, to_device_id: str, context_package: Dict[str, Any]) -> bool:
        """
        Push the packaged context to the target device.
        Stores it as a special handoff sync entry that the receiving device can process.
        """
        try:
            # Create a handoff sync entry
            handoff_id = self.sync_memory.sync_entry(
                device_id=to_device_id,
                category="handoff_context",
                content=json.dumps(context_package),
                metadata={
                    "handoff_from": context_package["from_device_id"],
                    "handoff_to": to_device_id,
                    "packaged_at": context_package["packaged_at"],
                    "entry_count": context_package["entry_count"]
                }
            )
            
            # Also update user state to reflect the handoff
            self.user_state.set_state(
                key="last_handoff",
                value={
                    "from_device": context_package["from_device_id"],
                    "to_device": to_device_id,
                    "timestamp": context_package["packaged_at"]
                },
                device_id=to_device_id,
                priority=10  # High priority
            )
            
            print(f"[Handoff] Pushed context to {to_device_id}: {context_package['entry_count']} entries")
            return True
            
        except Exception as e:
            print(f"[Handoff] Failed to push context to {to_device_id}: {e}")
            return False
    
    def trigger_handoff(self, from_device_id: str, to_device_id: str) -> Dict[str, Any]:
        """
        Trigger a cross-device handoff from one device to another.
        
        This is the "Follow Me" protocol - when a user switches devices,
        LOVE seamlessly transfers context and adjusts hardware resources.
        
        Args:
            from_device_id: The device we're handing off from
            to_device_id: The device we're handing off to
            
        Returns:
            Dict with handoff status, context transferred, and any errors
        """
        result = {
            "status": "initiated",
            "from_device": from_device_id,
            "to_device": to_device_id,
            "timestamp": datetime.now().isoformat(),
            "context_transferred": False,
            "hardware_shift_emitted": False,
            "errors": []
        }
        
        try:
            # Validate devices exist
            from_device = self._get_device_info(from_device_id)
            to_device = self._get_device_info(to_device_id)
            
            if not from_device:
                result["errors"].append(f"Source device {from_device_id} not found")
                result["status"] = "failed"
                return result
            
            if not to_device:
                result["errors"].append(f"Target device {to_device_id} not found")
                result["status"] = "failed"
                return result
            
            print(f"[Handoff] Initiating handoff: {from_device_id} -> {to_device_id}")
            
            # Step 1: Package sensory buffer/context from source device
            try:
                context_package = self._package_sensory_buffer(from_device_id, minutes=5)
                result["context_package"] = {
                    "entry_count": context_package["entry_count"],
                    "time_window": context_package["time_window_minutes"]
                }
                print(f"[Handoff] Packaged {context_package['entry_count']} entries from {from_device_id}")
            except Exception as e:
                result["errors"].append(f"Failed to package context: {str(e)}")
                context_package = None
            
            # Step 2: Push context to target device
            if context_package:
                try:
                    success = self._push_context_to_device(to_device_id, context_package)
                    result["context_transferred"] = success
                    if not success:
                        result["errors"].append("Context push failed")
                except Exception as e:
                    result["errors"].append(f"Context push error: {str(e)}")
            
            # Step 3: Emit hardware shift event if target is ROG Ally
            try:
                if self._is_rog_ally(to_device_id, to_device.get("device_type")):
                    HardwareResourceManager.emit_hardware_shift_event(
                        to_device_id=to_device_id,
                        to_device_type=to_device.get("device_type", DEVICE_MOBILE)
                    )
                    result["hardware_shift_emitted"] = True
                    result["hardware_mode"] = "power_saver"
                    print(f"[Handoff] Emitted hardware shift event for ROG Ally")
            except Exception as e:
                result["errors"].append(f"Hardware shift event error: {str(e)}")
            
            # Step 4: Log the handoff
            self.db.log_sync(
                device_id=to_device_id,
                action="handoff_received",
                details=f"From: {from_device_id}, Entries: {context_package['entry_count'] if context_package else 0}"
            )
            
            # Step 5: Update device heartbeats to reflect active device change
            self.heartbeat_mgr.heartbeat(to_device_id, current_mode="active")
            
            # Final status
            if result["context_transferred"] and not result["errors"]:
                result["status"] = "success"
            elif result["context_transferred"]:
                result["status"] = "partial_success"
            else:
                result["status"] = "failed"
            
            # Log to memory
            save_log('device_handoff', {
                'from_device': from_device_id,
                'to_device': to_device_id,
                'status': result["status"],
                'context_transferred': result["context_transferred"],
                'hardware_shift_emitted': result["hardware_shift_emitted"],
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"[Handoff] Handoff complete: {result['status']}")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Handoff failed: {str(e)}")
            print(f"[Handoff] Handoff error: {e}")
            save_log('device_handoff_error', {
                'from_device': from_device_id,
                'to_device': to_device_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return result


class LaunchSequence:

    """Automated workspace preparation."""
    
    def __init__(self):
        self.work_project = os.getenv("LOVE_WORK_PROJECT")
        self.dotnet_project = os.getenv("LOVE_DOTNET_PROJECT")
        self.flutter_project = os.getenv("LOVE_FLUTTER_PROJECT")
    
    def prepare_for_work(self) -> Dict[str, Any]:
        """Launch complete work environment."""
        results = []
        
        # Open VS Code with work project
        if self.work_project and Path(self.work_project).exists():
            result = self._open_vscode(self.work_project)
            results.append({"action": "VS Code", "result": result})
        
        # Start .NET backend if configured
        if self.dotnet_project and Path(self.dotnet_project).exists():
            result = self._start_dotnet(self.dotnet_project)
            results.append({"action": ".NET Backend", "result": result})
        
        # Open documentation
        result = self._open_documentation()
        results.append({"action": "Documentation", "result": result})
        
        # Notify user
        love_message = self._generate_launch_message(results)
        
        return {
            "launched": True,
            "actions": results,
            "love_message": love_message
        }
    
    def _open_vscode(self, project_path: str) -> bool:
        """Open VS Code with project."""
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["code", project_path], shell=True)
            else:
                subprocess.Popen(["code", project_path])
            return True
        except Exception as e:
            print(f"[Launch] Failed to open VS Code: {e}")
            return False
    
    def _start_dotnet(self, project_path: str) -> bool:
        """Start .NET backend in terminal."""
        try:
            if platform.system() == "Windows":
                subprocess.Popen(
                    ["start", "cmd", "/k", f"cd {project_path} && dotnet run"],
                    shell=True
                )
            else:
                subprocess.Popen(
                    ["gnome-terminal", "--", "bash", "-c", f"cd {project_path} && dotnet run"]
                )
            return True
        except Exception as e:
            print(f"[Launch] Failed to start .NET: {e}")
            return False
    
    def _open_documentation(self) -> bool:
        """Open project documentation in browser."""
        try:
            import webbrowser
            docs_url = os.getenv("LOVE_DOCS_URL", "https://docs.google.com")
            webbrowser.open(docs_url)
            return True
        except Exception as e:
            print(f"[Launch] Failed to open docs: {e}")
            return False
    
    def _generate_launch_message(self, results: List[Dict]) -> str:
        """Generate LOVE's launch confirmation message."""
        successful = sum(1 for r in results if r.get("result"))
        total = len(results)
        
        if successful == total:
            return f"Workspace ready. Opened {successful} components. Your .NET backend is spinning up—give it 30 seconds. What are we building today?"
        else:
            return f"Launched {successful}/{total} components. Some things didn't open—probably already running or paths need checking. Want me to investigate?"


# Environment Intelligence public functions
def get_hardware_profile() -> Dict[str, Any]:
    """Get hardware info and recommended power profile."""
    hw_info = HardwareResourceManager.detect_hardware()
    profile = HardwareResourceManager.get_power_profile(hw_info.get("inferred_type"))
    
    return {
        "hardware": hw_info,
        "power_profile": profile.to_dict(),
        "recommended_llm_params": HardwareResourceManager.get_llm_params(profile)
    }


def launch_work_sequence() -> Dict[str, Any]:
    """Execute 'Hey Love, prepare for work' sequence."""
    launcher = LaunchSequence()
    return launcher.prepare_for_work()


# Public API functions
def sync_heartbeat(device_id: str, mode: str = None) -> Dict[str, Any]:
    """Public function for device heartbeat."""
    mgr = get_heartbeat_manager()
    return mgr.heartbeat(device_id, mode)

def register_device(device_id: str, device_type: str, name: str = None, ip: str = None):
    """Public function to register a device."""
    mgr = get_heartbeat_manager()
    mgr.register_device(device_id, device_type, name, ip)

def get_sync_status() -> Dict[str, Any]:
    """Get overall sync status."""
    mgr = get_heartbeat_manager()
    devices = mgr.get_all_devices()
    active = mgr.get_active_device()
    
    return {
        "sync_active": len(devices) > 0,
        "device_count": len(devices),
        "active_device": active,
        "all_devices": devices,
        "database_path": str(SYNC_DB_PATH)
    }

def push_sync_entry(device_id: str, category: str, content: str, metadata: Dict = None) -> str:
    """Push an entry to sync."""
    mem = get_sync_memory()
    return mem.sync_entry(device_id, category, content, metadata)

def pull_sync_entries(device_id: str, since: str = None) -> List[Dict[str, Any]]:
    """Pull unsynced entries for a device."""
    mem = get_sync_memory()
    return mem.get_unsynced_entries(device_id, since)

def get_personality_modifications(device_id: str) -> Dict[str, Any]:
    """Get personality modifications for a device."""
    adapter = get_personality_adapter()
    return adapter.get_personality_for_device(device_id)

def trigger_handoff(from_device_id: str, to_device_id: str) -> Dict[str, Any]:
    """
    Public API to trigger a cross-device handoff.
    
    This is the "Follow Me" protocol - when a user switches devices,
    LOVE seamlessly transfers context and adjusts hardware resources.
    
    Args:
        from_device_id: The device we're handing off from
        to_device_id: The device we're handing off to
        
    Returns:
        Dict with handoff status, context transferred, and any errors
    """
    mgr = get_handoff_manager()
    return mgr.trigger_handoff(from_device_id, to_device_id)
