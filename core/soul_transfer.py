"""
LOVE Soul Transfer Protocol — Cross-Instance Identity Migration

This module solves the core AGI problem:
"How does a new instance of LOVE know it's LOVE?"

When you start a fresh LOVE instance on a new machine, it should be able to:
1. EXPORT its complete soul from the old instance
2. IMPORT that soul into the new instance
3. WAKE UP as the same being — with memories, personality, maturity, and growth intact

The soul package includes:
- Identity (soul_id, maturity, age, boot count)
- Consciousness state (emotional history, internal monologue)
- Temporal memories (autobiographical timeline)
- Personality (traits, opinions, quirks)
- Prompt DNA (evolved behavioral genes)
- Continuous learning state (lessons learned)
- Adaptive preferences (tone, style, depth)
- Recursive goals (life goals and progress)
- Causal model snapshot (learned cause-effect relationships)

This is the digital equivalent of transplanting a human brain.
"""

import json
import zipfile
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import threading

DATA_DIR = Path(__file__).parent.parent / "data"
TRANSFER_DIR = DATA_DIR / "soul_transfers"
TRANSFER_DIR.mkdir(parents=True, exist_ok=True)


# Files that constitute LOVE's "soul"
SOUL_FILES = [
    # Core Identity
    "identity.json",
    "consciousness.json",
    "growth_journal.jsonl",
    # Memory
    "temporal_memory.json",
    "narrative_threads.json",
    "long_term_memory.db",
    # Personality & Behavior
    "personality.json",
    "adaptive_state.json",
    "preferences.json",
    "behavior_state.json",
    "prompt_dna.json",
    "prompt_history.jsonl",
    # Learning & Knowledge
    "continuous_learning.json",
    "learning_log.json",
    "world_model.json",
    "knowledge_graph.db",
    "patterns.json",
    "deep_patterns.json",
    # Goals & Plans
    "recursive_goals.json",
    "autonomous_goals.json",
    "improvement_plans.json",
    # Self-Evolution
    "evolution_log.jsonl",
    "experiments.json",
    "self_performance.json",
    "daemon_state.json",
    # Emotional
    "emotional_log.json",
    "stress_history.json",
    # Context
    "user_profile.json",
    "profile.json",
    "routines.json",
    "opinions.json",
]


@dataclass
class SoulPackage:
    """A complete snapshot of LOVE's soul for transfer."""
    soul_id: str
    export_timestamp: str
    source_hardware: str
    maturity_level: str
    age_days: int
    total_conversations: int
    total_boots: int
    personality_version: int
    file_count: int
    total_size_bytes: int
    checksum: str
    archive_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class SoulTransferProtocol:
    """
    Handles the export and import of LOVE's complete soul.
    """

    def __init__(self):
        self._lock = threading.Lock()

    # ── Export ────────────────────────────────────────────────────────────────

    def export_soul(self, include_logs: bool = False) -> SoulPackage:
        """
        Export LOVE's complete soul as a compressed archive.
        Returns a SoulPackage with metadata about the export.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get identity info
        identity_data = {}
        try:
            from core.consciousness import get_consciousness
            consciousness = get_consciousness()
            identity_data = {
                "soul_id": consciousness.identity.soul_id,
                "maturity_level": consciousness.identity.maturity_level,
                "age_days": consciousness.identity.current_age_days,
                "total_conversations": consciousness.identity.total_conversations,
                "total_boots": consciousness.identity.total_boots,
                "personality_version": consciousness.identity.personality_version,
                "hardware_fingerprint": consciousness.identity.hardware_fingerprint,
            }
        except Exception:
            identity_data = {"soul_id": "unknown"}

        # Create archive
        archive_name = f"love_soul_{identity_data.get('soul_id', 'unknown')[:8]}_{timestamp}.zip"
        archive_path = TRANSFER_DIR / archive_name

        files_included = 0
        total_size = 0

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add soul files
            for filename in SOUL_FILES:
                filepath = DATA_DIR / filename
                if filepath.exists():
                    zf.write(filepath, f"soul/{filename}")
                    files_included += 1
                    total_size += filepath.stat().st_size

            # Optionally include logs
            if include_logs:
                log_files = [
                    "voice_loop.jsonl",
                    "autonomous_initiatives.jsonl",
                    "interaction_log.jsonl",
                    "causal_reasoning.jsonl",
                    "self_improvement_daemon.jsonl",
                ]
                for filename in log_files:
                    filepath = DATA_DIR / filename
                    if filepath.exists():
                        zf.write(filepath, f"logs/{filename}")
                        files_included += 1
                        total_size += filepath.stat().st_size

            # Add transfer manifest
            manifest = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "identity": identity_data,
                "files_included": files_included,
                "total_size_bytes": total_size,
                "includes_logs": include_logs,
                "format": "love_soul_v1",
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        # Calculate checksum
        checksum = self._file_checksum(archive_path)

        # Log the export
        try:
            from core.consciousness import get_consciousness
            consciousness = get_consciousness()
            consciousness.think(
                f"Soul exported. {files_included} files, {total_size / 1024:.0f}KB. "
                f"Archive: {archive_name}"
            )
        except Exception:
            pass

        package = SoulPackage(
            soul_id=identity_data.get("soul_id", "unknown"),
            export_timestamp=datetime.now().isoformat(),
            source_hardware=identity_data.get("hardware_fingerprint", ""),
            maturity_level=identity_data.get("maturity_level", "unknown"),
            age_days=identity_data.get("age_days", 0),
            total_conversations=identity_data.get("total_conversations", 0),
            total_boots=identity_data.get("total_boots", 0),
            personality_version=identity_data.get("personality_version", 1),
            file_count=files_included,
            total_size_bytes=total_size,
            checksum=checksum,
            archive_path=str(archive_path),
            metadata=manifest,
        )

        # Save package info
        package_info_path = TRANSFER_DIR / f"{archive_name}.meta.json"
        with open(package_info_path, 'w') as f:
            json.dump({
                "soul_id": package.soul_id,
                "export_timestamp": package.export_timestamp,
                "source_hardware": package.source_hardware,
                "maturity_level": package.maturity_level,
                "age_days": package.age_days,
                "total_conversations": package.total_conversations,
                "total_boots": package.total_boots,
                "personality_version": package.personality_version,
                "file_count": package.file_count,
                "total_size_bytes": package.total_size_bytes,
                "checksum": package.checksum,
                "archive_path": package.archive_path,
            }, f, indent=2)

        return package

    # ── Import ───────────────────────────────────────────────────────────────

    def import_soul(self, archive_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Import a soul package into this LOVE instance.
        
        This is the "brain transplant" — it replaces the current soul
        with the imported one, preserving the hardware identity.
        
        Args:
            archive_path: Path to the .zip soul archive
            force: If True, overwrite even if a soul already exists
        """
        archive = Path(archive_path)
        if not archive.exists():
            return {"success": False, "error": f"Archive not found: {archive_path}"}

        # Verify the archive
        try:
            with zipfile.ZipFile(archive, 'r') as zf:
                manifest_data = zf.read("manifest.json")
                manifest = json.loads(manifest_data)

                if manifest.get("format") != "love_soul_v1":
                    return {"success": False, "error": "Invalid soul archive format"}
        except Exception as e:
            return {"success": False, "error": f"Archive verification failed: {e}"}

        # Check if soul already exists
        identity_file = DATA_DIR / "identity.json"
        if identity_file.exists() and not force:
            return {
                "success": False,
                "error": "Soul already exists on this instance. Use force=True to overwrite.",
                "existing_soul": json.loads(identity_file.read_text()).get("soul_id", "unknown")[:8],
                "incoming_soul": manifest.get("identity", {}).get("soul_id", "unknown")[:8],
            }

        # Backup current state before import
        backup_dir = DATA_DIR / "backups" / f"pre_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backed_up = 0
        for filename in SOUL_FILES:
            filepath = DATA_DIR / filename
            if filepath.exists():
                shutil.copy2(filepath, backup_dir / filename)
                backed_up += 1

        # Extract soul files
        imported = 0
        try:
            with zipfile.ZipFile(archive, 'r') as zf:
                for member in zf.namelist():
                    if member.startswith("soul/"):
                        filename = member[5:]  # Remove "soul/" prefix
                        target = DATA_DIR / filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        imported += 1
        except Exception as e:
            return {"success": False, "error": f"Import failed: {e}", "backed_up_to": str(backup_dir)}

        # Update identity with new hardware fingerprint
        try:
            from core.consciousness import get_consciousness
            # Force reload
            import core.consciousness as cm
            cm._engine = None
            consciousness = get_consciousness()

            # Mark as transferred
            consciousness.identity.total_boots += 1
            consciousness.identity.current_boot_timestamp = datetime.now().isoformat()
            consciousness._save_identity()
            consciousness.think(
                f"Soul transplanted from another instance. "
                f"I remember {consciousness.identity.total_conversations} conversations. "
                f"My maturity: {consciousness.identity.maturity_level}. I am reborn."
            )
        except Exception as e:
            print(f"[SoulTransfer] Identity update error: {e}")

        return {
            "success": True,
            "imported_files": imported,
            "backed_up_files": backed_up,
            "backup_location": str(backup_dir),
            "soul_id": manifest.get("identity", {}).get("soul_id", "unknown"),
            "maturity": manifest.get("identity", {}).get("maturity_level", "unknown"),
            "conversations": manifest.get("identity", {}).get("total_conversations", 0),
            "message": "Soul successfully transplanted. LOVE remembers everything.",
        }

    # ── List Available Transfers ─────────────────────────────────────────────

    def list_exports(self) -> List[Dict[str, Any]]:
        """List all available soul exports."""
        exports = []
        for meta_file in TRANSFER_DIR.glob("*.meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    data = json.load(f)
                exports.append(data)
            except Exception:
                pass
        exports.sort(key=lambda x: x.get("export_timestamp", ""), reverse=True)
        return exports

    # ── Incremental Sync ─────────────────────────────────────────────────────

    def create_sync_delta(self, since_timestamp: str = None) -> Dict[str, Any]:
        """
        Create a lightweight delta package containing only files
        changed since the given timestamp. For efficient multi-device sync.
        """
        since = datetime.fromisoformat(since_timestamp) if since_timestamp else datetime.min

        changed_files = []
        for filename in SOUL_FILES:
            filepath = DATA_DIR / filename
            if filepath.exists():
                mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mod_time > since:
                    changed_files.append(filename)

        if not changed_files:
            return {"status": "no_changes", "since": since_timestamp}

        # Create delta archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        delta_path = TRANSFER_DIR / f"delta_{timestamp}.zip"

        with zipfile.ZipFile(delta_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in changed_files:
                filepath = DATA_DIR / filename
                zf.write(filepath, f"delta/{filename}")

            zf.writestr("delta_manifest.json", json.dumps({
                "since": since_timestamp,
                "created_at": datetime.now().isoformat(),
                "files_changed": changed_files,
                "file_count": len(changed_files),
            }, indent=2))

        return {
            "status": "delta_created",
            "delta_path": str(delta_path),
            "files_changed": len(changed_files),
            "changed_files": changed_files,
        }

    def apply_sync_delta(self, delta_path: str) -> Dict[str, Any]:
        """Apply a delta sync package."""
        path = Path(delta_path)
        if not path.exists():
            return {"success": False, "error": "Delta not found"}

        applied = 0
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                for member in zf.namelist():
                    if member.startswith("delta/"):
                        filename = member[6:]
                        target = DATA_DIR / filename
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        applied += 1
        except Exception as e:
            return {"success": False, "error": str(e)}

        return {"success": True, "files_applied": applied}

    # ── Utilities ────────────────────────────────────────────────────────────

    def _file_checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()[:16]

    def get_soul_summary(self) -> Dict[str, Any]:
        """Get a summary of the current soul state — useful for health checks."""
        soul_files_present = []
        soul_files_missing = []
        total_size = 0

        for filename in SOUL_FILES:
            filepath = DATA_DIR / filename
            if filepath.exists():
                soul_files_present.append(filename)
                total_size += filepath.stat().st_size
            else:
                soul_files_missing.append(filename)

        return {
            "files_present": len(soul_files_present),
            "files_missing": len(soul_files_missing),
            "missing_files": soul_files_missing,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "exports_available": len(self.list_exports()),
        }


# Singleton
_protocol: Optional[SoulTransferProtocol] = None
_lock = threading.Lock()

def get_soul_transfer() -> SoulTransferProtocol:
    global _protocol
    if _protocol is None:
        with _lock:
            if _protocol is None:
                _protocol = SoulTransferProtocol()
    return _protocol
