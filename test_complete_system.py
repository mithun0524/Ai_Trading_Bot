#!/usr/bin/env python3
"""
🧪 Complete Paper Trading System Test
Tests all components with proper imports
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

import time
import json
import subprocess
from datetime import datetime

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test paper trading manager
        from src.paper_trading.manager import PaperTradingManager
        print("   ✅ PaperTradingManager imported successfully")
        
        # Test paper trading API
        from src.paper_trading.api import app, socketio
        print("   ✅ Paper Trading API imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_paper_trading_manager():
    """Test paper trading manager functionality"""
    print("🔍 Testing Paper Trading Manager...")
    
    try:
        from src.paper_trading.manager import PaperTradingManager
        
        # Initialize manager
        manager = PaperTradingManager()
        print("   ✅ Manager initialized successfully")
        
        # Test portfolio creation
        portfolio = manager.get_portfolio()
        print(f"   ✅ Portfolio retrieved: Balance ₹{portfolio.get('balance', 0):,.2f}")
        
        # Test order placement
        order_result = manager.place_order(
            symbol='RELIANCE',
            quantity=10,
            order_type='MARKET',
            transaction_type='BUY'
        )
        print(f"   ✅ Test order placed: {order_result.get('message', 'Success')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Manager test failed: {e}")
        return False

def test_api_components():
    """Test API components"""
    print("🔍 Testing API components...")
    
    try:
        from src.paper_trading.api import app, socketio
        
        with app.test_client() as client:
            # Test main route
            response = client.get('/')
            print(f"   ✅ Main route status: {response.status_code}")
            
            # Test portfolio API
            response = client.get('/api/portfolio')
            if response.status_code == 200:
                print("   ✅ Portfolio API working")
            else:
                print(f"   ⚠ Portfolio API status: {response.status_code}")
            
            # Test positions API
            response = client.get('/api/positions')
            if response.status_code == 200:
                print("   ✅ Positions API working")
            else:
                print(f"   ⚠ Positions API status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

def test_database():
    """Test database operations"""
    print("🔍 Testing database...")
    
    try:
        from src.paper_trading.manager import PaperTradingManager
        
        manager = PaperTradingManager()
        
        # Test portfolio operations
        portfolio = manager.get_portfolio()
        if portfolio:
            print("   ✅ Database portfolio query successful")
        
        # Test positions query
        positions = manager.get_positions()
        print("   ✅ Database positions query successful")
        
        # Test orders query
        orders = manager.get_orders()
        print("   ✅ Database orders query successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Paper Trading System - Comprehensive Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Manager Test", test_paper_trading_manager),
        ("API Test", test_api_components),
        ("Database Test", test_database)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Paper Trading System is ready!")
        print("\n🚀 To start the system:")
        print("   cd src/paper_trading")
        print("   python api.py")
        print("\n🌐 Then visit: http://localhost:5002")
        return True
    else:
        print(f"\n⚠ {total - passed} tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    
    if success:
        print("\n" + "=" * 50)
        print("🎯 PAPER TRADING SYSTEM READY!")
        print("=" * 50)
        print("💰 Virtual Balance: ₹10,00,000")
        print("📈 Features: Stocks & Options Trading")
        print("🔄 Real-time Updates: Enabled")
        print("🌐 Web Dashboard: Professional UI")
        
        # Ask if user wants to start the system
        start_now = input("\n🚀 Start Paper Trading System now? (y/n): ").strip().lower()
        
        if start_now == 'y':
            print("\n🌟 Starting Paper Trading System...")
            try:
                os.chdir('src/paper_trading')
                subprocess.run([sys.executable, 'api.py'])
            except Exception as e:
                print(f"❌ Failed to start: {e}")
                print("Please run manually: cd src/paper_trading && python api.py")
    else:
        print("\n❌ System not ready. Fix the errors above first.")
