-- SQLite Database Schema for Conversational Data Analysis System
-- Simple, file-based database with no external dependencies

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,           -- Format: DD/MM/YY
    time TEXT NOT NULL,           -- Format: HH:MM:SS AM/PM
    author TEXT NOT NULL,          -- Message author name
    content TEXT NOT NULL,         -- Message content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- When record was inserted
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
CREATE INDEX IF NOT EXISTS idx_messages_author ON messages(author);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Sample queries for reference:
-- Get all messages: SELECT * FROM messages ORDER BY date, time;
-- Get messages by author: SELECT * FROM messages WHERE author = 'John' ORDER BY date, time;
-- Search messages: SELECT * FROM messages WHERE content LIKE '%training%' ORDER BY date, time;
-- Get message count: SELECT COUNT(*) FROM messages;
-- Get top authors: SELECT author, COUNT(*) as count FROM messages GROUP BY author ORDER BY count DESC LIMIT 5;
