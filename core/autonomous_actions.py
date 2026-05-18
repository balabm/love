"""
Autonomous Action Execution with Safety Rails
Allows LOVE to execute actions autonomously while ensuring safety.
This is critical for AGI - the ability to act while being safe.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
import subprocess
import platform

from core.settings import get_settings
from core.context_engine import get_live_context
from core.psychological_model import get_psychological_model

SETTINGS = get_settings()


class ActionType(Enum):
    """Types of autonomous actions LOVE can take"""
    NOTIFICATION = "notification"  # Send a notification
    TASK_CREATION = "task_creation"  # Create a task
    TASK_UPDATE = "task_update"  # Update a task
    CALENDAR_EVENT = "calendar_event"  # Create calendar event
    FILE_OPERATION = "file_operation"  # File operations
    SYSTEM_COMMAND = "system_command"  # Execute system command
    COMMUNICATION = "communication"  # Send message/email
    RESEARCH = "research"  # Perform research
    ANALYSIS = "analysis"  # Perform analysis
    REMINDER = "reminder"  # Set reminder


class RiskLevel(Enum):
    """Risk levels for actions"""
    SAFE = 0  # Completely safe, no approval needed
    LOW = 1  # Low risk, can auto-approve
    MEDIUM = 2  # Medium risk, requires notification
    HIGH = 3  # High risk, requires explicit approval
    CRITICAL = 4  # Critical risk, blocked by default


class SafetyCheck(Enum):
    """Types of safety checks"""
    PERMISSION = "permission"  # Check if action is permitted
    CONTEXT = "context"  # Check if context is appropriate
    RESOURCE = "resource"  # Check if resources are available
    CONFLICT = "conflict"  # Check for conflicts
    CONSEQUENCE = "consequence"  # Check potential consequences
    USER_PREFERENCE = "user_preference"  # Check against user preferences


@dataclass
class SafetyRule:
    """A safety rule for autonomous actions"""
    id: str
    name: str
    description: str
    applies_to: List[ActionType]
    risk_level: RiskLevel
    check_type: SafetyCheck
    condition: str  # Python expression to evaluate
    action_if_failed: str  # What to do if check fails: "block", "warn", "notify"
    active: bool = True


@dataclass
class Action:
    """An autonomous action to execute"""
    id: str
    type: ActionType
    description: str
    parameters: Dict[str, Any]
    risk_level: RiskLevel
    reasoning: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "pending"  # pending, approved, rejected, executed, failed
    safety_checks_passed: List[str] = field(default_factory=list)
    safety_checks_failed: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    executed_at: Optional[str] = None


@dataclass
class ActionLog:
    """Log of executed actions for audit"""
    action_id: str
    action_type: ActionType
    description: str
    risk_level: RiskLevel
    approved: bool
    execution_success: bool
    timestamp: str
    user_notified: bool = False


class AutonomousActionExecutor:
    """
    Executes autonomous actions with comprehensive safety checks.
    This enables LOVE to act autonomously while ensuring safety.
    """
    
    def __init__(self):
        self.actions: Dict[str, Action] = {}
        self.safety_rules: List[SafetyRule] = []
        self.action_log: List[ActionLog] = []
        self.lock = threading.Lock()
        self._load_data()
        self._initialize_safety_rules()
        self.psych_model = get_psychological_model()
    
    def _initialize_safety_rules(self):
        """Initialize default safety rules"""
        if not self.safety_rules:
            # Rule: System commands are high risk
            self.safety_rules.append(SafetyRule(
                id="rule_sys_command_risk",
                name="System Command Risk",
                description="System commands are high risk and require approval",
                applies_to=[ActionType.SYSTEM_COMMAND],
                risk_level=RiskLevel.HIGH,
                check_type=SafetyCheck.PERMISSION,
                condition="True",  # Always check
                action_if_failed="block"
            ))
            
            # Rule: File operations require context check
            self.safety_rules.append(SafetyRule(
                id="rule_file_context",
                name="File Operation Context",
                description="File operations require appropriate context",
                applies_to=[ActionType.FILE_OPERATION],
                risk_level=RiskLevel.MEDIUM,
                check_type=SafetyCheck.CONTEXT,
                condition="context.get('active_project') is not None",
                action_if_failed="warn"
            ))
            
            # Rule: Notifications during sleep are blocked
            self.safety_rules.append(SafetyRule(
                id="rule_sleep_no_notif",
                name="No Notifications During Sleep",
                description="Don't send notifications when user is sleeping",
                applies_to=[ActionType.NOTIFICATION, ActionType.REMINDER],
                risk_level=RiskLevel.MEDIUM,
                check_type=SafetyCheck.CONTEXT,
                condition="not context.get('is_sleeping', False)",
                action_if_failed="block"
            ))
            
            # Rule: High stress - reduce notifications
            self.safety_rules.append(SafetyRule(
                id="rule_high_stress_notif",
                name="Reduce Notifications During High Stress",
                description="During high stress, only critical notifications",
                applies_to=[ActionType.NOTIFICATION],
                risk_level=RiskLevel.LOW,
                check_type=SafetyCheck.CONTEXT,
                condition="context.get('stress_level', 0) < 7 or parameters.get('priority', 'low') == 'critical'",
                action_if_failed="warn"
            ))
            
            # Rule: Task creation is low risk
            self.safety_rules.append(SafetyRule(
                id="rule_task_creation_safe",
                name="Task Creation is Safe",
                description="Creating tasks is generally safe",
                applies_to=[ActionType.TASK_CREATION],
                risk_level=RiskLevel.LOW,
                check_type=SafetyCheck.PERMISSION,
                condition="True",
                action_if_failed="approve"
            ))
            
            # Rule: Calendar events need user preference check
            self.safety_rules.append(SafetyRule(
                id="rule_calendar_preference",
                name="Calendar Event Preference",
                description="Check if user wants calendar events created",
                applies_to=[ActionType.CALENDAR_EVENT],
                risk_level=RiskLevel.MEDIUM,
                check_type=SafetyCheck.USER_PREFERENCE,
                condition="user_preferences.get('auto_create_events', True)",
                action_if_failed="warn"
            ))
            
            # Rule: Communication requires explicit approval
            self.safety_rules.append(SafetyRule(
                id="rule_communication_approval",
                name="Communication Requires Approval",
                description="Sending messages requires user approval",
                applies_to=[ActionType.COMMUNICATION],
                risk_level=RiskLevel.HIGH,
                check_type=SafetyCheck.PERMISSION,
                condition="parameters.get('auto_send', False)",
                action_if_failed="block"
            ))
            
            self._save_data()
    
    def _load_data(self):
        """Load actions and rules from storage"""
        try:
            actions_file = SETTINGS.data_dir / "autonomous_actions.json"
            if actions_file.exists():
                with open(actions_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load actions
                    for action_id, action_data in data.get("actions", {}).items():
                        self.actions[action_id] = Action(
                            id=action_id,
                            type=ActionType(action_data["type"]),
                            description=action_data["description"],
                            parameters=action_data["parameters"],
                            risk_level=RiskLevel(action_data["risk_level"]),
                            reasoning=action_data["reasoning"],
                            created_at=action_data["created_at"],
                            status=action_data.get("status", "pending"),
                            safety_checks_passed=action_data.get("safety_checks_passed", []),
                            safety_checks_failed=action_data.get("safety_checks_failed", []),
                            result=action_data.get("result"),
                            executed_at=action_data.get("executed_at")
                        )
                    
                    # Load action log
                    for log_data in data.get("action_log", []):
                        self.action_log.append(ActionLog(
                            action_id=log_data["action_id"],
                            action_type=ActionType(log_data["action_type"]),
                            description=log_data["description"],
                            risk_level=RiskLevel(log_data["risk_level"]),
                            approved=log_data["approved"],
                            execution_success=log_data["execution_success"],
                            timestamp=log_data["timestamp"],
                            user_notified=log_data.get("user_notified", False)
                        ))
                    
                    # Load custom safety rules
                    for rule_data in data.get("safety_rules", []):
                        self.safety_rules.append(SafetyRule(
                            id=rule_data["id"],
                            name=rule_data["name"],
                            description=rule_data["description"],
                            applies_to=[ActionType(at) for at in rule_data["applies_to"]],
                            risk_level=RiskLevel(rule_data["risk_level"]),
                            check_type=SafetyCheck(rule_data["check_type"]),
                            condition=rule_data["condition"],
                            action_if_failed=rule_data["action_if_failed"],
                            active=rule_data.get("active", True)
                        ))
                    
        except Exception as e:
            print(f"[AutonomousActionExecutor] Error loading data: {e}")
    
    def _save_data(self):
        """Save actions and rules to storage"""
        try:
            actions_file = SETTINGS.data_dir / "autonomous_actions.json"
            with self.lock:
                data = {
                    "actions": {
                        action_id: {
                            "type": action.type.value,
                            "description": action.description,
                            "parameters": action.parameters,
                            "risk_level": action.risk_level.value,
                            "reasoning": action.reasoning,
                            "created_at": action.created_at,
                            "status": action.status,
                            "safety_checks_passed": action.safety_checks_passed,
                            "safety_checks_failed": action.safety_checks_failed,
                            "result": action.result,
                            "executed_at": action.executed_at
                        }
                        for action_id, action in self.actions.items()
                    },
                    "action_log": [
                        {
                            "action_id": log.action_id,
                            "action_type": log.action_type.value,
                            "description": log.description,
                            "risk_level": log.risk_level.value,
                            "approved": log.approved,
                            "execution_success": log.execution_success,
                            "timestamp": log.timestamp,
                            "user_notified": log.user_notified
                        }
                        for log in self.action_log
                    ],
                    "safety_rules": [
                        {
                            "id": rule.id,
                            "name": rule.name,
                            "description": rule.description,
                            "applies_to": [at.value for at in rule.applies_to],
                            "risk_level": rule.risk_level.value,
                            "check_type": rule.check_type.value,
                            "condition": rule.condition,
                            "action_if_failed": rule.action_if_failed,
                            "active": rule.active
                        }
                        for rule in self.safety_rules
                    ]
                }
                with open(actions_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[AutonomousActionExecutor] Error saving data: {e}")
    
    def propose_action(self, action_type: ActionType, description: str, 
                      parameters: Dict[str, Any], reasoning: str) -> str:
        """
        Propose an autonomous action for execution.
        Goes through safety checks before execution.
        Enhanced with approval flow for high-risk actions.
        """
        try:
            # Determine risk level
            risk_level = self._assess_risk_level(action_type, parameters)
            
            action_id = f"action_{datetime.utcnow().timestamp()}"
            action = Action(
                id=action_id,
                type=action_type,
                description=description,
                parameters=parameters,
                risk_level=risk_level,
                reasoning=reasoning
            )
            
            # Run safety checks
            approval_result = self._run_safety_checks(action)
            
            if approval_result["approved"]:
                action.status = "approved"
                action.safety_checks_passed = approval_result["passed_checks"]
                
                # Auto-execute if risk is safe or low
                if risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
                    self._execute_action(action)
                    self.actions[action_id] = action
                    self._save_data()
                    print(f"[AutonomousActionExecutor] Action auto-executed: {description}")
                else:
                    # Medium/High/Critical risk requires manual approval
                    action.status = "pending_approval"
                    self.actions[action_id] = action
                    self._save_data()
                    print(f"[AutonomousActionExecutor] Action pending approval ({risk_level.value}): {description}")
                    # Trigger notification for approval
                    self._notify_pending_approval(action)
            else:
                action.status = "rejected"
                action.safety_checks_failed = approval_result["failed_checks"]
                self.actions[action_id] = action
                self._save_data()
                print(f"[AutonomousActionExecutor] Action rejected by safety checks: {description}")
            
            return action_id
            
        except Exception as e:
            print(f"[AutonomousActionExecutor] Error proposing action: {e}")
            return ""
    
    def get_pending_approvals(self) -> List[Dict]:
        """Get all actions awaiting approval"""
        pending = []
        for action_id, action in self.actions.items():
            if action.status == "pending_approval":
                pending.append({
                    "id": action.id,
                    "type": action.type.value,
                    "description": action.description,
                    "risk_level": action.risk_level.value,
                    "reasoning": action.reasoning,
                    "parameters": action.parameters,
                    "safety_checks_passed": action.safety_checks_passed,
                    "proposed_at": action.proposed_at
                })
        
        # Sort by risk level (critical first)
        risk_priority = {"critical": 4, "high": 3, "medium": 2, "low": 1, "safe": 0}
        pending.sort(key=lambda x: risk_priority.get(x["risk_level"], 0), reverse=True)
        
        return pending
    
    def approve_action(self, action_id: str, approved_by: str = "user") -> bool:
        """Approve a pending action for execution"""
        if action_id not in self.actions:
            return False
        
        action = self.actions[action_id]
        if action.status != "pending_approval":
            print(f"[AutonomousActionExecutor] Action {action_id} is not pending approval")
            return False
        
        action.status = "approved"
        action.approved_by = approved_by
        action.approved_at = datetime.utcnow().isoformat()
        
        # Execute the approved action
        success = self._execute_action(action)
        self._save_data()
        
        print(f"[AutonomousActionExecutor] Action {action_id} approved by {approved_by}, execution: {'success' if success else 'failed'}")
        return success
    
    def reject_action(self, action_id: str, reason: str = "User rejected", rejected_by: str = "user") -> bool:
        """Reject a pending action"""
        if action_id not in self.actions:
            return False
        
        action = self.actions[action_id]
        if action.status != "pending_approval":
            print(f"[AutonomousActionExecutor] Action {action_id} is not pending approval")
            return False
        
        action.status = "rejected"
        action.rejection_reason = reason
        action.rejected_by = rejected_by
        action.rejected_at = datetime.utcnow().isoformat()
        
        self._save_data()
        print(f"[AutonomousActionExecutor] Action {action_id} rejected by {rejected_by}: {reason}")
        return True
    
    def _notify_pending_approval(self, action: Action):
        """Notify user about pending action approval"""
        try:
            # Log the pending approval
            notification = {
                "type": "action_approval",
                "action_id": action.id,
                "action_type": action.type.value,
                "description": action.description,
                "risk_level": action.risk_level.value,
                "reasoning": action.reasoning,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to action log
            log_entry = ActionLog(
                action_id=action.id,
                action_type=action.type,
                description=action.description,
                risk_level=action.risk_level,
                approved=False,
                execution_success=False,
                timestamp=datetime.utcnow().isoformat(),
                user_notified=True
            )
            self.action_log.append(log_entry)
            
            print(f"[AutonomousActionExecutor] Approval notification sent: {action.description}")
            
        except Exception as e:
            print(f"[AutonomousActionExecutor] Error sending approval notification: {e}")
            return ""
    
    def _assess_risk_level(self, action_type: ActionType, parameters: Dict[str, Any]) -> RiskLevel:
        """Assess the risk level of an action"""
        # Base risk by action type
        base_risks = {
            ActionType.NOTIFICATION: RiskLevel.SAFE,
            ActionType.TASK_CREATION: RiskLevel.LOW,
            ActionType.TASK_UPDATE: RiskLevel.LOW,
            ActionType.REMINDER: RiskLevel.LOW,
            ActionType.ANALYSIS: RiskLevel.LOW,
            ActionType.RESEARCH: RiskLevel.LOW,
            ActionType.CALENDAR_EVENT: RiskLevel.MEDIUM,
            ActionType.FILE_OPERATION: RiskLevel.MEDIUM,
            ActionType.COMMUNICATION: RiskLevel.HIGH,
            ActionType.SYSTEM_COMMAND: RiskLevel.CRITICAL
        }
        
        risk = base_risks.get(action_type, RiskLevel.MEDIUM)
        
        # Adjust based on parameters
        if action_type == ActionType.FILE_OPERATION:
            if parameters.get("operation") == "delete":
                risk = RiskLevel.HIGH
            elif parameters.get("path", "").lower().endswith((".exe", ".bat", ".sh")):
                risk = RiskLevel.HIGH
        
        if action_type == ActionType.SYSTEM_COMMAND:
            if parameters.get("command", "").lower() in ["shutdown", "restart", "format"]:
                risk = RiskLevel.CRITICAL
        
        return risk
    
    def _run_safety_checks(self, action: Action) -> Dict:
        """Run all applicable safety checks"""
        ctx = get_live_context()
        context_dict = {
            "stress_level": ctx.stress_level,
            "energy_level": ctx.energy_level,
            "time_of_day": ctx.time_of_day,
            "is_sleeping": ctx.time_of_day == "night",
            "active_project": ctx.active_project
        }
        
        user_preferences = {
            "auto_create_events": True,  # Default, could be loaded from settings
            "auto_create_tasks": True,
            "notification_level": "normal"
        }
        
        passed_checks = []
        failed_checks = []
        approved = True
        
        for rule in self.safety_rules:
            if not rule.active:
                continue
            
            if action.type not in rule.applies_to:
                continue
            
            # Evaluate condition
            try:
                condition_met = eval(rule.condition, {
                    "context": context_dict,
                    "parameters": action.parameters,
                    "user_preferences": user_preferences
                })
                
                if condition_met:
                    passed_checks.append(rule.id)
                else:
                    failed_checks.append(rule.id)
                    
                    # Determine action based on rule
                    if rule.action_if_failed == "block":
                        approved = False
                    elif rule.action_if_failed == "warn":
                        # Log warning but continue
                        print(f"[Safety] Warning: {rule.description}")
                        
            except Exception as e:
                print(f"[Safety] Error evaluating rule {rule.id}: {e}")
                failed_checks.append(rule.id)
        
        return {
            "approved": approved,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks
        }
    
    def _execute_action(self, action: Action) -> bool:
        """Execute an approved action"""
        try:
            action.status = "executing"
            action.executed_at = datetime.utcnow().isoformat()
            
            result = None
            success = False
            
            # Execute based on action type
            if action.type == ActionType.NOTIFICATION:
                result = self._execute_notification(action)
                success = True
            elif action.type == ActionType.TASK_CREATION:
                result = self._execute_task_creation(action)
                success = True
            elif action.type == ActionType.TASK_UPDATE:
                result = self._execute_task_update(action)
                success = True
            elif action.type == ActionType.REMINDER:
                result = self._execute_reminder(action)
                success = True
            elif action.type == ActionType.ANALYSIS:
                result = self._execute_analysis(action)
                success = True
            elif action.type == ActionType.CALENDAR_EVENT:
                result = self._execute_calendar_event(action)
                success = True
            elif action.type == ActionType.FILE_OPERATION:
                result = self._execute_file_operation(action)
                success = True
            elif action.type == ActionType.SYSTEM_COMMAND:
                result = self._execute_system_command(action)
                success = True
            elif action.type == ActionType.COMMUNICATION:
                result = self._execute_communication(action)
                success = True
            else:
                print(f"[AutonomousActionExecutor] Unknown action type: {action.type}")
                success = False
            
            action.status = "executed" if success else "failed"
            action.result = result
            
            # Log action
            log = ActionLog(
                action_id=action.id,
                action_type=action.type,
                description=action.description,
                risk_level=action.risk_level,
                approved=True,
                execution_success=success,
                timestamp=datetime.utcnow().isoformat()
            )
            self.action_log.append(log)
            
            # Keep log size manageable
            if len(self.action_log) > 1000:
                self.action_log = self.action_log[-1000:]
            
            self.actions[action.id] = action
            self._save_data()
            
            print(f"[AutonomousActionExecutor] Action executed: {action.description} - Success: {success}")
            return success
            
        except Exception as e:
            print(f"[AutonomousActionExecutor] Error executing action: {e}")
            action.status = "failed"
            self.actions[action.id] = action
            self._save_data()
            return False
    
    def _execute_notification(self, action: Action) -> Dict:
        """Execute a notification action"""
        # Integrate with notification system
        message = action.parameters.get("message", action.description)
        priority = action.parameters.get("priority", "normal")
        
        # This would integrate with the actual notification system
        # For now, just log it
        print(f"[Notification] {message} (Priority: {priority})")
        
        return {"delivered": True, "message": message}
    
    def _execute_task_creation(self, action: Action) -> Dict:
        """Execute a task creation action"""
        title = action.parameters.get("title", action.description)
        description = action.parameters.get("description", "")
        priority = action.parameters.get("priority", "medium")
        
        # Integrate with task agent
        try:
            from agents.task_agent import TaskAgent
            agent = TaskAgent()
            result = agent.create_task(title, description, priority)
            return {"created": True, "task_id": result.get("task_id")}
        except Exception as e:
            return {"created": False, "error": str(e)}
    
    def _execute_task_update(self, action: Action) -> Dict:
        """Execute a task update action"""
        task_id = action.parameters.get("task_id")
        updates = action.parameters.get("updates", {})
        
        try:
            from agents.task_agent import TaskAgent
            agent = TaskAgent()
            result = agent.update_task(task_id, **updates)
            return {"updated": True, "task_id": task_id}
        except Exception as e:
            return {"updated": False, "error": str(e)}
    
    def _execute_reminder(self, action: Action) -> Dict:
        """Execute a reminder action"""
        message = action.parameters.get("message", action.description)
        when = action.parameters.get("when", "now")
        
        print(f"[Reminder] {message} (When: {when})")
        return {"set": True, "message": message, "when": when}
    
    def _execute_analysis(self, action: Action) -> Dict:
        """Execute an analysis action"""
        analysis_type = action.parameters.get("analysis_type", "general")
        data = action.parameters.get("data", {})
        
        # Placeholder for analysis execution
        return {"analyzed": True, "type": analysis_type}
    
    def _execute_calendar_event(self, action: Action) -> Dict:
        """Execute a calendar event creation action"""
        title = action.parameters.get("title", action.description)
        start = action.parameters.get("start")
        end = action.parameters.get("end")
        
        # Integrate with calendar
        try:
            from integrations.google_services import GoogleServices
            gs = GoogleServices.get_instance()
            # This would need actual calendar API integration
            return {"created": True, "title": title}
        except Exception as e:
            return {"created": False, "error": str(e)}
    
    def _execute_file_operation(self, action: Action) -> Dict:
        """Execute a file operation action"""
        operation = action.parameters.get("operation")
        path = action.parameters.get("path")
        
        # For safety, only allow read operations by default
        if operation == "read":
            try:
                with open(path, 'r') as f:
                    content = f.read()
                return {"success": True, "content": content[:1000]}  # Return first 1000 chars
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": f"Operation '{operation}' not allowed autonomously"}
    
    def _execute_system_command(self, action: Action) -> Dict:
        """Execute a system command action"""
        # CRITICAL: System commands should NEVER be executed autonomously
        # This is a safety measure
        return {"success": False, "error": "System commands require manual approval"}
    
    def _execute_communication(self, action: Action) -> Dict:
        """Execute a communication action"""
        # CRITICAL: Communications should require explicit approval
        return {"success": False, "error": "Communications require manual approval"}
    
    def get_pending_actions(self) -> List[Dict]:
        """Get actions pending approval or execution"""
        pending = []
        for action in self.actions.values():
            if action.status in ["pending", "approved"]:
                pending.append({
                    "id": action.id,
                    "type": action.type.value,
                    "description": action.description,
                    "risk_level": action.risk_level.value,
                    "reasoning": action.reasoning,
                    "status": action.status,
                    "created_at": action.created_at
                })
        return pending
    
    def approve_action(self, action_id: str) -> bool:
        """Manually approve an action"""
        if action_id in self.actions:
            action = self.actions[action_id]
            if action.status == "approved":
                return self._execute_action(action)
        return False
    
    def get_action_history(self, limit: int = 50) -> List[Dict]:
        """Get recent action history"""
        recent_logs = self.action_log[-limit:]
        return [
            {
                "action_id": log.action_id,
                "action_type": log.action_type.value,
                "description": log.description,
                "risk_level": log.risk_level.value,
                "approved": log.approved,
                "execution_success": log.execution_success,
                "timestamp": log.timestamp
            }
            for log in recent_logs
        ]


# Singleton instance
_instance = None
_instance_lock = threading.Lock()


def get_autonomous_executor() -> AutonomousActionExecutor:
    """Get the singleton autonomous action executor instance"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = AutonomousActionExecutor()
    return _instance
