import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "transly.db")

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.create_db()
            print(f"Connected to database sqlite")
        except Exception as err:
            print(f"Database error: {err}")

    def create_db(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang VARCHAR(10) NOT NULL,
                    target_lang VARCHAR(10) NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
        except Exception as err:
            print(f"Error creating database: {err}")

    def save_translation(self, source_lang, target_lang, source_text, translated_text):
        if not self.connection:
            print("Failed to save translation: No database connection.")
            return

        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO translations (source_lang, target_lang, source_text, translated_text) VALUES (?, ?, ?, ?)"
            cursor.execute(query, (source_lang, target_lang, source_text, translated_text))
            self.connection.commit()
        except Exception as err:
            print(f"Error saving translation: {err}")

    def get_history(self, limit=10, search=""):
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            limit = int(limit) # ensure limit is int
            if search:
                query = "SELECT * FROM translations WHERE source_text LIKE ? OR translated_text LIKE ? ORDER BY timestamp DESC LIMIT ?"
                like_pattern = f"%{search}%"
                cursor.execute(query, (like_pattern, like_pattern, limit))
            else:
                query = "SELECT * FROM translations ORDER BY timestamp DESC LIMIT ?"
                cursor.execute(query, (limit,))
            result = [dict(row) for row in cursor.fetchall()]
            return result
        except Exception as err:
            print(f"Error fetching history: {err}")
            return []

db_handler = DatabaseHandler()
