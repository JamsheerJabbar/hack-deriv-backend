import sqlite3
import random
import uuid
import json
from datetime import datetime, timedelta

# Configuration
DB_NAME = "derivinsight_hackathon.db"
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 1, 25)

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def create_schema(conn):
    cursor = conn.cursor()
    cursor.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS transactions;
    DROP TABLE IF EXISTS login_events;
    DROP TABLE IF EXISTS alert_rules;
    DROP TABLE IF EXISTS alerts;
    DROP TABLE IF EXISTS audit_logs;
    DROP TABLE IF EXISTS dashboards;
    DROP TABLE IF EXISTS query_history;

    CREATE TABLE users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        full_name TEXT,
        country TEXT,
        phone TEXT,
        date_of_birth DATE,
        kyc_status TEXT,
        kyc_verified_at DATETIME,
        kyc_expiry_date DATETIME,
        risk_level TEXT,
        risk_score INTEGER,
        is_pep BOOLEAN DEFAULT 0,
        account_status TEXT,
        created_at DATETIME,
        updated_at DATETIME
    );

    CREATE TABLE transactions (
        txn_id TEXT PRIMARY KEY,
        user_id TEXT,
        txn_type TEXT,
        instrument TEXT,
        amount REAL,
        currency TEXT,
        amount_usd REAL,
        status TEXT,
        flag_reason TEXT,
        payment_method TEXT,
        external_ref TEXT,
        ip_address TEXT,
        created_at DATETIME,
        processed_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

    CREATE TABLE login_events (
        event_id TEXT PRIMARY KEY,
        user_id TEXT,
        email_attempted TEXT,
        ip_address TEXT,
        country TEXT,
        city TEXT,
        device_type TEXT,
        device_fingerprint TEXT,
        user_agent TEXT,
        status TEXT,
        failure_reason TEXT,
        created_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );

    CREATE TABLE alert_rules (
        rule_id TEXT PRIMARY KEY,
        rule_name TEXT,
        rule_type TEXT,
        condition TEXT,
        severity TEXT,
        is_active BOOLEAN,
        created_at DATETIME
    );

    CREATE TABLE alerts (
        alert_id TEXT PRIMARY KEY,
        rule_name TEXT,
        rule_id TEXT,
        user_id TEXT,
        txn_id TEXT,
        severity TEXT,
        status TEXT,
        details TEXT,
        assigned_to TEXT,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(txn_id) REFERENCES transactions(txn_id),
        FOREIGN KEY(rule_id) REFERENCES alert_rules(rule_id)
    );

    CREATE TABLE audit_logs (
        log_id TEXT PRIMARY KEY,
        actor_id TEXT,
        action TEXT,
        resource_type TEXT,
        resource_id TEXT,
        query_text TEXT,
        ip_address TEXT,
        created_at DATETIME
    );

    CREATE TABLE dashboards (
        dashboard_id TEXT PRIMARY KEY,
        name TEXT,
        owner_id TEXT,
        widgets TEXT,
        layout TEXT,
        is_deployed BOOLEAN,
        deploy_url TEXT,
        refresh_interval INTEGER,
        created_at DATETIME,
        deployed_at DATETIME,
        FOREIGN KEY(owner_id) REFERENCES users(user_id)
    );

    CREATE TABLE query_history (
        history_id TEXT PRIMARY KEY,
        user_id TEXT,
        natural_query TEXT,
        sql_query TEXT,
        execution_time_ms INTEGER,
        status TEXT,
        created_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """)
    conn.commit()

# --- Helpers ---
def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def weighted_random(choices, weights):
    return random.choices(choices, weights=weights)[0]

def generate_ip():
    return f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

# --- Data Generation ---

def generate_data():
    conn = get_db_connection()
    create_schema(conn)
    cursor = conn.cursor()

    print("🌱 Generating Alert Rules...")
    rules = [
        ('RULE-001', 'Large Transaction', 'THRESHOLD', 'amount_usd > 50000', 'HIGH', 1),
        ('RULE-002', 'Velocity Alert', 'VELOCITY', '25 trades in 5 mins', 'MEDIUM', 1),
        ('RULE-003', 'Structuring Detection', 'PATTERN', 'Multiple txns < 10k', 'CRITICAL', 1),
        ('RULE-004', 'Failed Auth Spike', 'SECURITY', '3 fails in 10 mins', 'HIGH', 1),
        ('RULE-005', 'New Geo Login', 'SECURITY', 'Country mismatch', 'MEDIUM', 1),
        ('RULE-006', 'Withdrawal Pattern', 'PATTERN', 'Rapid withdrawal', 'HIGH', 1),
        ('RULE-007', 'Off-Hours Activity', 'SECURITY', 'Activity 00:00-05:00', 'LOW', 1),
        ('RULE-008', 'Dormant Account Activity', 'RISK', 'Activity after 90 days', 'MEDIUM', 1),
        ('RULE-009', 'High Risk Country', 'COMPLIANCE', 'Country IN (IR, SY, KP)', 'HIGH', 1),
        ('RULE-010', 'Rapid Fund Movement', 'AML', 'Deposit then withdrawal', 'HIGH', 1),
        ('RULE-011', 'Multi-Account Detection', 'SECURITY', 'Same IP/Fingerprint', 'HIGH', 1),
        ('RULE-012', 'Margin Call Alert', 'RISK', 'Margin < 50%', 'CRITICAL', 1),
    ]
    cursor.executemany("INSERT INTO alert_rules VALUES (?,?,?,?,?,?,?)", 
                       [(r[0], r[1], r[2], r[3], r[4], r[5], START_DATE.isoformat()) for r in rules])

    print("👥 Generating 500 Users...")
    countries = {
        'AE': 125, 'GB': 75, 'US': 60, 'DE': 40, 'SG': 40, 'IN': 35, 
        'FR': 25, 'HK': 20, 'AU': 20, 'JP': 15, 'RU': 10, 'CN': 10, 
        'NG': 8, 'PK': 7, 'IR': 3, 'SY': 2
    }
    
    user_list = []
    # Create Story Users First
    story_users = [
        ('USR-0001', 'ahmed.alrashid@example.ae', 'Ahmed Al-Rashid', 'AE', 'VERIFIED', 'LOW', 15, 0, 'ACTIVE'),
        ('USR-0042', 'john.smith@example.gb', 'John Smith', 'GB', 'VERIFIED', 'HIGH', 78, 1, 'ACTIVE'),
        ('USR-0099', 'maria.garcia@example.us', 'Maria Garcia', 'US', 'PENDING', 'MEDIUM', 45, 0, 'ACTIVE'),
        ('USR-0150', 'suspicious.user@example.ng', 'Suspicious User', 'NG', 'VERIFIED', 'HIGH', 85, 0, 'ACTIVE'),
        ('USR-0200', 'victim.user@example.de', 'Account Takeover Victim', 'DE', 'VERIFIED', 'MEDIUM', 40, 0, 'ACTIVE'),
        ('USR-0250', 'fraudster.user@example.ru', 'Multi-Account Fraudster', 'RU', 'VERIFIED', 'HIGH', 72, 0, 'SUSPENDED'),
        ('USR-0300', 'margin.user@example.sg', 'Margin Call User', 'SG', 'VERIFIED', 'MEDIUM', 55, 0, 'ACTIVE'),
        ('USR-0350', 'sanctioned.user@example.ir', 'Sanctioned Country User', 'IR', 'REJECTED', 'HIGH', 95, 0, 'FROZEN'),
    ]
    
    user_ids_created = set()
    for u_id, email, name, country, kyc, risk, score, pep, status in story_users:
        created = random_date(START_DATE, END_DATE - timedelta(days=60))
        verified = created + timedelta(days=random.randint(1, 7)) if kyc == 'VERIFIED' else None
        user_list.append((u_id, email, name, country, '555-0100', '1985-05-15', kyc, verified, None, risk, score, pep, status, created, created))
        user_ids_created.add(u_id)

    # Fill remaining 492
    rem_count = 500 - len(story_users)
    country_pool = []
    for c, count in countries.items():
        # Subtract already used in story users
        existing = sum(1 for su in story_users if su[3] == c)
        country_pool.extend([c] * (count - existing))
    
    # Handle others if count doesn't match exactly
    while len(country_pool) < rem_count:
        country_pool.append('GB')

    for i in range(rem_count):
        idx = 500 - rem_count + i + 1
        u_id = f'USR-{str(idx).zfill(4)}'
        if u_id in user_ids_created: continue
        
        country = country_pool[i]
        kyc = weighted_random(['VERIFIED', 'PENDING', 'REJECTED', 'EXPIRED'], [75, 18, 5, 2])
        status = weighted_random(['ACTIVE', 'SUSPENDED', 'FROZEN', 'CLOSED'], [94, 3, 1, 2])
        
        risk = 'LOW'
        score = random.randint(0, 30)
        if country in ['NG', 'PK', 'RU', 'CN']:
            risk = 'MEDIUM'
            score = random.randint(31, 60)
        if country in ['IR', 'SY']:
            risk = 'HIGH'
            score = random.randint(70, 100)
            
        pep = 1 if random.random() < 0.02 else 0
        if pep: 
            risk = 'HIGH'
            score = max(score, 70)

        created = random_date(START_DATE, END_DATE - timedelta(days=30))
        verified = created + timedelta(days=random.randint(1, 7)) if kyc == 'VERIFIED' else None
        
        user_list.append((u_id, f'user{idx}@example.com', f'Full Name {idx}', country, generate_ip(), '1990-01-01', kyc, verified, None, risk, score, pep, status, created, created))

    cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", user_list)
    conn.commit()

    print("💸 Generating 50,000 Transactions...")
    tx_types = ['TRADE', 'DEPOSIT', 'WITHDRAWAL', 'FEE', 'BONUS']
    tx_weights = [55, 20, 15, 8, 2]
    instruments = ['EUR/USD', 'GBP/USD', 'GOLD', 'BTC/USD', 'USD/JPY', 'ETH/USD', 'OIL', 'AAPL', 'TSLA', 'AED/USD']
    
    transactions = []
    for i in range(50000):
        t_id = f'TXN-{str(i+1).zfill(6)}'
        user = random.choice(user_list)
        u_id = user[0]
        u_country = user[3]
        u_risk = user[9]
        
        t_type = weighted_random(tx_types, tx_weights)
        inst = random.choice(instruments) if t_type == 'TRADE' else None
        
        # Amount logic
        if t_type == 'TRADE': amount = random.uniform(100, 50000)
        elif t_type == 'DEPOSIT': amount = random.uniform(100, 100000)
        else: amount = random.uniform(10, 1000)
        
        status = weighted_random(['COMPLETED', 'PENDING', 'FAILED', 'FLAGGED'], [85, 8, 4, 3])
        reason = None
        if amount > 50000:
            status = 'FLAGGED' if random.random() < 0.8 else 'COMPLETED'
            reason = 'Large transaction exceeds threshold'
        
        # Inject Story Patterns
        if u_id == 'USR-0150' and i < 10: # Structuring
             amount = random.uniform(9000, 9999)
             status = 'FLAGGED'
             reason = 'Potential structuring'
             
        created = random_date(user[13], END_DATE)
        proc = created + timedelta(minutes=random.randint(1, 60)) if status == 'COMPLETED' else None
        
        transactions.append((t_id, u_id, t_type, inst, amount, 'USD', amount, status, reason, 'CARD', str(uuid.uuid4()), generate_ip(), created, proc))
        
        if len(transactions) >= 5000:
            cursor.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", transactions)
            transactions = []
    
    if transactions:
        cursor.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", transactions)
    conn.commit()

    print("🔐 Generating 20,000 Login Events...")
    logins = []
    for i in range(20000):
        e_id = f'EVT-{str(i+1).zfill(5)}'
        user = random.choice(user_list)
        u_id = user[0]
        u_country = user[3]
        
        status = weighted_random(['SUCCESS', 'FAILED', 'BLOCKED', 'MFA_REQUIRED'], [85, 12, 2, 1])
        reason = weighted_random(['WRONG_PASSWORD', 'ACCOUNT_LOCKED', 'MFA_FAILED'], [60, 20, 20]) if status != 'SUCCESS' else None
        
        device = weighted_random(['DESKTOP', 'MOBILE', 'TABLET'], [45, 45, 10])
        created = random_date(user[13], END_DATE)
        
        ip = generate_ip() if random.random() < 0.1 else user[11] # 10% geo anomaly
        
        logins.append((e_id, u_id, user[1], ip, u_country, None, device, f"FP-{uuid.uuid4().hex[:8].upper()}", "Mozilla/5.0", status, reason, created))
        
        if len(logins) >= 5000:
            cursor.executemany("INSERT INTO login_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", logins)
            logins = []
            
    if logins:
        cursor.executemany("INSERT INTO login_events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", logins)
    conn.commit()

    print("🚨 Generating 500 Alerts...")
    alert_list = []
    for i in range(500):
        a_id = f'ALR-{str(i+1).zfill(4)}'
        user = random.choice(user_list)
        rule = random.choice(rules)
        
        status = weighted_random(['OPEN', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'], [35, 15, 40, 10])
        sev = rule[4]
        created = random_date(START_DATE, END_DATE)
        resolved = created + timedelta(days=random.randint(1, 3)) if status in ['RESOLVED', 'DISMISSED'] else None
        
        details = {"rule": rule[1], "user": user[2], "risk": user[9]}
        
        alert_list.append((a_id, rule[1], rule[0], user[0], None, sev, status, json.dumps(details), 'Analyst-01', resolved, 'Verified patterns', created))
    
    cursor.executemany("INSERT INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", alert_list)
    conn.commit()

    print("📝 Generating 10,000 Audit Logs...")
    logs = []
    actions = ['QUERY', 'VIEW', 'LOGIN', 'EXPORT', 'UPDATE', 'DELETE']
    resources = ['USER', 'TRANSACTION', 'ALERT', 'DASHBOARD', 'REPORT']
    for i in range(10000):
        l_id = f'LOG-{uuid.uuid4().hex[:8]}'
        user = random.choice(user_list)
        act = weighted_random(actions, [40, 25, 15, 10, 7, 3])
        res = random.choice(resources)
        created = random_date(START_DATE, END_DATE)
        logs.append((l_id, user[0], act, res, str(uuid.uuid4()), "User query text here", generate_ip(), created))
        
        if len(logs) >= 5000:
            cursor.executemany("INSERT INTO audit_logs VALUES (?,?,?,?,?,?,?,?)", logs)
            logs = []
    if logs:
        cursor.executemany("INSERT INTO audit_logs VALUES (?,?,?,?,?,?,?,?)", logs)
    conn.commit()

    print("📊 Generating Meta Tables...")
    cursor.execute("INSERT INTO dashboards VALUES ('DASH-001', 'Security Overview', 'USR-0001', '[]', '{}', 1, 'http://view', 60, ?, ?)", (START_DATE.isoformat(), START_DATE.isoformat()))
    
    conn.commit()
    conn.close()
    print(f"✨ COMPLETED: Database created at {DB_NAME}")

if __name__ == "__main__":
    generate_data()
