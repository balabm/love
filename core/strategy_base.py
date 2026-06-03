"""
LOVE BaseStrategy — reusable trading-strategy base class.

Provides:
  - Typed param accessors (get_int_param, get_float_param)
  - Built-in technical indicators (SMA, EMA, RSI, ATR, Bollinger, etc.)
  - Stateful signal tracking
  - Validation helpers

Generated strategies can subclass BaseStrategy or use the helpers injected
by StrategyExecutor when running raw code strings.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseStrategy(ABC):
    """Base class for LLM-generated trading strategies."""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {}
        self._state: Dict[str, Any] = {}

    # ── Param Accessors ───────────────────────────────────────────────────────

    def get_param(self, key: str, default: float = 0.0) -> float:
        """Return a parameter as float."""
        v = self.params.get(key, default)
        try:
            return float(v)
        except (TypeError, ValueError):
            return float(default)

    def get_int_param(self, key: str, default: int = 10) -> int:
        """Return a parameter as int — safe for list indexing.

        Handles the common case where JSON/evolution produces 14.0 instead of 14.
        """
        v = self.params.get(key, default)
        try:
            f = float(v)
            return int(f)
        except (TypeError, ValueError):
            return int(default)

    def get_float_param(self, key: str, default: float = 0.0) -> float:
        """Return a parameter as float."""
        return self.get_param(key, default)

    # ── State Helpers ───────────────────────────────────────────────────────

    def set_state(self, key: str, value: Any):
        self._state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    # ── Validation ────────────────────────────────────────────────────────────

    def validate(self, candles: List[List]) -> bool:
        """Check that we have enough candles for the strategy."""
        return len(candles) >= self.get_int_param("min_bars", 10)

    # ── Built-in Indicators ─────────────────────────────────────────────────

    @staticmethod
    def sma(data: List[float], period: int) -> float:
        """Simple Moving Average."""
        if len(data) < period:
            return data[-1] if data else 0.0
        return sum(data[-period:]) / period

    @staticmethod
    def ema(data: List[float], period: int) -> float:
        """Exponential Moving Average."""
        if len(data) < period:
            return data[-1] if data else 0.0
        k = 2.0 / (period + 1)
        ema_val = sum(data[:period]) / period
        for price in data[period:]:
            ema_val = price * k + ema_val * (1 - k)
        return ema_val

    @staticmethod
    def rsi(data: List[float], period: int = 14) -> float:
        """Relative Strength Index (0-100)."""
        if len(data) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(data)):
            change = data[i] - data[i - 1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1 + rs))

    @staticmethod
    def atr(candles: List[List], period: int = 14) -> float:
        """Average True Range."""
        if len(candles) < period + 1:
            return 0.0
        trs = []
        for i in range(1, len(candles)):
            high = float(candles[i][2])
            low = float(candles[i][3])
            prev_close = float(candles[i - 1][4])
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs[-period:]) / period

    @staticmethod
    def bollinger(data: List[float], period: int = 20, std: float = 2.0) -> tuple:
        """Bollinger Bands: (middle, upper, lower)."""
        if len(data) < period:
            mid = data[-1] if data else 0.0
            return mid, mid, mid
        mid = sum(data[-period:]) / period
        variance = sum((x - mid) ** 2 for x in data[-period:]) / period
        band = (variance ** 0.5) * std
        return mid, mid + band, mid - band

    @staticmethod
    def volume_profile(candles: List[List], bins: int = 10) -> List[float]:
        """Return volume-weighted price distribution."""
        if not candles:
            return []
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]
        min_p = min(closes)
        max_p = max(closes)
        if max_p == min_p:
            return [sum(volumes)]
        bucket_size = (max_p - min_p) / bins
        profile = [0.0] * bins
        for c, v in zip(closes, volumes):
            idx = min(int((c - min_p) / bucket_size), bins - 1)
            profile[idx] += v
        return profile

    @staticmethod
    def crossover(series_a: List[float], series_b: List[float]) -> Optional[bool]:
        """Detect if series_a crossed above series_b on the latest bar.

        Returns True for bullish crossover, False for bearish, None if no cross.
        """
        if len(series_a) < 2 or len(series_b) < 2:
            return None
        prev_a = series_a[-2]
        prev_b = series_b[-2]
        curr_a = series_a[-1]
        curr_b = series_b[-1]
        if prev_a <= prev_b and curr_a > curr_b:
            return True
        if prev_a >= prev_b and curr_a < curr_b:
            return False
        return None

    # ── Abstract Interface ────────────────────────────────────────────────────

    @abstractmethod
    def on_data(self, candles: List[List]) -> str:
        """Return exactly 'BUY', 'SELL', or 'HOLD'."""
        ...
