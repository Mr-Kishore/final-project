import sqlite3


class DatabaseSchema:
    """Class containing SQL commands for SQLite database schema creation"""

    # Table creation command for SQLite - stores LLM-extracted opportunities
    CREATE_OPPORTUNITIES_TABLE = """
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain_topic TEXT,
        location TEXT,
        start_date TEXT,
        duration TEXT,
        mode TEXT,
        pay TEXT,
        contact TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Index creation for better performance
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_opportunities_domain ON opportunities(domain_topic);",
        "CREATE INDEX IF NOT EXISTS idx_opportunities_location ON opportunities(location);",
        "CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at);"
    ]

    # Sample queries
    GET_ALL_OPPORTUNITIES = "SELECT * FROM opportunities ORDER BY created_at DESC;"
    GET_BY_DOMAIN = "SELECT * FROM opportunities WHERE domain_topic = ?;"
    GET_BY_LOCATION = "SELECT * FROM opportunities WHERE location = ?;"
    SEARCH_OPPORTUNITIES = "SELECT * FROM opportunities WHERE domain_topic LIKE ? OR location LIKE ? OR contact LIKE ?;"

    @staticmethod
    def create_all_indexes(cursor):
        """Create all indexes for better performance"""
        for index_query in DatabaseSchema.CREATE_INDEXES:
            try:
                cursor.execute(index_query)
                print(f" Created index: {index_query.split('idx_')[1].split(' ')[0]}")
            except sqlite3.Error as e:
                print(f" Error creating index: {e}")