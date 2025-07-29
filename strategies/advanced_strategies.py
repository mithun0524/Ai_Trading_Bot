#!/usr/bin/env python3
"""
🔄 Advanced Trading Strategies
Multiple trading strategies for enhanced signal generation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("TA-Lib not available, using pandas-ta as fallback")
    try:
        import pandas_ta as ta
        PANDAS_TA_AVAILABLE = True
    except ImportError:
        PANDAS_TA_AVAILABLE = False
        print("pandas-ta not available, using basic calculations")
from dataclasses import dataclass
from enum import Enum
from config import Config
from analysis.technical_analysis import TechnicalAnalysis
from utils.logger import logger

class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    PAIRS_TRADING = "pairs_trading"
    VOLUME_ANALYSIS = "volume_analysis"

@dataclass
class StrategySignal:
    symbol: str
    strategy: StrategyType
    signal_type: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    holding_period: Optional[int] = None
    metadata: Dict = None

class AdvancedStrategies:
    def __init__(self, config: Config):
        self.config = config
        self.technical_analyzer = TechnicalAnalysis(config)
    
    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI manually if TA-Lib is not available"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices, window=20, std_dev=2):
        """Calculate Bollinger Bands manually"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, sma, lower_band
        
    def analyze_all_strategies(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Run all trading strategies and return combined signals"""
        signals = []
        
        try:
            # Ensure we have enough data
            if len(df) < 50:
                logger.warning(f"Insufficient data for {symbol}: {len(df)} rows")
                return signals
            
            # Run each strategy
            strategies = [
                self.momentum_strategy,
                self.mean_reversion_strategy,
                self.breakout_strategy,
                self.scalping_strategy,
                self.swing_strategy,
                self.volume_analysis_strategy
            ]
            
            for strategy in strategies:
                try:
                    strategy_signals = strategy(df, symbol)
                    if strategy_signals:
                        signals.extend(strategy_signals)
                except Exception as e:
                    logger.error(f"Error in strategy {strategy.__name__} for {symbol}: {e}")
                    continue
            
            # Filter and rank signals
            signals = self._filter_and_rank_signals(signals)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in analyze_all_strategies for {symbol}: {e}")
            return []
    
    def momentum_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Momentum-based trading strategy"""
        signals = []
        
        try:
            # Calculate momentum indicators with fallback
            if TALIB_AVAILABLE:
                df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
                df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'].values)
                df['ema_12'] = talib.EMA(df['close'].values, timeperiod=12)
                df['ema_26'] = talib.EMA(df['close'].values, timeperiod=26)
                df['adx'] = talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            elif PANDAS_TA_AVAILABLE:
                df['rsi'] = ta.rsi(df['close'], length=14)
                macd_data = ta.macd(df['close'])
                df['macd'] = macd_data['MACD_12_26_9']
                df['macd_signal'] = macd_data['MACDs_12_26_9']
                df['macd_hist'] = macd_data['MACDh_12_26_9']
                df['ema_12'] = ta.ema(df['close'], length=12)
                df['ema_26'] = ta.ema(df['close'], length=26)
                adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
                df['adx'] = adx_data['ADX_14']
            else:
                # Basic calculations as fallback
                df['rsi'] = self._calculate_rsi(df['close'], 14)
                df['ema_12'] = df['close'].ewm(span=12).mean()
                df['ema_26'] = df['close'].ewm(span=26).mean()
                df['macd'] = df['ema_12'] - df['ema_26']
                df['macd_signal'] = df['macd'].ewm(span=9).mean()
                df['adx'] = 50  # Default value when ADX can't be calculated
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Strong momentum BUY conditions
            if (current['rsi'] > 60 and current['rsi'] < 80 and
                current['macd'] > current['macd_signal'] and
                current['ema_12'] > current['ema_26'] and
                current['adx'] > 25):
                
                confidence = min(90, (current['adx'] - 25) * 2 + 60)
                target_price = current['close'] * 1.03  # 3% target
                stop_loss = current['close'] * 0.98   # 2% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.MOMENTUM,
                    signal_type="BUY",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=5,  # 5 periods
                    metadata={
                        'rsi': current['rsi'],
                        'adx': current['adx'],
                        'macd_strength': current['macd'] - current['macd_signal']
                    }
                ))
            
            # Strong momentum SELL conditions
            elif (current['rsi'] < 40 and current['rsi'] > 20 and
                  current['macd'] < current['macd_signal'] and
                  current['ema_12'] < current['ema_26'] and
                  current['adx'] > 25):
                
                confidence = min(90, (current['adx'] - 25) * 2 + 60)
                target_price = current['close'] * 0.97  # 3% target
                stop_loss = current['close'] * 1.02   # 2% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.MOMENTUM,
                    signal_type="SELL",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=5,
                    metadata={
                        'rsi': current['rsi'],
                        'adx': current['adx'],
                        'macd_strength': current['macd_signal'] - current['macd']
                    }
                ))
            
        except Exception as e:
            logger.error(f"Error in momentum strategy for {symbol}: {e}")
        
        return signals
    
    def mean_reversion_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Mean reversion trading strategy"""
        signals = []
        
        try:
            # Calculate mean reversion indicators with fallback
            if TALIB_AVAILABLE:
                df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'].values)
                df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
                df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'].values, df['low'].values, df['close'].values)
            elif PANDAS_TA_AVAILABLE:
                bb_data = ta.bbands(df['close'])
                df['bb_upper'] = bb_data['BBU_20_2.0']
                df['bb_middle'] = bb_data['BBM_20_2.0']
                df['bb_lower'] = bb_data['BBL_20_2.0']
                df['rsi'] = ta.rsi(df['close'], length=14)
                stoch_data = ta.stoch(df['high'], df['low'], df['close'])
                df['stoch_k'] = stoch_data['STOCHk_14_3_3']
                df['stoch_d'] = stoch_data['STOCHd_14_3_3']
            else:
                # Basic calculations as fallback
                df['bb_upper'], df['bb_middle'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
                df['rsi'] = self._calculate_rsi(df['close'], 14)
                # Simple stochastic calculation
                low_min = df['low'].rolling(window=14).min()
                high_max = df['high'].rolling(window=14).max()
                df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
                df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            current = df.iloc[-1]
            
            # Oversold mean reversion BUY
            if (current['close'] <= current['bb_lower'] and
                current['rsi'] < 30 and
                current['stoch_k'] < 20):
                
                confidence = 70 + (30 - current['rsi']) + (20 - current['stoch_k']) / 2
                target_price = current['bb_middle']  # Target middle band
                stop_loss = current['close'] * 0.95  # 5% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.MEAN_REVERSION,
                    signal_type="BUY",
                    confidence=min(95, confidence),
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=3,
                    metadata={
                        'bb_position': 'lower',
                        'rsi': current['rsi'],
                        'stoch_k': current['stoch_k']
                    }
                ))
            
            # Overbought mean reversion SELL
            elif (current['close'] >= current['bb_upper'] and
                  current['rsi'] > 70 and
                  current['stoch_k'] > 80):
                
                confidence = 70 + (current['rsi'] - 70) + (current['stoch_k'] - 80) / 2
                target_price = current['bb_middle']  # Target middle band
                stop_loss = current['close'] * 1.05  # 5% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.MEAN_REVERSION,
                    signal_type="SELL",
                    confidence=min(95, confidence),
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=3,
                    metadata={
                        'bb_position': 'upper',
                        'rsi': current['rsi'],
                        'stoch_k': current['stoch_k']
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error in mean reversion strategy for {symbol}: {e}")
        
        return signals
    
    def breakout_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Breakout trading strategy"""
        signals = []
        
        try:
            # Calculate breakout indicators
            df['high_20'] = df['high'].rolling(window=20).max()
            df['low_20'] = df['low'].rolling(window=20).min()
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            
            # Calculate ATR with fallback
            if TALIB_AVAILABLE:
                df['atr'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            elif PANDAS_TA_AVAILABLE:
                df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
            else:
                # Basic ATR calculation
                df['tr1'] = df['high'] - df['low']
                df['tr2'] = abs(df['high'] - df['close'].shift())
                df['tr3'] = abs(df['low'] - df['close'].shift())
                df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
                df['atr'] = df['tr'].rolling(window=14).mean()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Upward breakout
            if (current['high'] > prev['high_20'] and
                current['volume'] > current['volume_sma'] * 1.5 and
                current['close'] > current['open']):
                
                confidence = 75 + min(20, (current['volume'] / current['volume_sma'] - 1.5) * 10)
                target_price = current['close'] + current['atr'] * 2
                stop_loss = prev['high_20']
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.BREAKOUT,
                    signal_type="BUY",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=10,
                    metadata={
                        'breakout_level': prev['high_20'],
                        'volume_ratio': current['volume'] / current['volume_sma'],
                        'atr': current['atr']
                    }
                ))
            
            # Downward breakout
            elif (current['low'] < prev['low_20'] and
                  current['volume'] > current['volume_sma'] * 1.5 and
                  current['close'] < current['open']):
                
                confidence = 75 + min(20, (current['volume'] / current['volume_sma'] - 1.5) * 10)
                target_price = current['close'] - current['atr'] * 2
                stop_loss = prev['low_20']
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.BREAKOUT,
                    signal_type="SELL",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=10,
                    metadata={
                        'breakout_level': prev['low_20'],
                        'volume_ratio': current['volume'] / current['volume_sma'],
                        'atr': current['atr']
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error in breakout strategy for {symbol}: {e}")
        
        return signals
    
    def scalping_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Scalping strategy for quick profits"""
        signals = []
        
        try:
            # Use shorter timeframes for scalping
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            
            # Calculate RSI and MACD with fallback
            if TALIB_AVAILABLE:
                df['rsi_5'] = talib.RSI(df['close'].values, timeperiod=5)
                df['macd_fast'], df['macd_signal_fast'], _ = talib.MACD(df['close'].values, fastperiod=5, slowperiod=10, signalperiod=3)
            elif PANDAS_TA_AVAILABLE:
                df['rsi_5'] = ta.rsi(df['close'], length=5)
                macd_data = ta.macd(df['close'], fast=5, slow=10, signal=3)
                df['macd_fast'] = macd_data['MACD_5_10_3']
                df['macd_signal_fast'] = macd_data['MACDs_5_10_3']
            else:
                # Basic calculations
                df['rsi_5'] = self._calculate_rsi(df['close'], 5)
                df['macd_fast'] = df['ema_5'] - df['ema_10']
                df['macd_signal_fast'] = df['macd_fast'].ewm(span=3).mean()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Quick BUY scalp
            if (current['ema_5'] > current['ema_10'] and
                prev['ema_5'] <= prev['ema_10'] and  # Just crossed
                current['rsi_5'] > 50 and current['rsi_5'] < 70 and
                current['macd_fast'] > current['macd_signal_fast']):
                
                confidence = 65
                target_price = current['close'] * 1.005  # 0.5% target
                stop_loss = current['close'] * 0.997   # 0.3% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.SCALPING,
                    signal_type="BUY",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=1,  # Very short holding
                    metadata={
                        'ema_cross': True,
                        'rsi_5': current['rsi_5'],
                        'strategy_type': 'quick_scalp'
                    }
                ))
            
            # Quick SELL scalp
            elif (current['ema_5'] < current['ema_10'] and
                  prev['ema_5'] >= prev['ema_10'] and  # Just crossed
                  current['rsi_5'] < 50 and current['rsi_5'] > 30 and
                  current['macd_fast'] < current['macd_signal_fast']):
                
                confidence = 65
                target_price = current['close'] * 0.995  # 0.5% target
                stop_loss = current['close'] * 1.003   # 0.3% stop loss
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.SCALPING,
                    signal_type="SELL",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=1,
                    metadata={
                        'ema_cross': True,
                        'rsi_5': current['rsi_5'],
                        'strategy_type': 'quick_scalp'
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error in scalping strategy for {symbol}: {e}")
        
        return signals
    
    def swing_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Swing trading strategy for medium-term positions"""
        signals = []
        
        try:
            # Calculate swing indicators with fallback
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            if TALIB_AVAILABLE:
                df['rsi'] = talib.RSI(df['close'].values, timeperiod=14)
                df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'].values)
            elif PANDAS_TA_AVAILABLE:
                df['rsi'] = ta.rsi(df['close'], length=14)
                macd_data = ta.macd(df['close'])
                df['macd'] = macd_data['MACD_12_26_9']
                df['macd_signal'] = macd_data['MACDs_12_26_9']
            else:
                df['rsi'] = self._calculate_rsi(df['close'], 14)
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                df['macd'] = ema_12 - ema_26
                df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            # Support and resistance levels
            df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
            df['support'] = df['pivot'] - (df['high'] - df['close'])
            df['resistance'] = df['pivot'] + (df['close'] - df['low'])
            
            current = df.iloc[-1]
            
            # Swing BUY setup
            if (current['close'] > current['sma_50'] > current['sma_200'] and  # Uptrend
                current['rsi'] > 40 and current['rsi'] < 60 and  # Not overbought
                current['close'] > current['support'] and
                current['macd'] > current['macd_signal']):
                
                confidence = 80
                target_price = current['resistance']
                stop_loss = current['support']
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.SWING,
                    signal_type="BUY",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=20,  # Longer holding period
                    metadata={
                        'trend': 'uptrend',
                        'support_level': current['support'],
                        'resistance_level': current['resistance'],
                        'rsi': current['rsi']
                    }
                ))
            
            # Swing SELL setup
            elif (current['close'] < current['sma_50'] < current['sma_200'] and  # Downtrend
                  current['rsi'] > 40 and current['rsi'] < 60 and  # Not oversold
                  current['close'] < current['resistance'] and
                  current['macd'] < current['macd_signal']):
                
                confidence = 80
                target_price = current['support']
                stop_loss = current['resistance']
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.SWING,
                    signal_type="SELL",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=20,
                    metadata={
                        'trend': 'downtrend',
                        'support_level': current['support'],
                        'resistance_level': current['resistance'],
                        'rsi': current['rsi']
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error in swing strategy for {symbol}: {e}")
        
        return signals
    
    def volume_analysis_strategy(self, df: pd.DataFrame, symbol: str) -> List[StrategySignal]:
        """Volume-based trading strategy"""
        signals = []
        
        try:
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            df['price_volume'] = df['close'] * df['volume']
            df['pv_sma'] = df['price_volume'].rolling(window=10).mean()
            
            # Calculate OBV with fallback
            if TALIB_AVAILABLE:
                df['obv'] = talib.OBV(df['close'].values, df['volume'].values)
            elif PANDAS_TA_AVAILABLE:
                df['obv'] = ta.obv(df['close'], df['volume'])
            else:
                # Basic OBV calculation
                df['price_change'] = df['close'].diff()
                df['obv_raw'] = df['volume'].where(df['price_change'] > 0, 
                                                  -df['volume'].where(df['price_change'] < 0, 0))
                df['obv'] = df['obv_raw'].cumsum()
            
            df['obv_sma'] = df['obv'].rolling(window=10).mean()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Volume spike with price increase
            if (current['volume_ratio'] > 2.0 and  # High volume
                current['close'] > prev['close'] and  # Price up
                current['obv'] > current['obv_sma'] and  # OBV confirmation
                (current['close'] - prev['close']) / prev['close'] > 0.01):  # Significant price move
                
                confidence = 70 + min(25, (current['volume_ratio'] - 2) * 10)
                target_price = current['close'] * 1.02
                stop_loss = current['close'] * 0.99
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.VOLUME_ANALYSIS,
                    signal_type="BUY",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=5,
                    metadata={
                        'volume_ratio': current['volume_ratio'],
                        'price_change': (current['close'] - prev['close']) / prev['close'],
                        'obv_signal': 'positive'
                    }
                ))
            
            # Volume spike with price decrease
            elif (current['volume_ratio'] > 2.0 and  # High volume
                  current['close'] < prev['close'] and  # Price down
                  current['obv'] < current['obv_sma'] and  # OBV confirmation
                  (prev['close'] - current['close']) / prev['close'] > 0.01):  # Significant price move
                
                confidence = 70 + min(25, (current['volume_ratio'] - 2) * 10)
                target_price = current['close'] * 0.98
                stop_loss = current['close'] * 1.01
                
                signals.append(StrategySignal(
                    symbol=symbol,
                    strategy=StrategyType.VOLUME_ANALYSIS,
                    signal_type="SELL",
                    confidence=confidence,
                    entry_price=current['close'],
                    target_price=target_price,
                    stop_loss=stop_loss,
                    holding_period=5,
                    metadata={
                        'volume_ratio': current['volume_ratio'],
                        'price_change': (prev['close'] - current['close']) / prev['close'],
                        'obv_signal': 'negative'
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error in volume analysis strategy for {symbol}: {e}")
        
        return signals
    
    def _filter_and_rank_signals(self, signals: List[StrategySignal]) -> List[StrategySignal]:
        """Filter and rank signals by confidence and strategy type"""
        if not signals:
            return []
        
        # Remove duplicate signals for same symbol and direction
        unique_signals = {}
        for signal in signals:
            key = f"{signal.symbol}_{signal.signal_type}"
            if key not in unique_signals or signal.confidence > unique_signals[key].confidence:
                unique_signals[key] = signal
        
        # Convert back to list and sort by confidence
        filtered_signals = list(unique_signals.values())
        filtered_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply minimum confidence threshold
        min_confidence = 60
        filtered_signals = [s for s in filtered_signals if s.confidence >= min_confidence]
        
        return filtered_signals
    
    def get_strategy_performance(self, strategy_type: StrategyType) -> Dict:
        """Get performance metrics for a specific strategy"""
        try:
            # This would typically query historical signal performance from database
            # For now, return mock performance data
            
            performance_data = {
                StrategyType.MOMENTUM: {'win_rate': 65, 'avg_return': 2.3, 'max_drawdown': 1.8},
                StrategyType.MEAN_REVERSION: {'win_rate': 72, 'avg_return': 1.8, 'max_drawdown': 1.2},
                StrategyType.BREAKOUT: {'win_rate': 58, 'avg_return': 3.1, 'max_drawdown': 2.5},
                StrategyType.SCALPING: {'win_rate': 68, 'avg_return': 0.8, 'max_drawdown': 0.5},
                StrategyType.SWING: {'win_rate': 61, 'avg_return': 4.2, 'max_drawdown': 3.1},
                StrategyType.VOLUME_ANALYSIS: {'win_rate': 69, 'avg_return': 2.1, 'max_drawdown': 1.6}
            }
            
            return performance_data.get(strategy_type, {'win_rate': 0, 'avg_return': 0, 'max_drawdown': 0})
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return {'win_rate': 0, 'avg_return': 0, 'max_drawdown': 0}

class StrategyOptimizer:
    """Optimize strategy parameters based on historical performance"""
    
    def __init__(self):
        self.strategies = AdvancedStrategies(Config())
        
    def optimize_strategy_weights(self) -> Dict[StrategyType, float]:
        """Optimize weights for different strategies based on performance"""
        weights = {}
        
        for strategy_type in StrategyType:
            performance = self.strategies.get_strategy_performance(strategy_type)
            
            # Calculate weight based on win rate and return
            weight = (performance['win_rate'] / 100) * (1 + performance['avg_return'] / 100)
            weight = max(0.1, min(1.0, weight))  # Clamp between 0.1 and 1.0
            
            weights[strategy_type] = weight
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def combine_strategy_signals(self, all_signals: List[StrategySignal]) -> List[StrategySignal]:
        """Combine signals from multiple strategies with optimized weights"""
        if not all_signals:
            return []
        
        weights = self.optimize_strategy_weights()
        
        # Apply weights to confidence scores
        for signal in all_signals:
            weight = weights.get(signal.strategy, 0.5)
            signal.confidence = signal.confidence * weight
        
        # Re-filter and rank with weighted confidence
        return self.strategies._filter_and_rank_signals(all_signals)
