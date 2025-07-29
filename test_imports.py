#!/usr/bin/env python3
"""
Minimal test to find where imports are hanging
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("Testing imports step by step...")

try:
    print("1. Testing unified_config...")
    from core.unified_config import config
    print("✅ unified_config imported")

    print("2. Testing unified_database...")
    from core.unified_database import db
    print("✅ unified_database imported")

    print("3. Testing unified_notifications...")
    from core.unified_notifications import notification_manager
    print("✅ unified_notifications imported")

    print("4. Testing unified_live_data...")
    from core.unified_live_data import live_data_manager
    print("✅ unified_live_data imported")

    print("5. Testing AI signal generator...")
    from ai.signal_generator import AISignalGenerator
    print("✅ AI signal generator imported")

    print("6. Testing unified_trading_manager...")
    from core.unified_trading_manager import trading_manager
    print("✅ unified_trading_manager imported")

    print("7. Testing unified_web_dashboard...")
    from core.unified_web_dashboard import dashboard_manager
    print("✅ unified_web_dashboard imported")

    print("8. Testing main platform...")
    from core.unified_ai_trading_platform import UnifiedTradingPlatform
    print("✅ unified_ai_trading_platform imported")

    print("\n🎉 All imports successful!")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
