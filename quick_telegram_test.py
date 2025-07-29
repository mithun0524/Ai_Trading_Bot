#!/usr/bin/env python3
"""
Quick test to send a Telegram notification right now
"""

if __name__ == "__main__":
    print("🧪 Quick Telegram Test...")
    
    try:
        print("📦 Importing modules...")
        from unified_config import config
        from unified_notifications import notification_manager
        
        print("📱 Sending test notification...")
        success = notification_manager.send_system_notification(
            "🧪 Manual Test",
            """
🚀 **Manual Notification Test**
📱 This is a test message to verify Telegram notifications are working!
⏰ Time: """ + str(__import__('datetime').datetime.now().strftime('%d-%m-%Y %H:%M:%S')),
            priority='high'
        )
        
        if success:
            print("✅ Notification sent successfully!")
            print("📱 Check your Telegram now!")
        else:
            print("❌ Notification failed")
            
        # Also try signal notification
        print("📊 Testing signal notification...")
        test_signal = {
            'symbol': 'RELIANCE',
            'signal_type': 'BUY',
            'confidence': 85.0,
            'price': 1417.10,
            'reasoning': ['Manual test signal', 'Telegram verification'],
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        success2 = notification_manager.send_signal_notification(test_signal)
        
        if success2:
            print("✅ Signal notification sent successfully!")
        else:
            print("❌ Signal notification failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
