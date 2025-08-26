#!/usr/bin/env python3
"""
📊 UNIFIED LIVE DATA MANAGER
Real-time market data aggregation from multiple sources
"""

import asyncio
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import logging
import threading
import time
from dataclasses import dataclass
import requests
from concurrent.futures import ThreadPoolExecutor
import json

from unified_config import config
from unified_database import db, UnifiedDatabaseManager

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class LiveQuote:
    """Live market quote data structure"""
    symbol: str
    price: float
    open_price: float
    high: float
    low: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime
    source: str = 'YAHOO'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'open': self.open_price,
            'high': self.high,
            'low': self.low,
            'volume': self.volume,
            'change': self.change,
            'change_percent': self.change_percent,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

class DataSource:
    """Base class for data sources"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_active = True
        self.error_count = 0
        self.max_errors = 5
    
    async def get_quote(self, symbol: str) -> Optional[LiveQuote]:
        """Get live quote for symbol"""
        raise NotImplementedError
    
    async def get_multiple_quotes(self, symbols: List[str]) -> List[LiveQuote]:
        """Get quotes for multiple symbols"""
        quotes = []
        for symbol in symbols:
            try:
                quote = await self.get_quote(symbol)
                if quote:
                    quotes.append(quote)
            except Exception as e:
                logger.error(f"{self.name}: Error getting quote for {symbol}: {e}")
        return quotes
    
    def handle_error(self, error: Exception):
        """Handle data source errors"""
        self.error_count += 1
        logger.error(f"{self.name}: Error {self.error_count}/{self.max_errors}: {error}")
        
        if self.error_count >= self.max_errors:
            self.is_active = False
            logger.warning(f"{self.name}: Deactivated due to repeated errors")

class YahooFinanceSource(DataSource):
    """Yahoo Finance data source"""
    
    def __init__(self):
        super().__init__("Yahoo Finance")
        self.session = requests.Session()
    
    async def get_quote(self, symbol: str) -> Optional[LiveQuote]:
        """Get live quote from Yahoo Finance"""
        try:
            # Try Indian stock first (.NS suffix)
            if not symbol.endswith('.NS') and symbol not in config.INTERNATIONAL_SYMBOLS:
                symbol_ns = f"{symbol}.NS"
            else:
                symbol_ns = symbol
            
            # Let yfinance handle the session
            ticker = yf.Ticker(symbol_ns)
            
            # Get intraday data
            data = ticker.history(period="1d", interval="1m")
            
            if data.empty and symbol_ns.endswith('.NS'):
                # Try without .NS suffix
                ticker = yf.Ticker(symbol.replace('.NS', ''))
                data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                latest = data.iloc[-1]
                open_price = data.iloc[0]['Open']
                
                quote = LiveQuote(
                    symbol=symbol,
                    price=float(latest['Close']),
                    open_price=float(open_price),
                    high=float(data['High'].max()),
                    low=float(data['Low'].min()),
                    volume=int(latest['Volume']),
                    change=float(latest['Close'] - open_price),
                    change_percent=float((latest['Close'] - open_price) / open_price * 100),
                    timestamp=datetime.now(),
                    source=self.name
                )
                
                self.error_count = 0  # Reset error count on success
                return quote
            
            return None
            
        except Exception as e:
            self.handle_error(e)
            return None


class UnifiedLiveDataManager:
    """Unified manager for live market data from multiple sources"""
    
    def __init__(self, database: UnifiedDatabaseManager = None):
        self.db = database or db
        self.data_sources = []
        self.subscribers = []
        self.running = False
        self.watchlist = config.get_active_symbols()
        self.update_interval = config.LIVE_DATA_UPDATE_INTERVAL
        self.quote_cache = {}
        self.last_update = {}
        
        self._setup_data_sources()
        self._executor = ThreadPoolExecutor(max_workers=5)
        
        logger.info(f"Live data manager initialized with {len(self.watchlist)} symbols")
    
    def _setup_data_sources(self):
        """Setup available data sources"""
        # Primary and only: Yahoo Finance
        self.data_sources = [YahooFinanceSource()]
        logger.info("Configured 1 data source: Yahoo Finance")
    
    def add_subscriber(self, callback: Callable[[str, LiveQuote], None]):
        """Add callback for live data updates"""
        self.subscribers.append(callback)
        logger.info(f"Added data subscriber: {callback.__name__}")
    
    def remove_subscriber(self, callback: Callable):
        """Remove data update callback"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
            logger.info(f"Removed data subscriber: {callback.__name__}")
    
    def notify_subscribers(self, symbol: str, quote: LiveQuote):
        """Notify all subscribers of data update"""
        for callback in self.subscribers:
            try:
                callback(symbol, quote)
            except Exception as e:
                logger.error(f"Error notifying subscriber {callback.__name__}: {e}")
    
    async def get_live_quote(self, symbol: str) -> Optional[LiveQuote]:
        """Get live quote using best available data source"""
        for source in self.data_sources:
            if not source.is_active:
                continue
            
            try:
                quote = await source.get_quote(symbol)
                if quote:
                    # Cache the quote
                    self.quote_cache[symbol] = quote
                    self.last_update[symbol] = datetime.now()
                    
                    # Store in database
                    self.db.store_live_quote(symbol, quote.to_dict())
                    
                    return quote
            except Exception as e:
                logger.error(f"Error getting quote for {symbol} from {source.name}: {e}")
                continue
        
        # Return cached quote if available
        if symbol in self.quote_cache:
            cached_quote = self.quote_cache[symbol]
            # Check if cache is not too old (max 60 seconds)
            if (datetime.now() - self.last_update.get(symbol, datetime.min)).seconds < 60:
                return cached_quote
        
        return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, LiveQuote]:
        """Get quotes for multiple symbols efficiently"""
        quotes = {}
        
        # Use ThreadPoolExecutor for parallel requests
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.get_live_quote(symbol))
            tasks.append((symbol, task))
        
        # Wait for all tasks to complete
        for symbol, task in tasks:
            try:
                quote = await task
                if quote:
                    quotes[symbol] = quote
            except Exception as e:
                logger.error(f"Error getting quote for {symbol}: {e}")
        
        return quotes
    
    async def update_watchlist_quotes(self):
        """Update quotes for all watchlist symbols"""
        try:
            start_time = time.time()
            quotes = await self.get_multiple_quotes(self.watchlist)
            
            # Notify subscribers
            for symbol, quote in quotes.items():
                self.notify_subscribers(symbol, quote)
            
            update_time = time.time() - start_time
            logger.debug(f"Updated {len(quotes)} quotes in {update_time:.2f} seconds")
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error updating watchlist quotes: {e}")
            return {}
    
    async def start_live_feed(self):
        """Start continuous live data feed"""
        if self.running:
            logger.warning("Live feed already running")
            return
        
        self.running = True
        logger.info("Starting live data feed...")
        
        try:
            while self.running:
                if config.is_market_hours() or True:  # Always run in demo mode
                    await self.update_watchlist_quotes()
                else:
                    logger.debug("Market closed, sleeping...")
                
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"Error in live feed: {e}")
        finally:
            self.running = False
            logger.info("Live data feed stopped")
    
    def stop_live_feed(self):
        """Stop live data feed"""
        self.running = False
        logger.info("Stopping live data feed...")
    
    def get_cached_quotes(self) -> Dict[str, LiveQuote]:
        """Get all cached quotes"""
        return self.quote_cache.copy()
    
    def get_latest_quotes(self) -> Dict[str, LiveQuote]:
        """Get latest quotes (alias for get_cached_quotes for backward compatibility)"""
        return self.get_cached_quotes()
    
    def get_data_source_status(self) -> List[Dict[str, Any]]:
        """Get status of all data sources"""
        status = []
        for source in self.data_sources:
            status.append({
                'name': source.name,
                'active': source.is_active,
                'error_count': source.error_count,
                'max_errors': source.max_errors
            })
        return status
    
    def add_symbol_to_watchlist(self, symbol: str):
        """Add symbol to watchlist"""
        if symbol not in self.watchlist:
            self.watchlist.append(symbol)
            logger.info(f"Added {symbol} to watchlist")
    
    def remove_symbol_from_watchlist(self, symbol: str):
        """Remove symbol from watchlist"""
        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
            logger.info(f"Removed {symbol} from watchlist")
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical data for technical analysis"""
        try:
            # Try with .NS suffix for Indian stocks
            if not symbol.endswith('.NS') and symbol not in config.INTERNATIONAL_SYMBOLS:
                symbol_ns = f"{symbol}.NS"
            else:
                symbol_ns = symbol
            
            ticker = yf.Ticker(symbol_ns)
            data = ticker.history(period=period)
            
            if data.empty and symbol_ns.endswith('.NS'):
                # Try without .NS suffix
                ticker = yf.Ticker(symbol.replace('.NS', ''))
                data = ticker.history(period=period)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        is_open = config.is_market_hours()
        
        status = {
            'is_open': is_open,
            'market_time': config.MARKET_START_TIME + " - " + config.MARKET_END_TIME,
            'timezone': config.TIMEZONE,
            'current_time': datetime.now().strftime("%H:%M:%S"),
            'watchlist_size': len(self.watchlist),
            'data_sources': len([s for s in self.data_sources if s.is_active]),
            'last_update': max(self.last_update.values()) if self.last_update else None
        }
        
        return status

# Create global live data manager instance
live_data_manager = UnifiedLiveDataManager()

async def start_live_data_background():
    """Start live data feed in background"""
    await live_data_manager.start_live_feed()

def start_live_data_thread():
    """Start live data feed in separate thread"""
    def run_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(live_data_manager.start_live_feed())
    
    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()
    logger.info("Live data feed started in background thread")
    return thread

if __name__ == "__main__":
    print("📊 UNIFIED LIVE DATA MANAGER")
    print("=" * 50)
    
    async def test_data_manager():
        print("Testing live data manager...")
        
        # Test single quote
        print("Getting quote for RELIANCE...")
        quote = await live_data_manager.get_live_quote('RELIANCE')
        if quote:
            print(f"✅ RELIANCE: Rs.{quote.price:.2f} ({quote.change_percent:+.2f}%)")
        else:
            print("❌ Failed to get RELIANCE quote")
        
        # Test multiple quotes
        print("\nGetting quotes for watchlist...")
        quotes = await live_data_manager.get_multiple_quotes(['RELIANCE', 'TCS', 'HDFCBANK'])
        print(f"✅ Retrieved {len(quotes)} quotes")
        
        # Test data source status
        print("\nData source status:")
        for status in live_data_manager.get_data_source_status():
            status_text = "✅ Active" if status['active'] else "❌ Inactive"
            print(f"  {status['name']}: {status_text} (Errors: {status['error_count']})")
        
        # Test market status
        market_status = live_data_manager.get_market_status()
        print(f"\nMarket Status: {'🟢 Open' if market_status['is_open'] else '🔴 Closed'}")
        print(f"Market Hours: {market_status['market_time']}")
        print(f"Watchlist: {market_status['watchlist_size']} symbols")
    
    # Run test
    asyncio.run(test_data_manager())
    print("✅ Live data manager ready!")
    print("=" * 50)
