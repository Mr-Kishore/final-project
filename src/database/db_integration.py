import os
import sqlite3
from .models import DatabaseSchema


class DatabaseManager:
    """Manages SQLite database operations for the Conversational Data Analysis System.
    
    The database stores LLM-extracted opportunities only.
    Raw parsed messages are stored in chat.json, not the database.
    """

    def __init__(self, db_path="data/conversational_analysis.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def connect(self):
        """Open a connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f" Connected to SQLite database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f" Database connection failed: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print(" Database connection closed")

    def create_table_if_not_exists(self):
        """Create the opportunities table and indexes if they don't exist."""
        try:
            self.cursor.execute(DatabaseSchema.CREATE_OPPORTUNITIES_TABLE)
            self.connection.commit()
            DatabaseSchema.create_all_indexes(self.cursor)
            self.connection.commit()
            print(" Opportunities table created/verified successfully")
            return True
        except sqlite3.Error as e:
            print(f" Error creating table: {e}")
            return False

    def insert_opportunities(self, opportunities):
        """Insert LLM-extracted opportunities into the database.
        
        Args:
            opportunities: list of dicts with keys:
                domain/topic, location, start_date, duration, mode, pay, contact
        
        Returns:
            Number of records inserted.
        """
        if not opportunities:
            return 0

        try:
            data_to_insert = []
            for opp in opportunities:
                data_to_insert.append((
                    opp.get("domain/topic") or None,
                    opp.get("location") or None,
                    opp.get("start_date") or None,
                    opp.get("duration") or None,
                    opp.get("mode") or None,
                    opp.get("pay") or None,
                    opp.get("contact") or None,
                ))

            self.cursor.executemany(
                """INSERT INTO opportunities
                   (domain_topic, location, start_date, duration, mode, pay, contact)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                data_to_insert,
            )
            self.connection.commit()
            inserted_count = len(data_to_insert)
            print(f" Inserted {inserted_count} opportunities into database")
            return inserted_count

        except sqlite3.Error as e:
            print(f" Error inserting opportunities: {e}")
            return 0

    def get_table_stats(self):
        """Print summary statistics about stored opportunities."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM opportunities")
            total = self.cursor.fetchone()[0]

            self.cursor.execute(
                """SELECT domain_topic, COUNT(*) as cnt
                   FROM opportunities
                   WHERE domain_topic IS NOT NULL
                   GROUP BY domain_topic
                   ORDER BY cnt DESC
                   LIMIT 5"""
            )
            top_domains = self.cursor.fetchall()

            print(f"\n📊 Database Statistics:")
            print(f"   • Total opportunities: {total}")
            print(f"   • Top domains:")
            for i, (domain, count) in enumerate(top_domains, 1):
                print(f"     {i}. {domain}: {count} records")

        except sqlite3.Error as e:
            print(f" Error getting stats: {e}")

    def execute_query(self, query, params=None):
        """Execute a custom SQL query."""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount

        except sqlite3.Error as e:
            print(f" Query execution error: {e}")
            return None