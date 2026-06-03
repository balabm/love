"""
LOVE Sentiment Analyzer — Fear & Greed, On-chain, Social Sentiment

Aggregates multiple sentiment sources into a unified sentiment score:
  - Fear & Greed Index proxy (volatility + momentum + volume + dominance)
  - On-chain signals (exchange inflow/outflow proxy from price action)
  - Social sentiment (proxy from volume anomalies + momentum divergence)
  - VIX-like fear proxy from recent volatility

Output: sentiment score in [-1, 1] with confidence and component breakdown.
"""

import math
import json
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import statistics

DATA_DIR = Path(__file__).parent.parent / "data"
SENTIMENT_LOG = DATA_DIR / "sentiment.jsonl"
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


def _max_drawdown(prices: List[float]) -> float:
    peak = prices[0]
    max_dd = 0.0
    for p in prices:
        if p > peak:
            peak = p
        dd = (p - peak) / peak if peak else 0
        if dd < max_dd:
            max_dd = dd
    return max_dd


class SentimentAnalyzer:
    """
    Produces a composite sentiment score for a market from OHLCV data.
    No external APIs required — everything derived from price/volume.
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
        self._history: deque = deque(maxlen=500)
        self._lock = threading.RLock()

    # ── Component analyzers ──────────────────────────────────────────────────

    def _fear_greed_proxy(self, closes: List[float], volumes: List[float]) -> float:
        """
        Proxy for Fear & Greed Index using:
          - Volatility (price swings = fear)
          - Momentum (strong momentum = greed)
          - Volume (high volume with drops = fear)
        Returns score in [-1, 1] where -1 = extreme fear, 1 = extreme greed
        """
        if len(closes) < 20:
            return 0.0

        returns = [(closes[i] - closes[i-1]) / (closes[i-1] + 1e-9) for i in range(1, len(closes))]
        vol = _std(returns[-20:]) * math.sqrt(365)  # annualized-ish

        # Volatility component: high vol = fear
        vol_score = max(-1, min(1, 1 - vol * 10))  # vol=0.2 -> score=0, vol=0.1 -> score=0

        # Momentum component: strong positive = greed, strong negative = fear
        mom = (closes[-1] - closes[-20]) / closes[-20] if closes[-20] > 0 else 0
        mom_score = max(-1, min(1, mom * 20))

        # Volume component: volume spike with price drop = fear
        vol_sma = _sma(volumes, 20)
        vol_ratio = volumes[-1] / (vol_sma + 1e-9)
        price_trend = 1 if closes[-1] > closes[-5] else -1
        if vol_ratio > 1.5 and price_trend < 0:
            volume_score = -0.5  # fear
        elif vol_ratio > 1.5 and price_trend > 0:
            volume_score = 0.3   # greed
        else:
            volume_score = 0.0

        composite = vol_score * 0.4 + mom_score * 0.4 + volume_score * 0.2
        return max(-1, min(1, composite))

    def _onchain_proxy(self, closes: List[float], volumes: List[float]) -> float:
        """
        On-chain sentiment proxy:
          - Large volume inflows to exchanges (proxy: volume spikes + price decline)
          - Exchange outflows (proxy: volume spikes + price rise)
          - Network activity (proxy: sustained volume)
        Returns: positive = bullish on-chain, negative = bearish
        """
        if len(closes) < 10:
            return 0.0

        vol_sma = _sma(volumes, 10)
        vol_spike = volumes[-1] / (vol_sma + 1e-9)
        price_change = (closes[-1] - closes[-2]) / closes[-2] if closes[-2] > 0 else 0

        # Inflow proxy: volume spike + price drop = selling pressure
        if vol_spike > 1.5 and price_change < -0.02:
            return -0.6
        # Outflow proxy: volume spike + price rise = buying pressure
        elif vol_spike > 1.5 and price_change > 0.02:
            return 0.6

        # Sustained volume trend
        vol_trend = _sma(volumes[-5:], 5) / (_sma(volumes[-20:], 20) + 1e-9)
        price_trend = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] > 0 else 0

        if vol_trend > 1.2 and price_trend > 0:
            return 0.3
        elif vol_trend > 1.2 and price_trend < 0:
            return -0.3
        return 0.0

    def _social_proxy(self, closes: List[float], volumes: List[float]) -> float:
        """
        Social sentiment proxy from volume-momentum divergence:
          - High volume + momentum = positive social buzz
          - Volume divergence (price up, volume down) = fading interest
        """
        if len(closes) < 10:
            return 0.0

        price_mom = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] > 0 else 0
        vol_mom = (volumes[-1] - _sma(volumes, 5)) / (_sma(volumes, 5) + 1e-9)

        # Align volume with price momentum
        if price_mom > 0.01 and vol_mom > 0.2:
            return 0.5
        elif price_mom < -0.01 and vol_mom > 0.2:
            return -0.5
        elif price_mom > 0 and vol_mom < -0.1:
            return -0.3  # divergence
        elif price_mom < 0 and vol_mom < -0.1:
            return 0.1   # declining interest on decline (less bearish)
        return 0.0

    def _vix_proxy(self, closes: List[float]) -> float:
        """VIX-like fear proxy from recent volatility."""
        if len(closes) < 20:
            return 0.0
        returns = [(closes[i] - closes[i-1]) / (closes[i-1] + 1e-9) for i in range(1, len(closes))]
        vol = _std(returns[-20:]) * math.sqrt(365)
        # Map vol to fear: higher vol = more fear (negative sentiment)
        fear = min(1.0, vol * 5)  # vol=0.2 -> fear=1.0
        return -fear  # negative = fear

    # ── Core API ───────────────────────────────────────────────────────────

    def analyze(self, candles: List[List], symbol: str = "") -> Dict[str, Any]:
        """
        candles: [[timestamp, open, high, low, close, volume], ...]
        Returns composite sentiment with component breakdown.
        """
        if len(candles) < 30:
            return {"sentiment": 0.0, "confidence": 0.0, "regime": "NEUTRAL", "reason": "insufficient data"}

        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]

        fng = self._fear_greed_proxy(closes, volumes)
        onchain = self._onchain_proxy(closes, volumes)
        social = self._social_proxy(closes, volumes)
        vix = self._vix_proxy(closes)

        # Weighted ensemble
        weights = {"fear_greed": 0.35, "onchain": 0.25, "social": 0.20, "vix": 0.20}
        composite = (fng * weights["fear_greed"] +
                     onchain * weights["onchain"] +
                     social * weights["social"] +
                     vix * weights["vix"])

        # Confidence = how aligned the components are
        components = [fng, onchain, social, vix]
        signs = [1 if c > 0.1 else (-1 if c < -0.1 else 0) for c in components]
        non_neutral = [s for s in signs if s != 0]
        if non_neutral:
            agreement = sum(1 for s in non_neutral if s == non_neutral[0]) / len(non_neutral)
            confidence = 0.3 + agreement * 0.7
        else:
            confidence = 0.2

        # Regime label
        if composite > 0.4:
            regime = "GREED"
        elif composite > 0.1:
            regime = "OPTIMISTIC"
        elif composite < -0.4:
            regime = "FEAR"
        elif composite < -0.1:
            regime = "PESSIMISTIC"
        else:
            regime = "NEUTRAL"

        result = {
            "sentiment": round(composite, 4),
            "confidence": round(confidence, 4),
            "regime": regime,
            "components": {
                "fear_greed": round(fng, 4),
                "onchain": round(onchain, 4),
                "social": round(social, 4),
                "vix_proxy": round(vix, 4),
            },
            "weights": weights,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
        }

        with self._lock:
            self._history.append(result)
            try:
                with open(SENTIMENT_LOG, "a") as f:
                    f.write(json.dumps(result, default=str) + "\n")
            except Exception:
                pass

        return result

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(self._history)[-limit:]

    def current_sentiment(self) -> Optional[Dict]:
        with self._lock:
            return self._history[-1] if self._history else None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()
