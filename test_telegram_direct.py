#!/usr/bin/env python3
"""
Direct Telegram test using the existing notifier
"""

if __name__ == "__main__":
    print("🧪 Direct Telegram Test...")
    
    try:
        print("📦 Importing config...")
        from unified_config import config
        print(f"✅ Config loaded - Telegram enabled: {config.TELEGRAM_ENABLED}")
        
        print("📦 Importing Telegram notifier...")
        from notifications.telegram_notifier import TelegramNotifier
        print("✅ TelegramNotifier imported")
        
        print("🔧 Initializing Telegram notifier...")
        telegram = TelegramNotifier(config)
        print("✅ TelegramNotifier initialized")
        
        if telegram.bot:
            print("📱 Sending test message...")
            
            test_signal = {
                'symbol': 'TEST',
                'signal_type': 'BUY',
                'confidence': 95.0,
                'price': 1000.0,
                'reasoning': ['This is a test message from your AI Trading Platform!'],
                'timestamp': '2025-07-30T14:30:00'
            }
            
            success = telegram.send_signal_sync(test_signal)
            
            if success:
                print("✅ Test message sent successfully!")
                print("📱 Check your Telegram for the message!")
            else:
                print("❌ Failed to send test message")
        else:
            print("❌ Telegram bot not initialized properly")
            print(f"Token: {'Set' if config.TELEGRAM_BOT_TOKEN else 'Not set'}")
            print(f"Chat ID: {'Set' if config.TELEGRAM_CHAT_ID else 'Not set'}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
