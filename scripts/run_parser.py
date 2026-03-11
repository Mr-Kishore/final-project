#!/usr/bin/env python3
"""
Standalone script to run the Conversational Data Analysis System parser.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import parse_chat_file, save_messages_to_json, filter_system_messages
from src.database import DatabaseManager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def main():
    """Run the parser with database integration."""
    print("🚀 Starting Conversational Data Analysis System...")
    print("📂 Running chat conversation parser...")
    
    # Parse the chat file
    input_file = DATA_DIR / "chat.txt"
    messages = parse_chat_file(str(input_file))
    if messages is None:
        print(f"❌ Could not parse input file: {input_file}")
        sys.exit(1)

    print(f"📊 Parsed {len(messages)} raw messages")
    
    # Filter system messages
    filtered_messages = filter_system_messages(messages)
    print(f"🔍 Filtered to {len(filtered_messages)} messages (removed {len(messages) - len(filtered_messages)} system messages)")
    
    # Save to JSON
    output_file = DATA_DIR / "chat.json"
    save_messages_to_json(filtered_messages, str(output_file))
    print(f"💾 Saved filtered messages to {output_file}")
    
    # Insert into database
    db = DatabaseManager()
    db.insert_messages(filtered_messages)
    print("🗄️  Messages inserted into database")
    
    # Show stats
    db.show_stats()
    
    print("✅ Conversational Data Analysis completed successfully!")


if __name__ == "__main__":
    main()
