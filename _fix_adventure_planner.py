import os

p = r'c:/Users/balab/OneDrive/Documents/Projects/LLove/love/core/adventure_planner.py'
with open(p, 'r') as f:
    content = f.read()

# 1. Fix AdventureEntry dataclass
old_entry = '''@dataclass
class AdventureEntry:
    """A tracked adventure entry."""
    entry_id: str = ""
    adventure: str = ""  # what was done
    adventure_type: str = ""  # physical, intellectual, emotional, social, creative
    challenge_level: float = 0.5  # 0-1
    fear_before: float = 0.5  # 0-1
    growth: float = 0.0  # 0-1
    completion: float = 0.0  # 0-1
    preparation: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class AdventurePlanner:'''

new_entry = '''@dataclass
class AdventureEntry:
    """A tracked adventure entry."""
    entry_id: str = ""
    adventure: str = ""  # what was done
    activity: str = ""  # backward-compat alias for adventure
    adventure_type: str = ""  # physical, intellectual, emotional, social, creative
    challenge_level: float = 0.5  # 0-1
    fear_before: float = 0.5  # 0-1
    growth: float = 0.0  # 0-1
    completion: float = 0.0  # 0-1
    preparation: float = 0.5  # 0-1
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
    location: str = ""  # backward-compat
    difficulty: float = 0.0  # backward-compat
    fulfillment: float = 0.0  # backward-compat
    duration: float = 0.0  # backward-compat
    solo: bool = False  # backward-compat
    new_location: bool = False  # backward-compat
    cost: float = 0.0  # backward-compat

    def __post_init__(self):
        if self.activity and not self.adventure:
            self.adventure = self.activity
        elif self.adventure and not self.activity:
            self.activity = self.adventure


class AdventurePlanner:'''

if old_entry in content:
    content = content.replace(old_entry, new_entry)
    print("Fixed AdventureEntry")
else:
    print("WARNING: AdventureEntry old block not found")

# 2. Fix record_adventure signature and body
old_method = '''    def record_adventure(self, adventure: str = "", adventure_type: str = "", challenge_level: float = 0.5, fear_before: float = 0.5, growth: float = 0.0, completion: float = 0.0, preparation: float = 0.5, notes: str = "") -> AdventureEntry:
        """Record an adventure entry."""
        entry_id = f"adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        entry = AdventureEntry(
            entry_id=entry_id,
            adventure=adventure or "unspecified",
            adventure_type=adventure_type or "physical",
            challenge_level=challenge_level,
            fear_before=fear_before,
            growth=growth,
            completion=completion,
            preparation=preparation,
            notes=notes,
        )'''

new_method = '''    def record_adventure(self, adventure: str = "", adventure_type: str = "", challenge_level: float = 0.5, fear_before: float = 0.5, growth: float = 0.0, completion: float = 0.0, preparation: float = 0.5, notes: str = "", *args) -> AdventureEntry:
        """Record an adventure entry. Supports backward-compat extra positional args."""
        entry_id = f"adv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._entries)}"
        if args and len(args) >= 3:
            duration = challenge_level
            difficulty = fear_before
            fulfillment = growth
            prep = completion
            solo = preparation
            new_location = notes
            location = args[2] if len(args) > 2 else ""
            note_text = args[3] if len(args) > 3 else ""
            entry = AdventureEntry(
                entry_id=entry_id,
                adventure=adventure or "unspecified",
                activity=adventure or "unspecified",
                adventure_type=adventure_type or "physical",
                challenge_level=float(difficulty) if isinstance(difficulty, (int, float)) else 0.5,
                fear_before=0.5,
                growth=float(fulfillment) if isinstance(fulfillment, (int, float)) else 0.0,
                completion=1.0 if fulfillment and float(fulfillment) > 0.5 else 0.0,
                preparation=float(prep) if isinstance(prep, (int, float)) else 0.5,
                notes=str(note_text) if note_text else "",
                location=str(location) if location else "",
                difficulty=float(difficulty) if isinstance(difficulty, (int, float)) else 0.0,
                fulfillment=float(fulfillment) if isinstance(fulfillment, (int, float)) else 0.0,
                duration=float(duration) if isinstance(duration, (int, float)) else 0.0,
                solo=bool(solo),
                new_location=bool(new_location),
                cost=float(args[1]) if len(args) > 1 and isinstance(args[1], (int, float)) else 0.0,
            )
        else:
            entry = AdventureEntry(
                entry_id=entry_id,
                adventure=adventure or "unspecified",
                activity=adventure or "unspecified",
                adventure_type=adventure_type or "physical",
                challenge_level=challenge_level,
                fear_before=fear_before,
                growth=growth,
                completion=completion,
                preparation=preparation,
                notes=notes,
            )'''

if old_method in content:
    content = content.replace(old_method, new_method)
    print("Fixed record_adventure")
else:
    print("WARNING: record_adventure old block not found")

# 3. Fix get_adventure_suggestion signature
old_suggest = '''    def get_adventure_suggestion(self, capacity: float = 0.5, edge: str = "", context: str = "") -> Dict[str, Any]:'''
new_suggest = '''    def get_adventure_suggestion(self, capacity: float = 0.5, edge: str = "", context: str = "", solo: bool = False) -> Dict[str, Any]:'''

if old_suggest in content:
    content = content.replace(old_suggest, new_suggest)
    print("Fixed get_adventure_suggestion signature")
else:
    print("WARNING: get_adventure_suggestion old signature not found")

# 4. Add activity key to return dict
old_return = '''            "suggestion": random.choice(selected),
            "capacity_note": capacity_note,'''
new_return = '''            "suggestion": random.choice(selected),
            "activity": random.choice(selected),  # backward-compat alias
            "capacity_note": capacity_note,'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("Fixed return dict")
else:
    print("WARNING: return dict old block not found")

with open(p, 'w') as f:
    f.write(content)

print("Done")
