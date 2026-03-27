import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Provide a lightweight ollama module if unavailable in the environment.
if "ollama" not in sys.modules:
    ollama_stub = types.ModuleType("ollama")

    def _default_generate(*args, **kwargs):
        return {"response": "[]"}

    ollama_stub.generate = _default_generate
    sys.modules["ollama"] = ollama_stub

from src.llm import extractor


class TestExtractorUnit(unittest.TestCase):
    def _write_chat_json(self, messages):
        temp_dir = tempfile.TemporaryDirectory()
        chat_path = os.path.join(temp_dir.name, "chat.json")
        with open(chat_path, "w", encoding="utf-8") as f:
            json.dump(messages, f)
        return temp_dir, chat_path

    @patch("src.llm.extractor.ollama.generate")
    def test_chat_with_llm_success(self, mock_generate):
        mock_generate.return_value = {"response": "ok"}
        result = extractor.chat_with_llm("hello", model="llama3.2:1b")
        self.assertEqual(result, "ok")

    @patch("src.llm.extractor.ollama.generate")
    def test_chat_with_llm_error_is_returned(self, mock_generate):
        mock_generate.side_effect = RuntimeError("service unavailable")
        result = extractor.chat_with_llm("hello")
        self.assertIn("Error:", result)
        self.assertIn("service unavailable", result)

    @patch("src.database.DatabaseManager")
    @patch("src.llm.extractor.chat_with_llm")
    def test_extract_info_deduplicates_and_saves(self, mock_chat_with_llm, mock_db_cls):
        messages = [
            {"text": "Python trainer needed in Chennai. Contact 90001"},
            {"text": "General chat"},
            {"text": "Another opening"},
            {"text": "Random"},
            {"text": "One more message"},
            {"text": "DevOps opening in Pune. Contact 90002"},
        ]
        temp_dir, chat_path = self._write_chat_json(messages)

        # Two batches expected for 6 messages (batch_size=5).
        mock_chat_with_llm.side_effect = [
            json.dumps(
                [
                    {
                        "domain/topic": "Python",
                        "location": "Chennai",
                        "start_date": None,
                        "duration": None,
                        "mode": "offline",
                        "pay": None,
                        "contact": "90001",
                    },
                    {
                        "domain/topic": "Python",
                        "location": "Chennai",
                        "start_date": None,
                        "duration": None,
                        "mode": "offline",
                        "pay": None,
                        "contact": "90001",
                    },
                    {
                        "domain/topic": None,
                        "location": "Ignore",
                        "start_date": None,
                        "duration": None,
                        "mode": None,
                        "pay": None,
                        "contact": None,
                    },
                ]
            ),
            json.dumps(
                [
                    {
                        "domain/topic": "DevOps",
                        "location": "Pune",
                        "start_date": "10th Jan",
                        "duration": "5 days",
                        "mode": "online",
                        "pay": "4000/day",
                        "contact": "90002",
                    }
                ]
            ),
        ]

        mock_db = MagicMock()
        mock_db.connect.return_value = True
        mock_db.insert_opportunities.return_value = 2
        mock_db_cls.return_value = mock_db

        try:
            result = extractor.extract_training_info_from_chat(chat_path)

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["domain/topic"], "Python")
            self.assertEqual(result[1]["domain/topic"], "DevOps")

            job_details_path = os.path.join(temp_dir.name, "job_details.json")
            self.assertTrue(os.path.exists(job_details_path))
            with open(job_details_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(len(saved), 2)

            mock_db.create_table_if_not_exists.assert_called_once()
            mock_db.insert_opportunities.assert_called_once_with(result)
            mock_db.close.assert_called_once()
        finally:
            temp_dir.cleanup()

    @patch("src.database.DatabaseManager")
    @patch("src.llm.extractor.chat_with_llm")
    def test_extract_info_skips_invalid_json_batch(self, mock_chat_with_llm, mock_db_cls):
        messages = [{"text": "Message one"}]
        temp_dir, chat_path = self._write_chat_json(messages)

        mock_chat_with_llm.return_value = "not-json"
        mock_db = MagicMock()
        mock_db.connect.return_value = True
        mock_db.insert_opportunities.return_value = 0
        mock_db_cls.return_value = mock_db

        try:
            result = extractor.extract_training_info_from_chat(chat_path)
            self.assertEqual(result, [])

            job_details_path = os.path.join(temp_dir.name, "job_details.json")
            self.assertTrue(os.path.exists(job_details_path))
            with open(job_details_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, [])
        finally:
            temp_dir.cleanup()

    def test_extract_info_missing_file_returns_empty_list(self):
        result = extractor.extract_training_info_from_chat("/tmp/no_such_chat_file_12345.json")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
