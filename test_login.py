#!/usr/bin/env python3
"""
Quick test to verify login and get JWT token
"""
import requests
import json

def test_login():
    print("🔐 Testing Login Process")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test login
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("1. Attempting login...")
        response = requests.post(f"{base_url}/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            
            print("✅ Login successful!")
            print(f"📄 Full response: {json.dumps(token_data, indent=2)}")
            print(f"\n🎯 JWT Token to use in Swagger:")
            print(f"   {token}")
            print(f"\n📋 Copy this token and paste it in Swagger's Authorize dialog")
            print(f"   (Don't include 'Bearer' prefix - just the token)")
            
            # Test the token
            print(f"\n2. Testing token with /me endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{base_url}/me", headers=headers)
            
            if me_response.status_code == 200:
                user_data = me_response.json()
                print("✅ Token works!")
                print(f"   User: {user_data['full_name']} ({user_data['username']})")
            else:
                print(f"❌ Token test failed: {me_response.status_code}")
                print(f"   Error: {me_response.text}")
                
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure containers are running:")
        print("   docker-compose up")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()
