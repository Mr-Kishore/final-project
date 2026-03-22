import argparse
from pathlib import Path
from src.core import parse_chat, is_system_message, save_messages_to_json

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"


def run_parser():
    """Parse the chat file and save to chat.json only — no DB insertion."""
    print("Starting Conversational Data Analysis System...")
    print("Parsing chat conversation...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    input_file = DATA_DIR / "chat.txt"

    messages = parse_chat(str(input_file))
    if messages is None:
        print(f"Parsing failed. Ensure input exists at: {input_file}")
        return

    filtered_messages = [msg for msg in messages if not is_system_message(msg.get("text", ""))]
    save_messages_to_json(filtered_messages, str(DATA_DIR / "chat.json"))

    print(f"Total parsed: {len(messages)} messages")
    print(f"After filtering: {len(filtered_messages)} messages")
    print(f"Saved to chat.json")
    print(f"Run --llm next to extract opportunities and save to database.")


def run_llm():
    """Run LLM extractor — saves opportunities to DB + job_details.json."""
    from src.llm import extract_opportunities
    print("Starting LLM opportunity extractor...")
    results = extract_opportunities(str(DATA_DIR / "chat.json"))
    if results:
        print(f"Extracted {len(results)} opportunities — saved to database & job_details.json")
    else:
        print("No opportunities extracted.")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Conversational Data Analysis System',
        epilog='To launch the web UI: streamlit run src/gui/streamlit_app.py'
    )
    parser.add_argument('--parse', action='store_true', help='Parse chat file and save to chat.json')
    parser.add_argument('--llm', action='store_true', help='Run LLM extractor and save to database')

    args = parser.parse_args()

    if args.parse:
        run_parser()
    elif args.llm:
        run_llm()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()