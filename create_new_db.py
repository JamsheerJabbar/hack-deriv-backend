import sqlite3
import csv
import os
from datetime import datetime

def create_new_db():
    db_path = 'derivinsightnew.db'
    archive_dir = 'Archive'
    
    # Remove existing db if it exists
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.close() # Ensure it's not and-locked
            os.remove(db_path)
        except Exception as e:
            print(f"Warning: Could not remove {db_path}: {e}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Create Users Table
    print("Creating 'users' table...")
    cursor.execute("""
    CREATE TABLE users (
        user_id VARCHAR(36) PRIMARY KEY,
        username VARCHAR(200),
        age INTEGER,
        kyc_status VARCHAR(20),
        risk_level VARCHAR(10),
        risk_score INTEGER,
        is_pep INTEGER,
        account_status VARCHAR(20),
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)
    
    users_csv = os.path.join(archive_dir, 'users.csv')
    if os.path.exists(users_csv):
        with open(users_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users_to_insert = []
            for row in reader:
                kyc_val = row.get('keyValid', '').lower()
                kyc_status = 'VERIFIED' if kyc_val == 'true' else 'PENDING'
                
                pep_val = row.get('isPoliticallyExposed', '').lower()
                is_pep = 1 if pep_val == 'true' else 0
                
                users_to_insert.append((
                    row.get('userId'),
                    row.get('username'),
                    int(row.get('age')) if row.get('age') else None,
                    kyc_status,
                    row.get('riskLevel').upper() if row.get('riskLevel') else None,
                    int(row.get('riskScore')) if row.get('riskScore') else None,
                    is_pep,
                    row.get('accountStatus').upper() if row.get('accountStatus') else None,
                    row.get('createdAt'),
                    row.get('updatedAt')
                ))
            
            cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", users_to_insert)
            print(f"Imported {len(users_to_insert)} users.")

    # 2. Create Transactions Table
    print("Creating 'transactions' table...")
    cursor.execute("""
    CREATE TABLE transactions (
        txn_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36),
        txn_type VARCHAR(20),
        instrument VARCHAR(20),
        amount DECIMAL(18,2),
        currency CHAR(3),
        amount_usd DECIMAL(18,2),
        status VARCHAR(20),
        flag_reason VARCHAR(100),
        payment_method VARCHAR(50),
        external_ref VARCHAR(100),
        ip_address VARCHAR(45),
        created_at TIMESTAMP,
        processed_at TIMESTAMP
    )
    """)
    
    transactions_csv = os.path.join(archive_dir, 'transactions.csv')
    if os.path.exists(transactions_csv):
        with open(transactions_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            txns_to_insert = []
            for row in reader:
                txns_to_insert.append((
                    row.get('txn_id'), row.get('user_id'), 
                    row.get('txn_type').upper() if row.get('txn_type') else None,
                    row.get('instrument'), 
                    row.get('amount'), row.get('currency'),
                    row.get('amount_usd'), 
                    row.get('status').upper() if row.get('status') else None,
                    row.get('flag_reason'),
                    row.get('payment_method'), row.get('external_ref'), row.get('ip_address'),
                    row.get('created_at'), row.get('processed_at')
                ))
            
            cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", txns_to_insert)
            print(f"Imported {len(txns_to_insert)} transactions.")

    # 3. Create Login Events Table
    print("Creating 'login_events' table...")
    cursor.execute("""
    CREATE TABLE login_events (
        event_id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36),
        email_attempted VARCHAR(255),
        ip_address VARCHAR(45),
        country VARCHAR(100),
        city VARCHAR(100),
        device_type VARCHAR(20),
        device_fingerprint VARCHAR(64),
        user_agent TEXT,
        status VARCHAR(20),
        failure_reason VARCHAR(50),
        created_at TIMESTAMP
    )
    """)
    
    login_csv = os.path.join(archive_dir, 'login_events.csv')
    if os.path.exists(login_csv):
        with open(login_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            logins_to_insert = []
            for row in reader:
                logins_to_insert.append((
                    row.get('event_id'), row.get('user_id'), row.get('email_attempted'),
                    row.get('ip_address'), row.get('country'), row.get('city'),
                    row.get('device_type'), row.get('device_fingerprint'), row.get('user_agent'),
                    row.get('status').upper() if row.get('status') else None,
                    row.get('failure_reason'), row.get('created_at')
                ))
            
            cursor.executemany("INSERT INTO login_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", logins_to_insert)
            print(f"Imported {len(logins_to_insert)} login events.")

    conn.commit()
    conn.close()
    print("Database 'derivinsightnew.db' created successfully with standard casing.")

if __name__ == "__main__":
    create_new_db()
