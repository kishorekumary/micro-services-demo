#!/usr/bin/env python3
"""
Script to toggle JWT authentication on/off for debugging
"""
import os
import sys

def toggle_auth():
    env_file = "app/.env"
    
    if not os.path.exists(env_file):
        print(f"❌ Error: {env_file} not found!")
        return
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Find and toggle ENABLE_AUTH line
    auth_line_found = False
    for i, line in enumerate(lines):
        if line.startswith('ENABLE_AUTH='):
            current_value = line.strip().split('=')[1].lower()
            if current_value == 'true':
                lines[i] = 'ENABLE_AUTH=false  # Set to \'true\' to enable authentication for production\n'
                new_status = "DISABLED"
            else:
                lines[i] = 'ENABLE_AUTH=true  # Set to \'false\' to disable authentication for debugging\n'
                new_status = "ENABLED"
            auth_line_found = True
            break
    
    if not auth_line_found:
        print("❌ ENABLE_AUTH line not found in .env file!")
        return
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Authentication is now: {new_status}")
    print(f"📝 Updated {env_file}")
    
    if new_status == "DISABLED":
        print("\n🚫 DEBUG MODE ACTIVE:")
        print("   - All API endpoints are accessible without authentication")
        print("   - No need to login or use JWT tokens in Swagger")
        print("   - Any token will work in the 'Authorize' dialog")
        print("\n⚠️  Remember to enable auth for production!")
    else:
        print("\n🔐 PRODUCTION MODE ACTIVE:")
        print("   - All API endpoints require JWT authentication")
        print("   - Use /login endpoint to get JWT token")
        print("   - Click 'Authorize' in Swagger and paste token")
    
    print("\n🔄 Restart your containers to apply changes:")
    print("   docker-compose restart backend")

def show_status():
    env_file = "app/.env"
    
    if not os.path.exists(env_file):
        print(f"❌ Error: {env_file} not found!")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'ENABLE_AUTH=true' in content:
        print("🔐 Authentication: ENABLED")
        print("   All endpoints require JWT tokens")
    elif 'ENABLE_AUTH=false' in content:
        print("🚫 Authentication: DISABLED (Debug Mode)")
        print("   All endpoints are accessible without authentication")
    else:
        print("❓ Authentication status unclear - check ENABLE_AUTH in .env")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        toggle_auth()
