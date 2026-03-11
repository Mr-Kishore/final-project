# Conversational Data Analysis System

Parse exported chat conversations, filter system noise, store messages in SQLite, and optionally extract training/job opportunities using a local LLM (Ollama).

## 🏗️ Professional Project Structure

```
conversational_data_analysis/
├── main.py                 # Main entry point with CLI interface
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (copy from config/.env.example)
├── README.md              # This file
├── src/                   # Source code
│   ├── core/              # Core parsing logic
│   │   └── parser.py      # Chat conversation parsing
│   ├── database/          # Database layer
│   │   ├── db_integration.py  # Database operations
│   │   └── models.py      # Database schemas
│   ├── gui/               # Desktop GUI
│   │   └── app.py         # GUI application
│   ├── llm/               # LLM integration
│   │   └── extractor.py   # Opportunity extraction
│   └── utils/             # Utility functions
├── config/                # Configuration files
│   ├── database.sql       # Database schema
│   └── .env.example       # Environment variables template
├── scripts/               # Standalone scripts
│   ├── run_parser.py      # Run parser independently
│   └── run_llm.py         # Run LLM extractor independently
├── tests/                 # Test suite
│   └── test_parser.py     # Parser tests
├── data/                  # Data files (place chat.txt here)
└── docs/                  # Documentation
    └── ARCHITECTURE.md    # Detailed architecture
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
source .venv/bin/actipython -m venv .venv
vate  # Linux/Mac
# or
source .venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp config/.env.example .env
# Edit .env if needed (SQLite works out of the box)
```

### 2. Run the Application

**Option A: Streamlit UI**
```bash
python main.py --gui
# or directly
streamlit run src/gui/streamlit_app.py
```

**Option B: Command Line**
```bash
# Parse chat and store in database
python main.py --parse

# Extract opportunities with LLM
python main.py --llm
```

**Option C: Standalone Scripts**
```bash
# Run parser only
python scripts/run_parser.py

# Run LLM extractor only
python scripts/run_llm.py
```

## 📋 Prerequisites

- Python `3.9+`
- `pip`
- Ollama installed and running locally (for LLM features)
- **No database server needed!** Uses SQLite (built into Python)

## 🔧 Configuration

Create a `.env` file in the project root (copy from `config/.env.example`):

```env
# SQLite Database Configuration
DB_PATH=data/conversational_analysis.db

# Ollama configuration
OLLAMA_MODEL=llama3.2:3b
OLLAMA_HOST=http://localhost:11434
```

## 📁 Input/Output Files

- **Input**: Place your chat export as `data/chat.txt`
- **Outputs**: 
  - `data/chat.json` - Parsed and filtered messages
  - `data/job_details.json` - Extracted opportunities

## 🎯 Features

1. **Smart Parsing**: Handles chat export format with multi-line messages
2. **System Message Filtering**: Automatically removes group events, encryption notices, etc.
3. **Database Integration**: Batch insertion into SQLite with proper schema
4. **LLM Extraction**: Uses local Ollama models to extract job/training opportunities
5. **Streamlit UI**: Web UI with file management and pipeline controls
6. **CLI Support**: Command-line interface for automation
7. **Professional Structure**: Clean, maintainable codebase following Python best practices

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
# or
python -m unittest tests.test_parser
```

## 📊 Database Schema

Messages are stored in SQLite database at `data/conversational_analysis.db`:
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `date` (TEXT) - Format: DD/MM/YY
- `time` (TEXT) - Format: HH:MM:SS AM/PM
- `author` (TEXT)
- `content` (TEXT)
- `created_at` (TIMESTAMP) - When record was inserted

See `config/database.sql` for complete schema.

## 🔍 Input Format

Expected chat line format:
```
[DD/MM/YY, HH:MM:SS AM/PM] Author: Message text
```

Example:
```
[09/10/24, 09:30:12 PM] John: Training starts tomorrow in Hyderabad
```

## 🤖 LLM Integration

Uses Ollama with `llama3.2:3b` model by default to extract:
- Domain/Topic
- Location
- Start Date
- Duration
- Mode (online/offline)
- Pay
- Contact Information

## 🐛 Troubleshooting

- **Environment variables not loading**: Ensure `.env` exists in project root
- **Database errors**: SQLite creates database automatically, no setup needed
- **Chat file not found**: Place export as `data/chat.txt`
- **LLM errors**: Ensure Ollama is running and model is available

## 📚 Documentation

- `docs/ARCHITECTURE.md` - Detailed architecture and design decisions
- Inline docstrings in all modules
- Type hints throughout the codebase

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Keep modules focused and single-purpose
