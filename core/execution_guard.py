"""
Execution Guard — No Silent Failures

Enforces the "No Silent Failures" law from the AGI directive.
All errors must be wrapped in logging.error(e, exc_info=True) and piped
to logs/love_system.log so the Self-Healing daemon can patch them.

Usage:
    from core.execution_guard import guard, log_error

    @guard
def my_function():
        ...

    try:
        risky()
    except Exception as e:
        log_error(e, module="my_module", context={"action": "trade"})
"""

import logging
import functools
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure logs directory exists
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "love_system.log"

# Configure the love_system logger
_love_logger = logging.getLogger("love_system")
_love_logger.setLevel(logging.DEBUG)

# File handler for love_system.log
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(LOG_FILE) for h in _love_logger.handlers):
    fh = logging.FileHandler(LOG_FILE, mode="a")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(module)s] %(message)s"
    )
    fh.setFormatter(formatter)
    _love_logger.addHandler(fh)

# Also ensure root logging streams errors if no other handler exists
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def log_error(
    exception: Exception,
    module: str = "unknown",
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
) -> None:
    """
    Log an exception to love_system.log with full traceback and structured context.
    Never silently swallow errors.
    """
    ctx = context or {}
    ctx_str = " | ".join(f"{k}={v}" for k, v in ctx.items()) if ctx else ""
    tb = traceback.format_exc()

    msg = f"[{module}] {ctx_str}\nException: {exception}\n{tb}"

    if level == "critical":
        _love_logger.critical(msg)
    elif level == "warning":
        _love_logger.warning(msg)
    else:
        _love_logger.error(msg)

    # Also push to console for visibility during development
    print(f"[ExecutionGuard] {level.upper()} in {module}: {exception}")


def guard(func):
    """
    Decorator that wraps a function so any uncaught exception is logged
    rather than silently swallowed.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(
                e,
                module=func.__module__,
                context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
            )
            raise
    return wrapper


def guard_async(func):
    """Async variant of the @guard decorator."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            log_error(
                e,
                module=func.__module__,
                context={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)},
            )
            raise
    return wrapper


def safe_call(func, *args, default=None, log_ctx=None, **kwargs):
    """
    Call a function safely: log any exception and return `default`.
    Use ONLY for non-critical paths where continuation is acceptable.
    Still logs the failure.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(
            e,
            module=getattr(func, "__module__", "unknown"),
            context={"function": getattr(func, "__name__", "<lambda>"), **(log_ctx or {})},
            level="warning",
        )
        return default
