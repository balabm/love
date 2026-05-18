"""
LOVE Prediction Market

LOVE makes predictions about Karthi and tracks its accuracy.
This is how LOVE gets smarter — it learns from being wrong.

Predictions:
- "Karthi will check email within 10 minutes of waking"
- "Karthi will be stressed after the standup"
- "Karthi will work on LOVE tonight"
- "Karthi will forget to drink water during deep work"

Every prediction has:
- confidence score
- basis (what pattern triggered it)
- resolution criteria
- actual outcome (when known)
- accuracy delta (how wrong was I?)

LOVE uses accuracy history to calibrate future confidence.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent / "data"
PREDICTIONS_FILE = DATA_DIR / "predictions.json"
ACCURACY_FILE = DATA_DIR / "prediction_accuracy.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path, default: Any = None) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return default if default is not None else {}


def _save(path: Path, data: Any):
    try:
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def make_prediction(what: str, confidence: float, basis: str,
                    resolution_time: str, criteria: str) -> Dict[str, Any]:
    """LOVE makes a prediction and tracks it."""
    preds = _load(PREDICTIONS_FILE, {"predictions": []})

    pred = {
        "id": f"pred_{int(time.time() * 1000)}",
        "what": what,
        "confidence": confidence,
        "basis": basis,
        "resolution_time": resolution_time,
        "criteria": criteria,
        "status": "active",  # active | resolved | expired
        "outcome": None,
        "accuracy": None,
        "created_at": datetime.now().isoformat(),
    }

    preds["predictions"].append(pred)
    _save(PREDICTIONS_FILE, preds)
    return pred


def resolve_prediction(pred_id: str, outcome: str, actual_happened: bool):
    """Mark a prediction as resolved and calculate accuracy."""
    preds = _load(PREDICTIONS_FILE, {"predictions": []})

    for p in preds["predictions"]:
        if p["id"] == pred_id:
            p["status"] = "resolved"
            p["outcome"] = outcome
            p["resolved_at"] = datetime.now().isoformat()

            # Accuracy: if we predicted it would happen and it did → 1.0
            # If we predicted high confidence and it didn't → 0.0
            predicted_happening = p["confidence"] > 0.5
            if actual_happened and predicted_happening:
                p["accuracy"] = p["confidence"]
            elif not actual_happened and not predicted_happening:
                p["accuracy"] = 1.0 - p["confidence"]
            else:
                p["accuracy"] = 0.0

            _update_accuracy_history(p["what"], p["accuracy"])
            break

    _save(PREDICTIONS_FILE, preds)


def _update_accuracy_history(prediction_type: str, accuracy: float):
    """Track accuracy by prediction type so LOVE learns what it's good/bad at."""
    acc = _load(ACCURACY_FILE, {})
    if prediction_type not in acc:
        acc[prediction_type] = {"count": 0, "total_accuracy": 0, "scores": []}

    acc[prediction_type]["count"] += 1
    acc[prediction_type]["total_accuracy"] += accuracy
    acc[prediction_type]["scores"].append(accuracy)
    acc[prediction_type]["scores"] = acc[prediction_type]["scores"][-20:]  # Keep last 20
    acc[prediction_type]["avg_accuracy"] = acc[prediction_type]["total_accuracy"] / acc[prediction_type]["count"]

    _save(ACCURACY_FILE, acc)


def get_accuracy_report() -> Dict[str, Any]:
    """How good is LOVE at predicting?"""
    acc = _load(ACCURACY_FILE, {})
    if not acc:
        return {"message": "Not enough predictions yet. Still learning."}

    report = {}
    for pred_type, data in acc.items():
        report[pred_type] = {
            "avg_accuracy": round(data.get("avg_accuracy", 0), 2),
            "count": data["count"],
            "trend": "improving" if len(data["scores"]) >= 3 and data["scores"][-1] > data["scores"][0] else "stable",
        }

    overall = sum(d["avg_accuracy"] for d in acc.values()) / len(acc)
    report["overall_accuracy"] = round(overall, 2)
    return report


def get_active_predictions() -> List[Dict[str, Any]]:
    preds = _load(PREDICTIONS_FILE, {"predictions": []})
    return [p for p in preds.get("predictions", []) if p.get("status") == "active"]


def get_prediction_for_prompt() -> str:
    """Generate a prediction block for the LLM prompt."""
    active = get_active_predictions()
    if not active:
        return ""

    lines = ["[PREDICTIONS I'm currently tracking]"]
    for p in active[:5]:
        lines.append(f"- {p['what']} (confidence: {p['confidence']:.0%}, basis: {p['basis']})")

    acc = get_accuracy_report()
    if "overall_accuracy" in acc:
        lines.append(f"\nMy prediction accuracy so far: {acc['overall_accuracy']:.0%}")

    return "\n".join(lines)


def auto_resolve_expired():
    """Mark expired predictions. Called periodically."""
    preds = _load(PREDICTIONS_FILE, {"predictions": []})
    now = datetime.now()

    for p in preds.get("predictions", []):
        if p.get("status") != "active":
            continue
        try:
            resolve_by = datetime.fromisoformat(p["resolution_time"])
            if now > resolve_by + timedelta(hours=2):
                p["status"] = "expired"
                p["outcome"] = "unknown — no data"
                p["accuracy"] = None
        except Exception:
            pass

    _save(PREDICTIONS_FILE, preds)


# ── Proactive prediction generation ───────────────────────────────────────────

def generate_predictions_from_world(world: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Auto-generate predictions based on world model."""
    new_preds = []
    now = datetime.now()

    # Predict routines
    for routine, data in world.get("routines", {}).items():
        hours = data.get("hours", [])
        if len(hours) >= 3:
            avg = sum(hours) / len(hours)
            next_time = now.replace(hour=int(avg), minute=0) + timedelta(days=1)
            conf = min(len(hours) / 10, 0.85)

            pred = make_prediction(
                what=f"Karthi will engage in '{routine}' around {int(avg)}:00",
                confidence=conf,
                basis=f"observed {len(hours)} times at ~{int(avg)}:00",
                resolution_time=next_time.isoformat(),
                criteria=f"Karthi does something related to {routine} within 2 hours of {int(avg)}:00",
            )
            new_preds.append(pred)

    # Predict stress from patterns
    stressors = world.get("stressors", [])
    if len(stressors) >= 3:
        pred = make_prediction(
            what="Karthi will mention stress or being overwhelmed in the next 24 hours",
            confidence=0.4 + min(len(stressors) / 20, 0.3),
            basis=f"{len(stressors)} stress signals in recent history",
            resolution_time=(now + timedelta(hours=24)).isoformat(),
            criteria="User mentions stress, overwhelmed, anxious, or frustrated",
        )
        new_preds.append(pred)

    return new_preds


def enrich_prompt() -> str:
    """Get prediction context for the chat prompt."""
    return get_prediction_for_prompt()


if __name__ == "__main__":
    # Test
    p = make_prediction("Karthi will check email within 5 min", 0.7, "morning routine", (datetime.now() + timedelta(minutes=10)).isoformat(), "email check detected")
    print(json.dumps(p, indent=2))
    print("\nActive:", json.dumps(get_active_predictions(), indent=2))
