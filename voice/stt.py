"""
Speech-to-Text (STT) Module
Configurable wake-word detection and Whisper transcription.
"""

import os
import wave
import tempfile
from pathlib import Path
from typing import Callable, Optional, List

from core.settings import get_settings
from core.execution_guard import log_error

# Load wake word from settings
SETTINGS = get_settings()
WAKE_WORD = SETTINGS.voice.wake_word or "Hey Love"

# Heavy optional deps are imported lazily to avoid startup hangs
# (whisper/torch do GPU detection; pyaudio opens audio drivers)
def _check_porcupine():
    try:
        import pvporcupine  # noqa: F401
        return True
    except ImportError:
        return False

def _check_pyaudio():
    try:
        import pyaudio  # noqa: F401
        return True
    except ImportError:
        return False

def _check_whisper():
    try:
        import whisper  # noqa: F401
        return True
    except ImportError:
        return False

PORCUPINE_AVAILABLE = False  # resolved on first use via _check_porcupine()
PYAUDIO_AVAILABLE = False    # resolved on first use via _check_pyaudio()
WHISPER_AVAILABLE = False    # resolved on first use via _check_whisper()


try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False


class WakeWordListener:
    """Listens for configurable wake word using Porcupine."""
    
    def __init__(self, access_key: str = None, keyword_path: str = None):
        self.access_key = access_key or os.getenv("PORCUPINE_ACCESS_KEY")
        self.keyword_path = keyword_path
        self.porcupine = None
        self.audio = None
        self.stream = None
        self.is_listening = False
        
        if not PORCUPINE_AVAILABLE:
            print("[STT] Porcupine not available. Wake word detection disabled.")
            return
            
        self._init_porcupine()
        
    def _init_porcupine(self):
        """Initialize Porcupine wake word engine."""
        try:
            if self.keyword_path and Path(self.keyword_path).exists():
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.keyword_path]
                )
            else:
                # Use built-in "Hey" keyword as fallback
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=["hey"]
                )
        except Exception as e:
            print(f"[STT] Failed to initialize Porcupine: {e}")
            self.porcupine = None
    
    def start_listening(self, callback: Callable[[], None]):
        """Start listening for wake word."""
        if not PORCUPINE_AVAILABLE or not self.porcupine:
            print("[STT] Cannot start listening - Porcupine not available")
            return
            
        if not PYAUDIO_AVAILABLE:
            print("[STT] PyAudio not available")
            return
        
        self.is_listening = True
        
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            print("[STT] Listening for 'Hey Love'...")
            
            while self.is_listening:
                pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = [int((ord(pcm[i]) + ord(pcm[i+1]) * 256) / 32768.0 * 32767) 
                       for i in range(0, len(pcm), 2)]
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("[STT] Wake word detected!")
                    callback()
                    
        except Exception as e:
            print(f"[STT] Listening error: {e}")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop listening for wake word."""
        self.is_listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()
        
        print("[STT] Stopped listening")


def _has_ffmpeg() -> bool:
    """Check if ffmpeg is available in PATH."""
    try:
        import subprocess
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


class WhisperTranscriber:
    """Transcribes audio using OpenAI Whisper with context awareness."""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.model = None
        self.ffmpeg_ok = _has_ffmpeg()
        
        if not self.ffmpeg_ok:
            print("[STT] ffmpeg not found in PATH. Install from https://ffmpeg.org/download.html")
        
        if WHISPER_AVAILABLE and self.ffmpeg_ok:
            self._load_model()
        elif not WHISPER_AVAILABLE:
            print("[STT] Whisper not available. Falling back to mock transcription.")
    
    def _load_model(self):
        """Load Whisper model."""
        try:
            print(f"[STT] Loading Whisper {self.model_size} model...")
            self.model = whisper.load_model(self.model_size)
            print("[STT] Whisper model loaded")
        except Exception as e:
            print(f"[STT] Failed to load Whisper: {e}")
            self.model = None
    
    def _get_context_vocabulary(self) -> list:
        """Extract vocabulary from current context for better transcription."""
        vocabulary = []
        
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            
            # Add active project name
            if ctx.active_project:
                vocabulary.append(ctx.active_project)
            
            # Add recent file names
            if ctx.recent_files:
                for f in ctx.recent_files[:5]:
                    name = f.get("name", "")
                    if name:
                        # Extract base name without extension
                        base = name.rsplit(".", 1)[0] if "." in name else name
                        vocabulary.append(base)
            
            # Add people from relationships
            try:
                from core.emotional import get_relationship_summary
                rel = get_relationship_summary()
                for person in rel.get("top_people", [])[:5]:
                    vocabulary.append(person.get("name", ""))
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="voice.stt")
            
        except Exception as e:
            print(f"[STT] Context vocabulary extraction error: {e}")
        
        return vocabulary
    
    def _post_process_transcription(self, text: str) -> str:
        """Post-process transcription with context-aware corrections."""
        if not text:
            return text
        
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            
            # Common technical terms that might be misheard
            corrections = {
                "python": "Python",
                "javascript": "JavaScript",
                "typescript": "TypeScript",
                "react": "React",
            }
            
            # Add project-specific corrections
            if ctx.active_project:
                project_lower = ctx.active_project.lower()
                project_corrections = {
                    'love': 'LOVE',
                    'karthi': 'Karthi',
                }
                corrections.update(project_corrections)
            
            # Apply corrections
            for wrong, right in corrections.items():
                if wrong in text.lower() and right not in text:
                    text = text.replace(wrong, right)
            
            return text
        except Exception as e:
            print(f"[STT] Post-processing error: {e}")
            return text
    
    def get_proactive_command_suggestions(self) -> List[str]:
        """Generate proactive voice command suggestions based on current context."""
        try:
            from core.context_engine import get_live_context
            ctx = get_live_context()
            
            suggestions = []
            
            # Meeting-related suggestions
            if ctx.next_event and ctx.next_event.get('minutes_away', 999) <= 15:
                suggestions.append(f"Join meeting: {ctx.next_event.get('title', 'next meeting')}")
            
            # Task-related suggestions
            if ctx.tasks_due_today > 0:
                suggestions.append("Show me today's tasks")
                suggestions.append("What should I work on next?")
            
            # Device-related suggestions
            if ctx.phone_battery and ctx.phone_battery < 20:
                suggestions.append("Phone battery low - check charging")
            
            if ctx.pc_battery and ctx.pc_battery < 20:
                suggestions.append("PC battery low - plug in charger")
            
            # Calendar suggestions
            if ctx.events_today:
                suggestions.append("What's on my calendar today?")
                suggestions.append("When is my next free time?")
            
            # General suggestions
            suggestions.append("What's my current context?")
            suggestions.append("How am I feeling today?")
            suggestions.append("Show my relationship insights")
            
            # Time-specific suggestions
            if ctx.time_of_day == 'morning':
                suggestions.append("Start my day routine")
                suggestions.append("What are my priorities today?")
            elif ctx.time_of_day == 'afternoon':
                suggestions.append("What's my progress today?")
                suggestions.append("Should I take a break?")
            elif ctx.time_of_day == 'evening':
                suggestions.append("Summarize my day")
                suggestions.append("What should I do tomorrow?")
            
            return suggestions[:8]  # Limit to top 8 suggestions
            
        except Exception as e:
            print(f"[STT] Command suggestions error: {e}")
            return []
    
    def transcribe_file(self, audio_path: str, use_context: bool = True) -> str:
        """Transcribe an audio file with optional context awareness."""
        if not self.ffmpeg_ok:
            return "[Transcription unavailable - ffmpeg not installed. Install from ffmpeg.org/download.html]"
        if not WHISPER_AVAILABLE or not self.model:
            return "[Transcription unavailable - Whisper not loaded]"
        
        try:
            # Get context vocabulary if enabled
            vocabulary = self._get_context_vocabulary() if use_context else []
            
            # Prepare initial prompt with vocabulary
            prompt = None
            if vocabulary:
                prompt = " ".join(vocabulary)
            
            result = self.model.transcribe(
                audio_path,
                language="en",
                initial_prompt=prompt if prompt else None,
                word_timestamps=False
            )
            
            text = result["text"].strip()
            
            # Post-process with context-aware corrections
            if use_context:
                text = self._post_process_transcription(text)
            
            return text
            
        except FileNotFoundError as e:
            print(f"[STT] Transcription error (ffmpeg missing): {e}")
            return "[Transcription unavailable - ffmpeg not installed. Install from ffmpeg.org/download.html]"
        except Exception as e:
            print(f"[STT] Transcription error: {e}")
            return "[Transcription failed]"
    
    def transcribe_microphone(self, duration: int = 5, use_context: bool = True) -> str:
        """Record from microphone and transcribe with context awareness."""
        if not PYAUDIO_AVAILABLE:
            return "[Recording unavailable - PyAudio not installed]"
        
        # Record audio
        temp_file = tempfile.mktemp(suffix=".wav")
        
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            print(f"[STT] Recording for {duration} seconds...")
            frames = []
            
            for _ in range(0, int(16000 / 1024 * duration)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Save to file
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
            
            # Transcribe with context
            return self.transcribe_file(temp_file, use_context=use_context)
            
        except Exception as e:
            print(f"[STT] Recording error: {e}")
            return "[Recording failed]"
        finally:
            if Path(temp_file).exists():
                Path(temp_file).unlink()


class VoiceInterface:
    """Main voice interface combining wake word and transcription."""
    
    def __init__(self):
        self.wake_listener = WakeWordListener()
        self.transcriber = WhisperTranscriber()
        self.on_wake_word: Optional[Callable[[], None]] = None
        self.on_transcription: Optional[Callable[[str], None]] = None
        self.is_active = False
    
    def set_callbacks(self, on_wake: Callable[[], None], on_transcribe: Callable[[str], None]):
        """Set callbacks for wake word and transcription."""
        self.on_wake_word = on_wake
        self.on_transcription = on_transcribe
    
    def _on_wake(self):
        """Handle wake word detection."""
        if self.on_wake_word:
            self.on_wake_word()
        
        # Start listening for command
        text = self.transcriber.transcribe_microphone(duration=5)
        
        if self.on_transcription:
            self.on_transcription(text)
    
    def start(self):
        """Start voice interface."""
        self.is_active = True
        
        if self.wake_listener.porcupine:
            # Start wake word listening in a thread
            import threading
            thread = threading.Thread(
                target=self.wake_listener.start_listening,
                args=(self._on_wake,)
            )
            thread.daemon = True
            thread.start()
        else:
            print("[Voice] Wake word not available - using manual activation only")
    
    def stop(self):
        """Stop voice interface."""
        self.is_active = False
        self.wake_listener.stop_listening()
    
    def listen_once(self) -> str:
        """Listen for one command (manual activation)."""
        return self.transcriber.transcribe_microphone(duration=5)


# Public API functions
def create_voice_interface() -> VoiceInterface:
    """Create and configure voice interface."""
    return VoiceInterface()


def quick_listen(duration: int = 5) -> str:
    """Quick one-off transcription."""
    transcriber = WhisperTranscriber()
    return transcriber.transcribe_microphone(duration)


def is_voice_available() -> dict:
    """Check voice component availability."""
    return {
        "porcupine": PORCUPINE_AVAILABLE,
        "pyaudio": PYAUDIO_AVAILABLE,
        "whisper": WHISPER_AVAILABLE,
        "full_voice": PORCUPINE_AVAILABLE and PYAUDIO_AVAILABLE and WHISPER_AVAILABLE
    }
