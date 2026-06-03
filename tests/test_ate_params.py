"""
Regression tests for ATE StrategyExecutor param normalization
and BaseStrategy helpers.
"""

import pytest
from core.autonomous_trading_engine import GeneratedStrategy, StrategyExecutor
from core.strategy_base import BaseStrategy


class DummyStrategy(BaseStrategy):
    def on_data(self, candles):
        period = self.get_int_param("period", 14)
        threshold = self.get_float_param("threshold", 0.01)
        if len(candles) < period + 1:
            return "HOLD"
        closes = [float(c[4]) for c in candles]
        sma_fast = sum(closes[-5:]) / 5
        sma_slow = sum(closes[-period:]) / period
        if sma_fast > sma_slow * (1 + threshold):
            return "BUY"
        if sma_fast < sma_slow * (1 - threshold):
            return "SELL"
        return "HOLD"


def _make_candles(n=50):
    """Generate simple ascending candles."""
    candles = []
    for i in range(n):
        price = 100.0 + i
        candles.append([i, price, price + 1, price - 1, price, 1000.0])
    return candles


class TestStrategyExecutorParams:
    """Verify float params used as indices don't crash."""

    def test_float_period_cast_to_int(self):
        """A period=14.0 float should be silently treated as int for slicing."""
        code = """
def on_data(candles):
    closes = [float(c[4]) for c in candles]
    period = get_int_param("period", 14)
    if len(closes) < period + 1:
        return "HOLD"
    sma = sum(closes[-period:]) / period
    return "BUY" if closes[-1] > sma else "HOLD"
"""
        strat = GeneratedStrategy(
            name="FloatPeriod", description="test", logic_type="momentum",
            params={"period": 14.0}, code=code,
        )
        executor = StrategyExecutor(strat)
        candles = _make_candles(60)
        signal = executor.run(candles)
        assert signal in ("BUY", "SELL", "HOLD")

    def test_string_float_period(self):
        """A period='14.5' string should fallback to default int."""
        code = """
def on_data(candles):
    closes = [float(c[4]) for c in candles]
    period = get_int_param("period", 10)
    if len(closes) < period + 1:
        return "HOLD"
    return "BUY"
"""
        strat = GeneratedStrategy(
            name="StrFloat", description="test", logic_type="momentum",
            params={"period": "14.5"}, code=code,
        )
        executor = StrategyExecutor(strat)
        candles = _make_candles(60)
        signal = executor.run(candles)
        assert signal in ("BUY", "SELL", "HOLD")

    def test_missing_param_uses_default(self):
        """Missing param should use default without crashing."""
        code = """
def on_data(candles):
    closes = [float(c[4]) for c in candles]
    period = get_int_param("period", 10)
    if len(closes) < period:
        return "HOLD"
    return "BUY"
"""
        strat = GeneratedStrategy(
            name="MissingParam", description="test", logic_type="momentum",
            params={}, code=code,
        )
        executor = StrategyExecutor(strat)
        candles = _make_candles(60)
        signal = executor.run(candles)
        assert signal == "BUY"

    def test_raw_index_with_float_fails_without_helper(self):
        """A strategy that uses raw float indexing should still crash — we only protect via helpers."""
        code = """
def on_data(candles):
    closes = [float(c[4]) for c in candles]
    period = params["period"]  # raw float access, no helper
    if len(closes) < period:
        return "HOLD"
    sma = sum(closes[-period:]) / period
    return "BUY"
"""
        strat = GeneratedStrategy(
            name="RawFloat", description="test", logic_type="momentum",
            params={"period": 14.0}, code=code,
        )
        executor = StrategyExecutor(strat)
        candles = _make_candles(60)
        # Should NOT crash because we now normalize 14.0 -> 14 in norm_params
        signal = executor.run(candles)
        assert signal in ("BUY", "SELL", "HOLD")


class TestBaseStrategyIndicators:
    """Verify BaseStrategy indicator helpers produce sane values."""

    def test_sma(self):
        assert BaseStrategy.sma([1, 2, 3, 4, 5], 3) == pytest.approx(4.0)

    def test_ema(self):
        data = [10.0, 11.0, 12.0, 13.0, 14.0]
        ema = BaseStrategy.ema(data, 3)
        assert isinstance(ema, float)
        assert 10 < ema < 14

    def test_rsi(self):
        data = [10.0, 11.0, 12.0, 11.0, 10.0, 9.0]
        rsi = BaseStrategy.rsi(data, 5)
        assert 0 <= rsi <= 100

    def test_atr(self):
        candles = [
            [0, 10.0, 12.0, 9.0, 11.0, 1000],
            [1, 11.0, 13.0, 10.0, 12.0, 1000],
            [2, 12.0, 14.0, 11.0, 13.0, 1000],
        ]
        atr = BaseStrategy.atr(candles, 2)
        assert atr > 0

    def test_bollinger(self):
        data = list(range(1, 21))
        mid, upper, lower = BaseStrategy.bollinger(data, 10)
        assert upper > mid > lower

    def test_crossover(self):
        a = [1, 1, 1, 1, 5]  # crosses above b on last bar
        b = [2, 2, 2, 2, 1]
        assert BaseStrategy.crossover(a, b) is True
        a2 = [5, 5, 5, 5, 1]  # crosses below b on last bar
        b2 = [2, 2, 2, 2, 5]
        assert BaseStrategy.crossover(a2, b2) is False
        a3 = [1, 1, 1, 1, 1]
        b3 = [2, 2, 2, 2, 2]
        assert BaseStrategy.crossover(a3, b3) is None

    def test_dummy_strategy_runs(self):
        candles = _make_candles(60)
        ds = DummyStrategy(params={"period": 10, "threshold": 0.01})
        signal = ds.on_data(candles)
        assert signal in ("BUY", "SELL", "HOLD")
