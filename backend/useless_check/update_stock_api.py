import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USER = "admin_test"
ADMIN_PASS = "AdminPass123!@#"

def update_stock():
    # 1. Login
    print("Logging in as admin...")
    resp = requests.post(f"{BASE_URL}/login/access-token", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Products
    print("Fetching products...")
    resp = requests.get(f"{BASE_URL}/admin/products", headers=headers)
    if resp.status_code != 200:
        print(f"Get products failed: {resp.text}")
        sys.exit(1)
        
    products = resp.json()
    print(f"Found {len(products)} products.")
    
    # 3. Update each
    for p in products:
        p_id = p["id"]
        name = p["name"]
        print(f"Updating {name} (ID: {p_id})...")
        
        update_data = {
            "inventory_count": 1000
        }
        
        put_resp = requests.put(f"{BASE_URL}/admin/products/{p_id}", headers=headers, json=update_data)
        if put_resp.status_code != 200:
             print(f"Update failed for {name}: {put_resp.text}")
        else:
             print(f"Updated {name} stock to 1000")

if __name__ == "__main__":
    update_stock()
