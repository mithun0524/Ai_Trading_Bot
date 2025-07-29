import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from utils.logger import logger

class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.db_path = getattr(config, 'DATABASE_URL', 'sqlite:///trading_bot.db')
        
        # Extract SQLite database path
        if self.db_path.startswith('sqlite:///'):
            self.db_file = self.db_path.replace('sqlite:///', '')
        else:
            self.db_file = 'trading_bot.db'
        
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.init_database()
        logger.info("Database initialized successfully")
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create signals table
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
                        pnl REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create market_data table for caching
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        open_price REAL,
                        high_price REAL,
                        low_price REAL,
                        close_price REAL,
                        volume INTEGER,
                        interval_type TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create performance_metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE NOT NULL,
                        total_signals INTEGER DEFAULT 0,
                        winning_signals INTEGER DEFAULT 0,
                        losing_signals INTEGER DEFAULT 0,
                        total_pnl REAL DEFAULT 0,
                        win_rate REAL DEFAULT 0,
                        avg_profit REAL DEFAULT 0,
                        avg_loss REAL DEFAULT 0,
                        max_drawdown REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create bot_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL,
                        module TEXT,
                        function TEXT
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)')
                
                conn.commit()
                logger.debug("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_signal(self, signal: Dict) -> int:
        """Insert a new trading signal"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO signals (
                        symbol, signal_type, entry_price, target_price, 
                        stop_loss, confidence_score, reason, timestamp, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.get('symbol'),
                    signal.get('signal_type'),
                    signal.get('entry_price'),
                    signal.get('target_price'),
                    signal.get('stop_loss'),
                    signal.get('confidence_score'),
                    signal.get('reason'),
                    signal.get('timestamp', datetime.now()),
                    signal.get('status', 'ACTIVE')
                ))
                
                signal_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Signal inserted with ID: {signal_id}")
                return signal_id
                
        except Exception as e:
            logger.error(f"Error inserting signal: {e}")
            raise
    
    def update_signal_status(self, signal_id: int, status: str, exit_price: Optional[float] = None) -> bool:
        """Update signal status and exit details"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                if exit_price:
                    # Calculate P&L
                    cursor.execute('SELECT entry_price, signal_type FROM signals WHERE id = ?', (signal_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        entry_price, signal_type = result
                        if signal_type == 'BUY':
                            pnl = ((exit_price - entry_price) / entry_price) * 100
                        else:  # SELL
                            pnl = ((entry_price - exit_price) / entry_price) * 100
                        
                        cursor.execute('''
                            UPDATE signals 
                            SET status = ?, exit_price = ?, exit_timestamp = ?, profit_loss = ?
                            WHERE id = ?
                        ''', (status, exit_price, datetime.now(), pnl, signal_id))
                    else:
                        logger.warning(f"Signal {signal_id} not found")
                        return False
                else:
                    cursor.execute('UPDATE signals SET status = ? WHERE id = ?', (status, signal_id))
                
                conn.commit()
                logger.info(f"Signal {signal_id} updated to status: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating signal status: {e}")
            return False
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals WHERE status = 'ACTIVE'
                    ORDER BY timestamp DESC
                ''')
                
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                signals = []
                for row in results:
                    signal = dict(zip(columns, row))
                    signals.append(signal)
                
                return signals
                
        except Exception as e:
            logger.error(f"Error getting active signals: {e}")
            return []
    
    def get_signals_by_date(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get signals within date range"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals 
                    WHERE timestamp BETWEEN ? AND ?
                    ORDER BY timestamp DESC
                ''', (start_date, end_date))
                
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                signals = []
                for row in results:
                    signal = dict(zip(columns, row))
                    signals.append(signal)
                
                return signals
                
        except Exception as e:
            logger.error(f"Error getting signals by date: {e}")
            return []
    
    def get_recent_signals(self, limit: int = 50) -> List[Dict]:
        """Get recent signals with limit"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM signals 
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                signals = []
                for row in results:
                    signal = dict(zip(columns, row))
                    # Convert timestamp string to datetime if needed
                    if 'timestamp' in signal and isinstance(signal['timestamp'], str):
                        try:
                            signal['timestamp'] = datetime.fromisoformat(signal['timestamp'].replace('Z', '+00:00'))
                        except:
                            pass
                    signals.append(signal)
                
                return signals
                
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    def get_performance_metrics(self, days: int = 30) -> Dict:
        """Get performance metrics for the last N days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Get basic metrics
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_signals,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_signals,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_signals,
                        SUM(profit_loss) as total_pnl,
                        AVG(CASE WHEN profit_loss > 0 THEN profit_loss END) as avg_profit,
                        AVG(CASE WHEN profit_loss < 0 THEN profit_loss END) as avg_loss,
                        MAX(profit_loss) as max_profit,
                        MIN(profit_loss) as max_loss
                    FROM signals 
                    WHERE timestamp BETWEEN ? AND ? AND status != 'ACTIVE'
                ''', (start_date, end_date))
                
                result = cursor.fetchone()
                
                if result and result[0] > 0:  # If we have signals
                    total_signals, winning_signals, losing_signals, total_pnl, avg_profit, avg_loss, max_profit, max_loss = result
                    
                    win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
                    
                    metrics = {
                        'total_signals': total_signals or 0,
                        'winning_signals': winning_signals or 0,
                        'losing_signals': losing_signals or 0,
                        'win_rate': win_rate,
                        'total_pnl': total_pnl or 0,
                        'avg_profit': avg_profit or 0,
                        'avg_loss': avg_loss or 0,
                        'max_profit': max_profit or 0,
                        'max_loss': max_loss or 0,
                        'period_days': days
                    }
                else:
                    # No signals in period
                    metrics = {
                        'total_signals': 0,
                        'winning_signals': 0,
                        'losing_signals': 0,
                        'win_rate': 0,
                        'total_pnl': 0,
                        'avg_profit': 0,
                        'avg_loss': 0,
                        'max_profit': 0,
                        'max_loss': 0,
                        'period_days': days
                    }
                
                return metrics
                
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                'total_signals': 0,
                'winning_signals': 0,
                'losing_signals': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'max_profit': 0,
                'max_loss': 0,
                'period_days': days
            }
    
    def store_market_data(self, symbol: str, data: pd.DataFrame, interval: str):
        """Store market data for caching"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Delete old data for this symbol and interval
                conn.execute('''
                    DELETE FROM market_data 
                    WHERE symbol = ? AND interval_type = ?
                ''', (symbol, interval))
                
                # Insert new data
                for timestamp, row in data.iterrows():
                    conn.execute('''
                        INSERT INTO market_data (
                            symbol, timestamp, open_price, high_price, 
                            low_price, close_price, volume, interval_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        symbol,
                        timestamp,
                        row.get('Open', 0),
                        row.get('High', 0),
                        row.get('Low', 0),
                        row.get('Close', 0),
                        row.get('Volume', 0),
                        interval
                    ))
                
                conn.commit()
                logger.debug(f"Stored {len(data)} records for {symbol}")
                
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    def get_market_data(self, symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
        """Get cached market data"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                query = '''
                    SELECT timestamp, open_price, high_price, low_price, close_price, volume
                    FROM market_data 
                    WHERE symbol = ? AND interval_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
                
                df = pd.read_sql_query(query, conn, params=(symbol, interval, limit))
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    df.rename(columns={
                        'open_price': 'Open',
                        'high_price': 'High',
                        'low_price': 'Low',
                        'close_price': 'Close',
                        'volume': 'Volume'
                    }, inplace=True)
                    df = df.sort_index()
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return pd.DataFrame()
    
    def log_bot_event(self, level: str, message: str, module: str = None, function: str = None):
        """Log bot events to database"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO bot_logs (level, message, module, function)
                    VALUES (?, ?, ?, ?)
                ''', (level, message, module, function))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging bot event: {e}")
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data to keep database size manageable"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Clean old market data
                cursor.execute('DELETE FROM market_data WHERE created_at < ?', (cutoff_date,))
                
                # Clean old bot logs
                cursor.execute('DELETE FROM bot_logs WHERE timestamp < ?', (cutoff_date,))
                
                # Keep signals but we can archive very old ones
                cursor.execute('''
                    UPDATE signals SET status = 'ARCHIVED' 
                    WHERE timestamp < ? AND status != 'ACTIVE'
                ''', (cutoff_date,))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                for table in ['signals', 'market_data', 'performance_metrics', 'bot_logs']:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    stats[f'{table}_count'] = count
                
                # Database file size
                if os.path.exists(self.db_file):
                    stats['file_size_mb'] = round(os.path.getsize(self.db_file) / 1024 / 1024, 2)
                else:
                    stats['file_size_mb'] = 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def export_signals_to_csv(self, filepath: str, days: int = 30) -> bool:
        """Export signals to CSV file"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            signals = self.get_signals_by_date(start_date, end_date)
            
            if signals:
                df = pd.DataFrame(signals)
                df.to_csv(filepath, index=False)
                logger.info(f"Exported {len(signals)} signals to {filepath}")
                return True
            else:
                logger.warning("No signals to export")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting signals: {e}")
            return False
    
    def get_watchlist(self) -> List[str]:
        """Get current watchlist symbols"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Check if watchlist table exists and has data
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist';")
                if cursor.fetchone():
                    cursor.execute("SELECT symbol FROM watchlist WHERE is_active = 1 ORDER BY symbol;")
                    results = cursor.fetchall()
                    if results:
                        return [row[0] for row in results]
                
                # Fallback to config symbols if no watchlist in DB
                from config import Config
                return Config.NIFTY_50_SYMBOLS
                
        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            # Fallback to config symbols
            from config import Config
            return Config.NIFTY_50_SYMBOLS
    
    def add_to_watchlist(self, symbol: str, instrument_type: str = 'EQUITY'):
        """Add symbol to watchlist"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Create watchlist table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS watchlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT UNIQUE NOT NULL,
                        instrument_type TEXT DEFAULT 'EQUITY',
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Insert or update symbol
                cursor.execute('''
                    INSERT OR REPLACE INTO watchlist (symbol, instrument_type, is_active)
                    VALUES (?, ?, 1)
                ''', (symbol, instrument_type))
                
                conn.commit()
                logger.debug(f"Added {symbol} to watchlist")
                
        except Exception as e:
            logger.error(f"Error adding {symbol} to watchlist: {e}")