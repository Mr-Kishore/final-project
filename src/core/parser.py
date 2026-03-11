import re
import csv
import json
from datetime import datetime
import os
from pathlib import Path

# === Configuration ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
INPUT_FILE = "chat.txt"
JSON_OUT = "chat.json"

# Adjust this to match export format
DATE_FORMAT = "%d/%m/%y, %I:%M:%S %p"

# Regex pattern to match each new message line with square brackets
msg_pattern = re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2}:\d{2}\s(?:AM|PM))\]\s([^:]+):\s(.*)")


def parse_chat_file(input_file=INPUT_FILE):
    """Parse the chat conversation file and return a list of messages"""
    messages = []
    current_msg = None
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                match = msg_pattern.match(line)
                if match:
                    if current_msg:
                        messages.append(current_msg)
                        
                    date_str, time_str, author, text = match.groups()
                    try:
                        dt = datetime.strptime(f"{date_str}, {time_str}", DATE_FORMAT)
                    except Exception as e:
                        print(f"   Date parsing error on line {line_num}: {e}")
                        dt = None
                        
                    # Clean up author name (remove ~ prefix and phone number formatting)
                    text = text.strip()
                    if text.startswith('~'):
                        text = text[1:].strip()
                    
                    current_msg = {
                        "datetime": dt.isoformat() if dt else None,
                        "date": date_str,
                        "time": time_str,
                        "author": author,
                        "text": text.strip(),
                        "line_number": line_num
                    }
                else:
                    # Continuation of the previous message (multi-line)
                    if current_msg and line:
                        current_msg["text"] += "\n" + line
    except FileNotFoundError:
        print(f"  Error: Could not find file '{input_file}'")
        return None
    except Exception as e:
        print(f"  Error reading file: {e}")
        return None
    
    # Append last message
    if current_msg:
        messages.append(current_msg)
    
    return messages


def save_messages_to_json(messages, output_file=JSON_OUT):
    """Save parsed messages to JSON file"""
    try:
        with open(output_file, "w", encoding="utf-8") as jf:
            json.dump(messages, jf, ensure_ascii=False, indent=2)
        print(f"  Saved JSON → {output_file}")
        return True
    except Exception as e:
        print(f"  Error writing JSON: {e}")
        return False

def save_to_json(messages, output_file=JSON_OUT):
    """Backward-compatible alias for save_messages_to_json."""
    return save_messages_to_json(messages, output_file)


def display_sample_messages(messages, count=3):
    print(f"\n Sample messages:")
    for i, msg in enumerate(messages[:count]):
        print(f"   {i+1}. [{msg['date']} {msg['time']}] {msg['author']}: {msg['text'][:50]}...")


def is_system_message(text):
    """Check if a message is a system message that should be filtered out"""
    if not text:
        return True
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower().strip()
    
    # System message patterns to filter out
    system_patterns = [
        "created this group",
        "joined using a group link",
        "you joined using a group link",
        "left",
        "changed the group name",
        "changed the group icon",
        "changed the group description",
        "changed the group settings",
        "changed the group's settings",
        "turned off disappearing messages",
        "turned on disappearing messages",
        "pinned a message",
        "unpinned a message",
        "changed their phone number",
        "change the settings",
        "removed",
        "added",
        "messages and calls are end-to-end encrypted",
        "changed the group description",
        "changed the subject",
        "security code changed",
        "group invite link",
        "deleted this message",
        "this message was deleted"
    ]
    
    # Check if any system pattern is in the message
    for pattern in system_patterns:
        if pattern in text_lower:
            return True
    
    return False

def filter_system_messages(messages):
    """Return only user messages after dropping system-generated events."""
    if messages is None:
        return []
    return [msg for msg in messages if not is_system_message(msg.get("text", ""))]

def filter_and_insert_messages(messages, batch_size=100):
    """Insert filtered messages into SQLite database in batches"""
    print(f"\n Inserting data into SQLite database...")
    print(f"   • Total messages to insert: {len(messages)}")
    
    # Import DatabaseManager only when needed to avoid circular imports
    try:
        from ..database import DatabaseManager
    except Exception as e:
        print(f"    Database dependency unavailable: {e}")
        return False
    
    # Process messages in batches
    total_inserted = 0
    db = DatabaseManager()
    
    if db.connect():
        if db.create_table_if_not_exists():
            # Insert messages in batches
            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                inserted_count = db.insert_messages(batch)
                total_inserted += inserted_count
                print(f"   • Inserted batch {i//batch_size + 1}: {inserted_count} messages")
            
            if total_inserted > 0:
                db.get_table_stats()
        db.close()
        return True
    else:
        print("    Skipping database insertion due to connection failure")
        return False


def main():
    """Main function to parse chat file, save to JSON, and insert into database"""
    # Parse the chat file
    messages = parse_chat_file()
    print(f" Parsed {len(messages)} messages from chat file")
    
    # Filter system messages
    filtered_messages = filter_system_messages(messages)
    print(f" Filtered to {len(filtered_messages)} messages (removed {len(messages) - len(filtered_messages)} system messages)")
    
    # Save to JSON
    if save_messages_to_json(filtered_messages):
        print(" Saved filtered messages to chat.json")
    
    # Insert into database
    if filter_and_insert_messages(filtered_messages):
        print("  Messages inserted into database")
    
    return filtered_messages


if __name__ == "__main__":
    main()
