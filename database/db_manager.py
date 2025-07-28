import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import logger

class DatabaseManager:
    def __init__(self, db_path: str = "trading_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Signals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        entry_price REAL NOT NULL,
                        target_price REAL,
                        stop_loss REAL,
                        confidence_score REAL,
                        reason TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'ACTIVE',
                        exit_price REAL,
                        exit_timestamp DATETIME,
                        profit_loss REAL
                    )
                ''')
                
                # Market data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        volume INTEGER,
                        timeframe TEXT
                    )
                ''')
                
                # Performance metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE,
                        total_signals INTEGER,
                        successful_signals INTEGER,
                        win_percentage REAL,
                        total_profit_loss REAL,
                        avg_profit_loss REAL
                    )
                ''')
                
                # Watchlist table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS watchlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT UNIQUE NOT NULL,
                        instrument_type TEXT,
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def insert_signal(self, signal_data: Dict) -> int:
        """Insert a new trading signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO signals (symbol, signal_type, entry_price, target_price, 
                                       stop_loss, confidence_score, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_data['symbol'],
                    signal_data['signal_type'],
                    signal_data['entry_price'],
                    signal_data.get('target_price'),
                    signal_data.get('stop_loss'),
                    signal_data['confidence_score'],
                    signal_data.get('reason', '')
                ))
                signal_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Signal inserted with ID: {signal_id}")
                return signal_id
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
            return None
    
    def update_signal_exit(self, signal_id: int, exit_price: float, exit_time: datetime = None):
        """Update signal with exit information"""
        try:
            if exit_time is None:
                exit_time = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get signal details
                cursor.execute('SELECT entry_price, signal_type FROM signals WHERE id = ?', (signal_id,))
                result = cursor.fetchone()
                
                if result:
                    entry_price, signal_type = result
                    
                    # Calculate P&L
                    if signal_type.upper() == 'BUY':
                        profit_loss = exit_price - entry_price
                    else:  # SELL
                        profit_loss = entry_price - exit_price
                    
                    # Update signal
                    cursor.execute('''
                        UPDATE signals 
                        SET exit_price = ?, exit_timestamp = ?, profit_loss = ?, status = 'CLOSED'
                        WHERE id = ?
                    ''', (exit_price, exit_time, profit_loss, signal_id))
                    
                    conn.commit()
                    logger.info(f"Signal {signal_id} updated with exit price: {exit_price}")
                    return profit_loss
                    
        except Exception as e:
            logger.error(f"Error updating signal exit: {e}")
            return None
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM signals WHERE status = 'ACTIVE'
                    ORDER BY timestamp DESC
                ''')
                
                columns = [description[0] for description in cursor.description]
                signals = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return signals
                
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    def get_performance_stats(self, days: int = 30) -> Dict:
        """Get performance statistics for the last N days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_signals,
                        AVG(profit_loss) as avg_profit_loss,
                        SUM(profit_loss) as total_profit_loss,
                        COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_signals
                    FROM signals 
                    WHERE timestamp >= datetime('now', '-{} days')
                    AND status = 'CLOSED'
                '''.format(days))
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    total, winning, avg_pl, total_pl, closed = result
                    win_rate = (winning / closed * 100) if closed > 0 else 0
                    
                    return {
                        'total_signals': total,
                        'winning_signals': winning,
                        'win_rate': round(win_rate, 2),
                        'avg_profit_loss': round(avg_pl, 2) if avg_pl else 0,
                        'total_profit_loss': round(total_pl, 2) if total_pl else 0,
                        'closed_signals': closed
                    }
                else:
                    return {
                        'total_signals': 0,
                        'winning_signals': 0,
                        'win_rate': 0,
                        'avg_profit_loss': 0,
                        'total_profit_loss': 0,
                        'closed_signals': 0
                    }
                    
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {}
    
    def store_market_data(self, symbol: str, data: Dict, timeframe: str):
        """Store market data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO market_data 
                    (symbol, timestamp, open_price, high_price, low_price, close_price, volume, timeframe)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    data['timestamp'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data.get('volume', 0),
                    timeframe
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get historical market data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT timestamp, open_price, high_price, low_price, close_price, volume
                    FROM market_data 
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                '''
                df = pd.read_sql_query(query, conn, params=(symbol, timeframe, limit))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df.sort_values('timestamp').reset_index(drop=True)
                
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def add_to_watchlist(self, symbol: str, instrument_type: str = 'EQUITY'):
        """Add symbol to watchlist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO watchlist (symbol, instrument_type)
                    VALUES (?, ?)
                ''', (symbol, instrument_type))
                conn.commit()
                logger.info(f"Added {symbol} to watchlist")
                
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
    
    def get_watchlist(self) -> List[str]:
        """Get active watchlist symbols"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT symbol FROM watchlist WHERE is_active = 1')
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return []
