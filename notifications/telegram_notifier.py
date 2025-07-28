import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import aiohttp
from telegram import Bot
from telegram.error import TelegramError
import requests  # For synchronous requests
from utils.logger import logger

class TelegramNotifier:
    def __init__(self, config):
        self.config = config
        self.bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', None)
        self.chat_id = getattr(config, 'TELEGRAM_CHAT_ID', None)
        
        if self.bot_token and self.bot_token != 'your_telegram_bot_token':
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("Telegram bot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.bot = None
        else:
            logger.warning("Telegram bot token not configured")
            self.bot = None
    
    def send_signal_sync(self, signal: Dict) -> bool:
        """Send trading signal synchronously (for testing and simple usage)"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured")
            return False
        
        try:
            message = self._format_signal_message(signal)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Signal sent to Telegram: {signal['symbol']}")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending signal to Telegram: {e}")
            return False
    
    async def send_signal(self, signal: Dict) -> bool:
        """Send trading signal asynchronously"""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured")
            return False
        
        try:
            message = self._format_signal_message(signal)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Signal sent to Telegram: {signal['symbol']}")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending signal to Telegram: {e}")
            return False
    
    def _format_signal_message(self, signal: Dict) -> str:
        """Format trading signal for Telegram"""
        try:
            signal_type = signal.get('signal_type', 'UNKNOWN')
            symbol = signal.get('symbol', 'UNKNOWN')
            entry_price = signal.get('entry_price', 0)
            target_price = signal.get('target_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            confidence = signal.get('confidence', 0)
            reason = signal.get('reason', 'No reason provided')
            timestamp = signal.get('timestamp', datetime.now())
            
            # Determine emoji based on signal type
            if signal_type == 'BUY':
                emoji = "🟢"
                action_text = "BUY Signal Alert"
            elif signal_type == 'SELL':
                emoji = "🔴"
                action_text = "SELL Signal Alert"
            else:
                emoji = "🟡"
                action_text = "Signal Alert"
            
            # Format timestamp
            time_str = timestamp.strftime("%I:%M %p") if isinstance(timestamp, datetime) else str(timestamp)
            
            # Create message
            message = f"""
{emoji} <b>{action_text} - {symbol}</b>

🔹 <b>Reason:</b> {reason}
📈 <b>Entry:</b> ₹{entry_price:.2f}
🎯 <b>Target:</b> ₹{target_price:.2f}
🛑 <b>SL:</b> ₹{stop_loss:.2f}
🤖 <b>Confidence:</b> {confidence:.0%}
⏰ <b>Time:</b> {time_str}

🚨 <i>This is an automated signal. Please do your own research before trading.</i>
"""
            
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error formatting signal message: {e}")
            return f"Trading Signal: {signal.get('signal_type', 'UNKNOWN')} {signal.get('symbol', 'UNKNOWN')}"
    
    async def send_market_status(self, status: str) -> bool:
        """Send market status update"""
        if not self.bot or not self.chat_id:
            return False
        
        try:
            if status == "OPEN":
                message = "🔔 <b>Market is now OPEN</b>\n📈 Bot is actively monitoring for signals..."
            elif status == "CLOSED":
                message = "🔕 <b>Market is now CLOSED</b>\n😴 Bot will resume monitoring at 9:15 AM"
            else:
                message = f"📊 Market Status: {status}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Market status sent: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending market status: {e}")
            return False
    
    def send_market_status_sync(self, status: str) -> bool:
        """Send market status synchronously"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            if status == "OPEN":
                message = "🔔 <b>Market is now OPEN</b>\n📈 Bot is actively monitoring for signals..."
            elif status == "CLOSED":
                message = "🔕 <b>Market is now CLOSED</b>\n😴 Bot will resume monitoring at 9:15 AM"
            else:
                message = f"📊 Market Status: {status}"
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Market status sent: {status}")
                return True
            else:
                logger.error(f"Failed to send market status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending market status: {e}")
            return False
    
    async def send_performance_report(self, report: Dict) -> bool:
        """Send daily/weekly performance report"""
        if not self.bot or not self.chat_id:
            return False
        
        try:
            total_signals = report.get('total_signals', 0)
            winning_signals = report.get('winning_signals', 0)
            win_rate = (winning_signals / total_signals * 100) if total_signals > 0 else 0
            total_pnl = report.get('total_pnl', 0)
            
            message = f"""
📊 <b>Trading Performance Report</b>

📈 <b>Total Signals:</b> {total_signals}
✅ <b>Winning Signals:</b> {winning_signals}
📊 <b>Win Rate:</b> {win_rate:.1f}%
💰 <b>Total P&L:</b> ₹{total_pnl:.2f}

📅 <b>Report Period:</b> {report.get('period', 'Daily')}
⏰ <b>Generated at:</b> {datetime.now().strftime('%I:%M %p')}
"""
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info("Performance report sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending performance report: {e}")
            return False
    
    async def send_error_alert(self, error_msg: str) -> bool:
        """Send error alert to admin"""
        if not self.bot or not self.chat_id:
            return False
        
        try:
            message = f"""
⚠️ <b>Bot Error Alert</b>

🚨 <b>Error:</b> {error_msg}
⏰ <b>Time:</b> {datetime.now().strftime('%I:%M %p')}

🔧 Please check the bot logs for more details.
"""
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info("Error alert sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending error alert: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test Telegram connection synchronously"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        try:
            # Simple API call to check bot
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Telegram bot connection successful: {result['result']['username']}")
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
                    return False
            else:
                logger.error(f"Telegram connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False
    
    async def send_custom_message(self, message: str) -> bool:
        """Send custom message"""
        if not self.bot or not self.chat_id:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info("Custom message sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending custom message: {e}")
            return False
    
    def send_startup_message(self) -> bool:
        """Send bot startup message synchronously"""
        if not self.bot_token or not self.chat_id:
            return False
        
        try:
            message = """
🚀 <b>AI Trading Bot Started</b>

🤖 Bot is now online and monitoring the markets
📊 Ready to generate trading signals
⏰ Market hours: 9:15 AM - 3:30 PM

🔔 You will receive notifications for:
• Buy/Sell signals
• Market open/close alerts
• Performance reports
• Error alerts

Happy Trading! 📈
"""
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Startup message sent")
                return True
            else:
                logger.error(f"Failed to send startup message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
            return False
