#!/usr/bin/env python3
"""
🧪 Test Telegram Integration with Unified Platform
Quick test to verify Telegram notifications are working
"""

if __name__ == "__main__":
    print("🧪 Testing Telegram Integration...")
    print("=" * 50)
    
    try:
        print("📦 Importing unified modules...")
        from unified_config import config
        from unified_notifications import notification_manager
        from datetime import datetime
        
        print("✅ Modules imported successfully")
        print(f"� Telegram enabled: {config.TELEGRAM_ENABLED}")
        print(f"🤖 Bot token: {config.TELEGRAM_BOT_TOKEN[:10]}..." if config.TELEGRAM_BOT_TOKEN else "❌ No bot token")
        print(f"💬 Chat ID: {config.TELEGRAM_CHAT_ID}")
        
        if config.TELEGRAM_ENABLED:
            print("\n📱 Testing system notification...")
            
            test_message = f"""
🧪 <b>Telegram Integration Test</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ <b>Test Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚀 <b>Platform:</b> Unified AI Trading Platform
✅ <b>Status:</b> Telegram integration working perfectly!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you see this message, your Telegram notifications are properly configured! 🎉
            """
            
            success = notification_manager.send_system_notification(
                title="🧪 Integration Test",
                message=test_message,
                priority="medium"
            )
            
            if success:
                print("✅ Test notification sent successfully!")
                print("� Check your Telegram to see the message")
            else:
                print("❌ Failed to send test notification")
                
            # Test simple message too
            print("\n📲 Testing simple message...")
            simple_success = notification_manager.send_system_notification(
                title="🚀 Simple Test",
                message="This is a simple test message from your AI Trading Platform! 🎯",
                priority="low"
            )
            
            if simple_success:
                print("✅ Simple message sent successfully!")
            else:
                print("❌ Failed to send simple message")
                
        else:
            print("❌ Telegram not enabled in configuration")
            print("� Make sure you have TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nDebugging info:")
        print("1. Make sure the unified platform modules are available")
        print("2. Check your .env file has TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        print("3. Verify your bot token is correct and active")
        
    print("\n" + "=" * 50)
    print("🧪 Telegram integration test completed!")
            priority='high'
        )
        
        if success:
            print("✅ System notification sent successfully!")
        else:
            print("❌ System notification failed")
        
        print("📊 Testing signal notification...")
        test_signal = {
            'symbol': 'RELIANCE',
            'signal_type': 'BUY',
            'confidence': 85.0,
            'price': 1417.10,
            'reasoning': ['Strong bullish momentum', 'RSI oversold', 'Volume surge'],
            'timestamp': datetime.now().isoformat()
        }
        
        success2 = send_signal_notification(test_signal)
        
        if success2:
            print("✅ Signal notification sent successfully!")
        else:
            print("❌ Signal notification failed")
            
        print("📱 Check your Telegram for both messages!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
