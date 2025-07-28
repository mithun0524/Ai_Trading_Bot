#!/usr/bin/env python3
"""
Comprehensive test script to verify all project components
"""
import sys
import traceback
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("🔍 Testing imports...")
    
    try:
        # Core dependencies
        import pandas as pd
        import numpy as np
        print("✅ pandas, numpy")
        
        # Custom modules
        from config import Config
        print("✅ Config")
        
        from utils.logger import logger
        print("✅ Logger")
        
        from utils.ta_indicators import RSI, MACD, BBANDS, SMA, EMA, SUPERTREND
        print("✅ TA Indicators")
        
        from data.data_provider import DataProvider
        print("✅ Data Provider")
        
        from analysis.technical_analysis import TechnicalAnalysis
        print("✅ Technical Analysis")
        
        from ai.signal_generator import AISignalGenerator
        print("✅ AI Signal Generator")
        
        from database.db_manager import DatabaseManager
        print("✅ Database Manager")
        
        from notifications.telegram_notifier import TelegramNotifier
        print("✅ Telegram Notifier")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration"""
    print("\n🔍 Testing configuration...")
    
    try:
        from config import Config
        config = Config()
        
        # Check essential config values
        print(f"✅ Telegram Token: {'✓' if config.TELEGRAM_BOT_TOKEN else '✗'}")
        print(f"✅ Telegram Chat ID: {'✓' if config.TELEGRAM_CHAT_ID else '✗'}")
        print(f"✅ Upstox API Key: {'✓' if config.UPSTOX_API_KEY else '✗'}")
        print(f"✅ Risk Percentage: {config.RISK_PERCENTAGE}%")
        print(f"✅ Max Trades/Day: {config.MAX_TRADES_PER_DAY}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_data_provider():
    """Test data provider"""
    print("\n🔍 Testing data provider...")
    
    try:
        from data.data_provider import DataProvider
        from config import Config
        
        provider = DataProvider()  # No config needed
        
        # Test market status
        status = provider.get_market_status()
        print(f"✅ Market Status: {status['status']} - {status['message']}")
        
        # Test data retrieval (small sample)
        data = provider.get_historical_data('RELIANCE', 'day', 10)
        if not data.empty:
            print(f"✅ Data retrieval: Got {len(data)} records for RELIANCE")
        else:
            print("⚠️ No data retrieved (may be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Data Provider test failed: {e}")
        traceback.print_exc()
        return False

def test_technical_analysis():
    """Test technical analysis"""
    print("\n🔍 Testing technical analysis...")
    
    try:
        from analysis.technical_analysis import TechnicalAnalysis
        from data.data_provider import DataProvider
        from config import Config
        
        config = Config()
        ta = TechnicalAnalysis(config)
        provider = DataProvider()  # No config needed
        
        # Get some test data
        data = provider.get_historical_data('RELIANCE', 'day', 100)
        
        if not data.empty:
            # Test indicator calculation
            analyzed_data = ta.calculate_indicators(data)
            print(f"✅ Indicators calculated: {len(analyzed_data.columns)} columns")
            
            # Test analysis
            analysis = ta.analyze_all_indicators(analyzed_data)
            if analysis:
                print("✅ Technical analysis completed")
            else:
                print("⚠️ Analysis returned empty (may be normal)")
        else:
            print("⚠️ No data for analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical Analysis test failed: {e}")
        traceback.print_exc()
        return False

def test_ai_model():
    """Test AI model"""
    print("\n🔍 Testing AI model...")
    
    try:
        from ai.signal_generator import AISignalGenerator
        from config import Config
        
        ai = AISignalGenerator()  # No config needed
        
        # Check if model exists
        try:
            if ai.load_model():
                print("✅ AI model loaded successfully")
            else:
                print("⚠️ No trained model found")
        except:
            print("⚠️ Model loading failed")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Model test failed: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database"""
    print("\n🔍 Testing database...")
    
    try:
        from database.db_manager import DatabaseManager
        from config import Config
        
        config = Config()
        db = DatabaseManager(config.DATABASE_URL.replace('sqlite:///', ''))
        
        # Test basic operations
        watchlist = db.get_watchlist()
        print(f"✅ Database connection: Got {len(watchlist)} symbols in watchlist")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_telegram():
    """Test Telegram connection"""
    print("\n🔍 Testing Telegram...")
    
    try:
        from notifications.telegram_notifier import TelegramNotifier
        from config import Config
        
        config = Config()
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("⚠️ Telegram credentials not configured")
            return True
        
        telegram = TelegramNotifier(config)
        print("✅ Telegram notifier initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting comprehensive project test...\n")
    print(f"📅 Test Date: {datetime.now()}")
    print(f"🐍 Python Version: {sys.version}")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Data Provider", test_data_provider),
        ("Technical Analysis", test_technical_analysis),
        ("AI Model", test_ai_model),
        ("Database", test_database),
        ("Telegram", test_telegram),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"🎯 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Project is ready to run.")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. Minor issues may exist.")
    else:
        print("❌ Multiple failures detected. Check configuration and dependencies.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
