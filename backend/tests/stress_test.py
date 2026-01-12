import httpx
import time
import random
import string
import sys
import asyncio

BASE_URL = "http://localhost:80/api/v1"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def run_stress_test(iterations=10):
    print(f"Starting Stress Test: {iterations} iterations")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 0. Initial Setup: Login as Admin and Top Up
        print("Initial Setup: Topping up Admin account...")
        try:
            # Login Admin
            login_resp = await client.post("/login/access-token", data={
                "username": "admin",
                "password": "89129885"  # Using known persistent password
            })
            if login_resp.status_code == 200:
                token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Get ID (usually 1)
                me_resp = await client.get("/users/me", headers=headers)
                if me_resp.status_code == 200:
                    user_id = me_resp.json()["id"]
                    # Top up 1,000,000 cents (10,000 Yuan)
                    await client.post(f"/users/{user_id}/deposit", params={"amount": 1000000}, headers=headers)
                    # Verify
                    me_resp = await client.get("/users/me", headers=headers)
                    print(f"  > Admin topped up. Current Balance: {me_resp.json()['balance']}")
            else:
                print(f"  > Admin login failed during setup: {login_resp.status_code}")
                
        except Exception as e:
            print(f"  > Warning: Top up failed ({e}), checking balance might fail later.")

        # Loop
        for i in range(1, iterations + 1):
            print(f"\n[Iteration {i}/{iterations}]")
            try:
                # 1. Login (simulating fresh user session)
                username = "admin"
                password = "89129885"

                print(f"  > Logging in as {username}...")
                login_resp = await client.post("/login/access-token", data={
                    "username": username,
                    "password": password
                })
                
                if login_resp.status_code != 200:
                    print(f"    FAILED: Login ({login_resp.status_code}) - {login_resp.text}")
                    fail_count += 1
                    continue
                    
                token = login_resp.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Check balance
                me_resp = await client.get("/users/me", headers=headers)
                balance = me_resp.json().get('balance', 0)
                print(f"    Balance: {balance}")

                # 2. Get Menu
                print("  > Fetching menu...")
                menu_resp = await client.get("/menu/", headers=headers)
                if menu_resp.status_code != 200:
                    print(f"    FAILED: Menu fetch ({menu_resp.status_code})")
                    fail_count += 1
                    continue
                
                menu_items = menu_resp.json()
                if not menu_items:
                    print("    FAILED: Menu is empty")
                    fail_count += 1
                    continue
                    
                # 3. Place Order
                item = random.choice(menu_items)
                print(f"  > Ordering {item['name']} (Price: {item['price']})...")
                
                if balance < item['price']:
                     print(f"    WARNING: Balance {balance} < Price {item['price']}. Order will fail.")

                order_payload = {
                    "items": [
                        {
                            "menu_item_id": item["id"],
                            "spec": {"size": "Regular", "sugar": "Regular", "temp": "Hot"}
                        }
                    ]
                }
                
                order_resp = await client.post("/orders/", json=order_payload, headers=headers)
                if order_resp.status_code != 200:
                    print(f"    FAILED: Place order ({order_resp.status_code}) - {order_resp.text}")
                    fail_count += 1
                    continue
                
                order_data = order_resp.json()
                order_id = order_data.get("id") or order_data.get("order_no")
                print(f"    Order placed: {order_id}")
                
                # 4. Check Status (simulate polling)
                print("  > Checking status...")
                status_resp = await client.get("/orders/me", headers=headers)
                if status_resp.status_code != 200:
                    print(f"    FAILED: Status check ({status_resp.status_code})")
                    fail_count += 1
                    continue
                
                print("  > Iteration SUCCESS")
                success_count += 1
                
            except Exception as e:
                print(f"  > EXCEPTION: {e}")
                fail_count += 1
            
            # Brief pause
            await asyncio.sleep(0.5)

    print("-" * 50)
    print(f"Test Complete.")
    print(f"Success: {success_count}")
    print(f"Failed:  {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_stress_test(iterations=60))
