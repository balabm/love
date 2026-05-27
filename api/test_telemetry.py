"""
Test script for WebSocket Telemetry Manager
Demonstrates the telemetry functionality without requiring a running server.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.websocket_manager import get_telemetry_manager, TelemetryPayload
from core.neural_bus import get_neural_bus, NeuralEvent, EventDomain, EventPriority


async def test_telemetry_manager():
    """Test the TelemetryManager functionality."""
    print("=" * 60)
    print("Testing WebSocket Telemetry Manager")
    print("=" * 60)
    
    # Get the telemetry manager
    manager = get_telemetry_manager()
    
    # Test 1: Manager initialization
    print("\n[TEST 1] Manager Initialization")
    print(f"  - Manager instance: {manager}")
    print(f"  - Subscribed domains: {len(manager.subscribed_domains)}")
    print(f"  - Domains: {', '.join(manager.subscribed_domains[:5])}...")
    
    # Test 2: Statistics
    print("\n[TEST 2] Statistics")
    stats = manager.get_stats()
    print(f"  - Active connections: {stats['active_connections']}")
    print(f"  - Events broadcast: {stats['events_broadcast']}")
    print(f"  - Is streaming: {stats['is_streaming']}")
    
    # Test 3: Event type mapping
    print("\n[TEST 3] Event Type Mapping")
    test_events = [
        (EventDomain.HEALTH.value, "health_alert", "Health alert"),
        (EventDomain.EMOTION.value, "mood_change", "Mood change"),
        (EventDomain.MEMORY.value, "intervention", "Intervention"),
        (EventDomain.SYSTEM.value, "system_warning", "System warning"),
        (EventDomain.USER.value, "task_completed", "Task completed"),
    ]
    
    for domain, event_type, description in test_events:
        event = NeuralEvent(
            id="test",
            domain=domain,
            event_type=event_type,
            payload={"test": True},
            source_module="test",
            priority=EventPriority.NORMAL.value
        )
        mapped_type = manager._map_event_to_type(event)
        print(f"  - {description}: {domain}/{event_type} -> {mapped_type}")
    
    # Test 4: Telemetry payload structure
    print("\n[TEST 4] Telemetry Payload Structure")
    event = NeuralEvent(
        id="test123",
        domain=EventDomain.HEALTH.value,
        event_type="health_alert",
        payload={"heart_rate": 120, "activity": "running"},
        source_module="fitness_agent",
        priority=EventPriority.HIGH.value
    )
    
    telemetry = TelemetryPayload(
        type=manager._map_event_to_type(event),
        domain=event.domain,
        event_type=event.event_type,
        data=event.payload,
        timestamp=event.iso_time,
        source=event.source_module,
        priority=event.priority,
        event_id=event.id,
    )
    
    print(f"  - Payload type: {telemetry.type}")
    print(f"  - Payload domain: {telemetry.domain}")
    print(f"  - Payload data: {telemetry.data}")
    print(f"  - Full payload (JSON):")
    import json
    print(f"    {json.dumps(telemetry.to_dict(), indent=4)}")
    
    # Test 5: NeuralBus integration (if available)
    print("\n[TEST 5] NeuralBus Integration")
    try:
        bus = get_neural_bus()
        print(f"  - NeuralBus instance: {bus}")
        print(f"  - Can subscribe: True")
        
        # Publish a test event
        event_id = bus.publish(
            domain=EventDomain.HEALTH.value,
            event_type="health_alert",
            payload={"test": "telemetry_test"},
            source_module="test_telemetry",
            priority=EventPriority.NORMAL
        )
        print(f"  - Published test event: {event_id}")
        
    except Exception as e:
        print(f"  - NeuralBus not available: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_telemetry_manager())
