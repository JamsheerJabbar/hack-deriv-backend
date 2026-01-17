import sqlite3
import os

DB_FILE = 'derivinsight_fixed.db'

def validate_db():
    if not os.path.exists(DB_FILE):
        print(f"Database {DB_FILE} not found!")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    tables = ['users', 'transactions', 'login_events', 'alerts', 'alert_rules', 'audit_logs', 'dashboards']
    
    print("Record counts:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")
        except sqlite3.OperationalError as e:
            print(f"{table}: ERROR - {e}")

    conn.close()

if __name__ == '__main__':
    validate_db()
