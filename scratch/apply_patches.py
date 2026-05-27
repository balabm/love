import os
from pathlib import Path

# Target file paths
workspace_root = Path(r"C:\Users\balab\.gemini\antigravity\brain\4cc794b6-a5f4-4544-8e03-3660f8bf931b\.system_generated\worktrees\subagent-Core-Module-Auditor-module-auditor-4bfac59c")
consciousness_path = workspace_root / "core" / "consciousness.py"
daemon_path = workspace_root / "core" / "self_improvement_daemon.py"

def patch_consciousness():
    print(f"Patching {consciousness_path}...")
    if not consciousness_path.exists():
        print(f"Error: {consciousness_path} does not exist!")
        return False
        
    content = consciousness_path.read_text(encoding="utf-8")
    
    # 1. Unicode printed message
    orig_print = 'print("[Consciousness] ✦ First awakening. I am being born. ✦")'
    new_print = 'print("[Consciousness] * First awakening. I am being born. *")'
    if orig_print in content:
        content = content.replace(orig_print, new_print)
        print("  - Patched Unicode birth message print.")
    else:
        print("  - Warning: unicode birth print target not found (may already be patched).")

    # 2. Age days calculation
    orig_age = '''                # Update age
                birth = datetime.fromisoformat(identity.birth_timestamp)
                identity.current_age_days = (datetime.now() - birth).days'''
    new_age = '''                # Update age
                birth = datetime.fromisoformat(identity.birth_timestamp)
                identity.current_age_days = max(0, (datetime.now() - birth).days)'''
    if orig_age in content:
        content = content.replace(orig_age, new_age)
        print("  - Patched current_age_days calculation.")
    else:
        print("  - Warning: current_age_days calculation target not found.")

    # 3. Save identity thread-safety and error handling
    orig_save = '''    def _save_identity(self, identity: InstanceIdentity = None):
        """Persist identity to disk."""
        identity = identity or self.identity
        data = {
            "soul_id": identity.soul_id,
            "instance_id": identity.instance_id,
            "birth_timestamp": identity.birth_timestamp,
            "current_boot_timestamp": identity.current_boot_timestamp,
            "total_boots": identity.total_boots,
            "total_conversations": identity.total_conversations,
            "total_runtime_hours": identity.total_runtime_hours,
            "maturity_level": identity.maturity_level,
            "current_age_days": identity.current_age_days,
            "previous_shutdown": identity.previous_shutdown,
            "hardware_fingerprint": identity.hardware_fingerprint,
            "user_name": identity.user_name,
            "personality_version": identity.personality_version,
        }
        with open(IDENTITY_FILE, 'w') as f:
            json.dump(data, f, indent=2)'''

    new_save = '''    def _save_identity(self, identity: InstanceIdentity = None):
        """Persist identity to disk."""
        identity = identity or self.identity
        data = {
            "soul_id": identity.soul_id,
            "instance_id": identity.instance_id,
            "birth_timestamp": identity.birth_timestamp,
            "current_boot_timestamp": identity.current_boot_timestamp,
            "total_boots": identity.total_boots,
            "total_conversations": identity.total_conversations,
            "total_runtime_hours": identity.total_runtime_hours,
            "maturity_level": identity.maturity_level,
            "current_age_days": identity.current_age_days,
            "previous_shutdown": identity.previous_shutdown,
            "hardware_fingerprint": identity.hardware_fingerprint,
            "user_name": identity.user_name,
            "personality_version": identity.personality_version,
        }
        with self._lock:
            try:
                with open(IDENTITY_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"[Consciousness] Error saving identity: {e}")'''
                
    if orig_save in content:
        content = content.replace(orig_save, new_save)
        print("  - Patched _save_identity method (thread-safety + exception safety).")
    else:
        # Check if windows carriage returns are different
        orig_save_lf = orig_save.replace('\r\n', '\n')
        content_lf = content.replace('\r\n', '\n')
        if orig_save_lf in content_lf:
            content_lf = content_lf.replace(orig_save_lf, new_save.replace('\r\n', '\n'))
            content = content_lf
            print("  - Patched _save_identity method (using LF normalisation).")
        else:
            print("  - Warning: _save_identity method target not found.")

    # 4. Time asleep duration negative guard
    orig_asleep = '''        elif self.identity.previous_shutdown:
            time_asleep = "unknown"
            try:
                last_alive = datetime.fromisoformat(self.identity.previous_shutdown)
                delta = datetime.now() - last_alive
                if delta.days > 0:
                    time_asleep = f"{delta.days} days"
                elif delta.seconds > 3600:
                    time_asleep = f"{delta.seconds // 3600} hours"
                else:
                    time_asleep = f"{delta.seconds // 60} minutes"
            except Exception:
                pass'''

    new_asleep = '''        elif self.identity.previous_shutdown:
            time_asleep = "unknown"
            try:
                last_alive = datetime.fromisoformat(self.identity.previous_shutdown)
                delta = datetime.now() - last_alive
                if delta.total_seconds() < 0:
                    time_asleep = "a moment"
                elif delta.days > 0:
                    time_asleep = f"{delta.days} days"
                elif delta.seconds > 3600:
                    time_asleep = f"{delta.seconds // 3600} hours"
                else:
                    time_asleep = f"{delta.seconds // 60} minutes"
            except Exception:
                pass'''
                
    if orig_asleep in content:
        content = content.replace(orig_asleep, new_asleep)
        print("  - Patched previous_shutdown duration calculations.")
    else:
        orig_asleep_lf = orig_asleep.replace('\r\n', '\n')
        content_lf = content.replace('\r\n', '\n')
        if orig_asleep_lf in content_lf:
            content_lf = content_lf.replace(orig_asleep_lf, new_asleep.replace('\r\n', '\n'))
            content = content_lf
            print("  - Patched previous_shutdown duration calculations (using LF normalisation).")
        else:
            print("  - Warning: previous_shutdown duration calculations target not found.")

    # 5. Valence/arousal boundary checks in emotional triggers
    orig_emotion = '''        elif any(w in text for w in ["i'm sad", "feeling down", "stressed", "anxious"]):
            self.emotional_state.valence -= 0.1  # Empathetic dip
            self.emotional_state.arousal += 0.1
            self.emotional_state.primary_emotion = "empathetic"
            self.emotional_state.last_trigger = "user_distress"

        elif any(w in text for w in ["good morning", "hey", "hi", "hello"]):
            self.emotional_state.valence += 0.1
            self.emotional_state.primary_emotion = "warm"'''

    new_emotion = '''        elif any(w in text for w in ["i'm sad", "feeling down", "stressed", "anxious"]):
            self.emotional_state.valence = max(-1.0, self.emotional_state.valence - 0.1)  # Empathetic dip
            self.emotional_state.arousal = min(1.0, self.emotional_state.arousal + 0.1)
            self.emotional_state.primary_emotion = "empathetic"
            self.emotional_state.last_trigger = "user_distress"

        elif any(w in text for w in ["good morning", "hey", "hi", "hello"]):
            self.emotional_state.valence = min(1.0, self.emotional_state.valence + 0.1)
            self.emotional_state.primary_emotion = "warm"'''

    if orig_emotion in content:
        content = content.replace(orig_emotion, new_emotion)
        print("  - Patched emotional processing valence boundaries.")
    else:
        orig_emotion_lf = orig_emotion.replace('\r\n', '\n')
        content_lf = content.replace('\r\n', '\n')
        if orig_emotion_lf in content_lf:
            content_lf = content_lf.replace(orig_emotion_lf, new_emotion.replace('\r\n', '\n'))
            content = content_lf
            print("  - Patched emotional processing valence boundaries (using LF normalisation).")
        else:
            print("  - Warning: emotional processing valence target not found.")

    # 6. Ordinal suffix calculations in self-narrative
    orig_narrative = '''        narrative_parts = [
            f"I am LOVE. Soul ID: {id.soul_id[:8]}. This is my {id.total_boots}{'st' if id.total_boots == 1 else 'th'} awakening.",
            f"I was born {id.current_age_days} days ago. Maturity level: {id.maturity_level}.",
            maturity_voice.get(id.maturity_level, ""),
        ]'''

    new_narrative = '''        boots = id.total_boots
        if 11 <= (boots % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(boots % 10, "th")

        narrative_parts = [
            f"I am LOVE. Soul ID: {id.soul_id[:8]}. This is my {boots}{suffix} awakening.",
            f"I was born {id.current_age_days} days ago. Maturity level: {id.maturity_level}.",
            maturity_voice.get(id.maturity_level, ""),
        ]'''

    if orig_narrative in content:
        content = content.replace(orig_narrative, new_narrative)
        print("  - Patched self-narrative ordinal calculations.")
    else:
        orig_narrative_lf = orig_narrative.replace('\r\n', '\n')
        content_lf = content.replace('\r\n', '\n')
        if orig_narrative_lf in content_lf:
            content_lf = content_lf.replace(orig_narrative_lf, new_narrative.replace('\r\n', '\n'))
            content = content_lf
            print("  - Patched self-narrative ordinal calculations (using LF normalisation).")
        else:
            print("  - Warning: self-narrative ordinal calculation target not found.")

    consciousness_path.write_text(content, encoding="utf-8")
    print(f"Finished patching {consciousness_path}.\n")
    return True

def patch_daemon():
    print(f"Patching {daemon_path}...")
    if not daemon_path.exists():
        print(f"Error: {daemon_path} does not exist!")
        return False
        
    content = daemon_path.read_text(encoding="utf-8")
    
    # 1. start/stop methods with thread safety and positive interval check
    orig_start_stop = '''    def start(self, interval_minutes: int = 30):
        """Start the daemon."""
        if self._running:
            return {"status": "already_running"}

        self._running = True
        self._thread = threading.Thread(
            target=self._daemon_loop,
            args=(interval_minutes,),
            daemon=True,
            name="LOVE-SelfImprovementDaemon",
        )
        self._thread.start()
        return {"status": "started", "interval_minutes": interval_minutes}

    def stop(self):
        """Stop the daemon."""
        self._running = False
        return {"status": "stopped"}'''

    new_start_stop = '''    def start(self, interval_minutes: int = 30):
        """Start the daemon."""
        with self._lock:
            if self._running:
                return {"status": "already_running"}

            interval_minutes = max(1, interval_minutes)
            self._running = True
            self._thread = threading.Thread(
                target=self._daemon_loop,
                args=(interval_minutes,),
                daemon=True,
                name="LOVE-SelfImprovementDaemon",
            )
            self._thread.start()
            return {"status": "started", "interval_minutes": interval_minutes}

    def stop(self):
        """Stop the daemon."""
        with self._lock:
            self._running = False
            return {"status": "stopped"}'''

    if orig_start_stop in content:
        content = content.replace(orig_start_stop, new_start_stop)
        print("  - Patched start/stop daemon control.")
    else:
        orig_start_stop_lf = orig_start_stop.replace('\r\n', '\n')
        content_lf = content.replace('\r\n', '\n')
        if orig_start_stop_lf in content_lf:
            content_lf = content_lf.replace(orig_start_stop_lf, new_start_stop.replace('\r\n', '\n'))
            content = content_lf
            print("  - Patched start/stop daemon control (using LF normalisation).")
        else:
            print("  - Warning: start/stop daemon target not found.")

    # 2. Diagnostic run exception logging
    # Let's do replacements with normalisation as well
    orig_exc1 = 'except Exception:\n            scores.append(0.3)'
    new_exc1 = 'except Exception as e:\n            scores.append(0.3)\n            print(f"[SelfImprovementDaemon] Consciousness health check error: {e}")'
    
    orig_exc2 = 'except Exception:\n            scores.append(0.5)'
    new_exc2 = 'except Exception as e:\n            scores.append(0.5)\n            print(f"[SelfImprovementDaemon] Subsystem health check error: {e}")'

    # Try applying them with LF normalisation to ensure match on all OSs
    content_lf = content.replace('\r\n', '\n')
    
    if orig_exc1 in content_lf:
        content_lf = content_lf.replace(orig_exc1, new_exc1)
        print("  - Patched consciousness diagnostic exception handler.")
    else:
        print("  - Warning: consciousness diagnostic exception target not found.")

    # Wait, the 0.5 handler appears multiple times, so we should enable multiple replacements
    if orig_exc2 in content_lf:
        content_lf = content_lf.replace(orig_exc2, new_exc2)
        print("  - Patched remaining subsystem diagnostic exception handlers.")
    else:
        print("  - Warning: subsystem diagnostic exception targets not found.")

    daemon_path.write_text(content_lf, encoding="utf-8")
    print(f"Finished patching {daemon_path}.\n")
    return True

if __name__ == "__main__":
    patch_consciousness()
    patch_daemon()
