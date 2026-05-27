import logging

# Neural Bus integration
try:
    from core.neural_bus import get_neural_bus, EventPriority
    NEURAL_BUS_AVAILABLE = True
except ImportError:
    NEURAL_BUS_AVAILABLE = False

def evaluate_utility(task_priority: int, compute_cost: int, user_energy: int, user_stress: int) -> bool:
    utility = (task_priority * 2) - compute_cost - (user_stress / 2)
    threshold = 10 if user_energy < 4 else 5
    if utility >= threshold:
        logging.info(f"Task allowed: Utility {utility:.1f} >= Threshold {threshold}")
        
        # Publish to neural bus
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="axiology",
                    event_type="utility_evaluated",
                    payload={
                        "allowed": True,
                        "utility": utility,
                        "threshold": threshold,
                        "task_priority": task_priority,
                        "user_energy": user_energy,
                        "user_stress": user_stress
                    },
                    source_module="axiological_engine",
                    priority=EventPriority.NORMAL
                )
            except Exception as e:
                logging.error(f"Neural bus publish error: {e}")
        
        return True
    else:
        logging.info(f"Task aborted: Utility {utility:.1f} < Threshold {threshold}")
        
        # Publish to neural bus
        if NEURAL_BUS_AVAILABLE:
            try:
                bus = get_neural_bus()
                bus.publish(
                    domain="axiology",
                    event_type="utility_evaluated",
                    payload={
                        "allowed": False,
                        "utility": utility,
                        "threshold": threshold,
                        "task_priority": task_priority,
                        "user_energy": user_energy,
                        "user_stress": user_stress
                    },
                    source_module="axiological_engine",
                    priority=EventPriority.NORMAL
                )
            except Exception as e:
                logging.error(f"Neural bus publish error: {e}")
        
        return False
