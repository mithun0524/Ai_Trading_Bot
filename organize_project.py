#!/usr/bin/env python3
"""
🔧 Project Structure Organizer & Fixer
Organizes the entire AI Trading Bot project with proper structure
"""

import os
import sys
import shutil
from pathlib import Path

def organize_project():
    """Organize the entire project structure"""
    print("🔧 Organizing AI Trading Bot Project Structure")
    print("=" * 50)
    
    base_dir = Path("c:/Users/mitun/OneDrive/Desktop/AI AGENT")
    
    # 1. Create organized directory structure
    directories = {
        'src': base_dir / 'src',
        'src/core': base_dir / 'src' / 'core',
        'src/trading': base_dir / 'src' / 'trading', 
        'src/paper_trading': base_dir / 'src' / 'paper_trading',
        'src/web': base_dir / 'src' / 'web',
        'src/mobile': base_dir / 'src' / 'mobile',
        'tests': base_dir / 'tests',
        'docs': base_dir / 'docs',
        'config': base_dir / 'config',
        'scripts': base_dir / 'scripts'
    }
    
    print("Creating organized directory structure...")
    for name, path in directories.items():
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {name}")
    
    # 2. Move and organize existing files
    file_moves = [
        # Core trading files to src/core
        ('trading_bot.py', 'src/core/trading_bot.py'),
        ('config.py', 'src/core/config.py'),
        ('train_ai_model.py', 'src/core/train_ai_model.py'),
        
        # Paper trading to organized location
        ('paper_trading/paper_trading_manager.py', 'src/paper_trading/manager.py'),
        ('paper_trading/paper_trading_api.py', 'src/paper_trading/api.py'),
        ('paper_trading/start_paper_trading.py', 'src/paper_trading/start.py'),
        
        # Web dashboard
        ('web_dashboard.py', 'src/web/dashboard.py'),
        ('mobile_api.py', 'src/mobile/api.py'),
        
        # Test scripts to tests directory
        ('test_paper_trading.py', 'tests/test_paper_trading.py'),
        ('enhanced_test.py', 'tests/test_enhanced.py'),
        ('quick_test.py', 'tests/quick_test.py'),
        
        # Documentation
        ('README.md', 'docs/README.md'),
        ('HOW_TO_RUN.md', 'docs/HOW_TO_RUN.md'),
        ('QUICKSTART.md', 'docs/QUICKSTART.md'),
        
        # Scripts
        ('run_bot.py', 'scripts/run_bot.py'),
        ('launch_enhanced.py', 'scripts/launch_enhanced.py'),
    ]
    
    print("\nMoving files to organized structure...")
    for src, dst in file_moves:
        src_path = base_dir / src
        dst_path = base_dir / dst
        
        if src_path.exists():
            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                if dst_path.exists():
                    dst_path.unlink()  # Remove existing file
                shutil.move(str(src_path), str(dst_path))
                print(f"✅ Moved: {src} → {dst}")
            except Exception as e:
                print(f"⚠ Failed to move {src}: {e}")
        else:
            print(f"⚠ File not found: {src}")
    
    # 3. Copy paper_trading templates
    paper_trading_templates = base_dir / 'paper_trading' / 'templates'
    if paper_trading_templates.exists():
        dst_templates = base_dir / 'src' / 'paper_trading' / 'templates'
        shutil.copytree(str(paper_trading_templates), str(dst_templates), dirs_exist_ok=True)
        print("✅ Copied paper trading templates")
    
    # 4. Create __init__.py files for proper packages
    init_files = [
        'src/__init__.py',
        'src/core/__init__.py', 
        'src/trading/__init__.py',
        'src/paper_trading/__init__.py',
        'src/web/__init__.py',
        'src/mobile/__init__.py',
        'tests/__init__.py'
    ]
    
    print("\nCreating package structure...")
    for init_file in init_files:
        init_path = base_dir / init_file
        with open(init_path, 'w') as f:
            f.write('"""Package initialization"""\n')
        print(f"✅ Created: {init_file}")
    
    # 5. Create main project launcher
    launcher_content = '''#!/usr/bin/env python3
"""
🚀 AI Trading Bot - Main Launcher
Centralized launcher for all components
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def main():
    """Main launcher menu"""
    print("🤖 AI Trading Bot - Main Launcher")
    print("=" * 40)
    print("1. Start Trading Bot")
    print("2. Start Paper Trading")
    print("3. Start Web Dashboard")
    print("4. Train AI Model")
    print("5. Run Tests")
    print("0. Exit")
    
    choice = input("\\nSelect option (0-5): ").strip()
    
    if choice == "1":
        from core.trading_bot import main as start_trading
        start_trading()
    elif choice == "2":
        from paper_trading.api import app, socketio
        print("🎯 Starting Paper Trading System...")
        print("🌐 Dashboard: http://localhost:5002")
        socketio.run(app, host='0.0.0.0', port=5002, debug=False)
    elif choice == "3":
        from web.dashboard import main as start_dashboard
        start_dashboard()
    elif choice == "4":
        from core.train_ai_model import train_ai_model
        import asyncio
        asyncio.run(train_ai_model())
    elif choice == "5":
        import subprocess
        subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v'])
    elif choice == "0":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
'''
    
    with open(base_dir / 'launcher.py', 'w') as f:
        f.write(launcher_content)
    print("✅ Created main launcher")
    
    print("\n🎉 Project organization complete!")
    print("\nNew structure:")
    print("📁 src/")
    print("  📁 core/ - Core trading logic")
    print("  📁 paper_trading/ - Virtual trading system")
    print("  📁 web/ - Web dashboard")
    print("  📁 mobile/ - Mobile API")
    print("📁 tests/ - All test files")
    print("📁 docs/ - Documentation")
    print("📁 scripts/ - Utility scripts")
    print("📄 launcher.py - Main application launcher")

if __name__ == "__main__":
    organize_project()
