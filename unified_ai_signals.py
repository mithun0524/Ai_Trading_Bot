#!/usr/bin/env python3
"""
🤖 UNIFIED AI SIGNAL GENERATOR
Advanced AI-powered trading signal generation with multiple strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import asyncio
import json
from dataclasses import dataclass

# Try to import talib, but make it optional
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("⚠️  TA-Lib not available - using fallback technical indicators")

import warnings
warnings.filterwarnings('ignore')

from unified_config import config
from unified_database import db, UnifiedDatabaseManager, SignalRecord
from unified_live_data import live_data_manager, LiveQuote

# Setup logging
logger = logging.getLogger(__name__)

# Fallback technical indicators when TA-Lib is not available
def fallback_rsi(close_prices, period=14):
    """Calculate RSI without TA-Lib"""
    if len(close_prices) < period + 1:
        return np.array([np.nan] * len(close_prices))
    
    deltas = np.diff(close_prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gains = np.zeros_like(close_prices, dtype=float)
    avg_losses = np.zeros_like(close_prices, dtype=float)
    
    # First calculation
    avg_gains[period] = np.mean(gains[:period])
    avg_losses[period] = np.mean(losses[:period])
    
    # Subsequent calculations using smoothing
    for i in range(period + 1, len(close_prices)):
        avg_gains[i] = (avg_gains[i-1] * (period - 1) + gains[i-1]) / period
        avg_losses[i] = (avg_losses[i-1] * (period - 1) + losses[i-1]) / period
    
    rs = avg_gains / (avg_losses + 1e-10)  # Avoid division by zero
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def fallback_macd(close_prices, fast=12, slow=26, signal=9):
    """Calculate MACD without TA-Lib"""
    if len(close_prices) < slow:
        return np.array([np.nan] * len(close_prices)), np.array([np.nan] * len(close_prices)), np.array([np.nan] * len(close_prices))
    
    # Calculate EMAs
    ema_fast = pd.Series(close_prices).ewm(span=fast).mean().values
    ema_slow = pd.Series(close_prices).ewm(span=slow).mean().values
    
    # MACD line
    macd_line = ema_fast - ema_slow
    
    # Signal line
    signal_line = pd.Series(macd_line).ewm(span=signal).mean().values
    
    # Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def fallback_bollinger_bands(close_prices, period=20, std_dev=2):
    """Calculate Bollinger Bands without TA-Lib"""
    if len(close_prices) < period:
        return np.array([np.nan] * len(close_prices)), np.array([np.nan] * len(close_prices)), np.array([np.nan] * len(close_prices))
    
    rolling_mean = pd.Series(close_prices).rolling(window=period).mean().values
    rolling_std = pd.Series(close_prices).rolling(window=period).std().values
    
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    
    return upper_band, rolling_mean, lower_band

def fallback_sma(close_prices, period):
    """Calculate Simple Moving Average without TA-Lib"""
    if len(close_prices) < period:
        return np.array([np.nan] * len(close_prices))
    return pd.Series(close_prices).rolling(window=period).mean().values

def fallback_ema(close_prices, period):
    """Calculate Exponential Moving Average without TA-Lib"""
    return pd.Series(close_prices).ewm(span=period).mean().values

def fallback_adx(high, low, close, period=14):
    """Calculate ADX without TA-Lib (simplified version)"""
    if len(close) < period + 1:
        return np.array([np.nan] * len(close))
    
    # Simplified ADX calculation - returns trend strength approximation
    price_range = high - low
    avg_range = pd.Series(price_range).rolling(window=period).mean().values
    price_change = np.abs(np.diff(close, prepend=close[0]))
    avg_change = pd.Series(price_change).rolling(window=period).mean().values
    
    # Simple trend strength indicator (0-100)
    trend_strength = np.minimum(100, (avg_change / (avg_range + 1e-10)) * 50)
    
    return trend_strength

def fallback_stochastic(high, low, close, k_period=14, d_period=3):
    """Calculate Stochastic without TA-Lib"""
    if len(close) < k_period:
        return np.array([np.nan] * len(close)), np.array([np.nan] * len(close))
    
    lowest_low = pd.Series(low).rolling(window=k_period).min().values
    highest_high = pd.Series(high).rolling(window=k_period).max().values
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
    d_percent = pd.Series(k_percent).rolling(window=d_period).mean().values
    
    return k_percent, d_percent

def fallback_williams_r(high, low, close, period=14):
    """Calculate Williams %R without TA-Lib"""
    if len(close) < period:
        return np.array([np.nan] * len(close))
    
    highest_high = pd.Series(high).rolling(window=period).max().values
    lowest_low = pd.Series(low).rolling(window=period).min().values
    
    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low + 1e-10))
    
    return williams_r

def fallback_cci(high, low, close, period=20):
    """Calculate CCI without TA-Lib"""
    if len(close) < period:
        return np.array([np.nan] * len(close))
    
    typical_price = (high + low + close) / 3
    sma_tp = pd.Series(typical_price).rolling(window=period).mean().values
    mad = pd.Series(typical_price).rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x)))).values
    
    cci = (typical_price - sma_tp) / (0.015 * mad + 1e-10)
    
    return cci

def fallback_momentum(close_prices, period=10):
    """Calculate Momentum without TA-Lib"""
    if len(close_prices) < period:
        return np.array([np.nan] * len(close_prices))
    
    momentum = np.zeros_like(close_prices, dtype=float)
    momentum[:period] = np.nan
    momentum[period:] = close_prices[period:] - close_prices[:-period]
    
    return momentum

@dataclass
class TechnicalIndicators:
    """Technical indicators for a symbol"""
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    volume_sma: float
    adx: float
    stoch_k: float
    stoch_d: float
    williams_r: float
    cci: float
    momentum: float

@dataclass
class AISignal:
    """AI-generated trading signal"""
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: List[str]
    technical_data: Dict[str, Any]
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    expected_duration: Optional[str] = None  # short, medium, long
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class TechnicalAnalyzer:
    """Advanced technical analysis engine"""
    
    def __init__(self):
        self.indicators_cache = {}
        logger.info("Technical analyzer initialized")
    
    def calculate_indicators(self, data: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """Calculate all technical indicators"""
        try:
            if data.empty or len(data) < 50:
                return None
            
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values
            volume = data['Volume'].values
            
            if TALIB_AVAILABLE:
                # Use TA-Lib functions
                rsi = talib.RSI(close, timeperiod=config.RSI_PERIOD)[-1]
                
                macd, macd_signal, macd_hist = talib.MACD(close, 
                                                         fastperiod=config.MACD_FAST,
                                                         slowperiod=config.MACD_SLOW,
                                                         signalperiod=config.MACD_SIGNAL)
                
                bb_upper, bb_middle, bb_lower = talib.BBANDS(close, 
                                                            timeperiod=config.BB_PERIOD,
                                                            nbdevup=config.BB_STD,
                                                            nbdevdn=config.BB_STD)
                
                sma_20 = talib.SMA(close, timeperiod=config.SMA_SHORT)[-1]
                sma_50 = talib.SMA(close, timeperiod=config.SMA_LONG)[-1]
                ema_12 = talib.EMA(close, timeperiod=config.EMA_SHORT)[-1]
                ema_26 = talib.EMA(close, timeperiod=config.EMA_LONG)[-1]
                
                volume_sma = talib.SMA(volume.astype(float), timeperiod=20)[-1]
                adx = talib.ADX(high, low, close, timeperiod=14)[-1]
                
                stoch_k, stoch_d = talib.STOCH(high, low, close)
                williams_r = talib.WILLR(high, low, close)[-1]
                cci = talib.CCI(high, low, close)[-1]
                momentum = talib.MOM(close, timeperiod=10)[-1]
                
            else:
                # Use fallback functions
                rsi_array = fallback_rsi(close, config.RSI_PERIOD)
                rsi = rsi_array[-1] if not np.isnan(rsi_array[-1]) else 50
                
                macd, macd_signal, macd_hist = fallback_macd(close, 
                                                            config.MACD_FAST,
                                                            config.MACD_SLOW,
                                                            config.MACD_SIGNAL)
                
                bb_upper, bb_middle, bb_lower = fallback_bollinger_bands(close, 
                                                                        config.BB_PERIOD,
                                                                        config.BB_STD)
                
                sma_20_array = fallback_sma(close, config.SMA_SHORT)
                sma_20 = sma_20_array[-1] if not np.isnan(sma_20_array[-1]) else close[-1]
                
                sma_50_array = fallback_sma(close, config.SMA_LONG)
                sma_50 = sma_50_array[-1] if not np.isnan(sma_50_array[-1]) else close[-1]
                
                ema_12_array = fallback_ema(close, config.EMA_SHORT)
                ema_12 = ema_12_array[-1] if not np.isnan(ema_12_array[-1]) else close[-1]
                
                ema_26_array = fallback_ema(close, config.EMA_LONG)
                ema_26 = ema_26_array[-1] if not np.isnan(ema_26_array[-1]) else close[-1]
                
                volume_sma_array = fallback_sma(volume.astype(float), 20)
                volume_sma = volume_sma_array[-1] if not np.isnan(volume_sma_array[-1]) else volume[-1]
                
                adx_array = fallback_adx(high, low, close, 14)
                adx = adx_array[-1] if not np.isnan(adx_array[-1]) else 25
                
                stoch_k, stoch_d = fallback_stochastic(high, low, close)
                williams_r_array = fallback_williams_r(high, low, close)
                williams_r = williams_r_array[-1] if not np.isnan(williams_r_array[-1]) else -50
                
                cci_array = fallback_cci(high, low, close)
                cci = cci_array[-1] if not np.isnan(cci_array[-1]) else 0
                
                momentum_array = fallback_momentum(close, 10)
                momentum = momentum_array[-1] if not np.isnan(momentum_array[-1]) else 0
            
            return TechnicalIndicators(
                rsi=float(rsi),
                macd=float(macd[-1]),
                macd_signal=float(macd_signal[-1]),
                macd_histogram=float(macd_hist[-1]),
                bb_upper=float(bb_upper[-1]),
                bb_middle=float(bb_middle[-1]),
                bb_lower=float(bb_lower[-1]),
                sma_20=float(sma_20),
                sma_50=float(sma_50),
                ema_12=float(ema_12),
                ema_26=float(ema_26),
                volume_sma=float(volume_sma),
                adx=float(adx),
                stoch_k=float(stoch_k[-1]),
                stoch_d=float(stoch_d[-1]),
                williams_r=float(williams_r),
                cci=float(cci),
                momentum=float(momentum)
            )
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return None

class AISignalGenerator:
    """Advanced AI signal generator with multiple strategies"""
    
    def __init__(self, database: UnifiedDatabaseManager = None):
        self.db = database or db
        self.technical_analyzer = TechnicalAnalyzer()
        self.signal_cache = {}
        self.last_signals = {}
        
        # Strategy weights
        self.strategy_weights = {
            'trend_following': 0.25,
            'mean_reversion': 0.20,
            'momentum': 0.25,
            'breakout': 0.15,
            'volume_analysis': 0.15
        }
        
        logger.info("AI signal generator initialized with 5 strategies")
    
    def _trend_following_strategy(self, indicators: TechnicalIndicators, 
                                 current_price: float) -> Tuple[str, float, List[str]]:
        """Trend following strategy"""
        signals = []
        reasons = []
        
        # Moving average signals
        if indicators.sma_20 > indicators.sma_50:
            if current_price > indicators.sma_20:
                signals.append('BUY')
                reasons.append(f"Price above upward trending SMA20 ({indicators.sma_20:.2f})")
        else:
            if current_price < indicators.sma_20:
                signals.append('SELL')
                reasons.append(f"Price below downward trending SMA20 ({indicators.sma_20:.2f})")
        
        # EMA crossover
        if indicators.ema_12 > indicators.ema_26:
            signals.append('BUY')
            reasons.append("EMA12 above EMA26 (bullish trend)")
        else:
            signals.append('SELL')
            reasons.append("EMA12 below EMA26 (bearish trend)")
        
        # ADX trend strength
        if indicators.adx > 25:
            if len(signals) > 0:
                reasons.append(f"Strong trend confirmed by ADX ({indicators.adx:.1f})")
        
        # Determine signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            confidence = min(80, 40 + (buy_count * 15))
            return 'BUY', confidence, reasons
        elif sell_count > buy_count:
            confidence = min(80, 40 + (sell_count * 15))
            return 'SELL', confidence, reasons
        else:
            return 'HOLD', 30, ['Trend signals mixed']
    
    def _mean_reversion_strategy(self, indicators: TechnicalIndicators,
                                current_price: float) -> Tuple[str, float, List[str]]:
        """Mean reversion strategy"""
        signals = []
        reasons = []
        
        # RSI oversold/overbought
        if indicators.rsi < config.RSI_OVERSOLD:
            signals.append('BUY')
            reasons.append(f"RSI oversold ({indicators.rsi:.1f} < {config.RSI_OVERSOLD})")
        elif indicators.rsi > config.RSI_OVERBOUGHT:
            signals.append('SELL')
            reasons.append(f"RSI overbought ({indicators.rsi:.1f} > {config.RSI_OVERBOUGHT})")
        
        # Bollinger Bands
        if current_price <= indicators.bb_lower:
            signals.append('BUY')
            reasons.append(f"Price at lower Bollinger Band ({indicators.bb_lower:.2f})")
        elif current_price >= indicators.bb_upper:
            signals.append('SELL')
            reasons.append(f"Price at upper Bollinger Band ({indicators.bb_upper:.2f})")
        
        # Williams %R
        if indicators.williams_r < -80:
            signals.append('BUY')
            reasons.append(f"Williams %R oversold ({indicators.williams_r:.1f})")
        elif indicators.williams_r > -20:
            signals.append('SELL')
            reasons.append(f"Williams %R overbought ({indicators.williams_r:.1f})")
        
        # CCI
        if indicators.cci < -100:
            signals.append('BUY')
            reasons.append(f"CCI oversold ({indicators.cci:.1f})")
        elif indicators.cci > 100:
            signals.append('SELL')
            reasons.append(f"CCI overbought ({indicators.cci:.1f})")
        
        # Determine signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count >= 2:
            confidence = min(85, 50 + (buy_count * 10))
            return 'BUY', confidence, reasons
        elif sell_count >= 2:
            confidence = min(85, 50 + (sell_count * 10))
            return 'SELL', confidence, reasons
        else:
            return 'HOLD', 25, ['Mean reversion signals inconclusive']
    
    def _momentum_strategy(self, indicators: TechnicalIndicators,
                          quote: LiveQuote) -> Tuple[str, float, List[str]]:
        """Momentum-based strategy"""
        signals = []
        reasons = []
        
        # MACD
        if indicators.macd > indicators.macd_signal and indicators.macd_histogram > 0:
            signals.append('BUY')
            reasons.append("MACD bullish (above signal line with positive histogram)")
        elif indicators.macd < indicators.macd_signal and indicators.macd_histogram < 0:
            signals.append('SELL')
            reasons.append("MACD bearish (below signal line with negative histogram)")
        
        # Stochastic
        if indicators.stoch_k > indicators.stoch_d and indicators.stoch_k < 80:
            signals.append('BUY')
            reasons.append(f"Stochastic bullish crossover (K={indicators.stoch_k:.1f})")
        elif indicators.stoch_k < indicators.stoch_d and indicators.stoch_k > 20:
            signals.append('SELL')
            reasons.append(f"Stochastic bearish crossover (K={indicators.stoch_k:.1f})")
        
        # Price momentum
        if indicators.momentum > 0:
            signals.append('BUY')
            reasons.append(f"Positive price momentum ({indicators.momentum:.2f})")
        elif indicators.momentum < 0:
            signals.append('SELL')
            reasons.append(f"Negative price momentum ({indicators.momentum:.2f})")
        
        # Intraday momentum
        if quote.change_percent > 2:
            signals.append('BUY')
            reasons.append(f"Strong intraday momentum (+{quote.change_percent:.1f}%)")
        elif quote.change_percent < -2:
            signals.append('SELL')
            reasons.append(f"Strong intraday decline ({quote.change_percent:.1f}%)")
        
        # Determine signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            confidence = min(85, 45 + (buy_count * 12))
            return 'BUY', confidence, reasons
        elif sell_count > buy_count:
            confidence = min(85, 45 + (sell_count * 12))
            return 'SELL', confidence, reasons
        else:
            return 'HOLD', 35, ['Momentum signals neutral']
    
    def _breakout_strategy(self, indicators: TechnicalIndicators,
                          current_price: float, data: pd.DataFrame) -> Tuple[str, float, List[str]]:
        """Breakout detection strategy"""
        signals = []
        reasons = []
        
        try:
            # 20-day high/low breakouts
            high_20 = data['High'].tail(20).max()
            low_20 = data['Low'].tail(20).min()
            
            if current_price > high_20 * 1.001:  # 0.1% above 20-day high
                signals.append('BUY')
                reasons.append(f"Breakout above 20-day high ({high_20:.2f})")
            elif current_price < low_20 * 0.999:  # 0.1% below 20-day low
                signals.append('SELL')
                reasons.append(f"Breakdown below 20-day low ({low_20:.2f})")
            
            # Bollinger Band breakouts
            bb_width = (indicators.bb_upper - indicators.bb_lower) / indicators.bb_middle
            if bb_width < 0.02:  # Narrow bands indicate potential breakout
                if current_price > indicators.bb_upper:
                    signals.append('BUY')
                    reasons.append("Bullish breakout from tight Bollinger Bands")
                elif current_price < indicators.bb_lower:
                    signals.append('SELL')
                    reasons.append("Bearish breakdown from tight Bollinger Bands")
            
            # Volume confirmation
            recent_volume = data['Volume'].tail(5).mean()
            if recent_volume > indicators.volume_sma * 1.5:
                if len(signals) > 0:
                    reasons.append("High volume confirms breakout")
            
        except Exception as e:
            logger.error(f"Error in breakout strategy: {e}")
        
        # Determine signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > 0:
            confidence = min(90, 60 + (buy_count * 15))
            return 'BUY', confidence, reasons
        elif sell_count > 0:
            confidence = min(90, 60 + (sell_count * 15))
            return 'SELL', confidence, reasons
        else:
            return 'HOLD', 20, ['No breakout detected']
    
    def _volume_analysis_strategy(self, quote: LiveQuote, data: pd.DataFrame,
                                 indicators: TechnicalIndicators) -> Tuple[str, float, List[str]]:
        """Volume-based analysis strategy"""
        signals = []
        reasons = []
        
        try:
            # Volume trend analysis
            if quote.volume > indicators.volume_sma * 2:
                if quote.change_percent > 0:
                    signals.append('BUY')
                    reasons.append(f"High volume bullish ({quote.volume:,} vs avg {indicators.volume_sma:,.0f})")
                else:
                    signals.append('SELL')
                    reasons.append(f"High volume bearish ({quote.volume:,} vs avg {indicators.volume_sma:,.0f})")
            
            # On-Balance Volume (OBV) simulation
            obv_data = []
            obv = 0
            for i, row in data.tail(20).iterrows():
                if row['Close'] > row['Open']:
                    obv += row['Volume']
                elif row['Close'] < row['Open']:
                    obv -= row['Volume']
                obv_data.append(obv)
            
            if len(obv_data) >= 2:
                obv_trend = obv_data[-1] - obv_data[-5] if len(obv_data) >= 5 else obv_data[-1] - obv_data[-2]
                if obv_trend > 0 and quote.change_percent > 0:
                    signals.append('BUY')
                    reasons.append("Positive volume accumulation trend")
                elif obv_trend < 0 and quote.change_percent < 0:
                    signals.append('SELL')
                    reasons.append("Negative volume distribution trend")
            
            # Price-volume divergence
            price_change = quote.change_percent
            volume_ratio = quote.volume / indicators.volume_sma
            
            if price_change > 1 and volume_ratio < 0.8:
                reasons.append("Caution: Price rise on low volume")
            elif price_change < -1 and volume_ratio < 0.8:
                reasons.append("Caution: Price fall on low volume")
            
        except Exception as e:
            logger.error(f"Error in volume analysis: {e}")
        
        # Determine signal
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > 0:
            confidence = min(75, 50 + (buy_count * 12))
            return 'BUY', confidence, reasons
        elif sell_count > 0:
            confidence = min(75, 50 + (sell_count * 12))
            return 'SELL', confidence, reasons
        else:
            return 'HOLD', 30, ['Volume analysis neutral']
    
    def generate_signal(self, symbol: str, quote: LiveQuote, 
                       historical_data: pd.DataFrame) -> AISignal:
        """Generate comprehensive AI signal"""
        try:
            # Calculate technical indicators
            indicators = self.technical_analyzer.calculate_indicators(historical_data)
            if not indicators:
                return AISignal(
                    symbol=symbol,
                    signal_type='HOLD',
                    confidence=0,
                    reasoning=['Insufficient data for analysis'],
                    technical_data={}
                )
            
            # Run all strategies
            strategy_results = {}
            all_reasons = []
            
            # 1. Trend Following
            trend_signal, trend_conf, trend_reasons = self._trend_following_strategy(
                indicators, quote.price)
            strategy_results['trend_following'] = (trend_signal, trend_conf)
            all_reasons.extend([f"Trend: {r}" for r in trend_reasons])
            
            # 2. Mean Reversion
            mr_signal, mr_conf, mr_reasons = self._mean_reversion_strategy(
                indicators, quote.price)
            strategy_results['mean_reversion'] = (mr_signal, mr_conf)
            all_reasons.extend([f"Mean Rev: {r}" for r in mr_reasons])
            
            # 3. Momentum
            mom_signal, mom_conf, mom_reasons = self._momentum_strategy(
                indicators, quote)
            strategy_results['momentum'] = (mom_signal, mom_conf)
            all_reasons.extend([f"Momentum: {r}" for r in mom_reasons])
            
            # 4. Breakout
            bo_signal, bo_conf, bo_reasons = self._breakout_strategy(
                indicators, quote.price, historical_data)
            strategy_results['breakout'] = (bo_signal, bo_conf)
            all_reasons.extend([f"Breakout: {r}" for r in bo_reasons])
            
            # 5. Volume Analysis
            vol_signal, vol_conf, vol_reasons = self._volume_analysis_strategy(
                quote, historical_data, indicators)
            strategy_results['volume_analysis'] = (vol_signal, vol_conf)
            all_reasons.extend([f"Volume: {r}" for r in vol_reasons])
            
            # Combine signals using weighted approach
            weighted_score = 0
            total_weight = 0
            
            for strategy, (signal, confidence) in strategy_results.items():
                weight = self.strategy_weights[strategy]
                if signal == 'BUY':
                    weighted_score += confidence * weight
                elif signal == 'SELL':
                    weighted_score -= confidence * weight
                # HOLD contributes 0
                total_weight += weight
            
            # Normalize score
            final_score = weighted_score / total_weight if total_weight > 0 else 0
            
            # Determine final signal
            if final_score > 20:
                final_signal = 'BUY'
                final_confidence = min(95, abs(final_score))
            elif final_score < -20:
                final_signal = 'SELL'
                final_confidence = min(95, abs(final_score))
            else:
                final_signal = 'HOLD'
                final_confidence = 50 - abs(final_score)
            
            # Calculate price targets and stop loss
            price_target = None
            stop_loss = None
            risk_reward_ratio = None
            
            if final_signal == 'BUY':
                price_target = quote.price * 1.03  # 3% target
                stop_loss = quote.price * 0.98     # 2% stop loss
                risk_reward_ratio = 1.5
            elif final_signal == 'SELL':
                price_target = quote.price * 0.97  # 3% target
                stop_loss = quote.price * 1.02     # 2% stop loss
                risk_reward_ratio = 1.5
            
            # Prepare technical data
            technical_data = {
                'current_price': quote.price,
                'rsi': indicators.rsi,
                'macd': indicators.macd,
                'macd_signal': indicators.macd_signal,
                'bb_position': (quote.price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower),
                'sma_20': indicators.sma_20,
                'sma_50': indicators.sma_50,
                'volume_ratio': quote.volume / indicators.volume_sma if indicators.volume_sma > 0 else 1,
                'adx': indicators.adx,
                'strategy_scores': {k: v[1] for k, v in strategy_results.items()},
                'weighted_score': final_score
            }
            
            signal = AISignal(
                symbol=symbol,
                signal_type=final_signal,
                confidence=final_confidence,
                reasoning=all_reasons[:10],  # Limit to top 10 reasons
                technical_data=technical_data,
                price_target=price_target,
                stop_loss=stop_loss,
                risk_reward_ratio=risk_reward_ratio,
                expected_duration='medium'  # Default to medium term
            )
            
            # Cache signal
            self.signal_cache[symbol] = signal
            self.last_signals[symbol] = datetime.now()
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return AISignal(
                symbol=symbol,
                signal_type='HOLD',
                confidence=0,
                reasoning=[f'Signal generation error: {str(e)}'],
                technical_data={}
            )
    
    async def generate_signals_for_watchlist(self) -> List[AISignal]:
        """Generate signals for all watchlist symbols"""
        signals = []
        
        try:
            watchlist = config.get_active_symbols()
            logger.info(f"Generating signals for {len(watchlist)} symbols")
            
            for symbol in watchlist:
                try:
                    # Get live quote
                    quote = await live_data_manager.get_live_quote(symbol)
                    if not quote:
                        logger.warning(f"No live quote available for {symbol}")
                        continue
                    
                    # Get historical data
                    historical_data = live_data_manager.get_historical_data(symbol, period="6mo")
                    if historical_data.empty:
                        logger.warning(f"No historical data available for {symbol}")
                        continue
                    
                    # Generate signal
                    signal = self.generate_signal(symbol, quote, historical_data)
                    signals.append(signal)
                    
                    # Store in database
                    signal_record = SignalRecord(
                        symbol=signal.symbol,
                        signal_type=signal.signal_type,
                        confidence=signal.confidence,
                        reasoning=signal.reasoning,
                        technical_data=signal.technical_data,
                        timestamp=signal.timestamp
                    )
                    
                    self.db.store_signal(signal_record)
                    
                    logger.debug(f"Generated {signal.signal_type} signal for {symbol} "
                               f"with {signal.confidence:.1f}% confidence")
                    
                except Exception as e:
                    logger.error(f"Error generating signal for {symbol}: {e}")
                    continue
            
            logger.info(f"Generated {len(signals)} signals successfully")
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals for watchlist: {e}")
            return []
    
    def get_cached_signal(self, symbol: str) -> Optional[AISignal]:
        """Get cached signal for symbol"""
        if symbol in self.signal_cache:
            # Check if signal is not too old (max 5 minutes)
            if symbol in self.last_signals:
                age = datetime.now() - self.last_signals[symbol]
                if age.seconds < 300:  # 5 minutes
                    return self.signal_cache[symbol]
        return None

# Create global AI signal generator instance
ai_signal_generator = AISignalGenerator()

if __name__ == "__main__":
    print("🤖 UNIFIED AI SIGNAL GENERATOR")
    print("=" * 50)
    
    async def test_signal_generator():
        print("Testing AI signal generator...")
        
        # Test single signal generation
        print("Generating signal for RELIANCE...")
        quote = await live_data_manager.get_live_quote('RELIANCE')
        if quote:
            historical_data = live_data_manager.get_historical_data('RELIANCE')
            signal = ai_signal_generator.generate_signal('RELIANCE', quote, historical_data)
            
            print(f"✅ Signal: {signal.signal_type} with {signal.confidence:.1f}% confidence")
            print(f"   Reasons: {signal.reasoning[:3]}")
            print(f"   Price Target: {signal.price_target}")
            print(f"   Stop Loss: {signal.stop_loss}")
        
        # Test watchlist signals
        print("\nGenerating signals for watchlist...")
        signals = await ai_signal_generator.generate_signals_for_watchlist()
        
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        hold_signals = [s for s in signals if s.signal_type == 'HOLD']
        
        print(f"✅ Generated {len(signals)} signals:")
        print(f"   🟢 BUY: {len(buy_signals)}")
        print(f"   🔴 SELL: {len(sell_signals)}")
        print(f"   🟡 HOLD: {len(hold_signals)}")
        
        # Show top signals
        top_signals = sorted(signals, key=lambda x: x.confidence, reverse=True)[:5]
        print(f"\nTop 5 signals by confidence:")
        for i, signal in enumerate(top_signals, 1):
            print(f"   {i}. {signal.symbol}: {signal.signal_type} ({signal.confidence:.1f}%)")
    
    # Run test
    asyncio.run(test_signal_generator())
    print("✅ AI signal generator ready!")
    print("=" * 50)
