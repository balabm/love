import logging

from core.central_logger import get_logger

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

logger = get_logger(__name__)

def reconcile_state_conflicts(current_state: dict) -> dict:
    """Detect and fix obvious paradoxes in user state JSON."""
    state = current_state.copy()
    
    # Rule 1: Can't be sleeping with device active
    activity = state.get("activity", "idle")
    device_active = state.get("device_active", False)
    if activity == "sleeping" and device_active:
        state["activity"] = "idle"
        logger.warning("Fixed: activity changed from 'sleeping' to 'idle' (device was active)")
    
    # Rule 2: Work hours cannot exceed 24 in a day
    work_hours = state.get("work_hours_logged", 0)
    if work_hours > 24:
        state["work_hours_logged"] = 0
        logger.error(f"Invalid work_hours_logged ({work_hours} > 24), reset to 0")
    
    # Rule 3: Stress level must be between 0 and 10
    stress = state.get("stress_level", 5)
    if stress > 10:
        state["stress_level"] = 10
        logger.info(f"Clamped stress_level from {stress} to 10")
    elif stress < 0:
        state["stress_level"] = 0
        logger.info(f"Clamped stress_level from {stress} to 0")
    
    # Publish to neural bus
    if NEURAL_BUS_AVAILABLE:
        try:
            bus = get_neural_bus()
            bus.publish(
                domain="reality",
                event_type="state_reconciled",
                payload={"state": state, "conflicts_fixed": True},
                source_module="reality_check",
                priority=EventPriority.NORMAL
            )
        except Exception as e:
            logger.error(f"Neural bus publish error: {e}")
    
    return state


def start_reality_check():
    """Start the reality check system."""
    logger.info("Reality Check system initialized")
    return True
