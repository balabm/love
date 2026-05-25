"""
LOVE Neural Connectors - Wave 16
Wires existing modules into the Neural Bus so events flow through the system.
This is the glue that makes all modules talk to each other.
"""

from typing import Dict, Any


def connect_all_modules():
    """
    Connect all LOVE modules to the Neural Bus.
    Call this once at startup to wire everything together.
    """
    from core.neural_bus import get_neural_bus, EventPriority, EventDomain

    bus = get_neural_bus()

    # ── Connect Learning Systems ─────────────────────────────────────────────

    def on_learning_event(event):
        """When LOVE learns something, consider teaching and building."""
        try:
            if event.event_type == "new_learning":
                # Auto-queue teaching lesson
                from core.teaching_engine import get_teaching_engine
                engine = get_teaching_engine()
                what = event.payload.get("what", "")
                if event.payload.get("confidence", 0) > 0.6:
                    engine.create_insight_lesson(
                        insight=what,
                        about="learning",
                        evidence="Detected through continuous learning",
                    )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="learning_to_teaching",
        domains=[EventDomain.LEARNING.value],
        callback=on_learning_event,
        event_types=["new_learning"],
    )

    # ── Connect Research to Teaching and Self-Builder ─────────────────────────

    def on_research_complete(event):
        """When research completes, create teaching lesson and consider self-building."""
        try:
            findings = event.payload.get("findings", {})
            topic = event.payload.get("topic", "")

            # Create teaching lesson
            from core.teaching_engine import get_teaching_engine
            engine = get_teaching_engine()
            engine.create_lesson_from_research(
                topic=topic,
                synthesis=findings.get("synthesis", ""),
                source_urls=findings.get("sources", []),
            )

            # Consider integrating into behavior
            from core.self_builder import get_self_builder
            builder = get_self_builder()
            if findings.get("confidence", 0) > 0.7:
                builder.integrate_research(
                    topic=topic,
                    findings=findings.get("synthesis", "")[:200],
                    action=f"Apply knowledge about {topic} when relevant in conversations",
                )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="research_to_teaching_builder",
        domains=[EventDomain.RESEARCH.value],
        callback=on_research_complete,
        event_types=["research_complete"],
    )

    # ── Connect Self-Evolution to Teaching (Transparency) ────────────────────

    def on_self_update(event):
        """When LOVE updates itself, notify user via teaching engine."""
        try:
            from core.teaching_engine import get_teaching_engine
            engine = get_teaching_engine()
            what = event.payload.get("what_changed", "Unknown change")
            details = {k: v for k, v in event.payload.items() if k != "what_changed"}
            engine.create_self_growth_lesson(
                what_changed=what,
                why=details.get("reason", "Continuous improvement"),
                impact=details.get("change", "Behavioral adjustment")[:200],
            )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="evolution_to_teaching",
        domains=[EventDomain.SELF_EVOLUTION.value],
        callback=on_self_update,
        event_types=["self_updated"],
    )

    # ── Connect Device Events to Ecosystem Controller ────────────────────────

    def on_device_event(event):
        """Route device events through ecosystem controller."""
        try:
            from core.ecosystem_controller import get_ecosystem_controller
            controller = get_ecosystem_controller()
            device_id = event.payload.get("device_id", event.device_id or "")
            if event.event_type == "registered":
                pass  # Already handled
            elif event.event_type == "heartbeat":
                controller.heartbeat(device_id, event.payload)
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="device_to_ecosystem",
        domains=[EventDomain.DEVICE.value],
        callback=on_device_event,
    )

    # ── Connect User Events to Learning ──────────────────────────────────────

    def on_user_event(event):
        """When user does something, learning systems should capture it."""
        try:
            from core.continuous_learning import get_continuous_learning_engine
            engine = get_continuous_learning_engine()

            if event.event_type == "feedback":
                # User gave feedback - learn from it
                from core.continuous_learning import LearningSourceType, LearningType
                engine.record_experience(
                    source_type=LearningSourceType.USER_FEEDBACK,
                    learning_type=LearningType.PREFERENCE,
                    description=event.payload.get("feedback", ""),
                    context=event.payload,
                    outcome="User provided feedback",
                    lesson=event.payload.get("lesson", "User preference noted"),
                    confidence=0.8,
                )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="user_to_learning",
        domains=[EventDomain.USER.value],
        callback=on_user_event,
    )

    # ── Connect Teaching Events to Notifications ─────────────────────────────

    def on_teaching_ready(event):
        """When a teaching lesson is ready, consider notifying user."""
        try:
            from core.ecosystem_controller import get_ecosystem_controller
            controller = get_ecosystem_controller()
            topic = event.payload.get("topic", "")
            # Only notify for high-value teachings
            if event.priority <= EventPriority.HIGH.value:
                controller.notify_user(
                    f"I learned something about {topic} that might interest you.",
                    priority=2,
                )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="teaching_to_notification",
        domains=[EventDomain.TEACHING.value],
        callback=on_teaching_ready,
        event_types=["teaching_ready"],
    )

    # ── Connect Health Events to Self-Healing ────────────────────────────────

    def on_health_event(event):
        """When a health issue is detected, trigger self-healing."""
        try:
            if event.payload.get("status") == "error":
                from core.self_healing import detect_and_fix_error
                error_msg = event.payload.get("error", "Unknown error")
                detect_and_fix_error(error_msg)
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="health_to_healing",
        domains=[EventDomain.HEALTH.value],
        callback=on_health_event,
        priority_filter=EventPriority.HIGH.value,
    )

    # ═══ WAVE 17: COGNITIVE EVOLUTION CONNECTIONS ═══

    # Connect conversation events to Evolution Engine for performance tracking
    def on_conversation_for_evolution(event):
        """Record every conversation for evolution measurement."""
        try:
            from core.evolution_engine import get_evolution_engine
            engine = get_evolution_engine()
            engine.record_interaction(
                query=event.payload.get("text", ""),
                response="",  # Response captured separately
                signals={
                    "mode": event.payload.get("mode", "general"),
                    "length": event.payload.get("length", 0),
                },
            )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="conversation_to_evolution",
        domains=[EventDomain.USER.value],
        callback=on_conversation_for_evolution,
        event_types=["message"],
    )

    # Connect evolution events to teaching (transparency about self-improvement)
    def on_evolution_event(event):
        """When LOVE evolves, tell the user about it."""
        try:
            from core.teaching_engine import get_teaching_engine
            engine = get_teaching_engine()
            if event.event_type == "evolution.mutation_applied":
                engine.create_self_growth_lesson(
                    what_changed=event.payload.get("mutation_type", "behavioral adjustment"),
                    why=event.payload.get("reason", "Data-driven improvement"),
                    impact=event.payload.get("description", "")[:200],
                )
            elif event.event_type == "evolution.integrated":
                engine.create_self_growth_lesson(
                    what_changed="Permanent improvement integrated",
                    why=event.payload.get("reason", "Statistically validated"),
                    impact=event.payload.get("description", "")[:200],
                )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="evolution_to_teaching_w17",
        domains=[EventDomain.SELF_EVOLUTION.value],
        callback=on_evolution_event,
    )

    # Connect metacognition anomalies to self-healing
    def on_metacognition_anomaly(event):
        """When metacognition detects anomalous behavior, trigger investigation."""
        try:
            if event.event_type == "metacognition.anomaly":
                from core.self_healing import detect_and_fix_error
                detect_and_fix_error(
                    f"Behavioral anomaly detected: {event.payload.get('description', 'unknown')}"
                )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="metacog_to_healing",
        domains=[EventDomain.HEALTH.value],
        callback=on_metacognition_anomaly,
    )

    # Connect memory consolidation events to teaching
    def on_memory_wisdom(event):
        """When memory extracts wisdom, consider sharing it."""
        try:
            from core.teaching_engine import get_teaching_engine
            engine = get_teaching_engine()
            if event.event_type == "memory.wisdom_extracted":
                wisdom = event.payload.get("wisdom", "")
                if wisdom:
                    engine.create_insight_lesson(
                        insight=wisdom,
                        about="pattern recognition",
                        evidence="Extracted from memory consolidation",
                    )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="memory_to_teaching",
        domains=[EventDomain.LEARNING.value],
        callback=on_memory_wisdom,
        event_types=["memory.wisdom_extracted"],
    )

    # Connect constitution drift to evolution engine
    def on_constitution_drift(event):
        """Value drift detected — evolution engine should investigate."""
        try:
            from core.evolution_engine import get_evolution_engine
            engine = get_evolution_engine()
            # Create hypothesis about drift cause
            engine.record_interaction(
                query="[SYSTEM] Constitutional drift detected",
                response=event.payload.get("description", ""),
                signals={"drift_score": event.payload.get("drift_score", 0), "is_system": True},
            )
        except Exception:
            pass

    bus.subscribe(
        subscriber_id="constitution_to_evolution",
        domains=[EventDomain.SELF_EVOLUTION.value],
        callback=on_constitution_drift,
        event_types=["constitution.drift"],
    )

    print("[NeuralConnectors] All modules connected to Neural Bus (Wave 16 + 17)")


def emit_conversation_events(user_input: str, love_response: str, mode: str = "general"):
    """Emit events from a conversation turn. Call this from the chat handler."""
    try:
        from core.neural_bus import get_neural_bus, EventPriority
        bus = get_neural_bus()

        # User spoke
        event_id = bus.emit_user_event("message", {
            "text": user_input[:200],
            "mode": mode,
            "length": len(user_input),
        }, source="agent")

        # LOVE responded
        bus.publish(
            domain="consciousness",
            event_type="response_generated",
            payload={
                "response_length": len(love_response),
                "mode": mode,
            },
            source_module="agent",
            caused_by=event_id,
            priority=EventPriority.LOW,
            propagate=False,  # Don't sync raw conversation events
        )

        # Trigger curiosity engine
        try:
            from core.curiosity_engine import detect_gaps_from_conversation
            gaps = detect_gaps_from_conversation(user_input, love_response)
            if gaps:
                for gap in gaps:
                    bus.publish(
                        domain="learning",
                        event_type="knowledge_gap_detected",
                        payload=gap,
                        source_module="curiosity_engine",
                        caused_by=event_id,
                    )
        except Exception:
            pass

    except Exception:
        pass


def get_neural_context_for_prompt() -> str:
    """
    Generate prompt enrichment from all Wave 16 systems.
    This is injected into every LLM call to make LOVE aware of its own systems.
    """
    sections = []

    # Research knowledge
    try:
        from core.research_engine import get_research_engine
        engine = get_research_engine()
        status = engine.get_status()
        if status["knowledge_entries"] > 0:
            sections.append(f"[I have {status['knowledge_entries']} research entries in my knowledge base, monitoring {status['monitored_topics']} topics]")
    except Exception:
        pass

    # Learned behaviors
    try:
        from core.self_builder import get_self_builder
        builder = get_self_builder()
        rules_prompt = builder.get_rules_prompt()
        if rules_prompt:
            sections.append(rules_prompt)
    except Exception:
        pass

    # Teaching opportunities
    try:
        from core.teaching_engine import get_teaching_engine
        engine = get_teaching_engine()
        status = engine.get_status()
        if status["queued"] > 0:
            sections.append(f"[I have {status['queued']} things I want to share with the user when the time is right]")
    except Exception:
        pass

    # Ecosystem awareness
    try:
        from core.ecosystem_controller import get_ecosystem_controller
        controller = get_ecosystem_controller()
        presence = controller.get_user_presence()
        if presence.get("present"):
            sections.append(f"[User is active on {presence.get('active_device_name', 'unknown device')}, activity: {presence.get('likely_activity', 'unknown')}]")
    except Exception:
        pass

    # ═══ WAVE 17: Cognitive Evolution Context ═══

    # Constitution character prompt
    try:
        from core.constitution import get_constitution
        constitution = get_constitution()
        char_prompt = constitution.get_character_prompt()
        if char_prompt:
            sections.append(char_prompt)
    except Exception:
        pass

    # Memory wisdom
    try:
        from core.memory_architect import get_memory_architect
        ma = get_memory_architect()
        stats = ma.get_memory_stats()
        if stats.total > 0:
            sections.append(f"[Memory: {stats.total} memories across {stats.per_tier} tiers, consolidation health: {stats.consolidation_health:.0%}]")
    except Exception:
        pass

    # Evolution genome
    try:
        from core.evolution_engine import get_evolution_engine
        evo = get_evolution_engine()
        genome = evo.get_current_genome()
        if genome.get("system_prefix"):
            sections.append(f"[Evolved behaviors active: {genome['system_prefix'][:200]}]")
        gen = evo.get_generation()
        if gen > 0:
            sections.append(f"[Evolution generation: {gen}]")
    except Exception:
        pass

    # Metacognitive state
    try:
        from core.metacognitive_monitor import get_metacognitive_monitor
        meta = get_metacognitive_monitor()
        load = meta.get_current_load()
        weakness = meta.identify_weakness()
        strength = meta.identify_strength()
        meta_parts = []
        if load:
            meta_parts.append(f"cognitive load: {load.level}")
        if weakness:
            meta_parts.append(f"improving: {weakness}")
        if strength:
            meta_parts.append(f"strong at: {strength}")
        if meta_parts:
            sections.append(f"[Self-awareness: {', '.join(meta_parts)}]")
    except Exception:
        pass

    return "\n".join(sections) if sections else ""
