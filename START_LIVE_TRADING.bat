@echo off
title LIVE Trading System Launcher
color 0A

echo.
echo ===============================================
echo     🚀 LIVE TRADING SYSTEM LAUNCHER
echo ===============================================
echo.
echo 🔥 Complete Live Trading System with:
echo    📊 Real-time stock data
echo    🤖 AI-powered signals  
echo    💰 Virtual trading
echo    🌐 Live web dashboard
echo.
echo ===============================================

cd /d "%~dp0"

echo 🚀 Starting system...
python launch_complete_system.py

echo.
echo System stopped. Press any key to exit...
pause >nul
