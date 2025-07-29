#!/usr/bin/env python3
"""
🔍 Stock Symbol Validator
Tests which stock symbols have live data available
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def test_symbol(symbol):
    """Test if a stock symbol has live data"""
    try:
        # Try with .NS suffix first (NSE)
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(period="1d", interval="1m")
        
        if not data.empty:
            latest = data.iloc[-1]
            return {
                'symbol': symbol,
                'status': '✅ ACTIVE',
                'price': f"Rs.{latest['Close']:.2f}",
                'volume': f"{latest['Volume']:,}",
                'suffix': '.NS'
            }
        else:
            # Try without suffix
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    'symbol': symbol,
                    'status': '✅ ACTIVE',
                    'price': f"${latest['Close']:.2f}",
                    'volume': f"{latest['Volume']:,}",
                    'suffix': 'None'
                }
            else:
                return {
                    'symbol': symbol,
                    'status': '❌ NO DATA',
                    'price': 'N/A',
                    'volume': 'N/A',
                    'suffix': 'N/A'
                }
                
    except Exception as e:
        return {
            'symbol': symbol,
            'status': f'❌ ERROR: {str(e)[:50]}',
            'price': 'N/A',
            'volume': 'N/A',
            'suffix': 'N/A'
        }

def main():
    """Test all symbols"""
    print("🔍 STOCK SYMBOL VALIDATOR")
    print("=" * 60)
    
    # Test symbols
    test_symbols = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT',
        'HCLTECH', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA',
        'WIPRO', 'TITAN', 'NESTLEIND', 'BAJFINANCE', 'ULTRACEMCO'
    ]
    
    print(f"Testing {len(test_symbols)} symbols...")
    print()
    
    results = []
    for symbol in test_symbols:
        print(f"Testing {symbol}...", end=" ")
        result = test_symbol(symbol)
        results.append(result)
        print(result['status'])
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    # Show results in table format
    print(f"{'Symbol':<12} {'Status':<15} {'Price':<15} {'Volume':<12} {'Suffix'}")
    print("-" * 60)
    
    active_symbols = []
    for result in results:
        print(f"{result['symbol']:<12} {result['status']:<15} {result['price']:<15} {result['volume']:<12} {result['suffix']}")
        if '✅ ACTIVE' in result['status']:
            active_symbols.append(result['symbol'])
    
    print("\n" + "=" * 60)
    print("✅ RECOMMENDED WATCHLIST (Active Symbols)")
    print("=" * 60)
    
    print("Python list:")
    print("watchlist = [")
    for i, symbol in enumerate(active_symbols[:15]):  # First 15 active symbols
        if i == len(active_symbols[:15]) - 1:
            print(f"    '{symbol}'")
        else:
            print(f"    '{symbol}',")
    print("]")
    
    print(f"\nTotal active symbols found: {len(active_symbols)}")
    print(f"Recommended for watchlist: {min(15, len(active_symbols))}")

if __name__ == "__main__":
    main()
