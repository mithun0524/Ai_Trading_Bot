#!/usr/bin/env python3
"""
Telegram Bot with Command Handlers
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from config import Config
from utils.logger import logger

class TelegramBotServer:
    def __init__(self, trading_bot=None):
        self.config = Config()
        self.bot_token = self.config.TELEGRAM_BOT_TOKEN
        self.chat_id = self.config.TELEGRAM_CHAT_ID
        self.trading_bot = trading_bot
        
        if not self.bot_token or self.bot_token == 'your_telegram_bot_token':
            logger.error("Telegram bot token not configured")
            return
        
        # Initialize bot application
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.setup_command_handlers()
        
        logger.info("Telegram bot server initialized with command handlers")
    
    def setup_command_handlers(self):
        """Setup all command handlers"""
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("watchlist", self.watchlist_command))
        self.application.add_handler(CommandHandler("signals", self.signals_command))
        self.application.add_handler(CommandHandler("performance", self.performance_command))
        
        logger.info("Command handlers registered")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            welcome_message = """
🚀 <b>Welcome to AI Trading Bot!</b>

🤖 <b>Available Commands:</b>
• /start - Show this welcome message
• /help - Get detailed help
• /status - Check bot status
• /watchlist - View current watchlist
• /signals - See recent signals
• /performance - View performance stats

📊 <b>Bot Features:</b>
• Real-time market monitoring
• AI-powered signal generation
• 35+ technical indicators
• Automated risk management
• Daily performance reports

⏰ <b>Market Hours:</b> 9:15 AM - 3:30 PM IST
🎯 <b>Signal Accuracy:</b> 53.62% (backtested)

Happy Trading! 📈
"""
            
            await update.message.reply_text(welcome_message, parse_mode='HTML')
            logger.info(f"Start command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            help_message = """
📖 <b>Trading Bot Command Guide</b>

🤖 <b>Basic Commands:</b>
• <code>/start</code> - Welcome message and overview
• <code>/help</code> - This help message
• <code>/status</code> - Current bot status and market info

📊 <b>Trading Commands:</b>
• <code>/watchlist</code> - View monitored stocks (52 symbols)
• <code>/signals</code> - Recent trading signals (last 5)
• <code>/performance</code> - Performance statistics

🎯 <b>How Signals Work:</b>
• Bot scans 5 symbols every 10 minutes
• AI analyzes 35+ technical indicators
• Only high-confidence signals (70%+) are sent
• Each signal includes entry, target, and stop-loss

⚠️ <b>Important:</b>
• Signals are for educational purposes only
• Always do your own research
• Trade at your own risk

📞 <b>Need Support?</b>
Check logs in trading_bot.log or restart the bot.
"""
            
            await update.message.reply_text(help_message, parse_mode='HTML')
            logger.info(f"Help command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("❌ Error processing command")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            current_time = datetime.now()
            
            # Check if trading bot is available
            if not self.trading_bot:
                status_message = """
⚠️ <b>Bot Status: INITIALIZING</b>

The trading bot is still starting up. Please wait a moment and try again.
"""
                await update.message.reply_text(status_message, parse_mode='HTML')
                return
            
            # Get market status
            try:
                market_status = self.trading_bot.data_provider.get_market_status()
                is_market_open = market_status.get('is_open', False)
            except:
                is_market_open = False
            
            # Get daily signal count
            daily_signals = getattr(self.trading_bot, 'daily_signal_count', 0)
            max_daily = getattr(Config, 'MAX_TRADES_PER_DAY', 10)
            
            # Get database stats
            try:
                db_stats = self.trading_bot.db_manager.get_database_stats()
                total_signals = db_stats.get('signals_count', 0)
            except:
                total_signals = 0
            
            status_message = f"""
🤖 <b>Trading Bot Status</b>

🕒 <b>Current Time:</b> {current_time.strftime('%I:%M %p')}
📈 <b>Market Status:</b> {'🟢 OPEN' if is_market_open else '🔴 CLOSED'}
🎯 <b>Bot Status:</b> {'🟢 ACTIVE' if self.trading_bot.is_running else '🔴 STOPPED'}

📊 <b>Today's Activity:</b>
• Signals Generated: {daily_signals}/{max_daily}
• Total Signals in DB: {total_signals}

⏰ <b>Next Actions:</b>
{'• Market scan every 10 minutes' if is_market_open else '• Waiting for market open (9:15 AM)'}
• Daily report at 4:00 PM
• Weekly report on Saturday

🔄 <b>Last Updated:</b> {current_time.strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await update.message.reply_text(status_message, parse_mode='HTML')
            logger.info(f"Status command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text("❌ Error getting bot status")
    
    async def watchlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /watchlist command"""
        try:
            if not self.trading_bot:
                await update.message.reply_text("⚠️ Trading bot not available")
                return
            
            # Get watchlist from database
            try:
                watchlist = self.trading_bot.db_manager.get_watchlist()
                if not watchlist:
                    watchlist = Config.NIFTY_50_SYMBOLS[:20]  # Fallback to first 20
            except:
                watchlist = Config.NIFTY_50_SYMBOLS[:20]
            
            # Format watchlist message
            watchlist_message = """
📋 <b>Current Watchlist</b>

🏢 <b>Monitored Symbols:</b>
"""
            
            # Group symbols in rows of 4
            for i in range(0, len(watchlist), 4):
                row_symbols = watchlist[i:i+4]
                watchlist_message += "• " + " | ".join(row_symbols) + "\n"
            
            watchlist_message += f"""

📊 <b>Total Symbols:</b> {len(watchlist)}
🔄 <b>Scan Frequency:</b> Every 10 minutes (5 symbols per scan)
⏰ <b>Market Hours:</b> 9:15 AM - 3:30 PM IST

💡 <b>How it works:</b>
Bot rotates through the watchlist, analyzing 5 symbols every 10 minutes during market hours.
"""
            
            await update.message.reply_text(watchlist_message, parse_mode='HTML')
            logger.info(f"Watchlist command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in watchlist command: {e}")
            await update.message.reply_text("❌ Error retrieving watchlist")
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        try:
            if not self.trading_bot:
                await update.message.reply_text("⚠️ Trading bot not available")
                return
            
            # Get recent signals
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)  # Last 7 days
                signals = self.trading_bot.db_manager.get_signals_by_date(start_date, end_date)
                
                if not signals:
                    await update.message.reply_text("""
📊 <b>Recent Signals</b>

🤷‍♂️ No signals found in the last 7 days.

💡 <b>Possible reasons:</b>
• Market conditions don't meet signal criteria
• Confidence threshold too high (currently 70%)
• Bot recently started

⏰ <b>Next scan:</b> Bot scans every 10 minutes during market hours.
""", parse_mode='HTML')
                    return
                
                # Format signals message
                signals_message = f"""
📊 <b>Recent Trading Signals</b>

🔢 <b>Found {len(signals)} signals in last 7 days</b>

"""
                
                # Show last 5 signals
                recent_signals = signals[:5]
                for i, signal in enumerate(recent_signals, 1):
                    symbol = signal.get('symbol', 'UNKNOWN')
                    signal_type = signal.get('signal_type', 'UNKNOWN')
                    entry_price = signal.get('entry_price', 0)
                    confidence = signal.get('confidence_score', 0)
                    timestamp = signal.get('timestamp', '')
                    status = signal.get('status', 'UNKNOWN')
                    
                    emoji = "🟢" if signal_type == 'BUY' else "🔴"
                    confidence_pct = confidence * 100 if confidence <= 1 else confidence
                    
                    if isinstance(timestamp, str):
                        try:
                            time_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = time_obj.strftime('%m/%d %I:%M %p')
                        except:
                            time_str = timestamp[:16] if len(timestamp) > 16 else timestamp
                    else:
                        time_str = str(timestamp)[:16]
                    
                    signals_message += f"""
{emoji} <b>{symbol}</b> - {signal_type}
💰 Entry: ₹{entry_price:.2f} | 🔥 {confidence_pct:.0f}%
📅 {time_str} | Status: {status}

"""
                
                signals_message += f"""
📈 <b>Signal Performance:</b>
Use /performance for detailed statistics

⏰ <b>Market Hours:</b> 9:15 AM - 3:30 PM IST
"""
                
                await update.message.reply_text(signals_message, parse_mode='HTML')
                
            except Exception as e:
                logger.error(f"Error fetching signals: {e}")
                await update.message.reply_text("❌ Error retrieving signals from database")
            
            logger.info(f"Signals command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in signals command: {e}")
            await update.message.reply_text("❌ Error processing signals command")
    
    async def performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /performance command"""
        try:
            if not self.trading_bot:
                await update.message.reply_text("⚠️ Trading bot not available")
                return
            
            # Get performance metrics
            try:
                # Get 30-day performance
                perf_30d = self.trading_bot.db_manager.get_performance_metrics(30)
                # Get 7-day performance
                perf_7d = self.trading_bot.db_manager.get_performance_metrics(7)
                # Get today's performance
                perf_1d = self.trading_bot.db_manager.get_performance_metrics(1)
                
                performance_message = f"""
📊 <b>Trading Performance Report</b>

📅 <b>Last 30 Days:</b>
• Total Signals: {perf_30d.get('total_signals', 0)}
• Winning Signals: {perf_30d.get('winning_signals', 0)}
• Win Rate: {perf_30d.get('win_rate', 0):.1f}%
• Total P&L: ₹{perf_30d.get('total_pnl', 0):.2f}

📅 <b>Last 7 Days:</b>
• Total Signals: {perf_7d.get('total_signals', 0)}
• Winning Signals: {perf_7d.get('winning_signals', 0)}
• Win Rate: {perf_7d.get('win_rate', 0):.1f}%
• Total P&L: ₹{perf_7d.get('total_pnl', 0):.2f}

📅 <b>Today:</b>
• Total Signals: {perf_1d.get('total_signals', 0)}
• Winning Signals: {perf_1d.get('winning_signals', 0)}
• Win Rate: {perf_1d.get('win_rate', 0):.1f}%
• Total P&L: ₹{perf_1d.get('total_pnl', 0):.2f}

🎯 <b>AI Model Accuracy:</b> 53.62% (backtested)
⚙️ <b>Min Confidence:</b> 70%
📈 <b>Max Daily Signals:</b> {getattr(Config, 'MAX_TRADES_PER_DAY', 10)}

⏰ <b>Generated at:</b> {datetime.now().strftime('%I:%M %p')}

💡 <b>Note:</b> Performance is calculated on closed positions only.
"""
                
                await update.message.reply_text(performance_message, parse_mode='HTML')
                
            except Exception as e:
                logger.error(f"Error fetching performance data: {e}")
                await update.message.reply_text("❌ Error retrieving performance data")
            
            logger.info(f"Performance command received from user: {update.effective_user.id}")
            
        except Exception as e:
            logger.error(f"Error in performance command: {e}")
            await update.message.reply_text("❌ Error processing performance command")
    
    async def start_polling(self):
        """Start the bot polling for commands"""
        try:
            logger.info("Starting Telegram bot polling...")
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("Telegram bot is now listening for commands")
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot polling: {e}")
    
    async def stop_polling(self):
        """Stop the bot polling"""
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot polling stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Telegram bot polling: {e}")
    
    def set_trading_bot(self, trading_bot):
        """Set reference to trading bot for data access"""
        self.trading_bot = trading_bot
        logger.info("Trading bot reference set for Telegram commands")

if __name__ == "__main__":
    # Test the bot
    telegram_bot = TelegramBotServer()
    
    async def main():
        await telegram_bot.start_polling()
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await telegram_bot.stop_polling()
    
    asyncio.run(main())
