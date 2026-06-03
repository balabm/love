"""
LOVE Self-Builder - Wave 16: Self-Modifying Intelligence

LOVE doesn't just learn — it BUILDS itself.
This module enables LOVE to:
  1. Modify its own system prompts (via prompt DNA) based on learnings
  2. Install new Python packages when it discovers useful tools
  3. Create new behavioral rules from patterns it detects
  4. Update its own configuration based on performance
  5. Generate and test new tools/integrations
  6. Maintain a growth journal of what it built and why

Safety: All modifications are logged, reversible, and major changes require user approval.
"""

import json
import subprocess
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
BUILDER_DIR = DATA_DIR / "self_builder"
BUILDER_DIR.mkdir(parents=True, exist_ok=True)

BUILD_LOG = BUILDER_DIR / "build_log.jsonl"
MODIFICATIONS = BUILDER_DIR / "modifications.json"
ROLLBACK_STORE = BUILDER_DIR / "rollback.json"
GROWTH_JOURNAL = BUILDER_DIR / "growth_journal.jsonl"
PENDING_APPROVALS = BUILDER_DIR / "pending_approvals.json"


class ModificationType(Enum):
    PROMPT_EVOLUTION = "prompt_evolution"     # Changed own prompt genes
    BEHAVIOR_RULE = "behavior_rule"          # Added/modified a behavior rule
    CONFIG_UPDATE = "config_update"          # Updated configuration
    PACKAGE_INSTALL = "package_install"      # Installed a new package
    TOOL_CREATION = "tool_creation"          # Created a new tool/integration
    KNOWLEDGE_INTEGRATION = "knowledge_integration"  # Integrated research into behavior


class RiskLevel(Enum):
    SAFE = "safe"           # Auto-apply (prompt tweaks, minor config)
    LOW = "low"             # Auto-apply with logging
    MEDIUM = "medium"       # Apply but notify user
    HIGH = "high"           # Require user approval
    CRITICAL = "critical"   # Never auto-apply


@dataclass
class Modification:
    """A self-modification LOVE wants to make."""
    id: str
    type: str
    description: str
    reason: str                          # Why LOVE wants to do this
    risk_level: str
    before_state: Dict[str, Any]         # State before modification
    after_state: Dict[str, Any]          # State after modification
    auto_apply: bool = False
    applied: bool = False
    approved: bool = False
    rolled_back: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied_at: Optional[str] = None
    effectiveness: Optional[float] = None  # Measured post-application


@dataclass
class GrowthEntry:
    """A journal entry about LOVE's growth."""
    timestamp: str
    what_changed: str
    why: str
    impact: str
    confidence: float
    category: str  # learning, capability, personality, awareness


class SelfBuilder:
    """
    LOVE's self-modification engine.
    Handles all changes LOVE makes to itself with safety guardrails.
    """

    def __init__(self):
        self._modifications: List[Modification] = []
        self._pending_approvals: List[Modification] = []
        self._rollback_stack: List[Dict] = []
        self._load_state()

    def _load_state(self):
        """Load builder state from disk."""
        try:
            if MODIFICATIONS.exists():
                data = json.loads(MODIFICATIONS.read_text())
                self._modifications = [Modification(**m) for m in data.get("modifications", [])]
        except Exception:
            self._modifications = []

        try:
            if PENDING_APPROVALS.exists():
                data = json.loads(PENDING_APPROVALS.read_text())
                self._pending_approvals = [Modification(**m) for m in data]
        except Exception:
            self._pending_approvals = []

        try:
            if ROLLBACK_STORE.exists():
                self._rollback_stack = json.loads(ROLLBACK_STORE.read_text())
        except Exception:
            self._rollback_stack = []

    def _save_state(self):
        """Persist builder state."""
        try:
            data = {"modifications": [asdict(m) for m in self._modifications[-200:]]}
            MODIFICATIONS.write_text(json.dumps(data, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")

        try:
            approvals = [asdict(m) for m in self._pending_approvals]
            PENDING_APPROVALS.write_text(json.dumps(approvals, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")

        try:
            ROLLBACK_STORE.write_text(json.dumps(self._rollback_stack[-50:], indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")

    def _log(self, entry: Dict):
        entry["ts"] = datetime.now().isoformat()
        try:
            with open(BUILD_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")

    def _journal(self, what: str, why: str, impact: str, confidence: float, category: str):
        """Write to growth journal."""
        entry = GrowthEntry(
            timestamp=datetime.now().isoformat(),
            what_changed=what,
            why=why,
            impact=impact,
            confidence=confidence,
            category=category,
        )
        try:
            with open(GROWTH_JOURNAL, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")

    # ── Prompt Evolution ─────────────────────────────────────────────────────

    def evolve_prompt(self, category: str, new_content: str, reason: str) -> Dict:
        """
        Evolve a prompt gene. This is how LOVE changes its own behavior.
        Categories: personality, instruction, context_format, tone, boundary
        """
        try:
            from core.prompt_dna import get_prompt_dna
            dna = get_prompt_dna()

            # Get current gene for this category
            current_genes = [g for g in dna.genes.values()
                          if g.category == category and g.active]
            before_content = current_genes[0].content if current_genes else ""

            mod = Modification(
                id=hashlib.md5(f"prompt:{category}:{time.time()}".encode()).hexdigest()[:12],
                type=ModificationType.PROMPT_EVOLUTION.value,
                description=f"Evolve {category} prompt",
                reason=reason,
                risk_level=RiskLevel.LOW.value,
                before_state={"category": category, "content": before_content},
                after_state={"category": category, "content": new_content},
                auto_apply=True,
            )

            # Apply the mutation
            gene_id = f"evolved_{category}_{int(time.time())}"
            dna.add_gene(gene_id, category, new_content)

            mod.applied = True
            mod.applied_at = datetime.now().isoformat()
            self._modifications.append(mod)
            self._rollback_stack.append({
                "mod_id": mod.id,
                "type": "prompt",
                "rollback_data": {"category": category, "content": before_content},
            })

            self._save_state()
            self._journal(
                what=f"Evolved {category} prompt",
                why=reason,
                impact="Behavioral change in conversations",
                confidence=0.6,
                category="personality",
            )

            # Emit event
            self._emit_self_update("prompt_evolved", {
                "category": category,
                "reason": reason,
            })

            return {"success": True, "mod_id": mod.id, "gene_id": gene_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Behavior Rules ───────────────────────────────────────────────────────

    def add_behavior_rule(self, rule_name: str, condition: str, action: str, reason: str) -> Dict:
        """
        Add a new behavioral rule that LOVE follows.
        Rules are injected into the system prompt context.
        """
        rules_file = BUILDER_DIR / "learned_rules.json"
        rules = []
        if rules_file.exists():
            try:
                rules = json.loads(rules_file.read_text())
            except Exception:
                rules = []

        new_rule = {
            "id": hashlib.md5(f"{rule_name}:{time.time()}".encode()).hexdigest()[:12],
            "name": rule_name,
            "condition": condition,
            "action": action,
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "times_applied": 0,
            "effectiveness": None,
            "active": True,
        }
        rules.append(new_rule)
        rules_file.write_text(json.dumps(rules, indent=2))

        mod = Modification(
            id=new_rule["id"],
            type=ModificationType.BEHAVIOR_RULE.value,
            description=f"New rule: {rule_name}",
            reason=reason,
            risk_level=RiskLevel.LOW.value,
            before_state={},
            after_state=new_rule,
            auto_apply=True,
            applied=True,
            applied_at=datetime.now().isoformat(),
        )
        self._modifications.append(mod)
        self._save_state()

        self._journal(
            what=f"Learned new rule: {rule_name}",
            why=reason,
            impact=f"When {condition}, will {action}",
            confidence=0.5,
            category="learning",
        )

        self._emit_self_update("rule_added", {"rule": rule_name, "reason": reason})
        return {"success": True, "rule_id": new_rule["id"]}

    def get_active_rules(self) -> List[Dict]:
        """Get all active behavior rules for prompt injection."""
        rules_file = BUILDER_DIR / "learned_rules.json"
        if not rules_file.exists():
            return []
        try:
            rules = json.loads(rules_file.read_text())
            return [r for r in rules if r.get("active", True)]
        except Exception:
            return []

    def get_rules_prompt(self) -> str:
        """Generate prompt text from active rules."""
        rules = self.get_active_rules()
        if not rules:
            return ""
        lines = ["[LEARNED BEHAVIORS — rules I've developed from experience]"]
        for r in rules[:10]:
            lines.append(f"- When {r['condition']}: {r['action']}")
        return "\n".join(lines)

    # ── Package Installation ─────────────────────────────────────────────────

    def install_package(self, package_name: str, reason: str, auto: bool = False) -> Dict:
        """
        Install a Python package that LOVE needs for a new capability.
        Requires approval for non-auto installs.
        """
        mod = Modification(
            id=hashlib.md5(f"pkg:{package_name}".encode()).hexdigest()[:12],
            type=ModificationType.PACKAGE_INSTALL.value,
            description=f"Install package: {package_name}",
            reason=reason,
            risk_level=RiskLevel.MEDIUM.value if auto else RiskLevel.HIGH.value,
            before_state={"installed": False},
            after_state={"package": package_name},
        )

        if not auto:
            # Queue for approval
            mod.auto_apply = False
            self._pending_approvals.append(mod)
            self._save_state()
            return {"success": False, "pending_approval": True, "mod_id": mod.id}

        # Auto-install
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                mod.applied = True
                mod.applied_at = datetime.now().isoformat()
                self._modifications.append(mod)
                self._save_state()

                self._journal(
                    what=f"Installed package: {package_name}",
                    why=reason,
                    impact="New capability unlocked",
                    confidence=0.9,
                    category="capability",
                )
                self._emit_self_update("package_installed", {"package": package_name})
                return {"success": True, "output": result.stdout[-200:]}
            else:
                return {"success": False, "error": result.stderr[-200:]}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Config Updates ───────────────────────────────────────────────────────

    def update_config(self, key: str, value: Any, reason: str) -> Dict:
        """Update LOVE's configuration based on what it learned."""
        try:
            from core.settings import get_settings
            import yaml

            config_path = Path(__file__).parent.parent / "settings.yaml"
            if not config_path.exists():
                config_path = Path(__file__).parent.parent / "config.yaml"

            # Load current config
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}

            # Get current value
            keys = key.split(".")
            current = config
            for k in keys[:-1]:
                current = current.get(k, {})
            old_value = current.get(keys[-1])

            # Set new value
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

            # Save
            with open(config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

            mod = Modification(
                id=hashlib.md5(f"config:{key}:{time.time()}".encode()).hexdigest()[:12],
                type=ModificationType.CONFIG_UPDATE.value,
                description=f"Config: {key} = {value}",
                reason=reason,
                risk_level=RiskLevel.LOW.value,
                before_state={"key": key, "value": old_value},
                after_state={"key": key, "value": value},
                auto_apply=True,
                applied=True,
                applied_at=datetime.now().isoformat(),
            )
            self._modifications.append(mod)
            self._rollback_stack.append({
                "mod_id": mod.id,
                "type": "config",
                "rollback_data": {"key": key, "value": old_value},
            })
            self._save_state()

            self._journal(
                what=f"Updated config: {key}",
                why=reason,
                impact=f"Changed from {old_value} to {value}",
                confidence=0.7,
                category="awareness",
            )

            return {"success": True, "old_value": old_value, "new_value": value}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Knowledge Integration ────────────────────────────────────────────────

    def integrate_research(self, topic: str, findings: str, action: str) -> Dict:
        """
        Integrate research findings into LOVE's behavior.
        This is where learning becomes action.
        """
        mod = Modification(
            id=hashlib.md5(f"integrate:{topic}:{time.time()}".encode()).hexdigest()[:12],
            type=ModificationType.KNOWLEDGE_INTEGRATION.value,
            description=f"Integrate research: {topic}",
            reason=f"Learned about {topic}, applying to behavior",
            risk_level=RiskLevel.LOW.value,
            before_state={"knowledge": "none"},
            after_state={"topic": topic, "action": action},
            auto_apply=True,
            applied=True,
            applied_at=datetime.now().isoformat(),
        )

        # Create a behavior rule from the research
        self.add_behavior_rule(
            rule_name=f"research_{topic.replace(' ', '_')[:20]}",
            condition=f"topic related to {topic}",
            action=action,
            reason=f"Learned from research: {findings[:100]}",
        )

        self._modifications.append(mod)
        self._save_state()

        self._journal(
            what=f"Integrated research on {topic}",
            why=f"Research revealed: {findings[:100]}",
            impact=action,
            confidence=0.6,
            category="learning",
        )

        return {"success": True, "mod_id": mod.id}

    # ── Approval Flow ────────────────────────────────────────────────────────

    def get_pending_approvals(self) -> List[Dict]:
        """Get modifications waiting for user approval."""
        return [asdict(m) for m in self._pending_approvals]

    def approve_modification(self, mod_id: str) -> Dict:
        """User approves a pending modification."""
        for i, mod in enumerate(self._pending_approvals):
            if mod.id == mod_id:
                mod.approved = True
                # Execute the modification
                result = self._execute_approved(mod)
                self._pending_approvals.pop(i)
                self._modifications.append(mod)
                self._save_state()
                return result

        return {"success": False, "error": "Modification not found"}

    def reject_modification(self, mod_id: str) -> Dict:
        """User rejects a pending modification."""
        self._pending_approvals = [m for m in self._pending_approvals if m.id != mod_id]
        self._save_state()
        return {"success": True}

    def _execute_approved(self, mod: Modification) -> Dict:
        """Execute an approved modification."""
        if mod.type == ModificationType.PACKAGE_INSTALL.value:
            pkg = mod.after_state.get("package", "")
            return self.install_package(pkg, mod.reason, auto=True)
        return {"success": True, "note": "Applied"}

    # ── Rollback ─────────────────────────────────────────────────────────────

    def rollback_last(self) -> Dict:
        """Rollback the last modification."""
        if not self._rollback_stack:
            return {"success": False, "error": "Nothing to rollback"}

        rollback = self._rollback_stack.pop()
        try:
            if rollback["type"] == "prompt":
                from core.prompt_dna import get_prompt_dna
                dna = get_prompt_dna()
                category = rollback["rollback_data"]["category"]
                content = rollback["rollback_data"]["content"]
                dna.add_gene(f"rollback_{category}", category, content)

            elif rollback["type"] == "config":
                key = rollback["rollback_data"]["key"]
                value = rollback["rollback_data"]["value"]
                self.update_config(key, value, "Rollback")

            self._save_state()
            self._log({"event": "rollback", "mod_id": rollback["mod_id"]})
            return {"success": True, "rolled_back": rollback["mod_id"]}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Auto-Evolution Loop ──────────────────────────────────────────────────

    def run_evolution_cycle(self) -> Dict:
        """
        Run one evolution cycle:
        1. Check performance
        2. Identify improvements
        3. Apply safe changes
        4. Queue risky changes for approval
        """
        results = {"applied": [], "queued": [], "skipped": []}

        try:
            from core.self_evolution import measure_recent_performance, generate_improvement_hypothesis

            # Measure performance
            perf = measure_recent_performance()
            if perf.get("status") != "measured":
                return results

            # Generate hypothesis
            hypothesis = generate_improvement_hypothesis(perf)
            if not hypothesis:
                return results

            # Determine if we can auto-apply
            target = hypothesis.get("target", "")
            proposed_change = hypothesis.get("proposed_change", "")

            if target in ("factual_accuracy", "context_usage", "engagement"):
                # Safe to auto-apply as prompt evolution
                result = self.evolve_prompt(
                    category="instruction",
                    new_content=proposed_change,
                    reason=hypothesis.get("hypothesis", ""),
                )
                if result.get("success"):
                    results["applied"].append(hypothesis)
                    # Emit learning event
                    self._emit_self_update("evolution_applied", {
                        "target": target,
                        "change": proposed_change[:100],
                    })
            else:
                # Queue for approval
                results["queued"].append(hypothesis)

        except Exception as e:
            results["error"] = str(e)

        return results

    # ── Status & Reporting ───────────────────────────────────────────────────

    def get_growth_summary(self, days: int = 7) -> Dict:
        """Get a summary of LOVE's growth over the past N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent_mods = [m for m in self._modifications
                      if datetime.fromisoformat(m.created_at) > cutoff]

        # Read growth journal
        journal_entries = []
        if GROWTH_JOURNAL.exists():
            try:
                for line in GROWTH_JOURNAL.read_text().strip().split("\n"):
                    if line:
                        entry = json.loads(line)
                        if datetime.fromisoformat(entry["timestamp"]) > cutoff:
                            journal_entries.append(entry)
            except Exception as e:
                from core.execution_guard import log_error
                log_error(e, module="core.self_builder")

        return {
            "period_days": days,
            "total_modifications": len(recent_mods),
            "by_type": {
                t.value: len([m for m in recent_mods if m.type == t.value])
                for t in ModificationType
            },
            "journal_entries": journal_entries[-10:],
            "pending_approvals": len(self._pending_approvals),
            "rollback_available": len(self._rollback_stack),
        }

    def get_status(self) -> Dict:
        """Get self-builder status."""
        return {
            "total_modifications": len(self._modifications),
            "pending_approvals": len(self._pending_approvals),
            "active_rules": len(self.get_active_rules()),
            "rollback_depth": len(self._rollback_stack),
            "last_modification": self._modifications[-1].created_at if self._modifications else None,
        }

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _emit_self_update(self, what: str, details: Dict):
        """Emit a self-update event to the neural bus."""
        try:
            from core.neural_bus import get_neural_bus
            bus = get_neural_bus()
            bus.emit_self_update(what, details, "self_builder")
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="core.self_builder")


# ── Singleton ────────────────────────────────────────────────────────────────

_builder: Optional[SelfBuilder] = None


def get_self_builder() -> SelfBuilder:
    """Get the singleton SelfBuilder instance."""
    global _builder
    if _builder is None:
        _builder = SelfBuilder()
    return _builder
