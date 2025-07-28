"""
Simple Technical Analysis Library Alternative
Provides basic indicators without requiring TA-Lib compilation
"""
import pandas as pd
import numpy as np

def RSI(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return pd.Series(index=prices.index, dtype=float)

def MACD(prices, fast=12, slow=26, signal=9):
    """Calculate MACD (Moving Average Convergence Divergence)"""
    try:
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    except Exception as e:
        print(f"Error calculating MACD: {e}")
        empty_series = pd.Series(index=prices.index, dtype=float)
        return empty_series, empty_series, empty_series

def BBANDS(prices, period=20, std=2):
    """Calculate Bollinger Bands"""
    try:
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)
        
        return upper, sma, lower
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {e}")
        empty_series = pd.Series(index=prices.index, dtype=float)
        return empty_series, empty_series, empty_series

def SMA(prices, period):
    """Simple Moving Average"""
    try:
        return prices.rolling(window=period).mean()
    except Exception as e:
        print(f"Error calculating SMA: {e}")
        return pd.Series(index=prices.index, dtype=float)

def EMA(prices, period):
    """Exponential Moving Average"""
    try:
        return prices.ewm(span=period).mean()
    except Exception as e:
        print(f"Error calculating EMA: {e}")
        return pd.Series(index=prices.index, dtype=float)

def SUPERTREND(high, low, close, period=10, multiplier=3):
    """Calculate Supertrend"""
    try:
        hl2 = (high + low) / 2
        atr = (high - low).rolling(window=period).mean()
        
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=float)
        
        for i in range(len(close)):
            if i == 0:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            else:
                if close.iloc[i] > supertrend.iloc[i-1]:
                    supertrend.iloc[i] = lower_band.iloc[i]
                    direction.iloc[i] = 1
                else:
                    supertrend.iloc[i] = upper_band.iloc[i]
                    direction.iloc[i] = -1
        
        return supertrend, direction
    except Exception as e:
        print(f"Error calculating Supertrend: {e}")
        empty_series = pd.Series(index=close.index, dtype=float)
        return empty_series, empty_series

def ATR(high, low, close, period=14):
    """Average True Range"""
    try:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    except Exception as e:
        print(f"Error calculating ATR: {e}")
        return pd.Series(index=high.index, dtype=float)

def STOCH(high, low, close, k_period=14, d_period=3):
    """Stochastic Oscillator"""
    try:
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    except Exception as e:
        print(f"Error calculating Stochastic: {e}")
        empty_series = pd.Series(index=high.index, dtype=float)
        return empty_series, empty_series

def WILLIAMS_R(high, low, close, period=14):
    """Williams %R"""
    try:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = ((highest_high - close) / (highest_high - lowest_low)) * -100
        
        return williams_r
    except Exception as e:
        print(f"Error calculating Williams %R: {e}")
        return pd.Series(index=high.index, dtype=float)

def OBV(close, volume):
    """On Balance Volume"""
    try:
        obv = (volume * np.sign(close.diff())).cumsum()
        return obv
    except Exception as e:
        print(f"Error calculating OBV: {e}")
        return pd.Series(index=close.index, dtype=float)

def ROC(prices, period=10):
    """Rate of Change"""
    try:
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    except Exception as e:
        print(f"Error calculating ROC: {e}")
        return pd.Series(index=prices.index, dtype=float)

# Additional utility functions
def crossover(series1, series2):
    """Check if series1 crosses over series2"""
    try:
        return (series1 > series2) & (series1.shift(1) <= series2.shift(1))
    except Exception as e:
        print(f"Error calculating crossover: {e}")
        return pd.Series(index=series1.index, dtype=bool)

def crossunder(series1, series2):
    """Check if series1 crosses under series2"""
    try:
        return (series1 < series2) & (series1.shift(1) >= series2.shift(1))
    except Exception as e:
        print(f"Error calculating crossunder: {e}")
        return pd.Series(index=series1.index, dtype=bool)

def highest(series, period):
    """Highest value in period"""
    try:
        return series.rolling(window=period).max()
    except Exception as e:
        print(f"Error calculating highest: {e}")
        return pd.Series(index=series.index, dtype=float)

def lowest(series, period):
    """Lowest value in period"""
    try:
        return series.rolling(window=period).min()
    except Exception as e:
        print(f"Error calculating lowest: {e}")
        return pd.Series(index=series.index, dtype=float)
