import random
import time
import json
from datetime import datetime
from threading import Thread

EVENT_FILE = "events.jsonl"
event_id = 0

def write_event(event_type, data):
    global event_id
    event_id += 1
    
    event = {
        "id": event_id,
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(EVENT_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
    
    print(f"[EVENT] {event_type} → {data}")

# ================= USERS (every ~1 hour) =================

def generate_users():
    while True:
        user = {
            "user_id": random.randint(1, 10000),
            "name": f"user_{random.randint(1000,9999)}"
        }
        write_event("user", user)
        time.sleep(3600)   # 1 hour (for demo you can reduce to 30s)

# ================= LOGIN EVENTS (2–10 sec) =================

def generate_logins():
    while True:
        login = {
            "user_id": random.randint(1, 100),
            "status": random.choice(["success", "failed"])
        }
        write_event("login", login)
        time.sleep(random.uniform(2, 10))

# ================= TRANSACTIONS (1–4 sec) =================

def generate_transactions():
    while True:
        txn = {
            "user_id": random.randint(1, 100),
            "amount": random.randint(100, 5000),
            "status": random.choice(["success", "failed"])
        }
        write_event("transaction", txn)
        time.sleep(random.uniform(1, 4))


# ================= KYC EVENTS (every 10–20 sec) =================

def generate_kyc_events():
    kyc_statuses = ["pending", "approved", "rejected"]
    weights = [0.4, 0.45, 0.15]  # realistic distribution
    
    while True:
        user_id = random.randint(1, 100)  # assume user_id range
        
        status = random.choices(kyc_statuses, weights=weights)[0]
        
        kyc_event = {
            "user_id": user_id,
            "kyc_status": status
        }
        
        write_event("kyc", kyc_event)
        
        time.sleep(random.uniform(10, 20))

# ================= RUN ALL =================

if __name__ == "__main__":
    Thread(target=generate_users).start()
    Thread(target=generate_logins).start()
    Thread(target=generate_transactions).start()
