import requests
import json

def test_alert_metric():
    url = "http://localhost:8080/alert"
    payload = {
        "query": "Alert me if there are more than 3 failed transactions in 60 seconds",
        "domain": "risk"
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Testing Alert API at {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error Response: {response.text}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_alert_metric()
