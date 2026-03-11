# Conversational Data Analysis System Architecture

## Project Structure

```
conversational_data_analysis/
├── main.py                 # Main entry point with CLI interface
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (copy from config/.env.example)
├── README.md              # Project documentation
├── src/                   # Source code
│   ├── __init__.py
│   ├── core/              # Core parsing logic
│   │   ├── __init__.py
│   │   └── parser.py      # Chat conversation parsing
│   ├── database/          # Database layer
│   │   ├── __init__.py
│   │   ├── db_integration.py  # Database operations
│   │   └── models.py      # Database schemas
│   ├── gui/               # Desktop GUI
│   │   ├── __init__.py
│   │   └── app.py         # GUI application
│   ├── llm/               # LLM integration
│   │   ├── __init__.py
│   │   └── extractor.py   # Opportunity extraction
│   └── utils/             # Utility functions
│       └── __init__.py
├── config/                # Configuration files
│   ├── database.sql       # Database schema
│   └── .env.example       # Environment variables template
├── scripts/               # Standalone scripts
│   ├── run_parser.py      # Run parser independently
│   └── run_llm.py         # Run LLM extractor independently
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_parser.py     # Parser tests
├── data/                  # Data files (place chat.txt here)
│   ├── chat.txt           # Input chat export
│   ├── chat.json          # Parsed messages
│   └── job_details.json   # Extracted opportunities
└── docs/                  # Documentation
    └── ARCHITECTURE.md    # This file
```

## Data Flow

1. **Input Processing**
   - `chat.txt` → `src/core/parser.py` → Structured messages

2. **Filtering**
   - Raw messages → System message filter → Clean messages

3. **Storage**
   - Clean messages → `src/database/db_integration.py` → SQLite database

4. **Extraction**
   - Clean messages → `src/llm/extractor.py` → `job_details.json`

5. **Interface**
   - `src/gui/streamlit_app.py` provides Streamlit interface
   - `main.py` provides CLI interface

## Components

### Core (`src/core/`)
- **parser.py**: Handles chat conversation parsing with regex pattern matching
- Supports multi-line messages and date parsing
- Filters system messages automatically

### Database (`src/database/`)
- **db_integration.py**: SQLite database connection and operations
- **models.py**: Database schema definitions
- Automatic database creation and indexing
- No external database server required

### LLM (`src/llm/`)
- **extractor.py**: Uses Ollama for opportunity extraction
- Processes messages in batches
- Handles JSON parsing errors gracefully

### GUI (`src/gui/`)
- **streamlit_app.py**: Streamlit-based web application
- File management and process controls
- Real-time output display

## Configuration

- Environment variables loaded from `.env` (optional for SQLite)
- SQLite database created automatically at `data/conversational_analysis.db`
- LLM configuration via Ollama (optional)

## Development Guidelines

- Follow Python PEP 8 style
- Use type hints where appropriate
- Add docstrings to all functions
- Write tests for new features
- Keep modules focused and single-purpose
