import sqlite3
import csv

def get_table_columns(db_name, table_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    return columns

def import_csv_to_db(db_name, csv_file, table_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    db_columns = get_table_columns(db_name, table_name)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Get header row

        # Define a mapping from CSV header to database column names (snake_case)
        column_mapping = {
            'userid': 'user_id',
            'username': 'full_name',
            'keyvalid': 'kyc_status',
            'risklevel': 'risk_level',
            'riskscore': 'risk_score',
            'ispoliticallyexposed': 'is_pep',
            'accountstatus': 'account_status',
            'createdat': 'created_at',
            'updatedat': 'updated_at',
            'txnid': 'txn_id',
            'txntype': 'txn_type',
            'amountusd': 'amount_usd',
            'flagreason': 'flag_reason',
            'paymentmethod': 'payment_method',
            'externalref': 'external_ref',
            'ipaddress': 'ip_address',
            'processedat': 'processed_at',
            'eventid': 'event_id',
            'emailattempted': 'email_attempted',
            'devicetype': 'device_type',
            'devicefingerprint': 'device_fingerprint',
            'useragent': 'user_agent',
            'failurereason': 'failure_reason',
        }

        # Prepare the header and row data to match database columns
        mapped_header = []
        for col in header:
            col_lower = col.lower().replace(' ', '_')
            mapped_header.append(column_mapping.get(col_lower, col_lower))

        # Filter columns that exist in the database table
        filtered_header_and_data_map = []
        for i, col in enumerate(mapped_header):
            if col in db_columns:
                filtered_header_and_data_map.append((col, i))

        # Get the actual database column names for the INSERT statement
        final_db_columns = [item[0] for item in filtered_header_and_data_map]

        # Add email and country to final_db_columns if they are in DB schema but not in CSV
        if table_name == "users":
            if "email" in db_columns and "email" not in final_db_columns:
                final_db_columns.append("email")
            if "country" in db_columns and "country" not in final_db_columns:
                final_db_columns.append("country")

        placeholders = ', '.join(['?' for _ in final_db_columns])
        insert_sql = f"INSERT INTO {table_name} ({', '.join(final_db_columns)}) VALUES ({placeholders})"

        for row_data in reader:
            filtered_row = []
            full_name_for_email = None
            for col_name, original_idx in filtered_header_and_data_map:
                filtered_row.append(row_data[original_idx])
                if table_name == "users" and col_name == "full_name":
                    full_name_for_email = row_data[original_idx]

            # Generate email and country if it's the users table and they were added to final_db_columns
            if table_name == "users":
                if "email" in db_columns and "email" not in [item[0] for item in filtered_header_and_data_map]:
                    if full_name_for_email:
                        generated_email = f"{full_name_for_email.lower().replace(' ', '_')}@example.com"
                        filtered_row.append(generated_email)
                    else:
                        print(f"Warning: Could not generate email for row: {row_data}. Skipping row if email is NOT NULL.")
                        continue
                if "country" in db_columns and "country" not in [item[0] for item in filtered_header_and_data_map]:
                    # Default country code
                    filtered_row.append("US") 

            try:
                cursor.execute(insert_sql, filtered_row)
            except sqlite3.IntegrityError as e:
                print(f"Skipping row due to integrity error: {filtered_row} - {e}")
            except sqlite3.Error as e:
                print(f"Error inserting row: {filtered_row} - {e}")

    conn.commit()
    conn.close()
    print(f"Data from '{csv_file}' imported into '{table_name}' table.")

if __name__ == "__main__":
    db_file = "derivinsight.db"

    # Import data from CSVs
    import_csv_to_db(db_file, "Archive/users.csv", "users")
    import_csv_to_db(db_file, "Archive/transactions.csv", "transactions")
    import_csv_to_db(db_file, "Archive/login_events.csv", "login_events")
