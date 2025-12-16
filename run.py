#!/usr/bin/env python3
"""
Main launcher for NutriLens
"""

import os
import sys
import subprocess
import webbrowser
import time

def check_requirements():
    """Check and install requirements"""
    print(" Checking requirements...")
    
    try:
        # Try to import key modules
        import pymongo
        import streamlit
        import google.generativeai
        print(" All modules are installed")
        return True
    except ImportError as e:
        print(f" Missing module: {e}")
        
        response = input("Install missing requirements? (y/n): ").lower()
        if response == 'y':
            print(" Installing requirements...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                print(" Requirements installed")
                return True
            except Exception as e:
                print(f" Failed to install: {e}")
                return False
        return False

def run_app():
    """Run the Streamlit app"""
    print("\n" + "="*60)
    print(" LAUNCHING NUTRI LENS")
    print("="*60)
    
    print("\n Opening browser to: http://localhost:8501")
    print(" Starting Streamlit...")
    print(" Press Ctrl+C to stop")
    print("="*60)
    
    # Open browser after delay
    time.sleep(2)
    webbrowser.open("http://localhost:8501")
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit",
            "run", "app.py",
            "--server.port=8501",
            "--server.headless=false",
            "--theme.base=light"
        ])
    except KeyboardInterrupt:
        print("\n App stopped by user")
    except Exception as e:
        print(f"\n Error: {e}")

def main():
    """Main entry point"""
    print("="*60)
    print(" NUTRI LENS - AI Nutrition Assistant")
    print("="*60)
    
    # Check requirements
    if not check_requirements():
        print(" Cannot proceed without requirements")
        return
    
    # Ask for run mode
    print("\n1. Run app")
    print("2. Exit")
    
    choice = input("\nSelect (1-2): ").strip()
    
    if choice == "1":
        run_app()
    else:
        print(" Goodbye!")

if __name__ == "__main__":
    main()