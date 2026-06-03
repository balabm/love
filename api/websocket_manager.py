"""
LOVE WebSocket Telemetry Manager - Wave 16
Real-time event streaming from NeuralBus to React UI.

This manager:
- Subscribes to NeuralBus events across all relevant domains
- Broadcasts events to connected WebSocket clients
- Handles disconnections gracefully
- Provides structured payloads with type field for frontend parsing
- Manages connection lifecycle and error handling
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field, asdict

from core.neural_bus import get_neural_bus, NeuralEvent, EventDomain
from core.execution_guard import log_error

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TelemetryPayload:
    """Structured payload for WebSocket clients."""
    type: str  # intervention, health_update, market_alert, etc.
    domain: str
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    source: str
    priority: int
    event_id: str

    def to_dict(self) -> Dict:
        return asdict(self)


class TelemetryManager:
    """
    Manages WebSocket connections and broadcasts NeuralBus events to clients.
    
    This is the bridge between LOVE's nervous system (NeuralBus) and the React UI.
    Every event on the bus is transformed into a telemetry payload and pushed to
    all connected clients in real-time.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True
        
        # Connection management
        self.active_connections: Dict[str, WebSocket] = {}  # connection_id -> WebSocket
        self.connection_metadata: Dict[str, Dict] = {}  # connection_id -> metadata
        
        # NeuralBus subscription
        self.neural_bus = None
        self.subscription_id = "telemetry_manager"
        self._streaming_task: Optional[asyncio.Task] = None
        self._is_streaming = False
        
        # Configuration
        self.subscribed_domains = [
            EventDomain.CONSCIOUSNESS.value,
            EventDomain.EMOTION.value,
            EventDomain.HEALTH.value,
            EventDomain.MEMORY.value,
            EventDomain.LEARNING.value,
            EventDomain.RESEARCH.value,
            EventDomain.SELF_EVOLUTION.value,
            EventDomain.DEVICE.value,
            EventDomain.USER.value,
            EventDomain.SYSTEM.value,
            EventDomain.TEACHING.value,
            EventDomain.PREDICTION.value,
            EventDomain.ACTION.value,
        ]
        
        # Statistics
        self._stats = {
            "connections_total": 0,
            "events_broadcast": 0,
            "events_filtered": 0,
            "disconnections": 0,
            "errors": 0,
        }
        
        logger.info("[TelemetryManager] Initialized")

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """
        Accept a WebSocket connection and add to active connections.
        
        Args:
            websocket: The WebSocket connection
            client_id: Optional client identifier (generated if not provided)
            
        Returns:
            The connection ID
        """
        await websocket.accept()
        
        # Generate connection ID if not provided
        if not client_id:
            client_id = f"client_{datetime.now().timestamp()}_{id(websocket)}"
        
        # Store connection
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "client_id": client_id,
        }
        
        self._stats["connections_total"] += 1
        logger.info(f"[TelemetryManager] Client connected: {client_id}")
        
        # Send welcome message
        await self._send_to_client(client_id, {
            "type": "connection_established",
            "data": {
                "connection_id": client_id,
                "subscribed_domains": self.subscribed_domains,
                "timestamp": datetime.now().isoformat(),
            }
        })
        
        # Start streaming if not already running
        if not self._is_streaming:
            await self.start_streaming()
        
        return client_id

    def disconnect(self, client_id: str):
        """
        Remove a client connection gracefully.
        
        Args:
            client_id: The connection ID to disconnect
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                # Don't close here - let the client close or handle in exception
                del self.active_connections[client_id]
                del self.connection_metadata[client_id]
                self._stats["disconnections"] += 1
                logger.info(f"[TelemetryManager] Client disconnected: {client_id}")
            except Exception as e:
                logger.error(f"[TelemetryManager] Error disconnecting {client_id}: {e}")

    async def broadcast_event(self, payload: Dict[str, Any]):
        """
        Broadcast an event payload to all connected WebSocket clients.

        Args:
            payload: The event payload to broadcast
        """
        if not self.active_connections:
            return

        # Snapshot current clients to avoid dict-mutation races
        clients_snapshot = list(self.active_connections.items())
        disconnected_clients = []
        send_tasks = []
        task_to_client: dict = {}

        for client_id, websocket in clients_snapshot:
            try:
                task = asyncio.create_task(self._send_to_client(client_id, payload))
                send_tasks.append(task)
                task_to_client[id(task)] = client_id
            except Exception as e:
                logger.warning(f"[TelemetryManager] Error preparing send to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Execute all sends concurrently
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)

            # Track successful broadcasts
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            self._stats["events_broadcast"] += success_count

            # Log errors
            for task, result in zip(send_tasks, results):
                if isinstance(result, Exception):
                    client_id = task_to_client.get(id(task), "unknown")
                    if isinstance(result, (ConnectionResetError, BrokenPipeError)):
                        logger.info(f"[TelemetryManager] Client {client_id} disconnected during broadcast")
                    else:
                        logger.warning(f"[TelemetryManager] Broadcast error to {client_id}: {type(result).__name__}")
                    self._stats["errors"] += 1

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def _send_to_client(self, client_id: str, payload: Dict[str, Any]) -> bool:
        """
        Send a payload to a specific client.

        Args:
            client_id: The connection ID
            payload: The payload to send

        Returns:
            True if successful, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[client_id]
            # Fast pre-check: skip if socket already closing/closed
            if hasattr(websocket, "client_state") and websocket.client_state.value != 1:
                self.disconnect(client_id)
                return False
            await asyncio.wait_for(websocket.send_json(payload), timeout=3)
            return True
        except asyncio.TimeoutError:
            logger.warning(f"[TelemetryManager] Send timeout to {client_id} — disconnecting stale connection")
            self.disconnect(client_id)
            return False
        except WebSocketDisconnect:
            self.disconnect(client_id)
            return False
        except (ConnectionResetError, BrokenPipeError, RuntimeError):
            # Socket closed by client — clean disconnect, no error log needed
            self.disconnect(client_id)
            return False
        except Exception as e:
            logger.warning(f"[TelemetryManager] Error sending to {client_id}: {type(e).__name__}")
            self.disconnect(client_id)
            return False

    async def start_streaming(self):
        """
        Start the background task that subscribes to NeuralBus and streams events.
        """
        if self._is_streaming:
            logger.warning("[TelemetryManager] Streaming already active")
            return
        
        self._is_streaming = True
        self._streaming_task = asyncio.create_task(self._stream_neural_bus())
        logger.info("[TelemetryManager] Started NeuralBus streaming")

    async def stop_streaming(self):
        """
        Stop the background streaming task.
        """
        if not self._is_streaming:
            return
        
        self._is_streaming = False
        if self._streaming_task:
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="api.websocket_manager")
        
        # Unsubscribe from NeuralBus
        if self.neural_bus:
            self.neural_bus.unsubscribe(self.subscription_id)
        
        logger.info("[TelemetryManager] Stopped NeuralBus streaming")

    async def _stream_neural_bus(self):
        """
        Background task that subscribes to NeuralBus and broadcasts events.
        
        This runs continuously, listening to the NeuralBus and forwarding
        events to all connected WebSocket clients.
        """
        try:
            # Get NeuralBus instance
            self.neural_bus = get_neural_bus()
            
            # Subscribe to all relevant domains
            self.neural_bus.subscribe(
                subscriber_id=self.subscription_id,
                domains=self.subscribed_domains,
                callback=self._handle_neural_event,
                is_async=True,
            )
            
            logger.info(f"[TelemetryManager] Subscribed to domains: {self.subscribed_domains}")
            
            # Keep the task alive
            while self._is_streaming:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("[TelemetryManager] Streaming task cancelled")
            raise
        except Exception as e:
            logger.error(f"[TelemetryManager] Streaming error: {e}", exc_info=True)
            self._stats["errors"] += 1
            # Retry after delay
            await asyncio.sleep(5)
            if self._is_streaming:
                self._streaming_task = asyncio.create_task(self._stream_neural_bus())

    async def _handle_neural_event(self, event: NeuralEvent):
        """
        Handle an event from the NeuralBus and broadcast to clients.
        
        Args:
            event: The NeuralEvent to process
        """
        try:
            # Transform NeuralEvent to TelemetryPayload
            telemetry = TelemetryPayload(
                type=self._map_event_to_type(event),
                domain=event.domain,
                event_type=event.event_type,
                data=event.payload,
                timestamp=event.iso_time,
                source=event.source_module,
                priority=event.priority,
                event_id=event.id,
            )
            
            # Broadcast to all clients
            await self.broadcast_event(telemetry.to_dict())
            
        except Exception as e:
            logger.error(f"[TelemetryManager] Error handling event: {e}", exc_info=True)
            self._stats["errors"] += 1

    def _map_event_to_type(self, event: NeuralEvent) -> str:
        """
        Map NeuralBus events to frontend-friendly type strings.
        
        Args:
            event: The NeuralEvent to map
            
        Returns:
            A type string for the frontend
        """
        # Domain-based mapping
        domain_type_map = {
            EventDomain.CONSCIOUSNESS.value: "consciousness_update",
            EventDomain.EMOTION.value: "emotion_update",
            EventDomain.HEALTH.value: "health_update",
            EventDomain.MEMORY.value: "memory_update",
            EventDomain.LEARNING.value: "learning_update",
            EventDomain.RESEARCH.value: "research_update",
            EventDomain.SELF_EVOLUTION.value: "evolution_update",
            EventDomain.DEVICE.value: "device_update",
            EventDomain.USER.value: "user_update",
            EventDomain.SYSTEM.value: "system_update",
            EventDomain.TEACHING.value: "teaching_update",
            EventDomain.PREDICTION.value: "prediction_update",
            EventDomain.ACTION.value: "action_update",
        }
        
        # Event-specific mapping for monitoring
        if event.domain == EventDomain.SELF_EVOLUTION.value:
            if event.event_type == "cognitive_load_assessed":
                return "monitoring_update"
            if event.event_type == "anomaly_detected":
                return "monitoring_alert"

        # Event type specific overrides
        event_type_map = {
            "intervention": "intervention",
            "intervention_triggered": "intervention",
            "health_alert": "health_alert",
            "market_signal": "market_alert",
            "trade_signal": "market_alert",
            "portfolio_update": "market_update",
            "mood_change": "emotion_update",
            "emotion_detected": "emotion_update",
            "memory_consolidated": "memory_update",
            "learning_progress": "learning_update",
            "task_completed": "task_update",
            "goal_achieved": "achievement",
            "system_warning": "system_alert",
            "error_occurred": "error",
        }
        
        # Check event type map first
        if event.event_type in event_type_map:
            return event_type_map[event.event_type]
        
        # Fall back to domain mapping
        return domain_type_map.get(event.domain, "general_update")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get telemetry manager statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            **self._stats,
            "active_connections": len(self.active_connections),
            "is_streaming": self._is_streaming,
            "subscribed_domains": self.subscribed_domains,
        }

    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.
        
        Args:
            client_id: The connection ID
            
        Returns:
            Connection metadata or None if not found
        """
        return self.connection_metadata.get(client_id)


# Global instance
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager() -> TelemetryManager:
    """
    Get the global TelemetryManager instance.
    
    Returns:
        The singleton TelemetryManager instance
    """
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager
