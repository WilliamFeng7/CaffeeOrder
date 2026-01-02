import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login_admin():
    try:
        data = {
            "username": "admin_test", # Uses credentials from stress_test.py
            "password": "AdminPass123!@#"
        }
        response = requests.post(f"{BASE_URL}/login/access-token", data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def verify_orders(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{BASE_URL}/admin/orders", headers=headers)
        if response.status_code == 200:
            print("[\u2713] Order API Fixed: Successfully retrieved orders.")
            orders = response.json()
            print(f"    Retrieved {len(orders)} orders.")
            if len(orders) > 0:
                print(f"    First order user_id: {orders[0].get('user_id')}")
        else:
            print(f"[\u2717] Order API Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[\u2717] Order API Exception: {e}")

def verify_user_validation(token):
    headers = {"Authorization": f"Bearer {token}"}
    # Try to create user with weak password
    data = {
        "username": "testuser_weak",
        "password": "123", 
        "role": "student",
        "balance": 50000
    }
    try:
        response = requests.post(f"{BASE_URL}/admin/users", json=data, headers=headers)
        if response.status_code == 400: # Expected bad request
            print(f"[\u2713] User Validation Working: Caught weak password - {response.json()['detail']}")
        elif response.status_code == 200:
             print("[\u2717] User Validation FAILED: Weak password accepted!")
        else:
             print(f"[\u2717] User Validation Unexpected: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[\u2717] User Validation Exception: {e}")

if __name__ == "__main__":
    print("--- Verifying Admin Panel Fixes ---")
    token = login_admin()
    if token:
        verify_orders(token)
        verify_user_validation(token)
    else:
        print("Skipping tests due to login failure.")
