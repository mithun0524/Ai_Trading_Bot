import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from data.data_provider import DataProvider
from analysis.technical_analysis import TechnicalAnalysis
from ai.signal_generator import AISignalGenerator
from notifications.telegram_notifier import TelegramNotifier
from database.database_manager import DatabaseManager
from backtesting.backtest_engine import BacktestEngine
from telegram_bot_server import TelegramBotServer
from utils.logger import logger

class TradingBot:
    def __init__(self):
        # Initialize components
        self.data_provider = DataProvider()
        self.technical_analyzer = TechnicalAnalysis(Config())
        self.ai_generator = AISignalGenerator()
        self.telegram_notifier = TelegramNotifier(Config())
        self.db_manager = DatabaseManager(Config())
        self.backtest_engine = BacktestEngine()
        
        # Initialize Telegram bot server for commands
        self.telegram_bot_server = TelegramBotServer(self)
        
        # Trading state
        self.is_running = False
        self.daily_signal_count = 0
        self.last_signals = {}
        
        # Scheduler
        self.scheduler = AsyncIOScheduler()
        
        # Initialize watchlist
        self.initialize_watchlist()
        
        # Train AI model if needed
        asyncio.create_task(self.train_ai_model_if_needed())
        
        logger.info("Trading Bot initialized successfully")
    
    def initialize_watchlist(self):
        """Initialize default watchlist"""
        try:
            # Add Nifty 50 stocks to watchlist
            for symbol in Config.NIFTY_50_SYMBOLS:
                self.db_manager.add_to_watchlist(symbol, 'EQUITY')
            
            # Add F&O symbols
            for symbol in Config.FNO_SYMBOLS:
                self.db_manager.add_to_watchlist(symbol, 'FNO')
            
            logger.info("Watchlist initialized with default symbols")
            
        except Exception as e:
            logger.error(f"Error initializing watchlist: {e}")
    
    async def start(self):
        """Start the trading bot"""
        try:
            self.is_running = True
            logger.info("Starting Trading Bot...")
            
            # Start Telegram command bot
            if self.telegram_bot_server:
                asyncio.create_task(self.telegram_bot_server.start_polling())
                logger.info("Telegram command bot started")
            
            # Test connections
            await self.test_connections()
            
            # Setup scheduled tasks
            self.setup_scheduler()
            
            # Start scheduler
            self.scheduler.start()
            
            # Send startup message
            await self.send_startup_message()
            
            # Main monitoring loop
            await self.main_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading bot: {e}")
            await self.telegram_notifier.send_error_alert(f"Bot startup failed: {str(e)}")
    
    async def test_connections(self):
        """Test all external connections"""
        logger.info("Testing connections...")
        
        # Test market data
        try:
            market_status = self.data_provider.get_market_status()
            logger.info(f"Market status: {market_status}")
        except Exception as e:
            logger.warning(f"Market data connection issue: {e}")
        
        # Test Telegram
        try:
            if self.telegram_notifier.test_connection():
                logger.info("Telegram connection successful")
            else:
                logger.warning("Telegram connection failed")
        except Exception as e:
            logger.warning(f"Telegram connection issue: {e}")
    
    def setup_scheduler(self):
        """Setup scheduled tasks"""
        try:
            # Market hours monitoring (every 10 minutes during market hours)
            self.scheduler.add_job(
                self.scan_and_generate_signals,
                CronTrigger(
                    day_of_week='mon-fri',
                    hour='9-15',
                    minute='*/10'
                ),
                id='market_scan'
            )
            
            # End of day report (after market close)
            self.scheduler.add_job(
                self.send_daily_report,
                CronTrigger(
                    day_of_week='mon-fri',
                    hour=16,
                    minute=0
                ),
                id='daily_report'
            )
            
            # Weekly performance report (Saturday morning)
            self.scheduler.add_job(
                self.send_weekly_report,
                CronTrigger(
                    day_of_week='sat',
                    hour=9,
                    minute=0
                ),
                id='weekly_report'
            )
            
            # Model training (Sunday evening)
            self.scheduler.add_job(
                self.retrain_model,
                CronTrigger(
                    day_of_week='sun',
                    hour=20,
                    minute=0
                ),
                id='model_training'
            )
            
            logger.info("Scheduler tasks configured")
            
        except Exception as e:
            logger.error(f"Error setting up scheduler: {e}")
    
    async def main_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_running:
                current_time = datetime.now()
                market_status = self.data_provider.get_market_status()
                
                if market_status.get('is_open', False):
                    # Market is open - let scheduler handle monitoring
                    logger.debug("Market is open - scheduler handling monitoring")
                else:
                    # Market is closed - reduced activity
                    logger.info("Market is closed - bot on standby")
                
                # Sleep for 5 minutes before next status check (reduced frequency)
                await asyncio.sleep(300)
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            await self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await self.telegram_notifier.send_error_alert(f"Main loop error: {str(e)}")
    
    async def monitor_market(self):
        """Monitor market during trading hours"""
        try:
            # Check if we've exceeded daily signal limit
            if self.daily_signal_count >= Config.MAX_TRADES_PER_DAY:
                logger.info(f"Daily signal limit reached: {self.daily_signal_count}")
                await self.telegram_notifier.send_custom_message(
                    f"📊 Daily signal limit reached: {self.daily_signal_count}/{Config.MAX_TRADES_PER_DAY}"
                )
                return
            
            # Get watchlist
            watchlist = self.db_manager.get_watchlist()
            
            # Rotate through symbols to avoid API limits
            # Process only 5 symbols per scan, rotating each time
            if not hasattr(self, 'symbol_index'):
                self.symbol_index = 0
            
            symbols_to_check = []
            for i in range(5):  # Check only 5 symbols per scan
                if self.symbol_index + i < len(watchlist):
                    symbols_to_check.append(watchlist[self.symbol_index + i])
            
            # Update index for next rotation
            self.symbol_index = (self.symbol_index + 5) % len(watchlist)
            
            # Send scan start notification
            current_time = datetime.now().strftime("%I:%M %p")
            scan_message = f"🔍 **Market Scan Started**\n📊 Analyzing: {', '.join(symbols_to_check)}\n⏰ {current_time}"
            await self.telegram_notifier.send_custom_message(scan_message)
            
            logger.info(f"Scanning {len(symbols_to_check)} symbols: {', '.join(symbols_to_check)}")
            
            signals_found = 0
            for symbol in symbols_to_check:
                try:
                    # Analyze symbol and check if signal was generated
                    signal_generated = await self.analyze_symbol(symbol)
                    if signal_generated:
                        signals_found += 1
                    await asyncio.sleep(2)  # Increased rate limiting
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Send scan completion notification
            next_scan_time = (datetime.now() + timedelta(minutes=10)).strftime("%I:%M %p")
            completion_message = f"📊 **Scan Complete**\n✅ Analyzed {len(symbols_to_check)} symbols\n"
            
            if signals_found == 0:
                completion_message += f"⚠️ No high-confidence signals found\n🔄 Next scan: {next_scan_time}"
            else:
                completion_message += f"🚨 Generated {signals_found} signals\n🔄 Next scan: {next_scan_time}"
                
            await self.telegram_notifier.send_custom_message(completion_message)
            
        except Exception as e:
            logger.error(f"Error monitoring market: {e}")
            await self.telegram_notifier.send_error_alert(f"Market monitoring error: {str(e)}")
    
    async def analyze_symbol(self, symbol: str) -> bool:
        """Analyze a single symbol and generate signals if needed"""
        try:
            # Get live price
            live_data = self.data_provider.get_live_price(symbol)
            if not live_data:
                return False
            
            # Get historical data for analysis (more data for better analysis)
            historical_data = self.data_provider.get_historical_data(symbol, 'day', 365)  # Get 1 year of data
            if historical_data.empty:
                logger.warning(f"No historical data available for {symbol}")
                return False
            
            # Check if we have enough data for technical analysis
            if len(historical_data) < 50:
                logger.warning(f"Insufficient data for {symbol}: only {len(historical_data)} records (need >50)")
                return False
            
            # Perform technical analysis
            analysis = self.technical_analyzer.analyze_all_indicators(historical_data)
            if not analysis:
                return False
            
            # Generate AI signal
            signal_result = self.ai_generator.predict_signal(historical_data, analysis)
            
            # Check if signal meets criteria
            if self.should_send_signal(symbol, signal_result):
                await self.process_signal(symbol, signal_result, live_data)
                return True  # Signal was generated and sent
            
            return False  # No signal generated
            
        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol}: {e}")
            return False
    
    def should_send_signal(self, symbol: str, signal_result: Dict) -> bool:
        """Determine if signal should be sent"""
        try:
            signal_type = signal_result.get('signal', 'NEUTRAL')
            confidence = signal_result.get('confidence', 0)
            
            # Don't send neutral signals
            if signal_type == 'NEUTRAL':
                return False
            
            # Check confidence threshold
            if confidence < Config.MODEL_CONFIDENCE_THRESHOLD:
                return False
            
            # Check if we recently sent a signal for this symbol
            last_signal_time = self.last_signals.get(symbol)
            if last_signal_time:
                time_diff = (datetime.now() - last_signal_time).total_seconds() / 60
                if time_diff < 30:  # Don't send signals within 30 minutes
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking signal criteria: {e}")
            return False
    
    async def process_signal(self, symbol: str, signal_result: Dict, live_data: Dict):
        """Process and send a trading signal"""
        try:
            current_price = live_data.get('price', 0)
            signal_type = signal_result.get('signal')
            confidence = signal_result.get('confidence')
            reason = signal_result.get('reason', 'Technical analysis')
            
            # Calculate target and stop loss
            target_price, stop_loss = self.calculate_levels(current_price, signal_type)
            
            # Prepare signal data
            signal_data = {
                'symbol': symbol,
                'signal': signal_type,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'confidence': confidence,
                'reason': reason,
                'timestamp': datetime.now()
            }
            
            # Store in database
            signal_id = self.db_manager.insert_signal(signal_data)
            if signal_id:
                # Send to Telegram
                success = await self.telegram_notifier.send_signal(signal_data)
                if success:
                    self.daily_signal_count += 1
                    self.last_signals[symbol] = datetime.now()
                    logger.info(f"Signal sent for {symbol}: {signal_type} at ₹{current_price:.2f}")
                else:
                    logger.error(f"Failed to send signal for {symbol}")
            
        except Exception as e:
            logger.error(f"Error processing signal for {symbol}: {e}")
    
    def calculate_levels(self, price: float, signal_type: str) -> tuple:
        """Calculate target and stop loss levels"""
        try:
            if signal_type == 'BUY':
                target = price * 1.03  # 3% target
                stop_loss = price * 0.98  # 2% stop loss
            elif signal_type == 'SELL':
                target = price * 0.97  # 3% target (price decline)
                stop_loss = price * 1.02  # 2% stop loss
            else:
                target = price
                stop_loss = price
            
            return round(target, 2), round(stop_loss, 2)
            
        except Exception as e:
            logger.error(f"Error calculating levels: {e}")
            return price, price
    
    async def scan_and_generate_signals(self):
        """Scheduled task to scan market and generate signals"""
        try:
            logger.info("Starting scheduled market scan...")
            
            # Reset daily count if new day
            current_date = datetime.now().date()
            last_reset_date = getattr(self, 'last_reset_date', None)
            
            if last_reset_date != current_date:
                self.daily_signal_count = 0
                self.last_reset_date = current_date
                logger.info("Daily signal count reset")
            
            # Perform market scan
            await self.monitor_market()
            
        except Exception as e:
            logger.error(f"Error in scheduled scan: {e}")
    
    async def send_daily_report(self):
        """Send daily performance report"""
        try:
            logger.info("Generating daily report...")
            
            # Get performance data
            performance_data = self.db_manager.get_performance_metrics(days=1)
            
            # Send report
            success = await self.telegram_notifier.send_performance_report(performance_data)
            if success:
                logger.info("Daily report sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    async def send_weekly_report(self):
        """Send weekly performance report"""
        try:
            logger.info("Generating weekly report...")
            
            # Get performance data
            performance_data = self.db_manager.get_performance_metrics(days=7)
            
            # Add additional analysis
            performance_data['report_type'] = 'Weekly'
            
            # Send report
            success = await self.telegram_notifier.send_performance_report(performance_data)
            if success:
                logger.info("Weekly report sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending weekly report: {e}")
    
    async def retrain_model(self):
        """Retrain AI model with recent data"""
        try:
            logger.info("Starting model retraining...")
            
            # Collect training data
            training_data = []
            watchlist = self.db_manager.get_watchlist()
            
            for symbol in watchlist[:20]:  # Train on top 20 symbols
                try:
                    # Get historical data
                    df = self.data_provider.get_historical_data(symbol, 'day', Config.TRAINING_DATA_DAYS)
                    if df.empty:
                        continue
                    
                    # Get technical analysis
                    analysis = self.technical_analyzer.analyze_all_indicators(df)
                    if analysis:
                        training_data.append({'df': df, 'analysis': analysis})
                    
                except Exception as e:
                    logger.error(f"Error collecting training data for {symbol}: {e}")
                    continue
            
            # Train model
            if training_data:
                success = self.ai_generator.train_model(training_data)
                if success:
                    logger.info("Model retrained successfully")
                    await self.telegram_notifier.send_custom_message("🤖 AI Model retrained successfully!")
                else:
                    logger.error("Model retraining failed")
            
        except Exception as e:
            logger.error(f"Error retraining model: {e}")
    
    async def send_startup_message(self):
        """Send startup notification"""
        try:
            market_status = self.data_provider.get_market_status()
            message = f"""
🚀 <b>Trading Bot Started Successfully</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
🕒 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
📈 <b>Market Status:</b> {'OPEN' if market_status.get('is_open') else 'CLOSED'}

🤖 <b>Bot is now monitoring the markets!</b>

<i>Ready to generate trading signals...</i>
"""
            
            await self.telegram_notifier.send_custom_message(message)
            
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
    
    async def stop(self):
        """Stop the trading bot"""
        try:
            self.is_running = False
            
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            # Stop Telegram command bot
            if self.telegram_bot_server:
                await self.telegram_bot_server.stop_polling()
                logger.info("Telegram command bot stopped")
            
            # Send shutdown message
            message = f"""
🛑 <b>Trading Bot Stopped</b>

📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
🕒 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}

📊 <b>Today's Summary:</b>
• Signals Generated: {self.daily_signal_count}

<i>Bot has been shut down safely.</i>
"""
            
            await self.telegram_notifier.send_custom_message(message)
            logger.info("Trading Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def run_backtest(self, symbol: str, days: int = 30) -> Dict:
        """Run backtest for a specific symbol"""
        try:
            # Get historical data
            df = self.data_provider.get_historical_data(symbol, 'day', days)
            if df.empty:
                return {}
            
            # Generate historical signals
            signals = []
            for i in range(len(df) - 10):  # Leave buffer for analysis
                try:
                    subset = df.iloc[:i+50]  # Use data up to this point
                    analysis = self.technical_analyzer.analyze_all_indicators(subset)
                    signal_result = self.ai_generator.predict_signal(subset, analysis)
                    
                    if signal_result.get('signal') != 'NEUTRAL':
                        signal_data = {
                            'symbol': symbol,
                            'signal': signal_result.get('signal'),
                            'entry_price': df.iloc[i]['close'],
                            'timestamp': df.iloc[i]['timestamp'] if 'timestamp' in df.columns else datetime.now(),
                            'confidence': signal_result.get('confidence', 0)
                        }
                        signals.append(signal_data)
                        
                except Exception:
                    continue
            
            # Run backtest
            results = self.backtest_engine.run_backtest(df, signals)
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest for {symbol}: {e}")
            return {}
    
    async def train_ai_model_if_needed(self):
        """Train AI model if it's not already trained"""
        try:
            if self.ai_generator.is_trained:
                logger.info("AI model already trained and ready")
                return
            
            logger.info("AI model not trained. Starting training process...")
            
            # Get training data for multiple symbols
            training_data = []
            training_symbols = Config.NIFTY_50_SYMBOLS[:10]  # Use top 10 for training
            
            for symbol in training_symbols:
                try:
                    logger.info(f"Gathering training data for {symbol}")
                    
                    # Get longer historical data for training
                    df = self.data_provider.get_historical_data(symbol, 'day', Config.TRAINING_DATA_DAYS)
                    
                    if df.empty or len(df) < 100:
                        logger.warning(f"Insufficient data for {symbol}: {len(df) if not df.empty else 0} records")
                        continue
                    
                    # Perform technical analysis
                    analysis = self.technical_analyzer.analyze_all_indicators(df)
                    if not analysis:
                        logger.warning(f"Technical analysis failed for {symbol}")
                        continue
                    
                    training_data.append({
                        'symbol': symbol,
                        'df': df,
                        'analysis': analysis
                    })
                    
                    logger.info(f"Successfully gathered {len(df)} records for {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error gathering training data for {symbol}: {e}")
                    continue
            
            if len(training_data) < 3:
                logger.warning(f"Insufficient training data: only {len(training_data)} symbols with data")
                logger.info("AI model will use rule-based signals until more data is available")
                return
            
            # Train the model
            logger.info(f"Training AI model with data from {len(training_data)} symbols...")
            success = self.ai_generator.train_model(training_data)
            
            if success:
                logger.info("AI model training completed successfully!")
                await self.telegram_notifier.send_custom_message(
                    f"🤖 <b>AI Model Training Complete</b>\n\n"
                    f"✅ Successfully trained with {len(training_data)} symbols\n"
                    f"📊 Model is now ready for signal generation"
                )
            else:
                logger.warning("AI model training failed. Using rule-based signals.")
                
        except Exception as e:
            logger.error(f"Error in AI model training: {e}")
            logger.info("Will continue with rule-based signals")

# Entry point for running the bot
async def main():
    """Main function to run the trading bot"""
    bot = TradingBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
