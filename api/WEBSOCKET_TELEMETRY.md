# WebSocket Telemetry Stream

## Overview

The WebSocket telemetry stream provides real-time event streaming from LOVE's NeuralBus to connected clients (e.g., React UI). This enables live updates for interventions, state changes, market alerts, and other system events.

## Endpoint

**WebSocket URL:** `ws://localhost:8000/telemetry`

Optional query parameter:
- `client_id`: Custom client identifier for connection tracking

## Connection Example

### JavaScript/React

```javascript
const ws = new WebSocket('ws://localhost:8000/telemetry?client_id=my-react-app');

ws.onopen = () => {
  console.log('Connected to LOVE telemetry stream');
};

ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  // Handle different event types
  switch (payload.type) {
    case 'intervention':
      console.log('Intervention:', payload.data);
      break;
    case 'health_alert':
      console.log('Health alert:', payload.data);
      break;
    case 'market_alert':
      console.log('Market alert:', payload.data);
      break;
    case 'emotion_update':
      console.log('Emotion update:', payload.data);
      break;
    default:
      console.log('Event:', payload.type, payload.data);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from telemetry stream');
};
```

### Python

```python
import asyncio
import websockets
import json

async def listen_telemetry():
    uri = "ws://localhost:8000/telemetry?client_id=python-client"
    async with websockets.connect(uri) as websocket:
        print("Connected to LOVE telemetry stream")
        
        while True:
            message = await websocket.recv()
            payload = json.loads(message)
            print(f"Event: {payload['type']}", payload['data'])

asyncio.run(listen_telemetry())
```

## Payload Structure

All payloads follow this structure:

```json
{
  "type": "event_type",
  "domain": "neural_bus_domain",
  "event_type": "original_event_type",
  "data": {
    // Event-specific data
  },
  "timestamp": "2024-01-01T12:00:00.000000",
  "source": "source_module",
  "priority": 2,
  "event_id": "abc123def456"
}
```

## Event Types

The telemetry manager maps NeuralBus events to frontend-friendly types:

| NeuralBus Event | Telemetry Type | Description |
|----------------|----------------|-------------|
| `intervention` | `intervention` | LOVE intervention triggered |
| `health_alert` | `health_alert` | Health-related alert |
| `market_signal` | `market_alert` | Market/trading signal |
| `trade_signal` | `market_alert` | Trading opportunity |
| `mood_change` | `emotion_update` | User mood detected |
| `emotion_detected` | `emotion_update` | Emotion detected |
| `memory_consolidated` | `memory_update` | Memory consolidation event |
| `learning_progress` | `learning_update` | Learning progress update |
| `task_completed` | `task_update` | Task completion |
| `goal_achieved` | `achievement` | Goal achieved |
| `system_warning` | `system_alert` | System warning |
| `error_occurred` | `error` | Error occurred |

Domain-based fallbacks:
- `consciousness` → `consciousness_update`
- `emotion` → `emotion_update`
- `health` → `health_update`
- `memory` → `memory_update`
- `learning` → `learning_update`
- `research` → `research_update`
- `self_evolution` → `evolution_update`
- `device` → `device_update`
- `user` → `user_update`
- `system` → `system_update`
- `teaching` → `teaching_update`
- `prediction` → `prediction_update`
- `action` → `action_update`

## Client Messages

Clients can send messages to the WebSocket:

### Ping/Pong

```javascript
ws.send('ping');  // Server responds with 'pong'
```

### Get Statistics

```javascript
ws.send('stats');  // Server responds with telemetry stats
```

Response:
```json
{
  "type": "stats",
  "data": {
    "connections_total": 5,
    "events_broadcast": 1234,
    "events_filtered": 56,
    "disconnections": 2,
    "errors": 0,
    "active_connections": 3,
    "is_streaming": true,
    "subscribed_domains": [...]
  }
}
```

### Subscribe to Domains (Future)

```javascript
ws.send('subscribe:health,emotion,finance');
```

## REST API

### Get Telemetry Stats

**Endpoint:** `GET /neural/telemetry/stats`

Returns current telemetry manager statistics without WebSocket connection.

```bash
curl http://localhost:8000/neural/telemetry/stats
```

## Subscribed Domains

The telemetry manager subscribes to these NeuralBus domains by default:

- `consciousness` - Consciousness state changes
- `emotion` - Emotional state updates
- `health` - Health and fitness events
- `memory` - Memory consolidation events
- `learning` - Learning progress
- `research` - Research engine updates
- `self_evolution` - Self-evolution events
- `device` - Device status changes
- `user` - User-related events
- `system` - System events
- `teaching` - Teaching/learning events
- `prediction` - Prediction events
- `action` - Action execution events

## Error Handling

The telemetry manager handles:

- **WebSocket disconnections**: Automatically removes disconnected clients
- **Send failures**: Logs errors and removes failed connections
- **NeuralBus errors**: Continues streaming on errors with retry logic
- **Connection tracking**: Maintains metadata for each connection

## Production Considerations

1. **Connection Limits**: Monitor active connections to prevent resource exhaustion
2. **Event Filtering**: Implement client-side filtering to reduce bandwidth
3. **Reconnection**: Implement exponential backoff for reconnection attempts
4. **Authentication**: Add authentication for production deployments
5. **Rate Limiting**: Consider rate limiting for high-frequency events

## Example Use Cases

### Real-time Intervention Display

```javascript
ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  if (payload.type === 'intervention') {
    showInterventionBanner(payload.data);
  }
};
```

### Live Health Monitoring

```javascript
ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  if (payload.type === 'health_alert') {
    updateHealthDashboard(payload.data);
  }
};
```

### Market Alert Feed

```javascript
ws.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  if (payload.type === 'market_alert') {
    addMarketAlertToFeed(payload.data);
  }
};
```

## Troubleshooting

### Connection Refused

Ensure the LOVE API server is running:
```bash
python api/main.py
```

### No Events Received

1. Check that NeuralBus is publishing events
2. Verify the telemetry manager is streaming: call `/neural/telemetry/stats`
3. Check browser console for WebSocket errors

### Connection Drops

1. Check network stability
2. Implement reconnection logic in client
3. Check server logs for errors

## Architecture

```
NeuralBus (Event Publisher)
    ↓
TelemetryManager (Subscriber)
    ↓
WebSocket Broadcast
    ↓
Connected Clients (React UI, etc.)
```

The TelemetryManager acts as a bridge between LOVE's nervous system (NeuralBus) and external clients, transforming internal events into structured telemetry payloads.
