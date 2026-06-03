"""
LOVE Risk Manager — Position Sizing, Kelly Criterion, VaR, Drawdown Protection

Core functions:
  - kelly_sizing: fractional Kelly position sizing from backtest / recent trades
  - value_at_risk: historical simulation VaR (also parametric)
  - max_drawdown_protection: circuit breakers, dynamic leverage reduction
  - position_size: unified sizing that respects capital, risk, and drawdown
  - correlation_adjustment: reduce size when adding correlated assets
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
RISK_LOG = DATA_DIR / "risk_manager.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _std(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    try:
        return statistics.stdev(data)
    except statistics.StatisticsError:
        return 0.0


def _percentile(data: List[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    n = len(s)
    idx = (n - 1) * p
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return s[lo]
    return s[lo] * (hi - idx) + s[hi] * (idx - lo)


class RiskManager:
    """
    Unified risk management for the LOVE trading engine.
    Tracks capital, drawdown, VaR, and produces safe position sizes.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, initial_capital: float = 10000.0, max_risk_per_trade: float = 0.02,
                 max_drawdown_limit: float = 0.15, kelly_fraction: float = 0.25):
        if self._initialized:
            return
        self._initialized = True
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_drawdown_limit = max_drawdown_limit
        self.kelly_fraction = kelly_fraction
        self.peak_capital = initial_capital
        self._equity_curve: deque = deque([initial_capital], maxlen=10000)
        self._returns: deque = deque(maxlen=1000)
        self._trade_pnl: deque = deque(maxlen=500)
        self._lock = threading.RLock()

    def update_capital(self, new_capital: float):
        with self._lock:
            old = self.current_capital
            self.current_capital = new_capital
            ret = (new_capital - old) / old if old else 0
            self._returns.append(ret)
            self._equity_curve.append(new_capital)
            if new_capital > self.peak_capital:
                self.peak_capital = new_capital
            self._log_state()

    def record_trade_pnl(self, pnl: float, capital_at_risk: float):
        with self._lock:
            self._trade_pnl.append({"pnl": pnl, "capital_at_risk": capital_at_risk,
                                      "timestamp": datetime.now().isoformat()})

    def kelly_sizing(self, win_rate: float = None, avg_win: float = None,
                     avg_loss: float = None, recent_trades: int = 50) -> float:
        """Return fractional Kelly position size as fraction of capital."""
        with self._lock:
            trades = list(self._trade_pnl)[-recent_trades:]
        if not trades:
            return self.max_risk_per_trade

        if win_rate is None or avg_win is None or avg_loss is None:
            wins = [t["pnl"] for t in trades if t["pnl"] > 0]
            losses = [t["pnl"] for t in trades if t["pnl"] < 0]
            win_rate = len(wins) / len(trades) if trades else 0.5
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = abs(sum(losses) / len(losses)) if losses else 1e-9

        if avg_loss == 0:
            avg_loss = 1e-9
        kelly = win_rate - ((1 - win_rate) / (avg_win / avg_loss)) if avg_win > 0 else 0
        kelly = max(0, kelly)
        return min(kelly * self.kelly_fraction, self.max_risk_per_trade)

    def var_historical(self, confidence: float = 0.95, lookback: int = 100) -> float:
        """Historical simulation VaR as fraction of current capital."""
        with self._lock:
            returns = list(self._returns)[-lookback:]
        if not returns:
            return self.max_risk_per_trade
        var_return = _percentile(returns, 1 - confidence)
        return abs(var_return)

    def var_parametric(self, confidence: float = 0.95, lookback: int = 100) -> float:
        """Parametric (Gaussian) VaR as fraction of current capital."""
        with self._lock:
            returns = list(self._returns)[-lookback:]
        if not returns:
            return self.max_risk_per_trade
        mu = sum(returns) / len(returns)
        sigma = _std(returns)
        z = {0.9: 1.28, 0.95: 1.645, 0.99: 2.33}.get(confidence, 1.645)
        var = -(mu - z * sigma)
        return max(var, 0)

    def current_drawdown(self) -> float:
        with self._lock:
            return (self.peak_capital - self.current_capital) / self.peak_capital if self.peak_capital > 0 else 0

    def drawdown_penalty(self) -> float:
        """Multiplier in [0, 1] that reduces position size as drawdown grows."""
        dd = self.current_drawdown()
        if dd >= self.max_drawdown_limit:
            return 0.0
        penalty = 1.0 - (dd / self.max_drawdown_limit) ** 2
        return max(0.0, min(1.0, penalty))

    def is_circuit_breaker(self) -> Tuple[bool, str]:
        dd = self.current_drawdown()
        if dd >= self.max_drawdown_limit:
            return True, f"Circuit breaker: drawdown {dd*100:.1f}% >= limit {self.max_drawdown_limit*100:.1f}%"
        with self._lock:
            recent = list(self._trade_pnl)[-5:]
        if len(recent) >= 5 and all(t["pnl"] < 0 for t in recent):
            return True, "Circuit breaker: 5 consecutive losing trades"
        return False, ""

    def position_size(self, entry_price: float, stop_loss_price: float,
                      symbol: str = "", correlation_adjustment: float = 1.0) -> Dict[str, Any]:
        """
        Unified position sizing.
        S = min(Kelly, RiskBased, VaRBased) * DrawdownPenalty * CorrelationAdj
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            return {"quantity": 0, "reason": "invalid prices"}

        risk_per_unit = abs(entry_price - stop_loss_price) / entry_price if entry_price else 1
        if risk_per_unit == 0:
            return {"quantity": 0, "reason": "stop loss at entry price"}

        # 1. Kelly-based size
        kelly = self.kelly_sizing()

        # 2. Risk-based: don't lose more than max_risk_per_trade of capital
        risk_based = self.max_risk_per_trade / risk_per_unit

        # 3. VaR-based: don't exceed daily VaR budget
        var = self.var_historical(confidence=0.95)
        var_budget = max(var * 2, self.max_risk_per_trade)  # 2x daily VaR as trade limit
        var_based = var_budget / risk_per_unit

        raw_size = min(kelly, risk_based, var_based)

        # Apply drawdown penalty
        dd_penalty = self.drawdown_penalty()
        sized = raw_size * dd_penalty

        # Apply correlation adjustment
        sized *= max(0.1, min(1.0, correlation_adjustment))

        # Cap at reasonable max
        max_position = 0.5  # never more than 50% of capital in one trade
        sized = min(sized, max_position)

        # Convert to quantity
        notional = sized * self.current_capital
        quantity = notional / entry_price if entry_price > 0 else 0

        result = {
            "quantity": round(quantity, 6),
            "notional": round(notional, 2),
            "sized_fraction": round(sized, 4),
            "kelly_fraction": round(kelly, 4),
            "risk_based": round(risk_based, 4),
            "var_based": round(var_based, 4),
            "drawdown_penalty": round(dd_penalty, 4),
            "correlation_adjustment": round(correlation_adjustment, 4),
            "stop_loss_pct": round(risk_per_unit * 100, 2),
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
        }

        with self._lock:
            self._log_state(result)
        return result

    def get_status(self) -> Dict[str, Any]:
        dd = self.current_drawdown()
        cb, cb_reason = self.is_circuit_breaker()
        with self._lock:
            trades = list(self._trade_pnl)
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] < 0]
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "peak_capital": self.peak_capital,
            "drawdown_pct": round(dd * 100, 2),
            "circuit_breaker": cb,
            "circuit_reason": cb_reason,
            "total_trades": len(trades),
            "win_rate": round(len(wins) / len(trades) * 100, 1) if trades else 0,
            "var_95_pct": round(self.var_historical(0.95) * 100, 2),
            "kelly_fraction": round(self.kelly_sizing(), 4),
            "max_risk_per_trade_pct": round(self.max_risk_per_trade * 100, 2),
        }

    def _log_state(self, extra: Dict = None):
        try:
            entry = {"timestamp": datetime.now().isoformat(), "capital": self.current_capital,
                     "drawdown": self.current_drawdown()}
            if extra:
                entry.update(extra)
            with open(RISK_LOG, "a") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            pass


def get_risk_manager() -> RiskManager:
    return RiskManager()
