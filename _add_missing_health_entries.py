api_path = "api/evolution_routes.py"
with open(api_path, "r", encoding="utf-8") as f:
    api = f.read()

# Find the line with "uncertainty_embracer" and "overall" to insert before "overall"
old_end = '            "uncertainty_embracer": {"available": True},\n            "overall": "healthy" if integration._running else "degraded",'

new_entries = '''            "uncertainty_embracer": {"available": True},
            "perfectionism_healer": {"available": True},
            "comparison_detoxifier": {"available": True},
            "money_mindset_coach": {"available": True},
            "scarcity_healer": {"available": True},
            "generosity_cultivator": {"available": True},
            "abundance_architect": {"available": True},
            "decision_quality_tracker": {"available": True},
            "optionality_maximizer": {"available": True},
            "expected_value_coach": {"available": True},
            "regret_minimizer": {"available": True},
            "cognitive_bias_detector": {"available": True},
            "mental_model_trainer": {"available": True},
            "first_principles_thinker": {"available": True},
            "systems_thinking_coach": {"available": True},
            "authentic_expression_coach": {"available": True},
            "vulnerable_communication_trainer": {"available": True},
            "difficult_conversation_navigator": {"available": True},
            "active_listening_master": {"available": True},
            "body_awareness_trainer": {"available": True},
            "breath_work_coach": {"available": True},
            "movement_intelligence": {"available": True},
            "posture_presence_coach": {"available": True},
            "intimacy_coach": {"available": True},
            "sensory_awareness_trainer": {"available": True},
            "passion_cultivator": {"available": True},
            "deep_connection_coach": {"available": True},
            "music_mood_regulator": {"available": True},
            "sound_healing_guide": {"available": True},
            "playlist_therapist": {"available": True},
            "rhythmic_living_coach": {"available": True},
            "mindful_eating_coach": {"available": True},
            "cooking_joy_cultivator": {"available": True},
            "meal_ritual_designer": {"available": True},
            "food_as_medicine_coach": {"available": True},
            "pet_bonding_coach": {"available": True},
            "animal_empathy_trainer": {"available": True},
            "pet_loss_support": {"available": True},
            "human_animal_connection_guide": {"available": True},
            "garden_therapy_coach": {"available": True},
            "plant_parenting_guide": {"available": True},
            "seasonal_garden_planner": {"available": True},
            "urban_gardening_coach": {"available": True},
            "overall": "healthy" if integration._running else "degraded",'''

if old_end in api:
    api = api.replace(old_end, new_entries)
    print("Added 56 missing engine entries to health dict (batches 48-58).")
else:
    print("WARNING: Could not find insertion point in health dict")

with open(api_path, "w", encoding="utf-8") as f:
    f.write(api)
