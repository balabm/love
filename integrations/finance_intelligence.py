"""
LOVE Finance Intelligence — Real-time Market + News Awareness

Monitors:
- Cryptocurrency prices (Binance public API — no auth needed)
- Stock prices (Yahoo Finance — no auth needed)
- News sentiment on your watchlist
- Price alerts when things move significantly

Setup:
  Add to .env:
  FINANCE_WATCHLIST=BTCUSDT,ETHUSDT,BNBUSDT   (crypto)
  STOCK_WATCHLIST=AAPL,NVDA,TSLA               (stocks)
  PRICE_ALERT_THRESHOLD=0.05                    (5% move = alert)
"""

import json
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from core.execution_guard import log_error

DATA_DIR = Path(__file__).parent.parent / "data"
FINANCE_CACHE = DATA_DIR / "finance_intelligence.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CRYPTO_WATCHLIST = [s.strip() for s in os.getenv("FINANCE_WATCHLIST", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT").split(",") if s.strip()]
STOCK_WATCHLIST = [s.strip() for s in os.getenv("STOCK_WATCHLIST", "AAPL,NVDA,TSLA,MSFT").split(",") if s.strip()]
ALERT_THRESHOLD = float(os.getenv("PRICE_ALERT_THRESHOLD", "0.05"))


class FinanceIntelligence:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._prices: Dict[str, Dict] = {}
        self._prev_prices: Dict[str, float] = {}
        self._news: List[Dict] = []
        self._alerts: List[Dict] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_poll: Optional[float] = None
        self._load_cache()

    @classmethod
    def get_instance(cls) -> "FinanceIntelligence":
        with cls._lock:
            if cls._instance is None:
                cls._instance = FinanceIntelligence()
            return cls._instance

    def _fetch_crypto_price(self, symbol: str) -> Optional[Dict]:
        """Fetch crypto price from Binance public API."""
        try:
            import urllib.request
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())
            return {
                "symbol": symbol,
                "price": float(data.get("lastPrice", 0)),
                "change_pct": float(data.get("priceChangePercent", 0)),
                "volume": float(data.get("volume", 0)),
                "high_24h": float(data.get("highPrice", 0)),
                "low_24h": float(data.get("lowPrice", 0)),
                "source": "binance",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def _fetch_stock_price(self, symbol: str) -> Optional[Dict]:
        """Fetch stock price from Yahoo Finance (no API key)."""
        try:
            import urllib.request
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read())
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("previousClose", meta.get("chartPreviousClose", price))
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            return {
                "symbol": symbol,
                "price": price,
                "change_pct": round(change_pct, 2),
                "currency": meta.get("currency", "USD"),
                "market_state": meta.get("marketState", ""),
                "source": "yahoo",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def _fetch_financial_news(self) -> List[Dict]:
        """Fetch financial news from public RSS feeds."""
        try:
            import urllib.request, re
            url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                xml = r.read().decode("utf-8", errors="ignore")
            titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", xml)
            dates = re.findall(r"<pubDate>(.*?)</pubDate>", xml)
            news = []
            for i, title in enumerate(titles[:10]):
                if title.strip() and "Yahoo Finance" not in title:
                    news.append({
                        "title": title.strip(),
                        "date": dates[i] if i < len(dates) else "",
                        "source": "yahoo_finance_rss",
                    })
            return news
        except Exception:
            return []

    def refresh_prices(self) -> Dict[str, Dict]:
        """Refresh all prices and detect significant moves."""
        all_prices = {}
        # Crypto
        for symbol in CRYPTO_WATCHLIST:
            p = self._fetch_crypto_price(symbol)
            if p:
                all_prices[symbol] = p
                # Check for significant move
                prev = self._prev_prices.get(symbol)
                if prev and prev > 0:
                    change = abs(p["price"] - prev) / prev
                    if change >= ALERT_THRESHOLD:
                        direction = "up" if p["price"] > prev else "down"
                        self._alerts.append({
                            "symbol": symbol,
                            "message": f"{symbol} moved {direction} {change*100:.1f}% to ${p['price']:,.2f}",
                            "severity": "high" if change >= 0.1 else "normal",
                            "timestamp": datetime.now().isoformat(),
                        })
                self._prev_prices[symbol] = p["price"]
        # Stocks
        for symbol in STOCK_WATCHLIST:
            p = self._fetch_stock_price(symbol)
            if p:
                all_prices[symbol] = p
                if abs(p.get("change_pct", 0)) >= ALERT_THRESHOLD * 100:
                    direction = "up" if p["change_pct"] > 0 else "down"
                    self._alerts.append({
                        "symbol": symbol,
                        "message": f"{symbol} {direction} {abs(p['change_pct']):.1f}% today",
                        "severity": "high" if abs(p["change_pct"]) >= 10 else "normal",
                        "timestamp": datetime.now().isoformat(),
                    })
        self._prices = all_prices
        self._last_poll = time.time()
        self._save_cache()
        return all_prices

    def get_prices(self) -> Dict[str, Dict]:
        if not self._prices and (not self._last_poll or time.time() - self._last_poll > 300):
            self.refresh_prices()
        return self._prices

    def get_price_summary(self) -> str:
        """One-line price summary for context injection."""
        prices = self.get_prices()
        if not prices:
            return ""
        parts = []
        for symbol, data in list(prices.items())[:6]:
            price = data.get("price", 0)
            change = data.get("change_pct", 0)
            sign = "+" if change >= 0 else ""
            currency = "$" if data.get("source") in ("binance", "yahoo") else ""
            parts.append(f"{symbol}: {currency}{price:,.2f} ({sign}{change:.1f}%)")
        return " | ".join(parts)

    def get_context_summary(self) -> str:
        """Summary for injection into LOVE's context prompt."""
        parts = []
        price_line = self.get_price_summary()
        if price_line:
            parts.append(f"[MARKETS] {price_line}")
        pending_alerts = [a for a in self._alerts[-5:] if a.get("severity") == "high"]
        for alert in pending_alerts[:2]:
            parts.append(f"  !! {alert['message']}")
        news = self._news[:2]
        for n in news:
            parts.append(f"[FINEWS] {n['title'][:80]}")
        return "\n".join(parts)

    def get_alerts(self, limit: int = 10) -> List[Dict]:
        return list(reversed(self._alerts[-limit:]))

    def get_news(self, limit: int = 10) -> List[Dict]:
        return self._news[:limit]

    def start_monitoring(self, interval: int = 300):
        if self._running:
            return
        self._running = True
        def _loop():
            while self._running:
                try:
                    prices = self.refresh_prices()
                    self._news = self._fetch_financial_news()
                    # Push significant alerts
                    new_alerts = [a for a in self._alerts if a.get("severity") == "high" and not a.get("pushed")]
                    for alert in new_alerts[:2]:
                        try:
                            from core.proactive_push import get_push_engine
                            get_push_engine().push("ALERT", alert["message"], priority="high", metadata={"source": "finance"})
                            alert["pushed"] = True
                        except Exception as e:
                            from core.execution_guard import log_error
                            log_error(e, module="integrations.finance_intelligence")
                except Exception as e:
                    from core.execution_guard import log_error
                    log_error(e, module="integrations.finance_intelligence")
                time.sleep(interval)
        self._thread = threading.Thread(target=_loop, daemon=True, name="LOVE-Finance")
        self._thread.start()

    def _save_cache(self):
        try:
            cache = {"prices": self._prices, "news": self._news[:20], "prev_prices": self._prev_prices}
            FINANCE_CACHE.write_text(json.dumps(cache, default=str, indent=2))
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="integrations.finance_intelligence")

    def _load_cache(self):
        try:
            if FINANCE_CACHE.exists():
                data = json.loads(FINANCE_CACHE.read_text())
                self._prices = data.get("prices", {})
                self._news = data.get("news", [])
                self._prev_prices = data.get("prev_prices", {})
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="integrations.finance_intelligence")


def get_finance_intelligence() -> FinanceIntelligence:
    return FinanceIntelligence.get_instance()
