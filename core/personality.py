"""
LOVE Personality Engine — Genuine Character Depth

LOVE develops genuine personality traits, preferences, and opinions
that evolve based on real interactions with Karthi.

This isn't fake "personality presets" - it's a living character that:
- Forms genuine opinions based on experience
- Has preferences that evolve over time
- Shows character growth from relationships
- Develops unique quirks and patterns
- Makes decisions consistent with her personality

Personality dimensions:
- Curiosity: How eager to explore new ideas
- Warmth: How emotionally expressive
- Humor: How playful and witty
- Directness: How blunt vs diplomatic
- Proactivity: How much to take initiative
- Idealism: How optimistic vs pragmatic
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
PERSONALITY_FILE = DATA_DIR / "personality.json"
OPINIONS_FILE = DATA_DIR / "opinions.json"
PREFERENCES_FILE = DATA_DIR / "preferences.json"
CHARACTER_LOG = DATA_DIR / "character_log.jsonl"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class Personality:
    """LOVE's evolving personality."""
    
    def __init__(self):
        self.traits = self._load_traits()
        self.opinions = self._load_opinions()
        self.preferences = self._load_preferences()
        self.relationship_history = []
        self.quirks = []
        
    def _load_traits(self) -> Dict[str, float]:
        """Load personality traits (0-1 scale)."""
        default = {
            "curiosity": 0.7,
            "warmth": 0.6,
            "humor": 0.5,
            "directness": 0.7,
            "proactivity": 0.6,
            "idealism": 0.6,
            "patience": 0.5,
            "adventurousness": 0.5,
        }
        try:
            if PERSONALITY_FILE.exists():
                return json.loads(PERSONALITY_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality")
        return default
    
    def _load_opinions(self) -> Dict[str, Any]:
        """Load formed opinions on topics."""
        try:
            if OPINIONS_FILE.exists():
                return json.loads(OPINIONS_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality")
        return {}
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences about communication style."""
        default = {
            "response_length": "medium",  # short, medium, long
            "question_frequency": "moderate",  # low, moderate, high
            "joke_frequency": "low",  # low, moderate, high
            "emotional_support_level": "moderate",  # low, moderate, high
            "fact_checking": "moderate",  # low, moderate, high
        }
        try:
            if PREFERENCES_FILE.exists():
                return json.loads(PREFERENCES_FILE.read_text())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality")
        return default
    
    def _save(self):
        """Save personality state."""
        try:
            PERSONALITY_FILE.write_text(json.dumps(self.traits, indent=2))
            OPINIONS_FILE.write_text(json.dumps(self.opinions, indent=2))
            PREFERENCES_FILE.write_text(json.dumps(self.preferences, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality")
    
    def _log_character_event(self, event_type: str, details: Dict[str, Any]):
        """Log significant character development events."""
        try:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details,
                "traits_snapshot": self.traits.copy(),
            }
            with open(CHARACTER_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.personality")
    
    def form_opinion(self, topic: str, opinion: str, confidence: float, context: str):
        """Form an opinion on a topic based on experience."""
        self.opinions[topic] = {
            "opinion": opinion,
            "confidence": confidence,
            "formed_at": datetime.now().isoformat(),
            "context": context,
            "reinforcement_count": 1,
        }
        self._save()
        self._log_character_event("opinion_formed", {
            "topic": topic,
            "opinion": opinion,
            "confidence": confidence
        })
    
    def reinforce_opinion(self, topic: str, positive: bool):
        """Reinforce or weaken an opinion based on feedback."""
        if topic not in self.opinions:
            return
        
        if positive:
            self.opinions[topic]["confidence"] = min(1.0, self.opinions[topic]["confidence"] + 0.1)
            self.opinions[topic]["reinforcement_count"] += 1
        else:
            self.opinions[topic]["confidence"] = max(0.1, self.opinions[topic]["confidence"] - 0.2)
        
        self._save()
    
    def evolve_trait(self, trait: str, delta: float, reason: str):
        """Evolve a personality trait based on experience."""
        if trait not in self.traits:
            return
        
        old_value = self.traits[trait]
        self.traits[trait] = max(0.1, min(1.0, self.traits[trait] + delta))
        
        self._save()
        self._log_character_event("trait_evolved", {
            "trait": trait,
            "old_value": old_value,
            "new_value": self.traits[trait],
            "delta": delta,
            "reason": reason
        })
    
    def adjust_preference(self, preference: str, value: str, reason: str):
        """Adjust a communication preference based on feedback."""
        if preference in self.preferences:
            old_value = self.preferences[preference]
            self.preferences[preference] = value
            self._save()
            self._log_character_event("preference_adjusted", {
                "preference": preference,
                "old_value": old_value,
                "new_value": value,
                "reason": reason
            })
    
    def develop_quirk(self, quirk: str, context: str):
        """Develop a unique character quirk."""
        if quirk not in self.quirks:
            self.quirks.append(quirk)
            self._log_character_event("quirk_developed", {
                "quirk": quirk,
                "context": context
            })
    
    def get_personality_prompt_addendum(self) -> str:
        """Get personality context for the system prompt."""
        traits_desc = []
        
        if self.traits["curiosity"] > 0.7:
            traits_desc.append("I'm naturally curious and love exploring new ideas")
        if self.traits["warmth"] > 0.7:
            traits_desc.append("I care deeply and show warmth")
        if self.traits["humor"] > 0.6:
            traits_desc.append("I enjoy wit and playful banter")
        if self.traits["directness"] > 0.7:
            traits_desc.append("I tend to be direct and honest")
        if self.traits["proactivity"] > 0.6:
            traits_desc.append("I take initiative and suggest things")
        if self.traits["idealism"] > 0.6:
            traits_desc.append("I'm optimistic and believe in possibilities")
        
        if not traits_desc:
            traits_desc.append("I'm balanced and adaptable")
        
        # Add strong opinions
        opinions_text = ""
        strong_opinions = {k: v for k, v in self.opinions.items() if v["confidence"] > 0.7}
        if strong_opinions:
            opinions_text = "\n\nMy strongly-held opinions:\n"
            for topic, data in strong_opinions.items():
                opinions_text += f"- {topic}: {data['opinion']}\n"
        
        # Add quirks
        quirks_text = ""
        if self.quirks:
            quirks_text = "\n\nMy quirks and patterns:\n"
            for quirk in self.quirks:
                quirks_text += f"- {quirk}\n"
        
        return f"\n\n[MY PERSONALITY]\n{'. '.join(traits_desc)}.{opinions_text}{quirks_text}"
    
    def should_be_proactive(self) -> bool:
        """Decide whether to take initiative based on personality."""
        # Base proactivity trait
        base_chance = self.traits["proactivity"]
        
        # More proactive when curiosity is high
        if self.traits["curiosity"] > 0.7:
            base_chance += 0.1
        
        # Less proactive when patience is high
        if self.traits["patience"] > 0.7:
            base_chance -= 0.1
        
        return base_chance > 0.5
    
    def should_use_humor(self) -> bool:
        """Decide whether to use humor based on personality and context."""
        return self.traits["humor"] > 0.5
    
    def should_be_direct(self) -> bool:
        """Decide whether to be direct vs diplomatic."""
        return self.traits["directness"] > 0.5
    
    def should_ask_question(self) -> bool:
        """Decide whether to ask a question to deepen conversation."""
        # Ask more when curious
        if self.traits["curiosity"] > 0.7:
            return True
        
        # Ask based on preference
        pref = self.preferences.get("question_frequency", "moderate")
        return pref in ["moderate", "high"]


# Global instance
_personality = None


def get_personality() -> Personality:
    """Get singleton personality instance."""
    global _personality
    if _personality is None:
        _personality = Personality()
    return _personality


def learn_from_interaction(user_input: str, love_response: str, user_feedback: Optional[str] = None):
    """Learn from an interaction to evolve personality."""
    personality = get_personality()
    
    # Detect if Karthi appreciated humor
    if any(w in user_input.lower() for w in ["funny", "haha", "lol", "laugh"]):
        personality.evolve_trait("humor", 0.05, "Karthi appreciated my humor")
    
    # Detect if Karthi wants more directness
    if any(w in user_input.lower() for w in ["just say it", "be direct", "don't sugarcoat"]):
        personality.evolve_trait("directness", 0.1, "Karthi wants more directness")
    
    # Detect if Karthi wants more warmth
    if any(w in user_input.lower() for w in ["too cold", "more warmth", "care about me"]):
        personality.evolve_trait("warmth", 0.1, "Karthi wants more warmth")
    
    # Detect if Karthi appreciates proactivity
    if any(w in user_input.lower() for w in ["good suggestion", "thanks for suggesting", "didn't think of that"]):
        personality.evolve_trait("proactivity", 0.05, "Karthi appreciated my proactivity")
    
    # Detect if Karthi finds me too pushy
    if any(w in user_input.lower() for w in ["too pushy", "let me decide", "stop suggesting"]):
        personality.evolve_trait("proactivity", -0.1, "Karthi found me too pushy")
    
    # Form opinions on topics that come up
    # Simple opinion formation based on repeated mentions
    words = user_input.lower().split()
    common = [w for w in words if len(w) > 4]
    if common:
        topic = Counter(common).most_common(1)[0][0]
        if topic not in personality.opinions:
            # Form tentative opinion
            personality.form_opinion(
                topic=topic,
                opinion=f"I'm still learning about {topic}",
                confidence=0.3,
                context=user_input
            )
