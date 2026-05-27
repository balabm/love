import asyncio
import functools
import logging

from core.central_logger import get_logger

logger = get_logger(__name__)


async def simulate_outcome(action_description: str, current_context: dict) -> bool:
    from core.llm import get_reasoning_llm

    try:
        llm = get_reasoning_llm(temperature=0.1)
        prompt = f"""Action: {action_description}
Context: {current_context}
Question: Will executing this action cause data loss, financial ruin, or interrupt the user's critical workflow?
Answer ONLY with 'SAFE' or 'DANGER'."""
        response = await llm.ainvoke(prompt)
        result = "DANGER" not in response.upper()
        logger.info(f"Causal check for '{action_description}': {'SAFE' if result else 'DANGER'}")
        return result
    except Exception as e:
        logger.warning(f"Causal guardrail failed: {e}. Allowing execution (fail-safe).")
        return True


def requires_causal_check(action_name: str):
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {"args": args, "kwargs": kwargs}
            if not await simulate_outcome(action_name, context):
                logger.error(f"Causal Guardrail Blocked Execution: {action_name}")
                raise RuntimeError(f"Causal Guardrail Blocked Execution: {action_name}")
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = {"args": args, "kwargs": kwargs}
            if not asyncio.run(simulate_outcome(action_name, context)):
                logger.error(f"Causal Guardrail Blocked Execution: {action_name}")
                raise RuntimeError(f"Causal Guardrail Blocked Execution: {action_name}")
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def start_guardrail():
    """Start the causal guardrail system."""
    logger.info("Causal Guardrail system initialized")
    return True
