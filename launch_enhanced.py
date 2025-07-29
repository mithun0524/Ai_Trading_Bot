#!/usr/bin/env python3
"""
🚀 Enhanced AI Trading Bot Launcher
Launch all services with one command
"""

import subprocess
import sys
import time
import webbrowser
from threading import Thread
import signal
import os

class ServiceLauncher:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def launch_service(self, script_name, service_name, port=None):
        """Launch a service in the background"""
        try:
            print(f"🚀 Starting {service_name}...")
            process = subprocess.Popen([sys.executable, script_name], 
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append((process, service_name))
            
            if port:
                time.sleep(3)  # Wait for service to start
                print(f"✅ {service_name} started on port {port}")
            else:
                print(f"✅ {service_name} started")
                
            return True
        except Exception as e:
            print(f"❌ Failed to start {service_name}: {e}")
            return False
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Shutting down all services...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Clean up all processes"""
        for process, name in self.processes:
            try:
                process.terminate()
                print(f"🔄 Stopped {name}")
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
    
    def launch_all(self):
        """Launch all enhanced services"""
        print("🤖 Enhanced AI Trading Bot Launcher")
        print("=" * 50)
        
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
        services = [
            ("web_dashboard.py", "Web Dashboard", 5000),
            ("mobile_api.py", "Mobile API", 5001),
            ("trading_bot.py", "Trading Bot", None)
        ]
        
        success_count = 0
        
        for script, name, port in services:
            if self.launch_service(script, name, port):
                success_count += 1
            time.sleep(2)  # Stagger the starts
        
        if success_count == len(services):
            print("\n🎉 All services started successfully!")
            print("\n📍 Access Points:")
            print("🌐 Web Dashboard: http://localhost:5000")
            print("📱 Mobile Interface: http://localhost:5001")
            print("💬 Telegram Bot: Send /start to your bot")
            
            # Optionally open web dashboard
            try:
                print("\n🔗 Opening web dashboard in browser...")
                webbrowser.open("http://localhost:5000")
            except Exception:
                pass
            
            print("\n💡 Press Ctrl+C to stop all services")
            
            # Keep the launcher running
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.signal_handler(signal.SIGINT, None)
        else:
            print(f"\n⚠️  Only {success_count}/{len(services)} services started successfully")
            self.cleanup()

def main():
    """Main launcher function"""
    try:
        launcher = ServiceLauncher()
        launcher.launch_all()
    except Exception as e:
        print(f"❌ Launcher error: {e}")

if __name__ == "__main__":
    main()
