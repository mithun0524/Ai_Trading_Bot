#!/usr/bin/env python3
"""
Send a proper startup notification test
"""

if __name__ == "__main__":
    print("🧪 Sending Proper Startup Notification...")
    
    try:
        from notifications.telegram_notifier import TelegramNotifier
        from unified_config import config
        from datetime import datetime
        
        # Initialize Telegram directly
        telegram = TelegramNotifier(config)
        
        if telegram.bot:
            # Create a proper startup message
            startup_signal = {
                'symbol': 'SYSTEM',
                'signal_type': 'STARTUP',
                'confidence': 100.0,
                'price': 1000000.0,  # Portfolio value
                'reasoning': [
                    '🚀 AI Trading Platform Started Successfully!',
                    f'💰 Portfolio Value: ₹10,00,000.00',
                    f'📊 Dashboard: http://localhost:5000',
                    f'🤖 Auto Trading: ENABLED',
                    f'📈 Live Data: ENABLED',
                    f'⏰ Started: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            success = telegram.send_signal_sync(startup_signal)
            
            if success:
                print("✅ Startup notification sent successfully!")
                print("📱 Check your Telegram for the platform startup message!")
            else:
                print("❌ Failed to send startup notification")
        else:
            print("❌ Telegram bot not initialized")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
