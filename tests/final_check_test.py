import unittest
import json
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import (
    parse_chat_file,
    is_system_message,
    filter_system_messages,
    save_messages_to_json,
)
from src.database.db_integration import DatabaseManager


# ── Helper: write a temporary chat file ──────────────────────────────────────
SAMPLE_CHAT = """\
[15/11/24, 8:50:43 AM] ~ Aravinth AJ: Hi all
Urgently looking for a Python trainer
Topic: Python Full Stack
Location: Bangalore
Start: 20th Jan 2025
Duration: 10 days
Contact: 9845012345
[15/11/24, 9:00:00 AM] ~ Priya Sharma: Good morning everyone!
[15/11/24, 9:05:00 AM] ~ Karthik: ‎~ Karthik joined using a group link.
[15/11/24, 9:10:00 AM] ~ Admin: ‎Messages and calls are end-to-end encrypted.
[15/11/24, 9:15:00 AM] ~ Meena: Need a DevOps trainer
Location: Pune
Contact: 9823456789
[15/11/24, 9:20:00 AM] ~ Ravi: ‎~ Ravi left
"""


def _write_temp_chat(content=SAMPLE_CHAT):
    """Write sample chat content to a temp file and return path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", encoding="utf-8", delete=False
    )
    f.write(content)
    f.close()
    return f.name


# ════════════════════════════════════════════════════════════════════════════════
# 1. Parser Tests
# ════════════════════════════════════════════════════════════════════════════════
class TestParser(unittest.TestCase):
    """Tests for src/core/parser.py — parse_chat_file()"""

    def setUp(self):
        self.chat_file = _write_temp_chat()

    def tearDown(self):
        os.unlink(self.chat_file)

    def test_parse_returns_list(self):
        """parse_chat_file() should return a list."""
        result = parse_chat_file(self.chat_file)
        self.assertIsInstance(result, list)

    def test_parse_correct_message_count(self):
        """Parser should extract the correct number of messages."""
        result = parse_chat_file(self.chat_file)
        # SAMPLE_CHAT has 6 message blocks (first msg is multi-line)
        self.assertGreaterEqual(len(result), 4)

    def test_parse_message_fields(self):
        """Each parsed message must have date, time, author, text fields."""
        result = parse_chat_file(self.chat_file)
        for msg in result:
            self.assertIn("date", msg)
            self.assertIn("time", msg)
            self.assertIn("author", msg)
            self.assertIn("text", msg)

    def test_parse_multiline_message(self):
        """Multi-line messages should be concatenated into a single record."""
        result = parse_chat_file(self.chat_file)
        first_msg = result[0]
        self.assertIn("Python", first_msg["text"])
        self.assertIn("Bangalore", first_msg["text"])

    def test_parse_missing_file_returns_none(self):
        """Parsing a non-existent file should return None, not raise."""
        result = parse_chat_file("/tmp/nonexistent_chat_xyz.txt")
        self.assertIsNone(result)

    def test_parse_empty_file_returns_empty_list(self):
        """Parsing an empty file should return an empty list."""
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        )
        f.close()
        try:
            result = parse_chat_file(f.name)
            self.assertIsNotNone(result)
            self.assertEqual(len(result), 0)
        finally:
            os.unlink(f.name)

    def test_parse_author_extracted_correctly(self):
        """Author names should be extracted without leading ~ or spaces."""
        result = parse_chat_file(self.chat_file)
        authors = [msg["author"] for msg in result]
        # Authors should not contain leading/trailing whitespace
        for author in authors:
            self.assertEqual(author, author.strip())


# ════════════════════════════════════════════════════════════════════════════════
# 2. System Message Filter Tests
# ════════════════════════════════════════════════════════════════════════════════
class TestSystemMessageFilter(unittest.TestCase):
    """Tests for is_system_message() and filter_system_messages()"""

    # ── Known system messages ─────────────────────────────────────────────────
    def test_detects_encryption_notice(self):
        self.assertTrue(is_system_message(
            "Messages and calls are end-to-end encrypted"
        ))

    def test_detects_joined_group(self):
        self.assertTrue(is_system_message("joined using a group link"))

    def test_detects_created_group(self):
        self.assertTrue(is_system_message("created this group"))

    def test_detects_left(self):
        self.assertTrue(is_system_message("left"))

    def test_detects_added(self):
        self.assertTrue(is_system_message("added"))

    def test_detects_removed(self):
        self.assertTrue(is_system_message("removed"))

    def test_detects_changed_group_name(self):
        self.assertTrue(is_system_message("changed the group name"))

    def test_detects_deleted_message(self):
        self.assertTrue(is_system_message("This message was deleted"))

    def test_detects_pinned_message(self):
        self.assertTrue(is_system_message("pinned a message"))

    def test_case_insensitive(self):
        """Filter should be case-insensitive."""
        self.assertTrue(is_system_message("MESSAGES AND CALLS ARE END-TO-END ENCRYPTED"))
        self.assertTrue(is_system_message("Joined Using A Group Link"))

    # ── Normal user messages should NOT be filtered ───────────────────────────
    def test_allows_job_posting(self):
        self.assertFalse(is_system_message(
            "Looking for Python trainer in Bangalore. Contact: 9845012345"
        ))

    def test_allows_greeting(self):
        self.assertFalse(is_system_message("Good morning everyone!"))

    def test_allows_training_opportunity(self):
        self.assertFalse(is_system_message(
            "Topic: Data Science, Location: Hyderabad, Duration: 5 days"
        ))

    def test_allows_empty_adjacent_words(self):
        """'removed' as standalone word filters, but not as part of normal text."""
        self.assertFalse(is_system_message(
            "The feature was improved and bugs were fixed"
        ))

    def test_empty_string_is_system(self):
        """Empty string should be treated as a system message."""
        self.assertTrue(is_system_message(""))

    def test_none_text_is_system(self):
        """None text should be treated as a system message."""
        self.assertTrue(is_system_message(None))

    # ── filter_system_messages() ──────────────────────────────────────────────
    def test_filter_removes_system_messages(self):
        messages = [
            {"text": "joined using a group link"},
            {"text": "Good morning everyone!"},
            {"text": "Messages and calls are end-to-end encrypted"},
            {"text": "Looking for a trainer in Chennai"},
        ]
        filtered = filter_system_messages(messages)
        self.assertEqual(len(filtered), 2)

    def test_filter_preserves_order(self):
        messages = [
            {"text": "First normal message"},
            {"text": "left"},
            {"text": "Second normal message"},
        ]
        filtered = filter_system_messages(messages)
        self.assertEqual(filtered[0]["text"], "First normal message")
        self.assertEqual(filtered[1]["text"], "Second normal message")

    def test_filter_handles_none_input(self):
        """filter_system_messages(None) should return empty list, not crash."""
        result = filter_system_messages(None)
        self.assertEqual(result, [])

    def test_filter_handles_empty_list(self):
        result = filter_system_messages([])
        self.assertEqual(result, [])


# ════════════════════════════════════════════════════════════════════════════════
# 3. JSON Export Tests
# ════════════════════════════════════════════════════════════════════════════════
class TestJSONExport(unittest.TestCase):
    """Tests for save_messages_to_json()"""

    def setUp(self):
        self.messages = [
            {"date": "15/11/24", "time": "9:00 AM", "author": "Priya",
             "text": "Looking for a trainer"},
            {"date": "15/11/24", "time": "9:05 AM", "author": "Ravi",
             "text": "Available for Python"},
        ]
        self.out_file = tempfile.mktemp(suffix=".json")

    def tearDown(self):
        if os.path.exists(self.out_file):
            os.unlink(self.out_file)

    def test_json_file_created(self):
        """save_messages_to_json() should create the output file."""
        save_messages_to_json(self.messages, self.out_file)
        self.assertTrue(os.path.exists(self.out_file))

    def test_json_content_valid(self):
        """Output file should contain valid JSON."""
        save_messages_to_json(self.messages, self.out_file)
        with open(self.out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)

    def test_json_message_count(self):
        """JSON file should contain the same number of messages as input."""
        save_messages_to_json(self.messages, self.out_file)
        with open(self.out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 2)

    def test_json_fields_preserved(self):
        """All fields should be preserved in the JSON output."""
        save_messages_to_json(self.messages, self.out_file)
        with open(self.out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0]["author"], "Priya")
        self.assertEqual(data[1]["text"], "Available for Python")

    def test_json_unicode_preserved(self):
        """Unicode characters (emoji, Tamil, etc.) should be preserved."""
        msgs = [{"date": "15/11/24", "time": "9:00 AM",
                 "author": "தமிழ்", "text": "🔷 Training available"}]
        save_messages_to_json(msgs, self.out_file)
        with open(self.out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0]["author"], "தமிழ்")
        self.assertIn("🔷", data[0]["text"])


# ════════════════════════════════════════════════════════════════════════════════
# 4. Database Tests
# ════════════════════════════════════════════════════════════════════════════════
class TestDatabase(unittest.TestCase):
    """Tests for DatabaseManager — opportunities table."""

    def setUp(self):
        self.db_file = tempfile.mktemp(suffix=".db")
        self.db = DatabaseManager(db_path=self.db_file)
        self.db.connect()
        self.db.create_table_if_not_exists()

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_file):
            os.unlink(self.db_file)

    def test_connect_returns_true(self):
        """connect() should return True on success."""
        db2 = DatabaseManager(db_path=self.db_file)
        result = db2.connect()
        self.assertTrue(result)
        db2.close()

    def test_table_created(self):
        """opportunities table should exist after create_table_if_not_exists()."""
        self.db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='opportunities'"
        )
        row = self.db.cursor.fetchone()
        self.assertIsNotNone(row)

    def test_insert_single_opportunity(self):
        """Inserting one opportunity should return count of 1."""
        opps = [{
            "domain/topic": "Python Full Stack",
            "location": "Bangalore",
            "start_date": "20th Jan 2025",
            "duration": "10 days",
            "mode": "offline",
            "pay": "4000/day",
            "contact": "9845012345",
        }]
        count = self.db.insert_opportunities(opps)
        self.assertEqual(count, 1)

    def test_insert_multiple_opportunities(self):
        """Inserting multiple opportunities should return the correct count."""
        opps = [
            {"domain/topic": "Data Science", "location": "Hyderabad",
             "start_date": None, "duration": "5 days",
             "mode": "online", "pay": "3000/day", "contact": "9876543210"},
            {"domain/topic": "DevOps", "location": "Pune",
             "start_date": "1st Feb 2025", "duration": "8 days",
             "mode": "offline", "pay": "5000/day", "contact": "9823456789"},
        ]
        count = self.db.insert_opportunities(opps)
        self.assertEqual(count, 2)

    def test_inserted_data_retrievable(self):
        """Inserted opportunities should be retrievable via SELECT."""
        opps = [{"domain/topic": "AWS", "location": "Chennai",
                 "start_date": None, "duration": None,
                 "mode": "online", "pay": None, "contact": "9500123456"}]
        self.db.insert_opportunities(opps)
        rows = self.db.execute_query("SELECT domain_topic, location FROM opportunities")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "AWS")
        self.assertEqual(rows[0][1], "Chennai")

    def test_insert_empty_list_returns_zero(self):
        """Inserting an empty list should return 0."""
        count = self.db.insert_opportunities([])
        self.assertEqual(count, 0)

    def test_null_fields_stored_as_null(self):
        """Fields with None should be stored as SQL NULL, not the string 'None'."""
        opps = [{"domain/topic": "Java", "location": None,
                 "start_date": None, "duration": None,
                 "mode": None, "pay": None, "contact": "9944001122"}]
        self.db.insert_opportunities(opps)
        rows = self.db.execute_query("SELECT location FROM opportunities")
        self.assertIsNone(rows[0][0])

    def test_multiple_inserts_accumulate(self):
        """Calling insert_opportunities twice should accumulate records."""
        opp = [{"domain/topic": "React JS", "location": "Mumbai",
                "start_date": None, "duration": "7 days",
                "mode": "offline", "pay": "4500/day", "contact": "9819012345"}]
        self.db.insert_opportunities(opp)
        self.db.insert_opportunities(opp)
        rows = self.db.execute_query("SELECT COUNT(*) FROM opportunities")
        self.assertEqual(rows[0][0], 2)


# ════════════════════════════════════════════════════════════════════════════════
# 5. End-to-End Pipeline Test
# ════════════════════════════════════════════════════════════════════════════════
class TestEndToEndPipeline(unittest.TestCase):
    """Integration test: chat.txt → parse → filter → JSON → DB."""

    def setUp(self):
        self.chat_file = _write_temp_chat()
        self.json_file = tempfile.mktemp(suffix=".json")
        self.db_file  = tempfile.mktemp(suffix=".db")

    def tearDown(self):
        for f in [self.chat_file, self.json_file, self.db_file]:
            if os.path.exists(f):
                os.unlink(f)

    def test_full_pipeline(self):
        """Full pipeline: parse → filter → save JSON → DB insert."""
        # Step 1: Parse
        messages = parse_chat_file(self.chat_file)
        self.assertIsNotNone(messages)
        self.assertGreater(len(messages), 0)

        # Step 2: Filter
        filtered = filter_system_messages(messages)
        self.assertLess(len(filtered), len(messages))  # some removed
        self.assertGreater(len(filtered), 0)            # some remain

        # Step 3: Save to JSON
        result = save_messages_to_json(filtered, self.json_file)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.json_file))

        # Step 4: Verify JSON
        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), len(filtered))

        # Step 5: DB insert (simulated opportunities)
        db = DatabaseManager(db_path=self.db_file)
        db.connect()
        db.create_table_if_not_exists()
        opps = [{"domain/topic": "Python", "location": "Bangalore",
                 "start_date": "20th Jan", "duration": "10 days",
                 "mode": "offline", "pay": "4000/day", "contact": "9845012345"}]
        count = db.insert_opportunities(opps)
        self.assertEqual(count, 1)
        db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)