import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from utils.logger import logger

# Import our custom TA indicators instead of talib
try:
    import talib
    USE_TALIB = True
    logger.info("Using TA-Lib for technical indicators")
except ImportError:
    from utils.ta_indicators import RSI, MACD, BBANDS, SMA, EMA, SUPERTREND
    USE_TALIB = False
    logger.info("Using custom TA indicators (TA-Lib not available)")

class TechnicalAnalysis:
    def __init__(self, config):
        self.config = config
        self.rsi_period = int(config.get('RSI_PERIOD', 14))
        self.rsi_oversold = float(config.get('RSI_OVERSOLD', 30))
        self.rsi_overbought = float(config.get('RSI_OVERBOUGHT', 70))
        self.macd_fast = int(config.get('MACD_FAST', 12))
        self.macd_slow = int(config.get('MACD_SLOW', 26))
        self.macd_signal = int(config.get('MACD_SIGNAL', 9))
        self.bb_period = int(config.get('BB_PERIOD', 20))
        self.bb_std = float(config.get('BB_STD', 2))
        
        logger.info("TechnicalAnalysis initialized with custom indicators")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        # Normalize columns to lowercase for compatibility
        data.columns = [col.lower() for col in data.columns]
        if data.empty or len(data) < 50:
            logger.warning("Insufficient data for technical analysis")
            return data
        
        try:
            df = data.copy()
            
            # Calculate indicators based on available library
            if USE_TALIB:
                df = self._calculate_with_talib(df)
            else:
                df = self._calculate_with_custom(df)
            
            # Add additional indicators
            df = self._add_price_action_indicators(df)
            df = self._add_volume_indicators(df)
            df = self._add_momentum_indicators(df)
            
            logger.debug("All technical indicators calculated successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return data
    
    def _calculate_with_talib(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators using TA-Lib"""
        # RSI
        df['RSI'] = talib.RSI(df['close'].values, timeperiod=self.rsi_period)
        
        # MACD
        macd, signal, hist = talib.MACD(df['close'].values, 
                                       fastperiod=self.macd_fast,
                                       slowperiod=self.macd_slow, 
                                       signalperiod=self.macd_signal)
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(df['close'].values, 
                                           timeperiod=self.bb_period,
                                           nbdevup=self.bb_std,
                                           nbdevdn=self.bb_std)
        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower
        
        # Moving Averages
        df['SMA_20'] = talib.SMA(df['close'].values, timeperiod=20)
        df['SMA_50'] = talib.SMA(df['close'].values, timeperiod=50)
        df['EMA_12'] = talib.EMA(df['close'].values, timeperiod=12)
        df['EMA_26'] = talib.EMA(df['close'].values, timeperiod=26)
        df['EMA_50'] = talib.EMA(df['close'].values, timeperiod=50)
        
        return df
    
    def _calculate_with_custom(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators using custom functions"""
        # RSI
        df['RSI'] = RSI(df['close'], period=self.rsi_period)
        
        # MACD
        macd, signal, hist = MACD(df['close'], 
                                 fast=self.macd_fast,
                                 slow=self.macd_slow,
                                 signal=self.macd_signal)
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        # Bollinger Bands
        upper, middle, lower = BBANDS(df['close'], 
                                     period=self.bb_period,
                                     std=self.bb_std)
        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower
        
        # Moving Averages
        df['SMA_20'] = SMA(df['close'], 20)
        df['SMA_50'] = SMA(df['close'], 50)
        df['EMA_12'] = EMA(df['close'], 12)
        df['EMA_26'] = EMA(df['close'], 26)
        df['EMA_50'] = EMA(df['close'], 50)
        
        # Supertrend
        supertrend, direction = SUPERTREND(df['high'], df['low'], df['close'])
        df['Supertrend'] = supertrend
        df['ST_Direction'] = direction
        
        return df
    
    def _add_price_action_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price action indicators"""
        # Price changes
        df['Price_Change'] = df['close'].pct_change()
        df['Price_Change_5'] = df['close'].pct_change(5)
        
        # High-Low ratio
        df['HL_Ratio'] = (df['high'] - df['low']) / df['close']
        
        # Body size (for candlestick analysis)
        df['Body_Size'] = abs(df['open'] - df['close']) / df['close']
        df['Upper_Wick'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['close']
        df['Lower_Wick'] = (np.minimum(df['open'], df['close']) - df['low']) / df['close']
        
        # Support and Resistance levels (simplified)
        df['Resistance'] = df['high'].rolling(window=20).max()
        df['Support'] = df['low'].rolling(window=20).min()
        
        return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        # Volume moving average
        df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_SMA']
        
        # On Balance Volume (OBV)
        df['OBV'] = (df['volume'] * np.sign(df['close'].diff())).cumsum()
        
        # Volume Price Trend (VPT)
        df['VPT'] = (df['volume'] * df['close'].pct_change()).cumsum()
        
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        # Rate of Change
        df['ROC_10'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Stochastic Oscillator (simplified)
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['Stoch_K'] = ((df['close'] - low_14) / (high_14 - low_14)) * 100
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Williams %R
        df['Williams_R'] = ((high_14 - df['close']) / (high_14 - low_14)) * -100
        
        return df
    
    def detect_patterns(self, data: pd.DataFrame) -> List[Dict]:
        """Detect candlestick and chart patterns"""
        patterns = []
        
        if len(data) < 10:
            return patterns
        
        try:
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            # Bullish patterns
            if self._is_hammer(data.iloc[-1]):
                patterns.append({
                    'pattern': 'Hammer',
                    'type': 'Bullish',
                    'strength': 0.7
                })
            
            if self._is_bullish_engulfing(prev, latest):
                patterns.append({
                    'pattern': 'Bullish Engulfing',
                    'type': 'Bullish',
                    'strength': 0.8
                })
            
            # Bearish patterns
            if self._is_shooting_star(data.iloc[-1]):
                patterns.append({
                    'pattern': 'Shooting Star',
                    'type': 'Bearish',
                    'strength': 0.7
                })
            
            if self._is_bearish_engulfing(prev, latest):
                patterns.append({
                    'pattern': 'Bearish Engulfing',
                    'type': 'Bearish',
                    'strength': 0.8
                })
            
            # Doji pattern
            if self._is_doji(latest):
                patterns.append({
                    'pattern': 'Doji',
                    'type': 'Neutral',
                    'strength': 0.6
                })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            return []
    
    def _is_hammer(self, candle) -> bool:
        """Detect hammer pattern"""
        body = abs(candle['close'] - candle['open'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        
        return (lower_wick > 2 * body and upper_wick < body)
    
    def _is_shooting_star(self, candle) -> bool:
        """Detect shooting star pattern"""
        body = abs(candle['close'] - candle['open'])
        lower_wick = min(candle['open'], candle['close']) - candle['low']
        upper_wick = candle['high'] - max(candle['open'], candle['close'])
        
        return (upper_wick > 2 * body and lower_wick < body)
    
    def _is_doji(self, candle) -> bool:
        """Detect doji pattern"""
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        return body < (total_range * 0.1)  # Body is less than 10% of total range
    
    def _is_bullish_engulfing(self, prev, current) -> bool:
        """Detect bullish engulfing pattern"""
        return (prev['close'] < prev['open'] and  # Previous red candle
                current['close'] > current['open'] and  # Current green candle
                current['open'] < prev['close'] and  # Current opens below prev close
                current['close'] > prev['open'])  # Current closes above prev open
    
    def _is_bearish_engulfing(self, prev, current) -> bool:
        """Detect bearish engulfing pattern"""
        return (prev['close'] > prev['open'] and  # Previous green candle
                current['close'] < current['open'] and  # Current red candle
                current['open'] > prev['close'] and  # Current opens above prev close
                current['close'] < prev['open'])  # Current closes below prev open
    
    def get_trend_direction(self, data: pd.DataFrame) -> str:
        """Determine overall trend direction"""
        if data.empty or len(data) < 50:
            return "Unknown"
        
        try:
            latest = data.iloc[-1]
            
            # Use multiple indicators for trend determination
            trends = []
            
            # SMA trend
            if 'SMA_20' in data.columns and 'SMA_50' in data.columns:
                if latest['SMA_20'] > latest['SMA_50']:
                    trends.append('Bullish')
                else:
                    trends.append('Bearish')
            
            # EMA trend
            if 'EMA_12' in data.columns and 'EMA_26' in data.columns:
                if latest['EMA_12'] > latest['EMA_26']:
                    trends.append('Bullish')
                else:
                    trends.append('Bearish')
            
            # Price vs moving average
            if 'SMA_20' in data.columns:
                if latest['close'] > latest['SMA_20']:
                    trends.append('Bullish')
                else:
                    trends.append('Bearish')
            
            # MACD trend
            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                if latest['MACD'] > latest['MACD_Signal']:
                    trends.append('Bullish')
                else:
                    trends.append('Bearish')
            
            # Majority vote
            bullish_count = trends.count('Bullish')
            bearish_count = trends.count('Bearish')
            
            if bullish_count > bearish_count:
                return "Bullish"
            elif bearish_count > bullish_count:
                return "Bearish"
            else:
                return "Sideways"
                
        except Exception as e:
            logger.error(f"Error determining trend: {e}")
            return "Unknown"
    
    def get_support_resistance(self, data: pd.DataFrame) -> Tuple[float, float]:
        """Calculate support and resistance levels"""
        try:
            if len(data) < 20:
                latest = data.iloc[-1]
                return latest['low'], latest['high']
            
            # Use recent 20 periods for S/R calculation
            recent_data = data.tail(20)
            
            support = recent_data['low'].min()
            resistance = recent_data['high'].max()
            
            return support, resistance
            
        except Exception as e:
            logger.error(f"Error calculating S/R: {e}")
            latest = data.iloc[-1]
            return latest['low'], latest['high']
    
    def is_oversold(self, data: pd.DataFrame) -> bool:
        """Check if stock is oversold"""
        try:
            if 'RSI' in data.columns:
                latest_rsi = data['RSI'].iloc[-1]
                return latest_rsi < self.rsi_oversold
            return False
        except:
            return False
    
    def is_overbought(self, data: pd.DataFrame) -> bool:
        """Check if stock is overbought"""
        try:
            if 'RSI' in data.columns:
                latest_rsi = data['RSI'].iloc[-1]
                return latest_rsi > self.rsi_overbought
            return False
        except:
            return False
    
    def get_signal_strength(self, data: pd.DataFrame) -> float:
        """Calculate overall signal strength (0-1)"""
        try:
            if data.empty:
                return 0.0
            
            latest = data.iloc[-1]
            strength_factors = []
            
            # RSI factor
            if 'RSI' in data.columns and not pd.isna(latest['RSI']):
                rsi = latest['RSI']
                if rsi < 30 or rsi > 70:  # Strong oversold/overbought
                    strength_factors.append(0.8)
                elif rsi < 40 or rsi > 60:  # Moderate
                    strength_factors.append(0.6)
                else:
                    strength_factors.append(0.3)
            
            # Volume factor
            if 'Volume_Ratio' in data.columns and not pd.isna(latest['Volume_Ratio']):
                vol_ratio = latest['Volume_Ratio']
                if vol_ratio > 2.0:  # Very high volume
                    strength_factors.append(0.9)
                elif vol_ratio > 1.5:  # High volume
                    strength_factors.append(0.7)
                else:
                    strength_factors.append(0.4)
            
            # Price change factor
            if 'Price_Change' in data.columns and not pd.isna(latest['Price_Change']):
                price_change = abs(latest['Price_Change'])
                if price_change > 0.03:  # >3% change
                    strength_factors.append(0.8)
                elif price_change > 0.015:  # >1.5% change
                    strength_factors.append(0.6)
                else:
                    strength_factors.append(0.3)
            
            # MACD factor
            if all(col in data.columns for col in ['MACD', 'MACD_Signal']):
                if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']):
                    macd_diff = latest['MACD'] - latest['MACD_Signal']
                    if abs(macd_diff) > 0.5:
                        strength_factors.append(0.7)
                    else:
                        strength_factors.append(0.4)
            
            # Calculate average strength
            if strength_factors:
                return min(1.0, sum(strength_factors) / len(strength_factors))
            else:
                return 0.5  # Default moderate strength
                
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return 0.5
    
    def analyze_all_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate all indicators and return analysis dictionary for AI model"""
        try:
            # First calculate all indicators
            analyzed_df = self.calculate_indicators(df)
            
            if analyzed_df.empty or len(analyzed_df) < 10:
                return {}
            
            # Extract the latest values and create analysis dictionary
            latest = analyzed_df.iloc[-1]
            
            # Helper function to safely get array values
            def get_values(col_name):
                if col_name in analyzed_df.columns:
                    values = analyzed_df[col_name].dropna()
                    if len(values) > 0:
                        return values.values
                return np.array([])
            
            analysis = {
                'rsi': get_values('RSI'),
                'macd': {
                    'macd': get_values('MACD'),
                    'signal': get_values('MACD_Signal'),
                    'histogram': get_values('MACD_Hist'),
                },
                'bb': {
                    'upper': get_values('BB_Upper'),
                    'middle': get_values('BB_Middle'),
                    'lower': get_values('BB_Lower'),
                },
                'ma': {
                    'sma': {
                        'SMA_20': get_values('SMA_20'),
                        'SMA_50': get_values('SMA_50'),
                    },
                    'ema': {
                        'EMA_5': get_values('EMA_12'),  # Use EMA_12 as EMA_5
                        'EMA_10': get_values('EMA_12'),
                        'EMA_20': get_values('EMA_26'),  # Use EMA_26 as EMA_20
                        'EMA_50': get_values('EMA_50'),
                    }
                },
                'supertrend': {
                    'direction': get_values('ST_Direction') if 'ST_Direction' in analyzed_df.columns else np.array([1] * len(analyzed_df)),
                    'value': get_values('Supertrend') if 'Supertrend' in analyzed_df.columns else analyzed_df['close'].values * 0.98,
                },
                'patterns': {},
                'volume': {
                    'current': latest['volume'] if 'volume' in analyzed_df.columns and not pd.isna(latest['volume']) else 0,
                    'average': analyzed_df['volume'].mean() if 'volume' in analyzed_df.columns else 0,
                },
                'trend': 'BULLISH' if ('SMA_20' in analyzed_df.columns and 'SMA_50' in analyzed_df.columns and 
                                      not pd.isna(latest['SMA_20']) and not pd.isna(latest['SMA_50']) and 
                                      latest['SMA_20'] > latest['SMA_50']) else 'BEARISH',
                'support': analyzed_df['low'].min() if 'low' in analyzed_df.columns else latest['close'] * 0.95,
                'resistance': analyzed_df['high'].max() if 'high' in analyzed_df.columns else latest['close'] * 1.05,
                'current_price': latest['close'] if 'close' in analyzed_df.columns and not pd.isna(latest['close']) else 0,
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_all_indicators: {e}")
            return {}
