#!/usr/bin/env python3
"""
Unified Notification System
Handles all types of notifications including Telegram, email, and system alerts
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Set up logger early
logger = logging.getLogger(__name__)

# Import configuration and database
from unified_config import config
from unified_database import db

# Import existing Telegram notifier
try:
    import sys
    import os
    # Add the project root to path if needed
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    from notifications.telegram_notifier import TelegramNotifier
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram notifier imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Telegram module not available: {e}")
    TELEGRAM_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error importing Telegram notifier: {e}")
    TELEGRAM_AVAILABLE = False

@dataclass
class NotificationMessage:
    """Notification message structure"""
    title: str
    message: str
    notification_type: str  # 'signal', 'trade', 'error', 'info'
    priority: str = 'normal'  # 'low', 'normal', 'high', 'critical'
    data: Optional[Dict] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class UnifiedNotificationManager:
    """Centralized notification management"""
    
    def __init__(self):
        self.telegram_notifier = None
        self.notification_queue = []
        self.failed_notifications = []
        
        # Initialize Telegram if available and configured
        if TELEGRAM_AVAILABLE and config.TELEGRAM_ENABLED:
            try:
                self.telegram_notifier = TelegramNotifier(config)
                logger.info("✅ Telegram notifications enabled")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Telegram: {e}")
        else:
            if not TELEGRAM_AVAILABLE:
                logger.warning("⚠️ Telegram module not available")
            else:
                logger.info("ℹ️ Telegram notifications disabled in config")
    
    def send_signal_notification(self, signal: Dict) -> bool:
        """Send notification for new trading signal"""
        try:
            confidence = signal.get('confidence', 0)
            
            # Only send if confidence meets threshold
            if confidence < config.SIGNAL_NOTIFICATION_THRESHOLD:
                logger.debug(f"Signal confidence {confidence}% below threshold {config.SIGNAL_NOTIFICATION_THRESHOLD}%")
                return True
            
            # Create notification message
            symbol = signal.get('symbol', 'UNKNOWN')
            signal_type = signal.get('signal_type', 'UNKNOWN')
            price = signal.get('price', 0)
            
            title = f"🚨 {signal_type} Signal: {symbol}"
            message = f"""
🎯 **Trading Signal Generated**
📊 Symbol: {symbol}
📈 Signal: {signal_type}
💪 Confidence: {confidence:.1f}%
💰 Price: ₹{price:.2f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            # Add reasoning if available
            if 'reasoning' in signal and signal['reasoning']:
                reasoning_text = '\n'.join(signal['reasoning'][:3])  # First 3 reasons
                message += f"\n\n📝 Reasoning:\n{reasoning_text}"
            
            notification = NotificationMessage(
                title=title,
                message=message,
                notification_type='signal',
                priority='high' if confidence > 85 else 'normal',
                data=signal
            )
            
            return self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")
            return False
    
    def send_trade_notification(self, trade: Dict) -> bool:
        """Send notification for completed trade"""
        try:
            symbol = trade.get('symbol', 'UNKNOWN')
            side = trade.get('side', 'UNKNOWN')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            pnl = trade.get('pnl', 0)
            
            # Determine emoji based on trade result
            if pnl > 0:
                emoji = "🟢"
                result = "PROFIT"
            elif pnl < 0:
                emoji = "🔴"
                result = "LOSS"
            else:
                emoji = "⚪"
                result = "BREAK-EVEN"
            
            title = f"{emoji} Trade {result}: {symbol}"
            message = f"""
💼 **Trade Completed**
📊 Symbol: {symbol}
📈 Action: {side}
📦 Quantity: {quantity}
💰 Price: ₹{price:.2f}
💵 P&L: ₹{pnl:.2f}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}
            """.strip()
            
            notification = NotificationMessage(
                title=title,
                message=message,
                notification_type='trade',
                priority='high' if abs(pnl) > 5000 else 'normal',
                data=trade
            )
            
            return self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
            return False
    
    def send_portfolio_update(self, portfolio: Dict) -> bool:
        """Send daily portfolio summary"""
        try:
            total_value = portfolio.get('total_value', 0)
            day_pnl = portfolio.get('day_pnl', 0)
            total_pnl = portfolio.get('total_pnl', 0)
            positions_count = portfolio.get('positions_count', 0)
            
            # Determine emoji based on day PnL
            if day_pnl > 0:
                emoji = "🟢"
                performance = "UP"
            elif day_pnl < 0:
                emoji = "🔴"
                performance = "DOWN"
            else:
                emoji = "⚪"
                performance = "FLAT"
            
            title = f"{emoji} Portfolio Update - {performance}"
            message = f"""
📊 **Daily Portfolio Summary**
💰 Total Value: ₹{total_value:,.2f}
📈 Day P&L: ₹{day_pnl:,.2f}
📊 Total P&L: ₹{total_pnl:,.2f}
📦 Active Positions: {positions_count}
⏰ Time: {datetime.now().strftime('%d-%m-%Y %H:%M')}
            """.strip()
            
            notification = NotificationMessage(
                title=title,
                message=message,
                notification_type='portfolio',
                priority='normal',
                data=portfolio
            )
            
            return self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending portfolio notification: {e}")
            return False
    
    def send_system_notification(self, title: str, message: str, priority: str = 'normal') -> bool:
        """Send general system notification"""
        try:
            notification = NotificationMessage(
                title=title,
                message=message,
                notification_type='system',
                priority=priority
            )
            
            return self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: str = '') -> bool:
        """Send error notification"""
        try:
            title = "🚨 System Error Alert"
            message = f"""
❌ **Error Detected**
📝 Error: {error_message}
📍 Context: {context}
⏰ Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
            """.strip()
            
            notification = NotificationMessage(
                title=title,
                message=message,
                notification_type='error',
                priority='critical'
            )
            
            return self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def _send_notification(self, notification: NotificationMessage) -> bool:
        """Internal method to send notification via all enabled channels"""
        success = True
        
        try:
            # Send via Telegram if enabled
            if self.telegram_notifier and config.ENABLE_NOTIFICATIONS:
                try:
                    # For system notifications, send as plain text
                    if notification.notification_type == 'system':
                        message = f"<b>{notification.title}</b>\n\n{notification.message}"
                        
                        if self.telegram_notifier.send_text_message(message):
                            logger.debug(f"✅ Telegram system notification sent: {notification.title}")
                        else:
                            logger.warning(f"⚠️ Failed to send Telegram system notification: {notification.title}")
                            success = False
                    else:
                        # For signals and other notifications, use the signal format
                        telegram_data = {
                            'symbol': notification.data.get('symbol', 'SYSTEM') if notification.data else 'SYSTEM',
                            'signal_type': notification.notification_type.upper(),
                            'confidence': 100,  # Always send system notifications
                            'price': notification.data.get('price', 0) if notification.data else 0,
                            'reasoning': [notification.message],
                            'timestamp': notification.timestamp.isoformat()
                        }
                        
                        # Use sync method for reliability
                        if self.telegram_notifier.send_signal_sync(telegram_data):
                            logger.debug(f"✅ Telegram notification sent: {notification.title}")
                        else:
                            logger.warning(f"⚠️ Failed to send Telegram notification: {notification.title}")
                            success = False
                        
                except Exception as e:
                    logger.error(f"❌ Telegram notification failed: {e}")
                    success = False
            
            # Store notification in database
            try:
                self._store_notification(notification)
            except Exception as e:
                logger.error(f"Failed to store notification in database: {e}")
            
            # Add to queue for potential retry
            if not success:
                self.failed_notifications.append(notification)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in _send_notification: {e}")
            return False
    
    def _store_notification(self, notification: NotificationMessage):
        """Store notification in database"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (
                    notification_type, title, message, priority,
                    data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                notification.notification_type,
                notification.title,
                notification.message,
                notification.priority,
                json.dumps(notification.data) if notification.data else None,
                notification.timestamp
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store notification: {e}")
    
    def retry_failed_notifications(self) -> int:
        """Retry sending failed notifications"""
        retry_count = 0
        failed_copy = self.failed_notifications.copy()
        self.failed_notifications.clear()
        
        for notification in failed_copy:
            if self._send_notification(notification):
                retry_count += 1
            
        logger.info(f"Retried {retry_count}/{len(failed_copy)} failed notifications")
        return retry_count
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get counts by type
            cursor.execute('''
                SELECT notification_type, COUNT(*) as count
                FROM notifications 
                WHERE created_at >= date('now', '-7 days')
                GROUP BY notification_type
            ''')
            
            type_counts = dict(cursor.fetchall())
            
            # Get recent notifications
            cursor.execute('''
                SELECT * FROM notifications 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            
            recent = []
            for row in cursor.fetchall():
                recent.append(dict(row))
            
            conn.close()
            
            return {
                'type_counts': type_counts,
                'recent_notifications': recent,
                'failed_count': len(self.failed_notifications),
                'telegram_enabled': self.telegram_notifier is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}

# Global notification manager instance
notification_manager = UnifiedNotificationManager()

# Convenience functions for easy importing
def send_signal_notification(signal: Dict) -> bool:
    """Send trading signal notification"""
    return notification_manager.send_signal_notification(signal)

def send_trade_notification(trade: Dict) -> bool:
    """Send trade completion notification"""
    return notification_manager.send_trade_notification(trade)

def send_portfolio_update(portfolio: Dict) -> bool:
    """Send portfolio summary notification"""
    return notification_manager.send_portfolio_update(portfolio)

def send_system_notification(title: str, message: str, priority: str = 'normal') -> bool:
    """Send system notification"""
    return notification_manager.send_system_notification(title, message, priority)

def send_error_notification(error_message: str, context: str = '') -> bool:
    """Send error notification"""
    return notification_manager.send_error_notification(error_message, context)

if __name__ == "__main__":
    # Test notifications
    print("🧪 Testing Unified Notification System...")
    
    # Test system notification
    if send_system_notification("System Test", "Testing notification system functionality"):
        print("✅ System notification sent successfully")
    else:
        print("❌ System notification failed")
    
    # Test signal notification
    test_signal = {
        'symbol': 'RELIANCE',
        'signal_type': 'BUY',
        'confidence': 85.5,
        'price': 1417.10,
        'reasoning': ['Strong bullish momentum', 'RSI oversold', 'Volume surge']
    }
    
    if send_signal_notification(test_signal):
        print("✅ Signal notification sent successfully")
    else:
        print("❌ Signal notification failed")
    
    # Show stats
    stats = notification_manager.get_notification_stats()
    print(f"📊 Notification Stats: {stats}")
