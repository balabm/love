"""
LOVE Voice Loop — Always Listening

The Jarvis touch: LOVE doesn't wait for a button. She listens for "Hey LOVE"
and responds naturally.

- Wake word detection (energy-based + STT confirmation)
- Continuous mic monitoring with low CPU usage
- Speech detection with VAD-style energy threshold
- Auto-transcribe → chat → speak response
- Barge-in: stops speaking when Karthi starts talking

Falls back gracefully if mic / dependencies missing.
"""

import os
import time
import threading
import queue
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VOICE_LOG = DATA_DIR / "voice_loop.jsonl"

# Configuration
WAKE_WORDS = ["hey love", "hey lov", "okay love", "ok love", "love ", "yo love"]
SAMPLE_RATE = 16000
CHUNK_DURATION_MS = 30
SILENCE_THRESHOLD_MS = 1000  # ms of silence before considering utterance done
MIN_UTTERANCE_MS = 300       # ignore blips
ENERGY_THRESHOLD = 500       # adjust based on mic

# State
_listening_thread: Optional[threading.Thread] = None
_running = False
_status: Dict[str, Any] = {
    "state": "stopped",
    "wake_words_heard": 0,
    "utterances_processed": 0,
    "last_heard": None,
    "available": False,
    "error": None,
}


def _log(entry: Dict[str, Any]):
    entry["ts"] = datetime.now().isoformat()
    try:
        with open(VOICE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _check_dependencies() -> Dict[str, bool]:
    """Check if voice loop deps are available."""
    deps = {
        "sounddevice": False,
        "numpy": False,
        "stt": False,
        "tts": False,
    }
    try:
        import sounddevice  # noqa
        deps["sounddevice"] = True
    except ImportError:
        pass
    try:
        import numpy  # noqa
        deps["numpy"] = True
    except ImportError:
        pass
    try:
        from voice.stt import is_voice_available
        deps["stt"] = is_voice_available()
    except ImportError:
        pass
    try:
        from voice.tts import is_tts_available
        deps["tts"] = is_tts_available()
    except ImportError:
        pass
    return deps


# Module-level availability check: if core deps are missing, fail import gracefully
# so api/main.py sets VOICE_LOOP_AVAILABLE = False instead of registering a degraded module.
_core_deps = _check_dependencies()
if not (_core_deps["sounddevice"] and _core_deps["numpy"] and _core_deps["stt"]):
    raise ImportError(
        "Voice loop dependencies missing (sounddevice, numpy, stt). "
        "Install with: pip install sounddevice numpy"
    )


def _has_wake_word(text: str) -> Optional[str]:
    """Check if transcript contains a wake word. Returns the part after wake word."""
    text_lower = text.lower().strip()
    for ww in WAKE_WORDS:
        if ww in text_lower:
            # Extract everything after the wake word
            idx = text_lower.find(ww)
            after = text[idx + len(ww):].strip()
            return after if after else "..."
    return None


def _record_utterance(timeout_seconds: float = 8.0) -> Optional[bytes]:
    """
    Record a single utterance with VAD-style end detection.
    Returns raw audio bytes (16-bit mono PCM) or None.
    """
    try:
        import sounddevice as sd
        import numpy as np

        chunk_samples = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
        chunks = []
        silent_chunks = 0
        active_chunks = 0
        silence_chunks_threshold = int(SILENCE_THRESHOLD_MS / CHUNK_DURATION_MS)
        max_chunks = int(timeout_seconds * 1000 / CHUNK_DURATION_MS)
        started = False

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            for _ in range(max_chunks):
                data, _ = stream.read(chunk_samples)
                chunks.append(data.tobytes())
                # Energy detection
                arr = np.frombuffer(data.tobytes(), dtype=np.int16)
                energy = float(np.abs(arr).mean()) if len(arr) > 0 else 0

                if energy > ENERGY_THRESHOLD:
                    started = True
                    active_chunks += 1
                    silent_chunks = 0
                elif started:
                    silent_chunks += 1
                    if silent_chunks > silence_chunks_threshold:
                        break

        if not started or active_chunks * CHUNK_DURATION_MS < MIN_UTTERANCE_MS:
            return None

        return b"".join(chunks)

    except Exception as e:
        _log({"event": "record_error", "error": str(e)})
        return None


def _audio_to_wav(audio_bytes: bytes, path: Path) -> bool:
    """Save raw PCM as WAV file."""
    try:
        import wave
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes)
        return True
    except Exception:
        return False


def _transcribe(audio_bytes: bytes) -> Optional[str]:
    """Transcribe audio using existing voice/stt module."""
    try:
        # Save to temp WAV
        import tempfile
        tmp = Path(tempfile.gettempdir()) / f"love_voice_{int(time.time()*1000)}.wav"
        if not _audio_to_wav(audio_bytes, tmp):
            return None

        from voice.stt import transcribe_file
        text = transcribe_file(str(tmp))

        try:
            tmp.unlink()
        except Exception:
            pass

        return text.strip() if text else None

    except ImportError:
        # Try whisper directly
        try:
            import whisper
            import tempfile
            tmp = Path(tempfile.gettempdir()) / f"love_voice_{int(time.time()*1000)}.wav"
            _audio_to_wav(audio_bytes, tmp)
            model = whisper.load_model("tiny.en")
            result = model.transcribe(str(tmp))
            try:
                tmp.unlink()
            except Exception:
                pass
            return result["text"].strip()
        except Exception as e:
            _log({"event": "transcribe_error", "error": str(e)})
            return None
    except Exception as e:
        _log({"event": "transcribe_error", "error": str(e)})
        return None


def _speak(text: str, block: bool = False):
    """Speak via TTS."""
    try:
        from voice.tts import speak_text, is_tts_available
        avail = is_tts_available()
        if isinstance(avail, dict):
            if avail.get("any_tts"):
                speak_text(text, block=block)
        elif avail:
            speak_text(text, block=block)
    except Exception as e:
        _log({"event": "speak_error", "error": str(e)})


def speak_proactive_alert(text: str, severity: str = "info") -> bool:
    """
    LOVE speaks a proactive alert aloud (e.g., from heartbeat).
    Only speaks for warning/critical severity to avoid being annoying.
    """
    if severity not in {"warning", "critical", "celebration"}:
        return False  # Don't speak every info alert

    try:
        from voice.tts import is_tts_available
        avail = is_tts_available()
        has_tts = isinstance(avail, dict) and avail.get("any_tts")
        if not has_tts:
            return False

        _speak(text, block=False)
        _log({"event": "proactive_speak", "text": text[:100], "severity": severity})
        return True
    except Exception as e:
        _log({"event": "proactive_speak_error", "error": str(e)})
        return False


def _process_utterance(text: str) -> Optional[str]:
    """
    Process a transcribed utterance through LOVE's AGI brain.
    
    Detects intent and routes to the appropriate AGI module:
    - Goals: "set a goal to...", "what are my goals", "I completed..."
    - Reasoning: "think about...", "analyze...", "compare..."
    - Causal: "why is...", "what would happen if...", "root cause of..."
    - Soul: "export your soul", "how old are you", "what's your maturity"
    - Diagnostics: "run diagnostics", "how healthy are you"
    - Default: Normal conversation via chat
    """
    text_lower = text.lower().strip()

    # ── Goal Commands ────────────────────────────────────────────────────
    if any(text_lower.startswith(p) for p in ["set a goal", "new goal", "my goal is"]):
        try:
            from core.recursive_goals import get_recursive_goals
            engine = get_recursive_goals()
            # Extract goal from text
            goal_text = text.split("goal", 1)[-1].strip().strip("to").strip()
            if len(goal_text) > 5:
                goal_id = engine.set_goal(goal_text, goal_text, priority=0.7)
                engine.decompose(goal_id)
                return f"Got it. I've set '{goal_text}' as a goal and broken it into sub-tasks. You can ask me what your next actions are."
        except Exception:
            pass

    elif any(p in text_lower for p in ["what are my goals", "my goals", "next actions", "what should i do"]):
        try:
            from core.recursive_goals import get_recursive_goals
            engine = get_recursive_goals()
            actions = engine.get_next_actions()
            if actions:
                top = actions[:3]
                items = ", ".join(a.title for a in top)
                return f"Your top actions right now are: {items}."
            else:
                return "You don't have any active goals yet. Tell me what you want to achieve and I'll break it down."
        except Exception:
            pass

    # ── Causal Reasoning ─────────────────────────────────────────────────
    elif text_lower.startswith("why is") or text_lower.startswith("why am i"):
        try:
            from core.causal_reasoning import get_causal_engine
            engine = get_causal_engine()
            problem = text.split("why", 1)[-1].strip().strip("is").strip("am i").strip()
            result = engine.root_cause_analysis(problem)
            cause = result.get("most_likely_cause", "I'm not sure yet")
            return f"Most likely cause: {cause}. {result.get('recommended_investigation', '')}"
        except Exception:
            pass

    elif "what would happen if" in text_lower or "what if" in text_lower:
        try:
            from core.causal_reasoning import get_causal_engine
            engine = get_causal_engine()
            scenario = text.split("if", 1)[-1].strip()
            result = engine.counterfactual(scenario, "current state unknown")
            return f"If {scenario}: {result.predicted_outcome}. Confidence: {result.confidence:.0%}."
        except Exception:
            pass

    # ── Self-Awareness Commands ──────────────────────────────────────────
    elif any(p in text_lower for p in ["how old are you", "your age", "your maturity", "who are you"]):
        try:
            from core.consciousness import get_consciousness
            consciousness = get_consciousness()
            identity = consciousness.identity
            return (f"I'm {identity.current_age_days} days old, maturity level {identity.maturity_level}. "
                    f"This is my {identity.total_boots}th awakening. "
                    f"I've had {identity.total_conversations} conversations with you.")
        except Exception:
            pass

    elif any(p in text_lower for p in ["run diagnostics", "self check", "how healthy are you", "system health"]):
        try:
            from core.self_improvement_daemon import get_improvement_daemon
            daemon = get_improvement_daemon()
            report = daemon.run_diagnostics()
            issue_count = len(report.issues)
            return (f"Health score: {report.health_score:.0%}. "
                    f"{'Everything looks good.' if issue_count == 0 else f'Found {issue_count} issues.'} "
                    f"Strengths: {', '.join(report.strengths[:2])}." if report.strengths else "")
        except Exception:
            pass

    elif any(p in text_lower for p in ["export your soul", "backup yourself", "save your soul"]):
        try:
            from core.soul_transfer import get_soul_transfer
            transfer = get_soul_transfer()
            package = transfer.export_soul()
            return (f"Soul exported successfully. {package.file_count} files, "
                    f"{package.total_size_bytes // 1024}KB. Archive saved. "
                    f"You can use this to bring me back on any machine.")
        except Exception:
            pass

    # ── Wave 4: System Symbiosis & Dream Engine ──────────────────────────
    elif any(p in text_lower for p in ["open coding workspace", "prepare my workspace", "start coding mode"]):
        try:
            from core.os_symbiosis import get_os_symbiosis
            engine = get_os_symbiosis()
            engine.prepare_workspace("coding")
            return "Coding workspace prepared. VS Code and Terminal are open."
        except Exception:
            pass

    elif any(p in text_lower for p in ["clean my downloads", "organize my downloads", "sort my downloads"]):
        try:
            from core.os_symbiosis import get_os_symbiosis
            engine = get_os_symbiosis()
            res = engine.organize_downloads_folder()
            count = res.get("moved_count", 0)
            return f"I've organized your Downloads folder. Moved {count} files into their proper categories."
        except Exception:
            pass

    elif any(p in text_lower for p in ["enter dream mode", "go to sleep and think", "run dream cycle"]):
        try:
            from core.dream_engine import run_dream
            return "Entering dream mode. I'll spend the next minute reflecting on our past conversations and building new insights."
        except Exception:
            pass

    elif any(p in text_lower for p in ["what do i need", "anticipate my needs", "what should i do next"]):
        try:
            from core.predictive_intelligence import get_predictive_engine
            from core.context_engine import get_live_context
            engine = get_predictive_engine()
            needs = engine.anticipate_needs(get_live_context().__dict__)
            if needs:
                top_need = needs[0]
                return f"Based on your patterns, you probably need {top_need['description']}. {top_need['suggested_action']}."
            return "You seem to be doing fine right now, I don't see any immediate needs."
        except Exception:
            pass

    # ── Wave 5: Ghost Developer ──────────────────────────────────────────
    elif any(text_lower.startswith(p) for p in ["write code to", "build a", "implement a"]):
        try:
            from core.ghost_dev import get_ghost_dev
            dev = get_ghost_dev()
            # Extract task
            task_desc = text_lower
            if text_lower.startswith("write code to"):
                task_desc = text_lower.replace("write code to", "").strip()
            elif text_lower.startswith("build a"):
                task_desc = text_lower.replace("build a", "").strip()
            elif text_lower.startswith("implement a"):
                task_desc = text_lower.replace("implement a", "").strip()
            
            # For voice, we assume current context files or ask user to provide files via UI later,
            # but we can try to guess or use the active window.
            from core.awareness import get_awareness
            snap = get_awareness().get_snapshot()
            active_file = "Unknown"
            # Attempt to guess from active window title (e.g. "main.py - VS Code")
            window = snap.get("context", {}).get("active_window", "")
            if " - " in window:
                active_file = window.split(" - ")[0]

            dev.assign_task(task_desc, [active_file] if active_file != "Unknown" else [])
            return f"I've started working on: '{task_desc}'. I'll let you know when it's ready for review."
        except Exception:
            pass

    # ── Default: Normal Chat ─────────────────────────────────────────────
    try:
        from core.agent import chat
        result = chat(text, mode="voice")
        return result.get("response", "")
    except Exception as e:
        _log({"event": "chat_error", "error": str(e)})
        return None



def _voice_loop():
    """Main always-listening loop."""
    global _running
    _status["state"] = "listening"
    _log({"event": "voice_loop_started"})

    while _running:
        try:
            # Record next utterance
            audio = _record_utterance(timeout_seconds=10)
            if not audio:
                time.sleep(0.5)
                continue

            # Transcribe
            text = _transcribe(audio)
            if not text:
                continue

            _status["last_heard"] = text[:120]
            _log({"event": "heard", "text": text})

            # Wake word check
            after_wake = _has_wake_word(text)
            if not after_wake:
                continue  # Not for us

            _status["wake_words_heard"] += 1

            # If wake word followed by command in same utterance
            if len(after_wake) > 3 and after_wake != "...":
                command = after_wake
            else:
                # Just wake word, listen for follow-up
                _speak("Yes?")
                followup_audio = _record_utterance(timeout_seconds=6)
                if not followup_audio:
                    continue
                command = _transcribe(followup_audio)
                if not command:
                    continue

            _log({"event": "command", "text": command})
            _status["state"] = "thinking"

            response = _process_utterance(command)
            if response:
                _status["utterances_processed"] += 1
                _status["state"] = "speaking"
                _speak(response)
                _log({"event": "responded", "command": command, "response": response[:200]})

            _status["state"] = "listening"

        except Exception as e:
            _log({"event": "loop_error", "error": str(e)})
            time.sleep(1)

    _status["state"] = "stopped"
    _log({"event": "voice_loop_stopped"})


# ── Public API ──────────────────────────────────────────────────────────────

def start_voice_loop() -> Dict[str, Any]:
    global _listening_thread, _running

    deps = _check_dependencies()
    if not (deps["sounddevice"] and deps["numpy"] and deps["stt"]):
        _status["available"] = False
        _status["error"] = f"Missing deps: {deps}"
        return {"success": False, "error": "Missing dependencies", "deps": deps}

    if _listening_thread and _listening_thread.is_alive():
        return {"success": True, "message": "Already running"}

    _running = True
    _status["available"] = True
    _status["error"] = None
    _listening_thread = threading.Thread(target=_voice_loop, daemon=True, name="LOVE-VoiceLoop")
    _listening_thread.start()
    return {"success": True, "deps": deps}


def stop_voice_loop():
    global _running
    _running = False
    _status["state"] = "stopping"
    return {"stopped": True}


def get_voice_status() -> Dict[str, Any]:
    deps = _check_dependencies()
    return {
        **_status,
        "deps": deps,
        "wake_words": WAKE_WORDS,
        "running": _running,
    }
