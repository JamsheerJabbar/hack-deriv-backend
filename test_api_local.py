import requests
import json
import sys

def test_query():
    url = "http://localhost:8080/api/v1/query"
    payload = {
        "query": "Show me 5 users",
        "domain": "general"
    }
    
    print(f"Testing API at: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse Status:", data.get("status"))
            print("Generated SQL:", data.get("sql"))
            print("Error:", data.get("error"))
            results = data.get("results")
            if results:
                print(f"Result Count: {len(results)}")
                print("First Result:", results[0])
            else:
                print("Results: None or Empty")
                
            print("\nFull JSON:")
            print(json.dumps(data, indent=2))
        else:
            print(f"\n❌ ERROR: API request failed. Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to localhost:8080. Is the server running?")
    except Exception as e:
        print(f"\n❌ ERROR: An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    test_query()
