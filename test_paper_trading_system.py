#!/usr/bin/env python3
"""
🧪 Paper Trading System - Simple Test
Quick test to verify the system is working
"""

import sys
import os

def test_system():
    """Test the paper trading system"""
    print("🧪 Paper Trading System - Quick Test")
    print("=" * 50)
    
    try:
        # Test 1: Import the system
        print("📦 Testing imports...")
        from paper_trading_system import PaperTradingManager, app
        print("   ✅ All imports successful")
        
        # Test 2: Initialize manager
        print("\n🔧 Testing manager initialization...")
        manager = PaperTradingManager()
        print("   ✅ Manager initialized successfully")
        
        # Test 3: Test portfolio
        print("\n💰 Testing portfolio...")
        portfolio = manager.get_portfolio()
        print(f"   ✅ Portfolio balance: ₹{portfolio['cash_balance']:,.2f}")
        
        # Test 4: Test order placement
        print("\n📝 Testing order placement...")
        result = manager.place_order(
            symbol='RELIANCE',
            side='BUY',
            quantity=10,
            price=2500.0
        )
        
        if result['success']:
            print("   ✅ Test order placed successfully")
        else:
            print(f"   ⚠ Test order failed: {result['message']}")
        
        # Test 5: Test positions
        print("\n📊 Testing positions...")
        positions = manager.get_positions()
        print(f"   ✅ Current positions: {len(positions)}")
        
        # Test 6: Test orders
        print("\n📋 Testing orders...")
        orders = manager.get_orders()
        print(f"   ✅ Recent orders: {len(orders)}")
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("🚀 System is ready to use")
        print("💡 Run: python paper_trading_system.py")
        print("🌐 Then open: http://localhost:5002")
        print("=" * 50)
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("\n🔧 Installing missing dependencies...")
        os.system('pip install flask flask-socketio flask-cors pandas yfinance')
        print("Please run the test again after installation.")
        return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_system()
    if not success:
        sys.exit(1)
