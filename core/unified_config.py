#!/usr/bin/env python3
"""
🎯 UNIFIED AI TRADING PLATFORM - Core Configuration
Central configuration hub for all system components
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class UnifiedConfig:
    """Unified configuration for the entire AI trading platform"""
    
    # ================================
    # SYSTEM CONFIGURATION
    # ================================
    PLATFORM_NAME: str = "Apex AI Trading Platform"
    VERSION: str = "1.0.0"
    DEBUG_MODE: bool = False
    
    # ================================
    # DATABASE CONFIGURATION
    # ================================
    DATABASE_URL: str = "sqlite:///trading_platform.db"
    DATABASE_ECHO: bool = False
    
    # ================================
    # WEB SERVER CONFIGURATION
    # ================================
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 5000  # Flask default
    SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "trading_platform_secret_2025")
    
    # ================================
    # API CREDENTIALS
    # ================================
    UPSTOX_API_KEY: str = os.getenv('UPSTOX_API_KEY', '')
    UPSTOX_API_SECRET: str = os.getenv('UPSTOX_API_SECRET', '')
    UPSTOX_ACCESS_TOKEN: str = os.getenv('UPSTOX_ACCESS_TOKEN', '')
    
    # Alpha Vantage API for backup data source
    ALPHA_VANTAGE_API_KEY: str = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # ================================
    # TELEGRAM BOT CONFIGURATION
    # ================================
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
    TELEGRAM_ENABLED: bool = bool(os.getenv('TELEGRAM_BOT_TOKEN'))
    
    # ================================
    # TRADING CONFIGURATION
    # ================================
    INITIAL_VIRTUAL_BALANCE: float = 1000000.0  # Rs. 10 Lakhs
    INITIAL_CAPITAL: float = 1000000.0  # Alias for INITIAL_VIRTUAL_BALANCE
    MAX_POSITION_SIZE: float = 0.1  # 10% of portfolio per position
    MAX_TRADES_PER_DAY: int = 20
    RISK_PERCENTAGE: float = 2.0  # 2% risk per trade
    
    # ================================
    # MARKET TIMING
    # ================================
    MARKET_START_TIME: str = "09:15"
    MARKET_END_TIME: str = "15:30"
    TIMEZONE: str = "Asia/Kolkata"
    
    # ================================
    # TECHNICAL ANALYSIS PARAMETERS
    # ================================
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: float = 30
    RSI_OVERBOUGHT: float = 70
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BB_PERIOD: int = 20
    BB_STD: float = 2
    SMA_SHORT: int = 20
    SMA_LONG: int = 50
    EMA_SHORT: int = 12
    EMA_LONG: int = 26
    
    # ================================
    # AI MODEL CONFIGURATION
    # ================================
    AI_MODEL_CONFIDENCE_THRESHOLD: float = 70.0
    MIN_SIGNAL_CONFIDENCE: float = 70.0  # Minimum confidence for signal execution
    AI_SIGNAL_REFRESH_INTERVAL: int = 5  # seconds
    HISTORICAL_DATA_DAYS: int = 365
    TRAINING_DATA_DAYS: int = 1000
    
    # ================================
    # LIVE DATA CONFIGURATION
    # ================================
    LIVE_DATA_UPDATE_INTERVAL: int = 1  # seconds
    DATA_SOURCE_TIMEOUT: int = 10  # seconds
    MAX_RETRIES: int = 3
    
    # ================================
    # STOCK WATCHLISTS
    # ================================
    
    # Primary Indian stocks with high liquidity
    NIFTY_50_SYMBOLS: List[str] = field(default_factory=lambda: [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'HINDUNILVR', 'ITC', 'BHARTIARTL', 'KOTAKBANK', 'LT',
        'HCLTECH', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA',
        'TITAN', 'ULTRACEMCO', 'NESTLEIND', 'BAJFINANCE', 'WIPRO',
        'ONGC', 'TATAMOTORS', 'TECHM', 'POWERGRID', 'NTPC'
    ])
    
    # F&O enabled stocks
    FNO_SYMBOLS: List[str] = field(default_factory=lambda: [
        'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK',
        'INFY', 'ICICIBANK', 'ITC', 'BHARTIARTL', 'KOTAKBANK',
        'LT', 'HCLTECH', 'ASIANPAINT', 'AXISBANK', 'MARUTI'
    ])
    
    # Active trading watchlist (optimized for live trading)
    ACTIVE_WATCHLIST: List[str] = field(default_factory=lambda: [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
        'ITC', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH',
        'ASIANPAINT', 'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN'
    ])
    
    # International stocks for diversification
    INTERNATIONAL_SYMBOLS: List[str] = field(default_factory=lambda: [
        'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN',
        'NVDA', 'META', 'NFLX', 'CRM', 'ADBE'
    ])
    
    # ================================
    # NOTIFICATION SETTINGS
    # ================================
    ENABLE_NOTIFICATIONS: bool = True
    SIGNAL_NOTIFICATION_THRESHOLD: float = 75.0  # Only notify for high confidence signals
    PORTFOLIO_ALERT_THRESHOLD: float = 5.0  # Alert on 5% portfolio change
    
    # ================================
    # LOGGING CONFIGURATION
    # ================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "trading_platform.log"
    MAX_LOG_SIZE: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ================================
    # DASHBOARD CONFIGURATION
    # ================================
    DASHBOARD_REFRESH_INTERVAL: int = 5  # seconds
    CHART_DATA_POINTS: int = 100
    ENABLE_LIVE_CHARTS: bool = True
    
    # ================================
    # PERFORMANCE SETTINGS
    # ================================
    MAX_CONCURRENT_REQUESTS: int = 10
    REQUEST_TIMEOUT: int = 30
    CACHE_DURATION: int = 60  # seconds
    
    # ================================
    # BACKUP AND RECOVERY
    # ================================
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    MAX_BACKUP_FILES: int = 7
    
    # ================================
    # FEATURE FLAGS
    # ================================
    ENABLE_AI_SIGNALS: bool = True
    ENABLE_PAPER_TRADING: bool = True
    ENABLE_LIVE_DATA: bool = True
    ENABLE_TELEGRAM_BOT: bool = True
    ENABLE_WEB_DASHBOARD: bool = True
    ENABLE_API_ENDPOINTS: bool = True
    ENABLE_BACKTESTING: bool = True
    ENABLE_TECHNICAL_ANALYSIS: bool = True
    
    @property
    def FEATURES(self) -> Dict[str, bool]:
        """Feature flags dictionary for backward compatibility"""
        return {
            'AUTO_TRADING': self.ENABLE_AI_SIGNALS,
            'LIVE_DATA': self.ENABLE_LIVE_DATA,
            'PAPER_TRADING': self.ENABLE_PAPER_TRADING,
            'WEB_DASHBOARD': self.ENABLE_WEB_DASHBOARD,
            'TELEGRAM_BOT': self.ENABLE_TELEGRAM_BOT,
            'TECHNICAL_ANALYSIS': self.ENABLE_TECHNICAL_ANALYSIS,
            'BACKTESTING': self.ENABLE_BACKTESTING,
            'AI_SIGNALS': self.ENABLE_AI_SIGNALS
        }
    
    def get_active_symbols(self) -> List[str]:
        """Get the active trading symbols based on current configuration"""
        return self.ACTIVE_WATCHLIST
    
    def get_all_symbols(self) -> List[str]:
        """Get all available symbols"""
        return list(set(
            self.NIFTY_50_SYMBOLS + 
            self.FNO_SYMBOLS + 
            self.ACTIVE_WATCHLIST + 
            self.INTERNATIONAL_SYMBOLS
        ))
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours"""
        from datetime import datetime
        import pytz
        
        try:
            tz = pytz.timezone(self.TIMEZONE)
            now = datetime.now(tz)
            current_time = now.time()
            
            start_time = datetime.strptime(self.MARKET_START_TIME, "%H:%M").time()
            end_time = datetime.strptime(self.MARKET_END_TIME, "%H:%M").time()
            
            return start_time <= current_time <= end_time
        except:
            return True  # Default to allowing trading if timezone check fails
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            key: getattr(self, key) 
            for key in dir(self) 
            if not key.startswith('_') and not callable(getattr(self, key))
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default"""
        try:
            # First check if it's an environment variable
            env_value = os.getenv(key)
            if env_value is not None:
                return env_value
            
            # Then check if it's a config attribute
            return getattr(self, key, default)
        except Exception:
            return default
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check required API keys
        if self.ENABLE_TELEGRAM_BOT and not self.TELEGRAM_BOT_TOKEN:
            issues.append("Telegram bot enabled but TELEGRAM_BOT_TOKEN not provided")
        
        # Check trading parameters
        if self.INITIAL_VIRTUAL_BALANCE <= 0:
            issues.append("Initial virtual balance must be positive")
        
        if not (0 < self.MAX_POSITION_SIZE <= 1):
            issues.append("Max position size must be between 0 and 1")
        
        # Check watchlist
        if not self.ACTIVE_WATCHLIST:
            issues.append("Active watchlist cannot be empty")
        
        return issues

# Create global configuration instance
config = UnifiedConfig()

# Validate configuration on import
config_issues = config.validate_config()
if config_issues:
    print("⚠️ Configuration Issues:")
    for issue in config_issues:
        print(f"  - {issue}")

if __name__ == "__main__":
    print("🎯 UNIFIED AI TRADING PLATFORM - Configuration")
    print("=" * 60)
    print(f"Platform: {config.PLATFORM_NAME} v{config.VERSION}")
    print(f"Web Server: http://{config.WEB_HOST}:{config.WEB_PORT}")
    print(f"Database: {config.DATABASE_URL}")
    print(f"Active Symbols: {len(config.get_active_symbols())}")
    print(f"Market Hours: {config.MARKET_START_TIME} - {config.MARKET_END_TIME}")
    print(f"Virtual Balance: Rs.{config.INITIAL_VIRTUAL_BALANCE:,.2f}")
    
    print("\n🔧 Feature Status:")
    features = {
        "AI Signals": config.ENABLE_AI_SIGNALS,
        "Live Data": config.ENABLE_LIVE_DATA,
        "Paper Trading": config.ENABLE_PAPER_TRADING,
        "Web Dashboard": config.ENABLE_WEB_DASHBOARD,
        "Telegram Bot": config.ENABLE_TELEGRAM_BOT,
        "Technical Analysis": config.ENABLE_TECHNICAL_ANALYSIS
    }
    
    for feature, enabled in features.items():
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"  {feature}: {status}")
    
    print("\n📊 Active Watchlist:")
    for i, symbol in enumerate(config.get_active_symbols()[:10], 1):
        print(f"  {i:2d}. {symbol}")
    
    if len(config.get_active_symbols()) > 10:
        print(f"  ... and {len(config.get_active_symbols()) - 10} more")
    
    print("=" * 60)
