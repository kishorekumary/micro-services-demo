#!/usr/bin/env python3
"""
Debug script to test backend connectivity and authentication
"""
import requests
import json
import time

def test_backend():
    print("🔍 Backend Debug Test")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if backend is responding
    print("\n1. Testing backend connectivity...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not reachable. Make sure Docker containers are running.")
        print("   Run: docker-compose up --build")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 2: Check login endpoint specifically
    print("\n2. Testing login endpoint...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # Test with JSON content type
        print("   Trying JSON request...")
        response = requests.post(
            f"{base_url}/login", 
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            token_data = response.json()
            print(f"   Token received: {token_data.get('access_token', 'N/A')[:20]}...")
        elif response.status_code == 405:
            print("❌ Method Not Allowed - This suggests the endpoint expects a different method or content type")
        elif response.status_code == 422:
            print("❌ Validation Error - Check the request format")
        else:
            print(f"❌ Login failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
    
    # Test 3: Check available endpoints
    print("\n3. Checking available endpoints...")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            print("   Available endpoints:")
            for path, methods in paths.items():
                for method in methods.keys():
                    print(f"     {method.upper()} {path}")
        else:
            print("   Could not retrieve endpoint information")
    except Exception as e:
        print(f"   Error retrieving endpoints: {e}")
    
    # Test 4: Test with form data (alternative)
    print("\n4. Testing login with form data...")
    try:
        response = requests.post(
            f"{base_url}/login",
            data=login_data,  # Using form data instead of JSON
            timeout=10
        )
        print(f"   Form data status: {response.status_code}")
        if response.status_code != 405:
            print(f"   Form data response: {response.text}")
    except Exception as e:
        print(f"   Form data test error: {e}")

if __name__ == "__main__":
    test_backend()
