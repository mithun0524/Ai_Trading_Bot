#!/usr/bin/env python3
"""
🔗 SYSTEM INTEGRATION CONNECTOR
Connects live trading system with existing AI model and data providers
"""

import sys
import os
import asyncio
import importlib.util
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.extend([
    str(project_root),
    str(project_root / 'src' / 'core'),
    str(project_root / 'data'),
    str(project_root / 'ai'),
    str(project_root / 'analysis'),
    str(project_root / 'utils')
])

class SystemIntegrator:
    """Integrates all system components"""
    
    def __init__(self):
        self.components = {}
        self.initialized = False
        
    def load_existing_components(self):
        """Load existing system components"""
        print("🔗 Loading existing system components...")
        
        try:
            # Load configuration
            try:
                from src.core.config import Config
                self.components['config'] = Config()
                print("   ✅ Configuration loaded")
            except ImportError:
                print("   ⚠ Configuration not found, using defaults")
                self.components['config'] = self.create_default_config()
            
            # Load data provider
            try:
                from data.data_provider import DataProvider
                self.components['data_provider'] = DataProvider()
                print("   ✅ Data provider loaded")
            except ImportError:
                print("   ⚠ Data provider not found, using fallback")
                self.components['data_provider'] = None
            
            # Load AI signal generator
            try:
                from ai.signal_generator import AISignalGenerator
                self.components['ai_generator'] = AISignalGenerator()
                print("   ✅ AI signal generator loaded")
            except ImportError:
                print("   ⚠ AI generator not found, using built-in")
                self.components['ai_generator'] = None
            
            # Load technical analysis
            try:
                from analysis.technical_analysis import TechnicalAnalysis
                self.components['technical_analysis'] = TechnicalAnalysis(self.components['config'])
                print("   ✅ Technical analysis loaded")
            except ImportError:
                print("   ⚠ Technical analysis not found, using built-in")
                self.components['technical_analysis'] = None
            
            # Load logger
            try:
                from utils.logger import logger
                self.components['logger'] = logger
                print("   ✅ Logger loaded")
            except ImportError:
                import logging
                logging.basicConfig(level=logging.INFO)
                self.components['logger'] = logging.getLogger(__name__)
                print("   ⚠ Custom logger not found, using default")
            
            self.initialized = True
            print("✅ System components integration completed")
            
        except Exception as e:
            print(f"❌ Error loading components: {e}")
            self.create_fallback_components()
    
    def create_default_config(self):
        """Create default configuration"""
        class DefaultConfig:
            # Trading parameters
            RISK_PERCENTAGE = 2.0
            MAX_TRADES_PER_DAY = 10
            MARKET_START_TIME = '09:15'
            MARKET_END_TIME = '15:30'
            
            # Technical indicators
            RSI_PERIOD = 14
            RSI_OVERSOLD = 30
            RSI_OVERBOUGHT = 70
            MACD_FAST = 12
            MACD_SLOW = 26
            MACD_SIGNAL = 9
            BB_PERIOD = 20
            BB_STD = 2
            
            # AI model
            MODEL_CONFIDENCE_THRESHOLD = 70
            TRAINING_DATA_DAYS = 1000
            
            # Watchlist
            NIFTY_50_SYMBOLS = [
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
                'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT',
                'HCLTECH', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA'
            ]
            
            FNO_SYMBOLS = [
                'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK',
                'INFY', 'ICICIBANK', 'ITC', 'SBIN', 'BHARTIARTL'
            ]
        
        return DefaultConfig()
    
    def create_fallback_components(self):
        """Create fallback components if imports fail"""
        print("🔧 Creating fallback components...")
        
        # Fallback data provider
        if not self.components.get('data_provider'):
            class FallbackDataProvider:
                def get_historical_data(self, symbol, timeframe, days):
                    import yfinance as yf
                    ticker = yf.Ticker(f"{symbol}.NS")
                    data = ticker.history(period=f"{days}d")
                    if data.empty:
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period=f"{days}d")
                    return data
                
                def get_live_quote(self, symbol):
                    import yfinance as yf
                    ticker = yf.Ticker(f"{symbol}.NS")
                    info = ticker.history(period="1d", interval="1m")
                    if info.empty:
                        ticker = yf.Ticker(symbol)
                        info = ticker.history(period="1d", interval="1m")
                    
                    if not info.empty:
                        latest = info.iloc[-1]
                        return {
                            'symbol': symbol,
                            'price': float(latest['Close']),
                            'volume': int(latest['Volume']),
                            'timestamp': latest.name
                        }
                    return None
            
            self.components['data_provider'] = FallbackDataProvider()
            print("   ✅ Fallback data provider created")
        
        # Fallback AI generator
        if not self.components.get('ai_generator'):
            class FallbackAIGenerator:
                def predict_signal(self, df, analysis):
                    # Simple rule-based fallback
                    if df.empty or len(df) < 20:
                        return {'signal': 'HOLD', 'confidence': 0}
                    
                    # Simple moving average crossover
                    sma_short = df['Close'].rolling(5).mean()
                    sma_long = df['Close'].rolling(20).mean()
                    
                    if sma_short.iloc[-1] > sma_long.iloc[-1] and sma_short.iloc[-2] <= sma_long.iloc[-2]:
                        return {'signal': 'BUY', 'confidence': 75}
                    elif sma_short.iloc[-1] < sma_long.iloc[-1] and sma_short.iloc[-2] >= sma_long.iloc[-2]:
                        return {'signal': 'SELL', 'confidence': 75}
                    else:
                        return {'signal': 'HOLD', 'confidence': 50}
                
                def train_model(self, training_data):
                    print("Fallback AI: Using rule-based signals")
                    return True
            
            self.components['ai_generator'] = FallbackAIGenerator()
            print("   ✅ Fallback AI generator created")
        
        self.initialized = True
    
    def get_component(self, name):
        """Get system component"""
        return self.components.get(name)
    
    def integrate_with_live_system(self):
        """Integrate components with live trading system"""
        if not self.initialized:
            self.load_existing_components()
        
        print("🔗 Integrating with live trading system...")
        
        # Import live trading system
        from live_trading_system import LiveTradingManager, AISignalGenerator as LiveAI
        
        # Create enhanced live trading manager
        class IntegratedLiveTradingManager(LiveTradingManager):
            def __init__(self, integrator, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.integrator = integrator
                self.existing_data_provider = integrator.get_component('data_provider')
                self.existing_ai_generator = integrator.get_component('ai_generator')
                self.config = integrator.get_component('config')
                
                # Use existing watchlist if available
                if hasattr(self.config, 'NIFTY_50_SYMBOLS'):
                    self.watchlist = self.config.NIFTY_50_SYMBOLS[:15]  # First 15 for performance
                
                print("   ✅ Integrated existing components with live system")
            
            def get_historical_data(self, symbol: str, days: int = 100):
                """Use existing data provider if available"""
                try:
                    if self.existing_data_provider:
                        return self.existing_data_provider.get_historical_data(symbol, 'day', days)
                    else:
                        return super().get_historical_data(symbol, days)
                except Exception as e:
                    self.integrator.get_component('logger').error(f"Error getting historical data: {e}")
                    return super().get_historical_data(symbol, days)
        
        # Create enhanced AI signal generator
        class IntegratedAIGenerator(LiveAI):
            def __init__(self, integrator):
                super().__init__()
                self.integrator = integrator
                self.existing_ai = integrator.get_component('ai_generator')
                self.technical_analysis = integrator.get_component('technical_analysis')
                self.config = integrator.get_component('config')
                
            def analyze_live_data(self, symbol: str, quote, historical_data):
                """Enhanced analysis using existing AI and technical analysis"""
                try:
                    # Try using existing AI generator first
                    if self.existing_ai and hasattr(self.existing_ai, 'predict_signal'):
                        # Use existing technical analysis if available
                        if self.technical_analysis:
                            analysis = self.technical_analysis.analyze_all_indicators(historical_data)
                            existing_signal = self.existing_ai.predict_signal(historical_data, analysis)
                            
                            # Enhance with live data context
                            if existing_signal:
                                confidence_boost = 0
                                reasons = existing_signal.get('reasons', [])
                                
                                # Add momentum analysis
                                if quote.change_percent > 2:
                                    confidence_boost += 10
                                    reasons.append(f"Strong upward momentum ({quote.change_percent:.1f}%)")
                                elif quote.change_percent < -2:
                                    confidence_boost += 10
                                    reasons.append(f"Strong downward momentum ({quote.change_percent:.1f}%)")
                                
                                # Add volume analysis
                                if hasattr(quote, 'volume') and quote.volume > 0:
                                    avg_volume = historical_data['Volume'].tail(20).mean()
                                    if quote.volume > avg_volume * 1.5:
                                        confidence_boost += 5
                                        reasons.append("High volume activity")
                                
                                return {
                                    'symbol': symbol,
                                    'signal': existing_signal.get('signal', 'HOLD'),
                                    'confidence': min(95, existing_signal.get('confidence', 50) + confidence_boost),
                                    'reasons': reasons,
                                    'technical_data': existing_signal.get('technical_data', {}),
                                    'timestamp': quote.timestamp.isoformat(),
                                    'source': 'integrated_ai'
                                }
                    
                    # Fallback to built-in analysis
                    return super().analyze_live_data(symbol, quote, historical_data)
                    
                except Exception as e:
                    self.integrator.get_component('logger').error(f"Error in integrated AI analysis: {e}")
                    return super().analyze_live_data(symbol, quote, historical_data)
        
        return IntegratedLiveTradingManager, IntegratedAIGenerator

def main():
    """Main integration function"""
    print("🚀 COMPLETE SYSTEM INTEGRATION")
    print("=" * 60)
    
    try:
        # Initialize integrator
        integrator = SystemIntegrator()
        integrator.load_existing_components()
        
        # Get integrated components
        LiveTradingManager, AIGenerator = integrator.integrate_with_live_system()
        
        print("\n🔥 Starting Integrated Live Trading System...")
        print("Features:")
        print("  📊 Live stock data from multiple sources")
        print("  🤖 Your existing AI model + enhanced live analysis")
        print("  📈 Real-time technical analysis")
        print("  💰 Virtual trading with Rs.10,00,000")
        print("  🌐 Web dashboard with live updates")
        print("  🔄 Synchronized components")
        print("=" * 60)
        
        # Import and modify live system
        import live_trading_system
        
        # Replace components
        live_trading_system.LiveTradingManager = LiveTradingManager
        live_trading_system.AISignalGenerator = AIGenerator
        
        # Initialize with integrator
        live_trading_system.trading_manager = LiveTradingManager(integrator)
        
        # Setup enhanced AI
        live_trading_system.trading_manager.ai_generator = AIGenerator(integrator)
        
        print("✅ Integration complete! Starting system...")
        
        # Setup real-time updates
        live_trading_system.setup_realtime_updates()
        
        # Start background tasks
        def start_background_tasks():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(live_trading_system.trading_manager.start_live_trading())
            except Exception as e:
                print(f"Background task error: {e}")
        
        import threading
        background_thread = threading.Thread(target=start_background_tasks, daemon=True)
        background_thread.start()
        
        print("\n🌐 Web dashboard starting at http://localhost:5000")
        print("💡 Open your browser to view the live dashboard")
        print("🔄 System will start fetching live data...")
        print("\nPress Ctrl+C to stop the system")
        print("=" * 60)
        
        # Start Flask app
        live_trading_system.socketio.run(
            live_trading_system.app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Integrated system stopped by user")
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Falling back to simple live system...")
        # Fallback to simple system
        import live_trading_system
        live_trading_system.socketio.run(
            live_trading_system.app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"\n❌ System error: {e}")
        print("Check the error above and try again.")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()
