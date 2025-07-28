#!/usr/bin/env python3
"""
Database Health Check Script
"""

import sqlite3
import os
from datetime import datetime

def check_database():
    print('🔍 Database Health Check')
    print('=' * 50)
    
    db_file = 'trading_bot.db'
    
    if not os.path.exists(db_file):
        print('❌ Database file not found')
        return False
    
    file_size = os.path.getsize(db_file) / 1024  # KB
    print(f'📊 Database file size: {file_size:.2f} KB')
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            print(f'📋 Tables found: {table_names}')
            
            # Check signals table
            if 'signals' in table_names:
                print('\n🔍 Signals Table Analysis:')
                
                # Get table schema
                cursor.execute("PRAGMA table_info(signals);")
                columns = cursor.fetchall()
                print('   Columns:')
                for col in columns:
                    print(f'     - {col[1]} ({col[2]})')
                
                # Count total signals
                cursor.execute("SELECT COUNT(*) FROM signals;")
                total_signals = cursor.fetchone()[0]
                print(f'   📊 Total signals: {total_signals}')
                
                # Count active signals
                cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'ACTIVE';")
                active_signals = cursor.fetchone()[0]
                print(f'   🟢 Active signals: {active_signals}')
                
                # Show recent signals
                print('\n📈 Recent Signals (last 5):')
                cursor.execute("""
                    SELECT id, symbol, signal_type, entry_price, confidence_score, 
                           timestamp, status 
                    FROM signals 
                    ORDER BY id DESC 
                    LIMIT 5;
                """)
                recent = cursor.fetchall()
                
                if recent:
                    for signal in recent:
                        confidence = signal[4] * 100 if signal[4] and signal[4] <= 1 else signal[4]
                        print(f'     ID: {signal[0]}, {signal[1]}, {signal[2]}, '
                              f'₹{signal[3]:.2f}, {confidence:.1f}%, {signal[6]}')
                else:
                    print('     No signals found')
            
            # Check other tables
            for table in ['market_data', 'performance_metrics', 'bot_logs']:
                if table in table_names:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    print(f'📊 {table}: {count} records')
            
            print('\n✅ Database is healthy and functional!')
            return True
            
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

if __name__ == "__main__":
    check_database()
