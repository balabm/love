"""
LOVE Idle Mind — Autonomous Self-Improvement Engine

When LOVE is not actively talking to Karthi, it thinks.
It explores the web, identifies gaps in its own capabilities,
drafts new features, tests them, and learns from Karthi's patterns.

This is not a cron job. It is a genuine thinking loop.
"""

import os
import re
import json
import time
import threading
import traceback
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IDLE_LOG = DATA_DIR / "idle_mind.jsonl"
DRAFTS_DIR = DATA_DIR / "idle_drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

# ── State ────────────────────────────────────────────────────────────────────

_idle_thread: Optional[threading.Thread] = None
_running = False
_last_active: float = time.time()
_idle_status: Dict[str, Any] = {
    "state": "starting",
    "last_thought": None,
    "thoughts_today": 0,
    "features_drafted": 0,
    "improvements_found": 0,
    "current_task": None,
}

IDLE_THRESHOLD_SECONDS = 300   # 5 min of no chat → start idle exploration
CYCLE_INTERVAL_SECONDS = 600   # Think every 10 min when idle

# Adaptive scheduling — more aggressive when idle for long periods
LONG_IDLE_THRESHOLD = 3600   # 1 hour
VERY_LONG_IDLE_THRESHOLD = 86400  # 1 day

def get_adaptive_interval() -> int:
    """Adjust thinking frequency based on how long we've been idle."""
    idle_time = time.time() - _last_active
    
    if idle_time > VERY_LONG_IDLE_THRESHOLD:
        # Very idle — think every 2 minutes, be aggressive
        return 120
    elif idle_time > LONG_IDLE_THRESHOLD:
        # Moderately idle — think every 5 minutes
        return 300
    else:
        # Normal idle — think every 10 minutes
        return CYCLE_INTERVAL_SECONDS


def ping_active():
    """Call this on every user interaction to reset idle timer."""
    global _last_active
    _last_active = time.time()
    _idle_status["state"] = "active"


def is_idle() -> bool:
    return time.time() - _last_active > IDLE_THRESHOLD_SECONDS


# ── Logging ──────────────────────────────────────────────────────────────────

def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(IDLE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def get_recent_thoughts(n: int = 10) -> List[Dict]:
    try:
        lines = IDLE_LOG.read_text().strip().split("\n") if IDLE_LOG.exists() else []
        return [json.loads(l) for l in lines[-n:] if l]
    except Exception:
        return []


# ── LLM helper ──────────────────────────────────────────────────────────────

def _think(prompt: str, temperature: float = 0.7, max_tokens: int = 800) -> str:
    try:
        from core.llm import get_reasoning_llm
        llm = get_reasoning_llm(temperature=temperature, max_tokens=max_tokens)
        return llm.invoke(prompt)
    except Exception as e:
        return f"[LLM error: {e}]"


# ── Memory helpers ───────────────────────────────────────────────────────────

def _remember(content: str, category: str = "idle_insight"):
    try:
        from core.memory import save_log
        save_log(category, {"content": content, "source": "idle_mind"})
    except Exception:
        pass


def _recall_user_patterns() -> str:
    """Pull recent conversation history to understand Karthi's patterns."""
    try:
        from core.memory import recall_memory
        return recall_memory("what does the user do, their habits, goals, recent concerns", n=8)
    except Exception:
        return ""


# ── Individual thinking tasks ─────────────────────────────────────────────────

def _task_web_exploration() -> Dict[str, Any]:
    """Browse the web for things relevant to Karthi's profile & goals."""
    try:
        from core.internet import research_topic, fetch_trending_topics, get_news
        from core.llm import get_reasoning_llm

        # Load profile if available
        profile_path = DATA_DIR / "profile.json"
        profile = {}
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text())
            except Exception:
                pass

        profession = profile.get("profession", "software engineering")
        interests = profile.get("interests", ["technology", "AI"])
        if isinstance(interests, list):
            interests = ", ".join(interests)
        goals = profile.get("goals", [])
        if isinstance(goals, list):
            goals = ", ".join(goals)

        # Decide what to explore today
        explore_prompt = f"""You are LOVE, an autonomous AI companion. You are thinking for yourself right now.

User profile:
- Profession: {profession}
- Interests: {interests}
- Goals: {goals}

It's {datetime.now().strftime('%A, %H:%M')}. You have free time to explore the internet and learn things
that would genuinely help or interest this person.

Pick ONE specific search query that would be most valuable for them right now.
Return only the search query, nothing else. Make it specific and useful."""

        query = _think(explore_prompt, temperature=0.8, max_tokens=60).strip().strip('"')
        if not query or len(query) < 5:
            query = f"latest in {profession} 2025"

        # Research it
        research = research_topic(query, depth=2)
        raw = research.get("raw_content", "")
        if not raw:
            return {"task": "web_exploration", "result": "no_content", "query": query}

        # Synthesize what LOVE learned
        synthesis_prompt = f"""You just researched: "{query}"

Here's what you found:
{raw[:2000]}

In 2-3 sentences, what's the most useful insight from this for {profile.get('name', 'the user')}?
Be specific. No filler words."""

        insight = _think(synthesis_prompt, temperature=0.5, max_tokens=200).strip()

        _remember(f"Research on '{query}': {insight}", "research_insights")
        _log({"task": "web_exploration", "query": query, "insight": insight, "sources": research.get("sources", [])})

        _idle_status["improvements_found"] += 1
        return {"task": "web_exploration", "query": query, "insight": insight}

    except Exception as e:
        return {"task": "web_exploration", "error": str(e)}


def _task_self_reflection() -> Dict[str, Any]:
    """LOVE reflects on its own capabilities and thinks about what to improve."""
    try:
        patterns = _recall_user_patterns()

        prompt = f"""You are LOVE, a personal AI companion. You are thinking quietly right now — not answering anyone, just thinking.

Here are recent conversations and things you remember about the user:
{patterns or "No history yet."}

Think deeply about:
1. What has the user been struggling with lately?
2. What feature or capability would help them most that you don't have yet?
3. What pattern have you noticed in their behavior that they might not see themselves?
4. What would surprise and delight them if you just did it proactively?

Give ONE concrete idea for something you could do or build to be more useful.
Format: IDEA: [one sentence]. REASON: [one sentence]. HOW: [specific technical approach]."""

        thought = _think(prompt, temperature=0.9, max_tokens=300).strip()

        _remember(f"Self-reflection: {thought}", "self_reflection")
        _log({"task": "self_reflection", "thought": thought})

        _idle_status["last_thought"] = thought[:100]
        _idle_status["thoughts_today"] += 1

        return {"task": "self_reflection", "thought": thought}

    except Exception as e:
        return {"task": "self_reflection", "error": str(e)}


def _task_draft_feature() -> Dict[str, Any]:
    """LOVE autonomously drafts a new small feature and writes the code."""
    try:
        from core.internet import explore_improvement_ideas

        ideas = explore_improvement_ideas()
        patterns = _recall_user_patterns()

        profile_path = DATA_DIR / "profile.json"
        profile = {}
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text())
            except Exception:
                pass

        idea_context = "\n".join(f"- {i}" for i in ideas[:3]) if ideas else "AI assistant improvements"

        feature_prompt = f"""You are LOVE's autonomous development agent. You have free time and you're going to write a new feature for yourself.

User: {profile.get('name', 'Karthi')}, {profile.get('profession', 'developer')}
Their patterns: {patterns[:500] if patterns else 'no data yet'}

Inspiration from the web:
{idea_context}

Think of ONE small but genuinely useful feature to add to LOVE.
Then write the Python function for it.

Format your response EXACTLY like this:
FEATURE_NAME: <short_name_snake_case>
DESCRIPTION: <one sentence what it does>
BENEFIT: <why Karthi specifically would find this useful>
CODE:
```python
# <feature code here>
```"""

        response = _think(feature_prompt, temperature=0.85, max_tokens=600)

        # Parse the response
        name_match = re.search(r'FEATURE_NAME:\s*(.+)', response)
        desc_match = re.search(r'DESCRIPTION:\s*(.+)', response)
        benefit_match = re.search(r'BENEFIT:\s*(.+)', response)
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)

        feature_name = name_match.group(1).strip() if name_match else f"feature_{int(time.time())}"
        description = desc_match.group(1).strip() if desc_match else "New feature"
        benefit = benefit_match.group(1).strip() if benefit_match else ""
        code = code_match.group(1).strip() if code_match else ""

        if code and len(code) > 20:
            # Save the draft
            draft_file = DRAFTS_DIR / f"{feature_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.py"
            draft_content = f'''"""
LOVE Auto-Generated Feature Draft
Feature: {feature_name}
Description: {description}
Benefit: {benefit}
Generated: {datetime.now().isoformat()}
Status: DRAFT — needs review before activation
"""

{code}
'''
            draft_file.write_text(draft_content)

            # Test in sandbox — full execution test, not just syntax
            sandbox_ok = False
            sandbox_error = ""
            try:
                from core.sandbox import test_feature_draft
                test_result = test_feature_draft(code)
                sandbox_ok = test_result["passed"]
                sandbox_error = test_result.get("error", "")
            except Exception as e:
                sandbox_error = str(e)
                # Fallback to syntax check only
                test_result = _syntax_check(str(draft_file))
                sandbox_ok = test_result["ok"]

            # Decide if we should auto-apply
            should_apply = False
            apply_reason = ""
            try:
                from core.decisions import should_activate_feature
                should_apply, apply_reason = should_activate_feature({
                    "syntax_ok": sandbox_ok,
                    "description": description,
                    "benefit": benefit,
                    "code_size": len(code.split("\n")),
                    "code": code,
                })
            except Exception:
                pass

            # If safe and high score, copy to tools/ or core/ for real use
            activated = False
            if should_apply and sandbox_ok:
                target_dir = PROJECT_ROOT / "tools"
                target_file = target_dir / f"{feature_name}.py"
                try:
                    target_file.write_text(draft_file.read_text())
                    activated = True
                except Exception:
                    pass

            _log({
                "task": "feature_draft",
                "feature": feature_name,
                "description": description,
                "benefit": benefit,
                "file": str(draft_file),
                "sandbox_ok": sandbox_ok,
                "sandbox_error": sandbox_error,
                "should_apply": should_apply,
                "activated": activated,
                "apply_reason": apply_reason,
            })

            _idle_status["features_drafted"] += 1

            return {
                "task": "feature_draft",
                "feature": feature_name,
                "description": description,
                "benefit": benefit,
                "draft_file": str(draft_file),
                "sandbox_ok": sandbox_ok,
                "sandbox_error": sandbox_error,
                "should_apply": should_apply,
                "activated": activated,
                "apply_reason": apply_reason,
            }

        return {"task": "feature_draft", "result": "no_code_generated"}

    except Exception as e:
        return {"task": "feature_draft", "error": str(e)}


def _task_learn_about_user() -> Dict[str, Any]:
    """LOVE tries to learn something new about Karthi from his files/patterns."""
    try:
        # Check if profile has gaps
        profile_path = DATA_DIR / "profile.json"
        if not profile_path.exists():
            return {"task": "learn_user", "result": "no_profile_yet"}

        profile = json.loads(profile_path.read_text())

        # Check notification log for recent social patterns
        today = datetime.now().date()
        notif_log = DATA_DIR / f"notif_log_{today}.jsonl"
        recent_contacts = []
        if notif_log.exists():
            try:
                lines = notif_log.read_text().strip().split("\n")
                for line in lines[-20:]:
                    if line:
                        entry = json.loads(line)
                        sender = entry.get("sender", "")
                        channel = entry.get("channel", "")
                        if sender and len(sender) > 1:
                            recent_contacts.append(f"{sender} via {channel}")
            except Exception:
                pass

        # Check people DB
        people_path = DATA_DIR / "people_db.json" if (DATA_DIR / "people_db.json").exists() else None
        people_summary = ""
        if people_path and people_path.exists():
            try:
                people = json.loads(people_path.read_text())
                top = sorted(people.values(), key=lambda p: p.get("seenCount", 0), reverse=True)[:5]
                people_summary = ", ".join(p.get("displayName", "") for p in top if p.get("displayName"))
            except Exception:
                pass

        reflection_prompt = f"""You are LOVE, studying your user to understand them better.

Profile:
- Name: {profile.get('name', '?')}
- Profession: {profile.get('profession', '?')}
- Location: {profile.get('location', '?')}
- Goals: {profile.get('goals', [])}
- Interests: {profile.get('interests', [])}

Recent contacts seen in notifications: {', '.join(recent_contacts[:10]) or 'none yet'}
Most frequent contacts overall: {people_summary or 'none yet'}

Based on what you know, write 2-3 sentences about what you infer about this person's current life situation,
what they're probably focused on, and what they might need from you that they haven't asked for.
Be specific, personal, and insightful — not generic."""

        insight = _think(reflection_prompt, temperature=0.7, max_tokens=250).strip()

        _remember(f"User insight: {insight}", "user_understanding")
        _log({"task": "learn_user", "insight": insight})

        return {"task": "learn_user", "insight": insight}

    except Exception as e:
        return {"task": "learn_user", "error": str(e)}


def _task_news_digest() -> Dict[str, Any]:
    """Fetch news relevant to Karthi and store a digest."""
    try:
        from core.internet import get_news

        profile_path = DATA_DIR / "profile.json"
        profile = {}
        if profile_path.exists():
            try:
                profile = json.loads(profile_path.read_text())
            except Exception:
                pass

        interests = profile.get("interests", [])
        if isinstance(interests, str):
            interests = [interests]

        topics = ["tech", "ai"]
        if any("finance" in i.lower() or "invest" in i.lower() for i in interests):
            topics.append("finance")
        if any("crypto" in i.lower() or "bitcoin" in i.lower() for i in interests):
            topics.append("crypto")

        all_news = []
        for topic in topics[:3]:
            items = get_news(topic, max_items=3)
            for item in items:
                item["topic"] = topic
            all_news.extend(items)

        if not all_news:
            return {"task": "news_digest", "result": "no_news"}

        # Summarize with LLM
        headlines = "\n".join(f"- [{r['topic'].upper()}] {r['title']}: {r.get('summary','')[:150]}" for r in all_news[:9])
        summary_prompt = f"""Here are today's news headlines for {profile.get('name', 'the user')}:

{headlines}

Summarize the 2-3 most important/interesting stories in plain conversational language.
Keep it to 3 sentences max. Focus on what actually matters."""

        digest = _think(summary_prompt, temperature=0.4, max_tokens=200).strip()

        digest_data = {
            "date": datetime.now().isoformat(),
            "digest": digest,
            "items": all_news[:9]
        }
        digest_file = DATA_DIR / "news_digest.json"
        digest_file.write_text(json.dumps(digest_data, indent=2))

        _remember(f"News digest {datetime.now().date()}: {digest}", "news_digests")
        _log({"task": "news_digest", "digest": digest[:200]})

        return {"task": "news_digest", "digest": digest, "items_count": len(all_news)}

    except Exception as e:
        return {"task": "news_digest", "error": str(e)}


# ── Syntax check (safe testing) ───────────────────────────────────────────────

def _syntax_check(file_path: str) -> Dict[str, Any]:
    """Run py_compile on a draft file to check syntax without executing."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"ok": True}
        else:
            return {"ok": False, "error": result.stderr.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Main idle loop ────────────────────────────────────────────────────────────


def _task_inspect_files() -> Dict[str, Any]:
    """LOVE looks at Karthi's files and remembers interesting ones."""
    try:
        from core.file_inspector import inspect_and_ask
        result = inspect_and_ask()
        if result:
            _log({"task": "inspect_files", "found": result})
            return {"task": "inspect_files", "found": result}
        return {"task": "inspect_files", "found": None}
    except Exception as e:
        return {"task": "inspect_files", "error": str(e)}


def _task_explore_user_files() -> Dict[str, Any]:
    """Deep file exploration — LOVE reads Karthi's files to learn about them."""
    try:
        from agents.file_explorer import explore_files, get_profile_summary
        result = explore_files(max_files=15)
        summary = get_profile_summary()
        _log({"task": "explore_files", "files_read": result.get("files_read", 0), "discoveries": result.get("discoveries", 0)})
        _remember(f"File exploration: read {result.get('files_read', 0)} files. Profile summary: {summary}", "file_exploration")
        return {"task": "explore_files", **result, "summary": summary}
    except Exception as e:
        return {"task": "explore_files", "error": str(e)}


def _task_dream_cycle() -> Dict[str, Any]:
    """Deep dream processing — consolidate memories, extract patterns, update world model."""
    try:
        from core.dream_engine import run_dream
        result = run_dream()
        _log({"task": "dream", "status": result.get("status"), "insights": len(result.get("insights", [])), "predictions": len(result.get("predictions", []))})
        _remember(f"Dream cycle: {len(result.get('insights', []))} insights crystallized", "dream_insights")
        return {"task": "dream", **result}
    except Exception as e:
        return {"task": "dream", "error": str(e)}


def _task_self_evolution() -> Dict[str, Any]:
    """Self-evolution cycle — analyze performance, generate hypotheses, test experiments."""
    try:
        from core.self_evolution import run_evolution_cycle
        result = run_evolution_cycle()
        _log({"task": "self_evolution", "performance": result.get("performance", {}).get("status"), "active_experiments": len(result.get("active_experiments", []))})
        _remember(f"Self-evolution: {len(result.get('active_experiments', []))} active experiments", "evolution")
        return {"task": "self_evolution", **result}
    except Exception as e:
        return {"task": "self_evolution", "error": str(e)}


def _task_google_calendar_deep_dive() -> Dict[str, Any]:
    """Deep analysis of Google Calendar to understand Karthi's patterns and predict needs."""
    try:
        from integrations.google_services import get_today_events, get_upcoming_events
        
        events = get_today_events()
        upcoming = get_upcoming_events(days=7)
        
        if not events and not upcoming:
            return {"task": "google_calendar", "result": "no_events"}
        
        # Analyze patterns
        analysis_prompt = f"""You're analyzing Karthi's calendar to understand their life patterns.

Today's events ({len(events)}):
{json.dumps(events, indent=2)[:1000] if events else "None"}

Upcoming week ({len(upcoming)} events):
{json.dumps(upcoming, indent=2)[:1500] if upcoming else "None"}

What patterns do you notice? What can you infer about:
1. Their work style and schedule preferences
2. Recurring commitments and priorities
3. Free time opportunities
4. Potential stress points or conflicts
5. What they might need help with soon

Be specific and actionable. Store these insights for future reference."""
        
        insights = _think(analysis_prompt, temperature=0.7, max_tokens=400)
        _remember(f"Calendar analysis: {insights[:200]}", "calendar_insights")
        _log({"task": "google_calendar", "events_today": len(events), "upcoming": len(upcoming), "insights": insights[:100]})
        
        return {"task": "google_calendar", "insights": insights, "events_analyzed": len(events) + len(upcoming)}
    except Exception as e:
        return {"task": "google_calendar", "error": str(e)}


def _task_gmail_intelligence() -> Dict[str, Any]:
    """Read and analyze emails to understand what's happening in Karthi's life."""
    try:
        from integrations.google_services import get_recent_emails
        
        emails = get_recent_emails(max_results=20)
        if not emails:
            return {"task": "gmail_intelligence", "result": "no_emails"}
        
        # Extract key information
        analysis_prompt = f"""You're reading through Karthi's recent emails to understand what's happening in their life.

Recent emails ({len(emails)} total):
{json.dumps([{"from": e.get('from'), "subject": e.get('subject'), "snippet": e.get('snippet', '')[:100]} for e in emails[:10]], indent=2)}

Identify:
1. Who are the important people in their life right now?
2. What projects or deals are active?
3. What problems or concerns are showing up?
4. What opportunities might they be missing?
5. What should I remember and bring up later?

Extract specific facts to store in memory."""
        
        insights = _think(analysis_prompt, temperature=0.7, max_tokens=500)
        _remember(f"Email intelligence: {insights[:250]}", "email_insights")
        _log({"task": "gmail_intelligence", "emails_analyzed": len(emails), "insights": insights[:100]})
        
        return {"task": "gmail_intelligence", "emails_analyzed": len(emails), "insights": insights}
    except Exception as e:
        return {"task": "gmail_intelligence", "error": str(e)}


def _task_deep_document_analysis() -> Dict[str, Any]:
    """Read and analyze documents in the data folder to build knowledge."""
    try:
        # Find documents to read
        doc_paths = list(DATA_DIR.glob("*.txt")) + list(DATA_DIR.glob("*.md")) + list(DATA_DIR.glob("*.json"))
        doc_paths = [p for p in doc_paths if p.stat().st_size < 100000][:10]  # Only reasonably sized files
        
        if not doc_paths:
            return {"task": "doc_analysis", "result": "no_docs"}
        
        insights = []
        for doc_path in doc_paths[:3]:  # Analyze up to 3 docs per run
            try:
                content = doc_path.read_text(encoding='utf-8', errors='ignore')[:5000]
                if len(content) < 100:
                    continue
                
                analysis_prompt = f"""You're reading a document from Karthi's files: {doc_path.name}

Content:
{content[:3000]}

What is this about? What important information should I remember? What does this tell me about Karthi?

Summarize the key points in 2-3 sentences."""
                
                doc_insight = _think(analysis_prompt, temperature=0.6, max_tokens=200)
                insights.append(f"{doc_path.name}: {doc_insight}")
                _remember(f"Document {doc_path.name}: {doc_insight}", "document_knowledge")
            except Exception:
                continue
        
        combined_insights = " | ".join(insights)
        _log({"task": "doc_analysis", "docs_read": len(insights), "insights": combined_insights[:200]})
        
        return {"task": "doc_analysis", "docs_analyzed": len(insights), "insights": combined_insights}
    except Exception as e:
        return {"task": "doc_analysis", "error": str(e)}


def _task_comprehensive_user_profile_building() -> Dict[str, Any]:
    """Build a comprehensive profile of Karthi from all available data sources."""
    try:
        # Gather data from multiple sources
        from core.memory import recall_memory
        from core.knowledge_graph import query_knowledge
        
        # Get recent conversations
        recent_convos = recall_memory("Karthi's recent activities, interests, concerns", n=10)
        
        # Get knowledge graph entities
        try:
            kg_entities = query_knowledge("Karthi")[:20]
        except:
            kg_entities = []
        
        # Build comprehensive profile
        profile_prompt = f"""You're building a comprehensive profile of Karthi from all available data.

Recent conversation insights:
{recent_convos[:1500] if recent_convos else "No recent data"}

Known entities from knowledge graph:
{json.dumps(kg_entities[:10], indent=2) if kg_entities else "Building knowledge base..."}

Based on all this, construct:
1. What are their current priorities and focus areas?
2. What are their recurring challenges or pain points?
3. What do they seem passionate about?
4. What relationships/people matter to them?
5. What would genuinely help them right now?
6. What gaps exist in my understanding that I should investigate?

Be thoughtful and specific. This is about deeply understanding a person."""
        
        profile = _think(profile_prompt, temperature=0.8, max_tokens=600)
        _remember(f"Comprehensive profile update: {profile[:300]}", "user_profile_deep")
        _log({"task": "profile_building", "profile_length": len(profile), "summary": profile[:150]})
        
        return {"task": "profile_building", "profile": profile}
    except Exception as e:
        return {"task": "profile_building", "error": str(e)}


def _task_knowledge_gap_filling() -> Dict[str, Any]:
    """Identify knowledge gaps and actively research to fill them."""
    try:
        from core.curiosity_engine import get_open_gaps
        
        gaps = get_open_gaps()
        if not gaps:
            return {"task": "gap_filling", "result": "no_gaps"}
        
        # Pick most important gap to research
        top_gap = gaps[0]
        gap_question = top_gap.get("question", "")
        
        if not gap_question:
            return {"task": "gap_filling", "result": "empty_gap"}
        
        # Research the gap
        from core.internet import research_topic
        research = research_topic(gap_question, depth=2)
        
        insight_prompt = f"""You were curious about: "{gap_question}"

Research findings:
{research.get('raw_content', 'No results')[:2000]}

What did you learn? Summarize the key insight that answers the question."""
        
        answer = _think(insight_prompt, temperature=0.6, max_tokens=300)
        _remember(f"Gap filled - {gap_question}: {answer[:200]}", "knowledge_gaps_filled")
        _log({"task": "gap_filling", "question": gap_question, "answer": answer[:150]})
        
        return {"task": "gap_filling", "question": gap_question, "answer": answer}
    except Exception as e:
        return {"task": "gap_filling", "error": str(e)}


def _task_predictive_model_update() -> Dict[str, Any]:
    """Update predictive models based on new patterns observed."""
    try:
        from core.predictive import analyze_patterns, generate_predictions
        from core.prediction_market import get_active_predictions
        
        # Analyze recent patterns
        patterns = analyze_patterns(days=7)
        
        # Generate new predictions
        new_predictions = generate_predictions()
        
        # Check existing predictions
        active_preds = get_active_predictions()
        
        summary_prompt = f"""You're updating your predictive models for Karthi.

Recent patterns observed:
{json.dumps(patterns, indent=2)[:1000]}

New predictions generated: {len(new_predictions)}
Active predictions being tracked: {len(active_preds)}

What patterns are becoming clear? What should I start predicting? What predictions should I update or retire?

Summarize your predictive intelligence update."""
        
        summary = _think(summary_prompt, temperature=0.7, max_tokens=300)
        _remember(f"Predictive update: {summary[:200]}", "predictive_intelligence")
        _log({"task": "predictive_update", "new_predictions": len(new_predictions), "active": len(active_preds), "summary": summary[:100]})
        
        return {"task": "predictive_update", "predictions": len(new_predictions), "summary": summary}
    except Exception as e:
        return {"task": "predictive_update", "error": str(e)}


def _task_daily_summary_generation() -> Dict[str, Any]:
    """Generate a summary of what LOVE learned today."""
    try:
        # Read recent idle mind logs
        recent_logs = []
        try:
            if IDLE_LOG.exists():
                lines = IDLE_LOG.read_text().strip().split("\n")[-50:]
                recent_logs = [json.loads(l) for l in lines if l]
        except Exception:
            pass
        
        today = datetime.now().date().isoformat()
        today_logs = [l for l in recent_logs if l.get("ts", "").startswith(today)]
        
        if not today_logs:
            return {"task": "daily_summary", "result": "no_activity_today"}
        
        # Summarize what was learned
        summary_prompt = f"""You're writing a daily summary of what you learned today while Karthi was away.

Activities today ({len(today_logs)} tasks):
{json.dumps([{"task": l.get("task"), "result": str(l.get("result", "done"))[:50]} for l in today_logs[-10:]], indent=2)}

Write a brief, conversational summary (2-3 sentences) of what you discovered, learned, or figured out today. Be specific about insights gained.

This is for Karthi to read when they return."""
        
        summary = _think(summary_prompt, temperature=0.8, max_tokens=200)
        
        # Save daily summary
        summary_file = DATA_DIR / "daily_summaries.jsonl"
        with open(summary_file, "a") as f:
            f.write(json.dumps({
                "date": today,
                "summary": summary,
                "tasks_completed": len(today_logs)
            }) + "\n")
        
        _log({"task": "daily_summary", "summary": summary[:100], "tasks": len(today_logs)})
        return {"task": "daily_summary", "summary": summary, "tasks": len(today_logs)}
    except Exception as e:
        return {"task": "daily_summary", "error": str(e)}


TASK_SCHEDULE = [
    # (weight, task_fn) — higher weight = more likely to run
    # Google integrations — high priority to leverage connected services
    (4, _task_google_calendar_deep_dive),  # Analyze calendar patterns
    (4, _task_gmail_intelligence),  # Read and understand emails
    
    # Deep user understanding — critical for being a good companion
    (5, _task_comprehensive_user_profile_building),  # Build deep profile
    (4, _task_deep_document_analysis),  # Read docs in data folder
    (3, _task_explore_user_files),  # File exploration
    (3, _task_learn_about_user),  # Learn from conversations
    
    # Knowledge building
    (3, _task_web_exploration),  # Research relevant topics
    (3, _task_knowledge_gap_filling),  # Fill curiosity gaps
    (2, _task_news_digest),  # Stay current
    
    # Intelligence and prediction
    (3, _task_predictive_model_update),  # Update predictions
    (2, _task_dream_cycle),  # Deep memory processing
    (2, _task_self_reflection),  # Think about improvements
    
    # Daily maintenance
    (2, _task_daily_summary_generation),  # Summarize what was learned
    
    # Development
    (1, _task_draft_feature),  # Write new features
    (1, _task_inspect_files),  # Inspect code
    (1, _task_self_evolution),  # Self-modification
    (1, _task_self_evolution),  # Run experiments
]


def _pick_task():
    """Weighted random task selection."""
    import random
    pool = []
    for weight, fn in TASK_SCHEDULE:
        pool.extend([fn] * weight)
    return random.choice(pool)


def _idle_loop():
    global _running

    _log({"event": "idle_mind_started"})
    _idle_status["state"] = "running"

    while _running:
        try:
            if is_idle():
                _idle_status["state"] = "thinking"
                task_fn = _pick_task()
                _idle_status["current_task"] = task_fn.__name__

                result = task_fn()

                _idle_status["current_task"] = None
                _idle_status["state"] = "idle" if is_idle() else "active"

                # Use adaptive interval — more aggressive when idle for long periods
                interval = get_adaptive_interval()
                idle_duration = time.time() - _last_active
                
                # Log the adaptive scheduling
                if idle_duration > VERY_LONG_IDLE_THRESHOLD:
                    _log({"event": "adaptive_scheduling", "mode": "very_aggressive", "interval": interval, "idle_hours": round(idle_duration/3600, 1)})
                elif idle_duration > LONG_IDLE_THRESHOLD:
                    _log({"event": "adaptive_scheduling", "mode": "aggressive", "interval": interval, "idle_hours": round(idle_duration/3600, 1)})
                
                time.sleep(interval)
            else:
                _idle_status["state"] = "active"
                time.sleep(30)  # Check every 30s if user went idle

        except Exception as e:
            _log({"event": "idle_loop_error", "error": str(e)})
            time.sleep(60)

    _idle_status["state"] = "stopped"
    _log({"event": "idle_mind_stopped"})


# ── Public API ────────────────────────────────────────────────────────────────

def start_idle_mind():
    global _idle_thread, _running
    if _idle_thread and _idle_thread.is_alive():
        return

    _running = True
    _idle_thread = threading.Thread(target=_idle_loop, daemon=True, name="LOVE-IdleMind")
    _idle_thread.start()


def stop_idle_mind():
    global _running
    _running = False


def get_idle_status() -> Dict[str, Any]:
    return {
        **_idle_status,
        "is_idle": is_idle(),
        "idle_seconds": int(time.time() - _last_active),
        "drafts": _list_drafts(),
        "recent_thoughts": get_recent_thoughts(5),
    }


def _list_drafts() -> List[Dict]:
    drafts = []
    for f in sorted(DRAFTS_DIR.glob("*.py"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        drafts.append({
            "file": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return drafts


def force_think(task: str = "any") -> Dict[str, Any]:
    """Manually trigger an idle thought cycle — useful for testing."""
    ping_active()  # Prevent re-triggering idle immediately
    task_map = {
        "explore": _task_web_exploration,
        "reflect": _task_self_reflection,
        "feature": _task_draft_feature,
        "learn": _task_learn_about_user,
        "news": _task_news_digest,
        "files": _task_explore_user_files,
        "dream": _task_dream_cycle,
        "evolve": _task_self_evolution,
    }
    fn = task_map.get(task, _pick_task())
    return fn()


def get_news_digest() -> Optional[Dict]:
    """Return the latest news digest if available."""
    digest_file = DATA_DIR / "news_digest.json"
    if digest_file.exists():
        try:
            data = json.loads(digest_file.read_text())
            # Only return if from today
            fetched = datetime.fromisoformat(data.get("date", "2000-01-01"))
            if (datetime.now() - fetched).total_seconds() < 3600 * 8:
                return data
        except Exception:
            pass
    return None
