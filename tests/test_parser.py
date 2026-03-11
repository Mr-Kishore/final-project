"""
Tests for the Conversational Data Analysis System parser.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.parser import parse_chat_file, filter_system_messages, is_system_message


class TestParser(unittest.TestCase):
    """Test cases for the parser module."""
    
    def test_is_system_message(self):
        """Test system message detection."""
        system_messages = [
            "Messages and calls are end-to-end encrypted",
            "created this group",
            "left the group",
            "added you",
            "removed you",
            "changed the group description",
            "changed the subject"
        ]
        
        for msg in system_messages:
            self.assertTrue(is_system_message(msg), f"Should detect as system message: {msg}")
    
    def test_normal_message_not_system(self):
        """Test that normal messages are not detected as system messages."""
        normal_messages = [
            "Hey everyone, how are you?",
            "Training starts tomorrow in Hyderabad",
            "Looking for Python developers",
            "Check out this opportunity"
        ]
        
        for msg in normal_messages:
            self.assertFalse(is_system_message(msg), f"Should not detect as system message: {msg}")


if __name__ == '__main__':
    unittest.main()
