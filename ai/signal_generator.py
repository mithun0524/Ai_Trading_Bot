import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from utils.logger import logger

class AISignalGenerator:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_path = "models/trading_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        self.is_trained = False
        
        # Ensure models directory exists
        os.makedirs("models", exist_ok=True)
        
        # Try to load existing model
        self.load_model()
    
    def prepare_features(self, df: pd.DataFrame, analysis: Dict) -> pd.DataFrame:
        """Prepare features for machine learning model"""
        try:
            if df.empty or not analysis:
                return pd.DataFrame()
            
            features_df = pd.DataFrame(index=df.index)
            
            # Price-based features
            features_df['close'] = df['close']
            features_df['high'] = df['high']
            features_df['low'] = df['low']
            features_df['volume'] = df['volume'] if 'volume' in df.columns else 0
            
            # Price change features
            features_df['price_change'] = df['close'].pct_change()
            features_df['price_change_2'] = df['close'].pct_change(2)
            features_df['price_change_5'] = df['close'].pct_change(5)
            
            # Volume features
            if 'volume' in df.columns:
                features_df['volume_change'] = df['volume'].pct_change()
                features_df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
            else:
                features_df['volume_change'] = 0
                features_df['volume_ma_ratio'] = 1
            
            # Volatility features
            features_df['volatility'] = df['close'].rolling(10).std()
            features_df['high_low_ratio'] = df['high'] / df['low']
            
            # Helper function to safely align arrays with DataFrame index
            def align_array_to_index(array, target_index, fill_value=np.nan):
                if array is None or len(array) == 0:
                    return pd.Series([fill_value] * len(target_index), index=target_index)
                
                # If array is shorter, pad with fill_value at the beginning
                if len(array) < len(target_index):
                    padding = len(target_index) - len(array)
                    padded_array = np.concatenate([np.full(padding, fill_value), array])
                    return pd.Series(padded_array, index=target_index)
                elif len(array) > len(target_index):
                    # If array is longer, take the last len(target_index) values
                    return pd.Series(array[-len(target_index):], index=target_index)
                else:
                    # Perfect match
                    return pd.Series(array, index=target_index)
            
            # Technical indicator features
            if 'rsi' in analysis and analysis['rsi'] is not None and len(analysis['rsi']) > 0:
                rsi_series = align_array_to_index(analysis['rsi'], df.index, 50)
                features_df['rsi'] = rsi_series
                features_df['rsi_oversold'] = (rsi_series < 30).astype(int)
                features_df['rsi_overbought'] = (rsi_series > 70).astype(int)
            else:
                features_df['rsi'] = 50
                features_df['rsi_oversold'] = 0
                features_df['rsi_overbought'] = 0
            
            # MACD features
            if ('macd' in analysis and analysis['macd']['macd'] is not None and 
                len(analysis['macd']['macd']) > 0):
                macd_series = align_array_to_index(analysis['macd']['macd'], df.index, 0)
                signal_series = align_array_to_index(analysis['macd']['signal'], df.index, 0)
                hist_series = align_array_to_index(analysis['macd']['histogram'], df.index, 0)
                
                features_df['macd'] = macd_series
                features_df['macd_signal'] = signal_series
                features_df['macd_histogram'] = hist_series
                features_df['macd_bullish'] = (macd_series > signal_series).astype(int)
            else:
                features_df['macd'] = 0
                features_df['macd_signal'] = 0
                features_df['macd_histogram'] = 0
                features_df['macd_bullish'] = 0
            
            # Bollinger Bands features
            if ('bb' in analysis and analysis['bb']['middle'] is not None and 
                len(analysis['bb']['middle']) > 0):
                upper_series = align_array_to_index(analysis['bb']['upper'], df.index, df['close'].iloc[-1] * 1.02)
                middle_series = align_array_to_index(analysis['bb']['middle'], df.index, df['close'].iloc[-1])
                lower_series = align_array_to_index(analysis['bb']['lower'], df.index, df['close'].iloc[-1] * 0.98)
                
                features_df['bb_upper'] = upper_series
                features_df['bb_middle'] = middle_series
                features_df['bb_lower'] = lower_series
                
                # Avoid division by zero
                bb_width = upper_series - lower_series
                bb_width = bb_width.replace(0, 0.01)  # Replace zeros with small positive number
                features_df['bb_position'] = (df['close'] - lower_series) / bb_width
                features_df['bb_squeeze'] = ((upper_series - lower_series) / middle_series < 0.1).astype(int)
            else:
                features_df['bb_upper'] = df['close'] * 1.02
                features_df['bb_middle'] = df['close']
                features_df['bb_lower'] = df['close'] * 0.98
                features_df['bb_position'] = 0.5
                features_df['bb_squeeze'] = 0
            
            # Moving average features
            if 'ma' in analysis and 'ema' in analysis['ma']:
                for period in [5, 10, 20, 50]:
                    ema_key = f'EMA_{period}'
                    if (ema_key in analysis['ma']['ema'] and 
                        analysis['ma']['ema'][ema_key] is not None and 
                        len(analysis['ma']['ema'][ema_key]) > 0):
                        ema_series = align_array_to_index(analysis['ma']['ema'][ema_key], df.index, df['close'].iloc[-1])
                        features_df[f'ema_{period}'] = ema_series
                        features_df[f'price_above_ema_{period}'] = (df['close'] > ema_series).astype(int)
                    else:
                        features_df[f'ema_{period}'] = df['close']
                        features_df[f'price_above_ema_{period}'] = 1
            
            # SMA features
            if 'ma' in analysis and 'sma' in analysis['ma']:
                for period in [20, 50]:
                    sma_key = f'SMA_{period}'
                    if (sma_key in analysis['ma']['sma'] and 
                        analysis['ma']['sma'][sma_key] is not None and 
                        len(analysis['ma']['sma'][sma_key]) > 0):
                        sma_series = align_array_to_index(analysis['ma']['sma'][sma_key], df.index, df['close'].iloc[-1])
                        features_df[f'sma_{period}'] = sma_series
                        features_df[f'price_above_sma_{period}'] = (df['close'] > sma_series).astype(int)
                    else:
                        features_df[f'sma_{period}'] = df['close']
                        features_df[f'price_above_sma_{period}'] = 1
            
            # Supertrend features
            if ('supertrend' in analysis and analysis['supertrend']['direction'] is not None and
                len(analysis['supertrend']['direction']) > 0):
                if isinstance(analysis['supertrend']['direction'], np.ndarray):
                    direction_series = align_array_to_index(analysis['supertrend']['direction'], df.index, 0)
                else:
                    direction_series = pd.Series([0] * len(df.index), index=df.index)
                features_df['supertrend_direction'] = direction_series
                features_df['supertrend_bullish'] = (direction_series == 1).astype(int)
            else:
                features_df['supertrend_direction'] = 0
                features_df['supertrend_bullish'] = 0
            
            # Pattern features (simplified for now)
            features_df['pattern_count'] = 0  # Placeholder
            
            # Time-based features
            features_df['hour'] = pd.to_datetime(df['timestamp']).dt.hour if 'timestamp' in df.columns else 12
            features_df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek if 'timestamp' in df.columns else 1
            
            # Instead of removing all NaN rows, fill remaining NaN values with reasonable defaults
            features_df = features_df.bfill().ffill().fillna(0)
            
            # Only remove rows where all major features are still NaN (which shouldn't happen now)
            if features_df.isnull().all(axis=1).any():
                features_df = features_df.dropna(how='all')
            
            return features_df
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    def create_labels(self, df: pd.DataFrame, lookforward: int = 5, threshold: float = 0.02) -> pd.Series:
        """Create labels for supervised learning"""
        try:
            labels = []
            close_prices = df['close'].values
            
            for i in range(len(close_prices) - lookforward):
                current_price = close_prices[i]
                future_prices = close_prices[i+1:i+lookforward+1]
                
                # Calculate future returns
                max_future_return = np.max(future_prices) / current_price - 1
                min_future_return = np.min(future_prices) / current_price - 1
                
                # Labeling logic
                if max_future_return > threshold:
                    labels.append(1)  # Buy signal
                elif min_future_return < -threshold:
                    labels.append(-1)  # Sell signal
                else:
                    labels.append(0)  # Hold/Neutral
            
            # Add neutral labels for the last lookforward periods
            labels.extend([0] * lookforward)
            
            return pd.Series(labels, index=df.index)
            
        except Exception as e:
            logger.error(f"Error creating labels: {e}")
            return pd.Series([0] * len(df), index=df.index)
    
    def train_model(self, training_data: List[Dict]):
        """Train the AI model with historical data"""
        try:
            if not training_data:
                logger.warning("No training data provided")
                return False
            
            all_features = []
            all_labels = []
            
            for data in training_data:
                if 'df' not in data or 'analysis' not in data:
                    continue
                
                df = data['df']
                analysis = data['analysis']
                
                # Prepare features
                features_df = self.prepare_features(df, analysis)
                if features_df.empty:
                    continue
                
                # Create labels
                labels = self.create_labels(df)
                
                # Align features and labels
                common_index = features_df.index.intersection(labels.index)
                if len(common_index) < 10:  # Need minimum data
                    continue
                
                features_aligned = features_df.loc[common_index]
                labels_aligned = labels.loc[common_index]
                
                all_features.append(features_aligned)
                all_labels.append(labels_aligned)
            
            if not all_features:
                logger.warning("No valid training features created")
                return False
            
            # Combine all features and labels
            X = pd.concat(all_features, ignore_index=True)
            y = pd.concat(all_labels, ignore_index=True)
            
            # Store feature columns
            self.feature_columns = X.columns.tolist()
            
            # Handle infinite and NaN values
            X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble model
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"Model trained with accuracy: {accuracy:.4f}")
            logger.info(f"Training samples: {len(X_train)}")
            
            # Cross-validation
            cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
            logger.info(f"Cross-validation scores: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            # Save model
            self.save_model()
            self.is_trained = True
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def predict_signal(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Predict trading signal using the trained model"""
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model not trained, using rule-based signals")
                return self.rule_based_signal(analysis, df['close'].iloc[-1] if not df.empty else 0)
            
            # Prepare features
            features_df = self.prepare_features(df, analysis)
            if features_df.empty:
                return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'Insufficient data'}
            
            # Use only the latest data point
            latest_features = features_df.iloc[-1:].copy()
            
            # Ensure all required columns are present
            for col in self.feature_columns:
                if col not in latest_features.columns:
                    latest_features[col] = 0
            
            # Reorder columns to match training
            latest_features = latest_features[self.feature_columns]
            
            # Handle infinite and NaN values
            latest_features = latest_features.replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Predict
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Get confidence (max probability)
            confidence = np.max(probabilities) * 100
            
            # Map prediction to signal
            signal_map = {-1: 'SELL', 0: 'NEUTRAL', 1: 'BUY'}
            signal = signal_map.get(prediction, 'NEUTRAL')
            
            # Generate reason based on feature importance
            reason = self.generate_signal_reason(latest_features, analysis)
            
            return {
                'signal': signal,
                'confidence': round(confidence, 2),
                'reason': reason,
                'prediction': int(prediction),
                'probabilities': probabilities.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error predicting signal: {e}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': f'Prediction error: {str(e)}'}
    
    def rule_based_signal(self, analysis: Dict, current_price: float) -> Dict:
        """Generate trading signal using rule-based approach with improved logic"""
        try:
            if not analysis:
                return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'No analysis data'}
            
            signals = []
            reasons = []
            confidence_factors = []
            
            # RSI signals (weight: high)
            if 'rsi' in analysis and analysis['rsi'] is not None:
                current_rsi = analysis['rsi'][-1]
                if not np.isnan(current_rsi):
                    if current_rsi < 25:  # Strong oversold
                        signals.append('BUY')
                        reasons.append(f"RSI Oversold ({current_rsi:.1f})")
                        confidence_factors.append(80)
                    elif current_rsi < 35:  # Mild oversold
                        signals.append('BUY')
                        reasons.append(f"RSI Low ({current_rsi:.1f})")
                        confidence_factors.append(65)
                    elif current_rsi > 75:  # Strong overbought
                        signals.append('SELL')
                        reasons.append(f"RSI Overbought ({current_rsi:.1f})")
                        confidence_factors.append(80)
                    elif current_rsi > 65:  # Mild overbought
                        signals.append('SELL')
                        reasons.append(f"RSI High ({current_rsi:.1f})")
                        confidence_factors.append(65)
            
            # MACD signals (weight: medium-high)
            if 'macd' in analysis and analysis['macd']['macd'] is not None:
                macd_line = analysis['macd']['macd'][-1]
                signal_line = analysis['macd']['signal'][-1]
                histogram = analysis['macd']['histogram'][-1]
                
                if not any(np.isnan([macd_line, signal_line, histogram])):
                    if macd_line > signal_line and histogram > 0:
                        signals.append('BUY')
                        reasons.append("MACD Bullish Cross")
                        confidence_factors.append(70)
                    elif macd_line < signal_line and histogram < 0:
                        signals.append('SELL')
                        reasons.append("MACD Bearish Cross")
                        confidence_factors.append(70)
            
            # Bollinger Bands signals (weight: medium)
            if 'bb' in analysis and analysis['bb']['middle'] is not None:
                upper = analysis['bb']['upper'][-1]
                lower = analysis['bb']['lower'][-1]
                middle = analysis['bb']['middle'][-1]
                
                if not any(np.isnan([upper, lower, middle, current_price])):
                    bb_position = (current_price - lower) / (upper - lower)
                    
                    if bb_position < 0.1:  # Near lower band
                        signals.append('BUY')
                        reasons.append("BB Support")
                        confidence_factors.append(60)
                    elif bb_position > 0.9:  # Near upper band
                        signals.append('SELL')
                        reasons.append("BB Resistance")
                        confidence_factors.append(60)
            
            # Supertrend signals (weight: high)
            if 'supertrend' in analysis and analysis['supertrend']['direction'] is not None:
                direction = analysis['supertrend']['direction'].iloc[-1]
                if not np.isnan(direction):
                    if direction == 1:
                        signals.append('BUY')
                        reasons.append("Supertrend Bullish")
                        confidence_factors.append(75)
                    else:
                        signals.append('SELL')
                        reasons.append("Supertrend Bearish")
                        confidence_factors.append(75)
            
            # Calculate final signal and confidence
            if not signals:
                return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'No clear signals'}
            
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')
            
            if buy_count > sell_count:
                signal = 'BUY'
                # Weight confidence by signal strength
                buy_confidences = [conf for i, conf in enumerate(confidence_factors) if signals[i] == 'BUY']
                avg_confidence = sum(buy_confidences) / len(buy_confidences) if buy_confidences else 60
                confidence = min(avg_confidence + (buy_count - sell_count) * 5, 85)
            elif sell_count > buy_count:
                signal = 'SELL'
                # Weight confidence by signal strength
                sell_confidences = [conf for i, conf in enumerate(confidence_factors) if signals[i] == 'SELL']
                avg_confidence = sum(sell_confidences) / len(sell_confidences) if sell_confidences else 60
                confidence = min(avg_confidence + (sell_count - buy_count) * 5, 85)
            else:
                signal = 'NEUTRAL'
                confidence = 50
            
            # Only return strong signals (confidence > 60) or keep neutral
            if confidence < 60 and signal != 'NEUTRAL':
                signal = 'NEUTRAL'
                confidence = 45
                reason = "Weak signal strength"
            else:
                reason = " + ".join(reasons[:3]) if reasons else "Mixed signals"
            
            return {
                'signal': signal,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based signal: {e}")
            return {'signal': 'NEUTRAL', 'confidence': 0, 'reason': 'Analysis error'}
    
    def generate_signal_reason(self, features: pd.DataFrame, analysis: Dict) -> str:
        """Generate human-readable reason for the signal"""
        try:
            reasons = []
            
            if not features.empty:
                # RSI reason
                if 'rsi' in features.columns:
                    rsi_val = features['rsi'].iloc[0]
                    if rsi_val < 30:
                        reasons.append(f"RSI Oversold ({rsi_val:.1f})")
                    elif rsi_val > 70:
                        reasons.append(f"RSI Overbought ({rsi_val:.1f})")
                
                # MACD reason
                if 'macd_bullish' in features.columns:
                    if features['macd_bullish'].iloc[0] == 1:
                        reasons.append("MACD Bullish")
                    else:
                        reasons.append("MACD Bearish")
                
                # Supertrend reason
                if 'supertrend_bullish' in features.columns:
                    if features['supertrend_bullish'].iloc[0] == 1:
                        reasons.append("Supertrend Bullish")
                    else:
                        reasons.append("Supertrend Bearish")
                
                # Pattern reasons
                pattern_cols = [col for col in features.columns if col.startswith('pattern_')]
                for col in pattern_cols:
                    if features[col].iloc[0] == 1:
                        pattern_name = col.replace('pattern_', '').replace('_', ' ').title()
                        reasons.append(f"{pattern_name} Pattern")
            
            return " + ".join(reasons[:3]) if reasons else "Multiple indicators confluence"
            
        except Exception as e:
            logger.error(f"Error generating reason: {e}")
            return "Technical analysis confluence"
    
    def save_model(self):
        """Save the trained model and scaler"""
        try:
            if self.model is not None:
                joblib.dump(self.model, self.model_path)
                joblib.dump(self.scaler, self.scaler_path)
                
                # Save feature columns
                with open("models/feature_columns.txt", "w") as f:
                    f.write("\n".join(self.feature_columns))
                
                logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self):
        """Load the trained model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                
                # Load feature columns
                feature_file = "models/feature_columns.txt"
                if os.path.exists(feature_file):
                    with open(feature_file, "r") as f:
                        self.feature_columns = [line.strip() for line in f.readlines()]
                
                self.is_trained = True
                logger.info("Model loaded successfully")
                return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
        
        return False
