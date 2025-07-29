#!/usr/bin/env python3
"""
🎯 Paper Trading System
Advanced paper trading with stocks and options
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.logger import logger
    from config import Config
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Mock Config class
    class Config:
        API_KEY = ""
        SECRET_KEY = ""

class PaperTradingManager:
    def __init__(self, config=None):
        self.config = config or Config()
        self.db_file = os.path.join(project_root, 'paper_trading.db')
        self.initial_balance = 1000000  # 10 Lakh virtual money
        self.init_database()
        
    def init_database(self):
        """Initialize paper trading database"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Portfolio table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        balance REAL DEFAULT 1000000,
                        invested_amount REAL DEFAULT 0,
                        total_pnl REAL DEFAULT 0,
                        day_pnl REAL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Positions table (stocks and options)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        symbol TEXT NOT NULL,
                        instrument_type TEXT NOT NULL, -- 'EQUITY', 'OPTION'
                        option_type TEXT, -- 'CE', 'PE' for options
                        strike_price REAL, -- for options
                        expiry_date DATE, -- for options
                        quantity INTEGER NOT NULL,
                        avg_price REAL NOT NULL,
                        current_price REAL,
                        pnl REAL DEFAULT 0,
                        pnl_percent REAL DEFAULT 0,
                        side TEXT NOT NULL, -- 'BUY', 'SELL'
                        status TEXT DEFAULT 'OPEN', -- 'OPEN', 'CLOSED'
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Orders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        symbol TEXT NOT NULL,
                        instrument_type TEXT NOT NULL,
                        option_type TEXT,
                        strike_price REAL,
                        expiry_date DATE,
                        order_type TEXT NOT NULL, -- 'MARKET', 'LIMIT', 'SL', 'SL-M'
                        side TEXT NOT NULL, -- 'BUY', 'SELL'
                        quantity INTEGER NOT NULL,
                        price REAL,
                        trigger_price REAL,
                        filled_quantity INTEGER DEFAULT 0,
                        avg_filled_price REAL DEFAULT 0,
                        status TEXT DEFAULT 'PENDING', -- 'PENDING', 'EXECUTED', 'CANCELLED', 'REJECTED'
                        order_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time DATETIME
                    )
                ''')
                
                # Trades history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        order_id INTEGER,
                        symbol TEXT NOT NULL,
                        instrument_type TEXT NOT NULL,
                        side TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        trade_value REAL NOT NULL,
                        brokerage REAL DEFAULT 0,
                        net_value REAL NOT NULL,
                        trade_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    )
                ''')
                
                # Watchlist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS watchlist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT 'default',
                        symbol TEXT NOT NULL,
                        instrument_type TEXT DEFAULT 'EQUITY',
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Initialize default portfolio if not exists
                cursor.execute('SELECT COUNT(*) FROM portfolio WHERE user_id = ?', ('default',))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO portfolio (user_id, balance, invested_amount, total_pnl, day_pnl)
                        VALUES (?, ?, 0, 0, 0)
                    ''', ('default', self.initial_balance))
                
                conn.commit()
                logger.info("Paper trading database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing paper trading database: {e}")
    
    def get_portfolio(self, user_id='default') -> Dict:
        """Get portfolio summary"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                # Get portfolio basics
                portfolio = pd.read_sql_query(
                    'SELECT * FROM portfolio WHERE user_id = ?', 
                    conn, params=(user_id,)
                ).iloc[0].to_dict()
                
                # Get positions
                positions = pd.read_sql_query(
                    'SELECT * FROM positions WHERE user_id = ? AND status = "OPEN"',
                    conn, params=(user_id,)
                )
                
                # Calculate current portfolio value
                total_position_value = 0
                if not positions.empty:
                    total_position_value = positions['current_price'].fillna(positions['avg_price']) * positions['quantity']
                    total_position_value = total_position_value.sum()
                
                portfolio['positions_value'] = total_position_value
                portfolio['total_value'] = portfolio['balance'] + total_position_value
                portfolio['positions_count'] = len(positions)
                
                return portfolio
                
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {}
    
    def place_order(self, user_id='default', **order_data) -> Dict:
        """Place a paper trading order"""
        try:
            required_fields = ['symbol', 'instrument_type', 'order_type', 'side', 'quantity']
            for field in required_fields:
                if field not in order_data:
                    return {'success': False, 'message': f'Missing required field: {field}'}
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Insert order
                cursor.execute('''
                    INSERT INTO orders (
                        user_id, symbol, instrument_type, option_type, strike_price, 
                        expiry_date, order_type, side, quantity, price, trigger_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    order_data['symbol'],
                    order_data['instrument_type'],
                    order_data.get('option_type'),
                    order_data.get('strike_price'),
                    order_data.get('expiry_date'),
                    order_data['order_type'],
                    order_data['side'],
                    order_data['quantity'],
                    order_data.get('price'),
                    order_data.get('trigger_price')
                ))
                
                order_id = cursor.lastrowid
                
                # For market orders, execute immediately
                if order_data['order_type'] == 'MARKET':
                    execution_result = self._execute_order(cursor, order_id, order_data)
                    if execution_result['success']:
                        cursor.execute(
                            'UPDATE orders SET status = "EXECUTED", execution_time = ? WHERE id = ?',
                            (datetime.now(), order_id)
                        )
                    else:
                        cursor.execute(
                            'UPDATE orders SET status = "REJECTED" WHERE id = ?',
                            (order_id,)
                        )
                        return execution_result
                
                conn.commit()
                return {
                    'success': True, 
                    'message': 'Order placed successfully',
                    'order_id': order_id
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'message': f'Error placing order: {e}'}
    
    def _execute_order(self, cursor, order_id, order_data, execution_price=None):
        """Execute an order (internal method)"""
        try:
            from data.data_provider import DataProvider
            data_provider = DataProvider()
            
            # Get current market price
            if execution_price is None:
                if order_data['instrument_type'] == 'EQUITY':
                    # Get stock price
                    df = data_provider.get_historical_data(order_data['symbol'], 'day', 1)
                    if df.empty:
                        return {'success': False, 'message': 'Unable to get market price'}
                    execution_price = df.iloc[-1]['close']
                else:
                    # For options, you would need options data provider
                    # For now, use strike price as approximation
                    execution_price = order_data.get('price', order_data.get('strike_price', 100))
            
            # Calculate trade value
            trade_value = execution_price * order_data['quantity']
            brokerage = self._calculate_brokerage(trade_value, order_data['instrument_type'])
            net_value = trade_value + brokerage if order_data['side'] == 'BUY' else trade_value - brokerage
            
            # Check if user has sufficient balance for BUY orders
            if order_data['side'] == 'BUY':
                cursor.execute('SELECT balance FROM portfolio WHERE user_id = ?', ('default',))
                balance = cursor.fetchone()[0]
                if balance < net_value:
                    return {'success': False, 'message': 'Insufficient balance'}
            
            # Record trade
            cursor.execute('''
                INSERT INTO trades (
                    user_id, order_id, symbol, instrument_type, side, 
                    quantity, price, trade_value, brokerage, net_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'default', order_id, order_data['symbol'], order_data['instrument_type'],
                order_data['side'], order_data['quantity'], execution_price, 
                trade_value, brokerage, net_value
            ))
            
            # Update portfolio balance
            if order_data['side'] == 'BUY':
                cursor.execute(
                    'UPDATE portfolio SET balance = balance - ?, invested_amount = invested_amount + ? WHERE user_id = ?',
                    (net_value, trade_value, 'default')
                )
            else:
                cursor.execute(
                    'UPDATE portfolio SET balance = balance + ?, invested_amount = invested_amount - ? WHERE user_id = ?',
                    (net_value, trade_value, 'default')
                )
            
            # Update or create position
            self._update_position(cursor, order_data, execution_price)
            
            # Update order as filled
            cursor.execute(
                'UPDATE orders SET filled_quantity = ?, avg_filled_price = ? WHERE id = ?',
                (order_data['quantity'], execution_price, order_id)
            )
            
            return {'success': True, 'message': 'Order executed successfully'}
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {'success': False, 'message': f'Error executing order: {e}'}
    
    def _update_position(self, cursor, order_data, execution_price):
        """Update position after trade"""
        try:
            # Check if position exists
            cursor.execute('''
                SELECT * FROM positions WHERE user_id = ? AND symbol = ? AND instrument_type = ? 
                AND option_type = ? AND strike_price = ? AND expiry_date = ? AND status = "OPEN"
            ''', (
                'default', order_data['symbol'], order_data['instrument_type'],
                order_data.get('option_type'), order_data.get('strike_price'), 
                order_data.get('expiry_date')
            ))
            
            existing_position = cursor.fetchone()
            
            if existing_position:
                # Update existing position
                current_qty = existing_position[7]  # quantity
                current_avg = existing_position[8]  # avg_price
                
                if order_data['side'] == 'BUY':
                    new_qty = current_qty + order_data['quantity']
                    new_avg = ((current_qty * current_avg) + (order_data['quantity'] * execution_price)) / new_qty
                else:
                    new_qty = current_qty - order_data['quantity']
                    new_avg = current_avg  # Keep same average for sells
                
                if new_qty == 0:
                    # Close position
                    cursor.execute('UPDATE positions SET status = "CLOSED" WHERE id = ?', (existing_position[0],))
                else:
                    cursor.execute(
                        'UPDATE positions SET quantity = ?, avg_price = ?, updated_at = ? WHERE id = ?',
                        (new_qty, new_avg, datetime.now(), existing_position[0])
                    )
            else:
                # Create new position
                if order_data['side'] == 'BUY':
                    cursor.execute('''
                        INSERT INTO positions (
                            user_id, symbol, instrument_type, option_type, strike_price,
                            expiry_date, quantity, avg_price, current_price, side
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        'default', order_data['symbol'], order_data['instrument_type'],
                        order_data.get('option_type'), order_data.get('strike_price'),
                        order_data.get('expiry_date'), order_data['quantity'], 
                        execution_price, execution_price, 'BUY'
                    ))
                    
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    def _calculate_brokerage(self, trade_value, instrument_type):
        """Calculate brokerage and charges"""
        if instrument_type == 'EQUITY':
            # Equity: ₹20 or 0.03% whichever is lower
            return min(20, trade_value * 0.0003)
        else:
            # Options: ₹20 per order
            return 20
    
    def get_positions(self, user_id='default') -> List[Dict]:
        """Get all open positions"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                positions = pd.read_sql_query(
                    'SELECT * FROM positions WHERE user_id = ? AND status = "OPEN" ORDER BY created_at DESC',
                    conn, params=(user_id,)
                )
                return positions.to_dict('records') if not positions.empty else []
                
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    def get_orders(self, user_id='default', limit=50) -> List[Dict]:
        """Get order history"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                orders = pd.read_sql_query(
                    'SELECT * FROM orders WHERE user_id = ? ORDER BY order_time DESC LIMIT ?',
                    conn, params=(user_id, limit)
                )
                return orders.to_dict('records') if not orders.empty else []
                
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []
    
    def get_trades(self, user_id='default', limit=50) -> List[Dict]:
        """Get trade history"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                trades = pd.read_sql_query(
                    'SELECT * FROM trades WHERE user_id = ? ORDER BY trade_time DESC LIMIT ?',
                    conn, params=(user_id, limit)
                )
                return trades.to_dict('records') if not trades.empty else []
                
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    def update_positions_prices(self, user_id='default'):
        """Update current prices for all positions"""
        try:
            from data.data_provider import DataProvider
            data_provider = DataProvider()
            
            positions = self.get_positions(user_id)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                for position in positions:
                    try:
                        if position['instrument_type'] == 'EQUITY':
                            # Get current stock price
                            df = data_provider.get_historical_data(position['symbol'], 'day', 1)
                            if not df.empty:
                                current_price = df.iloc[-1]['close']
                                pnl = (current_price - position['avg_price']) * position['quantity']
                                pnl_percent = ((current_price - position['avg_price']) / position['avg_price']) * 100
                                
                                cursor.execute('''
                                    UPDATE positions SET current_price = ?, pnl = ?, pnl_percent = ?, updated_at = ?
                                    WHERE id = ?
                                ''', (current_price, pnl, pnl_percent, datetime.now(), position['id']))
                    except Exception as e:
                        logger.error(f"Error updating price for {position['symbol']}: {e}")
                        continue
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating position prices: {e}")
    
    def get_watchlist(self, user_id='default') -> List[Dict]:
        """Get user watchlist"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                watchlist = pd.read_sql_query(
                    'SELECT * FROM watchlist WHERE user_id = ? ORDER BY added_at DESC',
                    conn, params=(user_id,)
                )
                return watchlist.to_dict('records') if not watchlist.empty else []
                
        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return []
    
    def add_to_watchlist(self, symbol, instrument_type='EQUITY', user_id='default'):
        """Add symbol to watchlist"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR IGNORE INTO watchlist (user_id, symbol, instrument_type) VALUES (?, ?, ?)',
                    (user_id, symbol, instrument_type)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            return False
