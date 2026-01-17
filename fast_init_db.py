import sqlite3
import os
import time

DB_FILE = 'derivinsight_fixed.db'
SCHEMA_FILE = 'app/files/derivinsight_schema.sql'
DATA_FILE = 'derivinsight_mock_data.sql'

def init_db():
    try:
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
                print(f"Removed existing {DB_FILE}")
            except PermissionError:
                print(f"Cannot remove {DB_FILE}. It might be in use. Trying to rename...")
                os.rename(DB_FILE, f"{DB_FILE}.old")
    except Exception as e:
        print(f"Error handling existing DB: {e}")
        # Proceeding anyway might fail if locked

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Speed optimizations
    cursor.execute("PRAGMA synchronous = OFF")
    cursor.execute("PRAGMA journal_mode = MEMORY")

    print(f"Executing schema from {SCHEMA_FILE}...")
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    print(f"Executing data from {DATA_FILE}...")
    
    count = 0
    with open(DATA_FILE, 'r') as f:
        cursor.execute("BEGIN TRANSACTION")
        for line in f:
            line = line.strip()
            if line and not line.startswith('--'):
                try:
                    cursor.execute(line)
                    count += 1
                    if count % 5000 == 0:
                        print(f"Inserted {count} records...")
                except sqlite3.Error as e:
                    print(f"Error executing line: {line[:50]}... -> {e}")
        conn.commit()

    conn.close()
    print(f"Database initialization complete. Total inserts: {count}")

if __name__ == '__main__':
    init_db()
