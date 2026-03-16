
import argparse
import json
from pathlib import Path
from src.core import parse_chat, is_system_message, save_messages_to_json, filter_and_insert_messages

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def run_parser():
    """Run the chat parser and save to database."""
    print("🚀 Starting Conversational Data Analysis System...")
    print("📂 Running chat conversation parser and database insertion...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    input_file = DATA_DIR / "chat.txt"

    messages = parse_chat(str(input_file))
    if messages is None:
        print(f"❌ Parsing failed. Ensure input exists at: {input_file}")
        return

    filtered_messages = [msg for msg in messages if not is_system_message(msg.get("text", ""))]
    save_messages_to_json(filtered_messages, str(DATA_DIR / "chat.json"))
    print(f"💾 Saved filtered messages to chat.json")
    print(f"📊 Parsed {len(messages)} messages")
    print(f"🔍 Filtered to {len(filtered_messages)} messages")

    filter_and_insert_messages(filtered_messages)
    print("✅ Messages inserted into database")


def run_llm():
    """Run the LLM extractor."""
    from src.llm import extract_opportunities
    print("🤖 Starting LLM opportunity extractor...")
    extract_opportunities()
    print("✅ Opportunity extraction completed")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Conversational Data Analysis System',
        epilog='To launch the web UI, run: streamlit run src/gui/streamlit_app.py'
    )
    parser.add_argument('--parse', action='store_true', help='Parse chat file and save to database')
    parser.add_argument('--llm', action='store_true', help='Run LLM extractor')

    args = parser.parse_args()

    if args.parse:
        run_parser()
    elif args.llm:
        run_llm()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()