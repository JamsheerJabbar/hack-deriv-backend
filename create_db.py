
import sqlite3

def create_database(db_name, schema_file):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    with open(schema_file, 'r') as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"Database '{db_name}' created and schema applied.")

if __name__ == "__main__":
    create_database("derivinsight.db", "app/files/derivinsight_schema.sql")
