#!/usr/bin/env python3
"""
🌐 Web Dashboard for AI Trading Bot
Real-time monitoring, analytics, and control interface
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, send_from_directory
from flask_socketio import SocketIO, emit
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import asyncio
import threading
import time
from config import Config
from database.database_manager import DatabaseManager
from data.data_provider import DataProvider
from analysis.technical_analysis import TechnicalAnalysis
from ai.signal_generator import AISignalGenerator
from utils.logger import logger
import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class TradingDashboard:
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager(self.config)
        self.data_provider = DataProvider()
        self.technical_analyzer = TechnicalAnalysis(self.config)
        self.ai_generator = AISignalGenerator()
        
    def serialize_datetime(self, obj):
        """Convert datetime objects and numpy types to JSON serializable formats"""
        try:
            if isinstance(obj, dict):
                return {key: self.serialize_datetime(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [self.serialize_datetime(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):  # Handle pandas NaN values
                return None
            elif hasattr(obj, 'item'):  # numpy scalars
                return obj.item()
            else:
                return obj
        except Exception:
            # Fallback: convert to string if all else fails
            return str(obj)
        
    def get_dashboard_data(self):
        """Get comprehensive dashboard data"""
        try:
            # Get recent signals
            signals = self.db_manager.get_recent_signals(limit=50)
            
            # Get performance metrics
            performance = self.get_performance_metrics()
            
            # Get active watchlist
            watchlist = self.get_watchlist_data()
            
            # Get market overview
            market_overview = self.get_market_overview()
            
            data = {
                'signals': signals,
                'performance': performance,
                'watchlist': watchlist,
                'market_overview': market_overview,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Serialize datetime objects for JSON compatibility
            return self.serialize_datetime(data)
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            
            # Overall stats
            total_signals = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM signals", conn
            ).iloc[0]['count']
            
            # Today's signals
            today_signals = pd.read_sql_query(
                """SELECT COUNT(*) as count FROM signals 
                   WHERE DATE(timestamp) = DATE('now')""", conn
            ).iloc[0]['count']
            
            # Accuracy calculation
            completed_signals = pd.read_sql_query(
                """SELECT signal_type, profit_loss FROM signals 
                   WHERE status = 'completed' AND profit_loss IS NOT NULL""", conn
            )
            
            accuracy = 0
            if not completed_signals.empty:
                profitable = len(completed_signals[completed_signals['profit_loss'] > 0])
                accuracy = (profitable / len(completed_signals)) * 100
            
            # Recent profit/loss
            recent_pnl = pd.read_sql_query(
                """SELECT SUM(profit_loss) as total_pnl FROM signals 
                   WHERE status = 'completed' AND DATE(timestamp) >= DATE('now', '-7 days')""", conn
            ).iloc[0]['total_pnl'] or 0
            
            conn.close()
            
            return {
                'total_signals': total_signals,
                'today_signals': today_signals,
                'accuracy': round(accuracy, 2),
                'recent_pnl': round(recent_pnl, 2),
                'status': 'Active' if datetime.now().hour >= 9 and datetime.now().hour <= 15 else 'Inactive'
            }
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def get_watchlist_data(self):
        """Get current watchlist with live data"""
        try:
            watchlist = Config.NIFTY_50_SYMBOLS[:10]  # Top 10 for dashboard
            watchlist_data = []
            
            for symbol in watchlist:
                try:
                    # Get current price data
                    df = self.data_provider.get_historical_data(symbol, 'minute', 1)
                    if not df.empty:
                        current_price = df.iloc[-1]['close']
                        prev_close = df.iloc[-2]['close'] if len(df) > 1 else current_price
                        change = current_price - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close > 0 else 0
                        
                        watchlist_data.append({
                            'symbol': symbol,
                            'price': round(current_price, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'status': 'up' if change > 0 else 'down' if change < 0 else 'neutral'
                        })
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {e}")
                    continue
            
            return watchlist_data
        except Exception as e:
            logger.error(f"Error getting watchlist data: {e}")
            return []
    
    def get_market_overview(self):
        """Get overall market overview"""
        try:
            # Market indices (using major stocks as proxy)
            indices = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY']
            market_data = []
            
            for index in indices:
                try:
                    df = self.data_provider.get_historical_data(index, 'day', 2)
                    if len(df) >= 2:
                        current = df.iloc[-1]['close']
                        previous = df.iloc[-2]['close']
                        change_percent = ((current - previous) / previous) * 100
                        
                        market_data.append({
                            'name': index,
                            'value': round(current, 2),
                            'change': round(change_percent, 2)
                        })
                except Exception:
                    continue
            
            return market_data
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return []
    
    def get_chart_data(self, symbol, timeframe='day', days=30):
        """Get chart data for a symbol"""
        try:
            df = self.data_provider.get_historical_data(symbol, timeframe, days)
            if df.empty:
                return {}
            
            # Create candlestick chart data
            chart_data = {
                'x': df.index.strftime('%Y-%m-%d %H:%M:%S').tolist(),
                'open': df['open'].tolist(),
                'high': df['high'].tolist(),
                'low': df['low'].tolist(),
                'close': df['close'].tolist(),
                'volume': df['volume'].tolist()
            }
            
            # Add technical indicators
            analysis = self.technical_analyzer.analyze_all_indicators(df)
            if analysis:
                chart_data['rsi'] = analysis.get('rsi', [])
                chart_data['sma_20'] = analysis.get('sma_20', [])
                chart_data['ema_12'] = analysis.get('ema_12', [])
            
            return chart_data
        except Exception as e:
            logger.error(f"Error getting chart data for {symbol}: {e}")
            return {}

# Initialize dashboard
dashboard = TradingDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/mobile')
def mobile():
    """Mobile-optimized dashboard page"""
    return render_template('mobile.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    data = dashboard.get_dashboard_data()
    return jsonify(data)

@app.route('/api/chart/<symbol>')
def api_chart(symbol):
    """API endpoint for chart data"""
    timeframe = request.args.get('timeframe', 'day')
    days = int(request.args.get('days', 30))
    data = dashboard.get_chart_data(symbol, timeframe, days)
    return jsonify(data)

@app.route('/api/signals')
def api_signals():
    """API endpoint for recent signals"""
    limit = int(request.args.get('limit', 20))
    signals = dashboard.db_manager.get_recent_signals(limit=limit)
    return jsonify(signals)

@app.route('/api/performance')
def api_performance():
    """API endpoint for performance metrics"""
    performance = dashboard.get_performance_metrics()
    return jsonify(performance)

@app.route('/api/watchlist')
def api_watchlist():
    """API endpoint for watchlist data"""
    watchlist = dashboard.get_watchlist_data()
    return jsonify(watchlist)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to dashboard")
    emit('status', {'msg': 'Connected to AI Trading Bot Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from dashboard")

@socketio.on('request_update')
def handle_update_request():
    """Handle real-time update request"""
    try:
        data = dashboard.get_dashboard_data()
        emit('dashboard_update', data)
    except Exception as e:
        logger.error(f"Error handling update request: {e}")
        emit('error', {'message': 'Failed to get dashboard data'})

def background_updates():
    """Background thread for real-time updates"""
    while True:
        try:
            data = dashboard.get_dashboard_data()
            socketio.emit('dashboard_update', data)
            time.sleep(10)  # Update every 10 seconds
        except Exception as e:
            logger.error(f"Error in background updates: {e}")
            time.sleep(30)  # Wait longer if there's an error
            socketio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in background updates: {e}")
            socketio.sleep(60)

if __name__ == '__main__':
    print("🌐 Starting AI Trading Bot Web Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    
    # Start background updates
    socketio.start_background_task(background_updates)
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
