import json
import os

domains_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains'
files = ['general.json', 'compliance.json', 'risk.json', 'operations.json', 'security.json']

def update_activity_instruction():
    for filename in files:
        path = os.path.join(domains_path, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Update SQL prompt to include instruction about user activity
        sql_prompt = data['prompts'].get('sql', '')
        activity_instruction = "\n7. USER ACTIVITY: Any query about 'user activity', 'activity logs', or 'login frequency' MUST use the 'login_events' table."
        
        if activity_instruction not in sql_prompt:
            data['prompts']['sql'] = sql_prompt + activity_instruction
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print("Added User Activity instruction to all domain SQL prompts.")

if __name__ == "__main__":
    update_activity_instruction()
