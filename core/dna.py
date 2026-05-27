import json
import os
from pathlib import Path

DATA_PATH = Path("data/personality_weights.json")
DEFAULTS = {"verbosity": 5, "humor": 5, "technical_depth": 7}


def _ensure_data_file():
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_PATH, "w") as f:
            json.dump(DEFAULTS, f)


def _load_weights():
    _ensure_data_file()
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def mutate_trait(trait: str, direction: str):
    weights = _load_weights()
    if trait not in weights:
        weights[trait] = 5
    delta = 1 if direction == "up" else -1
    weights[trait] = max(1, min(10, weights[trait] + delta))
    with open(DATA_PATH, "w") as f:
        json.dump(weights, f)


def get_dynamic_instructions() -> str:
    weights = _load_weights()
    instructions = []
    if weights.get("verbosity", 5) <= 3:
        instructions.append("Keep answers under 2 sentences.")
    if weights.get("verbosity", 5) >= 8:
        instructions.append("Be thorough and detailed.")
    if weights.get("humor", 5) >= 7:
        instructions.append("Use occasional wit and humor.")
    if weights.get("technical_depth", 5) <= 3:
        instructions.append("Explain in simple terms, avoid jargon.")
    if weights.get("technical_depth", 5) >= 8:
        instructions.append("Include technical details and precise terminology.")
    return " ".join(instructions)
