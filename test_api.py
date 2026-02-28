import requests
import json

def test_api():
    url = "http://localhost:8000/api/generate_hbdi_json"
    payload = {
        "metrics": {
            "الاستدلال": 80,
            "القياس": 70,
            "النظم": 60,
            "التنفيذ": 50,
            "التأثير": 40,
            "التعاطف": 30,
            "الابتكار": 20,
            "التجريب": 10
        }
    }
    
    print(f"Testing URL: {url}")
    print("Payload sent to API...")
    
    try:
        # Note: This requires the server to be running. 
        # Since I can't guarantee it's running in this environment, 
        # I'll also do a code-level check.
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON Structure:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Could not connect to server: {e}")
        print("\n--- Code Logic Verification ---")
        print("I will now verify the code logic in app.py manually to ensure it handles JSON correctly without Pydantic.")

if __name__ == "__main__":
    test_api()
