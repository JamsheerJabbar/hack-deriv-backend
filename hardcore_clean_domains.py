import json
import os

domains_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains'
files = ['general.json', 'compliance.json', 'risk.json', 'operations.json', 'security.json']

# Define a set of "Base Truth" few-shots that we know are correct
BASE_FEW_SHOTS = [
    {
        "question": "Show me the usernames of users with instrument AMZN",
        "sql": "SELECT DISTINCT u.username FROM users u JOIN transactions t ON u.user_id = t.user_id WHERE UPPER(t.instrument) LIKE '%AMZN%';",
        "explanation": "Joins users and transactions using correct username column."
    },
    {
        "question": "Show failed login attempts for users with HIGH risk level",
        "sql": "SELECT le.*, u.username FROM login_events le JOIN users u ON le.user_id = u.user_id WHERE UPPER(le.status) LIKE '%FAILED%' AND UPPER(u.risk_level) LIKE '%HIGH%';",
        "explanation": "Joins logins and users using correct columns."
    },
    {
        "question": "Find debit payments that were flagged",
        "sql": "SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.user_id WHERE UPPER(t.payment_method) LIKE '%DEBIT%' AND UPPER(t.status) LIKE '%FLAGGED%';",
        "explanation": "Correctly uses transactions table for payments/debit and status for flagged."
    },
    {
        "question": "What is the average age of PEP users?",
        "sql": "SELECT AVG(age) FROM users WHERE is_pep = 1;",
        "explanation": "Simple filter on users table."
    }
]

def hardcore_clean():
    for filename in files:
        path = os.path.join(domains_path, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 1. Reset Few-Shots to only our verified base truth
        data['few_shots'] = BASE_FEW_SHOTS
        
        # 2. Reset Schema Context to a strict reliable version
        data['schema_context'] = "The database consists of exactly three tables: 'users' (identity/profile), 'transactions' (all financial acts like payments, trades, deposits), and 'login_events' (security logs). There are NO other tables."
        
        # 3. Ensure Prompts are strict
        domain_name = data.get('domain', 'general').capitalize()
        data['prompts']['sql'] = f"""You are a strict SQLite expert for {domain_name}.
ACTUAL TABLES:
- users (user_id, username, age, kyc_status, risk_level, risk_score, is_pep, account_status)
- transactions (txn_id, user_id, txn_type, instrument, amount, currency, amount_usd, status, flag_reason, payment_method)
- login_events (event_id, user_id, status, country, city, device_type, failure_reason)

RULES:
1. ONLY use tables: users, transactions, login_events.
2. If user mentions 'payment', 'transfer', 'debit', or 'credit', ALWAYS use 'transactions' table.
3. If user mentions 'flag', use 'transactions.status' or 'transactions.flag_reason'.
4. USE 'username' for names and 'user_id' for IDs. NEVER use 'name' or 'id'.
5. JOIN users and transactions on 'user_id'.
6. Use UPPER() and LIKE with % for all string comparisons.
"""
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print("Hardcore cleaned all domain configs. Removed all legacy hallucinations.")

if __name__ == "__main__":
    hardcore_clean()
