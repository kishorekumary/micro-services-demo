#!/usr/bin/env python3
"""
Test script for authentication system
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_authentication():
    print("🧪 Testing Authentication System")
    print("=" * 50)
    
    # Test 1: Login with admin credentials
    print("\n1. Testing admin login...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("✅ Admin login successful!")
            print(f"   Token: {token[:20]}...")
            
            # Test 2: Access protected route
            print("\n2. Testing protected route access...")
            headers = {"Authorization": f"Bearer {token}"}
            
            me_response = requests.get(f"{BASE_URL}/me", headers=headers)
            if me_response.status_code == 200:
                user_data = me_response.json()
                print("✅ Protected route access successful!")
                print(f"   User: {user_data['full_name']} ({user_data['username']})")
                
                # Test 3: Create order with authentication
                print("\n3. Testing order creation with auth...")
                order_data = {
                    "item": "Test Item",
                    "quantity": "1",
                    "price": "99.99"
                }
                
                create_response = requests.post(f"{BASE_URL}/create_order", 
                                              data=order_data, headers=headers)
                if create_response.status_code == 200:
                    order_result = create_response.json()
                    print("✅ Order creation successful!")
                    print(f"   Order ID: {order_result['order_id']}")
                else:
                    print(f"❌ Order creation failed: {create_response.status_code}")
                    print(f"   Error: {create_response.text}")
                    
                # Test 4: Search orders with authentication
                print("\n4. Testing order search with auth...")
                search_response = requests.get(f"{BASE_URL}/search?q=Test", headers=headers)
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    print("✅ Order search successful!")
                    print(f"   Results: {len(search_results.get('results', []))} orders found")
                else:
                    print(f"❌ Order search failed: {search_response.status_code}")
                    print(f"   Error: {search_response.text}")
                    
            else:
                print(f"❌ Protected route access failed: {me_response.status_code}")
                print(f"   Error: {me_response.text}")
                
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test 5: Test registration
    print("\n5. Testing user registration...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    
    try:
        register_response = requests.post(f"{BASE_URL}/register", json=register_data)
        if register_response.status_code == 200:
            print("✅ User registration successful!")
            
            # Test login with new user
            print("\n6. Testing login with new user...")
            new_login_data = {
                "username": "testuser",
                "password": "testpass123"
            }
            
            new_login_response = requests.post(f"{BASE_URL}/login", json=new_login_data)
            if new_login_response.status_code == 200:
                print("✅ New user login successful!")
            else:
                print(f"❌ New user login failed: {new_login_response.status_code}")
                
        else:
            print(f"⚠️ User registration failed (might already exist): {register_response.status_code}")
            
    except Exception as e:
        print(f"❌ Registration test error: {e}")
    
    # Test 6: Test unauthorized access
    print("\n7. Testing unauthorized access...")
    try:
        unauth_response = requests.get(f"{BASE_URL}/search?q=test")
        if unauth_response.status_code == 401:
            print("✅ Unauthorized access properly blocked!")
        else:
            print(f"⚠️ Unexpected response for unauthorized access: {unauth_response.status_code}")
    except Exception as e:
        print(f"❌ Unauthorized access test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Authentication system test completed!")

if __name__ == "__main__":
    test_authentication()
