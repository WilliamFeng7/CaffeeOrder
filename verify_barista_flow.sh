#!/bin/bash

# 1. Login
echo "Logging in as Barista..."
TOKEN_RESP=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=barista&password=barista123")

TOKEN=$(echo $TOKEN_RESP | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Login failed: $TOKEN_RESP"
    exit 1
fi

echo "Login Success. Token: $TOKEN"

# 2. List Orders (using Admin endpoint as KDS likely uses that or similar)
# Checking api.ts from Barista app: it uses /admin/orders
echo "Fetching Orders..."
ORDERS_RESP=$(curl -s -X GET "http://localhost:8000/api/v1/admin/orders" \
    -H "Authorization: Bearer $TOKEN")

echo "Orders Response: $ORDERS_RESP"

# Extract First Order ID (assuming there is one from Scenario B)
ORDER_ID=$(echo $ORDERS_RESP | grep -o '"id":[0-9]*' | head -n 1 | cut -d':' -f2)

if [ -z "$ORDER_ID" ]; then
    echo "No orders found."
    # Can't complete if no order.
    exit 0
fi

echo "Found Order ID: $ORDER_ID"

# 3. Complete Order
echo "Completing Order #$ORDER_ID..."
COMPLETE_RESP=$(curl -s -X PUT "http://localhost:8000/api/v1/admin/orders/$ORDER_ID/status?status=completed" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

echo "Complete Response: $COMPLETE_RESP"

# 4. Verify Status
echo "Verifying Status..."
VERIFY_RESP=$(curl -s -X GET "http://localhost:8000/api/v1/admin/orders" \
    -H "Authorization: Bearer $TOKEN")

# Check if status is completed
echo "Updated Orders: $VERIFY_RESP"
