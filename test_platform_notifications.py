#!/usr/bin/env python3
"""
Test the unified platform's notification integration
"""

if __name__ == "__main__":
    print("🧪 Testing Platform Notification Integration...")
    
    try:
        print("📦 Importing unified modules...")
        from unified_config import config
        from unified_database import db
        print("✅ Config and database imported")
        
        print("📦 Importing notification manager...")
        from unified_notifications import notification_manager
        print("✅ Notification manager imported")
        
        print(f"📱 Telegram enabled in config: {config.TELEGRAM_ENABLED}")
        print(f"📱 Notifications enabled: {config.ENABLE_NOTIFICATIONS}")
        print(f"📱 Signal threshold: {config.SIGNAL_NOTIFICATION_THRESHOLD}%")
        
        print("📱 Testing startup notification...")
        success = notification_manager.send_system_notification(
            "🧪 Platform Test",
            "Testing notification integration from unified platform",
            priority='high'
        )
        
        if success:
            print("✅ Startup notification sent successfully!")
        else:
            print("❌ Startup notification failed")
        
        print("📊 Testing signal notification...")
        test_signal = {
            'symbol': 'RELIANCE',
            'signal_type': 'BUY',
            'confidence': 85.5,  # Above threshold
            'price': 1417.10,
            'reasoning': ['Testing signal notification from platform'],
            'timestamp': '2025-07-30T15:00:00'
        }
        
        success = notification_manager.send_signal_notification(test_signal)
        
        if success:
            print("✅ Signal notification sent successfully!")
        else:
            print("❌ Signal notification failed")
        
        # Check notification stats
        stats = notification_manager.get_notification_stats()
        print(f"📊 Notification stats: {stats}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
