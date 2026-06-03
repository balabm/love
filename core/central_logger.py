"""
LOVE Central Logging System — The Unified Nervous System for Logs

This is LOVE's central logging infrastructure. All modules should use this
system for consistent, structured logging that integrates with the neural bus.

Features:
- Singleton pattern for consistent configuration
- Structured JSON logging for neural bus integration
- Automatic log rotation by size and time
- Multiple log levels and outputs (file, console, neural bus)
- Module-specific loggers with hierarchical naming
- Thread-safe operations
- Log filtering and search capabilities
- Real-time log streaming via neural bus

Usage:
    from core.central_logger import get_logger
    logger = get_logger("module_name")
    logger.info("Event occurred", extra={"context": "additional_data"})
"""

import json
import logging
import logging.handlers
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque

# ─── Configuration ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file configuration
MAIN_LOG_FILE = LOG_DIR / "love_system.log"
ERROR_LOG_FILE = LOG_DIR / "love_errors.log"
NEURAL_LOG_FILE = LOG_DIR / "love_neural.log"
DEBUG_LOG_FILE = LOG_DIR / "love_debug.log"

# Rotation settings
MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT = 5  # Keep 5 backup files

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Neural bus integration
NEURAL_BUS_AVAILABLE = False
_neural_bus_instance = None


# ─── Log Levels ────────────────────────────────────────────────────────────────

class LogLevel(str, Enum):
    """Extended log levels for LOVE."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    ALERT = "ALERT"  # For system-wide alerts
    EMERGENCY = "EMERGENCY"  # For critical system failures


# ─── Structured Log Entry ─────────────────────────────────────────────────────

@dataclass
class LogEntry:
    """A structured log entry for neural bus transmission."""
    timestamp: str
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line: int
    thread_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    stack_trace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─── Custom JSON Formatter ────────────────────────────────────────────────────

class WindowsSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """RotatingFileHandler that silently skips rotation when the file is locked (Windows multi-process)."""

    def rotate(self, source, dest):
        """Override rotate to use os.replace and silently skip on Windows lock."""
        try:
            # os.replace works even when dest exists (unlike os.rename on Windows)
            os.replace(source, dest)
        except (PermissionError, OSError):
            # File locked by another process (OneDrive, another Python process, etc.)
            # Skip rotation — the log will keep appending to the current file.
            pass

    def doRollover(self):
        try:
            super().doRollover()
        except (PermissionError, OSError):
            # If rotation fails mid-way, ensure the stream is reopened so logging continues
            if not self.delay and self.stream is None:
                try:
                    self.stream = self._open()
                except Exception:
                    pass

    def emit(self, record):
        """Override emit to silently skip records when the file is locked (Windows)."""
        try:
            super().emit(record)
        except (PermissionError, OSError):
            # File locked by another process — skip this record rather than crashing
            pass


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON for neural bus integration."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            thread_id=str(record.thread),
            context=getattr(record, 'context', {}),
            exception=self._format_exception(record),
            stack_trace=self._format_stack_trace(record)
        )
        return json.dumps(log_entry.to_dict())
    
    def _format_exception(self, record: logging.LogRecord) -> Optional[str]:
        """Format exception information if present."""
        if record.exc_info:
            return self.formatException(record.exc_info)
        return None
    
    def _format_stack_trace(self, record: logging.LogRecord) -> Optional[str]:
        """Format stack trace if present."""
        if record.stack_info:
            return self.formatStack(record.stack_info)
        return None


# ─── Neural Bus Handler ───────────────────────────────────────────────────────

class NeuralBusHandler(logging.Handler):
    """Custom logging handler that publishes to neural bus."""
    
    def __init__(self):
        super().__init__()
        self._bus = None
        self._connected = False
        self._connect_to_neural_bus()
    
    def _connect_to_neural_bus(self):
        """Connect to neural bus for log streaming."""
        global _neural_bus_instance, NEURAL_BUS_AVAILABLE
        try:
            from core.neural_bus import get_neural_bus, EventDomain, EventPriority
            _neural_bus_instance = get_neural_bus()
            NEURAL_BUS_AVAILABLE = True
            self._bus = _neural_bus_instance
            self._connected = True
        except Exception as e:
            self._connected = False
            print(f"[CentralLogger] Neural bus unavailable: {e}")
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record to neural bus."""
        if not self._connected or not self._bus:
            return
        
        try:
            # Only publish WARNING and above to neural bus to avoid noise
            if record.levelno < logging.WARNING:
                return
            
            # Format as JSON
            formatter = JSONFormatter()
            json_message = formatter.format(record)
            log_data = json.loads(json_message)
            
            # Import here to avoid circular dependency
            from core.neural_bus import EventDomain, EventPriority
            
            # Map log levels to event priorities
            priority_map = {
                logging.WARNING: EventPriority.LOW,
                logging.ERROR: EventPriority.NORMAL,
                logging.CRITICAL: EventPriority.HIGH,
            }
            
            # Publish to neural bus
            self._bus.publish(
                domain=EventDomain.SYSTEM,
                event_type="log_entry",
                payload=log_data,
                priority=priority_map.get(record.levelno, EventPriority.LOW),
                source_module=record.name
            )
            
        except Exception as e:
            # Don't use logging here to avoid infinite recursion
            print(f"[CentralLogger] Failed to publish to neural bus: {e}")


# ─── Central Logger Manager ────────────────────────────────────────────────────

class CentralLoggerManager:
    """
    Singleton manager for LOVE's central logging system.
    
    This ensures consistent logging configuration across all modules
    and provides a single point of control for log management.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._log_history: deque = deque(maxlen=1000)  # Keep last 1000 log entries in memory
        self._log_lock = threading.RLock()
        self._neural_bus_handler: Optional[NeuralBusHandler] = None
        
        # Configure root logger
        self._configure_root_logger()
        
        # Setup neural bus handler
        self._setup_neural_bus_handler()
    
    def _configure_root_logger(self):
        """Configure the root logger with handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture all levels
        
        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Main log file with rotation (delay=True reduces file-lock contention on Windows)
        main_handler = WindowsSafeRotatingFileHandler(
            MAIN_LOG_FILE,
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8',
            delay=True
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        main_handler.setFormatter(main_formatter)
        root_logger.addHandler(main_handler)
        
        # Error log file (ERROR and above only)
        error_handler = WindowsSafeRotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8',
            delay=True
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # Debug log file (DEBUG and TRACE only)
        debug_handler = WindowsSafeRotatingFileHandler(
            DEBUG_LOG_FILE,
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8',
            delay=True
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        debug_handler.setFormatter(debug_formatter)
        root_logger.addHandler(debug_handler)
    
    def _setup_neural_bus_handler(self):
        """Setup neural bus handler for real-time log streaming."""
        try:
            self._neural_bus_handler = NeuralBusHandler()
            # Only add if neural bus is available
            if self._neural_bus_handler._connected:
                root_logger = logging.getLogger()
                root_logger.addHandler(self._neural_bus_handler)
                print("[CentralLogger] Neural bus logging enabled")
        except Exception as e:
            print(f"[CentralLogger] Neural bus handler setup failed: {e}")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger with the specified name.
        
        Args:
            name: Logger name (typically __name__ or module name)
            
        Returns:
            Configured logger instance
        """
        with self._log_lock:
            if name not in self._loggers:
                logger = logging.getLogger(name)
                logger.setLevel(logging.DEBUG)
                logger.propagate = True  # Propagate to root logger
                self._loggers[name] = logger
            return self._loggers[name]
    
    def add_log_to_history(self, log_entry: LogEntry):
        """Add log entry to in-memory history."""
        with self._log_lock:
            self._log_history.append(log_entry)
    
    def get_log_history(self, limit: int = 100) -> List[LogEntry]:
        """Get recent log entries from history."""
        with self._log_lock:
            return list(self._log_history)[-limit:]
    
    def search_logs(self, query: str, level: Optional[str] = None, 
                   module: Optional[str] = None, limit: int = 100) -> List[LogEntry]:
        """
        Search logs by query, level, and/or module.
        
        Args:
            query: Search string to match in messages
            level: Filter by log level
            module: Filter by module name
            limit: Maximum number of results
            
        Returns:
            List of matching log entries
        """
        with self._log_lock:
            results = []
            for entry in reversed(self._log_history):
                if limit and len(results) >= limit:
                    break
                
                # Apply filters
                if query and query.lower() not in entry.message.lower():
                    continue
                if level and entry.level != level:
                    continue
                if module and module.lower() not in entry.module.lower():
                    continue
                
                results.append(entry)
            
            return results
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        with self._log_lock:
            level_counts = defaultdict(int)
            module_counts = defaultdict(int)
            
            for entry in self._log_history:
                level_counts[entry.level] += 1
                module_counts[entry.module] += 1
            
            return {
                "total_logs": len(self._log_history),
                "level_counts": dict(level_counts),
                "module_counts": dict(module_counts),
                "log_files": {
                    "main": str(MAIN_LOG_FILE),
                    "error": str(ERROR_LOG_FILE),
                    "debug": str(DEBUG_LOG_FILE),
                    "neural": str(NEURAL_LOG_FILE) if NEURAL_BUS_AVAILABLE else None
                },
                "neural_bus_enabled": NEURAL_BUS_AVAILABLE
            }


# ─── Global Instance ───────────────────────────────────────────────────────────

_central_logger_manager: Optional[CentralLoggerManager] = None
_manager_lock = threading.Lock()


def get_central_logger_manager() -> CentralLoggerManager:
    """Get the singleton central logger manager instance."""
    global _central_logger_manager
    if _central_logger_manager is None:
        with _manager_lock:
            if _central_logger_manager is None:
                _central_logger_manager = CentralLoggerManager()
    return _central_logger_manager


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the specified module.
    
    This is the main entry point for modules to get a logger.
    
    Usage:
        from core.central_logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    manager = get_central_logger_manager()
    return manager.get_logger(name)


def log_structured(level: str, logger_name: str, message: str, 
                  context: Optional[Dict[str, Any]] = None, **kwargs):
    """
    Log a structured message with additional context.
    
    Args:
        level: Log level (INFO, WARNING, ERROR, etc.)
        logger_name: Name of the logger
        message: Log message
        context: Additional context dictionary
        **kwargs: Additional fields to include in log entry
    """
    logger = get_logger(logger_name)
    
    # Add context to extra fields
    extra = {'context': context or {}}
    extra.update(kwargs)
    
    # Map level string to logging constant
    level_map = {
        'TRACE': logging.DEBUG - 5,
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
        'ALERT': logging.ERROR + 5,
        'EMERGENCY': logging.CRITICAL + 5,
    }
    
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # Add custom level if needed
    if log_level not in [logging.DEBUG, logging.INFO, logging.WARNING, 
                        logging.ERROR, logging.CRITICAL]:
        logging.addLevelName(log_level, level.upper())
    
    logger.log(log_level, message, extra=extra)


# ─── Convenience Functions ─────────────────────────────────────────────────────

def log_error(logger_name: str, message: str, exception: Optional[Exception] = None,
              context: Optional[Dict[str, Any]] = None):
    """Log an error with optional exception and context."""
    logger = get_logger(logger_name)
    if exception:
        logger.error(message, exc_info=exception, extra={'context': context or {}})
    else:
        logger.error(message, extra={'context': context or {}})


def log_warning(logger_name: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Log a warning with context."""
    logger = get_logger(logger_name)
    logger.warning(message, extra={'context': context or {}})


def log_info(logger_name: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Log an info message with context."""
    logger = get_logger(logger_name)
    logger.info(message, extra={'context': context or {}})


def log_debug(logger_name: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Log a debug message with context."""
    logger = get_logger(logger_name)
    logger.debug(message, extra={'context': context or {}})


# ─── Initialization ───────────────────────────────────────────────────────────

# Initialize central logger on import
get_central_logger_manager()

print(f"[CentralLogger] Initialized. Log directory: {LOG_DIR}")
print(f"[CentralLogger] Main log: {MAIN_LOG_FILE}")
print(f"[CentralLogger] Error log: {ERROR_LOG_FILE}")
print(f"[CentralLogger] Debug log: {DEBUG_LOG_FILE}")
