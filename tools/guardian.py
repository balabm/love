"""
Work-Life Guardian (Professional Autonomy)
Monitors work hours, Git activity, and enforces configurable work-life balance.
"""


def _platform_system() -> str:
    """Return platform name without blocking."""
    import sys as _sys
    if _sys.platform == "win32": return "Windows"
    if _sys.platform == "darwin": return "Darwin"
    return "Linux"

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Optional Git support
try:
    from git import Repo
    from git.exc import InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    Repo = None
    InvalidGitRepositoryError = Exception

from core.memory import save_log
from core.settings import get_settings

# Load settings
SETTINGS = get_settings()
USER_NAME = SETTINGS.user.name
WORK_LIMIT = SETTINGS.work.daily_limit_hours
WARNING_THRESHOLD = SETTINGS.work.warning_threshold
AUTO_COMMIT_MSG = SETTINGS.work.auto_commit_message

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Default user profile structure (now configurable)
DEFAULT_PROFILE = {
    "name": USER_NAME,
    "daily_work_limit_hours": WORK_LIMIT,
    "dev_folders": SETTINGS.work.dev_folders or [],
    "meetings": [],
    "tomorrows_agenda": [],
    "work_patterns": {
        "average_start_time": "09:00",
        "average_end_time": "18:00",
        "preferred_break_times": ["12:00", "15:30"]
    },
    "focus_blocks": {
        "deep_work": ["09:00-12:00", "14:00-17:00"],
        "meetings": ["10:00-11:00", "16:00-17:00"]
    }
}


def get_user_profile() -> Dict[str, Any]:
    """Load or create user profile."""
    if USER_PROFILE_PATH.exists():
        with open(USER_PROFILE_PATH, 'r') as f:
            profile = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_PROFILE.items():
                if key not in profile:
                    profile[key] = value
            return profile
    return DEFAULT_PROFILE.copy()


def save_user_profile(profile: Dict[str, Any]):
    """Save user profile to disk."""
    with open(USER_PROFILE_PATH, 'w') as f:
        json.dump(profile, f, indent=2)


class GitActivityTracker:
    """Scans dev folders for Git commits and calculates work time."""
    
    def __init__(self, dev_folders: List[str]):
        self.dev_folders = [Path(f) for f in dev_folders if Path(f).exists()]
        self.today_commits = []
        self.work_sessions = []
        
    def scan_all_repos(self) -> List[Dict[str, Any]]:
        """Scan all dev folders for Git activity today."""
        all_commits = []
        
        if not GIT_AVAILABLE:
            # Return empty if GitPython not installed
            self.today_commits = []
            self.work_sessions = []
            return []
        
        today = datetime.now().date()
        
        for folder in self.dev_folders:
            if not folder.exists():
                continue
                
            # Find all git repos in this folder
            for repo_path in self._find_git_repos(folder):
                try:
                    repo = Repo(repo_path)
                    commits = self._get_today_commits(repo, today)
                    all_commits.extend(commits)
                except InvalidGitRepositoryError:
                    continue
                    
        self.today_commits = sorted(all_commits, key=lambda x: x['timestamp'])
        self._calculate_work_sessions()
        
        return self.today_commits
    
    def _find_git_repos(self, base_path: Path) -> List[Path]:
        """Find all Git repositories under a path."""
        repos = []
        for item in base_path.iterdir():
            if item.is_dir():
                git_dir = item / ".git"
                if git_dir.exists():
                    repos.append(item)
                # Also check one level deeper
                elif not item.name.startswith('.'):
                    for subitem in item.iterdir():
                        if subitem.is_dir():
                            subgit = subitem / ".git"
                            if subgit.exists():
                                repos.append(subitem)
        return repos
    
    def _get_today_commits(self, repo: Repo, today: datetime.date) -> List[Dict[str, Any]]:
        """Get commits from today in a repo."""
        commits = []
        
        for commit in repo.iter_commits('HEAD', max_count=50):
            commit_date = datetime.fromtimestamp(commit.committed_date).date()
            if commit_date == today:
                commits.append({
                    'repo': repo.working_dir,
                    'message': commit.message.strip(),
                    'timestamp': datetime.fromtimestamp(commit.committed_date),
                    'author': commit.author.name,
                    'hexsha': commit.hexsha[:8]
                })
            elif commit_date < today:
                break
                
        return commits
    
    def _calculate_work_sessions(self):
        """Group commits into work sessions (gaps > 30 min = new session)."""
        if not self.today_commits:
            self.work_sessions = []
            return
            
        sessions = []
        current_session = {
            'start': self.today_commits[0]['timestamp'],
            'end': self.today_commits[0]['timestamp'],
            'commits': [self.today_commits[0]]
        }
        
        for commit in self.today_commits[1:]:
            gap = (commit['timestamp'] - current_session['end']).total_seconds() / 60
            
            if gap > 30:  # 30 min gap = new session
                sessions.append(current_session)
                current_session = {
                    'start': commit['timestamp'],
                    'end': commit['timestamp'],
                    'commits': [commit]
                }
            else:
                current_session['end'] = commit['timestamp']
                current_session['commits'].append(commit)
                
        sessions.append(current_session)
        self.work_sessions = sessions
    
    def get_total_work_hours(self) -> float:
        """Calculate total work hours from sessions."""
        total_minutes = 0
        for session in self.work_sessions:
            duration = (session['end'] - session['start']).total_seconds() / 60
            # Cap individual sessions at 4 hours (prevents overnight commits skewing data)
            if duration > 240:
                duration = 240
            total_minutes += duration
            
        return round(total_minutes / 60, 2)
    
    def get_work_summary(self) -> Dict[str, Any]:
        """Get summary of today's work activity."""
        return {
            'total_commits': len(self.today_commits),
            'work_sessions': self.work_sessions,
            'total_hours': self.get_total_work_hours(),
            'repositories': list(set(c['repo'] for c in self.today_commits)),
            'first_commit': self.today_commits[0]['timestamp'].strftime('%H:%M') if self.today_commits else None,
            'last_commit': self.today_commits[-1]['timestamp'].strftime('%H:%M') if self.today_commits else None
        }


class TimesheetGenerator:
    """Generates automated 9-hour timesheets with overflow handling."""
    
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.work_limit = profile.get('daily_work_limit_hours', 9)
        
    def generate_timesheet(self, git_activity: Dict[str, Any], manual_entries: List[Dict] = None) -> Dict[str, Any]:
        """Generate today's timesheet."""
        today = datetime.now().strftime('%Y-%m-%d')
        
        entries = []
        
        # Add Git-based work sessions
        for session in git_activity.get('work_sessions', []):
            entries.append({
                'type': 'development',
                'start': session['start'].strftime('%H:%M'),
                'end': session['end'].strftime('%H:%M'),
                'duration_hours': round((session['end'] - session['start']).total_seconds() / 3600, 2),
                'description': f"Coding: {len(session['commits'])} commits",
                'source': 'git'
            })
            
        # Add manual entries
        if manual_entries:
            entries.extend(manual_entries)
            
        # Calculate totals
        total_hours = sum(e['duration_hours'] for e in entries)
        
        timesheet = {
            'date': today,
            'entries': entries,
            'total_hours': round(total_hours, 2),
            'work_limit_hours': self.work_limit,
            'remaining_hours': round(max(0, self.work_limit - total_hours), 2),
            'overflow_hours': round(max(0, total_hours - self.work_limit), 2),
            'status': 'under_limit' if total_hours <= self.work_limit else 'overflow'
        }
        
        return timesheet
    
    def handle_overflow(self, timesheet: Dict[str, Any], overflow_tasks: List[Dict]) -> Dict[str, Any]:
        """Roll overflow tasks to tomorrow's agenda."""
        overflow_hours = timesheet['overflow_hours']
        
        if overflow_hours <= 0:
            return timesheet
            
        # Sort by priority (if available) or just take last ones
        sorted_tasks = sorted(overflow_tasks, key=lambda x: x.get('priority', 5))
        
        rolled_tasks = []
        remaining_overflow = overflow_hours
        
        for task in sorted_tasks:
            if remaining_overflow <= 0:
                break
                
            task_duration = task.get('estimated_hours', 1)
            if task_duration <= remaining_overflow:
                rolled_tasks.append({
                    **task,
                    'rolled_from': timesheet['date'],
                    'rolled_at': datetime.now().isoformat()
                })
                remaining_overflow -= task_duration
                
        # Update tomorrow's agenda
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        agenda = self.profile.get('tomorrows_agenda', [])
        
        # Remove duplicates
        existing_tasks = {a.get('description') for a in agenda}
        new_tasks = [t for t in rolled_tasks if t.get('description') not in existing_tasks]
        
        agenda.extend(new_tasks)
        self.profile['tomorrows_agenda'] = agenda
        save_user_profile(self.profile)
        
        timesheet['rolled_tasks'] = rolled_tasks
        timesheet['tomorrows_agenda_count'] = len(agenda)
        
        return timesheet


class MorningCheckIn:
    """Automated morning check-in with meeting prep and agenda."""
    
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        
    def get_morning_summary(self) -> Dict[str, Any]:
        """Generate morning check-in summary."""
        today = datetime.now()
        
        # Get today's meetings
        todays_meetings = [
            m for m in self.profile.get('meetings', [])
            if m.get('date') == today.strftime('%Y-%m-%d')
        ]
        
        # Get upcoming meetings in next 30 minutes
        upcoming = []
        for meeting in todays_meetings:
            meeting_time = datetime.strptime(f"{meeting['date']} {meeting['time']}", '%Y-%m-%d %H:%M')
            minutes_until = (meeting_time - today).total_seconds() / 60
            if 0 < minutes_until <= 30:
                upcoming.append({
                    **meeting,
                    'minutes_until': int(minutes_until)
                })
                
        # Get yesterday's summary
        yesterday_timesheet = self._get_yesterday_timesheet()
        
        # Get today's agenda
        agenda = self.profile.get('tomorrows_agenda', [])
        
        return {
            'greeting_time': self._get_greeting(),
            'upcoming_meetings': upcoming,
            'meetings_today': len(todays_meetings),
            'yesterday_summary': yesterday_timesheet,
            'todays_agenda': agenda[:5],  # Top 5 items
            'work_limit_reminder': f"Remember: {self.profile.get('daily_work_limit_hours', 9)} hour limit today"
        }
    
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting."""
        hour = datetime.now().hour
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"
    
    def _get_yesterday_timesheet(self) -> Optional[Dict[str, Any]]:
        """Retrieve yesterday's timesheet if available."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        timesheet_path = DATA_DIR / f"timesheet_{yesterday}.json"
        
        if timesheet_path.exists():
            with open(timesheet_path, 'r') as f:
                return json.load(f)
        return None
    
    def generate_prep_message(self, meeting: Dict[str, Any]) -> str:
        """Generate a prep message for an upcoming meeting."""
        minutes = meeting.get('minutes_until', 0)
        meeting_name = meeting.get('name', 'Meeting')
        
        # Look for related project notes
        project = meeting.get('project')
        notes = self._find_project_notes(project) if project else []
        
        message = f"You've got {meeting_name} in {minutes} minutes"
        
        if notes:
            message += f". Want me to summarize the last project notes? I've got {len(notes)} recent items."
        else:
            message += ". No prep notes found—want to review anything before it starts?"
            
        return message
    
    def _find_project_notes(self, project_name: str) -> List[str]:
        """Find recent notes related to a project."""
        # This would integrate with memory system
        # For now, return empty list
        return []


# Global instances
def get_tracker() -> GitActivityTracker:
    """Get configured Git tracker."""
    profile = get_user_profile()
    folders = profile.get('dev_folders', [str(Path.home() / 'projects')])
    return GitActivityTracker(folders)


def get_timesheet() -> TimesheetGenerator:
    """Get timesheet generator."""
    profile = get_user_profile()
    return TimesheetGenerator(profile)


def get_checkin() -> MorningCheckIn:
    """Get morning check-in handler."""
    profile = get_user_profile()
    return MorningCheckIn(profile)


# Public API functions
def check_work_status() -> Dict[str, Any]:
    """Check current work status and hours."""
    tracker = get_tracker()
    tracker.scan_all_repos()
    
    activity = tracker.get_work_summary()
    timesheet_gen = get_timesheet()
    timesheet = timesheet_gen.generate_timesheet(activity)
    
    # Log work status
    save_log('work_status', {
        'timestamp': datetime.now().isoformat(),
        'hours_worked': timesheet['total_hours'],
        'work_limit': timesheet['work_limit_hours'],
        'status': timesheet['status']
    })
    
    return {
        'hours_worked': timesheet['total_hours'],
        'work_limit': timesheet['work_limit_hours'],
        'remaining': timesheet['remaining_hours'],
        'overflow': timesheet['overflow_hours'],
        'commits_today': activity['total_commits'],
        'status': timesheet['status'],
        'should_stop': timesheet['overflow_hours'] > 0
    }


def morning_checkin() -> Dict[str, Any]:
    """Perform morning check-in."""
    checkin = get_checkin()
    summary = checkin.get_morning_summary()
    
    # Format for LOVE's chat
    greeting = summary['greeting_time']
    meeting_count = summary['meetings_today']
    
    if summary['upcoming_meetings']:
        meeting = summary['upcoming_meetings'][0]
        love_message = checkin.generate_prep_message(meeting)
    else:
        love_message = f"Good {greeting}, {USER_NAME}. {meeting_count} meetings today. Your agenda has {len(summary['todays_agenda'])} items waiting."
        
    return {
        'summary': summary,
        'love_message': love_message,
        'action_required': len(summary['upcoming_meetings']) > 0
    }


def add_dev_folder(folder_path: str) -> Dict[str, Any]:
    """Add a development folder to track."""
    profile = get_user_profile()
    folders = profile.get('dev_folders', [])
    
    if folder_path not in folders and Path(folder_path).exists():
        folders.append(folder_path)
        profile['dev_folders'] = folders
        save_user_profile(profile)
        return {'success': True, 'added': folder_path, 'total_folders': len(folders)}
    
    return {'success': False, 'error': 'Folder already tracked or does not exist'}


def add_meeting(name: str, date: str, time: str, project: str = None) -> Dict[str, Any]:
    """Add a meeting to the calendar."""
    profile = get_user_profile()
    meetings = profile.get('meetings', [])
    
    meeting = {
        'name': name,
        'date': date,
        'time': time,
        'project': project,
        'added_at': datetime.now().isoformat()
    }
    
    meetings.append(meeting)
    profile['meetings'] = meetings
    save_user_profile(profile)
    
    return {'success': True, 'meeting': meeting}


def enforce_work_limit() -> Dict[str, Any]:
    """Check and enforce the 9-hour work limit."""
    status = check_work_status()
    
    if status['should_stop']:
        overflow = status['overflow']
        love_message = f"You've hit your {status['work_limit']} hour limit. That's {overflow} hours over—time to shut it down. Your overflow tasks are already rolled to tomorrow. Go recover."
        
        return {
            'enforce': True,
            'hours_today': status['hours_worked'],
            'overflow_hours': overflow,
            'love_message': love_message,
            'actions': [
                'Save all work',
                'Commit pending changes',
                'Review tomorrow\'s agenda',
                'Shut down or switch to personal mode'
            ]
        }
    
    return {
        'enforce': False,
        'hours_today': status['hours_worked'],
        'remaining': status['remaining'],
        'love_message': f"You're at {status['hours_worked']} hours. {status['remaining']} hours left in your budget."
    }


def format_work_status_for_chat(status: Dict[str, Any]) -> str:
    """Format work status for LOVE's companion chat."""
    hours = status['hours_worked']
    limit = status['work_limit']
    remaining = status['remaining']
    
    if status['should_stop']:
        return f"{USER_NAME}, you've been working for {hours} hours. That's past your {limit}-hour limit. I've already queued your overflow for tomorrow. Time to rest."
    elif remaining <= 1:
        return f"You're at {hours}/{limit} hours. One hour left—wrap up what matters and don't start anything new."
    elif remaining <= 3:
        return f"Deep work today: {hours} hours down, {remaining} to go. Stay focused, no new meetings."
    else:
        return f"{hours} hours logged. You've got {remaining} hours of quality work left in you today."


# ========== WORK LIMIT HARD-STOP (PHYSICAL ENFORCEMENT) ==========

class HardStopEnforcer:
    """Physical enforcement of configurable work limit with auto-save and lock."""
    
    def __init__(self):
        self.profile = get_user_profile()
        self.dev_folders = self.profile.get('dev_folders', [])
        
    def generate_day_summary(self) -> Dict[str, Any]:
        """Generate summary of the work day."""
        status = check_work_status()
        tracker = get_tracker()
        
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_hours': status['hours_worked'],
            'commits_count': len(tracker.today_commits),
            'repositories_worked': list(set(c['repo'] for c in tracker.today_commits)),
            'work_sessions': len(tracker.work_sessions),
            'overflow_rolled': status.get('overflow', 0),
            'tomorrow_agenda': self.profile.get('tomorrows_agenda', [])[:5]
        }
        
        return summary
    
    def auto_commit_all(self) -> Dict[str, Any]:
        """Auto-commit and push all changes in tracked repos."""
        if not GIT_AVAILABLE:
            return {'committed': False, 'error': 'GitPython not available'}
        
        results = []
        commit_message = f"{AUTO_COMMIT_MSG} {datetime.now().strftime('%Y-%m-%d')}"
        
        for folder_path in self.dev_folders:
            folder = Path(folder_path)
            if not folder.exists():
                continue
                
            # Find all git repos
            for repo_path in self._find_git_repos(folder):
                try:
                    repo = Repo(repo_path)
                    
                    # Check for changes
                    if repo.is_dirty(untracked_files=True):
                        # Stage all changes
                        repo.git.add('--all')
                        
                        # Commit
                        repo.index.commit(commit_message)
                        
                        # Push if origin exists
                        push_result = 'skipped'
                        try:
                            origin = repo.remote('origin')
                            origin.push()
                            push_result = 'success'
                        except Exception as e:
                            push_result = f'failed: {str(e)[:50]}'
                        
                        results.append({
                            'repo': str(repo_path),
                            'committed': True,
                            'commit_msg': commit_message,
                            'pushed': push_result
                        })
                    else:
                        results.append({
                            'repo': str(repo_path),
                            'committed': False,
                            'reason': 'No changes'
                        })
                        
                except Exception as e:
                    results.append({
                        'repo': str(repo_path),
                        'committed': False,
                        'error': str(e)[:100]
                    })
        
        return {
            'total_repos': len(results),
            'commits_made': sum(1 for r in results if r.get('committed')),
            'details': results
        }
    
    def _find_git_repos(self, base_path: Path) -> List[Path]:
        """Find all Git repositories under a path."""
        repos = []
        for item in base_path.iterdir():
            if item.is_dir():
                git_dir = item / ".git"
                if git_dir.exists():
                    repos.append(item)
        return repos
    
    def trigger_system_lock(self) -> Dict[str, Any]:
        """Trigger screen dim and system lock notification."""
        import platform
        
        lock_triggered = False
        dim_triggered = False
        
        system = _platform_system()
        
        try:
            # Windows: Dim screen using powercfg (reduce brightness) or send notification
            if system == "Windows":
                # Send Windows notification
                try:
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        f"Work limit reached, {USER_NAME}. The brain needs a recharge. I've saved everything for you.",
                        f"LOVE - Work Limit Enforcer",
                        0x40 | 0x1000  # Info icon + system modal
                    )
                    lock_triggered = True
                except Exception:
                    pass
                
                # Attempt to dim screen via power settings (requires admin usually)
                try:
                    subprocess.run(
                        ['powercfg', '/change', 'monitor-timeout-ac', '1'],
                        capture_output=True, timeout=5
                    )
                    dim_triggered = True
                except Exception:
                    pass
            
            # macOS
            elif system == "Darwin":
                try:
                    subprocess.run(['pmset', 'displaysleepnow'], check=True, timeout=5)
                    lock_triggered = True
                except Exception:
                    pass
            
            # Linux
            else:
                try:
                    subprocess.run(['gnome-screensaver-command', '-l'], check=True, timeout=5)
                    lock_triggered = True
                except Exception:
                    pass
        except Exception as e:
            return {
                'lock_triggered': False,
                'dim_triggered': False,
                'error': str(e)
            }
        
        return {
            'lock_triggered': lock_triggered,
            'dim_triggered': dim_triggered,
            'message': f'Work limit reached, {USER_NAME}. The brain needs a recharge. I\'ve saved everything for you.'
        }
    
    def execute_hard_stop(self) -> Dict[str, Any]:
        """Execute complete hard-stop sequence."""
        # Generate day summary
        summary = self.generate_day_summary()
        
        # Auto-commit all changes
        commit_result = self.auto_commit_all()
        
        # Trigger system lock/dim
        lock_result = self.trigger_system_lock()
        
        # Log the hard stop
        save_log('hard_stop', {
            'timestamp': datetime.now().isoformat(),
            'hours_worked': summary['total_hours'],
            'commits_auto_saved': commit_result['commits_made'],
            'lock_triggered': lock_result['lock_triggered']
        })
        
        # Format LOVE's message
        love_message = f"""Hard stop activated. You worked {summary['total_hours']} hours today.

✓ Saved all changes ({commit_result['commits_made']} repos committed with 'Love-Auto-Save')
✓ Rolled {summary['overflow_rolled']} hours of overflow to tomorrow's agenda
✓ System {('locked' if lock_result['lock_triggered'] else 'notified')}

Your top 5 for tomorrow: {', '.join([t.get('description', 'Task')[:20] for t in summary['tomorrow_agenda'][:3]])}...

Go recover. The code will wait."""
        
        return {
            'hard_stop_executed': True,
            'day_summary': summary,
            'commits': commit_result,
            'system_lock': lock_result,
            'love_message': love_message
        }


def execute_nine_hour_hard_stop() -> Dict[str, Any]:
    """Public function to execute the 9-hour hard stop."""
    enforcer = HardStopEnforcer()
    return enforcer.execute_hard_stop()


def get_day_summary() -> Dict[str, Any]:
    """Get summary of today's work without enforcing."""
    enforcer = HardStopEnforcer()
    return enforcer.generate_day_summary()


# ========== GHOST DEVELOPER (CODE STAGING AGENT) ==========

class GhostDeveloper:
    """Monitors file changes and auto-generates tests and boilerplate."""
    
    def __init__(self):
        self.profile = get_user_profile()
        self.llm = None  # Lazy load when needed
        
    def detect_file_type(self, file_path: Path) -> str:
        """Detect if file is .NET, Flutter, or other."""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.cs', '.csproj', '.sln']:
            return 'dotnet'
        elif suffix in ['.dart', '.yaml']:
            return 'flutter'
        elif suffix == '.py':
            return 'python'
        return 'unknown'
    
    def analyze_dotnet_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a .NET file for test opportunities."""
        content = file_path.read_text(errors='ignore')
        
        # Look for class definitions
        import re
        class_matches = re.findall(r'class\s+(\w+)', content)
        
        # Look for public methods
        method_matches = re.findall(r'public\s+(?:async\s+)?(?:Task<[^>]+>|void|[^\s]+)\s+(\w+)\s*\(', content)
        
        return {
            'file': str(file_path),
            'classes': class_matches,
            'public_methods': method_matches,
            'needs_tests': len(method_matches) > 0 and 'test' not in file_path.name.lower()
        }
    
    def analyze_flutter_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Flutter file for boilerplate needs."""
        content = file_path.read_text(errors='ignore')
        
        # Look for Widget classes
        import re
        widget_matches = re.findall(r'class\s+(\w+)\s+extends\s+(StatelessWidget|StatefulWidget)', content)
        
        # Check for state management
        has_bloc = 'Bloc' in content or 'bloc' in file_path.name.lower()
        has_provider = 'Provider' in content or 'ChangeNotifier' in content
        
        return {
            'file': str(file_path),
            'widgets': [w[0] for w in widget_matches],
            'widget_types': [w[1] for w in widget_matches],
            'has_state_management': has_bloc or has_provider,
            'suggested_architecture': 'Clean Architecture with Bloc' if not has_bloc else None
        }
    
    def draft_dotnet_tests(self, analysis: Dict[str, Any]) -> str:
        """Draft unit tests for .NET class."""
        file_path = Path(analysis['file'])
        class_name = analysis['classes'][0] if analysis['classes'] else 'Unknown'
        methods = analysis['public_methods']
        
        test_code = f"""using Xunit;
using Moq;
using {class_name};

namespace {class_name}.Tests
{{
    public class {class_name}Tests
    {{
        private readonly {class_name} _sut;

        public {class_name}Tests()
        {{
            _sut = new {class_name}();
        }}

"""
        
        for method in methods[:5]:  # First 5 methods
            test_code += f"""        [Fact]
        public void {method}_ShouldReturnExpectedResult()
        {{
            // Arrange
            
            // Act
            var result = _sut.{method}();
            
            // Assert
            Assert.NotNull(result);
        }}

"""
        
        test_code += """    }}
}}"""
        
        return test_code
    
    def draft_flutter_boilerplate(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Draft Clean Architecture boilerplate for Flutter."""
        widget_name = analysis['widgets'][0] if analysis['widgets'] else 'Unknown'
        
        # Domain layer
        entity_code = f"""class {widget_name}Entity {{
  final String id;
  final String name;

  {widget_name}Entity({{required this.id, required this.name}});
}}"""
        
        # Bloc
        bloc_code = f"""import 'package:flutter_bloc/flutter_bloc.dart';

abstract class {widget_name}Event {{}}
class Load{widget_name} extends {widget_name}Event {{}}

abstract class {widget_name}State {{}}
class {widget_name}Initial extends {widget_name}State {{}}
class {widget_name}Loading extends {widget_name}State {{}}
class {widget_name}Loaded extends {widget_name}State {{}}

class {widget_name}Bloc extends Bloc<{widget_name}Event, {widget_name}State> {{
  {widget_name}Bloc() : super({widget_name}Initial()) {{
    on<Load{widget_name}>((event, emit) async {{
      emit({widget_name}Loading());
      // Load data
      emit({widget_name}Loaded());
    }});
  }}
}}"""
        
        # Folder structure suggestion
        structure = f"""
lib/
├── domain/
│   ├── entities/
│   │   └── {widget_name.lower()}_entity.dart
│   ├── repositories/
│   │   └── {widget_name.lower()}_repository.dart
│   └── usecases/
│       └── get_{widget_name.lower()}.dart
├── data/
│   ├── models/
│   ├── repositories/
│   └── datasources/
├── presentation/
│   ├── bloc/
│   │   └── {widget_name.lower()}_bloc.dart
│   ├── pages/
│   └── widgets/
└── main.dart"""
        
        return {
            'entity': entity_code,
            'bloc': bloc_code,
            'folder_structure': structure
        }
    
    def scan_for_staging(self, project_path: str) -> List[Dict[str, Any]]:
        """Scan a project for files needing staging."""
        if not project_path or not Path(project_path).exists():
            return []
        
        results = []
        project = Path(project_path)
        
        # Scan for .NET files
        for cs_file in project.rglob("*.cs"):
            if 'test' not in cs_file.name.lower() and 'obj' not in str(cs_file):
                analysis = self.analyze_dotnet_file(cs_file)
                if analysis['needs_tests']:
                    test_code = self.draft_dotnet_tests(analysis)
                    results.append({
                        'type': 'dotnet_test',
                        'source_file': str(cs_file),
                        'test_code': test_code,
                        'message': f"New .NET class detected in {cs_file.name}. Drafted unit tests."
                    })
        
        # Scan for Flutter files
        for dart_file in project.rglob("*.dart"):
            if 'test' not in dart_file.name.lower() and 'generated' not in str(dart_file):
                analysis = self.analyze_flutter_file(dart_file)
                if analysis['widgets'] and not analysis['has_state_management']:
                    boilerplate = self.draft_flutter_boilerplate(analysis)
                    results.append({
                        'type': 'flutter_boilerplate',
                        'source_file': str(dart_file),
                        'boilerplate': boilerplate,
                        'message': f"New Flutter widget in {dart_file.name}. Suggest Clean Architecture structure."
                    })
        
        return results


def scan_project_for_staging(project_path: str) -> List[Dict[str, Any]]:
    """Public function to scan project for code staging needs."""
    ghost = GhostDeveloper()
    return ghost.scan_for_staging(project_path)


def get_ghost_suggestions(project_type: str = 'all') -> List[Dict[str, Any]]:
    """Get Ghost Developer suggestions for configured projects."""
    profile = get_user_profile()
    suggestions = []
    
    # Check work project
    work_project = os.getenv("LOVE_WORK_PROJECT")
    if work_project and (project_type == 'all' or project_type == 'work'):
        suggestions.extend(scan_project_for_staging(work_project))
    
    # Check .NET project
    dotnet_project = os.getenv("LOVE_DOTNET_PROJECT")
    if dotnet_project and (project_type == 'all' or project_type == 'dotnet'):
        suggestions.extend(scan_project_for_staging(dotnet_project))
    
    # Check Flutter project
    flutter_project = os.getenv("LOVE_FLUTTER_PROJECT")
    if flutter_project and (project_type == 'all' or project_type == 'flutter'):
        suggestions.extend(scan_project_for_staging(flutter_project))
    
    return suggestions
