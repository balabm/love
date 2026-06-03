"""
LOVE Market Regime Detector — Trend / Ranging / Volatile classification

Uses multiple orthogonal indicators to classify current market regime:
  - ADX slope (trend strength)
  - Bollinger Band width expansion (volatility)
  - ATR vs historical (volatility regime)
  - Price-MA alignment (trend direction)
  - Hurst exponent (mean-reverting vs trending)

Output: regime label + confidence + expected duration estimate
"""

import math
import json
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import statistics

DATA_DIR = Path(__file__).parent.parent / "data"
REGIME_LOG = DATA_DIR / "market_regime.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _sma(data: List[float], period: int) -> float:
    if len(data) < period:
        return sum(data) / max(len(data), 1)
    return sum(data[-period:]) / period


def _std(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    try:
        return statistics.stdev(data)
    except statistics.StatisticsError:
        return 0.0


def _ema(data: List[float], period: int) -> List[float]:
    k = 2 / (period + 1)
    emas = [sum(data[:period]) / period]
    for price in data[period:]:
        emas.append(price * k + emas[-1] * (1 - k))
    return emas


def _linear_slope(y: List[float]) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    sx = sum(range(n))
    sy = sum(y)
    sxx = sum(i * i for i in range(n))
    sxy = sum(i * y[i] for i in range(n))
    den = n * sxx - sx * sx
    if den == 0:
        return 0.0
    return (n * sxy - sx * sy) / den


def _hurst_exponent(prices: List[float], max_lag: int = 20) -> float:
    if len(prices) < max_lag * 2:
        return 0.5
    lags = range(2, min(max_lag + 1, len(prices) // 2))
    tau = []
    for lag in lags:
        pp = [prices[i] - prices[i - lag] for i in range(lag, len(prices), lag)]
        if len(pp) < 2:
            continue
        m = sum(pp) / len(pp)
        s = math.sqrt(sum((x - m) ** 2 for x in pp) / len(pp)) + 1e-9
        r = max(pp) - min(pp)
        tau.append(math.log(r / s))
    if len(tau) < 2:
        return 0.5
    xs = [math.log(l) for l in lags[:len(tau)]]
    n = len(xs)
    sx = sum(xs)
    sy = sum(tau)
    sxx = sum(x * x for x in xs)
    sxy = sum(xs[i] * tau[i] for i in range(n))
    den = n * sxx - sx * sx
    return (n * sxy - sx * sy) / den if den else 0.5


class MarketRegimeDetector:
    """
    Classifies market regime into: TRENDING, RANGING, VOLATILE, or UNKNOWN.
    Provides confidence score and regime duration estimate.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, lookback: int = 50):
        if self._initialized:
            return
        self._initialized = True
        self.lookback = lookback
        self._history: deque = deque(maxlen=500)
        self._lock = threading.RLock()

    # ── Core detection ─────────────────────────────────────────────────────

    def detect(self, candles: List[List], symbol: str = "") -> Dict[str, Any]:
        """
        candles: [[timestamp, open, high, low, close, volume], ...] newest last
        Returns: { regime, confidence, duration_estimate, indicators, timestamp, symbol }
        """
        if len(candles) < self.lookback:
            return {"regime": "UNKNOWN", "confidence": 0.0, "reason": "insufficient data"}

        closes = [float(c[4]) for c in candles]
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        volumes = [float(c[5]) for c in candles]

        # 1. ADX proxy (using high-low range slope)
        atr = [h - l for h, l in zip(highs[-20:], lows[-20:])]
        atr_slope = _linear_slope(atr)
        atr_mean = sum(atr) / len(atr) if atr else 1e-9
        adx_proxy = atr_slope / atr_mean * 20 if atr_mean else 0

        # 2. Bollinger Band width
        sma20 = _sma(closes, 20)
        std20 = _std(closes[-20:])
        bb_width = (std20 / sma20 * 100) if sma20 > 0 else 0
        bb_width_sma = _sma([bb_width], 1)  # single point

        # 3. ATR vs historical
        atr_now = sum(atr[-5:]) / 5 if len(atr) >= 5 else atr_mean
        atr_historical = sum(atr) / len(atr) if atr else 1e-9
        atr_ratio = atr_now / atr_historical if atr_historical > 0 else 1.0

        # 4. Price-MA alignment
        sma50 = _sma(closes, 50) if len(closes) >= 50 else _sma(closes, len(closes))
        price_vs_sma = (closes[-1] - sma50) / sma50 if sma50 else 0

        # 5. Hurst exponent
        hurst = _hurst_exponent(closes)

        # 6. Volume confirmation
        vol_sma20 = _sma(volumes, 20)
        vol_ratio = volumes[-1] / vol_sma20 if vol_sma20 > 0 else 1.0

        # ── Classification logic ─────────────────────────────────────────
        trending_score = 0.0
        ranging_score = 0.0
        volatile_score = 0.0

        # ADX proxy -> trending
        if adx_proxy > 0.5:
            trending_score += 0.3
        elif adx_proxy < -0.3:
            ranging_score += 0.2

        # BB width -> volatile if expanding
        if bb_width > 5.0 or atr_ratio > 1.5:
            volatile_score += 0.35
        elif bb_width < 2.0 and atr_ratio < 0.8:
            ranging_score += 0.25

        # Price-MA -> trending if far from MA
        if abs(price_vs_sma) > 0.03:
            trending_score += 0.25
        elif abs(price_vs_sma) < 0.01:
            ranging_score += 0.25

        # Hurst -> trending if > 0.55, mean-reverting if < 0.45
        if hurst > 0.55:
            trending_score += 0.2
        elif hurst < 0.45:
            ranging_score += 0.2

        # Volume -> volatile if spiking
        if vol_ratio > 2.0:
            volatile_score += 0.2
        elif vol_ratio < 0.5:
            ranging_score += 0.1

        # Normalize
        total = trending_score + ranging_score + volatile_score
        if total == 0:
            total = 1e-9
        t_norm = trending_score / total
        r_norm = ranging_score / total
        v_norm = volatile_score / total

        # Pick winner
        scores = {"TRENDING": t_norm, "RANGING": r_norm, "VOLATILE": v_norm}
        regime = max(scores, key=scores.get)
        confidence = scores[regime]

        # Duration estimate: how long has current regime persisted?
        duration = self._estimate_duration(regime)

        result = {
            "regime": regime,
            "confidence": round(confidence, 4),
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "duration_estimate_hours": duration,
            "indicators": {
                "adx_proxy": round(adx_proxy, 4),
                "bb_width_pct": round(bb_width, 4),
                "atr_ratio": round(atr_ratio, 4),
                "price_vs_sma_pct": round(price_vs_sma * 100, 4),
                "hurst": round(hurst, 4),
                "volume_ratio": round(vol_ratio, 4),
            },
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
        }

        with self._lock:
            self._history.append(result)
            try:
                with open(REGIME_LOG, "a") as f:
                    f.write(json.dumps(result, default=str) + "\n")
            except Exception:
                pass

        return result

    def _estimate_duration(self, current_regime: str) -> int:
        """Estimate how long the current regime has been in place (hours, roughly)."""
        with self._lock:
            history = list(self._history)
        if not history:
            return 0
        # Count consecutive same-regime entries at the end
        count = 0
        for h in reversed(history):
            if h.get("regime") == current_regime:
                count += 1
            else:
                break
        # Assume each detection call represents ~1 hour of data (1h candles)
        return count

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(self._history)[-limit:]

    def current_regime(self) -> Optional[Dict]:
        with self._lock:
            return self._history[-1] if self._history else None


def get_regime_detector() -> MarketRegimeDetector:
    return MarketRegimeDetector()
