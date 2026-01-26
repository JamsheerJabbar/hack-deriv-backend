import json
import os

domains_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains'
domain_files = ['general.json', 'compliance.json', 'operations.json', 'risk.json', 'security.json']

# New schema descriptions based on derivinsightnew.db
users_desc = "The 'users' table stores profiles with: user_id, username, age, kyc_status (VERIFIED|PENDING), risk_level, risk_score, is_pep (0|1), account_status, created_at, updated_at."
txns_desc = "The 'transactions' table records financial activities: txn_id, user_id, txn_type (Refund|Deposit|Withdrawal|Transfer|Trade|Fee), instrument (uses ticker symbols like AMZN, AAPL, TSLA), amount, currency, amount_usd, status, flag_reason, payment_method, external_ref, ip_address, created_at, processed_at."
logins_desc = "The 'login_events' table logs attempts: event_id, user_id, email_attempted, ip_address, country, city, device_type, device_fingerprint, user_agent, status, failure_reason, created_at."

new_context = f"The database contains information about users, their transactions, and login events.\n1. {users_desc}\n2. {txns_desc}\n3. {logins_desc}"

for domain_file in domain_files:
    file_path = os.path.join(domains_path, domain_file)
    if not os.path.exists(file_path): continue
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['schema_context'] = new_context
    
    # Also update db_profile to show actual columns for better LLM precision
    if 'db_profile' in data:
        data['db_profile']['users'] = {
            "columns": ["user_id", "username", "age", "kyc_status", "risk_level", "risk_score", "is_pep", "account_status", "created_at", "updated_at"]
        }
        # transactions and login_events columns stayed mostly the same
        data['db_profile']['transactions'] = {
            "columns": ["txn_id", "user_id", "txn_type", "instrument", "amount", "currency", "amount_usd", "status", "flag_reason", "payment_method", "external_ref", "ip_address", "created_at", "processed_at"]
        }
        data['db_profile']['login_events'] = {
            "columns": ["event_id", "user_id", "email_attempted", "ip_address", "country", "city", "device_type", "device_fingerprint", "user_agent", "status", "failure_reason", "created_at"]
        }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated domain context and profiles to match derivinsightnew.db columns.")
