#!/usr/bin/env python3
"""
Simple test for Telegram notifications
"""

if __name__ == "__main__":
    print("🧪 Testing Telegram Notifications...")
    
    try:
        print("📦 Importing modules...")
        from unified_notifications import send_system_notification, send_signal_notification
        print("✅ Modules imported successfully")
        
        print("📱 Testing system notification...")
        success = send_system_notification(
            "🧪 Test Message", 
            "This is a test notification from your AI Trading Platform!"
        )
        
        if success:
            print("✅ System notification sent successfully!")
        else:
            print("❌ System notification failed")
        
        print("📊 Testing signal notification...")
        test_signal = {
            'symbol': 'RELIANCE',
            'signal_type': 'BUY',
            'confidence': 85.5,
            'price': 1417.10,
            'reasoning': ['Strong bullish momentum', 'RSI oversold', 'Volume surge']
        }
        
        success = send_signal_notification(test_signal)
        
        if success:
            print("✅ Signal notification sent successfully!")
            print("📱 Check your Telegram for the messages!")
        else:
            print("❌ Signal notification failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
