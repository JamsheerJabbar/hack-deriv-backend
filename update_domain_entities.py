import sqlite3
import json
import os

def update_entities_in_domains():
    db_path = 'derivinsightnew.db'
    domains_dir = r'app/data/domains'
    
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define columns we want to extract unique values for
    entity_map = {
        'users': ['kyc_status', 'risk_level', 'account_status', 'username'],
        'transactions': ['txn_type', 'status', 'payment_method', 'instrument', 'currency'],
        'login_events': ['country', 'city', 'device_type', 'status', 'failure_reason']
    }

    # Extract unique values from DB
    extracted_entities = {}
    for table, columns in entity_map.items():
        extracted_entities[table] = {"columns": [], "unique_values": {}}
        
        # Get all columns for the table setup
        cursor.execute(f"PRAGMA table_info({table})")
        all_cols = [row[1] for row in cursor.fetchall()]
        extracted_entities[table]["columns"] = all_cols
        
        for col in columns:
            if col in all_cols:
                cursor.execute(f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != '' LIMIT 100")
                values = [str(row[0]) for row in cursor.fetchall()]
                extracted_entities[table]["unique_values"][col] = values

    # Update each domain JSON file
    for filename in os.listdir(domains_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(domains_dir, filename)
            print(f"Updating {filename}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding {filename}, skipping.")
                    continue

            # Replace db_profile with our extracted one
            data['db_profile'] = extracted_entities
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    conn.close()
    print("Successfully updated all domain files with real entities from derivinsightnew.db")

if __name__ == "__main__":
    update_entities_in_domains()
