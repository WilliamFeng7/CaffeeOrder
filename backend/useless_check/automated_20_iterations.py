#!/usr/bin/env python3
"""
Automated 20-Iteration Testing Script
Creates 20 test users and products, tests order flow, then cleans up
"""
import sys
import os
import uuid
import requests
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, MenuItem, Order, UserRole
from app.core import security, timezone

BASE_URL = "http://localhost:8000/api/v1"

def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/login/access-token",
        data={"username": "admin", "password": "password"}
    )
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return None
    return response.json()["access_token"]

def run_iteration(iteration_num, admin_token):
    """Run a single test iteration"""
    print(f"\n{'='*60}")
    print(f"🔄 ITERATION {iteration_num}/20")
    print(f"{'='*60}\n")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. Create test user
    user_data = {
        "username": f"test_user_{iteration_num:02d}",
        "password": f"Test@Pass{iteration_num:02d}",
        "name": f"Test User {iteration_num:02d}",
        " email": f"testuser{iteration_num:02d}@test.com",
        "phone": f"139{iteration_num:08d}",
        "role": "student",
        "balance": 50000  # 500 Yuan
    }
    
    print(f"📝 Creating user: {user_data['username']}")
    response = requests.post(
        f"{BASE_URL}/admin/users",
        json=user_data,
        headers=headers
    )
    
    if response.status_code == 200:
        user = response.json()
        print(f"✅ User created: ID={user['id']}, Balance=¥{user['balance']/100:.2f}")
    else:
        print(f"❌ User creation failed: {response.status_code} - {response.text}")
        return False
    
    # 2. Create test product
    product_data = {
        "name": f"Test Product {iteration_num:02d}",
        "name_cn": f"测试商品 {iteration_num:02d}",
        "description": f"Test product created in iteration {iteration_num}",
        "price": 1500 + (iteration_num * 100),  # Variable pricing
        "category": ["coffee", "fruit", "bakery"][iteration_num % 3],
        "is_active": True,
        "is_recommend": iteration_num % 5 == 0,  # Every 5th iteration
        "inventory_count": 100
    }
    
    print(f"📦 Creating product: {product_data['name']}")
    response = requests.post(
        f"{BASE_URL}/admin/products",
        json=product_data,
        headers=headers
    )
    
    if response.status_code == 200:
        product = response.json()
        print(f"✅ Product created: ID={product['id']}, Price=¥{product['price']/100:.2f}")
    else:
        print(f"❌ Product creation failed: {response.status_code} - {response.text}")
        return False
    
    # 3. Test user login
    print(f"🔐 Testing user login...")
    response = requests.post(
        f"{BASE_URL}/login/access-token",
        data={"username": user_data["username"], "password": user_data["password"]}
    )
    
    if response.status_code == 200:
        user_token = response.json()["access_token"]
        print(f"✅ User logged in successfully")
    else:
        print(f"❌ User login failed: {response.text}")
        return False
    
    # 4. Get user profile and verify balance
    user_headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=user_headers)
    
    if response.status_code == 200:
        profile = response.json()
        print(f"✅ User profile retrieved: Balance=¥{profile['balance']/100:.2f}")
    else:
        print(f"❌ Failed to get user profile: {response.text}")
        return False
    
    # 5. Get menu and verify new product appears
    response = requests.get(f"{BASE_URL}/menu/")
    
    if response.status_code == 200:
        menu = response.json()
        new_product_found = any(p['id'] == product['id'] for p in menu)
        print(f"✅ Menu retrieved: {len(menu)} products, New product visible: {new_product_found}")
    else:
        print(f"❌ Failed to get menu: {response.text}")
        return False
    
    # 6. Test order creation (purchase flow)
    if len(menu) >= 2:
        order_data = {
            "items": [
                {"menu_item_id": menu[0]['id'], "spec": {"temp": "hot", "sugar": "normal"}},
                {"menu_item_id": menu[1]['id'], "spec": {"temp": "cold", "sugar": "less"}}
            ]
        }
        
        print(f"🛒 Creating order with 2 items...")
        response = requests.post(
            f"{BASE_URL}/orders/",
            json=order_data,
            headers=user_headers
        )
        
        if response.status_code == 200:
            order = response.json()
            print(f"✅ Order created successfully!")
            print(f"   Order#: {order['order_no']}")
            print(f"   Pickup Code: {order['pickup_code']}")
            print(f"   Total: ¥{order['total_amount']/100:.2f}")
            print(f"   Status: {order['status']}")
            
            # 7. Verify balance deduction
            response = requests.get(f"{BASE_URL}/users/me", headers=user_headers)
            if response.status_code == 200:
                new_profile = response.json()
                expected_balance = profile['balance'] - order['total_amount']
                actual_balance = new_profile['balance']
                balance_correct = actual_balance == expected_balance
                
                print(f"✅ Balance verification:")
                print(f"   Before: ¥{profile['balance']/100:.2f}")
                print(f"   Deducted: ¥{order['total_amount']/100:.2f}")
                print(f"   Expected: ¥{expected_balance/100:.2f}")
                print(f"   Actual: ¥{actual_balance/100:.2f}")
                print(f"   {'✅ CORRECT' if balance_correct else '❌ MISMATCH'}")
                
                if not balance_correct:
                    print(f"⚠️  CRITICAL: Balance calculation error detected!")
                    return False
        else:
            print(f"❌ Order creation failed: {response.status_code} - {response.text}")
            return False
    
    print(f"\n✅ Iteration {iteration_num} completed successfully!\n")
    return True

def cleanup_test_data(admin_token):
    """Delete all test users and products"""
    print(f"\n{'='*60}")
    print("🧹 CLEANUP: Deleting test data...")
    print(f"{'='*60}\n")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get all users
    response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        test_users = [u for u in users if u['username'].startswith('test_user_')]
        
        print(f"Found {len(test_users)} test users to delete")
        for user in test_users:
            response = requests.delete(
                f"{BASE_URL}/admin/users/{user['id']}",
                headers=headers
            )
            if response.status_code == 200:
                print(f"✅ Deleted user: {user['username']}")
            else:
                print(f"❌ Failed to delete user {user['username']}: {response.text}")
    
    # Get all products
    response = requests.get(f"{BASE_URL}/admin/products", headers=headers)
    if response.status_code == 200:
        products = response.json()
        test_products = [p for p in products if p['name'].startswith('Test Product')]
        
        print(f"\nFound {len(test_products)} test products to delete")
        for product in test_products:
            response = requests.delete(
                f"{BASE_URL}/admin/products/{product['id']}",
                headers=headers
            )
            if response.status_code == 200:
                print(f"✅ Deleted product: {product['name']}")
            else:
                print(f"❌ Failed to delete product {product['name']}: {response.text}")
    
    print(f"\n✅ Cleanup completed!\n")

def main():
    """Main test execution"""
    print("="*60)
    print("🚀 Starting 20-Iteration Automated Test")
    print("="*60)
    print()
    print("This script will:")
    print("  1. Create 20 test users (test_user_01 to test_user_20)")
    print("  2. Create 20 test products (Test Product 01 to Test Product 20)")
    print("  3. Test login, menu retrieval, and order creation for each")
    print("  4. Verify balance calculations")
    print("  5. Clean up all test data")
    print()
    
    # Get admin token
    print("🔑 Authenticating as admin...")
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Failed to get admin token. Exiting.")
        return
    print("✅ Admin authenticated\n")
    
    # Run 20 iterations
    successful_iterations = 0
    failed_iterations = []
    
    for i in range(1, 21):
        try:
            if run_iteration(i, admin_token):
                successful_iterations += 1
            else:
                failed_iterations.append(i)
                print(f"⚠️  Iteration {i} had errors\n")
        except Exception as e:
            print(f"❌ Iteration {i} crashed: {str(e)}\n")
            failed_iterations.append(i)
        
        # Small delay between iterations
        time.sleep(0.5)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Iterations: 20")
    print(f"Successful: {successful_iterations}")
    print(f"Failed: {len(failed_iterations)}")
    if failed_iterations:
        print(f"Failed iterations: {', '.join(map(str, failed_iterations))}")
    print()
    
    # Cleanup
    cleanup_test_data(admin_token)
    
    print("="*60)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    main()
