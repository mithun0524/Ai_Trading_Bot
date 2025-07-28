#!/usr/bin/env python3
"""
Quick Upstox API v2 test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import upstox_client
    from config import Config
    
    print("🧪 Testing Upstox API v2...")
    
    if Config.UPSTOX_ACCESS_TOKEN:
        print("✅ Access token found")
        
        # Configure API client
        configuration = upstox_client.Configuration()
        configuration.access_token = Config.UPSTOX_ACCESS_TOKEN
        
        # Test user profile
        try:
            api_instance = upstox_client.UserApi(upstox_client.ApiClient(configuration))
            profile = api_instance.get_profile(api_version='2.0')
            print(f"✅ Profile: {profile.data.user_name}")
        except Exception as e:
            print(f"❌ Profile error: {e}")
        
        # Test market data - check available methods
        try:
            api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(configuration))
            print(f"📋 Available methods: {[m for m in dir(api_instance) if not m.startswith('_')]}")
            
            # Try different method names
            methods_to_try = ['get_market_data_feed_authorize', 'ltp', 'get_market_data']
            for method_name in methods_to_try:
                if hasattr(api_instance, method_name):
                    print(f"✅ Found method: {method_name}")
                    method = getattr(api_instance, method_name)
                    try:
                        result = method("NSE_EQ:RELIANCE", api_version='2.0')
                        print(f"✅ {method_name} worked: {result}")
                        break
                    except Exception as e:
                        print(f"❌ {method_name} failed: {e}")
        except Exception as e:
            print(f"❌ Market data error: {e}")
            
        # Test historical data
        try:
            api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(configuration))
            history = api_instance.get_historical_candle_data(
                "NSE:RELIANCE",
                "1day", 
                "2025-01-20",
                "2025-01-27",
                api_version='2.0'
            )
            print(f"✅ Historical data: {len(history.data.candles) if history.data else 0} candles")
        except Exception as e:
            print(f"❌ Historical data error: {e}")
    else:
        print("❌ No access token")
        
except ImportError:
    print("❌ upstox_client not installed")
except Exception as e:
    print(f"❌ General error: {e}")

print("\n🎯 Test completed!")
