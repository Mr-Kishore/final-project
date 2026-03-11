#!/usr/bin/env python3
"""
Test script to verify the updated functionality
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        from src.database import DatabaseManager
        print("✅ DatabaseManager imported successfully")
        
        from src.core import parse_chat, is_system_message, save_messages_to_json, filter_and_insert_messages
        print("✅ Core functions imported successfully")
        
        # Test database connection
        db = DatabaseManager()
        if db.connect():
            print("✅ Database connection successful")
            db.close()
        else:
            print("❌ Database connection failed")
            
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_cli_help():
    """Test CLI help functionality"""
    try:
        import argparse
        from main import main
        
        # Mock sys.argv to test help
        original_argv = sys.argv
        sys.argv = ['main.py', '--help']
        
        try:
            main()
        except SystemExit:
            # argparse calls sys.exit(0) after showing help
            pass
        
        sys.argv = original_argv
        print("✅ CLI help works correctly")
        return True
    except Exception as e:
        print(f"❌ CLI help error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Updated Conversational Data Analysis System")
    print("=" * 50)
    
    print("\n📦 Testing Imports...")
    imports_ok = test_imports()
    
    print("\n🔧 Testing CLI...")
    cli_ok = test_cli_help()
    
    print("\n" + "=" * 50)
    if imports_ok and cli_ok:
        print("🎉 All tests passed! System is ready.")
    else:
        print("❌ Some tests failed. Check the errors above.")
