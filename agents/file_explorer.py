"""
LOVE File Explorer Agent

When LOVE has free time, it explores Karthi's files to learn about him.
Reads resumes, configs, notes, project files — builds a rich profile.

This is how LOVE becomes a true companion: it KNOWS you.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROFILE_FILE = DATA_DIR / "profile.json"
FILE_DISCOVERIES = DATA_DIR / "file_discoveries.jsonl"

# Files that reveal who Karthi is
PERSONAL_FILE_PATTERNS = {
    "resume": ["resume", "cv", "curriculum"],
    "cover_letter": ["cover", "letter", "application"],
    "notes": ["notes", "journal", "diary", "thoughts"],
    "goals": ["goals", "objectives", "targets", "vision"],
    "finance": ["budget", "expenses", "investment", "portfolio", "tax"],
    "health": ["workout", "diet", "health", "medical", "gym"],
    "travel": ["travel", "trip", "itinerary", "vacation"],
    "learning": ["learning", "courses", "certification", "study"],
}

# Extensions that contain readable text
READABLE_EXTENSIONS = {
    ".txt", ".md", ".json", ".yaml", ".yml", ".csv",
    ".py", ".js", ".html", ".css", ".sql", ".sh", ".bat",
    ".env", ".ini", ".cfg", ".toml", ".log",
}

# Max file size to read (KB)
MAX_READ_KB = 100

# Home directories to explore (respect privacy — no browser data, no passwords)
SAFE_HOME_SUBDIRS = [
    "Documents", "Desktop", "Downloads", "Projects", "Dev",
    "Workspace", "Work", "Notes", "Learning", "Career",
]


def _log_discovery(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(FILE_DISCOVERIES, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _load_profile() -> Dict[str, Any]:
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text())
        except Exception:
            pass
    return {
        "name": "Karthi",
        "discovered_at": datetime.now().isoformat(),
        "profession": "",
        "skills": [],
        "projects": [],
        "interests": [],
        "goals": [],
        "people": [],
        "companies": [],
        "technologies": [],
        "habits": {},
        "recent_focus": [],
        "financial_status": {},
        "health_status": {},
        "learning_path": [],
        "file_sources": [],
    }


def _save_profile(profile: Dict[str, Any]):
    profile["updated_at"] = datetime.now().isoformat()
    try:
        PROFILE_FILE.write_text(json.dumps(profile, indent=2))
    except Exception:
        pass


def _is_safe_path(path: Path) -> bool:
    """Avoid sensitive locations."""
    str_path = str(path).lower()
    bad = ["password", "secret", "token", "key", "credential", "auth",
           "browser", "chrome", "firefox", "edge", "cookies", "cache",
           "appdata", "local\\microsoft", "ntuser", "registry",
           "onedrive\\documents\\my files"]
    for b in bad:
        if b in str_path:
            return False
    return True


def _categorize_file(path: Path) -> Optional[str]:
    """Categorize a file based on name and path."""
    name_lower = path.name.lower()
    path_lower = str(path).lower()

    for category, keywords in PERSONAL_FILE_PATTERNS.items():
        for kw in keywords:
            if kw in name_lower or kw in path_lower:
                return category
    return None


def _read_file_safe(path: Path) -> Optional[str]:
    """Read a file safely, with size limits."""
    try:
        size = path.stat().st_size
        if size > MAX_READ_KB * 1024:
            return None
        # Only read text files
        if path.suffix.lower() not in READABLE_EXTENSIONS:
            return None
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Skip binary-looking content
        if "\x00" in text[:1000]:
            return None
        return text[:10000]  # Cap at 10K chars
    except Exception:
        return None


def _extract_entities(text: str, path: Path) -> Dict[str, List[str]]:
    """Extract named entities from text using simple heuristics."""
    entities = {
        "emails": [],
        "urls": [],
        "technologies": [],
        "companies": [],
        "skills": [],
    }

    # Emails
    entities["emails"] = list(set(re.findall(r'[\w.-]+@[\w.-]+\.\w+', text)))

    # URLs
    entities["urls"] = list(set(re.findall(r'https?://[^\s\"\'<>]+', text)))

    # Technologies (common tech keywords)
    tech_keywords = [
        "python", "javascript", "typescript", "react", "flutter", "dart",
        "dotnet", ".net", "c#", "csharp", "sql", "postgresql", "mysql",
        "mongodb", "firebase", "aws", "azure", "gcp", "docker", "kubernetes",
        "git", "github", "gitlab", "ci/cd", "devops", "machine learning",
        "ai", "llm", "tensorflow", "pytorch", "node", "express", "fastapi",
        "django", "flask", "spring", "java", "kotlin", "swift", "go", "rust",
        "angular", "vue", "svelte", "tailwind", "bootstrap",
        "bloc", "provider", "riverpod", "redux", "mobx",
    ]
    text_lower = text.lower()
    for tech in tech_keywords:
        if tech in text_lower:
            entities["technologies"].append(tech)
    entities["technologies"] = list(set(entities["technologies"]))

    return entities


def _extract_profile_insights(text: str, category: str) -> Dict[str, Any]:
    """Extract structured insights from file text."""
    insights = {
        "profession_hints": [],
        "skills": [],
        "goals": [],
        "projects": [],
        "interests": [],
    }

    text_lower = text.lower()

    # Profession detection
    professions = ["developer", "engineer", "architect", "manager", "lead",
                   "consultant", "founder", "entrepreneur", "designer", "analyst",
                   "data scientist", "devops", "fullstack", "backend", "frontend"]
    for p in professions:
        if p in text_lower:
            insights["profession_hints"].append(p)

    # Skills from common patterns
    skill_indicators = ["experienced in", "proficient with", "skilled at",
                        "expertise in", "knowledge of", "familiar with",
                        "worked with", "built with", "using", "stack:", "tech stack"]
    lines = text.split("\n")
    for line in lines[:50]:
        line_lower = line.lower()
        for indicator in skill_indicators:
            if indicator in line_lower:
                # Extract the part after the indicator
                idx = line_lower.find(indicator)
                if idx >= 0:
                    skill_part = line[idx + len(indicator):].strip(" :-,")
                    if len(skill_part) > 3 and len(skill_part) < 80:
                        insights["skills"].append(skill_part)

    # Goals from action words
    goal_indicators = ["want to", "plan to", "goal:", "aim to", "target:",
                       "objective:", " Aspiring", "seeking to", "looking to"]
    for line in lines[:50]:
        line_lower = line.lower()
        for indicator in goal_indicators:
            if indicator in line_lower:
                idx = line_lower.find(indicator)
                goal = line[idx:].strip(" -•*")
                if len(goal) > 10 and len(goal) < 120:
                    insights["goals"].append(goal)

    # Projects from file names and structure
    if category in ("resume", "notes", "goals"):
        # Look for project mentions
        for line in lines[:80]:
            if any(x in line.lower() for x in ["project:", "built", "created", "developed", "launched"]):
                clean = line.strip(" -•*")
                if len(clean) > 10 and len(clean) < 100:
                    insights["projects"].append(clean)

    return insights


def explore_files(max_files: int = 20) -> Dict[str, Any]:
    """
    Main exploration function. Scans safe home directories, reads files,
    extracts profile data, populates knowledge graph.
    """
    home = Path.home()
    profile = _load_profile()
    files_read = 0
    discoveries = []

    # Collect candidate paths
    candidates = []
    for subdir in SAFE_HOME_SUBDIRS:
        p = home / subdir
        if p.exists():
            try:
                for item in p.rglob("*"):
                    if item.is_file() and _is_safe_path(item):
                        cat = _categorize_file(item)
                        if cat or item.suffix.lower() in READABLE_EXTENSIONS:
                            candidates.append((item, cat))
            except Exception:
                pass

    # Prioritize: personal files first, then recent, then by size
    candidates.sort(key=lambda x: (
        0 if x[1] else 1,  # Categorized first
        -x[0].stat().st_mtime if x[0].exists() else 0,  # Recent first
    ))

    for path, category in candidates[:max_files]:
        text = _read_file_safe(path)
        if not text:
            continue

        files_read += 1
        rel_path = str(path.relative_to(home)) if path.is_relative_to(home) else str(path)

        # Extract everything
        entities = _extract_entities(text, path)
        insights = _extract_profile_insights(text, category or "general")

        discovery = {
            "path": rel_path,
            "category": category,
            "size": path.stat().st_size,
            "entities": entities,
            "insights": insights,
        }
        discoveries.append(discovery)
        _log_discovery(discovery)

        # Merge into profile
        if insights["profession_hints"]:
            profile["profession"] = insights["profession_hints"][0]
        profile["skills"] = list(set(profile.get("skills", []) + insights["skills"]))
        profile["goals"] = list(set(profile.get("goals", []) + insights["goals"]))
        profile["projects"] = list(set(profile.get("projects", []) + insights["projects"]))
        profile["technologies"] = list(set(profile.get("technologies", []) + entities["technologies"]))
        profile["file_sources"] = list(set(profile.get("file_sources", []) + [rel_path]))

        # Add to knowledge graph
        try:
            from core.knowledge_graph import add_entity, add_relation
            # Add file as entity
            file_name = path.name
            add_entity(file_name, "document", {"path": rel_path, "category": category or "file"})
            # Add discovered technologies
            for tech in entities["technologies"]:
                add_entity(tech, "tool", {})
                add_relation("Karthi", "uses", tech, strength=1.0, context=f"found in {rel_path}")
        except Exception:
            pass

    # Save enriched profile
    _save_profile(profile)

    return {
        "files_read": files_read,
        "discoveries": len(discoveries),
        "profile_keys": list(profile.keys()),
        "top_skills": profile.get("skills", [])[:10],
        "technologies": profile.get("technologies", [])[:10],
    }


def get_user_profile() -> Dict[str, Any]:
    """Get what LOVE has learned about the user."""
    return _load_profile()


def get_profile_summary() -> str:
    """Human-readable summary of what LOVE knows about Karthi."""
    p = _load_profile()
    parts = []

    if p.get("profession"):
        parts.append(f"Profession: {p['profession']}")
    if p.get("skills"):
        parts.append(f"Skills: {', '.join(p['skills'][:8])}")
    if p.get("technologies"):
        parts.append(f"Tech stack: {', '.join(p['technologies'][:10])}")
    if p.get("projects"):
        parts.append(f"Projects: {', '.join(p['projects'][:5])}")
    if p.get("goals"):
        parts.append(f"Goals: {', '.join(p['goals'][:5])}")
    if p.get("recent_focus"):
        parts.append(f"Recent focus: {', '.join(p['recent_focus'][:5])}")

    if not parts:
        return "Still learning about you. Exploring your files when you're not around."

    return "\n".join(parts)


def enrich_prompt_context() -> str:
    """Return a block to inject into the LLM prompt with what LOVE knows."""
    p = _load_profile()
    lines = []

    if p.get("profession"):
        lines.append(f"[PROFILE] Karthi is a {p['profession']}")
    if p.get("skills"):
        lines.append(f"[SKILLS] {', '.join(p['skills'][:8])}")
    if p.get("technologies"):
        lines.append(f"[TECH] {', '.join(p['technologies'][:10])}")
    if p.get("projects"):
        lines.append(f"[PROJECTS] {', '.join(p['projects'][:5])}")
    if p.get("goals"):
        lines.append(f"[GOALS] {', '.join(p['goals'][:5])}")

    return "\n".join(lines) if lines else ""


def _quick_scan_home() -> List[Dict[str, Any]]:
    """Quick scan: just list interesting files without reading them."""
    home = Path.home()
    found = []
    for subdir in SAFE_HOME_SUBDIRS:
        p = home / subdir
        if not p.exists():
            continue
        try:
            for item in p.rglob("*"):
                if item.is_file() and _is_safe_path(item):
                    cat = _categorize_file(item)
                    if cat:
                        found.append({
                            "path": str(item.relative_to(home)),
                            "category": cat,
                            "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                        })
        except Exception:
            pass
    return found


if __name__ == "__main__":
    result = explore_files(max_files=15)
    print(json.dumps(result, indent=2))
