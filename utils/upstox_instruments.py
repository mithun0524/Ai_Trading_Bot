"""
Upstox v2 Instrument Key Mapping
This file contains the correct instrument keys for Upstox API v2
"""

# Major Nifty 50 stocks with their correct Upstox instrument keys
UPSTOX_INSTRUMENT_MAP = {
    # Format: "SYMBOL": "NSE_EQ|ISIN_CODE" or use token numbers
    "RELIANCE": "NSE_EQ|INE002A01018",
    "TCS": "NSE_EQ|INE467B01029",
    "HDFCBANK": "NSE_EQ|INE040A01034", 
    "INFY": "NSE_EQ|INE009A01021",
    "ICICIBANK": "NSE_EQ|INE090A01021",
    "HINDUNILVR": "NSE_EQ|INE030A01027",
    "ITC": "NSE_EQ|INE154A01025",
    "SBIN": "NSE_EQ|INE062A01020",
    "BHARTIARTL": "NSE_EQ|INE397D01024",
    "KOTAKBANK": "NSE_EQ|INE237A01028",
    "LT": "NSE_EQ|INE018A01030",
    "HCLTECH": "NSE_EQ|INE860A01027",
    "ASIANPAINT": "NSE_EQ|INE021A01026",
    "AXISBANK": "NSE_EQ|INE238A01034",
    "MARUTI": "NSE_EQ|INE585B01010",
    "SUNPHARMA": "NSE_EQ|INE044A01036",
    "TITAN": "NSE_EQ|INE280A01028",
    "ULTRACEMCO": "NSE_EQ|INE481G01011",
    "NESTLEIND": "NSE_EQ|INE239A01016",
    "BAJFINANCE": "NSE_EQ|INE296A01024",
    "WIPRO": "NSE_EQ|INE075A01022",
    "ONGC": "NSE_EQ|INE213A01029",
    "TATAMOTORS": "NSE_EQ|INE155A01022",
    "TECHM": "NSE_EQ|INE669C01036",
    "POWERGRID": "NSE_EQ|INE752E01010",
    "NTPC": "NSE_EQ|INE733E01010",
    "TATASTEEL": "NSE_EQ|INE081A01020",
    "DIVISLAB": "NSE_EQ|INE361B01024",
    "GRASIM": "NSE_EQ|INE047A01021",
    "M&M": "NSE_EQ|INE101A01026",
    "BAJAJFINSV": "NSE_EQ|INE918I01018",
    "HINDALCO": "NSE_EQ|INE038A01020",
    "INDUSINDBK": "NSE_EQ|INE095A01012",
    "ADANIENT": "NSE_EQ|INE423A01024",
    "COALINDIA": "NSE_EQ|INE522F01014",
    "HDFCLIFE": "NSE_EQ|INE795G01014",
    "SBILIFE": "NSE_EQ|INE123W01016",
    "BPCL": "NSE_EQ|INE029A01011",
    "CIPLA": "NSE_EQ|INE059A01026",
    "EICHERMOT": "NSE_EQ|INE066A01021",
    "HEROMOTOCO": "NSE_EQ|INE158A01026",
    "APOLLOHOSP": "NSE_EQ|INE437A01024",
    "DRREDDY": "NSE_EQ|INE089A01023",
    "BRITANNIA": "NSE_EQ|INE216A01030",
    "TATACONSUM": "NSE_EQ|INE192A01025",
    "JSWSTEEL": "NSE_EQ|INE019A01038",
    "UPL": "NSE_EQ|INE628A01036",
    "BAJAJ-AUTO": "NSE_EQ|INE917I01010",
    "LTIM": "NSE_EQ|INE214T01019",
    "ADANIPORTS": "NSE_EQ|INE742F01042",
}

# Index instruments
INDEX_INSTRUMENT_MAP = {
    "NIFTY": "NSE_INDEX|Nifty 50",
    "BANKNIFTY": "NSE_INDEX|Nifty Bank",
    "FINNIFTY": "NSE_INDEX|Nifty Financial Services",
}

def get_upstox_instrument_key(symbol: str, exchange: str = "NSE") -> str:
    """
    Get the correct Upstox instrument key for a symbol
    
    Args:
        symbol (str): Trading symbol (e.g., 'RELIANCE')
        exchange (str): Exchange name (default: 'NSE')
    
    Returns:
        str: Upstox instrument key or fallback format
    """
    # Check if it's an index
    if symbol in INDEX_INSTRUMENT_MAP:
        return INDEX_INSTRUMENT_MAP[symbol]
    
    # Check if it's a stock with known mapping
    if symbol in UPSTOX_INSTRUMENT_MAP:
        return UPSTOX_INSTRUMENT_MAP[symbol]
    
    # Fallback to generic format (may not work for all symbols)
    return f"{exchange}_EQ|{symbol}"

def is_symbol_supported(symbol: str) -> bool:
    """
    Check if a symbol is supported for Upstox integration
    
    Args:
        symbol (str): Trading symbol
    
    Returns:
        bool: True if symbol is supported
    """
    return symbol in UPSTOX_INSTRUMENT_MAP or symbol in INDEX_INSTRUMENT_MAP
