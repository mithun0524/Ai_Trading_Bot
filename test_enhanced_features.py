#!/usr/bin/env python3
"""
🧪 Quick Test for Enhanced Features
Test the new web dashboard and mobile API
"""

import sys
import subprocess
import time
import requests
from threading import Thread

def test_web_dashboard():
    """Test if web dashboard is accessible"""
    print("🌐 Testing Web Dashboard...")
    try:
        # Start web dashboard in background
        process = subprocess.Popen([sys.executable, "web_dashboard.py"], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test if server is running
        try:
            response = requests.get("http://localhost:5000", timeout=5)
            if response.status_code == 200:
                print("✅ Web Dashboard is accessible at http://localhost:5000")
                return True
            else:
                print(f"❌ Web Dashboard returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Web Dashboard is not accessible: {e}")
            return False
        finally:
            # Clean up
            process.terminate()
            
    except Exception as e:
        print(f"❌ Error testing web dashboard: {e}")
        return False

def test_mobile_api():
    """Test if mobile API is accessible"""
    print("📱 Testing Mobile API...")
    try:
        # Start mobile API in background
        process = subprocess.Popen([sys.executable, "mobile_api.py"], 
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test authentication endpoint
        try:
            auth_data = {"username": "trader", "password": "trading123"}
            response = requests.post("http://localhost:5001/api/mobile/auth", 
                                   json=auth_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Mobile API authentication working")
                    print(f"✅ Mobile API is accessible at http://localhost:5001")
                    return True
                else:
                    print("❌ Mobile API authentication failed")
                    return False
            else:
                print(f"❌ Mobile API returned status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Mobile API is not accessible: {e}")
            return False
        finally:
            # Clean up
            process.terminate()
            
    except Exception as e:
        print(f"❌ Error testing mobile API: {e}")
        return False

def test_strategy_import():
    """Test if advanced strategies can be imported"""
    print("🔄 Testing Advanced Strategies...")
    try:
        from strategies.advanced_strategies import AdvancedStrategies, StrategyType
        from config import Config
        
        strategies = AdvancedStrategies(Config())
        print("✅ Advanced Strategies imported successfully")
        print(f"✅ Available strategies: {[s.value for s in StrategyType]}")
        return True
        
    except Exception as e:
        print(f"❌ Error importing strategies: {e}")
        return False

def test_portfolio_manager():
    """Test if portfolio manager can be imported"""
    print("💼 Testing Portfolio Manager...")
    try:
        from portfolio.portfolio_manager import AdvancedPortfolioManager, RiskLevel
        
        portfolio = AdvancedPortfolioManager(initial_capital=100000)
        summary = portfolio.get_portfolio_summary()
        
        print("✅ Portfolio Manager imported successfully")
        print(f"✅ Initial portfolio value: ₹{summary['initial_capital']:,}")
        return True
        
    except Exception as e:
        print(f"❌ Error importing portfolio manager: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Enhanced Features Test Suite")
    print("=" * 50)
    
    tests = [
        ("Strategy Import", test_strategy_import),
        ("Portfolio Manager", test_portfolio_manager),
        ("Web Dashboard", test_web_dashboard),
        ("Mobile API", test_mobile_api)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your enhanced AI Trading Bot is ready!")
        print("\n🚀 To start the system:")
        print("1. Run: python web_dashboard.py")
        print("2. Run: python mobile_api.py")
        print("3. Run: python trading_bot.py")
        print("\n🌐 Access web dashboard at: http://localhost:5000")
        print("📱 Access mobile interface at: http://localhost:5001")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()
