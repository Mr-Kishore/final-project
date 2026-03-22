#!/usr/bin/env python3
"""
Standalone script to run the Conversational Data Analysis System LLM extractor.
"""

import sys
import os
import json
from pathlib import Path

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

from src.llm.extractor import extract_opportunities


def main():
    """Run the LLM extractor."""
    print("Starting Conversational Data Analysis System LLM extractor...")
    
    try:
        opportunities = extract_opportunities()
        if not opportunities:
            print("No opportunities extracted.")
            return

        output_json = DATA_DIR / "job_details.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(opportunities, f, indent=2, ensure_ascii=False)

        print("LLM extraction completed successfully!")
        print(f"Check {output_json} for extracted opportunities")
    except Exception as e:
        print(f"Error during LLM extraction: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
