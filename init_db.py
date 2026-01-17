import sqlite3
import os

DB_FILE = 'derivinsight.db'
SCHEMA_FILE = 'app/files/derivinsight_schema.sql'
DATA_FILE = 'derivinsight_mock_data.sql'

def init_db():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed existing {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print(f"Executing schema from {SCHEMA_FILE}...")
    with open(SCHEMA_FILE, 'r') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    print(f"Executing data from {DATA_FILE}...")
    # Read the data file. It might be large.
    # executescript handles multiple statements.
    with open(DATA_FILE, 'r') as f:
        data_sql = f.read()
        cursor.executescript(data_sql)

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
