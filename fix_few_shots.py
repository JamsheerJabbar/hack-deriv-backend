import json
import os

file_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains\general.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Clear existing few-shots and add high-quality relevant ones
data['few_shots'] = [
    {
        "question": "Show me the usernames of users with instrument AMZN",
        "sql": "SELECT DISTINCT u.username FROM users u JOIN transactions t ON u.user_id = t.user_id WHERE UPPER(t.instrument) LIKE '%AMZN%';",
        "explanation": "Joins users and transactions to find usernames of users who traded Amazon stock using robust partial matching."
    },
    {
        "question": "Show failed login attempts for users with HIGH risk level",
        "sql": "SELECT le.*, u.username FROM login_events le JOIN users u ON le.user_id = u.user_id WHERE UPPER(le.status) LIKE '%FAILED%' AND UPPER(u.risk_level) LIKE '%HIGH%';",
        "explanation": "Finds all failed logins specifically for users marked as high risk using case-insensitive partial matching."
    },
    {
        "question": "What is the average age of PEP users?",
        "sql": "SELECT AVG(age) FROM users WHERE is_pep = 1;",
        "explanation": "Calculates average age for politically exposed persons (is_pep is numeric 0/1)."
    },
    {
        "question": "Find trades over 10000 USD for users from Singapore",
        "sql": "SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.user_id WHERE t.amount_usd > 10000 AND UPPER(t.txn_type) LIKE '%TRADE%' AND UPPER(u.country) LIKE '%SINGAPORE%';",
        "explanation": "Retrieves high-value trades for users in Singapore."
    },
    {
        "question": "List all unique instruments traded by user 'john_smith'",
        "sql": "SELECT DISTINCT instrument FROM transactions t JOIN users u ON t.user_id = u.user_id WHERE UPPER(u.username) LIKE '%JOHN_SMITH%' AND instrument IS NOT NULL;",
        "explanation": "Shows assets a specific user has interacted with using robust string matching."
    }
]

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Updated few-shot examples in general.json for better JOIN and column accuracy.")
