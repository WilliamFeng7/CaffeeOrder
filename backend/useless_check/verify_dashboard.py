
import requests

# Base URL - Updated to include /api/v1
BASE_URL = "http://localhost:8000/api/v1"

# Admin credentials (assumed from previous conversations or seed data)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin_password" # Replace with actual password if known, otherwise try common ones or check seed script

def verify_dashboard_api():
    # 1. Login to get token
    try:
        login_response = requests.post(f"{BASE_URL}/login/access-token", data={
            "username": ADMIN_USERNAME,
            "password": "password" # Trying 'password' as it's common in seed scripts
        })
        login_response.raise_for_status()
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful.")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # 2. Get Dashboard Stats
    try:
        stats_response = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
        stats_response.raise_for_status()
        data = stats_response.json()
        
        # 3. Verify Trend Data
        trend = data["operations"]["trend"]
        print(f"Trend data length: {len(trend)}")
        
        if len(trend) != 24:
            print("FAILURE: Trend data should have length 24.")
        else:
            print("SUCCESS: Trend data has length 24.")
            
        print("Trend Data Sample:")
        for item in trend:
            print(f"Hour: {item['hour']}, Orders: {item['orders']}, Revenue: {item['revenue']}")
            
    except Exception as e:
        print(f"Stats request failed: {e}")

if __name__ == "__main__":
    verify_dashboard_api()
