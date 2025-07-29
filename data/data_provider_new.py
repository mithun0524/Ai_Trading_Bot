import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import yfinance as yf
try:
    # Upstox API v2
    import upstox_client
    from upstox_client.rest import ApiException
except ImportError:
    upstox_client = None
    ApiException = None
try:
    from nsepy import get_history
except ImportError:
    get_history = None
from config import Config
from utils.logger import logger

class DataProvider:
    def __init__(self):
        self.upstox_config = None
        self.session_initialized = False
        self.init_upstox_session()
    
    def init_upstox_session(self):
        """Initialize Upstox API v2 session"""
        try:
            if Config.UPSTOX_API_KEY and Config.UPSTOX_ACCESS_TOKEN and upstox_client:
                # Configure API client
                configuration = upstox_client.Configuration()
                configuration.access_token = Config.UPSTOX_ACCESS_TOKEN
                
                # Test connection with user profile (API v2 requires api_version parameter)
                api_instance = upstox_client.UserApi(upstox_client.ApiClient(configuration))
                profile = api_instance.get_profile(api_version='2.0')
                
                self.upstox_config = configuration
                self.session_initialized = True
                logger.info(f"Upstox API v2 session initialized for user: {profile.data.user_name}")
            else:
                logger.warning("Upstox API credentials not found or upstox_client not available")
        except Exception as e:
            logger.error(f"Failed to initialize Upstox session: {e}")
            logger.info("Falling back to Yahoo Finance and other free data sources")
            self.session_initialized = False
    
    def get_live_price(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live price for a symbol using Upstox or fallback sources"""
        try:
            if self.session_initialized and self.upstox_config:
                # Use Upstox API v2 for live data
                api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(self.upstox_config))
                instrument_key = f"{exchange}:{symbol}"
                quote = api_instance.get_market_data_feed(symbol=instrument_key, api_version='2.0')
                
                if quote and quote.data:
                    data = quote.data[instrument_key]
                    return {
                        'symbol': symbol,
                        'price': data.last_price,
                        'open': data.ohlc.open,
                        'high': data.ohlc.high,
                        'low': data.ohlc.low,
                        'volume': data.volume,
                        'timestamp': datetime.now()
                    }
            
            # Fallback to yfinance for live price
            ticker = yf.Ticker(f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO")
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice')),
                'open': info.get('regularMarketOpen'),
                'high': info.get('dayHigh'),
                'low': info.get('dayLow'),
                'volume': info.get('regularMarketVolume'),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting live price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, timeframe: str = "day", 
                           days: int = 30, exchange: str = "NSE") -> pd.DataFrame:
        """Get historical data - primary method used by the bot"""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if self.session_initialized and self.upstox_config:
                return self.get_upstox_historical_data(symbol, timeframe, start_date, end_date, exchange)
            else:
                # Fallback to yfinance
                return self.get_yfinance_data(symbol, start_date, end_date, timeframe)
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_upstox_historical_data(self, symbol: str, timeframe: str, 
                                  start_date: datetime, end_date: datetime, 
                                  exchange: str = "NSE") -> pd.DataFrame:
        """Get historical data from Upstox API v2"""
        try:
            # Map timeframe to Upstox intervals
            interval_map = {
                "minute": "1minute",
                "5minute": "5minute", 
                "15minute": "15minute",
                "30minute": "30minute",
                "hour": "1hour",
                "day": "1day"
            }
            
            interval = interval_map.get(timeframe, "1day")
            instrument_key = f"{exchange}:{symbol}"
            
            api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(self.upstox_config))
            
            history = api_instance.get_historical_candle_data(
                instrument_key=instrument_key,
                interval=interval,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d'),
                api_version='2.0'
            )
            
            if history and history.data and history.data.candles:
                # Convert to DataFrame
                df = pd.DataFrame(history.data.candles, 
                                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()
                
                logger.info(f"Retrieved {len(df)} historical records from Upstox for {symbol}")
                return df
            else:
                logger.warning(f"No historical data from Upstox for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting Upstox historical data: {e}")
            # Fallback to yfinance
            return self.get_yfinance_data(symbol, start_date, end_date, timeframe)
    
    def get_yfinance_data(self, symbol: str, start_date: datetime, 
                         end_date: datetime, timeframe: str = "day") -> pd.DataFrame:
        """Get historical data from Yahoo Finance"""
        try:
            # Map timeframe to yfinance intervals
            interval_map = {
                "minute": "1m",
                "5minute": "5m",
                "15minute": "15m", 
                "30minute": "30m",
                "hour": "1h",
                "day": "1d"
            }
            
            interval = interval_map.get(timeframe, "1d")
            
            # Add .NS for NSE or .BO for BSE
            yf_symbol = f"{symbol}.NS"
            
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=interval
            )
            
            if not df.empty:
                # Rename columns to match our format
                df.columns = [col.lower() for col in df.columns]
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                logger.info(f"Retrieved {len(df)} historical records from Yahoo Finance for {symbol}")
                return df
            else:
                logger.warning(f"No data from Yahoo Finance for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting YFinance data: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators on price data"""
        try:
            if df.empty or len(df) < 20:
                logger.warning("Insufficient data for technical analysis")
                return df
            
            # Import technical analysis
            from analysis.technical_analysis import TechnicalAnalysis
            
            # Create TA instance with minimal config
            config = Config()
            ta = TechnicalAnalysis(config)
            
            # Calculate indicators
            analyzed_df = ta.calculate_indicators(df)
            
            return analyzed_df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def get_fno_data(self, symbol: str, expiry_date: str = None) -> List[Dict]:
        """Get F&O data - simplified for non-Kite sources"""
        try:
            # For now, return basic F&O info using yfinance
            # This is a simplified implementation
            base_symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK']
            
            if symbol in base_symbols:
                return [{
                    'symbol': symbol,
                    'expiry': expiry_date or 'Current Month',
                    'type': 'INDEX' if symbol in ['NIFTY', 'BANKNIFTY'] else 'STOCK',
                    'lot_size': 50 if symbol in ['NIFTY', 'BANKNIFTY'] else 25
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting F&O data: {e}")
            return []
    
    def get_nse_live_price(self, symbol: str) -> Optional[Dict]:
        """Get live price from NSE (basic implementation)"""
        try:
            # This is a simplified implementation
            # In practice, you might use NSE API or other sources
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('currentPrice', info.get('regularMarketPrice')),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting NSE live price: {e}")
            return None
