@echo off
echo 🤖 AI Trading Bot - Quick Setup
echo ================================

echo.
echo 📦 Installing dependencies...
python setup.py

echo.
echo 🧪 Testing bot functionality...
python test_bot.py

echo.
echo ⚙️ Setup complete!
echo.
echo 📝 Next steps:
echo 1. Edit the .env file with your API keys
echo 2. Run: start_bot.bat
echo.
pause
