#!/usr/bin/env python3
"""
🔥 LIVE TRADING SYSTEM - Complete Integration
Real-time stock data with AI signals, paper trading, and synchronized dashboard
"""

import os
import sys
import asyncio
import sqlite3
import pandas as pd
import yfinance as yf
import websocket
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LiveQuote:
    """Live stock quote data structure"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    open_price: float
    timestamp: datetime
    
class LiveDataManager:
    """Manages real-time stock data from multiple sources"""
    
    def __init__(self):
        self.subscribers = []
        self.quotes = {}
        self.running = False
        self.update_interval = 1  # seconds
        
    def add_subscriber(self, callback):
        """Add callback for live data updates"""
        self.subscribers.append(callback)
    
    def remove_subscriber(self, callback):
        """Remove data update callback"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def notify_subscribers(self, symbol: str, quote: LiveQuote):
        """Notify all subscribers of data update"""
        for callback in self.subscribers:
            try:
                callback(symbol, quote)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def get_live_quote(self, symbol: str) -> LiveQuote:
        """Get live quote from multiple sources"""
        try:
            # Primary: Yahoo Finance (most reliable for Indian stocks)
            ticker = yf.Ticker(f"{symbol}.NS")
            
            # Get today's data with 1-minute intervals
            data = ticker.history(period="1d", interval="1m")
            if data.empty:
                # Try without .NS suffix for international stocks
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                open_price = data.iloc[0]['Open']
                
                quote = LiveQuote(
                    symbol=symbol,
                    price=float(latest['Close']),
                    change=float(latest['Close'] - open_price),
                    change_percent=float((latest['Close'] - open_price) / open_price * 100),
                    volume=int(latest['Volume']),
                    high=float(data['High'].max()),
                    low=float(data['Low'].min()),
                    open_price=float(open_price),
                    timestamp=datetime.now()
                )
                
                self.quotes[symbol] = quote
                return quote
            else:
                # Fallback: Use previous data or create dummy quote
                if symbol in self.quotes:
                    return self.quotes[symbol]
                else:
                    return LiveQuote(
                        symbol=symbol,
                        price=100.0,
                        change=0.0,
                        change_percent=0.0,
                        volume=0,
                        high=100.0,
                        low=100.0,
                        open_price=100.0,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Error getting live quote for {symbol}: {e}")
            # Return cached data or dummy data
            if symbol in self.quotes:
                return self.quotes[symbol]
            else:
                return LiveQuote(
                    symbol=symbol,
                    price=100.0,
                    change=0.0,
                    change_percent=0.0,
                    volume=0,
                    high=100.0,
                    low=100.0,
                    open_price=100.0,
                    timestamp=datetime.now()
                )
    
    async def start_live_feed(self, symbols: List[str]):
        """Start live data feed for given symbols"""
        self.running = True
        logger.info(f"Starting live data feed for {len(symbols)} symbols")
        
        while self.running:
            try:
                # Update quotes for all symbols
                tasks = [self.get_live_quote(symbol) for symbol in symbols]
                quotes = await asyncio.gather(*tasks, return_exceptions=True)
                
                for symbol, quote in zip(symbols, quotes):
                    if isinstance(quote, LiveQuote):
                        self.notify_subscribers(symbol, quote)
                    
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in live feed: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def stop_live_feed(self):
        """Stop live data feed"""
        self.running = False
        logger.info("Live data feed stopped")

class AISignalGenerator:
    """AI-powered trading signal generator with live data"""
    
    def __init__(self):
        self.model_loaded = False
        self.signal_cache = {}
        
    def analyze_live_data(self, symbol: str, quote: LiveQuote, historical_data: pd.DataFrame) -> Dict:
        """Generate trading signal from live data and historical context"""
        try:
            if historical_data.empty or len(historical_data) < 50:
                return {
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'confidence': 0,
                    'reason': 'Insufficient data'
                }
            
            # Calculate technical indicators
            data = historical_data.copy()
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # MACD
            exp1 = data['Close'].ewm(span=12).mean()
            exp2 = data['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal_line = macd.ewm(span=9).mean()
            histogram = macd - signal_line
            
            # Moving Averages
            sma_20 = data['Close'].rolling(window=20).mean()
            sma_50 = data['Close'].rolling(window=50).mean()
            
            # Current values
            current_price = quote.price
            current_sma_20 = sma_20.iloc[-1]
            current_sma_50 = sma_50.iloc[-1]
            current_macd = macd.iloc[-1]
            current_signal = signal_line.iloc[-1]
            
            # Signal logic
            signals = []
            reasons = []
            
            # RSI signals
            if current_rsi < 30:
                signals.append('BUY')
                reasons.append(f'RSI oversold ({current_rsi:.1f})')
            elif current_rsi > 70:
                signals.append('SELL')
                reasons.append(f'RSI overbought ({current_rsi:.1f})')
            
            # MACD signals
            if current_macd > current_signal and macd.iloc[-2] <= signal_line.iloc[-2]:
                signals.append('BUY')
                reasons.append('MACD bullish crossover')
            elif current_macd < current_signal and macd.iloc[-2] >= signal_line.iloc[-2]:
                signals.append('SELL')
                reasons.append('MACD bearish crossover')
            
            # Moving average signals
            if current_price > current_sma_20 > current_sma_50:
                signals.append('BUY')
                reasons.append('Price above moving averages')
            elif current_price < current_sma_20 < current_sma_50:
                signals.append('SELL')
                reasons.append('Price below moving averages')
            
            # Price action signals
            if quote.change_percent > 2:
                signals.append('MOMENTUM_BUY')
                reasons.append(f'Strong upward momentum ({quote.change_percent:.1f}%)')
            elif quote.change_percent < -2:
                signals.append('MOMENTUM_SELL')
                reasons.append(f'Strong downward momentum ({quote.change_percent:.1f}%)')
            
            # Determine final signal
            buy_signals = signals.count('BUY') + signals.count('MOMENTUM_BUY')
            sell_signals = signals.count('SELL') + signals.count('MOMENTUM_SELL')
            
            if buy_signals > sell_signals:
                final_signal = 'BUY'
                confidence = min(90, 50 + (buy_signals * 15))
            elif sell_signals > buy_signals:
                final_signal = 'SELL'
                confidence = min(90, 50 + (sell_signals * 15))
            else:
                final_signal = 'HOLD'
                confidence = 30
            
            result = {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': confidence,
                'reasons': reasons,
                'technical_data': {
                    'rsi': current_rsi,
                    'macd': current_macd,
                    'signal_line': current_signal,
                    'sma_20': current_sma_20,
                    'sma_50': current_sma_50,
                    'price': current_price
                },
                'timestamp': datetime.now().isoformat()
            }
            
            self.signal_cache[symbol] = result
            return result
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return {
                'symbol': symbol,
                'signal': 'HOLD',
                'confidence': 0,
                'reason': f'Analysis error: {str(e)}'
            }

class LiveTradingManager:
    """Integrated trading manager with live data and AI signals"""
    
    def __init__(self, initial_balance: float = 1000000.0):
        self.initial_balance = initial_balance
        self.db_path = "live_trading_system.db"
        self.data_manager = LiveDataManager()
        self.ai_generator = AISignalGenerator()
        self.portfolio_listeners = []
        self.signal_listeners = []
        
        # Watchlist - major Indian stocks (verified active symbols)
        self.watchlist = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'ITC', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 
            'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA', 'WIPRO'
        ]
        
        self.init_database()
        self.setup_data_subscriptions()
        
        logger.info(f"Live Trading Manager initialized with Rs.{initial_balance:,.2f}")
    
    def init_database(self):
        """Initialize comprehensive trading database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY,
                    cash_balance REAL DEFAULT 1000000.0,
                    invested_value REAL DEFAULT 0.0,
                    total_value REAL DEFAULT 1000000.0,
                    day_pnl REAL DEFAULT 0.0,
                    total_pnl REAL DEFAULT 0.0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Positions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL DEFAULT 0.0,
                    day_pnl REAL DEFAULT 0.0,
                    total_pnl REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                )
            ''')
            
            # Signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasons TEXT,
                    technical_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Live quotes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_quotes (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_val REAL NOT NULL,
                    change_percent REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    open_price REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Initialize portfolio if empty
            cursor.execute('SELECT COUNT(*) FROM portfolio')
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'INSERT INTO portfolio (cash_balance, total_value) VALUES (?, ?)',
                    (self.initial_balance, self.initial_balance)
                )
            
            conn.commit()
            conn.close()
            logger.info("Live trading database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def setup_data_subscriptions(self):
        """Setup live data subscriptions"""
        self.data_manager.add_subscriber(self.on_live_quote_update)
    
    def on_live_quote_update(self, symbol: str, quote: LiveQuote):
        """Handle live quote updates"""
        try:
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update live quotes table
            cursor.execute('''
                INSERT OR REPLACE INTO live_quotes 
                (symbol, price, change_val, change_percent, volume, high, low, open_price, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, quote.price, quote.change, quote.change_percent, 
                  quote.volume, quote.high, quote.low, quote.open_price, 
                  quote.timestamp))
            
            # Update positions with current prices
            cursor.execute('UPDATE positions SET current_price = ?, last_updated = ? WHERE symbol = ?',
                          (quote.price, quote.timestamp, symbol))
            
            conn.commit()
            conn.close()
            
            # Generate AI signal
            historical_data = self.get_historical_data(symbol, days=100)
            signal = self.ai_generator.analyze_live_data(symbol, quote, historical_data)
            
            # Store signal
            self.store_signal(signal)
            
            # Notify listeners
            for callback in self.signal_listeners:
                callback(signal)
                
        except Exception as e:
            logger.error(f"Error processing live quote for {symbol}: {e}")
    
    def get_historical_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """Get historical data for analysis"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period=f"{days}d")
            if data.empty:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=f"{days}d")
            return data
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_signal(self, signal: Dict):
        """Store AI signal in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals (symbol, signal, confidence, reasons, technical_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (signal['symbol'], signal['signal'], signal['confidence'],
                  json.dumps(signal.get('reasons', [])),
                  json.dumps(signal.get('technical_data', {}))))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing signal: {e}")
    
    def get_portfolio(self) -> Dict:
        """Get current portfolio with real-time values"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get cash balance
            cursor.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT 1')
            portfolio_row = cursor.fetchone()
            
            if not portfolio_row:
                cash_balance = self.initial_balance
                total_value = self.initial_balance
            else:
                cash_balance = portfolio_row[1]
                total_value = portfolio_row[3]
            
            # Calculate invested value and P&L from positions
            cursor.execute('''
                SELECT symbol, quantity, avg_price, current_price 
                FROM positions WHERE quantity > 0
            ''')
            positions = cursor.fetchall()
            
            invested_value = 0.0
            current_value = 0.0
            
            for pos in positions:
                symbol, quantity, avg_price, current_price = pos
                invested_value += quantity * avg_price
                current_value += quantity * (current_price if current_price > 0 else avg_price)
            
            total_portfolio_value = cash_balance + current_value
            total_pnl = total_portfolio_value - self.initial_balance
            day_pnl = current_value - invested_value
            
            # Update portfolio table
            cursor.execute('''
                UPDATE portfolio 
                SET invested_value = ?, total_value = ?, day_pnl = ?, total_pnl = ?, updated_at = ?
                WHERE id = (SELECT MAX(id) FROM portfolio)
            ''', (invested_value, total_portfolio_value, day_pnl, total_pnl, datetime.now()))
            
            conn.commit()
            conn.close()
            
            return {
                'cash_balance': cash_balance,
                'invested_value': invested_value,
                'current_value': current_value,
                'total_value': total_portfolio_value,
                'day_pnl': day_pnl,
                'total_pnl': total_pnl,
                'day_pnl_percent': (day_pnl / invested_value * 100) if invested_value > 0 else 0,
                'total_pnl_percent': (total_pnl / self.initial_balance * 100)
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {
                'cash_balance': self.initial_balance,
                'invested_value': 0.0,
                'current_value': 0.0,
                'total_value': self.initial_balance,
                'day_pnl': 0.0,
                'total_pnl': 0.0,
                'day_pnl_percent': 0.0,
                'total_pnl_percent': 0.0
            }
    
    def get_live_quotes(self) -> List[Dict]:
        """Get all live quotes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, price, change_val, change_percent, volume, high, low, open_price, updated_at
                FROM live_quotes ORDER BY updated_at DESC
            ''')
            quotes = cursor.fetchall()
            conn.close()
            
            result = []
            for quote in quotes:
                result.append({
                    'symbol': quote[0],
                    'price': quote[1],
                    'change': quote[2],
                    'change_percent': quote[3],
                    'volume': quote[4],
                    'high': quote[5],
                    'low': quote[6],
                    'open': quote[7],
                    'updated_at': quote[8]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting live quotes: {e}")
            return []
    
    def get_signals(self, limit: int = 20) -> List[Dict]:
        """Get recent AI signals"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, signal, confidence, reasons, technical_data, created_at
                FROM signals ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            signals = cursor.fetchall()
            conn.close()
            
            result = []
            for signal in signals:
                result.append({
                    'symbol': signal[0],
                    'signal': signal[1],
                    'confidence': signal[2],
                    'reasons': json.loads(signal[3]) if signal[3] else [],
                    'technical_data': json.loads(signal[4]) if signal[4] else {},
                    'created_at': signal[5]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
    
    async def start_live_trading(self):
        """Start the live trading system"""
        logger.info("Starting live trading system...")
        
        # Start live data feed
        await self.data_manager.start_live_feed(self.watchlist)

# Flask App for Live Dashboard
app = Flask(__name__)
app.config['SECRET_KEY'] = 'live_trading_secret_key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Live Trading Manager
trading_manager = LiveTradingManager()

@app.route('/')
def dashboard():
    """Live trading dashboard"""
    return render_template('live_dashboard.html')

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio with real-time values"""
    portfolio = trading_manager.get_portfolio()
    return jsonify(portfolio)

@app.route('/api/quotes')
def get_quotes():
    """Get live quotes"""
    quotes = trading_manager.get_live_quotes()
    return jsonify(quotes)

@app.route('/api/signals')
def get_signals():
    """Get AI signals"""
    signals = trading_manager.get_signals()
    return jsonify(signals)

@app.route('/api/watchlist')
def get_watchlist():
    """Get watchlist symbols"""
    return jsonify(trading_manager.watchlist)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Dashboard client connected')
    emit('portfolio_update', trading_manager.get_portfolio())
    emit('quotes_update', trading_manager.get_live_quotes())
    emit('signals_update', trading_manager.get_signals())

# Setup real-time updates
def setup_realtime_updates():
    """Setup real-time dashboard updates"""
    def on_signal_update(signal):
        socketio.emit('signal_update', signal)
    
    def on_portfolio_update():
        socketio.emit('portfolio_update', trading_manager.get_portfolio())
    
    trading_manager.signal_listeners.append(on_signal_update)

if __name__ == '__main__':
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Create the live dashboard HTML
    dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 LIVE Trading Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .live-indicator { color: #28a745; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .price-up { color: #28a745; font-weight: bold; }
        .price-down { color: #dc3545; font-weight: bold; }
        .signal-buy { background: linear-gradient(45deg, #28a745, #20c997); color: white; }
        .signal-sell { background: linear-gradient(45deg, #dc3545, #e74c3c); color: white; }
        .signal-hold { background: linear-gradient(45deg, #6c757d, #adb5bd); color: white; }
        .portfolio-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .quotes-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
        .signals-card { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; }
        .card { border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .live-price { font-size: 1.2em; font-weight: bold; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-fire"></i> LIVE Trading Dashboard
                <span class="live-indicator ms-2"><i class="fas fa-circle"></i> LIVE</span>
            </span>
            <span class="navbar-text" id="connection-status">
                <i class="fas fa-wifi text-success"></i> Connected
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Portfolio Overview -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card portfolio-card">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-wallet"></i> Portfolio</h5>
                        <h3 id="total-value">Rs.10,00,000</h3>
                        <p class="mb-1">Cash: Rs.<span id="cash-balance">10,00,000</span></p>
                        <p class="mb-0">P&L: Rs.<span id="total-pnl">0</span> (<span id="total-pnl-percent">0%</span>)</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card quotes-card">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-chart-line"></i> Live Quotes</h5>
                        <h3 id="quotes-count">0</h3>
                        <p class="mb-0">Real-time Updates</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card signals-card">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-brain"></i> AI Signals</h5>
                        <h3 id="signals-count">0</h3>
                        <p class="mb-0">AI Generated</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h5><i class="fas fa-clock"></i> Market Status</h5>
                        <h3 id="market-status">OPEN</h3>
                        <p class="mb-0" id="market-time">Live Updates</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Live Quotes -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="fas fa-tachometer-alt"></i> Live Market Quotes</h5>
                        <span class="badge bg-success">Real-time</span>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Price</th>
                                        <th>Change</th>
                                        <th>Change %</th>
                                        <th>Volume</th>
                                        <th>High</th>
                                        <th>Low</th>
                                        <th>Updated</th>
                                    </tr>
                                </thead>
                                <tbody id="quotes-table">
                                    <tr>
                                        <td colspan="8" class="text-center text-muted">Loading live quotes...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Signals -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="fas fa-robot"></i> AI Trading Signals</h5>
                        <span class="badge bg-primary">AI Powered</span>
                    </div>
                    <div class="card-body">
                        <div class="row" id="signals-container">
                            <div class="col-12 text-center text-muted">
                                Loading AI signals...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <script>
        const socket = io();
        
        // Socket events
        socket.on('connect', function() {
            document.getElementById('connection-status').innerHTML = 
                '<i class="fas fa-wifi text-success"></i> Connected';
        });
        
        socket.on('portfolio_update', function(data) {
            updatePortfolio(data);
        });
        
        socket.on('quotes_update', function(data) {
            updateQuotes(data);
        });
        
        socket.on('signals_update', function(data) {
            updateSignals(data);
        });
        
        socket.on('signal_update', function(signal) {
            addNewSignal(signal);
        });
        
        // Update portfolio
        function updatePortfolio(portfolio) {
            document.getElementById('total-value').textContent = 'Rs.' + formatNumber(portfolio.total_value);
            document.getElementById('cash-balance').textContent = formatNumber(portfolio.cash_balance);
            document.getElementById('total-pnl').textContent = formatNumber(portfolio.total_pnl);
            document.getElementById('total-pnl-percent').textContent = portfolio.total_pnl_percent.toFixed(1) + '%';
        }
        
        // Update live quotes
        function updateQuotes(quotes) {
            const tbody = document.getElementById('quotes-table');
            document.getElementById('quotes-count').textContent = quotes.length;
            
            if (quotes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No live quotes available</td></tr>';
                return;
            }
            
            tbody.innerHTML = quotes.map(quote => {
                const changeClass = quote.change >= 0 ? 'price-up' : 'price-down';
                const changeIcon = quote.change >= 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down';
                
                return `<tr>
                    <td><strong>${quote.symbol}</strong></td>
                    <td class="live-price">Rs.${formatNumber(quote.price)}</td>
                    <td class="${changeClass}">
                        <i class="${changeIcon}"></i> Rs.${formatNumber(Math.abs(quote.change))}
                    </td>
                    <td class="${changeClass}">${quote.change_percent.toFixed(2)}%</td>
                    <td>${formatVolume(quote.volume)}</td>
                    <td>Rs.${formatNumber(quote.high)}</td>
                    <td>Rs.${formatNumber(quote.low)}</td>
                    <td><small>${new Date(quote.updated_at).toLocaleTimeString()}</small></td>
                </tr>`;
            }).join('');
        }
        
        // Update AI signals
        function updateSignals(signals) {
            const container = document.getElementById('signals-container');
            document.getElementById('signals-count').textContent = signals.length;
            
            if (signals.length === 0) {
                container.innerHTML = '<div class="col-12 text-center text-muted">No AI signals available</div>';
                return;
            }
            
            container.innerHTML = signals.slice(0, 12).map(signal => {
                const signalClass = `signal-${signal.signal.toLowerCase()}`;
                const signalIcon = signal.signal === 'BUY' ? 'fas fa-arrow-up' : 
                                 signal.signal === 'SELL' ? 'fas fa-arrow-down' : 'fas fa-minus';
                
                return `<div class="col-md-4 mb-3">
                    <div class="card ${signalClass}">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="${signalIcon}"></i> ${signal.symbol}
                                <span class="badge bg-light text-dark float-end">${signal.confidence}%</span>
                            </h6>
                            <h4>${signal.signal}</h4>
                            <small>
                                ${signal.reasons.slice(0, 2).join(', ')}
                                <br><em>${new Date(signal.created_at).toLocaleTimeString()}</em>
                            </small>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }
        
        // Add new signal (real-time)
        function addNewSignal(signal) {
            // Add notification or highlight effect
            console.log('New signal:', signal);
        }
        
        // Utility functions
        function formatNumber(num) {
            return new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num);
        }
        
        function formatVolume(volume) {
            if (volume >= 10000000) return (volume / 10000000).toFixed(1) + 'Cr';
            if (volume >= 100000) return (volume / 100000).toFixed(1) + 'L';
            if (volume >= 1000) return (volume / 1000).toFixed(1) + 'K';
            return volume.toString();
        }
        
        // Load initial data
        function loadData() {
            fetch('/api/portfolio').then(r => r.json()).then(updatePortfolio);
            fetch('/api/quotes').then(r => r.json()).then(updateQuotes);
            fetch('/api/signals').then(r => r.json()).then(updateSignals);
        }
        
        // Update market time
        function updateMarketTime() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString();
            document.getElementById('market-time').textContent = timeStr;
            
            // Simple market hours check (9:15 AM - 3:30 PM IST)
            const hour = now.getHours();
            const minute = now.getMinutes();
            const isMarketHours = (hour > 9 || (hour === 9 && minute >= 15)) && 
                                 (hour < 15 || (hour === 15 && minute <= 30));
            
            const statusEl = document.getElementById('market-status');
            if (isMarketHours) {
                statusEl.textContent = 'OPEN';
                statusEl.parentElement.className = 'card bg-success text-white';
            } else {
                statusEl.textContent = 'CLOSED';
                statusEl.parentElement.className = 'card bg-danger text-white';
            }
        }
        
        // Initialize
        loadData();
        updateMarketTime();
        
        // Refresh data every 5 seconds
        setInterval(loadData, 5000);
        setInterval(updateMarketTime, 1000);
    </script>
</body>
</html>
    '''
    
    with open('templates/live_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print("🔥 LIVE TRADING SYSTEM")
    print("=" * 60)
    print("🌐 Dashboard: http://localhost:5000")
    print("💰 Virtual Balance: Rs.10,00,000")
    print("🤖 AI Signals: Real-time generation")
    print("📊 Live Data: Yahoo Finance + Multiple sources")
    print("🔄 Updates: Every 1 second")
    print("=" * 60)
    print("Starting live data feed and AI signal generation...")
    
    # Setup real-time updates
    setup_realtime_updates()
    
    # Start background tasks
    def start_background_tasks():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(trading_manager.start_live_trading())
    
    # Start background thread for live data
    import threading
    background_thread = threading.Thread(target=start_background_tasks, daemon=True)
    background_thread.start()
    
    # Start Flask app
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Live trading system stopped by user")
        trading_manager.data_manager.stop_live_feed()
    except Exception as e:
        print(f"\n❌ System error: {e}")
