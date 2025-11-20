#!/usr/bin/env python3
"""
Campus Navigator Launcher

Quick launcher for the Campus Navigator application.
Provides options for GUI or command-line interface.
"""

import sys
import os

def main():
    print("🗺️  Campus Navigator - Graph-Based Pathfinding Tool")
    print("=" * 55)
    print()
    print("Choose your interface:")
    print("  1. 🖥️  GUI Application (Recommended)")
    print("  2. 💻 Command Line Interface")
    print("  3. 🧪 Run Tests")
    print("  4. 📊 View Demo")
    print("  5. ❌ Exit")
    print()
    
    while True:
        try:
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                print("🚀 Launching GUI application...")
                os.system('python gui.py')
                break
            elif choice == '2':
                print("🚀 Starting interactive command line...")
                os.system('python main.py --interactive')
                break
            elif choice == '3':
                print("🧪 Running test suite...")
                os.system('python tests/basic_tests.py')
                break
            elif choice == '4':
                print("📊 Running demonstration...")
                print("Press Ctrl+C to stop the demo at any time")
                os.system('python demo.py')
                break
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()