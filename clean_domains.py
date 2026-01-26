import json
import os

domains_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains'
files = ['general.json', 'compliance.json', 'risk.json', 'operations.json', 'security.json']

def clean_domain_config():
    for filename in files:
        path = os.path.join(domains_path, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        domain_name = data.get('domain', 'general').capitalize()
        
        # 1. Reset intent prompt to be simple and accurate
        data['prompts']['intent'] = f"""You are an AI assistant for the {domain_name} domain of a financial insights platform.
Your task is to classify the user's intent and extract key parameters.

Focus on:
- Users and Profiles (username, age, kyc_status, risk_level, account_status)
- Transactions and Trading (instrument, amount, currency, status, txn_type)
- Login Events and Security (ip_address, country, city, device_type, failure_reason)

If the user asks for data retrieval, classify it as SELECT.
If the user's request is ambiguous, set needs_clarification to true.
"""

        # 2. Reset SQL prompt to be strict
        data['prompts']['sql'] = f"""You are an expert SQLite generator for the {domain_name} domain.
CORE TABLES:
- users (user_id, username, age, kyc_status, risk_level, risk_score, is_pep, account_status)
- transactions (txn_id, user_id, txn_type, instrument, amount, currency, amount_usd, status)
- login_events (event_id, user_id, status, country, city, device_type)

STRICT RULES:
1. ONLY use the tables: users, transactions, login_events.
2. NEVER hallucinate tables like 'user_instruments' or 'accounts'.
3. Use 'user_id' as the primary key/foreign key.
4. Use 'username' for user names.
5. Use 'instrument' in the 'transactions' table for stock tickers or assets.
6. JOIN users and transactions on u.user_id = t.user_id.
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print("Cleaned up domain configurations and removed legacy story/mock context.")

if __name__ == "__main__":
    clean_domain_config()
