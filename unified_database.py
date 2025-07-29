#!/usr/bin/env python3
"""
🗄️ UNIFIED DATABASE MANAGER
Centralized database operations for the entire trading platform
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from unified_config import config

# Setup logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    symbol: str
    side: str  # BUY/SELL
    quantity: int
    price: float
    timestamp: datetime
    order_id: Optional[int] = None
    signal_id: Optional[int] = None

@dataclass
class PositionRecord:
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float

@dataclass
@dataclass
class SignalRecord:
    symbol: str
    signal_type: str  # BUY/SELL/HOLD
    confidence: float
    reasoning: List[str]
    technical_data: Dict[str, Any]
    timestamp: datetime

@dataclass
class OrderRecord:
    order_id: str
    symbol: str
    order_type: str  # MARKET/LIMIT/STOP_LOSS
    side: str  # BUY/SELL
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    status: str = "PENDING"  # PENDING/FILLED/CANCELLED/REJECTED
    commission: float = 0.0
    timestamp: datetime = None
    filled_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class UnifiedDatabaseManager:
    """Centralized database manager for all platform data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "unified_trading_platform.db"
        self.init_database()
        logger.info(f"Database manager initialized: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize all database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # ================================
            # PORTFOLIO MANAGEMENT TABLES
            # ================================
            
            # Portfolio overview
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_balance REAL NOT NULL DEFAULT 1000000.0,
                    invested_value REAL NOT NULL DEFAULT 0.0,
                    total_value REAL NOT NULL DEFAULT 1000000.0,
                    unrealized_pnl REAL NOT NULL DEFAULT 0.0,
                    realized_pnl REAL NOT NULL DEFAULT 0.0,
                    day_pnl REAL NOT NULL DEFAULT 0.0,
                    total_pnl REAL NOT NULL DEFAULT 0.0,
                    total_trades INTEGER NOT NULL DEFAULT 0,
                    winning_trades INTEGER NOT NULL DEFAULT 0,
                    losing_trades INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Individual positions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL UNIQUE,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL NOT NULL DEFAULT 0.0,
                    invested_amount REAL NOT NULL,
                    current_value REAL NOT NULL DEFAULT 0.0,
                    unrealized_pnl REAL NOT NULL DEFAULT 0.0,
                    realized_pnl REAL NOT NULL DEFAULT 0.0,
                    first_buy_date TIMESTAMP,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # ================================
            # TRADING TABLES
            # ================================
            
            # All orders (buy/sell)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    order_type TEXT NOT NULL DEFAULT 'MARKET',
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    requested_price REAL,
                    executed_price REAL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    signal_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (signal_id) REFERENCES signals (id)
                )
            ''')
            
            # Executed trades
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    commission REAL DEFAULT 0.0,
                    net_amount REAL NOT NULL,
                    pnl REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            ''')
            
            # ================================
            # AI SIGNALS TABLES
            # ================================
            
            # AI generated signals
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    technical_data TEXT NOT NULL,
                    source TEXT DEFAULT 'AI',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            # Signal performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    pnl_percentage REAL,
                    duration_hours REAL,
                    outcome TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signals (id)
                )
            ''')
            
            # ================================
            # LIVE DATA TABLES
            # ================================
            
            # Real-time market quotes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    price REAL NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    volume INTEGER DEFAULT 0,
                    change_amount REAL NOT NULL,
                    change_percentage REAL NOT NULL,
                    last_trade_time TIMESTAMP,
                    data_source TEXT DEFAULT 'YAHOO',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Historical price data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    low_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    volume INTEGER DEFAULT 0,
                    adj_close REAL,
                    timeframe TEXT DEFAULT 'daily',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date, timeframe)
                )
            ''')
            
            # ================================
            # TECHNICAL ANALYSIS TABLES
            # ================================
            
            # Technical indicators cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    indicator_name TEXT NOT NULL,
                    indicator_value REAL NOT NULL,
                    timeframe TEXT DEFAULT 'daily',
                    calculation_date DATE NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, indicator_name, calculation_date, timeframe)
                )
            ''')
            
            # ================================
            # SYSTEM TABLES
            # ================================
            
            # System events and logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    severity TEXT DEFAULT 'INFO',
                    component TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Application settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ================================
            # NOTIFICATION TABLES
            # ================================
            
            # Notification history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    priority TEXT DEFAULT 'normal',
                    data TEXT,
                    recipient TEXT,
                    status TEXT DEFAULT 'PENDING',
                    sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ================================
            # INITIALIZE DEFAULT DATA
            # ================================
            
            # Initialize portfolio if empty
            cursor.execute('SELECT COUNT(*) FROM portfolio')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO portfolio (cash_balance, total_value) 
                    VALUES (?, ?)
                ''', (config.INITIAL_VIRTUAL_BALANCE, config.INITIAL_VIRTUAL_BALANCE))
            
            # Initialize default settings
            default_settings = [
                ('platform_version', config.VERSION, 'Platform version'),
                ('last_startup', datetime.now().isoformat(), 'Last system startup'),
                ('total_startups', '1', 'Total number of system startups')
            ]
            
            for key, value, desc in default_settings:
                cursor.execute('''
                    INSERT OR IGNORE INTO app_settings (setting_key, setting_value, description)
                    VALUES (?, ?, ?)
                ''', (key, value, desc))
            
            # Create indexes for better performance
            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)',
                'CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)',
                'CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at)',
                'CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)',
                'CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at)',
                'CREATE INDEX IF NOT EXISTS idx_live_quotes_symbol ON live_quotes(symbol)',
                'CREATE INDEX IF NOT EXISTS idx_price_history_symbol_date ON price_history(symbol, date)',
                'CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol ON technical_indicators(symbol)'
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # ================================
    # PORTFOLIO OPERATIONS
    # ================================
    
    def get_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio status"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                # Return default portfolio
                return {
                    'cash_balance': config.INITIAL_VIRTUAL_BALANCE,
                    'total_value': config.INITIAL_VIRTUAL_BALANCE,
                    'total_pnl': 0.0,
                    'day_pnl': 0.0
                }
        finally:
            conn.close()
    
    def update_portfolio(self, **kwargs):
        """Update portfolio with new values"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get current portfolio
            portfolio = self.get_portfolio()
            
            # Update with new values
            portfolio.update(kwargs)
            portfolio['updated_at'] = datetime.now()
            
            # Insert new portfolio record
            cursor.execute('''
                INSERT INTO portfolio 
                (cash_balance, invested_value, total_value, unrealized_pnl, realized_pnl, 
                 day_pnl, total_pnl, total_trades, winning_trades, losing_trades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                portfolio.get('cash_balance', 0),
                portfolio.get('invested_value', 0),
                portfolio.get('total_value', 0),
                portfolio.get('unrealized_pnl', 0),
                portfolio.get('realized_pnl', 0),
                portfolio.get('day_pnl', 0),
                portfolio.get('total_pnl', 0),
                portfolio.get('total_trades', 0),
                portfolio.get('winning_trades', 0),
                portfolio.get('losing_trades', 0)
            ))
            
            conn.commit()
            logger.info("Portfolio updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_positions(self) -> pd.DataFrame:
        """Get all current positions"""
        conn = self.get_connection()
        try:
            query = """
            SELECT * FROM positions 
            WHERE quantity != 0 
            ORDER BY symbol
            """
            return pd.read_sql_query(query, conn)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        try:
            portfolio = self.get_portfolio()
            positions_df = self.get_positions()
            
            summary = {
                'total_value': portfolio.get('total_value', config.INITIAL_VIRTUAL_BALANCE),
                'cash_balance': portfolio.get('cash_balance', config.INITIAL_VIRTUAL_BALANCE),
                'invested_value': portfolio.get('invested_value', 0),
                'total_pnl': portfolio.get('total_pnl', 0),
                'day_pnl': portfolio.get('day_pnl', 0),
                'total_trades': portfolio.get('total_trades', 0),
                'winning_trades': portfolio.get('winning_trades', 0),
                'losing_trades': portfolio.get('losing_trades', 0),
                'positions_count': len(positions_df),
                'active_symbols': positions_df['symbol'].tolist() if not positions_df.empty else []
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {
                'total_value': config.INITIAL_VIRTUAL_BALANCE,
                'cash_balance': config.INITIAL_VIRTUAL_BALANCE,
                'invested_value': 0,
                'total_pnl': 0,
                'day_pnl': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'positions_count': 0,
                'active_symbols': []
            }
    
    # ================================
    # TRADING OPERATIONS
    # ================================
    
    def create_order(self, symbol: str, side: str, quantity: int, 
                    price: float = None, order_type: str = 'MARKET',
                    signal_id: int = None) -> int:
        """Create a new order"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO orders 
                (symbol, order_type, side, quantity, requested_price, executed_price, 
                 status, signal_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, order_type, side.upper(), quantity, price, price, 'EXECUTED', signal_id))
            
            order_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Order created: {order_id} - {side} {quantity} {symbol} @ {price}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def execute_trade(self, order_id: int, executed_price: float) -> int:
        """Execute a trade from an order"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Get order details
            cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
            order = cursor.fetchone()
            
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Calculate trade details
            amount = order['quantity'] * executed_price
            commission = amount * 0.001  # 0.1% commission
            net_amount = amount + commission if order['side'] == 'BUY' else amount - commission
            
            # Create trade record
            cursor.execute('''
                INSERT INTO trades 
                (order_id, symbol, side, quantity, price, amount, commission, net_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, order['symbol'], order['side'], order['quantity'], 
                  executed_price, amount, commission, net_amount))
            
            trade_id = cursor.lastrowid
            
            # Update order status
            cursor.execute('''
                UPDATE orders 
                SET status = 'EXECUTED', executed_price = ?, executed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (executed_price, order_id))
            
            conn.commit()
            logger.info(f"Trade executed: {trade_id} for order {order_id}")
            return trade_id
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            conn.rollback()
            return None
    
    def store_order(self, order: OrderRecord):
        """Store order record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO orders (
                        order_id, symbol, order_type, side, quantity, 
                        price, stop_price, status, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order.order_id, order.symbol, order.order_type, order.side,
                    order.quantity, order.price, order.stop_price, 
                    order.status, order.timestamp
                ))
                
                conn.commit()
                logger.debug(f"Stored order: {order.order_id}")
                
        except Exception as e:
            logger.error(f"Error storing order: {e}")
    
    def update_order(self, order: OrderRecord):
        """Update order record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE orders SET
                        filled_quantity = ?, filled_price = ?, status = ?,
                        commission = ?, filled_timestamp = ?
                    WHERE order_id = ?
                ''', (
                    order.filled_quantity, order.filled_price, order.status,
                    order.commission, order.filled_timestamp, order.order_id
                ))
                
                conn.commit()
                logger.debug(f"Updated order: {order.order_id}")
                
        except Exception as e:
            logger.error(f"Error updating order: {e}")
    
    def get_orders(self, status: str = None, limit: int = 100) -> pd.DataFrame:
        """Get orders with optional status filter"""
        try:
            with self.get_connection() as conn:
                if status:
                    query = '''
                        SELECT * FROM orders 
                        WHERE status = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(status, limit))
                else:
                    query = '''
                        SELECT * FROM orders 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    '''
                    df = pd.read_sql_query(query, conn, params=(limit,))
                
                return df
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    # ================================
    # SIGNAL OPERATIONS
    # ================================
    
    def store_signal(self, signal: SignalRecord) -> int:
        """Store AI-generated signal"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO signals 
                (symbol, signal_type, confidence, reasoning, technical_data, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                signal.symbol,
                signal.signal_type,
                signal.confidence,
                json.dumps(signal.reasoning),
                json.dumps(signal.technical_data),
                'AI'
            ))
            
            signal_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Signal stored: {signal_id} - {signal.signal_type} {signal.symbol}")
            return signal_id
            
        except Exception as e:
            logger.error(f"Error storing signal: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_recent_signals(self, limit: int = 20) -> List[Dict]:
        """Get recent AI signals"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM signals 
                WHERE is_active = TRUE 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            signals = []
            for row in cursor.fetchall():
                signal = dict(row)
                signal['reasoning'] = json.loads(signal['reasoning'])
                signal['technical_data'] = json.loads(signal['technical_data'])
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
        finally:
            conn.close()
    
    def get_signals(self, limit: int = 50) -> List[Dict]:
        """Get signals for web dashboard"""
        return self.get_recent_signals(limit)
    
    def get_trades(self, limit: int = 100) -> pd.DataFrame:
        """Get recent trades"""
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM trades 
                    ORDER BY created_at DESC 
                    LIMIT ?
                '''
                return pd.read_sql_query(query, conn, params=(limit,))
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return pd.DataFrame()
    
    # ================================
    # MARKET DATA OPERATIONS
    # ================================
    
    def store_live_quote(self, symbol: str, quote_data: Dict[str, Any]):
        """Store live market quote"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO live_quotes 
                (symbol, price, open_price, high_price, low_price, volume,
                 change_amount, change_percentage, last_trade_time, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                quote_data.get('price', 0),
                quote_data.get('open', 0),
                quote_data.get('high', 0),
                quote_data.get('low', 0),
                quote_data.get('volume', 0),
                quote_data.get('change', 0),
                quote_data.get('change_percent', 0),
                quote_data.get('timestamp'),
                quote_data.get('source', 'YAHOO')
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing quote for {symbol}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_live_quotes(self, symbols: List[str] = None) -> List[Dict]:
        """Get latest live quotes"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            if symbols:
                placeholders = ','.join(['?' for _ in symbols])
                query = f'''
                    SELECT * FROM live_quotes 
                    WHERE symbol IN ({placeholders})
                    AND id IN (
                        SELECT MAX(id) FROM live_quotes 
                        WHERE symbol IN ({placeholders})
                        GROUP BY symbol
                    )
                    ORDER BY created_at DESC
                '''
                cursor.execute(query, symbols + symbols)
            else:
                cursor.execute('''
                    SELECT * FROM live_quotes 
                    WHERE id IN (
                        SELECT MAX(id) FROM live_quotes GROUP BY symbol
                    )
                    ORDER BY created_at DESC
                ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting live quotes: {e}")
            return []
        finally:
            conn.close()
    
    # ================================
    # UTILITY METHODS
    # ================================
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('SELECT COUNT(*) as total_trades FROM trades')
            total_trades = cursor.fetchone()['total_trades']
            
            cursor.execute('SELECT COUNT(DISTINCT symbol) as unique_symbols FROM trades')
            unique_symbols = cursor.fetchone()['unique_symbols']
            
            cursor.execute('SELECT SUM(pnl) as total_pnl FROM trades WHERE pnl IS NOT NULL')
            total_pnl = cursor.fetchone()['total_pnl'] or 0
            
            cursor.execute('SELECT COUNT(*) as winning_trades FROM trades WHERE pnl > 0')
            winning_trades = cursor.fetchone()['winning_trades']
            
            cursor.execute('SELECT COUNT(*) as losing_trades FROM trades WHERE pnl < 0')
            losing_trades = cursor.fetchone()['losing_trades']
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'unique_symbols': unique_symbols,
                'total_pnl': total_pnl,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate
            }
            
        except Exception as e:
            logger.error(f"Error getting trading stats: {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to maintain performance"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Clean old live quotes
            cursor.execute('DELETE FROM live_quotes WHERE created_at < ?', (cutoff_date,))
            
            # Clean old system events
            cursor.execute('DELETE FROM system_events WHERE created_at < ?', (cutoff_date,))
            
            conn.commit()
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")
            conn.rollback()
        finally:
            conn.close()

# Create global database instance
db = UnifiedDatabaseManager()

if __name__ == "__main__":
    print("🗄️ UNIFIED DATABASE MANAGER")
    print("=" * 50)
    
    # Test database operations
    print("Testing database operations...")
    
    # Test portfolio
    portfolio = db.get_portfolio()
    print(f"✅ Portfolio: Rs.{portfolio.get('cash_balance', 0):,.2f}")
    
    # Test stats
    stats = db.get_trading_stats()
    print(f"✅ Total trades: {stats.get('total_trades', 0)}")
    
    print("✅ Database manager ready!")
    print("=" * 50)
