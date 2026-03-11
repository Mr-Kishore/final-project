import sqlite3

class DatabaseSchema:
    """Class containing SQL commands for SQLite database schema creation"""
    
    # Table creation command for SQLite
    CREATE_RAW_TABLE = """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Index creation for better performance
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);",
        "CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author);",
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);"
    ]
    
    # Sample queries
    GET_ALL_MESSAGES = "SELECT * FROM messages ORDER BY date, time;"
    GET_MESSAGES_BY_AUTHOR = "SELECT * FROM messages WHERE author = ? ORDER BY date, time;"
    GET_MESSAGES_BY_DATE_RANGE = "SELECT * FROM messages WHERE date BETWEEN ? AND ? ORDER BY date, time;"
    SEARCH_MESSAGES = "SELECT * FROM messages WHERE content LIKE ? ORDER BY date, time;"
    
    @staticmethod
    def create_all_indexes(cursor):
        """Create all indexes for better performance"""
        for index_query in DatabaseSchema.CREATE_INDEXES:
            try:
                cursor.execute(index_query)
                print(f" Created index: {index_query.split('idx_')[1].split(' ')[0]}")
            except sqlite3.Error as e:
                print(f" Error creating index: {e}")
