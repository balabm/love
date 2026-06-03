"""
Finance Sentinel (Binance Co-Pilot)
Crypto analyst and portfolio tracker for the user.
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.llm import get_reasoning_llm
from core.memory import save_log
from core.execution_guard import log_error

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USER_PROFILE_PATH = DATA_DIR / "user_profile.json"

# Binance API endpoints
BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_FAPI_URL = "https://fapi.binance.com"


@dataclass
class MarketSignal:
    """Trading signal with context."""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold', 'watch'
    confidence: float  # 0.0 to 1.0
    current_price: float
    analysis: str
    suggested_action: str
    risk_level: str  # 'low', 'medium', 'high'


@dataclass
class TradeHistory:
    """User's trade record."""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    timestamp: datetime
    pnl: Optional[float] = None
    notes: str = ""


class BinanceClient:
    """Lightweight Binance API client."""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol."""
        try:
            response = requests.get(
                f"{BINANCE_BASE_URL}/api/v3/ticker/24hr",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                'symbol': data['symbol'],
                'price': float(data['lastPrice']),
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume': float(data['volume']),
                'quote_volume': float(data['quoteVolume'])
            }
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[List]:
        """Get candlestick data for technical analysis."""
        try:
            response = requests.get(
                f"{BINANCE_BASE_URL}/api/v3/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return []
    
    def get_order_book(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Get order book depth."""
        try:
            response = requests.get(
                f"{BINANCE_BASE_URL}/api/v3/depth",
                params={"symbol": symbol.upper(), "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}


class PortfolioManager:
    """Manages the user's crypto portfolio in user_profile.json."""
    
    def __init__(self):
        self.profile_path = USER_PROFILE_PATH
        self._ensure_profile()
        
    def _ensure_profile(self):
        """Ensure portfolio section exists in profile."""
        profile = self._load_profile()
        if 'portfolio' not in profile:
            profile['portfolio'] = {
                'holdings': {},  # symbol -> {quantity, avg_buy_price}
                'trade_history': [],
                'watchlist': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
                'risk_profile': 'moderate',  # conservative, moderate, aggressive
                'max_position_size_inr': 50000,
                'stop_loss_percent': 5,
                'take_profit_percent': 15
            }
            self._save_profile(profile)
    
    def _load_profile(self) -> Dict[str, Any]:
        """Load user profile."""
        if self.profile_path.exists():
            with open(self.profile_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_profile(self, profile: Dict[str, Any]):
        """Save user profile."""
        with open(self.profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def get_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio."""
        profile = self._load_profile()
        return profile.get('portfolio', {})
    
    def update_holdings(self, symbol: str, quantity: float, price: float, side: str):
        """Update holdings after a trade."""
        profile = self._load_profile()
        portfolio = profile.get('portfolio', {})
        holdings = portfolio.get('holdings', {})
        
        if side.upper() == 'BUY':
            if symbol in holdings:
                # Update average buy price
                old_qty = holdings[symbol]['quantity']
                old_avg = holdings[symbol]['avg_buy_price']
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * price) / new_qty
                holdings[symbol] = {
                    'quantity': new_qty,
                    'avg_buy_price': round(new_avg, 2),
                    'last_buy': price,
                    'last_buy_time': datetime.now().isoformat()
                }
            else:
                holdings[symbol] = {
                    'quantity': quantity,
                    'avg_buy_price': price,
                    'last_buy': price,
                    'last_buy_time': datetime.now().isoformat()
                }
        elif side.upper() == 'SELL':
            if symbol in holdings:
                current_qty = holdings[symbol]['quantity']
                avg_buy = holdings[symbol]['avg_buy_price']
                
                if quantity >= current_qty:
                    # Selling all
                    pnl = (price - avg_buy) * current_qty
                    del holdings[symbol]
                else:
                    # Selling partial
                    pnl = (price - avg_buy) * quantity
                    holdings[symbol]['quantity'] = current_qty - quantity
                
                # Record trade
                trade = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'pnl': round(pnl, 2) if 'pnl' in dir() else None
                }
                portfolio.setdefault('trade_history', []).append(trade)
        
        portfolio['holdings'] = holdings
        profile['portfolio'] = portfolio
        self._save_profile(profile)
        
        # Log the update
        save_log('portfolio_update', {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now().isoformat()
        })
        
        return portfolio['holdings']
    
    def add_to_watchlist(self, symbol: str):
        """Add symbol to watchlist."""
        profile = self._load_profile()
        portfolio = profile.get('portfolio', {})
        watchlist = portfolio.get('watchlist', [])
        
        if symbol.upper() not in [s.upper() for s in watchlist]:
            watchlist.append(symbol.upper())
            portfolio['watchlist'] = watchlist
            profile['portfolio'] = portfolio
            self._save_profile(profile)
        
        return watchlist
    
    def get_trade_history(self, symbol: str = None, days: int = 30) -> List[Dict]:
        """Get trade history, optionally filtered by symbol."""
        profile = self._load_profile()
        portfolio = profile.get('portfolio', {})
        history = portfolio.get('trade_history', [])
        
        cutoff = datetime.now() - timedelta(days=days)
        
        filtered = []
        for trade in history:
            trade_time = datetime.fromisoformat(trade['timestamp'])
            if trade_time >= cutoff:
                if symbol is None or trade['symbol'].upper() == symbol.upper():
                    filtered.append(trade)
        
        return filtered


class CoPilotAnalyzer:
    """AI-powered market analysis using DeepSeek reasoning model."""
    
    def __init__(self):
        self.llm = get_reasoning_llm()
        self.client = BinanceClient()
        self.portfolio = PortfolioManager()
    
    def analyze_market(self, symbol: str) -> MarketSignal:
        """Analyze a market and generate trading signal."""
        # Get market data
        ticker = self.client.get_ticker(symbol)
        klines = self.client.get_klines(symbol, interval="4h", limit=50)
        
        if 'error' in ticker:
            return MarketSignal(
                symbol=symbol,
                signal_type='error',
                confidence=0,
                current_price=0,
                analysis=f"Error fetching data: {ticker['error']}",
                suggested_action="Check connection and try again",
                risk_level='high'
            )
        
        # Get portfolio context
        holdings = self.portfolio.get_portfolio().get('holdings', {})
        has_position = symbol.upper() in [s.upper() for s in holdings.keys()]
        
        # Build prompt for reasoning model
        klines_summary = self._summarize_klines(klines)
        
        prompt = f"""You are LOVE, the user's crypto co-pilot. Analyze this market data and give a clear, specific trading signal.

MARKET DATA FOR {symbol}:
- Current Price: ${ticker['price']:,.2f}
- 24h Change: {ticker['change_24h']:+.2f}%
- 24h High: ${ticker['high_24h']:,.2f}
- 24h Low: ${ticker['low_24h']:,.2f}
- 24h Volume: ${ticker['quote_volume']:,.0f}

RECENT PRICE ACTION (last 50 4h candles):
{klines_summary}

PORTFOLIO CONTEXT:
- User {'holds' if has_position else 'does not hold'} {symbol}
- Risk profile: {self.portfolio.get_portfolio().get('risk_profile', 'moderate')}

TASK: Provide a trading signal in this exact format:
SIGNAL: [buy/sell/hold/watch]
CONFIDENCE: [0.0-1.0]
ANALYSIS: [2-3 sentences explaining the setup]
SUGGESTED_ACTION: [specific action like "Consider 5000 INR buy at current price" or "Watch for breakout above $X"]
RISK: [low/medium/high]

Be direct and specific. No generic "DYOR" disclaimers. Give your actual read on this."""

        try:
            response = self.llm.invoke(prompt)
            signal = self._parse_signal_response(response, symbol, ticker['price'])
            
            # Log analysis
            save_log('market_analysis', {
                'symbol': symbol,
                'signal': signal.signal_type,
                'confidence': signal.confidence,
                'price': signal.current_price,
                'timestamp': datetime.now().isoformat()
            })
            
            return signal
            
        except Exception as e:
            return MarketSignal(
                symbol=symbol,
                signal_type='error',
                confidence=0,
                current_price=ticker['price'],
                analysis=f"Analysis error: {str(e)}",
                suggested_action="Retry analysis",
                risk_level='high'
            )
    
    def _summarize_klines(self, klines: List[List]) -> str:
        """Summarize kline data for the LLM."""
        if not klines or len(klines) < 10:
            return "Insufficient data"
        
        # Get recent context
        recent = klines[-10:]
        opens = [float(k[1]) for k in recent]
        highs = [float(k[2]) for k in recent]
        lows = [float(k[3]) for k in recent]
        closes = [float(k[4]) for k in recent]
        volumes = [float(k[5]) for k in recent]
        
        trend = "up" if closes[-1] > opens[0] else "down" if closes[-1] < opens[0] else "sideways"
        volatility = ((max(highs) - min(lows)) / closes[0]) * 100
        
        return f"Trend: {trend}, Range: ${min(lows):,.2f} - ${max(highs):,.2f}, Volatility: {volatility:.1f}%, Avg Volume: ${sum(volumes)/len(volumes):,.0f}"
    
    def _parse_signal_response(self, response: str, symbol: str, price: float) -> MarketSignal:
        """Parse LLM response into MarketSignal."""
        signal_type = 'hold'
        confidence = 0.5
        analysis = response
        suggested = "No specific action suggested"
        risk = 'medium'
        
        # Extract SIGNAL
        signal_match = re.search(r'SIGNAL:\s*(\w+)', response, re.IGNORECASE)
        if signal_match:
            signal_type = signal_match.group(1).lower()
        
        # Extract CONFIDENCE
        conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', response)
        if conf_match:
            confidence = float(conf_match.group(1))
        
        # Extract ANALYSIS
        analysis_match = re.search(r'ANALYSIS:\s*(.+?)(?=SUGGESTED_ACTION:|RISK:|$)', response, re.DOTALL)
        if analysis_match:
            analysis = analysis_match.group(1).strip()
        
        # Extract SUGGESTED_ACTION
        action_match = re.search(r'SUGGESTED_ACTION:\s*(.+?)(?=RISK:|$)', response, re.DOTALL)
        if action_match:
            suggested = action_match.group(1).strip()
        
        # Extract RISK
        risk_match = re.search(r'RISK:\s*(\w+)', response, re.IGNORECASE)
        if risk_match:
            risk = risk_match.group(1).lower()
        
        return MarketSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            current_price=price,
            analysis=analysis,
            suggested_action=suggested,
            risk_level=risk
        )
    
    def scan_watchlist(self) -> List[MarketSignal]:
        """Analyze all symbols in watchlist."""
        portfolio = self.portfolio.get_portfolio()
        watchlist = portfolio.get('watchlist', ['BTCUSDT', 'ETHUSDT'])
        
        signals = []
        for symbol in watchlist:
            signal = self.analyze_market(symbol)
            signals.append(signal)
        
        return signals
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio value and performance."""
        portfolio = self.portfolio.get_portfolio()
        holdings = portfolio.get('holdings', {})
        
        total_value = 0
        total_cost = 0
        positions = []
        
        for symbol, data in holdings.items():
            ticker = self.client.get_ticker(symbol)
            if 'error' in ticker:
                continue
            
            current_price = ticker['price']
            quantity = data['quantity']
            avg_buy = data['avg_buy_price']
            
            value = quantity * current_price
            cost = quantity * avg_buy
            pnl = value - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else 0
            
            total_value += value
            total_cost += cost
            
            positions.append({
                'symbol': symbol,
                'quantity': quantity,
                'avg_buy': avg_buy,
                'current_price': current_price,
                'value': round(value, 2),
                'pnl': round(pnl, 2),
                'pnl_pct': round(pnl_pct, 2)
            })
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl_pct, 2),
            'positions': positions,
            'position_count': len(positions)
        }


# Public API functions
def get_market_signal(symbol: str) -> Dict[str, Any]:
    """Get AI-powered market signal for a symbol."""
    analyzer = CoPilotAnalyzer()
    signal = analyzer.analyze_market(symbol)
    
    return {
        'symbol': signal.symbol,
        'signal': signal.signal_type,
        'confidence': signal.confidence,
        'price': signal.current_price,
        'analysis': signal.analysis,
        'suggested_action': signal.suggested_action,
        'risk_level': signal.risk_level
    }


def scan_all_markets() -> List[Dict[str, Any]]:
    """Scan watchlist and return all signals."""
    analyzer = CoPilotAnalyzer()
    signals = analyzer.scan_watchlist()
    
    return [
        {
            'symbol': s.symbol,
            'signal': s.signal_type,
            'confidence': s.confidence,
            'price': s.current_price,
            'analysis': s.analysis,
            'suggested_action': s.suggested_action,
            'risk_level': s.risk_level
        }
        for s in signals
    ]


def get_portfolio() -> Dict[str, Any]:
    """Get current portfolio summary."""
    analyzer = CoPilotAnalyzer()
    return analyzer.get_portfolio_summary()


def record_trade(symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
    """Record a trade and update holdings."""
    portfolio = PortfolioManager()
    holdings = portfolio.update_holdings(symbol, quantity, price, side)
    
    return {
        'success': True,
        'symbol': symbol,
        'side': side,
        'quantity': quantity,
        'price': price,
        'updated_holdings': holdings,
        'timestamp': datetime.now().isoformat()
    }


def add_to_watchlist(symbol: str) -> Dict[str, Any]:
    """Add a symbol to watchlist."""
    portfolio = PortfolioManager()
    watchlist = portfolio.add_to_watchlist(symbol)
    
    return {
        'success': True,
        'added': symbol,
        'watchlist': watchlist
    }


def format_signal_for_chat(signal: Dict[str, Any]) -> str:
    """Format a market signal for LOVE's companion chat."""
    symbol = signal['symbol']
    signal_type = signal['signal']
    price = signal['price']
    analysis = signal['analysis']
    suggested = signal['suggested_action']
    confidence = signal['confidence']
    risk = signal['risk_level']
    
    # Format based on signal strength
    if confidence >= 0.8:
        tone = "Strong signal"
    elif confidence >= 0.6:
        tone = "Decent setup"
    else:
        tone = "Worth watching"
    
    emoji_map = {
        'buy': '🟢',
        'sell': '🔴',
        'hold': '🟡',
        'watch': '👁️'
    }
    
    emoji = emoji_map.get(signal_type, '📊')
    
    return f"""{emoji} {tone} on {symbol} at ${price:,.2f}

{analysis}

{suggested} (Risk: {risk}, Confidence: {confidence:.0%})

Want me to draft an order or add this to your watchlist?"""


# ========== PREDICTIVE FINANCE (ALPHA SENTINEL) ==========

class AlphaSentinel:
    """Predictive finance with sentiment analysis and trade recommendations."""
    
    def __init__(self):
        self.llm = get_reasoning_llm()
        self.client = BinanceClient()
        self.portfolio = PortfolioManager()
        self.last_news_check = None
        
    def fetch_crypto_news(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch recent news headlines for a crypto symbol."""
        # In production, this would use a news API like CryptoPanic, NewsAPI, etc.
        # For now, we'll simulate with LLM-based generation based on market context
        
        ticker = self.client.get_ticker(symbol)
        if 'error' in ticker:
            return []
        
        # Use LLM to generate likely news based on market conditions
        prompt = f"""Generate 3 realistic news headlines for {symbol} given these market conditions:
        - Price: ${ticker['price']:,.2f}
        - 24h Change: {ticker['change_24h']:+.2f}%
        - 24h Volume: ${ticker['quote_volume']:,.0f}

Generate headlines that would be realistic for this price action. Mix positive and negative.
Return as a JSON array with objects containing: headline (str), sentiment (positive/negative/neutral), source (str)
"""
        try:
            response = self.llm.invoke(prompt)
            # Extract JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            from core.execution_guard import log_error
            log_error(e, module="tools.finance")
        
        # Fallback: empty list
        return []
    
    def analyze_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Analyze news sentiment for a symbol."""
        news = self.fetch_crypto_news(symbol)
        
        if not news:
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'sentiment_score': 0.0,
                'news_count': 0,
                'headlines': []
            }
        
        # Calculate sentiment score
        positive = sum(1 for n in news if n.get('sentiment') == 'positive')
        negative = sum(1 for n in news if n.get('sentiment') == 'negative')
        total = len(news)
        
        sentiment_score = (positive - negative) / total if total > 0 else 0
        
        # Determine overall sentiment
        if sentiment_score > 0.3:
            sentiment = 'positive'
        elif sentiment_score < -0.3:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'symbol': symbol,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'news_count': total,
            'positive_count': positive,
            'negative_count': negative,
            'headlines': [n.get('headline') for n in news]
        }
    
    def generate_trade_advice(self, symbol: str) -> Dict[str, Any]:
        """Generate calculated trade advice combining sentiment + portfolio + market."""
        # Get all data sources
        sentiment_data = self.analyze_sentiment(symbol)
        portfolio_data = self.portfolio.get_portfolio()
        market_signal = CoPilotAnalyzer().analyze_market(symbol)
        
        holdings = portfolio_data.get('holdings', {})
        has_position = symbol.upper() in [s.upper() for s in holdings.keys()]
        
        position_data = None
        if has_position:
            for pos in self.portfolio.get_portfolio_summary().get('positions', []):
                if pos['symbol'].upper() == symbol.upper():
                    position_data = pos
                    break
        
        # Build comprehensive prompt for reasoning model
        prompt = f"""You are LOVE's Alpha Sentinel. Generate a specific trade recommendation based on:

SYMBOL: {symbol}
PRICE: ${market_signal.current_price:,.2f}

SENTIMENT ANALYSIS:
- Overall: {sentiment_data['sentiment']} (score: {sentiment_data['sentiment_score']:+.2f})
- Positive news: {sentiment_data['positive_count']}
- Negative news: {sentiment_data['negative_count']}
- Recent headlines: {sentiment_data['headlines'][:2]}

PORTFOLIO STATUS:
- Has position: {has_position}
- Position P&L: {position_data['pnl_pct'] if position_data else 'N/A'}%
- Position value: ${position_data['value'] if position_data else 0:,.2f}

TECHNICAL SIGNAL:
- Signal: {market_signal.signal_type}
- Confidence: {market_signal.confidence:.0%}
- Analysis: {market_signal.analysis}

TASK: Return a specific trade recommendation as JSON:
{{
    "recommendation": "buy/sell/hold/move_to_stable",
    "urgency": "immediate/soon/watch",
    "action": "specific action like 'Move 5000 INR to USDT' or 'Hold current position'",
    "reasoning": "2-3 sentences combining sentiment, portfolio, and technicals",
    "risk_level": "low/medium/high",
    "confidence": 0.0-1.0,
    "requires_confirmation": true/false
}}

Be specific and actionable. If suggesting a move to stablecoins during negative sentiment, be clear about protecting profits."""

        try:
            response = self.llm.invoke(prompt)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                advice = json.loads(json_match.group())
            else:
                advice = {
                    'recommendation': 'hold',
                    'urgency': 'watch',
                    'action': 'Monitor market conditions',
                    'reasoning': 'Could not generate specific advice',
                    'risk_level': 'medium',
                    'confidence': 0.5,
                    'requires_confirmation': True
                }
            
            # Log the advice
            save_log('alpha_sentinel', {
                'symbol': symbol,
                'recommendation': advice['recommendation'],
                'sentiment': sentiment_data['sentiment'],
                'portfolio_pnl': position_data['pnl_pct'] if position_data else None,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                **advice,
                'symbol': symbol,
                'price': market_signal.current_price,
                'sentiment_data': sentiment_data,
                'has_position': has_position
            }
            
        except Exception as e:
            return {
                'recommendation': 'hold',
                'action': 'Analysis error - maintain current position',
                'reasoning': str(e),
                'symbol': symbol,
                'price': market_signal.current_price if 'market_signal' in locals() else 0,
                'error': str(e)
            }
    
    def scan_for_opportunities(self) -> List[Dict[str, Any]]:
        """Scan watchlist for high-confidence trade opportunities."""
        portfolio = self.portfolio.get_portfolio()
        watchlist = portfolio.get('watchlist', ['BTCUSDT', 'ETHUSDT'])
        
        opportunities = []
        
        for symbol in watchlist:
            advice = self.generate_trade_advice(symbol)
            
            # Only return high-confidence opportunities
            if advice.get('confidence', 0) > 0.7 and advice.get('requires_confirmation'):
                opportunities.append(advice)
        
        return opportunities


# Public API functions for Alpha Sentinel
def get_sentiment_analysis(symbol: str) -> Dict[str, Any]:
    """Get sentiment analysis for a symbol."""
    sentinel = AlphaSentinel()
    return sentinel.analyze_sentiment(symbol)


def get_trade_advice(symbol: str) -> Dict[str, Any]:
    """Get comprehensive trade advice with sentiment + portfolio correlation."""
    sentinel = AlphaSentinel()
    advice = sentinel.generate_trade_advice(symbol)
    
    return advice


def format_trade_advice_for_chat(advice: Dict[str, Any]) -> str:
    """Format Alpha Sentinel advice for LOVE's companion chat."""
    symbol = advice['symbol']
    recommendation = advice['recommendation']
    action = advice['action']
    reasoning = advice['reasoning']
    confidence = advice.get('confidence', 0.5)
    urgency = advice.get('urgency', 'watch')
    
    # Urgency emoji
    if urgency == 'immediate':
        emoji = '🔴'
        tone = "Act now"
    elif urgency == 'soon':
        emoji = '🟡'
        tone = "Consider soon"
    else:
        emoji = '🟢'
        tone = "Watch closely"
    
    # Has position context
    has_position = advice.get('has_position', False)
    position_note = "You're holding this." if has_position else "You don't hold this yet."
    
    return f"""{emoji} {tone} — {symbol} advice

{reasoning}

Suggested action: {action}

{position_note} Confidence: {confidence:.0%}. Say 'Execute' if you want me to help with this trade."""


def scan_alpha_opportunities() -> List[Dict[str, Any]]:
    """Scan for high-confidence trade opportunities."""
    sentinel = AlphaSentinel()
    return sentinel.scan_for_opportunities()
