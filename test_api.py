import requests
import json

def test_query():
    url = "http://localhost:8000/api/v1/query"
    payload = {
        "query": "Show me all high risk users from the UAE"
    }
    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse:")
            print(json.dumps(data, indent=2))
            
            if data.get("results"):
                print(f"\nFound {len(data['results'])} results.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_query()
