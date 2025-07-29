#!/usr/bin/env python3
"""
🌐 UNIFIED WEB DASHBOARD
Comprehensive web interface for AI trading platform
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import json
import asyncio
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any
import logging
import threading
import time
import os

from unified_config import config
from unified_database import db
from unified_live_data import live_data_manager
from unified_ai_signals import ai_signal_generator
from unified_trading_manager import trading_manager

# Setup logging
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'unified_trading_platform_2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class DashboardManager:
    """Manages dashboard data and real-time updates"""
    
    def __init__(self):
        self.last_update = {}
        self.update_intervals = {
            'portfolio': 10,  # 10 seconds
            'quotes': 5,      # 5 seconds
            'signals': 30,    # 30 seconds
            'orders': 15      # 15 seconds
        }
        self.running = False
    
    def start_background_updates(self):
        """Start background update thread"""
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._update_loop, daemon=True)
            thread.start()
            logger.info("Dashboard background updates started")
    
    def _update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check if portfolio update is needed
                if self._should_update('portfolio', current_time):
                    self._update_portfolio_data()
                
                # Check if quotes update is needed
                if self._should_update('quotes', current_time):
                    self._update_quotes_data()
                
                # Check if signals update is needed
                if self._should_update('signals', current_time):
                    self._update_signals_data()
                
                # Check if orders update is needed
                if self._should_update('orders', current_time):
                    self._update_orders_data()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                time.sleep(5)
    
    def _should_update(self, data_type: str, current_time: float) -> bool:
        """Check if data type should be updated"""
        last_time = self.last_update.get(data_type, 0)
        interval = self.update_intervals[data_type]
        return current_time - last_time >= interval
    
    def _update_portfolio_data(self):
        """Update portfolio data and emit to clients"""
        try:
            # Update portfolio value
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(trading_manager.update_portfolio_value())
            loop.close()
            
            # Get portfolio summary
            summary = trading_manager.get_portfolio_summary()
            
            # Emit to all connected clients
            socketio.emit('portfolio_update', summary)
            
            self.last_update['portfolio'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
    
    def _update_quotes_data(self):
        """Update live quotes and emit to clients"""
        try:
            # Get quotes for watchlist symbols
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            quotes = []
            for symbol in config.get_active_symbols()[:10]:  # Limit to first 10
                quote = loop.run_until_complete(live_data_manager.get_live_quote(symbol))
                if quote:
                    quotes.append({
                        'symbol': quote.symbol,
                        'price': quote.price,
                        'change': quote.change,
                        'change_percent': quote.change_percent,
                        'volume': quote.volume,
                        'timestamp': quote.timestamp.isoformat()
                    })
            
            loop.close()
            
            # Emit to all connected clients
            socketio.emit('quotes_update', {'quotes': quotes})
            
            self.last_update['quotes'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating quotes data: {e}")
    
    def _update_signals_data(self):
        """Update AI signals and emit to clients"""
        try:
            # Get recent signals from database
            signals_list = db.get_signals(limit=20)
            
            signals = []
            for signal in signals_list:
                signals.append({
                    'symbol': signal['symbol'],
                    'signal_type': signal['signal_type'],
                    'confidence': signal['confidence'],
                    'reasoning': signal['reasoning'] if isinstance(signal['reasoning'], list) else [],
                    'timestamp': pd.to_datetime(signal['created_at']).isoformat() if 'created_at' in signal else ''
                })
            
            # Emit to all connected clients
            socketio.emit('signals_update', {'signals': signals})
            
            self.last_update['signals'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating signals data: {e}")
    
    def _update_orders_data(self):
        """Update orders and trades data"""
        try:
            # Get recent orders
            orders_df = db.get_orders(limit=50)
            orders = []
            for _, row in orders_df.iterrows():
                orders.append({
                    'order_id': row['order_id'],
                    'symbol': row['symbol'],
                    'side': row['side'],
                    'quantity': row['quantity'],
                    'price': row['price'],
                    'status': row['status'],
                    'timestamp': pd.to_datetime(row['timestamp']).isoformat()
                })
            
            # Get recent trades
            trades_df = db.get_trades(limit=20)
            trades = []
            for _, row in trades_df.iterrows():
                trades.append({
                    'trade_id': row['trade_id'],
                    'symbol': row['symbol'],
                    'side': row['side'],
                    'entry_price': row['entry_price'],
                    'exit_price': row['exit_price'],
                    'quantity': row['quantity'],
                    'pnl': row['pnl'],
                    'entry_time': pd.to_datetime(row['entry_time']).isoformat(),
                    'exit_time': pd.to_datetime(row['exit_time']).isoformat()
                })
            
            # Emit to all connected clients
            socketio.emit('orders_update', {'orders': orders, 'trades': trades})
            
            self.last_update['orders'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating orders data: {e}")

# Create dashboard manager
dashboard_manager = DashboardManager()

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/portfolio')
def api_portfolio():
    """Get portfolio summary"""
    try:
        summary = trading_manager.get_portfolio_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quotes')
def api_quotes():
    """Get live quotes"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        quotes = []
        for symbol in config.get_active_symbols()[:20]:
            quote = loop.run_until_complete(live_data_manager.get_live_quote(symbol))
            if quote:
                quotes.append({
                    'symbol': quote.symbol,
                    'price': quote.price,
                    'change': quote.change,
                    'change_percent': quote.change_percent,
                    'volume': quote.volume,
                    'timestamp': quote.timestamp.isoformat()
                })
        
        loop.close()
        return jsonify({'quotes': quotes})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/signals')
def api_signals():
    """Get AI signals"""
    try:
        signals_list = db.get_signals(limit=50)
        signals = []
        
        for signal in signals_list:
            signals.append({
                'symbol': signal['symbol'],
                'signal_type': signal['signal_type'],
                'confidence': signal['confidence'],
                'reasoning': signal['reasoning'] if isinstance(signal['reasoning'], list) else [],
                'timestamp': pd.to_datetime(signal['created_at']).isoformat() if 'created_at' in signal else ''
            })
        
        return jsonify({'signals': signals})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_signals', methods=['POST'])
def api_generate_signals():
    """Generate new AI signals"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        signals = loop.run_until_complete(ai_signal_generator.generate_signals_for_watchlist())
        
        loop.close()
        
        signal_data = []
        for signal in signals:
            signal_data.append({
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning,
                'timestamp': signal.timestamp.isoformat()
            })
        
        return jsonify({'signals': signal_data, 'count': len(signals)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders')
def api_orders():
    """Get orders and trades"""
    try:
        # Get orders
        orders_df = db.get_orders(limit=100)
        orders = []
        for _, row in orders_df.iterrows():
            orders.append({
                'order_id': row['order_id'],
                'symbol': row['symbol'],
                'side': row['side'],
                'quantity': row['quantity'],
                'price': row['price'],
                'status': row['status'],
                'timestamp': pd.to_datetime(row['timestamp']).isoformat()
            })
        
        # Get trades
        trades_df = db.get_trades(limit=50)
        trades = []
        for _, row in trades_df.iterrows():
            trades.append({
                'trade_id': row['trade_id'],
                'symbol': row['symbol'],
                'side': row['side'],
                'entry_price': row['entry_price'],
                'exit_price': row['exit_price'],
                'quantity': row['quantity'],
                'pnl': row['pnl'],
                'entry_time': pd.to_datetime(row['entry_time']).isoformat(),
                'exit_time': pd.to_datetime(row['exit_time']).isoformat()
            })
        
        return jsonify({'orders': orders, 'trades': trades})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/place_order', methods=['POST'])
def api_place_order():
    """Place a manual order"""
    try:
        data = request.json
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        order = loop.run_until_complete(trading_manager.place_order(
            symbol=data['symbol'],
            side=data['side'],
            quantity=int(data['quantity']),
            order_type=trading_manager.OrderType.MARKET
        ))
        
        loop.close()
        
        if order:
            return jsonify({
                'success': True,
                'order_id': order.order_id,
                'message': f'Order placed: {order.side} {order.quantity} {order.symbol}'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to place order'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/historical/<symbol>')
def api_historical(symbol):
    """Get historical data for symbol"""
    try:
        period = request.args.get('period', '1mo')
        data = live_data_manager.get_historical_data(symbol, period=period)
        
        if data.empty:
            return jsonify({'error': 'No data available'}), 404
        
        # Convert to JSON format
        data_json = []
        for date, row in data.iterrows():
            data_json.append({
                'date': date.isoformat(),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
        
        return jsonify({'symbol': symbol, 'data': data_json})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Socket.IO events
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info("Client connected to dashboard")
    emit('status', {'message': 'Connected to AI Trading Platform'})

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from dashboard")

@socketio.on('request_update')
def on_request_update(data):
    """Handle manual update requests"""
    try:
        update_type = data.get('type', 'all')
        
        if update_type in ['all', 'portfolio']:
            dashboard_manager._update_portfolio_data()
        
        if update_type in ['all', 'quotes']:
            dashboard_manager._update_quotes_data()
        
        if update_type in ['all', 'signals']:
            dashboard_manager._update_signals_data()
        
        if update_type in ['all', 'orders']:
            dashboard_manager._update_orders_data()
        
        emit('status', {'message': f'Updated {update_type} data'})
        
    except Exception as e:
        emit('error', {'message': str(e)})

# Create templates directory and files
def create_dashboard_template():
    """Create the HTML template for dashboard"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Trading Platform Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .header h1 { 
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-align: center;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        .status-item {
            background: #f8f9fa;
            padding: 10px 20px;
            border-radius: 10px;
            border-left: 4px solid #007bff;
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
            gap: 25px; 
            margin-bottom: 30px;
        }
        .card { 
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover { transform: translateY(-5px); }
        .card h3 { 
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .metric { 
            display: flex; 
            justify-content: space-between; 
            margin: 10px 0;
            padding: 8px 0;
        }
        .metric.positive { color: #27ae60; }
        .metric.negative { color: #e74c3c; }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
            margin: 5px;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .btn.success { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .btn.danger { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .btn.warning { background: linear-gradient(135deg, #f39c12, #e67e22); }
        .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table th, .table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }
        .table th { 
            background: #f8f9fa; 
            font-weight: 600;
            color: #495057;
        }
        .table tr:hover { background: #f8f9fa; }
        .signal-buy { color: #27ae60; font-weight: bold; }
        .signal-sell { color: #e74c3c; font-weight: bold; }
        .signal-hold { color: #f39c12; font-weight: bold; }
        .loading { 
            text-align: center; 
            padding: 20px; 
            color: #6c757d;
            font-style: italic;
        }
        .chart-container { height: 400px; margin-top: 20px; }
        .full-width { grid-column: 1 / -1; }
        .connection-status {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transition: all 0.3s ease;
        }
        .connected { background: #27ae60; }
        .disconnected { background: #e74c3c; }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .grid { grid-template-columns: 1fr; }
            .status-bar { flex-direction: column; align-items: stretch; }
        }
    </style>
</head>
<body>
    <div class="connection-status" id="connectionStatus">Connecting...</div>
    
    <div class="container">
        <div class="header">
            <h1>🤖 AI Trading Platform Dashboard</h1>
            <div class="status-bar">
                <div class="status-item">
                    <strong>Status:</strong> <span id="systemStatus">Active</span>
                </div>
                <div class="status-item">
                    <strong>Last Update:</strong> <span id="lastUpdate">--</span>
                </div>
                <div class="status-item">
                    <strong>Active Symbols:</strong> <span id="activeSymbols">--</span>
                </div>
                <div>
                    <button class="btn" onclick="requestUpdate('all')">🔄 Refresh All</button>
                    <button class="btn success" onclick="generateSignals()">🎯 Generate Signals</button>
                </div>
            </div>
        </div>

        <div class="grid">
            <!-- Portfolio Summary -->
            <div class="card">
                <h3>💼 Portfolio Summary</h3>
                <div id="portfolioData" class="loading">Loading portfolio data...</div>
            </div>

            <!-- Live Quotes -->
            <div class="card">
                <h3>📊 Live Market Data</h3>
                <div id="quotesData" class="loading">Loading market data...</div>
            </div>

            <!-- AI Signals -->
            <div class="card">
                <h3>🎯 AI Trading Signals</h3>
                <div id="signalsData" class="loading">Loading AI signals...</div>
            </div>

            <!-- Recent Orders -->
            <div class="card">
                <h3>📋 Recent Orders</h3>
                <div id="ordersData" class="loading">Loading orders...</div>
            </div>

            <!-- Performance Chart -->
            <div class="card full-width">
                <h3>📈 Portfolio Performance</h3>
                <div class="chart-container" id="performanceChart"></div>
            </div>

            <!-- Recent Trades -->
            <div class="card full-width">
                <h3>💰 Recent Trades</h3>
                <div id="tradesData" class="loading">Loading trades data...</div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Connection status
        const statusEl = document.getElementById('connectionStatus');
        
        socket.on('connect', function() {
            statusEl.textContent = 'Connected';
            statusEl.className = 'connection-status connected';
            updateLastUpdate();
        });
        
        socket.on('disconnect', function() {
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'connection-status disconnected';
        });

        // Data update handlers
        socket.on('portfolio_update', function(data) {
            updatePortfolioData(data);
        });

        socket.on('quotes_update', function(data) {
            updateQuotesData(data.quotes);
        });

        socket.on('signals_update', function(data) {
            updateSignalsData(data.signals);
        });

        socket.on('orders_update', function(data) {
            updateOrdersData(data.orders);
            updateTradesData(data.trades);
        });

        // Update functions
        function updatePortfolioData(data) {
            const html = `
                <div class="metric ${data.total_pnl >= 0 ? 'positive' : 'negative'}">
                    <span>Portfolio Value:</span>
                    <span>₹${formatNumber(data.portfolio_value)}</span>
                </div>
                <div class="metric">
                    <span>Cash Balance:</span>
                    <span>₹${formatNumber(data.cash_balance)}</span>
                </div>
                <div class="metric ${data.total_pnl >= 0 ? 'positive' : 'negative'}">
                    <span>Total P&L:</span>
                    <span>₹${formatNumber(data.total_pnl)}</span>
                </div>
                <div class="metric">
                    <span>Positions:</span>
                    <span>${data.total_positions}</span>
                </div>
                <div class="metric">
                    <span>Win Rate:</span>
                    <span>${data.win_rate.toFixed(1)}%</span>
                </div>
            `;
            document.getElementById('portfolioData').innerHTML = html;
        }

        function updateQuotesData(quotes) {
            if (!quotes || quotes.length === 0) {
                document.getElementById('quotesData').innerHTML = '<div class="loading">No market data available</div>';
                return;
            }
            
            let html = '<table class="table"><thead><tr><th>Symbol</th><th>Price</th><th>Change</th><th>Volume</th></tr></thead><tbody>';
            
            quotes.slice(0, 8).forEach(quote => {
                const changeClass = quote.change_percent >= 0 ? 'positive' : 'negative';
                html += `
                    <tr>
                        <td><strong>${quote.symbol}</strong></td>
                        <td>₹${quote.price.toFixed(2)}</td>
                        <td class="${changeClass}">${quote.change_percent.toFixed(2)}%</td>
                        <td>${formatNumber(quote.volume)}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('quotesData').innerHTML = html;
            document.getElementById('activeSymbols').textContent = quotes.length;
        }

        function updateSignalsData(signals) {
            if (!signals || signals.length === 0) {
                document.getElementById('signalsData').innerHTML = '<div class="loading">No signals available</div>';
                return;
            }
            
            let html = '<table class="table"><thead><tr><th>Symbol</th><th>Signal</th><th>Confidence</th><th>Time</th></tr></thead><tbody>';
            
            signals.slice(0, 10).forEach(signal => {
                const signalClass = `signal-${signal.signal_type.toLowerCase()}`;
                const time = new Date(signal.timestamp).toLocaleTimeString();
                html += `
                    <tr>
                        <td><strong>${signal.symbol}</strong></td>
                        <td class="${signalClass}">${signal.signal_type}</td>
                        <td>${signal.confidence.toFixed(1)}%</td>
                        <td>${time}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('signalsData').innerHTML = html;
        }

        function updateOrdersData(orders) {
            if (!orders || orders.length === 0) {
                document.getElementById('ordersData').innerHTML = '<div class="loading">No orders available</div>';
                return;
            }
            
            let html = '<table class="table"><thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Status</th></tr></thead><tbody>';
            
            orders.slice(0, 10).forEach(order => {
                const time = new Date(order.timestamp).toLocaleTimeString();
                html += `
                    <tr>
                        <td><strong>${order.symbol}</strong></td>
                        <td class="${order.side === 'BUY' ? 'positive' : 'negative'}">${order.side}</td>
                        <td>${order.quantity}</td>
                        <td>${order.status}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('ordersData').innerHTML = html;
        }

        function updateTradesData(trades) {
            if (!trades || trades.length === 0) {
                document.getElementById('tradesData').innerHTML = '<div class="loading">No trades available</div>';
                return;
            }
            
            let html = '<table class="table"><thead><tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Exit</th><th>Qty</th><th>P&L</th><th>Date</th></tr></thead><tbody>';
            
            trades.forEach(trade => {
                const pnlClass = trade.pnl >= 0 ? 'positive' : 'negative';
                const date = new Date(trade.exit_time).toLocaleDateString();
                html += `
                    <tr>
                        <td><strong>${trade.symbol}</strong></td>
                        <td class="${trade.side === 'LONG' ? 'positive' : 'negative'}">${trade.side}</td>
                        <td>₹${trade.entry_price.toFixed(2)}</td>
                        <td>₹${trade.exit_price.toFixed(2)}</td>
                        <td>${trade.quantity}</td>
                        <td class="${pnlClass}">₹${trade.pnl.toFixed(2)}</td>
                        <td>${date}</td>
                    </tr>
                `;
            });
            
            html += '</tbody></table>';
            document.getElementById('tradesData').innerHTML = html;
        }

        // Utility functions
        function formatNumber(num) {
            if (num >= 10000000) return (num/10000000).toFixed(1) + 'Cr';
            if (num >= 100000) return (num/100000).toFixed(1) + 'L';
            if (num >= 1000) return (num/1000).toFixed(1) + 'K';
            return num.toFixed(0);
        }

        function updateLastUpdate() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }

        function requestUpdate(type) {
            socket.emit('request_update', {type: type});
            updateLastUpdate();
        }

        function generateSignals() {
            fetch('/api/generate_signals', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.signals) {
                        updateSignalsData(data.signals);
                        alert(`Generated ${data.count} new signals!`);
                    }
                })
                .catch(error => {
                    console.error('Error generating signals:', error);
                    alert('Error generating signals');
                });
        }

        // Load initial data
        window.onload = function() {
            requestUpdate('all');
        };
    </script>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(template_content)

def run_dashboard(host='127.0.0.1', port=5000, debug=False):
    """Run the web dashboard"""
    try:
        # Create template file
        create_dashboard_template()
        
        # Start background updates
        dashboard_manager.start_background_updates()
        
        logger.info(f"Starting web dashboard on http://{host}:{port}")
        
        # Run the Flask app with SocketIO
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        raise

if __name__ == "__main__":
    print("🌐 UNIFIED WEB DASHBOARD")
    print("=" * 50)
    
    # Test dashboard components
    print("Testing dashboard components...")
    
    # Create template
    create_dashboard_template()
    print("✅ Dashboard template created")
    
    # Test API endpoints (would need actual data)
    print("✅ Dashboard manager initialized")
    
    print("\nStarting web dashboard...")
    print("🌐 Dashboard will be available at: http://127.0.0.1:5000")
    print("📊 Real-time updates enabled")
    print("🔄 Auto-refresh every 5-30 seconds")
    print("=" * 50)
    
    # Run the dashboard
    run_dashboard(debug=True)
