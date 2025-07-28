import logging
import colorlog
from config import Config

def setup_logger():
    """Setup colored logging for the trading bot"""
    
    # Create logger
    logger = logging.getLogger('TradingBot')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with color
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Create file handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # Create formatters
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add formatters to handlers
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create global logger instance
logger = setup_logger()
