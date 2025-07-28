import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Upstox API (Primary Data Source)
    UPSTOX_API_KEY = os.getenv('UPSTOX_API_KEY')
    UPSTOX_API_SECRET = os.getenv('UPSTOX_API_SECRET')
    UPSTOX_ACCESS_TOKEN = os.getenv('UPSTOX_ACCESS_TOKEN')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading_bot.db')
    
    # Trading Parameters
    RISK_PERCENTAGE = float(os.getenv('RISK_PERCENTAGE', 2.0))
    MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 10))
    MARKET_START_TIME = os.getenv('MARKET_START_TIME', '09:15')
    MARKET_END_TIME = os.getenv('MARKET_END_TIME', '15:30')
    
    # Technical Indicators
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', 14))
    RSI_OVERSOLD = float(os.getenv('RSI_OVERSOLD', 30))
    RSI_OVERBOUGHT = float(os.getenv('RSI_OVERBOUGHT', 70))
    MACD_FAST = int(os.getenv('MACD_FAST', 12))
    MACD_SLOW = int(os.getenv('MACD_SLOW', 26))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', 9))
    BB_PERIOD = int(os.getenv('BB_PERIOD', 20))
    BB_STD = float(os.getenv('BB_STD', 2))
    
    # AI Model
    MODEL_CONFIDENCE_THRESHOLD = float(os.getenv('MODEL_CONFIDENCE_THRESHOLD', 70))
    BACKTEST_DAYS = int(os.getenv('BACKTEST_DAYS', 252))
    TRAINING_DATA_DAYS = int(os.getenv('TRAINING_DATA_DAYS', 1000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading_bot.log')
    
    # NSE/BSE Stocks Watchlist
    NIFTY_50_SYMBOLS = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC',
        'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 'ASIANPAINT', 'AXISBANK',
        'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'BAJFINANCE',
        'WIPRO', 'ONGC', 'TATAMOTORS', 'TECHM', 'POWERGRID', 'NTPC', 'TATASTEEL',
        'DIVISLAB', 'GRASIM', 'M&M', 'BAJAJFINSV', 'HINDALCO', 'INDUSINDBK',
        'ADANIENT', 'COALINDIA', 'HDFCLIFE', 'SBILIFE', 'BPCL', 'CIPLA',
        'EICHERMOT', 'HEROMOTOCO', 'APOLLOHOSP', 'DRREDDY', 'BRITANNIA',
        'TATACONSUM', 'JSWSTEEL', 'UPL', 'BAJAJ-AUTO', 'LTIM', 'ADANIPORTS'
    ]
    
    # F&O Instruments
    FNO_SYMBOLS = [
        'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 'ASIANPAINT',
        'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN', 'ULTRACEMCO', 'BAJFINANCE'
    ]
    
    # Timeframes for analysis
    TIMEFRAMES = ['5minute', '15minute', 'hour', 'day']
    
    def get(self, key, default=None):
        """Get configuration value with default fallback"""
        return getattr(self, key, default)
