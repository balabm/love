"""
Test suite for Wave 25+ quantitative finance modules.
"""
import sys
import math
sys.path.insert(0, ".")

# ── Helper: generate synthetic candles ───────────────────────────────────────

def make_candles(n=100, trend="up"):
    """Generate synthetic OHLCV candles."""
    candles = []
    price = 30000.0
    for i in range(n):
        if trend == "up":
            price *= 1.001
        elif trend == "down":
            price *= 0.999
        else:
            price += (i % 2 - 0.5) * 50
        o = price - 10
        c = price + 5
        h = c + 20
        l = o - 20
        v = 1000 + (i % 10) * 100
        candles.append([i, o, h, l, c, v])
    return candles


# ── 1. quantitative_signals ────────────────────────────────────────────────

def test_quant_signals():
    from core.quantitative_signals import get_quant_signals
    qs = get_quant_signals()
    candles = make_candles(100, "up")
    r = qs.analyze(candles, "TEST")
    assert "signal" in r
    assert r["signal"] in ("BUY", "SELL", "HOLD")
    assert -1 <= r["score"] <= 1
    assert 0 <= r["confidence"] <= 1
    assert len(r["details"]) == 5
    print("  quantitative_signals OK")


def test_quant_regime_weighting():
    from core.quantitative_signals import get_quant_signals
    qs = get_quant_signals()
    candles = make_candles(100, "up")
    r_trend = qs.analyze(candles, "TEST", regime_hint="trending")
    r_range = qs.analyze(candles, "TEST", regime_hint="ranging")
    # Trending should boost momentum weight
    assert r_trend["weights_used"]["momentum"] >= r_range["weights_used"]["momentum"]
    print("  regime weighting OK")


# ── 2. risk_manager ────────────────────────────────────────────────────────

def test_risk_manager():
    from core.risk_manager import get_risk_manager
    rm = get_risk_manager()
    rm.update_capital(11000)
    status = rm.get_status()
    assert status["current_capital"] == 11000
    assert status["drawdown_pct"] >= 0

    sizing = rm.position_size(30000, 29000, "BTC")
    assert sizing["quantity"] > 0
    assert sizing["stop_loss_pct"] > 0
    assert sizing["drawdown_penalty"] <= 1.0

    # Circuit breaker at 0 drawdown should be off
    cb, reason = rm.is_circuit_breaker()
    assert cb is False
    print("  risk_manager OK")


# ── 3. market_regime_detector ──────────────────────────────────────────────

def test_regime_detector():
    from core.market_regime_detector import get_regime_detector
    rd = get_regime_detector()
    candles = make_candles(100, "up")
    r = rd.detect(candles, "TEST")
    assert r["regime"] in ("TRENDING", "RANGING", "VOLATILE", "UNKNOWN")
    assert 0 <= r["confidence"] <= 1
    assert "indicators" in r
    print("  market_regime_detector OK")


# ── 4. sentiment_analyzer ──────────────────────────────────────────────────

def test_sentiment_analyzer():
    from core.sentiment_analyzer import get_sentiment_analyzer
    sa = get_sentiment_analyzer()
    candles = make_candles(100, "up")
    r = sa.analyze(candles, "TEST")
    assert -1 <= r["sentiment"] <= 1
    assert 0 <= r["confidence"] <= 1
    assert r["regime"] in ("GREED", "OPTIMISTIC", "NEUTRAL", "PESSIMISTIC", "FEAR")
    assert len(r["components"]) == 4
    print("  sentiment_analyzer OK")


# ── 5. portfolio_optimizer ─────────────────────────────────────────────────

def test_portfolio_optimizer():
    from core.portfolio_optimizer import get_portfolio_optimizer
    po = get_portfolio_optimizer()
    returns = {
        "BTC": [0.01, -0.005, 0.02, 0.01, -0.01, 0.015, 0.005, -0.008, 0.012, 0.003],
        "ETH": [0.008, -0.003, 0.015, 0.012, -0.008, 0.01, 0.003, -0.005, 0.009, 0.004],
    }
    r = po.optimize(returns, method="sharpe")
    assert "weights" in r
    assert abs(sum(r["weights"].values()) - 1.0) < 0.01
    assert r["sharpe"] >= 0
    print("  portfolio_optimizer OK")


# ── 6. finance_guardian integration ─────────────────────────────────────────

def test_finance_guardian_integration():
    # Import only — avoid singleton init side effects
    from core.finance_guardian import FinanceGuardian
    assert hasattr(FinanceGuardian, "analyze_signals")
    assert hasattr(FinanceGuardian, "get_market_regime")
    assert hasattr(FinanceGuardian, "get_sentiment")
    assert hasattr(FinanceGuardian, "get_risk_status")
    assert hasattr(FinanceGuardian, "optimize_portfolio")
    assert hasattr(FinanceGuardian, "sized_trade")
    assert hasattr(FinanceGuardian, "update_risk_capital")
    assert hasattr(FinanceGuardian, "record_trade_pnl")
    print("  finance_guardian integration OK")


# ── 7. autonomous_trading_engine integration ───────────────────────────────

def test_autonomous_trading_engine_integration():
    from core.autonomous_trading_engine import AutonomousTradingEngine
    assert hasattr(AutonomousTradingEngine, "_generate_strategy")
    assert hasattr(AutonomousTradingEngine, "_auto_paper_trade")
    print("  autonomous_trading_engine integration OK")


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running Wave 25+ quantitative module tests...")
    test_quant_signals()
    test_quant_regime_weighting()
    test_risk_manager()
    test_regime_detector()
    test_sentiment_analyzer()
    test_portfolio_optimizer()
    test_finance_guardian_integration()
    test_autonomous_trading_engine_integration()
    print("\nAll tests passed.")
