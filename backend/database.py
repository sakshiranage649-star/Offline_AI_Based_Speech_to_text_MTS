import sqlite3
import os
import hashlib
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "transly.db")

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            # Enable high-speed WAL mode and performance tuning PRAGMAs
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB memory cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            self.create_db()
            self.initialize_admin()
            print(f"Connected to database sqlite")
        except Exception as err:
            print(f"Database error: {err}")

    def create_db(self):
        try:
            cursor = self.connection.cursor()
            # Translations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER DEFAULT 1,
                    source_lang VARCHAR(10) NOT NULL,
                    target_lang VARCHAR(10) NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    role VARCHAR(20) DEFAULT 'user',
                    tokens INTEGER DEFAULT 1000,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration: Add email, phone, token_exhausted_at columns if they don't exist
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'email' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")
            if 'phone' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")
            if 'token_exhausted_at' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN token_exhausted_at DATETIME DEFAULT NULL")
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key VARCHAR(50) PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            
            # Initialize default settings if not present
            cursor.execute("SELECT * FROM settings WHERE key = 'default_welcome_tokens'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES ('default_welcome_tokens', '1000')")

            self.connection.commit()
        except Exception as err:
            print(f"Error creating database: {err}")

    def initialize_admin(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = 'Admin'")
            if not cursor.fetchone():
                hashed_pw = hashlib.sha256("Admin123".encode()).hexdigest()
                cursor.execute("INSERT INTO users (username, password, role, tokens) VALUES (?, ?, ?, ?)",
                             ('Admin', hashed_pw, 'admin', 999999))
                self.connection.commit()
        except Exception as err:
            print(f"Error initializing admin: {err}")

    def register_user(self, username, password, email=None, phone=None):
        try:
            cursor = self.connection.cursor()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            # Fetch default tokens from settings
            cursor.execute("SELECT value FROM settings WHERE key = 'default_welcome_tokens'")
            res = cursor.fetchone()
            default_tokens = int(res[0]) if res else 1000

            cursor.execute("INSERT INTO users (username, password, email, phone, tokens) VALUES (?, ?, ?, ?, ?)", 
                         (username, hashed_pw, email, phone, default_tokens))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as err:
            print(f"Error registering user: {err}")
            return False

    def _check_and_refill_tokens(self, user_dict):
        if not user_dict: return user_dict
        if user_dict.get('token_exhausted_at'):
            try:
                exhausted_time = datetime.strptime(user_dict['token_exhausted_at'], '%Y-%m-%d %H:%M:%S')
                if (datetime.utcnow() - exhausted_time) > timedelta(hours=1):
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT value FROM settings WHERE key = 'default_welcome_tokens'")
                    res = cursor.fetchone()
                    default_tokens = int(res[0]) if res else 1000
                    cursor.execute("UPDATE users SET tokens = ?, token_exhausted_at = NULL WHERE id = ?", (default_tokens, user_dict['id']))
                    self.connection.commit()
                    user_dict['tokens'] = default_tokens
                    user_dict['token_exhausted_at'] = None
            except Exception as e:
                print(f"Error refilling tokens: {e}")
        return user_dict

    def authenticate_user(self, username, password):
        try:
            cursor = self.connection.cursor()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
            user = cursor.fetchone()
            if user:
                user_dict = dict(user)
                return self._check_and_refill_tokens(user_dict)
            return None
        except Exception as err:
            print(f"Auth error: {err}")
            return None

    def get_user_by_id(self, user_id):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id, username, role, tokens, email, phone, token_exhausted_at FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                user_dict = dict(user)
                return self._check_and_refill_tokens(user_dict)
            return None
        except Exception: return None

    def update_user(self, user_id, email, phone):
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET email = ?, phone = ? WHERE id = ?", (email, phone, user_id))
            self.connection.commit()
            return True
        except Exception as err:
            print(f"Update error: {err}")
            return False

    def update_user_tokens(self, user_id, tokens):
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET tokens = ?, token_exhausted_at = NULL WHERE id = ?", (tokens, user_id))
            self.connection.commit()
            return True
        except Exception as err:
            print(f"Update tokens error: {err}")
            return False

    def update_setting(self, key, value):
        try:
            cursor = self.connection.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            self.connection.commit()
            return True
        except Exception as err:
            print(f"Update setting error: {err}")
            return False

    def get_settings(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM settings")
            return {row['key']: row['value'] for row in cursor.fetchall()}
        except Exception as err:
            print(f"Error fetching settings: {err}")
            return {}

    def save_translation(self, source_lang, target_lang, source_text, translated_text, user_id=1):
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            # Deduct tokens (simple estimation: 1 char = 1 token)
            tokens_used = len(source_text)
            cursor.execute("UPDATE users SET tokens = tokens - ? WHERE id = ?", (tokens_used, user_id))
            
            cursor.execute("SELECT tokens FROM users WHERE id = ?", (user_id,))
            current_tokens = cursor.fetchone()[0]
            if current_tokens <= 0:
                cursor.execute("UPDATE users SET token_exhausted_at = CURRENT_TIMESTAMP WHERE id = ? AND token_exhausted_at IS NULL", (user_id,))
            
            query = "INSERT INTO translations (source_lang, target_lang, source_text, translated_text, user_id) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(query, (source_lang, target_lang, source_text, translated_text, user_id))
            self.connection.commit()
        except Exception as err:
            print(f"Error saving translation: {err}")

    def get_history(self, limit=10, search="", user_id=None):
        if not self.connection:
            return []
            
        try:
            cursor = self.connection.cursor()
            params = []
            query = "SELECT * FROM translations "
            if user_id:
                query += "WHERE user_id = ? "
                params.append(user_id)
            
            if search:
                query += ("AND " if user_id else "WHERE ") + "(source_text LIKE ? OR translated_text LIKE ?) "
                like_pattern = f"%{search}%"
                params.extend([like_pattern, like_pattern])
            
            query += "ORDER BY timestamp DESC LIMIT ?"
            params.append(int(limit))
            
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as err:
            print(f"Error fetching history: {err}")
            return []

    # Admin Report Methods
    def get_admin_reports(self):
        try:
            cursor = self.connection.cursor()
            
            # 1. Total Users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # 2. Total Translations
            cursor.execute("SELECT COUNT(*) FROM translations")
            total_translations = cursor.fetchone()[0]
            
            # 3. Token Leaders (Top 5)
            cursor.execute("SELECT username, tokens FROM users ORDER BY tokens DESC LIMIT 5")
            token_leaders = [dict(row) for row in cursor.fetchall()]
            
            # 4. Language Popularity
            cursor.execute("SELECT target_lang as lang, COUNT(*) as count FROM translations GROUP BY target_lang ORDER BY count DESC LIMIT 5")
            lang_popularity = [dict(row) for row in cursor.fetchall()]
            
            # 5. Daily Traffic (Last 7 days)
            cursor.execute("""
                SELECT strftime('%Y-%m-%d', timestamp) as date, COUNT(*) as count 
                FROM translations 
                WHERE timestamp >= date('now', '-7 days')
                GROUP BY date 
                ORDER BY date ASC
            """)
            results = {row['date']: row['count'] for row in cursor.fetchall()}
            
            daily_traffic = []
            for i in range(6, -1, -1):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_traffic.append({"date": date, "count": results.get(date, 0)})
            
            # Extra: User List for management
            cursor.execute("SELECT id, username, role, tokens, created_at FROM users")
            user_list = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total_users": total_users,
                "total_translations": total_translations,
                "token_leaders": token_leaders,
                "lang_popularity": lang_popularity,
                "daily_traffic": daily_traffic,
                "user_list": user_list
            }
        except Exception as err:
            print(f"Report error: {err}")
            return {}

db_handler = DatabaseHandler()

