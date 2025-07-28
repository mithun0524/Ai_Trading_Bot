#!/usr/bin/env python3
"""
AI Model Training Script
Trains the AI signal generator with historical data from multiple symbols
"""

import asyncio
from config import Config
from data.data_provider import DataProvider
from analysis.technical_analysis import TechnicalAnalysis
from ai.signal_generator import AISignalGenerator
from utils.logger import logger

async def train_ai_model():
    """Train the AI model with fresh data"""
    try:
        logger.info("Starting AI model training...")
        
        # Initialize components
        data_provider = DataProvider()
        technical_analyzer = TechnicalAnalysis(Config())
        ai_generator = AISignalGenerator()
        
        # Get training data for multiple symbols
        training_data = []
        
        # Use a diverse set of symbols for training
        training_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'ITC', 'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT'
        ]
        
        logger.info(f"Gathering training data for {len(training_symbols)} symbols...")
        
        for symbol in training_symbols:
            try:
                logger.info(f"Processing {symbol}...")
                
                # Get longer historical data for training (2-3 years)
                df = data_provider.get_historical_data(symbol, 'day', Config.TRAINING_DATA_DAYS)
                
                if df.empty or len(df) < 100:
                    logger.warning(f"Insufficient data for {symbol}: {len(df) if not df.empty else 0} records")
                    continue
                
                # Perform technical analysis
                analysis = technical_analyzer.analyze_all_indicators(df)
                if not analysis or len(analysis) == 0:
                    logger.warning(f"Technical analysis failed for {symbol}")
                    continue
                
                training_data.append({
                    'symbol': symbol,
                    'df': df,
                    'analysis': analysis
                })
                
                logger.info(f"Successfully gathered {len(df)} records for {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        if len(training_data) < 3:
            logger.error(f"Insufficient training data: only {len(training_data)} symbols with data")
            logger.info("Need at least 3 symbols with sufficient historical data")
            return False
        
        # Train the model
        logger.info(f"Training AI model with data from {len(training_data)} symbols...")
        success = ai_generator.train_model(training_data)
        
        if success:
            logger.info("AI model training completed successfully!")
            logger.info("The trained model can now generate signals for the trading bot")
            
            # Test the trained model
            test_symbol = training_symbols[0]
            test_data = next((data for data in training_data if data['symbol'] == test_symbol), None)
            
            if test_data:
                logger.info(f"Testing model with {test_symbol}...")
                signal_result = ai_generator.predict_signal(test_data['df'], test_data['analysis'])
                logger.info(f"Test signal: {signal_result}")
            
            return True
        else:
            logger.error("AI model training failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in AI model training: {e}")
        return False

if __name__ == "__main__":
    print("🤖 AI Model Training Script")
    print("=" * 40)
    
    # Run the training
    success = asyncio.run(train_ai_model())
    
    if success:
        print("\n✅ Training completed successfully!")
        print("You can now run the trading bot with a trained AI model.")
    else:
        print("\n❌ Training failed!")
        print("Check the logs for details. The bot will use rule-based signals.")
