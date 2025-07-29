@echo off
echo Testing Python and pip installation...
python --version
echo.
echo Installing required packages...
pip install flask flask-socketio flask-cors pyjwt pandas-ta requests
echo.
echo Testing imports...
python -c "import flask; print('Flask: OK')"
python -c "import pandas; print('Pandas: OK')"
python -c "try: import talib; print('TA-Lib: OK'); except: print('TA-Lib: Using fallback')"
python -c "try: import pandas_ta; print('Pandas-TA: OK'); except: print('Pandas-TA: Installing...')"
echo.
echo Running quick test...
python quick_test.py
pause
