import logging

def evaluate_utility(task_priority: int, compute_cost: int, user_energy: int, user_stress: int) -> bool:
    utility = (task_priority * 2) - compute_cost - (user_stress / 2)
    threshold = 10 if user_energy < 4 else 5
    if utility >= threshold:
        logging.info(f"Task allowed: Utility {utility:.1f} >= Threshold {threshold}")
        return True
    else:
        logging.info(f"Task aborted: Utility {utility:.1f} < Threshold {threshold}")
        return False
