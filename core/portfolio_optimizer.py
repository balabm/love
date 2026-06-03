"""
LOVE Portfolio Optimizer — Mean-Variance, Sharpe Max, Risk Parity

No heavy dependencies — pure Python with numpy-like matrix ops via lists.
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
OPT_LOG = DATA_DIR / "portfolio_optimizer.jsonl"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _mean(data: List[float]) -> float:
    return sum(data) / len(data) if data else 0.0


def _std(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    try:
        return statistics.stdev(data)
    except statistics.StatisticsError:
        return 0.0


def _covariance(x: List[float], y: List[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx, my = _mean(x), _mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (len(x) - 1)


def _mat_vec_mul(mat: List[List[float]], vec: List[float]) -> List[float]:
    return [sum(row[j] * vec[j] for j in range(len(vec))) for row in mat]


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class PortfolioOptimizer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, risk_free_rate: float = 0.0):
        if self._initialized:
            return
        self._initialized = True
        self.risk_free_rate = risk_free_rate
        self._history: deque = deque(maxlen=200)
        self._lock = threading.RLock()

    def optimize(self, returns_map: Dict[str, List[float]],
                 method: str = "sharpe") -> Dict[str, Any]:
        """
        returns_map: { symbol: [daily_returns] }
        method: 'sharpe' | 'min_variance' | 'risk_parity' | 'equal_weight'
        Returns: { weights, expected_return, volatility, sharpe, method }
        """
        symbols = list(returns_map.keys())
        n = len(symbols)
        if n == 0:
            return {"error": "no assets"}

        means = [_mean(returns_map[s]) for s in symbols]
        stdevs = [_std(returns_map[s]) for s in symbols]

        # Covariance matrix
        cov = [[_covariance(returns_map[i], returns_map[j]) for j in symbols] for i in symbols]

        if method == "equal_weight":
            w = [1.0 / n] * n
        elif method == "min_variance":
            w = self._min_variance_weights(means, stdevs, cov)
        elif method == "risk_parity":
            w = self._risk_parity_weights(stdevs)
        else:
            w = self._max_sharpe_weights(means, stdevs, cov)

        # Portfolio metrics
        exp_ret = sum(w[i] * means[i] for i in range(n))
        port_var = sum(w[i] * w[j] * cov[i][j] for i in range(n) for j in range(n))
        port_vol = math.sqrt(max(port_var, 0))
        sharpe = (exp_ret - self.risk_free_rate) / port_vol if port_vol > 0 else 0

        result = {
            "weights": {symbols[i]: round(w[i], 4) for i in range(n)},
            "expected_return": round(exp_ret, 4),
            "volatility": round(port_vol, 4),
            "sharpe": round(sharpe, 4),
            "method": method,
            "timestamp": datetime.now().isoformat(),
        }

        with self._lock:
            self._history.append(result)
            try:
                with open(OPT_LOG, "a") as f:
                    f.write(json.dumps(result, default=str) + "\n")
            except Exception:
                pass
        return result

    def _max_sharpe_weights(self, means: List[float], stdevs: List[float],
                            cov: List[List[float]]) -> List[float]:
        n = len(means)
        if n == 1:
            return [1.0]
        # Simplified: use inverse variance as starting point, then tilt toward higher Sharpe
        iv = [1.0 / (s ** 2) if s > 0 else 0.0 for s in stdevs]
        total_iv = sum(iv)
        w = [v / total_iv for v in iv]
        # Tilt: boost assets with higher Sharpe, reduce lower
        sharpes = [(means[i] - self.risk_free_rate) / stdevs[i] if stdevs[i] > 0 else 0 for i in range(n)]
        max_sh = max(sharpes) if max(sharpes) > 0 else 1e-9
        tilt = [1 + 0.3 * (sh / max_sh - 0.5) for sh in sharpes]
        w = [w[i] * tilt[i] for i in range(n)]
        total = sum(w)
        return [v / total for v in w]

    def _min_variance_weights(self, means: List[float], stdevs: List[float],
                               cov: List[List[float]]) -> List[float]:
        n = len(means)
        if n == 1:
            return [1.0]
        iv = [1.0 / (s ** 2) if s > 0 else 0.0 for s in stdevs]
        total = sum(iv)
        return [v / total for v in iv]

    def _risk_parity_weights(self, stdevs: List[float]) -> List[float]:
        n = len(stdevs)
        if n == 1:
            return [1.0]
        inv_risk = [1.0 / s if s > 0 else 0.0 for s in stdevs]
        total = sum(inv_risk)
        return [v / total for v in inv_risk]

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._lock:
            return list(self._history)[-limit:]


def get_portfolio_optimizer() -> PortfolioOptimizer:
    return PortfolioOptimizer()
