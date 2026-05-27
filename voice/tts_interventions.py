import asyncio
import logging

logger = logging.getLogger(__name__)

INTERVENTIONS = {
    "9_HOUR_LIMIT": "Karthi. Nine hours. Drop the keyboard. The brain is cooked, the code can wait. Stand up.",
    "HIGH_STRESS": "I'm seeing red across the board. Step away from the IDE. Let's get some air.",
}

async def trigger_hype_intervention(trigger_type: str):
    if trigger_type not in INTERVENTIONS:
        logger.warning(f"Unknown intervention trigger: {trigger_type}")
        return
    
    text = INTERVENTIONS[trigger_type]
    logger.info(f"Triggering intervention: {trigger_type}")
    
    try:
        from voice.tts import speak
        asyncio.create_task(speak(text, block=False))
    except ImportError:
        logger.warning("TTS module unavailable, intervention not spoken")
