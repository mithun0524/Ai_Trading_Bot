#!/usr/bin/env python3
"""
🎯 Paper Trading API
RESTful API for paper trading system
"""

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.paper_trading_manager import PaperTradingManager
from config import Config
from data.data_provider import DataProvider
from utils.logger import logger

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'paper-trading-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize managers
paper_trading = PaperTradingManager(Config())
data_provider = DataProvider()

@app.route('/')
def paper_trading_dashboard():
    """Main paper trading dashboard"""
    return render_template('paper_trading.html')

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio summary"""
    try:
        portfolio = paper_trading.get_portfolio()
        return jsonify({'success': True, 'data': portfolio})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/positions')
def get_positions():
    """Get all positions"""
    try:
        positions = paper_trading.get_positions()
        return jsonify({'success': True, 'data': positions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/orders')
def get_orders():
    """Get order history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        orders = paper_trading.get_orders(limit=limit)
        return jsonify({'success': True, 'data': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        trades = paper_trading.get_trades(limit=limit)
        return jsonify({'success': True, 'data': trades})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/watchlist')
def get_watchlist():
    """Get watchlist"""
    try:
        watchlist = paper_trading.get_watchlist()
        # Add current prices
        for item in watchlist:
            try:
                df = data_provider.get_historical_data(item['symbol'], 'day', 1)
                if not df.empty:
                    item['current_price'] = df.iloc[-1]['close']
                    item['change'] = df.iloc[-1]['close'] - df.iloc[-1]['open']
                    item['change_percent'] = (item['change'] / df.iloc[-1]['open']) * 100
            except:
                item['current_price'] = 0
                item['change'] = 0
                item['change_percent'] = 0
        
        return jsonify({'success': True, 'data': watchlist})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add symbol to watchlist"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        instrument_type = data.get('instrument_type', 'EQUITY')
        
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol is required'})
        
        success = paper_trading.add_to_watchlist(symbol, instrument_type)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/order/place', methods=['POST'])
def place_order():
    """Place a trading order"""
    try:
        order_data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbol', 'instrument_type', 'order_type', 'side', 'quantity']
        for field in required_fields:
            if field not in order_data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'})
        
        # Place order
        result = paper_trading.place_order(**order_data)
        
        # Emit real-time update
        if result['success']:
            portfolio = paper_trading.get_portfolio()
            positions = paper_trading.get_positions()
            socketio.emit('portfolio_update', {
                'portfolio': portfolio,
                'positions': positions
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/market/quote')
def get_market_quote():
    """Get market quote for a symbol"""
    try:
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol is required'})
        
        # Get recent data
        df = data_provider.get_historical_data(symbol, 'day', 5)
        if df.empty:
            return jsonify({'success': False, 'error': 'No data available'})
        
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        quote = {
            'symbol': symbol,
            'ltp': latest['close'],
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'close': latest['close'],
            'volume': latest['volume'],
            'change': latest['close'] - previous['close'],
            'change_percent': ((latest['close'] - previous['close']) / previous['close']) * 100,
            'timestamp': latest.name.isoformat() if hasattr(latest.name, 'isoformat') else str(latest.name)
        }
        
        return jsonify({'success': True, 'data': quote})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/market/search')
def search_symbols():
    """Search for symbols"""
    try:
        query = request.args.get('q', '').upper()
        if len(query) < 2:
            return jsonify({'success': True, 'data': []})
        
        # Search in NIFTY 50 symbols
        symbols = Config.NIFTY_50_SYMBOLS
        matches = [s for s in symbols if query in s][:10]
        
        results = []
        for symbol in matches:
            try:
                df = data_provider.get_historical_data(symbol, 'day', 1)
                if not df.empty:
                    results.append({
                        'symbol': symbol,
                        'name': symbol,  # You can add company names later
                        'ltp': df.iloc[-1]['close'],
                        'instrument_type': 'EQUITY'
                    })
            except:
                results.append({
                    'symbol': symbol,
                    'name': symbol,
                    'ltp': 0,
                    'instrument_type': 'EQUITY'
                })
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/options/chain')
def get_options_chain():
    """Get options chain for a symbol"""
    try:
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol is required'})
        
        # Get current stock price
        df = data_provider.get_historical_data(symbol, 'day', 1)
        if df.empty:
            return jsonify({'success': False, 'error': 'No data available'})
        
        current_price = df.iloc[-1]['close']
        
        # Generate mock options data (In real implementation, use options data provider)
        options_chain = generate_mock_options_chain(symbol, current_price)
        
        return jsonify({'success': True, 'data': options_chain})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_mock_options_chain(symbol, current_price):
    """Generate mock options chain data"""
    from datetime import datetime, timedelta
    import math
    
    # Generate strike prices around current price
    base_strike = math.floor(current_price / 50) * 50
    strikes = []
    for i in range(-10, 11):
        strikes.append(base_strike + (i * 50))
    
    # Generate expiry dates (next 4 Thursdays)
    today = datetime.now()
    expiries = []
    for i in range(4):
        # Find next Thursday
        days_ahead = 3 - today.weekday()  # Thursday is 3
        if days_ahead <= 0:
            days_ahead += 7
        thursday = today + timedelta(days=days_ahead + (i * 7))
        expiries.append(thursday.strftime('%Y-%m-%d'))
    
    options_data = []
    for expiry in expiries:
        for strike in strikes:
            # Mock option pricing (simplified Black-Scholes approximation)
            moneyness = current_price / strike
            time_to_expiry = 0.25  # Assume 3 months
            
            # Call option
            if moneyness > 1:
                call_price = max(current_price - strike, 0) + (strike * 0.02 * time_to_expiry)
            else:
                call_price = strike * 0.01 * time_to_expiry
            
            # Put option
            if moneyness < 1:
                put_price = max(strike - current_price, 0) + (strike * 0.02 * time_to_expiry)
            else:
                put_price = strike * 0.01 * time_to_expiry
            
            options_data.append({
                'symbol': symbol,
                'expiry': expiry,
                'strike': strike,
                'call_ltp': round(call_price, 2),
                'call_bid': round(call_price * 0.98, 2),
                'call_ask': round(call_price * 1.02, 2),
                'call_volume': 1000,
                'call_oi': 5000,
                'put_ltp': round(put_price, 2),
                'put_bid': round(put_price * 0.98, 2),
                'put_ask': round(put_price * 1.02, 2),
                'put_volume': 800,
                'put_oi': 4000
            })
    
    return {
        'symbol': symbol,
        'underlying_price': current_price,
        'expiries': expiries,
        'options': options_data
    }

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Paper trading client connected")
    emit('status', {'msg': 'Connected to Paper Trading System'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Paper trading client disconnected")

@socketio.on('subscribe_updates')
def handle_subscribe():
    """Subscribe to real-time updates"""
    emit('subscribed', {'msg': 'Subscribed to real-time updates'})

def background_price_updates():
    """Background thread for real-time price updates"""
    while True:
        try:
            # Update position prices
            paper_trading.update_positions_prices()
            
            # Get updated data
            portfolio = paper_trading.get_portfolio()
            positions = paper_trading.get_positions()
            
            # Emit to all connected clients
            socketio.emit('portfolio_update', {
                'portfolio': portfolio,
                'positions': positions,
                'timestamp': datetime.now().isoformat()
            })
            
            time.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in background price updates: {e}")
            time.sleep(60)

if __name__ == "__main__":
    print("🎯 Starting Paper Trading System...")
    print("Dashboard will be available at: http://localhost:5002")
    
    # Start background price updates
    update_thread = threading.Thread(target=background_price_updates, daemon=True)
    update_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
