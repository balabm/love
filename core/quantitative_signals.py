"""
LOVE Quantitative Signals Engine v3 — Advanced ML Signal Ensemble

Produces BUY/SELL/HOLD signals from multiple orthogonal alpha sources:
  - Momentum (RSI, MACD, ADX slope)
  - Mean Reversion (Bollinger %B, z-score, VWAP deviation)
  - Volume Profile (OBV divergence, volume spike confirmation)
  - Statistical (hurst exponent, cointegration residual)
  - ML Micro-Ensemble (ensemble of simple classifiers on OHLCV features)

All signal generators return a float in [-1, 1] where -1 = strong sell, 1 = strong buy.
The ensemble aggregates with configurable weights and produces a final signal + confidence.
"""

import math
import json
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Optional heavy math ──────────────────────────────────────────────────────
import statistics

DATA_DIR = Path(__file__).parent.parent / "data"
SIGNAL_LOG = DATA_DIR / "quant_signals.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Helper math ──────────────────────────────────────────────────────────────


def _sma(data: List[float], period: int) -> float:
    if len(data) < period:
        return sum(data) / max(len(data), 1)
    return sum(data[-period:]) / period


def _ema(data: List[float], period: int) -> List[float]:
    k = 2 / (period + 1)
    emas = [sum(data[:period]) / period]
    for price in data[period:]:
        emas.append(price * k + emas[-1] * (1 - k))
    return emas


def _std(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    try:
        return statistics.stdev(data)
    except statistics.StatisticsError:
        return 0.0


def _zscore(val: float, mean: float, stdev: float) -> float:
    return (val - mean) / stdev if stdev > 0 else 0.0


def _linear_slope(y: List[float]) -> float:
    """Simple OLS slope (x = 0..n-1)."""
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
    """Estimate Hurst exponent via rescaled range (R/S) analysis."""
    if len(prices) < max_lag * 2:
        return 0.5
    lags = range(2, min(max_lag + 1, len(prices) // 2))
    tau = []
    for lag in lags:
        # Price differences over lag periods
        pp = [prices[i] - prices[i - lag] for i in range(lag, len(prices), lag)]
        if len(pp) < 2:
            continue
        m = sum(pp) / len(pp)
        s = math.sqrt(sum((x - m) ** 2 for x in pp) / len(pp)) + 1e-9
        r = max(pp) - min(pp)
        tau.append(math.log(r / s))
    if len(tau) < 2:
        return 0.5
    # Simplified: slope of log(tau) vs log(lag)
    xs = [math.log(l) for l in lags[:len(tau)]]
    n = len(xs)
    sx = sum(xs)
    sy = sum(tau)
    sxx = sum(x * x for x in xs)
    sxy = sum(xs[i] * tau[i] for i in range(n))
    den = n * sxx - sx * sx
    return (n * sxy - sx * sy) / den if den else 0.5


# ═════════════════════════════════════════════════════════════════════════════
#  SIGNAL GENERATORS
# ═════════════════════════════════════════════════════════════════════════════

class SignalGenerator:
    """Base class for a quantitative signal source."""

    name = "base"

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        """Return (signal, confidence) where signal in [-1, 1] and confidence in [0, 1]."""
        return 0.0, 0.0


class MomentumSignal(SignalGenerator):
    """RSI + MACD + ADX slope momentum composite."""

    name = "momentum"

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        if len(candles) < 30:
            return 0.0, 0.0
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]

        # RSI
        period = 14
        gains, losses = [], []
        for i in range(1, period + 1):
            diff = closes[-i] - closes[-(i + 1)]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        avg_gain = sum(gains) / period if gains else 0.0
        avg_loss = sum(losses) / period if losses else 0.0
        avg_loss = max(avg_loss, 1e-9)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_sig = ((rsi - 50) / 50)  # normalize to [-1, 1]

        # MACD
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(ema26))]
        signal_line = _ema(macd_line, 9)
        macd_sig = 0.0
        if len(macd_line) >= 2 and len(signal_line) >= 1:
            hist = macd_line[-1] - signal_line[-1]
            prev_hist = macd_line[-2] - signal_line[-2] if len(signal_line) > 1 else hist
            denom = (abs(prev_hist) + 1e-9)
            macd_sig = max(-1, min(1, (hist - prev_hist) / denom))

        # ADX slope (proxy via high-low range)
        highs = [float(c[2]) for c in candles[-20:]]
        lows = [float(c[3]) for c in candles[-20:]]
        atr = [h - l for h, l in zip(highs, lows)]
        atr_slope = _linear_slope(atr)
        adx_sig = max(-1, min(1, atr_slope / max(sum(atr) / len(atr), 1e-9) * 10))

        # Volume confirmation
        vol_sma = _sma(volumes, 20)
        vol_now = volumes[-1]
        vol_sig = max(-1, min(1, (vol_now - vol_sma) / (vol_sma + 1e-9)))  # volume spike direction

        composite = (rsi_sig * 0.35 + macd_sig * 0.35 + adx_sig * 0.15 + vol_sig * 0.15)
        confidence = min(1.0, abs(rsi_sig) * 0.4 + abs(macd_sig) * 0.4 + abs(adx_sig) * 0.2)
        return composite, confidence


class MeanReversionSignal(SignalGenerator):
    """Bollinger %B + z-score + VWAP deviation."""

    name = "mean_reversion"

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        if len(candles) < 20:
            return 0.0, 0.0
        closes = [float(c[4]) for c in candles]
        current = closes[-1]

        # Bollinger Bands
        sma20 = _sma(closes, 20)
        std20 = _std(closes[-20:])
        upper = sma20 + 2 * std20
        lower = sma20 - 2 * std20
        band_range = upper - lower if upper > lower else 1e-9
        pct_b = (current - lower) / band_range
        bb_sig = (0.5 - pct_b) * 2  # overbought -> sell, oversold -> buy

        # Z-score over 20
        z = _zscore(current, sma20, std20)
        z_sig = max(-1, min(1, -z / 3))  # inverse z-score (mean reversion)

        # VWAP deviation
        vwaps = []
        for c in candles[-20:]:
            tp = (float(c[2]) + float(c[3]) + float(c[4])) / 3
            vol = float(c[5])
            vwaps.append((tp, vol))
        total_pv = sum(p * v for p, v in vwaps)
        total_v = sum(v for _, v in vwaps) + 1e-9
        vwap = total_pv / total_v
        vwap_dev = (current - vwap) / vwap if vwap else 0
        vwap_sig = max(-1, min(1, -vwap_dev * 10))

        composite = (bb_sig * 0.5 + z_sig * 0.3 + vwap_sig * 0.2)
        confidence = min(1.0, abs(bb_sig) * 0.5 + abs(z_sig) * 0.3 + abs(vwap_sig) * 0.2)
        return composite, confidence


class VolumeProfileSignal(SignalGenerator):
    """OBV divergence + volume spike confirmation."""

    name = "volume_profile"

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        if len(candles) < 20:
            return 0.0, 0.0
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]

        # OBV
        obv = [0.0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i - 1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i - 1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])

        # OBV slope vs price slope divergence
        price_slope = _linear_slope(closes[-20:])
        obv_slope = _linear_slope(obv[-20:])
        obv_norm = obv_slope / (abs(sum(obv[-20:]) / 20) + 1e-9)
        price_norm = price_slope / (abs(sum(closes[-20:]) / 20) + 1e-9)
        divergence = obv_norm - price_norm
        div_sig = max(-1, min(1, divergence * 50))

        # Volume spike
        vol_sma20 = _sma(volumes, 20)
        vol_ratio = volumes[-1] / (vol_sma20 + 1e-9)
        vol_sig = max(-1, min(1, (vol_ratio - 1) * 2))

        # Trend-aligned volume (volume should confirm trend direction)
        trend = 1 if closes[-1] > closes[-5] else -1
        aligned = trend * vol_sig > 0
        align_bonus = 0.2 if aligned else -0.2

        composite = (div_sig * 0.6 + vol_sig * 0.4) + align_bonus
        composite = max(-1, min(1, composite))
        confidence = min(1.0, abs(div_sig) * 0.5 + abs(vol_sig) * 0.5)
        return composite, confidence


class StatisticalSignal(SignalGenerator):
    """Hurst exponent + autocorrelation lag-1 + variance ratio."""

    name = "statistical"

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        if len(candles) < 50:
            return 0.0, 0.0
        closes = [float(c[4]) for c in candles]
        returns = [(closes[i] - closes[i - 1]) / (closes[i - 1] + 1e-9) for i in range(1, len(closes))]

        # Hurst exponent
        hurst = _hurst_exponent(closes)
        # H > 0.5 => trending (momentum), H < 0.5 => mean-reverting
        hurst_sig = (hurst - 0.5) * 2  # [-1, 1] approx

        # Autocorrelation lag-1 of returns
        if len(returns) > 1:
            m = sum(returns) / len(returns)
            num = sum((returns[i] - m) * (returns[i - 1] - m) for i in range(1, len(returns)))
            den = sum((r - m) ** 2 for r in returns) + 1e-9
            acf = num / den
        else:
            acf = 0.0
        acf_sig = max(-1, min(1, -acf * 5))  # negative autocorr -> mean reversion

        # Variance ratio (short-term vs long-term volatility)
        var_short = _std(returns[-10:]) ** 2
        var_long = _std(returns[-30:]) ** 2
        vr = var_short / (var_long + 1e-9)
        vr_sig = max(-1, min(1, (vr - 1) * 2))

        composite = (hurst_sig * 0.4 + acf_sig * 0.4 + vr_sig * 0.2)
        confidence = min(1.0, 0.3 + abs(hurst_sig) * 0.3 + abs(acf_sig) * 0.2 + abs(vr_sig) * 0.2)
        return composite, confidence


class MicroMLSignal(SignalGenerator):
    """
    A tiny ensemble of rule-based + statistical 'micro classifiers'.
    No external ML library required — everything is pure Python.
    """

    name = "micro_ml"

    def _features(self, candles: List[List]) -> List[float]:
        """Extract a small feature vector from OHLCV."""
        if len(candles) < 30:
            return []
        closes = [float(c[4]) for c in candles]
        volumes = [float(c[5]) for c in candles]
        highs = [float(c[2]) for c in candles[-20:]]
        lows = [float(c[3]) for c in candles[-20:]]
        returns = [(closes[i] - closes[i - 1]) / (closes[i - 1] + 1e-9) for i in range(1, len(closes))]

        features = [
            (closes[-1] - _sma(closes, 20)) / (_sma(closes, 20) + 1e-9),  # price vs SMA
            (closes[-1] - _sma(closes, 50)) / (_sma(closes, 50) + 1e-9) if len(closes) >= 50 else 0,
            sum(returns[-5:]) / (abs(sum(returns[-20:])) + 1e-9),  # short vs long return
            _std(returns[-10:]) / (abs(_sma(returns, 10)) + 1e-9),  # volatility / mean return
            (volumes[-1] - _sma(volumes, 20)) / (_sma(volumes, 20) + 1e-9),  # volume anomaly
            (max(highs) - min(lows)) / (closes[-20] + 1e-9),  # 20-period range
            1 if closes[-1] > max(closes[-10:-1]) else -1 if closes[-1] < min(closes[-10:-1]) else 0,  # breakout
            sum(1 for r in returns[-10:] if r > 0) / 10.0,  # up-day ratio
        ]
        return features

    def compute(self, candles: List[List]) -> Tuple[float, float]:
        feats = self._features(candles)
        if not feats:
            return 0.0, 0.0

        # Model 1: linear scoring (weights learned conceptually)
        weights = [2.0, 1.5, 3.0, -1.0, 1.0, 0.5, 2.5, 1.0]
        linear_score = sum(f * w for f, w in zip(feats, weights)) / sum(abs(w) for w in weights)
        linear_score = max(-1, min(1, linear_score))

        # Model 2: momentum tree
        if feats[0] > 0.02 and feats[2] > 0.5 and feats[6] > 0:
            tree_score = 0.8
        elif feats[0] < -0.02 and feats[2] < -0.5 and feats[6] < 0:
            tree_score = -0.8
        else:
            tree_score = 0.0

        # Model 3: contrarian (inverse of linear with dampening)
        contrarian_score = -linear_score * 0.5

        # Ensemble
        ensemble = (linear_score * 0.5 + tree_score * 0.35 + contrarian_score * 0.15)
        # Confidence = disagreement inverse (when models agree, confidence high)
        disagreement = abs(linear_score - tree_score) + abs(linear_score - contrarian_score)
        confidence = max(0.0, 1.0 - disagreement / 3)
        return ensemble, confidence


# ═════════════════════════════════════════════════════════════════════════════
#  QUANTITATIVE SIGNALS ENGINE
# ═════════════════════════════════════════════════════════════════════════════

DEFAULT_WEIGHTS = {
    "momentum": 0.25,
    "mean_reversion": 0.20,
    "volume_profile": 0.20,
    "statistical": 0.15,
    "micro_ml": 0.20,
}


class QuantitativeSignalsEngine:
    """
    Aggregates multiple signal generators into a unified alpha score.
    Also tracks signal history for performance analysis.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, weights: Dict[str, float] = None):
        if self._initialized:
            return
        self._initialized = True
        self.generators: Dict[str, SignalGenerator] = {
            "momentum": MomentumSignal(),
            "mean_reversion": MeanReversionSignal(),
            "volume_profile": VolumeProfileSignal(),
            "statistical": StatisticalSignal(),
            "micro_ml": MicroMLSignal(),
        }
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self._history: deque = deque(maxlen=500)
        self._lock = threading.RLock()

    # ── Core API ─────────────────────────────────────────────────────────────

    def analyze(self, candles: List[List], symbol: str = "", regime_hint: str = None) -> Dict[str, Any]:
        """
        Run all signal generators and return ensemble signal.
        regime_hint: 'trending', 'ranging', 'volatile' — can boost/de-weight generators.
        """
        if len(candles) < 50:
            return {"signal": "HOLD", "score": 0.0, "confidence": 0.0, "details": {}, "reason": "insufficient data"}

        results = {}
        weighted_sum = 0.0
        total_weight = 0.0
        confidences = {}

        # Adjust weights by regime
        active_weights = dict(self.weights)
        if regime_hint == "trending":
            active_weights["momentum"] *= 1.5
            active_weights["mean_reversion"] *= 0.5
        elif regime_hint == "ranging":
            active_weights["momentum"] *= 0.5
            active_weights["mean_reversion"] *= 1.5
            active_weights["statistical"] *= 1.3
        elif regime_hint == "volatile":
            active_weights["volume_profile"] *= 1.4
            active_weights["micro_ml"] *= 1.2
            active_weights["momentum"] *= 0.7

        for name, gen in self.generators.items():
            sig, conf = gen.compute(candles)
            w = active_weights.get(name, 0.0)
            results[name] = {"signal": round(sig, 4), "confidence": round(conf, 4)}
            weighted_sum += sig * w * conf
            total_weight += w * conf
            confidences[name] = conf

        ensemble_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        ensemble_conf = min(1.0, sum(confidences.values()) / len(confidences)) if confidences else 0.0

        # Convert to discrete signal
        if ensemble_score > 0.25:
            discrete = "BUY"
        elif ensemble_score < -0.25:
            discrete = "SELL"
        else:
            discrete = "HOLD"

        report = {
            "signal": discrete,
            "score": round(ensemble_score, 4),
            "confidence": round(ensemble_conf, 4),
            "details": results,
            "weights_used": active_weights,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "candles_used": len(candles),
        }

        with self._lock:
            self._history.append(report)
            try:
                with open(SIGNAL_LOG, "a") as f:
                    f.write(json.dumps(report, default=str) + "\n")
            except Exception:
                pass

        return report

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(self._history)[-limit:]

    def set_weights(self, weights: Dict[str, float]):
        self.weights = {k: v for k, v in weights.items() if k in self.generators}

    def get_weights(self) -> Dict[str, float]:
        return dict(self.weights)


# ── Convenience ───────────────────────────────────────────────────────────────

_engine: Optional[QuantitativeSignalsEngine] = None


def get_quant_signals() -> QuantitativeSignalsEngine:
    global _engine
    if _engine is None:
        _engine = QuantitativeSignalsEngine()
    return _engine
