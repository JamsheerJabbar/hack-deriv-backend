import sqlite3
import os

def rename_column():
    db_path = 'derivinsightnew.db'
    if not os.path.exists(db_path):
        print("DB not found")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if full_name exists
        cursor.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cursor.fetchall()]
        
        if 'full_name' in cols and 'username' not in cols:
            print("Renaming full_name to username...")
            cursor.execute("ALTER TABLE users RENAME COLUMN full_name TO username")
            conn.commit()
            print("Done.")
        else:
            print("No action needed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    rename_column()
