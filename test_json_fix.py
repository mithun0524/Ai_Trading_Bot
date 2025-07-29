#!/usr/bin/env python3
"""
Test JSON serialization fix
"""

print("Testing JSON serialization fix...")

try:
    import numpy as np
    import pandas as pd
    from datetime import datetime
    
    # Import the fixed dashboard
    from web_dashboard import TradingDashboard
    
    dashboard = TradingDashboard()
    
    # Test data with various problematic types
    test_data = {
        'datetime_obj': datetime.now(),
        'numpy_int64': np.int64(42),
        'numpy_float64': np.float64(3.14),
        'pandas_nan': pd.NaT,
        'numpy_array': np.array([1, 2, 3]),
        'nested': {
            'int64': np.int64(100),
            'float64': np.float64(2.5)
        },
        'list_with_numpy': [np.int64(1), np.float64(2.5), datetime.now()]
    }
    
    print("Original data types:")
    for key, value in test_data.items():
        print(f"  {key}: {type(value)} = {value}")
    
    print("\nTesting serialization...")
    serialized = dashboard.serialize_datetime(test_data)
    
    print("Serialized data types:")
    for key, value in serialized.items():
        print(f"  {key}: {type(value)} = {value}")
    
    # Test JSON conversion
    import json
    json_str = json.dumps(serialized)
    print(f"\n✓ JSON serialization successful! Length: {len(json_str)} characters")
    
    print("\n🎉 int64/numpy serialization fix working!")
    print("\nThe web dashboard should now handle all data types properly.")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")
