"""Check database tables."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "wifisense.db"

if not db_path.exists():
    print("Database does not exist yet")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Existing tables: {tables}")
    
    # Check events table structure
    if "events" in tables:
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        print("\nEvents table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
