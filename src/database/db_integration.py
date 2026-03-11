import os
import sqlite3
from datetime import datetime
import json
from .models import DatabaseSchema

class DatabaseManager:
    def __init__(self, db_path="data/conversational_analysis.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            print(f" Connected to SQLite database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f" Database connection failed: {e}")
            return False
        
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print(" Database connection closed")
    
    def create_table_if_not_exists(self):
        """Create the messages table if it doesn't exist"""
        try:
            self.cursor.execute(DatabaseSchema.CREATE_RAW_TABLE)
            self.connection.commit()
            print(" Table created/verified successfully")
            return True
        except sqlite3.Error as e:
            print(f" Error creating table: {e}")
            return False
    
    def insert_messages(self, messages):
        """Insert messages into database"""
        if not messages:
            return 0
            
        try:
            # Prepare data for insertion
            data_to_insert = []
            for msg in messages:
                date_str = msg.get('date', '')
                time_str = msg.get('time', '')
                author = msg.get('author', '')
                content = msg.get('text', '')
                
                data_to_insert.append((date_str, time_str, author, content))
            
            # Insert in batch
            self.cursor.executemany(
                "INSERT INTO messages (date, time, author, content) VALUES (?, ?, ?, ?)",
                data_to_insert
            )
            self.connection.commit()
            
            inserted_count = self.cursor.rowcount
            print(f" Inserted {inserted_count} messages into database")
            return inserted_count
            
        except sqlite3.Error as e:
            print(f" Error inserting messages: {e}")
            return 0
    
    def get_table_stats(self):
        """Get statistics about the messages table"""
        try:
            # Get total count
            self.cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = self.cursor.fetchone()[0]
            
            # Get top 5 authors
            self.cursor.execute("""
                SELECT author, COUNT(*) as message_count 
                FROM messages 
                WHERE author != '' 
                GROUP BY author 
                ORDER BY message_count DESC 
                LIMIT 5
            """)
            top_authors = self.cursor.fetchall()
            
            print(f"\n📊 Database Statistics:")
            print(f"   • Total messages: {total_messages}")
            print(f"   • Top 5 authors:")
            for i, (author, count) in enumerate(top_authors, 1):
                print(f"     {i}. {author}: {count} messages")
                
        except sqlite3.Error as e:
            print(f" Error getting stats: {e}")
    
    def show_stats(self):
        """Alias for get_table_stats for compatibility"""
        self.get_table_stats()
    
    def execute_query(self, query, params=None):
        """Execute a custom query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
                
        except sqlite3.Error as e:
            print(f" Query execution error: {e}")
            return None
