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
from utils.upstox_instruments import get_upstox_instrument_key, is_symbol_supported

class DataProvider:
    def __init__(self):
        self.upstox_config = None
        self.session_initialized = False
        self.init_upstox_session()
    
    def init_upstox_session(self):
        """Initialize Upstox API v2 session (optional enhancement)"""
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
                logger.info(f"Upstox API v2 connected: {profile.data.user_name}")
                logger.info("Using Upstox + Yahoo Finance for data")
            else:
                logger.info("Upstox credentials not configured, using Yahoo Finance only")
                self.session_initialized = False
        except Exception as e:
            logger.warning(f"Upstox connection failed: {e}")
            logger.info("Falling back to Yahoo Finance (this is fine for basic operations)")
            self.session_initialized = False
    
    def get_live_price(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live price for a symbol using Yahoo Finance primarily"""
        try:
            # Primary: Use Yahoo Finance (most reliable for Indian stocks)
            ticker = yf.Ticker(f"{symbol}.NS" if exchange == "NSE" else f"{symbol}.BO")
            info = ticker.info
            
            if info and info.get('regularMarketPrice'):
                return {
                    'symbol': symbol,
                    'price': info.get('currentPrice', info.get('regularMarketPrice')),
                    'open': info.get('regularMarketOpen'),
                    'high': info.get('dayHigh'),
                    'low': info.get('dayLow'),
                    'volume': info.get('regularMarketVolume'),
                    'timestamp': datetime.now()
                }
            
            # Optional: Try Upstox if Yahoo Finance fails (for future enhancement)
            if self.session_initialized and self.upstox_config:
                try:
                    api_instance = upstox_client.MarketQuoteApi(upstox_client.ApiClient(self.upstox_config))
                    
                    # Use correct Upstox v2 instrument key format
                    instrument_key = get_upstox_instrument_key(symbol, exchange)
                    
                    if is_symbol_supported(symbol):
                        try:
                            quote = api_instance.ltp(instrument_key, api_version='2.0')
                            if quote and quote.data:
                                data = quote.data[instrument_key]
                                return {
                                    'symbol': symbol,
                                    'price': data.last_price,
                                    'volume': getattr(data, 'volume', 0),
                                    'timestamp': datetime.now()
                                }
                        except Exception as upstox_err:
                            logger.debug(f"Upstox live price failed for {symbol}: {upstox_err}")
                    else:
                        logger.debug(f"Symbol {symbol} not supported in Upstox mapping")
                            
                except Exception as e:
                    logger.debug(f"Upstox live price failed: {e}")
            
            return None
            
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
            
            # Primary: Use Yahoo Finance (most reliable)
            df = self.get_yfinance_data(symbol, start_date, end_date, timeframe)
            
            # If we don't get enough data, try extending the date range
            if df.empty or len(df) < 50:  # Need more data for proper analysis
                logger.info(f"Insufficient data for {symbol}, trying extended date range...")
                extended_days = min(days * 3, 2000)  # Try triple the days, max 2000
                extended_start = end_date - timedelta(days=extended_days)
                df = self.get_yfinance_data(symbol, extended_start, end_date, timeframe)
            
            if not df.empty and len(df) >= 50:
                logger.info(f"Got {len(df)} records from Yahoo Finance for {symbol}")
                return df
            
            # Optional: Try Upstox if Yahoo Finance fails (for future enhancement)
            if self.session_initialized and self.upstox_config:
                try:
                    logger.info("Attempting Upstox as fallback...")
                    return self.get_upstox_historical_data(symbol, timeframe, start_date, end_date, exchange)
                except Exception as upstox_error:
                    logger.warning(f"Upstox API failed: {upstox_error}")
            
            logger.warning(f"Insufficient data for technical analysis: {symbol} has {len(df) if not df.empty else 0} records (need >50)")
            return pd.DataFrame()
                
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
                "day": "day"  # Upstox expects "day" not "1day"
            }
            
            interval = interval_map.get(timeframe, "day")
            
            # Get correct Upstox instrument key
            instrument_key = get_upstox_instrument_key(symbol, exchange)
            
            if not is_symbol_supported(symbol):
                logger.warning(f"Symbol {symbol} not in Upstox mapping, trying generic format")
            
            api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(self.upstox_config))
            
            # Upstox API v2 correct method call
            history = api_instance.get_historical_candle_data(
                instrument_key,
                interval,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if history and history.data and history.data.candles:
                # Convert to DataFrame - Upstox v2 returns 7 columns
                # Format: [timestamp, open, high, low, close, volume, open_interest]
                df = pd.DataFrame(history.data.candles, 
                                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'open_interest'])
                
                # Keep only the columns we need
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
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

    def get_market_status(self) -> Dict:
        """Get current market status"""
        try:
            from datetime import datetime
            import pytz
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            current_time = now.time()
            
            # Market hours: 9:15 AM to 3:30 PM IST (Monday to Friday)
            market_start = datetime.strptime("09:15", "%H:%M").time()
            market_end = datetime.strptime("15:30", "%H:%M").time()
            
            is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
            is_market_hours = market_start <= current_time <= market_end
            
            if is_weekday and is_market_hours:
                status = "OPEN"
            elif is_weekday and current_time < market_start:
                status = "PRE_MARKET"
            elif is_weekday and current_time > market_end:
                status = "CLOSED"
            else:
                status = "WEEKEND"
            
            logger.info(f"Market status check: {now.strftime('%Y-%m-%d %H:%M:%S IST')}, Status: {status}")
            
            return {
                'status': status,
                'timestamp': now,
                'message': f"Market is {status.lower()}",
                'is_open': status == "OPEN"
            }
            
        except ImportError:
            # Fallback without pytz
            now = datetime.now()
            current_time = now.time()
            
            # Assume local time is IST for now
            market_start = datetime.strptime("09:15", "%H:%M").time()
            market_end = datetime.strptime("15:30", "%H:%M").time()
            
            is_weekday = now.weekday() < 5
            is_market_hours = market_start <= current_time <= market_end
            
            if is_weekday and is_market_hours:
                status = "OPEN"
            elif is_weekday and current_time < market_start:
                status = "PRE_MARKET"
            elif is_weekday and current_time > market_end:
                status = "CLOSED"
            else:
                status = "WEEKEND"
            
            logger.info(f"Market status check (no timezone): {now.strftime('%Y-%m-%d %H:%M:%S')}, Status: {status}")
            
            return {
                'status': status,
                'timestamp': now,
                'message': f"Market is {status.lower()}",
                'is_open': status == "OPEN"
            }
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {
                'status': 'OPEN',  # Default to open during debugging
                'timestamp': datetime.now(),
                'message': 'Market status check failed - assuming open',
                'is_open': True
            }
