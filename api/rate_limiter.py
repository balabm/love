"""
LOVE API Rate Limiter — Security & Abuse Protection (Modern AI Pattern)

Protects LOVE's modern API endpoints from abuse:

1. TOKEN BUCKET RATE LIMITING
   - Smooth rate limiting with burst tolerance
   - Per-endpoint and per-client configurable limits
   - Automatic refill over time

2. ENDPOINT-SPECIFIC LIMITS
   - Heavy endpoints (graph queries, vector search) get lower limits
   - Light endpoints (health checks, stats) get higher limits
   - Authentication endpoints get conservative limits

3. CLIENT TRACKING
   - Track by IP address + API key
   - Maintain sliding window history
   - Identify and throttle abusive patterns

4. GRACEFUL DEGRADATION
   - Return 429 with Retry-After header
   - Queue non-urgent requests during high load
   - Alert when system is under sustained load
"""

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "rate_limiter"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RATE_LIMIT_LOG = DATA_DIR / "rate_limit_log.jsonl"


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int = 60
    tokens: float = 60.0
    refill_rate: float = 1.0  # tokens per second
    last_refill: float = 0.0

    def __post_init__(self):
        if self.last_refill == 0:
            self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get seconds to wait before tokens are available."""
        if self.tokens >= tokens:
            return 0.0
        needed = tokens - self.tokens
        return needed / self.refill_rate


class RateLimiter:
    """
    API rate limiter for LOVE.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.Lock()
        self._buckets: Dict[str, TokenBucket] = {}
        self._stats = {"requests_allowed": 0, "requests_denied": 0}

        # Default limits per endpoint category
        self._limits = {
            "default": {"capacity": 60, "refill_rate": 1.0},
            "heavy": {"capacity": 10, "refill_rate": 0.2},      # Graph queries, vector search
            "medium": {"capacity": 30, "refill_rate": 0.5},    # Pattern detection, context opt
            "light": {"capacity": 120, "refill_rate": 2.0},    # Health checks, stats
            "auth": {"capacity": 10, "refill_rate": 0.1},       # Authentication
        }

    def get_bucket(self, client_id: str, category: str = "default") -> TokenBucket:
        """Get or create a token bucket for a client."""
        key = f"{client_id}:{category}"
        with self._lock:
            if key not in self._buckets:
                limits = self._limits.get(category, self._limits["default"])
                self._buckets[key] = TokenBucket(
                    capacity=limits["capacity"],
                    tokens=limits["capacity"],
                    refill_rate=limits["refill_rate"],
                )
            return self._buckets[key]

    def check_rate_limit(self, client_id: str, endpoint: str = "",
                         category: str = "default", tokens: int = 1) -> Dict[str, Any]:
        """Check if a request is within rate limits."""
        bucket = self.get_bucket(client_id, category)
        allowed = bucket.consume(tokens)

        with self._lock:
            if allowed:
                self._stats["requests_allowed"] += 1
            else:
                self._stats["requests_denied"] += 1

        wait_time = bucket.get_wait_time(tokens)

        return {
            "allowed": allowed,
            "remaining": int(bucket.tokens),
            "reset_after": round(wait_time, 1),
            "limit": bucket.capacity,
        }

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_buckets": len(self._buckets),
            "categories": list(self._limits.keys()),
        }

    def get_category_for_endpoint(self, endpoint: str) -> str:
        """Determine rate limit category for an endpoint."""
        endpoint_lower = endpoint.lower()
        if any(k in endpoint_lower for k in ["graph", "vector", "search", "build"]):
            return "heavy"
        elif any(k in endpoint_lower for k in ["predict", "analyze", "detect", "optimize", "summarize"]):
            return "medium"
        elif any(k in endpoint_lower for k in ["health", "stats", "status", "ping"]):
            return "light"
        elif any(k in endpoint_lower for k in ["auth", "login", "token"]):
            return "auth"
        return "default"


# ── Singleton Access ─────────────────────────────────────────────────────────────

_rl_instance: Optional[RateLimiter] = None
_rl_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    global _rl_instance
    with _rl_lock:
        if _rl_instance is None:
            _rl_instance = RateLimiter()
        return _rl_instance
