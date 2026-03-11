import contextlib
import io
import json
import sys
from pathlib import Path
import sqlite3
import pandas as pd

import streamlit as st

# Allow running via `streamlit run` without package context.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import core  # noqa: E402
from src import llm  # noqa: E402
from src.database import DatabaseManager  # noqa: E402


DATA_DIR = PROJECT_ROOT / "data"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _log(message):
    st.session_state.setdefault("logs", [])
    st.session_state["logs"].append(message)


def _render_logs():
    logs = st.session_state.get("logs", [])
    if not logs:
        st.info("No logs yet.")
        return
    st.text_area("Logs", value="\n".join(logs), height=240)


def _capture_output(fn, *args, **kwargs):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        result = fn(*args, **kwargs)
    return result, buffer.getvalue()


def _list_files(suffix):
    _ensure_data_dir()
    return sorted([p.name for p in DATA_DIR.glob(f"*{suffix}") if p.is_file()])


def _run_parse_and_db(input_file):
    """Single action to parse chat file and save to database"""
    _ensure_data_dir()
    input_path = DATA_DIR / input_file
    if not input_path.exists():
        _log(f"Missing input file: {input_path}")
        return

    def _pipeline():
        messages = core.parse_chat(input_file=str(input_path))
        if messages is None:
            print("❌ Parsing failed.")
            return
        if not messages:
            print("❌ No messages found.")
            return

        filtered_messages = [msg for msg in messages if not core.is_system_message(msg.get("text", ""))]
        
        # Save to database
        db = DatabaseManager()
        db.insert_messages(filtered_messages)
        
        print(f"✅ Parse and DB insert complete. Total messages: {len(messages)}, Filtered: {len(filtered_messages)}")
        print(f"📊 Messages saved to database: {db.db_path}")

    _, output = _capture_output(_pipeline)
    if output:
        for line in output.strip().splitlines():
            _log(line)


def _display_database_table():
    """Display database table contents"""
    try:
        db = DatabaseManager()
        if not db.connect():
            st.error("❌ Cannot connect to database")
            return
        
        # Query all messages
        query = "SELECT date, time, author, content FROM messages ORDER BY date, time"
        df = pd.read_sql_query(query, db.connection)
        
        if df.empty:
            st.info("📭 No messages found in database")
            return
        
        # Display statistics
        st.subheader("📊 Database Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Messages", len(df))
        with col2:
            st.metric("Unique Authors", df['author'].nunique())
        with col3:
            st.metric("Date Range", f"{df['date'].min()} - {df['date'].max()}")
        
        # Display table
        st.subheader("💬 Messages")
        
        # Add filters
        col1, col2 = st.columns(2)
        with col1:
            selected_author = st.selectbox("Filter by Author", options=["All"] + sorted(df['author'].unique()))
        with col2:
            search_term = st.text_input("Search in Content")
        
        # Apply filters
        filtered_df = df.copy()
        if selected_author != "All":
            filtered_df = filtered_df[filtered_df['author'] == selected_author]
        if search_term:
            filtered_df = filtered_df[filtered_df['content'].str.contains(search_term, case=False, na=False)]
        
        # Display filtered data
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Download option
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="chat_data.csv",
            mime="text/csv"
        )
        
        db.close()
        
    except Exception as e:
        st.error(f"❌ Error accessing database: {e}")


def _run_llm(input_json):
    _ensure_data_dir()
    input_path = DATA_DIR / input_json
    if not input_path.exists():
        _log(f"Missing input JSON: {input_path}")
        return

    def _pipeline():
        training_info = llm.extract_opportunities(str(input_path))
        if not training_info:
            print("❌ No training/job opportunities extracted.")
            return

        output_file = DATA_DIR / "job_details.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(training_info, f, indent=2, ensure_ascii=False)

        print(f"✅ LLM extraction complete. Records: {len(training_info)}")
        for idx, info in enumerate(training_info[:3], start=1):
            domain = info.get("domain/topic", "Unknown")
            location = info.get("location", "Unknown")
            contact = info.get("contact", "Unknown")
            print(f"{idx}. {domain} | {location} | {contact}")

    _, output = _capture_output(_pipeline)
    if output:
        for line in output.strip().splitlines():
            _log(line)


def main():
    st.set_page_config(page_title="Conversational Data Analysis System", layout="wide")
    st.title("🔍 Conversational Data Analysis System")

    _ensure_data_dir()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📂 Data Processing", "🗄️ Database Viewer", "🤖 LLM Extraction"])
    
    with tab1:
        st.caption("📁 Put your `chat.txt` into `data/` folder or upload below.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📥 Input Files")
            txt_files = _list_files(".txt")
            json_files = _list_files(".json")

            selected_text = st.selectbox("Select Chat File (.txt)", options=txt_files or ["<none>"])
            selected_json = st.selectbox("Select JSON File (.json)", options=json_files or ["<none>"])

            uploaded = st.file_uploader("📤 Upload .txt or .json", type=["txt", "json"])
            if uploaded:
                dest = DATA_DIR / uploaded.name
                dest.write_bytes(uploaded.getbuffer())
                _log(f"✅ Uploaded file: {dest.name}")
                st.success(f"✅ Uploaded {dest.name}")
                # Refresh file lists
                txt_files = _list_files(".txt")
                json_files = _list_files(".json")

        with col2:
            st.subheader("⚡ Actions")
            
            # Single action for parse and DB
            if st.button("🚀 Parse Chat & Save to Database", type="primary", use_container_width=True):
                if selected_text == "<none>":
                    st.error("❌ Please select a chat file first")
                else:
                    with st.spinner("🔄 Processing..."):
                        _run_parse_and_db(selected_text)
            
            st.markdown("---")
            
            # LLM extraction
            if st.button("🤖 Run LLM Extraction", use_container_width=True):
                if selected_json == "<none>":
                    st.error("❌ Please select a JSON file first")
                    st.info("💡 Tip: Run the parser first to generate chat.json")
                else:
                    with st.spinner("🤖 Extracting opportunities..."):
                        _run_llm(selected_json)
        
        # Output files section
        st.subheader("📤 Output Files")
        output_files = sorted([p.name for p in DATA_DIR.iterdir() if p.suffix in {".txt", ".json"}])
        selected_output = st.selectbox("View Output File", options=output_files or ["<none>"])
        if selected_output != "<none>":
            content = (DATA_DIR / selected_output).read_text(encoding="utf-8", errors="ignore")
            st.text_area("📄 File Content", value=content, height=200)
    
    with tab2:
        st.subheader("🗄️ Database Content Viewer")
        st.caption("View and filter messages stored in the database")
        _display_database_table()
    
    with tab3:
        st.subheader("🤖 LLM Opportunity Extraction")
        st.caption("Extract training and job opportunities from chat data")
        
        # File selection for LLM
        json_files = _list_files(".json")
        selected_llm_json = st.selectbox("Select JSON for LLM Analysis", options=json_files or ["<none>"])
        
        if st.button("🔍 Extract Opportunities", type="secondary"):
            if selected_llm_json == "<none>":
                st.error("❌ Please select a JSON file first")
            else:
                with st.spinner("🤖 Running LLM analysis..."):
                    _run_llm(selected_llm_json)
        
        # Display extracted opportunities if available
        job_details_path = DATA_DIR / "job_details.json"
        if job_details_path.exists():
            st.subheader("📋 Extracted Opportunities")
            with open(job_details_path, "r", encoding="utf-8") as f:
                opportunities = json.load(f)
            
            if opportunities:
                for i, opp in enumerate(opportunities, 1):
                    with st.expander(f"🎯 Opportunity {i}: {opp.get('domain/topic', 'Unknown Domain')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📍 Location:** {opp.get('location', 'Unknown')}")
                            st.write(f"**👥 Contact:** {opp.get('contact', 'Unknown')}")
                        with col2:
                            st.write(f"**🏷️ Tags:** {', '.join(opp.get('tags', []))}")
                            st.write(f"**📅 Date:** {opp.get('date', 'Unknown')}")
                        
                        if 'description' in opp:
                            st.write(f"**📝 Description:** {opp['description']}")
            else:
                st.info("📭 No opportunities extracted yet")
    
    # Global logs section
    st.markdown("---")
    st.subheader("📋 System Logs")
    _render_logs()


main()
