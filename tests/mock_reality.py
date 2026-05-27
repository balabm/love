import asyncio

class RealitySimulator:
    async def trigger_work_burnout(self):
        from core.neural_bus import NeuralBus
        await NeuralBus.publish(
            domain="user",
            event_type="work_status",
            payload={"hours_worked": 9.5, "stress_level": 9, "device_active": True}
        )

    async def trigger_market_crash(self):
        from core.neural_bus import NeuralBus
        await NeuralBus.publish(
            domain="finance",
            event_type="market_event",
            payload={"asset": "BTC", "change_pct": -5.0, "duration_minutes": 10}
        )

    async def trigger_deep_flow(self):
        from core.neural_bus import NeuralBus
        await NeuralBus.publish(
            domain="user",
            event_type="activity",
            payload={"activity": "coding", "typing_speed": "high", "heart_rate": "stable", "energy": 8}
        )
