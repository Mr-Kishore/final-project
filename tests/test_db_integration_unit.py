import os
import sys
import tempfile
import unittest

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_integration import DatabaseManager


class TestDatabaseManagerUnit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "nested", "unit_test.db")
        self.db = DatabaseManager(db_path=self.db_path)
        self.db.connect()
        self.db.create_table_if_not_exists()

    def tearDown(self):
        self.db.close()
        self.temp_dir.cleanup()

    def test_init_creates_parent_directory(self):
        self.assertTrue(os.path.isdir(os.path.dirname(self.db_path)))

    def test_insert_opportunities_converts_empty_strings_to_null(self):
        opportunities = [
            {
                "domain/topic": "Python",
                "location": "",
                "start_date": "",
                "duration": None,
                "mode": "",
                "pay": "",
                "contact": "9999999999",
            }
        ]

        inserted = self.db.insert_opportunities(opportunities)
        self.assertEqual(inserted, 1)

        rows = self.db.execute_query(
            "SELECT location, start_date, duration, mode, pay FROM opportunities"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], (None, None, None, None, None))

    def test_execute_query_non_select_returns_rowcount(self):
        rowcount = self.db.execute_query(
            "INSERT INTO opportunities (domain_topic, location, contact) VALUES (?, ?, ?)",
            ("Data Science", "Hyderabad", "12345"),
        )
        self.assertEqual(rowcount, 1)

    def test_execute_query_select_returns_rows(self):
        self.db.insert_opportunities(
            [{"domain/topic": "DevOps", "location": "Pune", "contact": "88888"}]
        )
        rows = self.db.execute_query(
            "SELECT domain_topic, location, contact FROM opportunities"
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ("DevOps", "Pune", "88888"))

    def test_execute_query_invalid_sql_returns_none(self):
        result = self.db.execute_query("SELECT * FROM does_not_exist")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
