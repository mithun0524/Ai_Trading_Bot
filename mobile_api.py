#!/usr/bin/env python3
"""
📱 Mobile API Server for AI Trading Bot
RESTful API optimized for mobile applications
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
from config import Config
from database.database_manager import DatabaseManager
from data.data_provider import DataProvider
from utils.logger import logger

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile apps

class MobileAPI:
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager(self.config)
        self.data_provider = DataProvider()
        self.secret_key = "your-mobile-app-secret-key"
    
    def generate_token(self, user_id):
        """Generate JWT token for mobile authentication"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_mobile_dashboard(self):
        """Get mobile-optimized dashboard data"""
        try:
            # Get essential metrics for mobile
            performance = self.get_mobile_performance()
            recent_signals = self.db_manager.get_recent_signals(limit=5)
            top_watchlist = self.get_top_watchlist(limit=5)
            
            return {
                'performance': performance,
                'recent_signals': recent_signals,
                'watchlist': top_watchlist,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting mobile dashboard: {e}")
            return {'error': str(e)}
    
    def get_mobile_performance(self):
        """Get mobile-optimized performance metrics"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            
            # Today's performance
            today_signals = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM signals WHERE DATE(created_at) = DATE('now')", conn
            ).iloc[0]['count']
            
            # Weekly P&L
            weekly_pnl = pd.read_sql_query(
                """SELECT SUM(profit_loss) as total FROM signals 
                   WHERE status = 'completed' AND DATE(created_at) >= DATE('now', '-7 days')""", conn
            ).iloc[0]['total'] or 0
            
            # Current accuracy
            accuracy_data = pd.read_sql_query(
                """SELECT signal_type, profit_loss FROM signals 
                   WHERE status = 'completed' AND profit_loss IS NOT NULL
                   AND DATE(created_at) >= DATE('now', '-30 days')""", conn
            )
            
            accuracy = 0
            if not accuracy_data.empty:
                profitable = len(accuracy_data[accuracy_data['profit_loss'] > 0])
                accuracy = (profitable / len(accuracy_data)) * 100
            
            # Bot status
            last_signal = pd.read_sql_query(
                "SELECT created_at FROM signals ORDER BY created_at DESC LIMIT 1", conn
            )
            
            is_active = False
            if not last_signal.empty:
                last_time = pd.to_datetime(last_signal.iloc[0]['created_at'])
                is_active = (datetime.now() - last_time).total_seconds() < 3600  # Active if signal in last hour
            
            conn.close()
            
            return {
                'today_signals': today_signals,
                'weekly_pnl': round(weekly_pnl, 2),
                'accuracy': round(accuracy, 1),
                'bot_status': 'active' if is_active else 'inactive',
                'market_status': self.get_market_status()
            }
        except Exception as e:
            logger.error(f"Error getting mobile performance: {e}")
            return {}
    
    def get_top_watchlist(self, limit=5):
        """Get top performing symbols for mobile"""
        try:
            watchlist = []
            symbols = Config.SYMBOLS[:limit]
            
            for symbol in symbols:
                try:
                    df = self.data_provider.get_historical_data(symbol, 'day', 2)
                    if len(df) >= 2:
                        current = df.iloc[-1]['close']
                        previous = df.iloc[-2]['close']
                        change_percent = ((current - previous) / previous) * 100
                        
                        watchlist.append({
                            'symbol': symbol,
                            'price': round(current, 2),
                            'change_percent': round(change_percent, 2),
                            'trend': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'neutral'
                        })
                except Exception:
                    continue
            
            return sorted(watchlist, key=lambda x: abs(x['change_percent']), reverse=True)
        except Exception as e:
            logger.error(f"Error getting top watchlist: {e}")
            return []
    
    def get_market_status(self):
        """Get current market status"""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        if market_open <= now <= market_close and now.weekday() < 5:
            return 'open'
        else:
            return 'closed'
    
    def get_signal_history(self, limit=20, signal_type=None):
        """Get signal history for mobile"""
        try:
            query = "SELECT * FROM signals ORDER BY created_at DESC"
            params = []
            
            if signal_type:
                query = "SELECT * FROM signals WHERE signal_type = ? ORDER BY created_at DESC"
                params = [signal_type]
            
            if limit:
                query += f" LIMIT {limit}"
            
            conn = sqlite3.connect('trading_bot.db')
            signals = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return signals.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting signal history: {e}")
            return []
    
    def get_portfolio_summary(self):
        """Get portfolio summary for mobile"""
        try:
            conn = sqlite3.connect('trading_bot.db')
            
            # Total portfolio value (mock data for demo)
            portfolio_value = 100000  # Starting portfolio
            
            # Get total P&L
            total_pnl = pd.read_sql_query(
                "SELECT SUM(profit_loss) as total FROM signals WHERE status = 'completed'", conn
            ).iloc[0]['total'] or 0
            
            current_value = portfolio_value + total_pnl
            
            # Get monthly performance
            monthly_pnl = pd.read_sql_query(
                """SELECT SUM(profit_loss) as total FROM signals 
                   WHERE status = 'completed' AND DATE(created_at) >= DATE('now', '-30 days')""", conn
            ).iloc[0]['total'] or 0
            
            # Get win rate
            completed_signals = pd.read_sql_query(
                "SELECT profit_loss FROM signals WHERE status = 'completed' AND profit_loss IS NOT NULL", conn
            )
            
            win_rate = 0
            if not completed_signals.empty:
                wins = len(completed_signals[completed_signals['profit_loss'] > 0])
                win_rate = (wins / len(completed_signals)) * 100
            
            conn.close()
            
            return {
                'initial_value': portfolio_value,
                'current_value': round(current_value, 2),
                'total_pnl': round(total_pnl, 2),
                'monthly_pnl': round(monthly_pnl, 2),
                'win_rate': round(win_rate, 1),
                'return_percentage': round((total_pnl / portfolio_value) * 100, 2)
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}

# Initialize mobile API
mobile_api = MobileAPI()

@app.route('/api/mobile/auth', methods=['POST'])
def mobile_auth():
    """Mobile authentication endpoint"""
    data = request.get_json()
    
    # Simple authentication (in production, use proper authentication)
    if data.get('username') == 'trader' and data.get('password') == 'trading123':
        token = mobile_api.generate_token('mobile_user')
        return jsonify({
            'success': True,
            'token': token,
            'expires_in': 30 * 24 * 3600  # 30 days
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/mobile/dashboard')
def mobile_dashboard():
    """Mobile dashboard endpoint"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    user_id = mobile_api.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = mobile_api.get_mobile_dashboard()
    return jsonify(data)

@app.route('/api/mobile/signals')
def mobile_signals():
    """Mobile signals endpoint"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    user_id = mobile_api.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    limit = request.args.get('limit', 20, type=int)
    signal_type = request.args.get('type')
    
    signals = mobile_api.get_signal_history(limit, signal_type)
    return jsonify({'signals': signals})

@app.route('/api/mobile/portfolio')
def mobile_portfolio():
    """Mobile portfolio endpoint"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    user_id = mobile_api.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    portfolio = mobile_api.get_portfolio_summary()
    return jsonify(portfolio)

@app.route('/api/mobile/watchlist')
def mobile_watchlist():
    """Mobile watchlist endpoint"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    user_id = mobile_api.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    limit = request.args.get('limit', 10, type=int)
    watchlist = mobile_api.get_top_watchlist(limit)
    return jsonify({'watchlist': watchlist})

@app.route('/api/mobile/status')
def mobile_status():
    """Mobile status endpoint"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    user_id = mobile_api.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    status = {
        'bot_status': 'active',
        'market_status': mobile_api.get_market_status(),
        'last_update': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    return jsonify(status)

if __name__ == '__main__':
    print("📱 Starting Mobile API Server...")
    print("Mobile API will be available at: http://localhost:5001")
    print("\nAuthentication:")
    print("Username: trader")
    print("Password: trading123")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
