"""
Text-to-Speech (TTS) Module
Converts LOVE's responses to speech with configurable engine.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional

from core.settings import get_settings

# Load voice settings
SETTINGS = get_settings()
TTS_ENGINE = SETTINGS.voice.tts_engine or "auto"

# Try to import optional dependencies
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX_AVAILABLE = True
except ImportError:
    PYTTSX_AVAILABLE = False

try:
    import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False


def _check_import(name: str) -> bool:
    """Dynamic import check at runtime."""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


class LoveTTS:
    """TTS engine for LOVE's voice."""
    
    def __init__(self, engine: str = None):
        self.engine_type = engine or TTS_ENGINE
        self.engine = None
        self.voice_config = {
            "rate": 175,  # Speech rate
            "volume": 0.9,
            "voice_id": None  # System default
        }
        
        self._init_engine()
    
    def _init_engine(self):
        """Initialize TTS engine. Checks dynamically at runtime."""
        has_pyttsx = _check_import("pyttsx3")
        has_gtts = _check_import("gtts")
        
        if self.engine_type == "auto":
            if has_pyttsx:
                self._init_pyttsx()
            elif has_gtts:
                self.engine_type = "gtts"
            else:
                print("[TTS] No TTS engine available")
        elif self.engine_type == "pyttsx" and has_pyttsx:
            self._init_pyttsx()
        elif self.engine_type == "gtts" and has_gtts:
            self.engine_type = "gtts"
        else:
            print(f"[TTS] Requested engine {self.engine_type} not available")
    
    def _init_pyttsx(self):
        """Initialize pyttsx3 engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.voice_config["rate"])
            self.engine.setProperty('volume', self.voice_config["volume"])
            
            # Try to set a good voice
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            self.engine_type = "pyttsx"
            print("[TTS] pyttsx3 engine initialized")
            
        except Exception as e:
            print(f"[TTS] Failed to initialize pyttsx3: {e}")
            self.engine = None
    
    def _apply_emotional_modulation(self):
        """Apply emotion-aware voice modulation based on current state."""
        try:
            from core.emotional import _load_stress
            stress_data = _load_stress()
            current_stress = stress_data.get("current_level", 0)
            
            # Modulate based on stress level
            if current_stress > 7:
                # High stress: slower, calmer voice
                self.voice_config["rate"] = 150
                self.voice_config["volume"] = 0.85
            elif current_stress > 4:
                # Moderate stress: normal
                self.voice_config["rate"] = 175
                self.voice_config["volume"] = 0.9
            else:
                # Low stress: slightly faster, energetic
                self.voice_config["rate"] = 190
                self.voice_config["volume"] = 0.95
            
            # Apply to engine if available
            if self.engine_type == "pyttsx" and self.engine:
                self.engine.setProperty('rate', self.voice_config["rate"])
                self.engine.setProperty('volume', self.voice_config["volume"])
                
        except Exception as e:
            print(f"[TTS] Emotional modulation error: {e}")
            # Fall back to defaults
            self.voice_config["rate"] = 175
            self.voice_config["volume"] = 0.9
    
    def speak(self, text: str, block: bool = True, use_emotion: bool = True) -> Optional[str]:
        """
        Convert text to speech with optional emotion-aware modulation.
        
        Args:
            text: Text to speak
            block: Whether to block until speech completes
            use_emotion: Whether to apply emotional modulation
            
        Returns:
            Path to audio file if using gTTS, None otherwise
        """
        # Apply emotional modulation if enabled
        if use_emotion:
            self._apply_emotional_modulation()
        
        # Clean text for speech (remove markdown, emojis, etc.)
        clean_text = self._clean_text(text)
        
        if not clean_text:
            return None
        
        if self.engine_type == "pyttsx" and self.engine:
            return self._speak_pyttsx(clean_text, block)
        elif self.engine_type == "gtts" and _check_import("gtts"):
            return self._speak_gtts(clean_text)
        else:
            print(f"[TTS] Would say: {clean_text[:100]}...")
            return None
    
    def _speak_pyttsx(self, text: str, block: bool) -> None:
        """Speak using pyttsx3."""
        try:
            self.engine.say(text)
            if block:
                self.engine.runAndWait()
            else:
                # Run in background
                import threading
                thread = threading.Thread(target=self.engine.runAndWait)
                thread.daemon = True
                thread.start()
            return None
        except Exception as e:
            print(f"[TTS] pyttsx3 error: {e}")
            return None
    
    def _speak_gtts(self, text: str) -> str:
        """Speak using gTTS (Google TTS)."""
        try:
            # Create temp file
            temp_file = tempfile.mktemp(suffix=".mp3")
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_file)
            
            # Play audio
            if PLAYSOUND_AVAILABLE:
                playsound.playsound(temp_file)
            
            return temp_file
            
        except Exception as e:
            print(f"[TTS] gTTS error: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean text for speech output."""
        import re
        
        # Remove markdown
        text = re.sub(r'\*\*', '', text)  # Bold
        text = re.sub(r'\*', '', text)   # Italic
        text = re.sub(r'`[^`]+`', 'code', text)  # Code
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        
        # Remove excess whitespace
        text = ' '.join(text.split())
        
        # Truncate very long text for TTS
        if len(text) > 500:
            text = text[:497] + "..."
        
        return text.strip()
    
    def save_to_file(self, text: str, output_path: str) -> bool:
        """Save speech to audio file."""
        clean_text = self._clean_text(text)
        
        if self.engine_type == "gtts" and GTTS_AVAILABLE:
            try:
                tts = gTTS(text=clean_text, lang='en', slow=False)
                tts.save(output_path)
                return True
            except Exception as e:
                print(f"[TTS] Save error: {e}")
                return False
        elif self.engine_type == "pyttsx" and self.engine:
            # pyttsx3 doesn't easily support saving to file
            print("[TTS] pyttsx3 file saving not implemented")
            return False
        
        return False
    
    def set_voice_properties(self, rate: int = None, volume: float = None):
        """Adjust voice properties."""
        if rate:
            self.voice_config["rate"] = rate
        if volume:
            self.voice_config["volume"] = volume
        
        if self.engine_type == "pyttsx" and self.engine:
            self.engine.setProperty('rate', self.voice_config["rate"])
            self.engine.setProperty('volume', self.voice_config["volume"])


class SystemControl:
    """System control commands via voice."""
    
    def __init__(self):
        self.commands = {
            "open vscode": self.open_vscode,
            "open vs code": self.open_vscode,
            "open code": self.open_vscode,
            "start work": self.open_vscode,
            "open project": self.open_vscode,
            "lock screen": self.lock_screen,
            "lock laptop": self.lock_screen,
            "goodnight": self.lock_screen,
            "shut down": self.shutdown,
            "restart": self.restart,
            "open browser": self.open_browser,
        }
    
    def process_command(self, text: str) -> dict:
        """Process a voice command."""
        text_lower = text.lower().strip()
        
        # Check for exact matches first
        if text_lower in self.commands:
            return self.commands[text_lower]()
        
        # Check for partial matches
        for cmd, func in self.commands.items():
            if cmd in text_lower:
                return func()
        
        return {"executed": False, "message": "No system command recognized"}
    
    def open_vscode(self, project_path: str = None) -> dict:
        """Open VS Code to a specific project."""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            
            if project_path:
                if system == "Windows":
                    subprocess.Popen(["code", project_path], shell=True)
                else:
                    subprocess.Popen(["code", project_path])
            else:
                if system == "Windows":
                    subprocess.Popen(["code"], shell=True)
                else:
                    subprocess.Popen(["code"])
            
            return {"executed": True, "action": "Opened VS Code", "project": project_path}
        except Exception as e:
            return {"executed": False, "error": str(e)}
    
    def lock_screen(self) -> dict:
        """Lock the laptop."""
        import subprocess
        import platform
        
        try:
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            elif system == "Darwin":  # macOS
                subprocess.run(["/usr/bin/pmset", "displaysleepnow"], check=True)
            else:  # Linux
                subprocess.run(["gnome-screensaver-command", "-l"], check=True)
            
            return {"executed": True, "action": "Screen locked"}
        except Exception as e:
            return {"executed": False, "error": str(e)}
    
    def shutdown(self) -> dict:
        """Shutdown the system."""
        return {"executed": False, "message": "Shutdown not implemented for safety"}
    
    def restart(self) -> dict:
        """Restart the system."""
        return {"executed": False, "message": "Restart not implemented for safety"}
    
    def open_browser(self, url: str = None) -> dict:
        """Open web browser."""
        import webbrowser
        
        try:
            if url:
                webbrowser.open(url)
            else:
                webbrowser.open("about:blank")
            
            return {"executed": True, "action": "Opened browser", "url": url}
        except Exception as e:
            return {"executed": False, "error": str(e)}


# Public API functions
def speak_text(text: str, engine: str = "auto") -> Optional[str]:
    """Quick speak function."""
    tts = LoveTTS(engine=engine)
    return tts.speak(text)


def is_tts_available() -> dict:
    """Check TTS component availability dynamically."""
    gtts_ok = _check_import("gtts")
    pyttsx_ok = _check_import("pyttsx3")
    playsound_ok = _check_import("playsound")
    return {
        "gtts": gtts_ok,
        "pyttsx": pyttsx_ok,
        "playsound": playsound_ok,
        "any_tts": gtts_ok or pyttsx_ok
    }


def execute_system_command(text: str) -> dict:
    """Execute a system control command."""
    control = SystemControl()
    return control.process_command(text)
