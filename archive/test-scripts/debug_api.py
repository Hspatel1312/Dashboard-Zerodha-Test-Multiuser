import requests
import json

# Test the investment status API directly
headers = {
    'Authorization': 'Bearer test_token_replace_with_actual',  # User should replace
    'Content-Type': 'application/json'
}

try:
    # Test investment status
    response = requests.get('http://localhost:8000/api/investment/status', headers=headers)
    print("Investment Status API Response:")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        min_investment = data.get('data', {}).get('min_investment') or data.get('min_investment')
        print(f"\nExtracted min_investment: {min_investment}")
    else:
        print(f"Error: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test investment requirements
    response2 = requests.get('http://localhost:8000/api/investment/requirements', headers=headers)
    print("Investment Requirements API Response:")
    print(f"Status Code: {response2.status_code}")
    if response2.status_code == 200:
        data2 = response2.json()
        print(json.dumps(data2, indent=2))
        min_req = data2.get('data', {}).get('minimum_investment', {}).get('minimum_investment') or data2.get('minimum_investment', {}).get('minimum_investment')
        print(f"\nExtracted minimum_investment: {min_req}")
    else:
        print(f"Error: {response2.text}")

except Exception as e:
    print(f"Error: {e}")
    print("\nNote: You need to replace 'test_token_replace_with_actual' with a real auth token")
    print("You can get it from localStorage in the browser or the user2_token.json file")