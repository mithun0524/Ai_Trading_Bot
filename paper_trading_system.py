#!/usr/bin/env python3
"""
🎯 Paper Trading System - All-in-One Solution
Complete paper trading system with web interface
"""

import os
import sys
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import logging
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaperTradingManager:
    """Complete Paper Trading Manager"""
    
    def __init__(self, initial_balance: float = 1000000.0):
        """Initialize with ₹10 lakh virtual balance"""
        self.initial_balance = initial_balance
        self.db_path = "paper_trading_system.db"
        self.init_database()
        logger.info("Paper Trading Manager initialized with ₹{:,.2f}".format(initial_balance))
    
    def init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY,
                    cash_balance REAL DEFAULT 1000000.0,
                    total_value REAL DEFAULT 1000000.0,
                    pnl REAL DEFAULT 0.0,
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
                    pnl REAL DEFAULT 0.0,
                    instrument_type TEXT DEFAULT 'EQUITY',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    instrument_type TEXT DEFAULT 'EQUITY',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP
                )
            ''')
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY,
                    order_id INTEGER,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    instrument_type TEXT DEFAULT 'EQUITY',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # Initialize portfolio if empty
            cursor.execute('SELECT COUNT(*) FROM portfolio')
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    'INSERT INTO portfolio (cash_balance, total_value, pnl) VALUES (?, ?, ?)',
                    (self.initial_balance, self.initial_balance, 0.0)
                )
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def get_portfolio(self) -> Dict:
        """Get current portfolio status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT 1')
            portfolio_row = cursor.fetchone()
            
            if not portfolio_row:
                # Create default portfolio
                cursor.execute(
                    'INSERT INTO portfolio (cash_balance, total_value, pnl) VALUES (?, ?, ?)',
                    (self.initial_balance, self.initial_balance, 0.0)
                )
                conn.commit()
                portfolio_row = (1, self.initial_balance, self.initial_balance, 0.0, datetime.now())
            
            conn.close()
            
            return {
                'cash_balance': portfolio_row[1],
                'total_value': portfolio_row[2],
                'pnl': portfolio_row[3],
                'updated_at': portfolio_row[4]
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {
                'cash_balance': self.initial_balance,
                'total_value': self.initial_balance,
                'pnl': 0.0,
                'updated_at': datetime.now()
            }
    
    def place_order(self, symbol: str, side: str, quantity: int, price: float, 
                   order_type: str = 'LIMIT', instrument_type: str = 'EQUITY') -> Dict:
        """Place a trading order"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate order value
            order_value = quantity * price
            
            # Get current portfolio
            portfolio = self.get_portfolio()
            
            # Check if sufficient balance for BUY orders
            if side.upper() == 'BUY' and order_value > portfolio['cash_balance']:
                return {
                    'success': False,
                    'message': f'Insufficient balance. Required: ₹{order_value:,.2f}, Available: ₹{portfolio["cash_balance"]:,.2f}'
                }
            
            # Insert order
            cursor.execute('''
                INSERT INTO orders (symbol, order_type, side, quantity, price, status, instrument_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, order_type, side.upper(), quantity, price, 'EXECUTED', instrument_type))
            
            order_id = cursor.lastrowid
            
            # Execute order immediately (paper trading)
            cursor.execute('''
                INSERT INTO trades (order_id, symbol, side, quantity, price, amount, instrument_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, symbol, side.upper(), quantity, price, order_value, instrument_type))
            
            # Update positions
            if side.upper() == 'BUY':
                # Check if position exists
                cursor.execute('SELECT * FROM positions WHERE symbol = ?', (symbol,))
                existing_position = cursor.fetchone()
                
                if existing_position:
                    # Update existing position
                    old_qty = existing_position[2]
                    old_avg_price = existing_position[3]
                    new_qty = old_qty + quantity
                    new_avg_price = ((old_qty * old_avg_price) + (quantity * price)) / new_qty
                    
                    cursor.execute('''
                        UPDATE positions SET quantity = ?, avg_price = ?, current_price = ?
                        WHERE symbol = ?
                    ''', (new_qty, new_avg_price, price, symbol))
                else:
                    # Create new position
                    cursor.execute('''
                        INSERT INTO positions (symbol, quantity, avg_price, current_price, instrument_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (symbol, quantity, price, price, instrument_type))
                
                # Update cash balance
                new_balance = portfolio['cash_balance'] - order_value
            else:  # SELL
                # Update position
                cursor.execute('SELECT * FROM positions WHERE symbol = ?', (symbol,))
                existing_position = cursor.fetchone()
                
                if existing_position:
                    old_qty = existing_position[2]
                    if old_qty >= quantity:
                        new_qty = old_qty - quantity
                        if new_qty == 0:
                            cursor.execute('DELETE FROM positions WHERE symbol = ?', (symbol,))
                        else:
                            cursor.execute('''
                                UPDATE positions SET quantity = ?, current_price = ?
                                WHERE symbol = ?
                            ''', (new_qty, price, symbol))
                    else:
                        return {
                            'success': False,
                            'message': f'Insufficient shares. Available: {old_qty}, Requested: {quantity}'
                        }
                else:
                    return {
                        'success': False,
                        'message': f'No position found for {symbol}'
                    }
                
                # Update cash balance
                new_balance = portfolio['cash_balance'] + order_value
            
            # Update portfolio
            cursor.execute('''
                UPDATE portfolio SET cash_balance = ?, total_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT MAX(id) FROM portfolio)
            ''', (new_balance, new_balance, ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Order executed: {side} {quantity} {symbol} @ ₹{price}")
            
            return {
                'success': True,
                'message': f'Order executed successfully',
                'order_id': order_id,
                'details': {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'value': order_value
                }
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                'success': False,
                'message': f'Order failed: {str(e)}'
            }
    
    def get_positions(self) -> List[Dict]:
        """Get all current positions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM positions WHERE quantity > 0')
            positions = cursor.fetchall()
            conn.close()
            
            result = []
            for pos in positions:
                result.append({
                    'id': pos[0],
                    'symbol': pos[1],
                    'quantity': pos[2],
                    'avg_price': pos[3],
                    'current_price': pos[4],
                    'pnl': pos[5],
                    'instrument_type': pos[6],
                    'value': pos[2] * pos[4] if pos[4] else pos[2] * pos[3]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, limit: int = 50) -> List[Dict]:
        """Get recent orders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT ?', (limit,))
            orders = cursor.fetchall()
            conn.close()
            
            result = []
            for order in orders:
                result.append({
                    'id': order[0],
                    'symbol': order[1],
                    'order_type': order[2],
                    'side': order[3],
                    'quantity': order[4],
                    'price': order[5],
                    'status': order[6],
                    'instrument_type': order[7],
                    'created_at': order[8]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_market_quote(self, symbol: str) -> Dict:
        """Get real-time market quote"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")  # NSE suffix for Indian stocks
            info = ticker.history(period="1d", interval="1m")
            
            if info.empty:
                # Try without .NS suffix
                ticker = yf.Ticker(symbol)
                info = ticker.history(period="1d", interval="1m")
            
            if not info.empty:
                latest = info.iloc[-1]
                return {
                    'symbol': symbol,
                    'price': float(latest['Close']),
                    'change': float(latest['Close'] - latest['Open']),
                    'change_percent': float((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                    'volume': int(latest['Volume']),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'symbol': symbol,
                    'price': 0.0,
                    'change': 0.0,
                    'change_percent': 0.0,
                    'volume': 0,
                    'error': 'No data available'
                }
                
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {
                'symbol': symbol,
                'price': 0.0,
                'change': 0.0,
                'change_percent': 0.0,
                'volume': 0,
                'error': str(e)
            }

# Flask App Setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'paper_trading_secret_key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Paper Trading Manager
trading_manager = PaperTradingManager()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('paper_trading_dashboard.html')

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio data"""
    portfolio = trading_manager.get_portfolio()
    return jsonify(portfolio)

@app.route('/api/positions')
def get_positions():
    """Get all positions"""
    positions = trading_manager.get_positions()
    return jsonify(positions)

@app.route('/api/orders')
def get_orders():
    """Get recent orders"""
    orders = trading_manager.get_orders()
    return jsonify(orders)

@app.route('/api/quote/<symbol>')
def get_quote(symbol):
    """Get market quote"""
    quote = trading_manager.get_market_quote(symbol)
    return jsonify(quote)

@app.route('/api/place_order', methods=['POST'])
def place_order():
    """Place a trading order"""
    try:
        data = request.get_json()
        
        result = trading_manager.place_order(
            symbol=data['symbol'],
            side=data['side'],
            quantity=int(data['quantity']),
            price=float(data['price']),
            order_type=data.get('order_type', 'LIMIT'),
            instrument_type=data.get('instrument_type', 'EQUITY')
        )
        
        # Emit update to all connected clients
        socketio.emit('portfolio_update', trading_manager.get_portfolio())
        socketio.emit('positions_update', trading_manager.get_positions())
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Order placement error: {str(e)}'
        })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('portfolio_update', trading_manager.get_portfolio())
    emit('positions_update', trading_manager.get_positions())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    # Create templates directory and HTML file
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Trading Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .dashboard-card { margin-bottom: 20px; }
        .portfolio-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .positions-card { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; }
        .trading-card { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
        .status-badge { font-size: 0.8em; }
        .price-up { color: #28a745; }
        .price-down { color: #dc3545; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-chart-line"></i> Paper Trading Dashboard
            </span>
            <span class="navbar-text" id="connection-status">
                <i class="fas fa-wifi text-success"></i> Connected
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- Portfolio Overview -->
        <div class="row">
            <div class="col-md-4">
                <div class="card dashboard-card portfolio-card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-wallet"></i> Portfolio</h5>
                        <h3 id="total-value">₹10,00,000</h3>
                        <p class="mb-1">Cash: ₹<span id="cash-balance">10,00,000</span></p>
                        <p class="mb-0">P&L: ₹<span id="total-pnl">0.00</span></p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card dashboard-card positions-card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-briefcase"></i> Positions</h5>
                        <h3 id="positions-count">0</h3>
                        <p class="mb-0">Active Holdings</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card dashboard-card trading-card">
                    <div class="card-body">
                        <h5 class="card-title"><i class="fas fa-exchange-alt"></i> Trading</h5>
                        <button class="btn btn-light" data-bs-toggle="modal" data-bs-target="#tradingModal">
                            <i class="fas fa-plus"></i> Place Order
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Positions Table -->
        <div class="row">
            <div class="col-12">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-list"></i> Current Positions</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Symbol</th>
                                        <th>Quantity</th>
                                        <th>Avg Price</th>
                                        <th>Current Price</th>
                                        <th>Value</th>
                                        <th>P&L</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="positions-table">
                                    <tr>
                                        <td colspan="7" class="text-center text-muted">No positions found</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Orders -->
        <div class="row">
            <div class="col-12">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-history"></i> Recent Orders</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Symbol</th>
                                        <th>Side</th>
                                        <th>Quantity</th>
                                        <th>Price</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="orders-table">
                                    <tr>
                                        <td colspan="6" class="text-center text-muted">No orders found</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Trading Modal -->
    <div class="modal fade" id="tradingModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Place Order</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="trading-form">
                        <div class="mb-3">
                            <label class="form-label">Symbol</label>
                            <input type="text" class="form-control" id="symbol" placeholder="e.g., RELIANCE" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Side</label>
                            <select class="form-select" id="side" required>
                                <option value="BUY">Buy</option>
                                <option value="SELL">Sell</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Quantity</label>
                            <input type="number" class="form-control" id="quantity" placeholder="100" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Price</label>
                            <input type="number" class="form-control" id="price" placeholder="100.00" step="0.01" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Order Type</label>
                            <select class="form-select" id="order-type">
                                <option value="LIMIT">Limit</option>
                                <option value="MARKET">Market</option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="place-order-btn">Place Order</button>
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
        
        socket.on('disconnect', function() {
            document.getElementById('connection-status').innerHTML = 
                '<i class="fas fa-wifi text-danger"></i> Disconnected';
        });
        
        socket.on('portfolio_update', function(data) {
            updatePortfolio(data);
        });
        
        socket.on('positions_update', function(data) {
            updatePositions(data);
        });
        
        // Update portfolio display
        function updatePortfolio(portfolio) {
            document.getElementById('total-value').textContent = 
                '₹' + formatNumber(portfolio.total_value);
            document.getElementById('cash-balance').textContent = 
                formatNumber(portfolio.cash_balance);
            document.getElementById('total-pnl').textContent = 
                formatNumber(portfolio.pnl);
        }
        
        // Update positions table
        function updatePositions(positions) {
            const tbody = document.getElementById('positions-table');
            document.getElementById('positions-count').textContent = positions.length;
            
            if (positions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No positions found</td></tr>';
                return;
            }
            
            tbody.innerHTML = positions.map(pos => 
                `<tr>
                    <td><strong>${pos.symbol}</strong></td>
                    <td>${pos.quantity}</td>
                    <td>₹${formatNumber(pos.avg_price)}</td>
                    <td>₹${formatNumber(pos.current_price)}</td>
                    <td>₹${formatNumber(pos.value)}</td>
                    <td class="${pos.pnl >= 0 ? 'price-up' : 'price-down'}">
                        ₹${formatNumber(pos.pnl)}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" 
                                onclick="sellPosition('${pos.symbol}', ${pos.quantity})">
                            Sell
                        </button>
                    </td>
                </tr>`
            ).join('');
        }
        
        // Format numbers
        function formatNumber(num) {
            return new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num);
        }
        
        // Place order
        document.getElementById('place-order-btn').addEventListener('click', function() {
            const formData = {
                symbol: document.getElementById('symbol').value.toUpperCase(),
                side: document.getElementById('side').value,
                quantity: document.getElementById('quantity').value,
                price: document.getElementById('price').value,
                order_type: document.getElementById('order-type').value
            };
            
            fetch('/api/place_order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Order placed successfully!');
                    bootstrap.Modal.getInstance(document.getElementById('tradingModal')).hide();
                    document.getElementById('trading-form').reset();
                    loadData();
                } else {
                    alert('Order failed: ' + data.message);
                }
            })
            .catch(error => {
                alert('Error: ' + error.message);
            });
        });
        
        // Sell position
        function sellPosition(symbol, quantity) {
            if (confirm(`Sell ${quantity} shares of ${symbol}?`)) {
                // Get current price first
                fetch(`/api/quote/${symbol}`)
                .then(response => response.json())
                .then(quote => {
                    const sellData = {
                        symbol: symbol,
                        side: 'SELL',
                        quantity: quantity,
                        price: quote.price || 100, // Use market price or default
                        order_type: 'MARKET'
                    };
                    
                    fetch('/api/place_order', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(sellData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Sell order executed!');
                            loadData();
                        } else {
                            alert('Sell failed: ' + data.message);
                        }
                    });
                });
            }
        }
        
        // Load initial data
        function loadData() {
            // Load portfolio
            fetch('/api/portfolio')
                .then(response => response.json())
                .then(data => updatePortfolio(data));
            
            // Load positions
            fetch('/api/positions')
                .then(response => response.json())
                .then(data => updatePositions(data));
            
            // Load orders
            fetch('/api/orders')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('orders-table');
                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No orders found</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.slice(0, 10).map(order => 
                        `<tr>
                            <td>${new Date(order.created_at).toLocaleTimeString()}</td>
                            <td>${order.symbol}</td>
                            <td><span class="badge ${order.side === 'BUY' ? 'bg-success' : 'bg-danger'}">${order.side}</span></td>
                            <td>${order.quantity}</td>
                            <td>₹${formatNumber(order.price)}</td>
                            <td><span class="badge bg-success">${order.status}</span></td>
                        </tr>`
                    ).join('');
                });
        }
        
        // Load data on page load
        loadData();
        
        // Refresh data every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    '''
    
    with open('templates/paper_trading_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("🎯 Paper Trading System - All-in-One")
    print("=" * 50)
    print("🌐 Dashboard: http://localhost:5002")
    print("💰 Virtual Balance: ₹10,00,000")
    print("🔄 Real-time updates enabled")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    
    # Start the Flask app
    try:
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        print("Please check the installation and try again.")
