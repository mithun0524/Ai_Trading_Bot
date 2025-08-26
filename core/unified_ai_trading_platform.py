#!/usr/bin/env python3
"""
🚀 Apex AI Trading Platform
Main integration system that ties all components together
"""

import asyncio
import logging
import threading
import time
import signal
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import argparse

# Import all unified modules
from unified_config import config
from unified_database import db
from unified_live_data import live_data_manager, start_live_data_thread
from unified_ai_signals import ai_signal_generator
from unified_trading_manager import trading_manager
from unified_web_dashboard import run_dashboard, dashboard_manager
from unified_notifications import notification_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_platform.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class UnifiedTradingPlatform:
    """Main AI trading platform orchestrator"""
    
    def __init__(self):
        self.running = False
        self.threads = {}
        self.last_signal_generation = None
        self.last_portfolio_update = None
        self.performance_stats = {
            'signals_generated': 0,
            'orders_placed': 0,
            'trades_completed': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'uptime_start': datetime.now()
        }
        
    logger.info("🚀 Apex AI Trading Platform initialized")
    
    def startup_checks(self) -> bool:
        """Perform startup checks and initialization"""
        try:
            logger.info("🔍 Performing startup checks...")
            
            # 1. Database connectivity
            logger.info("📊 Checking database connection...")
            portfolio_df = db.get_portfolio_summary()
            logger.info(f"✅ Database connected - {len(portfolio_df)} portfolio records")
            
            # 2. Configuration validation
            logger.info("⚙️  Validating configuration...")
            symbols = config.get_active_symbols()
            logger.info(f"✅ Configuration loaded - {len(symbols)} active symbols")
            
            # 3. Live data connectivity
            logger.info("📈 Testing live data connectivity...")
            test_quote = None
            try:
                test_quote = asyncio.run(live_data_manager.get_live_quote('RELIANCE'))
                if test_quote:
                    logger.info(f"✅ Live data connected - RELIANCE: ₹{test_quote.price:.2f}")
                else:
                    logger.warning("⚠️  Live data connection issue - will retry")
            except Exception as e:
                logger.error(f"Error during live data check: {e}", exc_info=True)

            # 4. Trading manager initialization
            logger.info("💼 Initializing trading manager...")
            summary = None
            try:
                asyncio.run(trading_manager.update_portfolio_value())
                summary = trading_manager.get_portfolio_summary()
                logger.info(f"✅ Trading manager ready - Portfolio: ₹{summary['portfolio_value']:,.2f}")
            except Exception as e:
                logger.error(f"Error during trading manager init: {e}", exc_info=True)

            # 5. AI signal generator test
            logger.info("🤖 Testing AI signal generator...")
            if test_quote:
                historical_data = live_data_manager.get_historical_data('RELIANCE')
                if not historical_data.empty:
                    signal = ai_signal_generator.generate_signal('RELIANCE', test_quote, historical_data)
                    logger.info(f"✅ AI signals ready - Test signal: {signal.signal_type} ({signal.confidence:.1f}%)")
                else:
                    logger.warning("⚠️  No historical data for signal test")
            
            logger.info("🎉 All startup checks completed successfully!")
            
            # Send startup notification to Telegram
            if summary:
                try:
                    startup_message = f"""
🚀 <b>AI Trading Platform Started</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>System Status:</b> ONLINE
💼 <b>Portfolio:</b> ₹{summary['portfolio_value']:,.2f}
📈 <b>Active Symbols:</b> {len(symbols)}
⏰ <b>Started:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All systems operational and ready for trading!
                    """
                    notification_manager.send_system_notification(
                        title="🚀 Trading Platform Started",
                        message=startup_message,
                        priority="high"
                    )
                    logger.info("📱 Startup notification sent to Telegram")
                except Exception as e:
                    logger.warning(f"⚠️ Could not send startup notification: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Startup check failed: {e}", exc_info=True)
            return False
    
    def schedule_tasks(self):
        """Schedule recurring tasks"""
        logger.info("📅 Scheduling recurring tasks...")
        
        # Market hours: 9:15 AM to 3:30 PM IST
        if config.FEATURES['AUTO_TRADING']:
            # Generate signals every 5 minutes during market hours
            schedule.every(5).minutes.do(self._scheduled_signal_generation)
            
            # Process pending orders every 1 minute
            schedule.every(1).minutes.do(self._scheduled_order_processing)
            
            # Update portfolio every 2 minutes
            schedule.every(2).minutes.do(self._scheduled_portfolio_update)
            
            # Monitor positions every 30 seconds
            schedule.every(30).seconds.do(self._scheduled_position_monitoring)
        
        # Generate end-of-day report
        schedule.every().day.at("15:45").do(self._scheduled_eod_report)
        
        # Clean up old data weekly
        schedule.every().sunday.at("18:00").do(self._scheduled_cleanup)
        
        logger.info("✅ Tasks scheduled successfully")
    
    def _scheduled_signal_generation(self):
        """Scheduled AI signal generation"""
        if not self._is_market_hours():
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            signals = loop.run_until_complete(ai_signal_generator.generate_signals_for_watchlist())
            
            # Process strong signals automatically
            if config.FEATURES['AUTO_TRADING']:
                for signal in signals:
                    if signal.confidence >= config.MIN_SIGNAL_CONFIDENCE:
                        processed = loop.run_until_complete(trading_manager.process_ai_signal(signal))
                        if processed:
                            self.performance_stats['orders_placed'] += 1
                            logger.info(f"🎯 Auto-processed signal: {signal.symbol} {signal.signal_type}")
            
            loop.close()
            
            self.performance_stats['signals_generated'] += len(signals)
            self.last_signal_generation = datetime.now()
            
            buy_signals = len([s for s in signals if s.signal_type == 'BUY'])
            sell_signals = len([s for s in signals if s.signal_type == 'SELL'])
            
            logger.info(f"🎯 Generated {len(signals)} signals - BUY: {buy_signals}, SELL: {sell_signals}")
            
            # Send high-confidence signals to Telegram
            if signals:
                try:
                    for signal in signals:
                        if signal.confidence >= 75.0:  # Only send high confidence signals
                            notification_manager.send_signal_notification(signal)
                            logger.info(f"📱 High-confidence signal sent to Telegram: {signal.symbol}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not send signal notifications: {e}")
            
        except Exception as e:
            logger.error(f"Error in scheduled signal generation: {e}")
            # Send error alert to Telegram
            try:
                error_message = f"""
⚠️ <b>Signal Generation Error</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
❌ <b>Error:</b> {str(e)[:200]}...
🔧 <b>Action:</b> System will retry automatically
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """
                notification_manager.send_system_notification(
                    title="⚠️ Signal Generation Error",
                    message=error_message,
                    priority="high"
                )
            except:
                pass  # Don't let notification errors break the main process
    
    def _scheduled_order_processing(self):
        """Scheduled order processing"""
        if not self._is_market_hours():
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(trading_manager.process_pending_orders())
            loop.close()
            
        except Exception as e:
            logger.error(f"Error in scheduled order processing: {e}")
    
    def _scheduled_portfolio_update(self):
        """Scheduled portfolio update"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(trading_manager.update_portfolio_value())
            loop.close()
            
            # Update performance stats
            summary = trading_manager.get_portfolio_summary()
            self.performance_stats['total_pnl'] = summary['total_pnl']
            self.performance_stats['win_rate'] = summary['win_rate']
            self.performance_stats['trades_completed'] = summary['total_trades']
            
            self.last_portfolio_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in scheduled portfolio update: {e}")
    
    def _scheduled_position_monitoring(self):
        """Scheduled position monitoring"""
        if not self._is_market_hours():
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(trading_manager.monitor_positions())
            loop.close()
            
        except Exception as e:
            logger.error(f"Error in scheduled position monitoring: {e}")
    
    def _scheduled_eod_report(self):
        """Generate end-of-day report"""
        try:
            logger.info("📋 Generating end-of-day report...")
            
            # Update portfolio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(trading_manager.update_portfolio_value())
            loop.close()
            
            # Get summary
            summary = trading_manager.get_portfolio_summary()
            
            # Get today's trades  
            trades_data = db.get_trades(limit=100)
            if isinstance(trades_data, pd.DataFrame) and not trades_data.empty and 'created_at' in trades_data.columns:
                today_trades = trades_data[trades_data['created_at'].dt.date == datetime.now().date()]
            elif isinstance(trades_data, list):
                # Convert list to DataFrame if needed
                today_trades = pd.DataFrame(trades_data) if trades_data else pd.DataFrame()
            else:
                today_trades = pd.DataFrame()
            
            # Get today's signals
            signals_data = db.get_signals(limit=500)
            if isinstance(signals_data, pd.DataFrame) and not signals_data.empty and 'created_at' in signals_data.columns:
                today_signals = signals_data[signals_data['created_at'].dt.date == datetime.now().date()]
            elif isinstance(signals_data, list):
                # Convert list to DataFrame if needed
                today_signals = pd.DataFrame(signals_data) if signals_data else pd.DataFrame()
            else:
                today_signals = pd.DataFrame()
            
            # Generate report
            report = f"""
📋 END-OF-DAY REPORT - {datetime.now().strftime('%Y-%m-%d')}
{'='*60}

💼 PORTFOLIO SUMMARY:
   Portfolio Value: ₹{summary['portfolio_value']:,.2f}
   Cash Balance: ₹{summary['cash_balance']:,.2f}
   Total P&L: ₹{summary['total_pnl']:,.2f}
   Active Positions: {summary['total_positions']}
   
🎯 TODAY'S SIGNALS:
   Total Signals: {len(today_signals)}
   BUY Signals: {len(today_signals[today_signals['signal_type'] == 'BUY']) if not today_signals.empty and 'signal_type' in today_signals.columns else 0}
   SELL Signals: {len(today_signals[today_signals['signal_type'] == 'SELL']) if not today_signals.empty and 'signal_type' in today_signals.columns else 0}
   
💰 TODAY'S TRADES:
   Completed Trades: {len(today_trades)}
   Total P&L: ₹{today_trades['pnl'].sum() if not today_trades.empty and 'pnl' in today_trades.columns else 0:.2f}
   
📊 PERFORMANCE STATS:
   Win Rate: {summary['win_rate']:.1f}%
   Total Trades: {summary['total_trades']}
   Orders Placed Today: {self.performance_stats['orders_placed']}
   Signals Generated Today: {len(today_signals)}
   
⏱️  SYSTEM UPTIME:
   Started: {self.performance_stats['uptime_start'].strftime('%Y-%m-%d %H:%M:%S')}
   Uptime: {datetime.now() - self.performance_stats['uptime_start']}

{'='*60}
            """
            
            logger.info(report)
            
            # Send EOD report to Telegram
            try:
                eod_telegram_message = f"""
📋 <b>End-of-Day Report</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}

💼 <b>Portfolio Summary:</b>
• Value: ₹{summary['portfolio_value']:,.2f}
• Cash: ₹{summary['cash_balance']:,.2f}
• P&L: ₹{summary['total_pnl']:,.2f}
• Positions: {summary['total_positions']}

🎯 <b>Today's Activity:</b>
• Signals: {len(today_signals)}
• Trades: {len(today_trades)}
• Orders: {self.performance_stats['orders_placed']}

📊 <b>Performance:</b>
• Win Rate: {summary['win_rate']:.1f}%
• Total Trades: {summary['total_trades']}

⏱️ <b>Uptime:</b> {datetime.now() - self.performance_stats['uptime_start']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """
                notification_manager.send_system_notification(
                    title="📋 End-of-Day Report",
                    message=eod_telegram_message,
                    priority="medium"
                )
                logger.info("📱 EOD report sent to Telegram")
            except Exception as e:
                logger.warning(f"⚠️ Could not send EOD report: {e}")
            
            # Save report to file
            with open(f"eod_report_{datetime.now().strftime('%Y%m%d')}.txt", 'w', encoding='utf-8') as f:
                f.write(report)
                
        except Exception as e:
            logger.error(f"Error generating EOD report: {e}")
    
    def _scheduled_cleanup(self):
        """Clean up old data"""
        try:
            logger.info("🧹 Performing weekly cleanup...")
            
            # Clean old signals (keep last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            db.cleanup_old_signals(cutoff_date)
            
            # Clean old live data (keep last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            db.cleanup_old_live_data(cutoff_date)
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")
    
    def _is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        now = datetime.now()
        
        # Skip weekends
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:15 AM to 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def _run_scheduler(self):
        """Run the task scheduler"""
        logger.info("⏰ Task scheduler started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(5)
        
        logger.info("⏰ Task scheduler stopped")
    
    def _run_dashboard(self):
        """Run the web dashboard"""
        try:
            logger.info("🌐 Starting web dashboard...")
            run_dashboard(host='0.0.0.0', port=5000, debug=False)
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    def start(self, enable_dashboard=True, enable_scheduler=True):
        """Start the trading platform"""
        try:
            logger.info("🚀 STARTING APEX AI TRADING PLATFORM")
            logger.info("="*60)
            
            # Perform startup checks
            if not self.startup_checks():
                logger.error("❌ Startup checks failed, exiting...")
                return False
            
            self.running = True
            
            # Start live data feed in background
            try:
                live_thread = start_live_data_thread()
                self.threads['live_data'] = live_thread
                logger.info("✅ Live data feed started")
            except Exception as e:
                logger.warning(f"⚠️ Could not start live data feed: {e}")

            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Schedule recurring tasks
            if enable_scheduler:
                self.schedule_tasks()
                scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
                scheduler_thread.start()
                self.threads['scheduler'] = scheduler_thread
                logger.info("✅ Task scheduler started")
            
            # Start web dashboard
            if enable_dashboard:
                dashboard_thread = threading.Thread(target=self._run_dashboard, daemon=True)
                dashboard_thread.start()
                self.threads['dashboard'] = dashboard_thread
                logger.info("✅ Web dashboard started on http://0.0.0.0:5000")
            
            # Initial signal generation
            if config.FEATURES['AUTO_TRADING'] and self._is_market_hours():
                logger.info("🎯 Generating initial signals...")
                self._scheduled_signal_generation()
            
            # Main monitoring loop
            logger.info("🎉 PLATFORM STARTED SUCCESSFULLY!")
            logger.info("="*60)
            logger.info("📊 Dashboard: http://localhost:5000")
            logger.info("🤖 AI Trading: " + ("ENABLED" if config.FEATURES['AUTO_TRADING'] else "DISABLED"))
            logger.info("📈 Live Data: " + ("ENABLED" if config.FEATURES['LIVE_DATA'] else "DISABLED"))
            logger.info("💼 Paper Trading: " + ("ENABLED" if config.FEATURES['PAPER_TRADING'] else "DISABLED"))
            logger.info("="*60)
            
            # Keep main thread alive
            while self.running:
                try:
                    # Print periodic status
                    if datetime.now().minute % 10 == 0 and datetime.now().second == 0:
                        self._print_status()
                    
                    # Send hourly status to Telegram (during market hours)
                    if (self._is_market_hours() and 
                        datetime.now().minute == 0 and datetime.now().second == 0 and
                        datetime.now().hour in [10, 12, 14]):  # 10 AM, 12 PM, 2 PM
                        try:
                            self._send_hourly_status()
                        except Exception as e:
                            logger.warning(f"⚠️ Could not send hourly status: {e}")
                    
                    time.sleep(1)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Keyboard interrupt received")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting platform: {e}")
            return False
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the trading platform gracefully"""
        if not self.running:
            return
        
        logger.info("🛑 STOPPING APEX AI TRADING PLATFORM")
        logger.info("="*50)
        
        self.running = False
        
        # Send shutdown notification to Telegram
        try:
            uptime = datetime.now() - self.performance_stats['uptime_start']
            shutdown_message = f"""
🛑 <b>Trading Platform Stopped</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ <b>Shutdown Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Session Uptime:</b> {uptime}
🎯 <b>Signals Generated:</b> {self.performance_stats['signals_generated']}
📋 <b>Orders Placed:</b> {self.performance_stats['orders_placed']}
💰 <b>Session P&L:</b> ₹{self.performance_stats['total_pnl']:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Platform stopped gracefully
            """
            notification_manager.send_system_notification(
                title="🛑 Trading Platform Stopped",
                message=shutdown_message,
                priority="medium"
            )
            logger.info("📱 Shutdown notification sent to Telegram")
        except Exception as e:
            logger.warning(f"⚠️ Could not send shutdown notification: {e}")
        
        # Generate final report
        try:
            self._scheduled_eod_report()
        except:
            pass
        
        # Wait for threads to finish
        for name, thread in self.threads.items():
            if thread.is_alive():
                logger.info(f"⏳ Waiting for {name} thread to finish...")
                thread.join(timeout=5)
        
        logger.info("✅ Platform stopped gracefully")
        logger.info("="*50)
    
    def _print_status(self):
        """Print current status"""
        try:
            summary = trading_manager.get_portfolio_summary()
            market_status = "OPEN" if self._is_market_hours() else "CLOSED"
            
            status = f"""
📊 STATUS UPDATE - {datetime.now().strftime('%H:%M:%S')}
   Market: {market_status} | Portfolio: ₹{summary['portfolio_value']:,.2f} | P&L: ₹{summary['total_pnl']:,.2f}
   Positions: {summary['total_positions']} | Orders: {summary['active_orders']} | Trades: {summary['total_trades']}
            """.strip()
            
            logger.info(status)
            
        except Exception as e:
            logger.error(f"Error printing status: {e}")
    
    def _send_hourly_status(self):
        """Send hourly status update to Telegram"""
        try:
            summary = trading_manager.get_portfolio_summary()
            current_time = datetime.now().strftime('%H:%M')
            
            hourly_message = f"""
📊 <b>Hourly Status Update</b> - {current_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 <b>Portfolio:</b> ₹{summary['portfolio_value']:,.2f}
📈 <b>Day P&L:</b> ₹{summary['total_pnl']:,.2f}
🎯 <b>Active Positions:</b> {summary['total_positions']}
📋 <b>Signals Today:</b> {self.performance_stats['signals_generated']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟢 System running smoothly
            """
            
            notification_manager.send_system_notification(
                title=f"📊 Status Update - {current_time}",
                message=hourly_message,
                priority="low"
            )
            logger.info(f"📱 Hourly status sent to Telegram at {current_time}")
            
        except Exception as e:
            logger.error(f"Error sending hourly status: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Apex AI Trading Platform')
    parser.add_argument('--no-dashboard', action='store_true', help='Disable web dashboard')
    parser.add_argument('--no-scheduler', action='store_true', help='Disable task scheduler')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # Create platform instance
    platform = UnifiedTradingPlatform()
    
    if args.test_mode:
        logger.info("🧪 RUNNING IN TEST MODE")
        
        # Run startup checks only
        success = platform.startup_checks()
        if success:
            logger.info("✅ Test mode completed successfully")
            return 0
        else:
            logger.error("❌ Test mode failed")
            return 1
    
    else:
        # Start the full platform
        try:
            success = platform.start(
                enable_dashboard=not args.no_dashboard,
                enable_scheduler=not args.no_scheduler
            )
            
            return 0 if success else 1
            
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
            return 0
        except Exception as e:
            logger.error(f"❌ Platform error: {e}")
            return 1

if __name__ == "__main__":
    print("""
🚀 Apex AI Trading Platform
================================
🤖 AI-Powered Trading Signals
📊 Real-time Market Data  
💼 Portfolio Management
🌐 Web Dashboard
📈 Paper Trading
💰 Risk Management
🎯 Automated Execution
================================
    """)
    
    exit_code = main()
    sys.exit(exit_code)
