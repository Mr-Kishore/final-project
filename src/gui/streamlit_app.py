import json
import sys
from pathlib import Path
import pandas as pd

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import core                    # noqa: E402
from src import llm                     # noqa: E402
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


def _list_files(suffix):
    _ensure_data_dir()
    return sorted([p.name for p in DATA_DIR.glob(f"*{suffix}") if p.is_file()])


# ── Stage 1: Parse only ───────────────────────────────────────────────────────
def _run_parse(input_file):
    """Parse chat.txt → chat.json only. No database interaction."""
    _ensure_data_dir()
    input_path = DATA_DIR / input_file

    if not input_path.exists():
        st.error(f"❌ File not found: {input_path}")
        _log(f"❌ Missing file: {input_path}")
        return

    try:
        messages = core.parse_chat(input_file=str(input_path))
        if messages is None:
            st.error("❌ Parsing failed. Check the chat file format.")
            _log("❌ Parsing failed.")
            return
        if not messages:
            st.error("❌ No messages found in the file.")
            _log("❌ No messages found.")
            return

        filtered_messages = [
            msg for msg in messages
            if not core.is_system_message(msg.get("text", ""))
        ]

        json_path = str(DATA_DIR / "chat.json")
        core.save_messages_to_json(filtered_messages, json_path)

        msg = (
            f"✅ Parsing complete! "
            f"Total: {len(messages)} | "
            f"After filtering: {len(filtered_messages)} | "
            f"Saved → chat.json"
        )
        st.success(msg)
        _log(msg)

    except Exception as e:
        st.error(f"❌ Error during parsing: {e}")
        _log(f"❌ Error: {e}")


# ── Stage 2: LLM extract → store in DB ───────────────────────────────────────
def _run_llm(input_json):
    """Run LLM extraction on chat.json and store results in the database."""
    _ensure_data_dir()
    input_path = DATA_DIR / input_json

    if not input_path.exists():
        st.error(f"❌ File not found: {input_path}")
        _log(f"❌ Missing JSON: {input_path}")
        return

    try:
        opportunities = llm.extract_opportunities(str(input_path))

        if not opportunities:
            st.warning("⚠️ No training/job opportunities were extracted.")
            _log("⚠️ No opportunities extracted.")
            return

        # extractor already saves job_details.json and inserts into DB
        msg = f"✅ Extracted {len(opportunities)} opportunities → saved to job_details.json & database"
        st.success(msg)
        _log(msg)

        for idx, info in enumerate(opportunities[:3], start=1):
            line = (
                f"{idx}. {info.get('domain/topic', '?')} | "
                f"{info.get('location', '?')} | "
                f"{info.get('contact', '?')}"
            )
            _log(line)

    except Exception as e:
        st.error(f"❌ Error during LLM extraction: {e}")
        _log(f"❌ Error: {e}")


# ── Database viewer ───────────────────────────────────────────────────────────
def _display_database_table():
    """Display the opportunities table from the database."""
    try:
        db = DatabaseManager(db_path=str(DATA_DIR / "conversational_analysis.db"))
        if not db.connect():
            st.error("❌ Cannot connect to database")
            return

        db.create_table_if_not_exists()

        query = "SELECT domain_topic, location, start_date, duration, mode, pay, contact, created_at FROM opportunities ORDER BY created_at DESC"
        df = pd.read_sql_query(query, db.connection)
        db.close()

        if df.empty:
            st.info("📭 No opportunities in database yet. Run LLM Extraction first.")
            return

        # Stats
        st.subheader("📊 Database Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Opportunities", len(df))
        with col2:
            st.metric("Unique Domains", df["domain_topic"].nunique())
        with col3:
            st.metric("Unique Locations", df["location"].nunique())

        # Filters
        st.subheader("🎯 Extracted Opportunities")
        col1, col2 = st.columns(2)
        with col1:
            domains = ["All"] + sorted(df["domain_topic"].dropna().unique().tolist())
            selected_domain = st.selectbox("Filter by Domain", options=domains)
        with col2:
            search_term = st.text_input("Search (domain / location / contact)")

        filtered_df = df.copy()
        if selected_domain != "All":
            filtered_df = filtered_df[filtered_df["domain_topic"] == selected_domain]
        if search_term:
            mask = (
                filtered_df["domain_topic"].str.contains(search_term, case=False, na=False)
                | filtered_df["location"].str.contains(search_term, case=False, na=False)
                | filtered_df["contact"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, height=400)

        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="opportunities.csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"❌ Error accessing database: {e}")


# ── Main app ──────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Conversational Data Analysis System", layout="wide")
    st.title("🔍 Conversational Data Analysis System")

    _ensure_data_dir()

    tab1, tab2, tab3 = st.tabs(["📂 Data Processing", "🗄️ Database Viewer", "🤖 LLM Extraction"])

    # ── Tab 1: Data Processing ────────────────────────────────────────────────
    with tab1:
        st.caption("📁 Place your `chat.txt` in the `data/` folder or upload below.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📥 Input Files")
            txt_files  = _list_files(".txt")
            json_files = _list_files(".json")

            selected_text = st.selectbox("Select Chat File (.txt)", options=txt_files or ["<none>"])
            selected_json = st.selectbox("Select JSON File (.json)", options=json_files or ["<none>"])

            uploaded = st.file_uploader("📤 Upload .txt or .json", type=["txt", "json"])
            if uploaded:
                dest = DATA_DIR / uploaded.name
                dest.write_bytes(uploaded.getbuffer())
                _log(f"✅ Uploaded: {dest.name}")
                st.success(f"✅ Uploaded {dest.name}")

        with col2:
            st.subheader("⚡ Actions")

            st.markdown("**Step 1 — Parse**")
            if st.button("📄 Parse Chat File", type="primary"):
                if selected_text == "<none>":
                    st.error("❌ Please select a .txt chat file first")
                else:
                    with st.spinner("🔄 Parsing..."):
                        _run_parse(selected_text)

            st.markdown("---")

            st.markdown("**Step 2 — Extract & Store**")
            if st.button("🤖 Run LLM Extraction → Save to DB"):
                if selected_json == "<none>":
                    st.error("❌ Please select a JSON file first")
                    st.info("💡 Run Step 1 first to generate chat.json")
                else:
                    with st.spinner("🤖 Extracting and storing opportunities..."):
                        _run_llm(selected_json)

        # Output preview
        st.subheader("📤 Output Files")
        output_files = sorted([p.name for p in DATA_DIR.iterdir() if p.suffix in {".txt", ".json"}])
        selected_output = st.selectbox("View Output File", options=output_files or ["<none>"])
        if selected_output != "<none>":
            file_path = DATA_DIR / selected_output
            file_size = file_path.stat().st_size
            st.caption(f"File size: {file_size / 1024:.1f} KB")
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            preview = content[:5000]
            if len(content) > 5000:
                preview += f"\n\n... (truncated — {len(content):,} total characters)"
            st.text_area("📄 File Content (Preview)", value=preview, height=200)
            st.download_button(
                label=f"📥 Download {selected_output}",
                data=content,
                file_name=selected_output,
                mime="text/plain",
            )

    # ── Tab 2: Database Viewer ────────────────────────────────────────────────
    with tab2:
        st.subheader("🗄️ Opportunities Database Viewer")
        st.caption("Shows structured opportunities extracted by the LLM and stored in SQLite")
        _display_database_table()

    # ── Tab 3: LLM Extraction ─────────────────────────────────────────────────
    with tab3:
        st.subheader("🤖 LLM Opportunity Extraction")
        st.caption("Extract training and job opportunities from parsed chat data")

        json_files = _list_files(".json")
        selected_llm_json = st.selectbox(
            "Select JSON for LLM Analysis", options=json_files or ["<none>"]
        )

        if st.button("🔍 Extract Opportunities", type="secondary"):
            if selected_llm_json == "<none>":
                st.error("❌ Please select a JSON file first")
            else:
                with st.spinner("🤖 Running LLM analysis and saving to database..."):
                    _run_llm(selected_llm_json)

        # Display job_details.json if available
        job_details_path = DATA_DIR / "job_details.json"
        if job_details_path.exists():
            st.subheader("📋 Extracted Opportunities")
            with open(job_details_path, "r", encoding="utf-8") as f:
                opportunities = json.load(f)

            if opportunities:
                for i, opp in enumerate(opportunities, 1):
                    with st.expander(f"🎯 Opportunity {i}: {opp.get('domain/topic', 'Unknown')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**📍 Location:** {opp.get('location', 'N/A')}")
                            st.write(f"**👥 Contact:** {opp.get('contact', 'N/A')}")
                            st.write(f"**📅 Start Date:** {opp.get('start_date', 'N/A')}")
                        with col2:
                            st.write(f"**⏱️ Duration:** {opp.get('duration', 'N/A')}")
                            st.write(f"**🖥️ Mode:** {opp.get('mode', 'N/A')}")
                            st.write(f"**💰 Pay:** {opp.get('pay', 'N/A')}")
            else:
                st.info("📭 No opportunities extracted yet")

    # ── Logs ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 System Logs")
    _render_logs()


main()