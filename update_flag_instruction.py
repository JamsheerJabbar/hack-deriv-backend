import json
import os

domains_path = r'c:\Users\josea\Desktop\nl2sql\app\data\domains'
files = ['general.json', 'compliance.json', 'risk.json', 'operations.json', 'security.json']

def add_flag_reason_instruction():
    for filename in files:
        path = os.path.join(domains_path, filename)
        if not os.path.exists(path): continue
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        sql_prompt = data['prompts'].get('sql', '')
        flag_instruction = "\n14. FLAG REASON: The 'flag_reason' column is located in the 'transactions' table. NEVER assume there is a separate 'flags' table."
        
        if flag_instruction not in sql_prompt:
            data['prompts']['sql'] = sql_prompt + flag_instruction
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    print("Added Flag Reason instruction to all domain SQL prompts.")

if __name__ == "__main__":
    add_flag_reason_instruction()
