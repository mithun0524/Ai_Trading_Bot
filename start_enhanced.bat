@echo off
title Enhanced Trading Bot Setup
color 0A

echo ========================================
echo    Enhanced Trading Bot Setup
echo ========================================
echo.

echo Step 1: Installing dependencies...
echo.
pip install flask flask-socketio flask-cors pyjwt pandas-ta requests
echo.

echo Step 2: Testing installation...
echo.
python enhanced_test.py
echo.

echo Step 3: Choose what to run:
echo.
echo [1] Web Dashboard (Recommended)
echo [2] Mobile API
echo [3] Both (Advanced)
echo [4] Just test and exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Starting Web Dashboard...
    echo Open your browser to: http://localhost:5000
    python web_dashboard.py
) else if "%choice%"=="2" (
    echo Starting Mobile API...
    echo API available at: http://localhost:5001
    python mobile_api.py
) else if "%choice%"=="3" (
    echo Starting both services...
    echo Web Dashboard: http://localhost:5000
    echo Mobile API: http://localhost:5001
    start "Mobile API" python mobile_api.py
    python web_dashboard.py
) else (
    echo Test completed. Check the output above.
    echo.
    echo To start manually:
    echo   Web Dashboard: python web_dashboard.py
    echo   Mobile API: python mobile_api.py
)

echo.
pause
