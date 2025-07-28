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
        self.init_sessions()
    
    def init_sessions(self):
        """Initialize API sessions - Upstox primary, fallback to free sources"""
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
    
    def init_kite_session(self):
        """Initialize Kite Connect session (fallback)"""
    def get_live_price(self, symbol: str, exchange: str = "NSE") -> Optional[Dict]:
        """Get live price for a symbol"""
        try:
            if self.session_initialized:
                # Use Kite Connect for live data
                instrument_token = self.get_instrument_token(symbol, exchange)
                if instrument_token:
                    quote = self.kite.quote(f"{exchange}:{symbol}")
                    if quote and f"{exchange}:{symbol}" in quote:
                        data = quote[f"{exchange}:{symbol}"]
                        return {
                            'symbol': symbol,
                            'price': data['last_price'],
                            'open': data['ohlc']['open'],
                            'high': data['ohlc']['high'],
                            'low': data['ohlc']['low'],
                            'close': data['ohlc']['close'],
                            'volume': data['volume'],
                            'timestamp': datetime.now()
                        }
            
            # Fallback to NSE API
            return self.get_nse_live_price(symbol)
            
        except Exception as e:
            logger.error(f"Error getting live price for {symbol}: {e}")
            return None
    
    def get_nse_live_price(self, symbol: str) -> Optional[Dict]:
        """Get live price from NSE website"""
        try:
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price_info = data.get('priceInfo', {})
                
                return {
                    'symbol': symbol,
                    'price': price_info.get('lastPrice', 0),
                    'open': price_info.get('open', 0),
                    'high': price_info.get('intraDayHighLow', {}).get('max', 0),
                    'low': price_info.get('intraDayHighLow', {}).get('min', 0),
                    'close': price_info.get('previousClose', 0),
                    'volume': 0,  # Volume not available in this API
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.error(f"Error getting NSE live price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, timeframe: str = "day", 
                          days: int = 100, exchange: str = "NSE") -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if self.session_initialized:
                return self.get_kite_historical_data(symbol, timeframe, start_date, end_date, exchange)
            else:
                return self.get_yfinance_data(symbol, start_date, end_date, timeframe)
                
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_kite_historical_data(self, symbol: str, timeframe: str, 
                               start_date: datetime, end_date: datetime,
                               exchange: str = "NSE") -> pd.DataFrame:
        """Get historical data from Kite Connect"""
        try:
            instrument_token = self.get_instrument_token(symbol, exchange)
            if not instrument_token:
                return pd.DataFrame()
            
            # Map timeframe
            interval_map = {
                '5minute': '5minute',
                '15minute': '15minute',
                'hour': '60minute',
                'day': 'day'
            }
            
            interval = interval_map.get(timeframe, 'day')
            
            records = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=start_date.date(),
                to_date=end_date.date(),
                interval=interval
            )
            
            if records:
                df = pd.DataFrame(records)
                df['timestamp'] = pd.to_datetime(df['date'])
                df = df.rename(columns={
                    'open': 'open',
                    'high': 'high', 
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error getting Kite historical data: {e}")
            
        return pd.DataFrame()
    
    def get_yfinance_data(self, symbol: str, start_date: datetime, 
                         end_date: datetime, timeframe: str = "day") -> pd.DataFrame:
        """Get historical data from Yahoo Finance"""
        try:
            # Convert NSE symbol to Yahoo Finance format
            if not symbol.endswith('.NS'):
                yf_symbol = f"{symbol}.NS"
            else:
                yf_symbol = symbol
            
            # Map timeframe
            interval_map = {
                '5minute': '5m',
                '15minute': '15m',
                'hour': '1h',
                'day': '1d'
            }
            
            interval = interval_map.get(timeframe, '1d')
            period = None
            
            # For intraday data, use period instead of start/end dates
            if interval in ['5m', '15m', '1h']:
                period = '5d'  # Last 5 days for intraday
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(period=period, interval=interval)
            else:
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if not df.empty:
                df.reset_index(inplace=True)
                df['timestamp'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date'])
                df = df.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low', 
                    'Close': 'close',
                    'Volume': 'volume'
                })
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Error getting Yahoo Finance data for {symbol}: {e}")
            
        return pd.DataFrame()
    
    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """Get instrument token for Kite Connect"""
        try:
            if not self.session_initialized:
                return None
                
            instruments = self.kite.instruments(exchange)
            for instrument in instruments:
                if instrument['tradingsymbol'] == symbol:
                    return instrument['instrument_token']
            
            logger.warning(f"Instrument token not found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument token: {e}")
            return None
    
    def get_fno_data(self, symbol: str, expiry_date: str = None) -> List[Dict]:
        """Get F&O data for a symbol"""
        try:
            if not self.session_initialized:
                logger.warning("Kite session not initialized, cannot fetch F&O data")
                return []
            
            # Get instruments
            instruments = self.kite.instruments("NFO")  # National Stock Exchange F&O
            
            fno_data = []
            for instrument in instruments:
                if (instrument['name'] == symbol or instrument['tradingsymbol'].startswith(symbol)) and \
                   instrument['segment'] == 'NFO-OPT':
                    
                    if expiry_date is None or instrument['expiry'] == expiry_date:
                        try:
                            quote = self.kite.quote(f"NFO:{instrument['tradingsymbol']}")
                            if quote and f"NFO:{instrument['tradingsymbol']}" in quote:
                                data = quote[f"NFO:{instrument['tradingsymbol']}"]
                                fno_data.append({
                                    'symbol': instrument['tradingsymbol'],
                                    'strike': instrument['strike'],
                                    'expiry': instrument['expiry'],
                                    'option_type': instrument['instrument_type'],
                                    'price': data['last_price'],
                                    'volume': data['volume'],
                                    'oi': data['oi']
                                })
                        except:
                            continue
            
            return fno_data
            
        except Exception as e:
            logger.error(f"Error getting F&O data for {symbol}: {e}")
            return []
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        try:
            current_time = datetime.now().time()
            market_start = datetime.strptime(Config.MARKET_START_TIME, "%H:%M").time()
            market_end = datetime.strptime(Config.MARKET_END_TIME, "%H:%M").time()
            
            is_open = market_start <= current_time <= market_end
            
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            is_weekday = datetime.now().weekday() < 5
            
            return {
                'is_open': is_open and is_weekday,
                'current_time': current_time.strftime("%H:%M"),
                'market_start': Config.MARKET_START_TIME,
                'market_end': Config.MARKET_END_TIME,
                'is_weekday': is_weekday
            }
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {'is_open': False}
    
    def get_top_gainers_losers(self, limit: int = 10) -> Dict:
        """Get top gainers and losers"""
        try:
            # This would require live market data
            # For now, return sample structure
            return {
                'gainers': [],
                'losers': []
            }
        except Exception as e:
            logger.error(f"Error getting gainers/losers: {e}")
            return {'gainers': [], 'losers': []}
