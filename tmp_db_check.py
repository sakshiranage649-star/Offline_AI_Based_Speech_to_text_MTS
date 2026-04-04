import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "transly.db")

try:
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in transly.db: {tables}")
        
        if ("translations",) in tables:
            cursor.execute("SELECT COUNT(*) FROM translations")
            count = cursor.fetchone()[0]
            print(f"Rows in translations: {count}")
            
        cursor.close()
        conn.close()
    else:
        print("Database transly.db does not exist yet.")
except Exception as e:
    print(f"Error: {e}")
