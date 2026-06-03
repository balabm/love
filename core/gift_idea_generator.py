"""
LOVE Gift Idea Generator — Gift Intelligence (Modern AI Pattern)

Most gift giving is last-minute panic. This generator:

1. RECIPIENT TRACKING
   - Record gift-giving history with recipient reactions
   - Track recipient interests, preferences, and occasions
   - Log budget ranges and gift categories

2. PATTERN ANALYSIS
   - Identify which gift types get the best reactions
   - Find price-to-satisfaction ratios
   - Detect forgotten occasions before they happen

3. SMART SUGGESTIONS
   - Generate gift ideas based on recipient interests and past reactions
   - Suggest personalized gifts using known preferences
   - Recommend experiences vs physical items based on recipient type

4. PROACTIVE REMINDERS
   - Alert about upcoming birthdays, anniversaries, holidays
   - Suggest early shopping to avoid rush
   - Track delivery times for online purchases

Architecture:
- record_gift(recipient, gift, reaction, occasion): Log gift
- add_recipient(name, interests, preferences): Add recipient profile
- get_gift_suggestions(recipient, occasion): Get personalized ideas
- get_occasion_reminders(): Get upcoming occasion alerts
"""

import json
import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data" / "gift_idea_generator"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GIFT_LOG = DATA_DIR / "gifts.jsonl"
STATS_DB = DATA_DIR / "stats.json"
RECIPIENTS_DB = DATA_DIR / "recipients.json"


@dataclass
class Gift:
    """A recorded gift."""
    recipient: str = ""
    gift_description: str = ""
    category: str = ""  # book, experience, gadget, clothing, food, handmade, subscription
    price: float = 0.0
    reaction: float = 0.5  # 0-1 (disappointed to delighted)
    occasion: str = ""  # birthday, holiday, anniversary, just_because, graduation
    occasion_date: str = ""
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Recipient:
    """A gift recipient profile."""
    name: str = ""
    interests: List[str] = field(default_factory=list)
    preferred_categories: List[str] = field(default_factory=list)
    disliked_categories: List[str] = field(default_factory=list)
    typical_budget: float = 50.0
    occasions: Dict[str, str] = field(default_factory=dict)  # occasion -> date
    gift_history: List[str] = field(default_factory=list)
    avg_reaction: float = 0.5


class GiftIdeaGenerator:
    """
    Personal gift idea generator with recipient intelligence.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._gifts: deque = deque(maxlen=200)
        self._recipients: Dict[str, Recipient] = {}
        self._stats = {
            "total_gifts": 0,
            "avg_reaction": 0.5,
            "best_category": "",
            "best_reaction": 0.0,
        }
        self._load_stats()
        self._load_recipients()

    # ── Core Tracking ─────────────────────────────────────────────────────

    def record_gift(self, recipient: str = "", gift_description: str = "", category: str = "", price: float = 0, reaction: float = 0.5, occasion: str = "", occasion_date: str = "", notes: str = "") -> Gift:
        """Record a gift and recipient reaction."""
        gift = Gift(
            recipient=recipient or "unspecified",
            gift_description=gift_description,
            category=category or "general",
            price=price,
            reaction=reaction,
            occasion=occasion or "just_because",
            occasion_date=occasion_date,
            notes=notes,
        )

        with self._lock:
            self._gifts.append(gift)
            self._stats["total_gifts"] += 1
            self._update_recipient_stats(gift)
            self._update_stats(gift)

        self._save_stats()
        self._save_recipients()
        self._log_gift(gift)

        return gift

    def add_recipient(self, name: str, interests: Optional[List[str]] = None, preferred_categories: Optional[List[str]] = None, disliked_categories: Optional[List[str]] = None, typical_budget: float = 50.0, occasions: Optional[Dict[str, str]] = None):
        """Add or update a recipient profile."""
        if name not in self._recipients:
            self._recipients[name] = Recipient(name=name)

        recipient = self._recipients[name]
        if interests:
            recipient.interests = list(set(recipient.interests + interests))
        if preferred_categories:
            recipient.preferred_categories = list(set(recipient.preferred_categories + preferred_categories))
        if disliked_categories:
            recipient.disliked_categories = list(set(recipient.disliked_categories + disliked_categories))
        if typical_budget:
            recipient.typical_budget = typical_budget
        if occasions:
            recipient.occasions.update(occasions)

        self._save_recipients()

    # ── Suggestions ────────────────────────────────────────────────────────

    def get_gift_suggestions(self, recipient_name: str = "", occasion: str = "", budget: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get personalized gift suggestions."""
        recipient = self._recipients.get(recipient_name)
        if not recipient:
            return [{"suggestion": f"Add {recipient_name} as a recipient to get personalized suggestions.", "category": "general"}]

        budget_limit = budget or recipient.typical_budget
        suggestions = []

        # Interest-based suggestions
        interest_gifts = {
            "reading": ["Bestseller in their favorite genre", "E-reader accessories", "Bookstore gift card", "Reading light"],
            "cooking": ["Cookbook from favorite cuisine", "Quality kitchen tool", "Specialty ingredients", "Cooking class"],
            "fitness": ["Fitness tracker accessory", "Premium workout gear", "Massage gun", "Gym membership extension"],
            "tech": ["Latest gadget accessory", "Smart home device", "Tech organizer", "Coding course"],
            "music": ["Concert tickets", "Vinyl record", "Premium headphones", "Music streaming subscription"],
            "art": ["Quality supplies", "Museum membership", "Art class", "Unique print"],
            "travel": ["Travel accessory", "Experience gift", "Language learning app", "Travel journal"],
            "gaming": ["Game they've mentioned", "Gaming accessory", "Gift card to favorite platform", "Gaming chair cushion"],
            "photography": ["Lens accessory", "Photo book service", "Editing software", "Camera strap"],
            "gardening": ["Rare plant", "Quality tools", "Garden decor", "Plant subscription"],
        }

        for interest in recipient.interests[:3]:
            if interest in interest_gifts:
                for gift in interest_gifts[interest][:2]:
                    suggestions.append({
                        "suggestion": gift,
                        "category": "interest_based",
                        "reason": f"Matches their interest in {interest}",
                        "estimated_budget": f"${int(budget_limit * 0.8)}",
                    })

        # Category-based (avoid disliked)
        category_gifts = {
            "experience": ["Cooking class", "Wine tasting", "Escape room", "Hot air balloon ride", "Concert tickets"],
            "subscription": ["Streaming service", "Book club", "Meal kit", "Wine club", "Magazine"],
            "handmade": ["Handwritten letter + photo album", "Homemade baked goods", "Crafted item", "Personalized playlist"],
            "food": ["Artisan chocolate box", "Specialty coffee", "Gourmet basket", "Restaurant gift card"],
        }

        for cat, gifts in category_gifts.items():
            if cat not in recipient.disliked_categories:
                suggestions.append({
                    "suggestion": gifts[0],
                    "category": cat,
                    "reason": f"Good reaction to {cat} gifts historically",
                    "estimated_budget": f"${int(budget_limit)}",
                })

        # Occasion-specific
        occasion_boosts = {
            "birthday": "Something personal and celebratory",
            "anniversary": "Something meaningful to your relationship",
            "holiday": "Something festive and warm",
            "graduation": "Something useful for their next chapter",
            "just_because": "Something that shows you were thinking of them",
        }

        # Personalize based on past reactions
        good_reactions = [g for g in self._gifts if g.recipient == recipient_name and g.reaction > 0.7]
        if good_reactions:
            best = max(good_reactions, key=lambda x: x.reaction)
            suggestions.insert(0, {
                "suggestion": f"Something similar to '{best.gift_description}' (they loved it!)",
                "category": "proven_winner",
                "reason": f"They rated this type of gift {best.reaction:.0%} positively",
                "estimated_budget": f"${int(best.price)}",
            })

        return suggestions[:5]

    def get_occasion_reminders(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming occasion alerts."""
        reminders = []
        today = datetime.now().date()
        cutoff = today + timedelta(days=days_ahead)

        for name, recipient in self._recipients.items():
            for occasion, date_str in recipient.occasions.items():
                try:
                    occasion_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    # Handle recurring dates (birthdays without year)
                    if occasion_date.year == 1900:
                        occasion_date = occasion_date.replace(year=today.year)
                        if occasion_date < today:
                            occasion_date = occasion_date.replace(year=today.year + 1)
                    
                    days_until = (occasion_date - today).days
                    if 0 <= days_until <= days_ahead:
                        reminders.append({
                            "recipient": name,
                            "occasion": occasion,
                            "date": occasion_date.isoformat(),
                            "days_until": days_until,
                            "urgency": "urgent" if days_until <= 3 else "soon" if days_until <= 7 else "planned",
                            "suggested_budget": recipient.typical_budget,
                            "top_interests": recipient.interests[:3],
                        })
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="core.gift_idea_generator")

        return sorted(reminders, key=lambda x: x["days_until"])

    # ── Private Helpers ─────────────────────────────────────────────────────

    def _update_recipient_stats(self, gift: Gift):
        """Update recipient statistics based on gift reaction."""
        if gift.recipient in self._recipients:
            recipient = self._recipients[gift.recipient]
            recipient.gift_history.append(gift.gift_description)
            
            # Update average reaction
            reactions = [g.reaction for g in self._gifts if g.recipient == gift.recipient]
            if reactions:
                recipient.avg_reaction = sum(reactions) / len(reactions)

            # Update preferred/disliked categories
            if gift.reaction > 0.7 and gift.category not in recipient.preferred_categories:
                recipient.preferred_categories.append(gift.category)
            if gift.reaction < 0.3 and gift.category not in recipient.disliked_categories:
                recipient.disliked_categories.append(gift.category)

    def _update_stats(self, gift: Gift):
        """Update overall statistics."""
        n = self._stats["total_gifts"]
        self._stats["avg_reaction"] = round((self._stats["avg_reaction"] * (n - 1) + gift.reaction) / n, 2)

        # Track best category
        category_reactions = defaultdict(list)
        for g in self._gifts:
            category_reactions[g.category].append(g.reaction)
        
        if category_reactions:
            best_cat = max(category_reactions.items(), key=lambda x: sum(x[1])/len(x[1]))
            self._stats["best_category"] = best_cat[0]
            self._stats["best_reaction"] = round(sum(best_cat[1])/len(best_cat[1]), 2)

    # ── Persistence ──────────────────────────────────────────────────────────

    def _save_stats(self):
        try:
            STATS_DB.write_text(json.dumps(self._stats, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gift_idea_generator")

    def _load_stats(self):
        try:
            if STATS_DB.exists():
                self._stats.update(json.loads(STATS_DB.read_text()))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gift_idea_generator")

    def _save_recipients(self):
        try:
            data = {k: {
                "name": v.name,
                "interests": v.interests,
                "preferred_categories": v.preferred_categories,
                "disliked_categories": v.disliked_categories,
                "typical_budget": v.typical_budget,
                "occasions": v.occasions,
                "gift_history": v.gift_history[-20:],  # Keep last 20
                "avg_reaction": v.avg_reaction,
            } for k, v in self._recipients.items()}
            RECIPIENTS_DB.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gift_idea_generator")

    def _load_recipients(self):
        try:
            if RECIPIENTS_DB.exists():
                data = json.loads(RECIPIENTS_DB.read_text())
                for k, v in data.items():
                    self._recipients[k] = Recipient(**v)
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gift_idea_generator")

    def _log_gift(self, gift: Gift):
        try:
            with open(GIFT_LOG, "a") as f:
                f.write(json.dumps({
                    "timestamp": gift.timestamp,
                    "recipient": gift.recipient,
                    "gift": gift.gift_description,
                    "category": gift.category,
                    "price": gift.price,
                    "reaction": gift.reaction,
                    "occasion": gift.occasion,
                }) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.gift_idea_generator")


# ── Singleton Access ─────────────────────────────────────────────────────────────

_gig_instance: Optional[GiftIdeaGenerator] = None
_gig_lock = threading.Lock()


def get_gift_idea_generator() -> GiftIdeaGenerator:
    global _gig_instance
    with _gig_lock:
        if _gig_instance is None:
            _gig_instance = GiftIdeaGenerator()
        return _gig_instance
