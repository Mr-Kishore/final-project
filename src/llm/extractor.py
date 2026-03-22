import ollama
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def chat_with_llm(prompt, model='llama3.2:1b'):
    """Simple function to chat with Ollama LLM"""
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response['response']
    except Exception as e:
        return f"Error: {e}"


def extract_training_info_from_chat(chat_json_path):
    """
    Extracts training/job posting information from chat.json using LLM,
    then saves results to both job_details.json and the SQLite database.
    """
    try:
        with open(chat_json_path, 'r', encoding='utf-8') as f:
            messages = json.load(f)

        print(f"Analyzing {len(messages)} messages for training opportunities...")

        extracted_info = []

        batch_size = 5
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            print(f"Processing batch {i // batch_size + 1}...")

            batch_text = "\n\n".join([
                f"Message {j + 1}: {msg['text']}" for j, msg in enumerate(batch)
            ])

            prompt = f"""
You are an expert at extracting training and job posting information from text messages.

Analyze the following messages and extract training/job opportunities. For each relevant message that contains training/job posting information, extract:

1. "domain/topic": The training domain/subject (e.g., "Aptitude", "Verbal", "Mathematics", etc.)
2. "location": The location/city mentioned
3. "start_date": Start date if mentioned (null if not mentioned)
4. "duration": Duration of the training (null if not mentioned)
5. "mode": "online" or "on-site" or "offline"
6. "pay": Salary/payment information (null if not mentioned)
7. "contact": Contact phone/email mentioned

Only extract information for messages that clearly contain training or job posting detail. If any fields are missing then just mark it as null. Skip regular conversation messages.

Messages to analyze:
{batch_text}

Return a JSON array of objects, where each object represents one training opportunity. Only include messages that have training/job posting content. If a field is not mentioned, use null.

Example format:
[
  {{
    "domain/topic": "Aptitude",
    "location": "Hyderabad",
    "start_date": "9th October",
    "duration": "3 Days",
    "mode": "offline",
    "pay": "50K",
    "contact": "98480 62116"
  }}
]

Return only valid JSON array, no explanations or additional text.
"""
            response = chat_with_llm(prompt)

            try:
                batch_info = json.loads(response.strip())
                if isinstance(batch_info, list):
                    extracted_info.extend(batch_info)
                    print(f"   Extracted {len(batch_info)} opportunities from this batch")
                else:
                    print(f"   Warning: Unexpected response format from LLM")
            except json.JSONDecodeError:
                print(f"   Error: Invalid JSON response. Raw: {response[:200]}...")

        # Deduplicate
        seen = set()
        unique_info = []
        for item in extracted_info:
            key = f"{item.get('domain/topic', '')}-{item.get('location', '')}-{item.get('contact', '')}"
            if key not in seen and item.get('domain/topic'):
                seen.add(key)
                unique_info.append(item)

        # Save to job_details.json
        data_dir = Path(chat_json_path).parent
        output_file = data_dir / "job_details.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_info, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(unique_info)} opportunities to job_details.json")

        # Save to SQLite database
        try:
            from src.database import DatabaseManager
            db = DatabaseManager(db_path=str(data_dir / "conversational_analysis.db"))
            if db.connect():
                db.create_table_if_not_exists()
                inserted = db.insert_opportunities(unique_info)
                db.get_table_stats()
                db.close()
                print(f"✅ Saved {inserted} opportunities to database")
        except Exception as e:
            print(f"⚠️ Could not save to database: {e}")

        return unique_info

    except FileNotFoundError:
        print(f"Error: {chat_json_path} not found")
        return []
    except Exception as e:
        print(f"Error processing chat: {e}")
        return []


if __name__ == "__main__":
    training_info = extract_training_info_from_chat("data/chat.json")
    if training_info:
        print(f"\nSuccessfully extracted {len(training_info)} training opportunities!")
        for i, info in enumerate(training_info[:3]):
            print(f"{i+1}. {info.get('domain/topic')} - {info.get('location')} - {info.get('contact')}")
    else:
        print("No training opportunities were extracted from the chat.")