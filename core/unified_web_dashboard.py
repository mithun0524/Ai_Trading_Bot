#!/usr/bin/env python3
"""
🌐 UNIFIED WEB DASHBOARD
Comprehensive web interface for AI trading platform
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
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
from unified_trading_manager import trading_manager, OrderType

# Setup logging
logger = logging.getLogger(__name__)

# Flask app setup
# Disable default static handler to serve PWA assets from project web/static via custom route
app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Paths for external web assets (PWA, mobile templates)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB_STATIC_DIR = os.path.join(BASE_DIR, 'web', 'static')
WEB_TEMPLATES_DIR = os.path.join(BASE_DIR, 'web', 'templates')

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
            # Get latest quotes from live data manager using the correct method
            quotes_data = live_data_manager.get_cached_quotes()
            
            market_data = []
            quotes_list = []
            for symbol, quote_obj in quotes_data.items():
                if hasattr(quote_obj, 'price'):
                    item = {
                        'symbol': symbol,
                        'price': float(quote_obj.price),
                        'change': float(getattr(quote_obj, 'change', getattr(quote_obj, 'change_percent', 0)) or 0),
                        'change_percent': float(getattr(quote_obj, 'change_percent', 0) or 0),
                        'volume': int(getattr(quote_obj, 'volume', 0) or 0),
                        'timestamp': getattr(quote_obj, 'timestamp', datetime.now()).isoformat()
                    }
                    market_data.append(item)
                    quotes_list.append(item)
                elif isinstance(quote_obj, dict):
                    item = {
                        'symbol': symbol,
                        'price': float(quote_obj.get('price', 0) or 0),
                        'change': float(quote_obj.get('change', quote_obj.get('change_percent', 0)) or 0),
                        'change_percent': float(quote_obj.get('change_percent', 0) or 0),
                        'volume': int(quote_obj.get('volume', 0) or 0),
                        'timestamp': quote_obj.get('timestamp', datetime.now().isoformat())
                    }
                    market_data.append(item)
                    quotes_list.append(item)
            
            # Emit to all connected clients (support both legacy and new events)
            socketio.emit('market_update', market_data)
            socketio.emit('quotes_update', {'quotes': quotes_list})
            
            self.last_update['quotes'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating quotes data: {e}")
    
    def _update_signals_data(self):
        """Update AI signals and emit to clients"""
        try:
            # Get recent signals from database
            signals_data = db.get_signals(limit=20)
            
            if isinstance(signals_data, pd.DataFrame) and not signals_data.empty:
                signals_list = signals_data.to_dict('records')
            else:
                signals_list = signals_data if isinstance(signals_data, list) else []
            
            # Process signals for frontend
            processed_signals = []
            for signal in signals_list:
                processed_signal = {
                    'symbol': signal.get('symbol', ''),
                    'signal_type': signal.get('signal_type', ''),
                    'confidence': signal.get('confidence', 0),
                    'reasoning': signal.get('reasoning', []) if isinstance(signal.get('reasoning'), list) else [],
                    'price': signal.get('price', 0),
                    'created_at': signal.get('created_at', datetime.now().isoformat())
                }
                processed_signals.append(processed_signal)
            
            # Emit to all connected clients (standardize payload shape)
            socketio.emit('signals_update', {'signals': processed_signals})
            
            self.last_update['signals'] = time.time()
            
        except Exception as e:
            logger.error(f"Error updating signals data: {e}")
    
    def _update_orders_data(self):
        """Update orders and trades data and emit to clients"""
        try:
            # Get recent orders
            orders_df = db.get_orders(limit=50)
            orders = []
            if isinstance(orders_df, pd.DataFrame) and not orders_df.empty:
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
            if isinstance(trades_df, pd.DataFrame) and not trades_df.empty:
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
    """Default landing page"""
    return render_template('landing.html')

@app.route('/home')
def landing_page():
    """Public landing page for the app."""
    return render_template('landing.html')

@app.route('/app')
def app_dashboard():
    """Primary application dashboard (clean, dark)."""
    return render_template('clean_dashboard.html')

## Removed legacy/enhanced/mobile routes to keep a single dashboard

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve PWA static assets from web/static."""
    try:
        return send_from_directory(WEB_STATIC_DIR, filename)
    except Exception as e:
        logger.error(f"Static asset not found: {filename} error: {e}")
        return "Not found", 404

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

@app.route('/api/quote/<symbol>')
def api_quote(symbol: str):
    """Get a single live quote for the given symbol."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        quote = loop.run_until_complete(live_data_manager.get_live_quote(symbol.upper()))
        loop.close()
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        data = {
            'symbol': quote.symbol,
            'price': float(quote.price),
            'change': float(getattr(quote, 'change', getattr(quote, 'change_percent', 0)) or 0),
            'change_percent': float(getattr(quote, 'change_percent', 0) or 0),
            'volume': int(getattr(quote, 'volume', 0) or 0),
            'timestamp': quote.timestamp.isoformat() if getattr(quote, 'timestamp', None) else datetime.now().isoformat()
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /api/quote/{symbol}: {e}")
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
        # Broadcast to all connected clients for instant UI update
        try:
            socketio.emit('signals_update', {'signals': signal_data})
        except Exception as emit_err:
            logger.warning(f"Could not emit signals_update: {emit_err}")

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
            order_type=OrderType.MARKET
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

@app.route('/api/watchlist')
def api_watchlist():
    """Return the active watchlist symbols."""
    try:
        symbols = config.get_active_symbols()
        return jsonify({'symbols': symbols, 'count': len(symbols)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        resp = make_response(jsonify({'symbol': symbol, 'data': data_json}))
        # Cache for 5 minutes to avoid hammering the endpoint for sparklines
        resp.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=60'
        return resp
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Socket.IO events
@socketio.on('connect')
def on_connect():
    """Handle client connection"""
    logger.info("Client connected to dashboard")
    emit('status', {'message': 'Connected to AI Trading Platform'})
    
    # Send initial data to new client
    try:
        # Send portfolio data
        portfolio_summary = trading_manager.get_portfolio_summary()
        emit('portfolio_update', portfolio_summary)
        
        # Send latest signals
        signals_data = db.get_signals(limit=10)
        if isinstance(signals_data, pd.DataFrame) and not signals_data.empty:
            signals_list = signals_data.to_dict('records')
        else:
            signals_list = signals_data if isinstance(signals_data, list) else []
        emit('signals_update', {'signals': signals_list})
        
        # Send latest trades
        trades_data = db.get_trades(limit=10)
        if isinstance(trades_data, pd.DataFrame) and not trades_data.empty:
            trades_list = trades_data.to_dict('records')
        else:
            trades_list = trades_data if isinstance(trades_data, list) else []
        emit('trades_update', trades_list)
        
        # Send market data
        try:
            quotes_data = live_data_manager.get_cached_quotes()
            market_data = []
            for symbol, quote_obj in quotes_data.items():
                if hasattr(quote_obj, 'price'):
                    market_data.append({
                        'symbol': symbol,
                        'price': quote_obj.price,
                        'change': getattr(quote_obj, 'change_percent', 0)
                    })
                elif isinstance(quote_obj, dict) and 'price' in quote_obj:
                    market_data.append({
                        'symbol': symbol,
                        'price': quote_obj.get('price', 0),
                        'change': quote_obj.get('change_percent', 0)
                    })
            emit('market_update', market_data[:10])
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
        
        # Send comprehensive dashboard update
        dashboard_data = {
            'portfolio': portfolio_summary,
            'signals': signals_list,
            'trades': trades_list,
            'market': market_data[:10] if 'market_data' in locals() else []
        }
        emit('dashboard_update', dashboard_data)
        
    except Exception as e:
        logger.error(f"Error sending initial data: {e}")
        emit('error', {'message': f'Error loading initial data: {str(e)}'})

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from dashboard")

@socketio.on('request_update')
def on_request_update(data=None):
    """Handle manual update requests"""
    try:
        update_type = 'all'
        if data and isinstance(data, dict):
            update_type = data.get('type', 'all')
        
        dashboard_data = {}
        
        if update_type in ['all', 'portfolio']:
            dashboard_manager._update_portfolio_data()
            portfolio_summary = trading_manager.get_portfolio_summary()
            dashboard_data['portfolio'] = portfolio_summary
            emit('portfolio_update', portfolio_summary)
        
        if update_type in ['all', 'quotes', 'market']:
            dashboard_manager._update_quotes_data()
            try:
                quotes_data = live_data_manager.get_cached_quotes()
                market_data = []
                for symbol, quote_obj in quotes_data.items():
                    if hasattr(quote_obj, 'price'):
                        market_data.append({
                            'symbol': symbol,
                            'price': quote_obj.price,
                            'change': getattr(quote_obj, 'change_percent', 0)
                        })
                    elif isinstance(quote_obj, dict) and 'price' in quote_obj:
                        market_data.append({
                            'symbol': symbol,
                            'price': quote_obj.get('price', 0),
                            'change': quote_obj.get('change_percent', 0)
                        })
                dashboard_data['market'] = market_data[:10]
                emit('market_update', market_data[:10])
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
        
        if update_type in ['all', 'signals']:
            dashboard_manager._update_signals_data()
            signals_data = db.get_signals(limit=10)
            if isinstance(signals_data, pd.DataFrame) and not signals_data.empty:
                signals_list = signals_data.to_dict('records')
            else:
                signals_list = signals_data if isinstance(signals_data, list) else []
            dashboard_data['signals'] = signals_list
            emit('signals_update', {'signals': signals_list})
        
        if update_type in ['all', 'trades']:
            dashboard_manager._update_orders_data()
            trades_data = db.get_trades(limit=10)
            if isinstance(trades_data, pd.DataFrame) and not trades_data.empty:
                trades_list = trades_data.to_dict('records')
            else:
                trades_list = trades_data if isinstance(trades_data, list) else []
            dashboard_data['trades'] = trades_list
            emit('trades_update', trades_list)
        
        # Send comprehensive update
        emit('dashboard_update', dashboard_data)
        emit('status', {'message': f'Updated {update_type} data successfully'})
        
    except Exception as e:
        logger.error(f"Error handling update request: {e}")
        emit('error', {'message': f'Error updating data: {str(e)}'})

@socketio.on('place_order')
def on_place_order(data):
    """Handle order placement via WebSocket"""
    try:
        symbol = data.get('symbol')
        order_type = data.get('type')  # 'BUY' or 'SELL'
        quantity = int(data.get('quantity', 1))
        
        if not symbol or not order_type:
            emit('error', {'message': 'Missing required order parameters'})
            return
        
        # Place order through trading manager
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Use the correct method name and parameters
        result = loop.run_until_complete(
            trading_manager.place_order(
                symbol=symbol,
                side=order_type.upper(),  # 'BUY' or 'SELL'
                quantity=quantity,
                order_type=OrderType.MARKET
            )
        )
        
        loop.close()
        
        if result is not None:
            # result is an Order object
            emit('order_placed', {
                'success': True,
                'message': f'{order_type} order for {quantity} {symbol} placed successfully',
                'order_id': getattr(result, 'order_id', None)
            })
            # Trigger updates
            on_request_update({'type': 'all'})
        else:
            emit('error', {'message': 'Order placement failed'})
            
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        emit('error', {'message': f'Error placing order: {str(e)}'})

# Create templates directory and files

def run_dashboard(host='127.0.0.1', port=5000, debug=False):
    """Run the web dashboard"""
    try:
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
    print("Single dashboard mode (/app) with landing page at /")
    print("=" * 50)
    run_dashboard(debug=True)
