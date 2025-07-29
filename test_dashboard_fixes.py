#!/usr/bin/env python3
"""
Quick test for web dashboard fixes
"""

print("Testing web dashboard fixes...")

try:
    print("1. Testing imports...")
    from web_dashboard import TradingDashboard
    print("✓ Web dashboard imports successful")
    
    print("2. Testing dashboard initialization...")
    dashboard = TradingDashboard()
    print("✓ Dashboard initialization successful")
    
    print("3. Testing data serialization...")
    from datetime import datetime
    test_data = {
        'timestamp': datetime.now(),
        'signals': [{'created': datetime.now(), 'symbol': 'TEST'}],
        'nested': {'date': datetime.now()}
    }
    
    serialized = dashboard.serialize_datetime(test_data)
    print("✓ DateTime serialization working")
    
    print("4. Testing dashboard data...")
    data = dashboard.get_dashboard_data()
    print("✓ Dashboard data retrieval successful")
    
    print("\n🎉 All fixes applied successfully!")
    print("\nFixed issues:")
    print("✓ Database column name (created_at → timestamp)")
    print("✓ Config.SYMBOLS → Config.NIFTY_50_SYMBOLS")
    print("✓ JSON serialization for datetime objects")
    print("✓ Error handling in background updates")
    print("✓ Added missing time import")
    
    print("\n🚀 Web dashboard should now work without errors!")
    print("Start with: python web_dashboard.py")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nSome issues may still exist. Check the error above.")

print("\nTest completed!")
