#!/usr/bin/env python3
"""
Simple launcher script for the Events Organizer Helper Streamlit interface.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'pydantic',
        'requests',
        'python-dotenv',
        'openai',
        'httpx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install them with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_env_file():
    """Check if .env file exists and has API key."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("⚠️  No .env file found.")
        print("📝 Create one by copying env_example.txt:")
        print("   cp env_example.txt .env")
        print("   Then edit .env and add your OpenRouter API key")
        return False
    
    # Check if API key is set
    with open(env_file, 'r') as f:
        content = f.read()
        if 'OPENROUTER_API_KEY=your_openrouter_api_key_here' in content:
            print("⚠️  Please set your OpenRouter API key in .env file")
            return False
    
    print("✅ Environment file configured!")
    return True

def main():
    """Main launcher function."""
    print("🎉 Events Organizer Helper - Streamlit Interface")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        print("\n💡 You can still run the app, but you'll need to configure the API key in the Settings page.")
    
    print("\n🚀 Starting Streamlit application...")
    print("📖 Open your browser to the URL shown below")
    print("=" * 50)
    
    # Run streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 