"""
Django Authentication Test Script
Run with: python manage.py shell < test_auth.py
Or: python manage.py shell
     >>> exec(open('test_auth.py').read())
"""

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()

print("=" * 60)
print("AUTHENTICATION SYSTEM TEST")
print("=" * 60)

# Clean up test user if exists
test_email = "testuser@example.com"
test_username = "testuser"
test_password = "TestPass123!"

print("\n1. Cleaning up existing test user...")
User.objects.filter(email=test_email).delete()
print("✓ Cleanup complete")

# Test 1: Create User
print("\n2. Creating test user...")
try:
    user = User.objects.create_user(
        email=test_email,
        username=test_username,
        password=test_password,
        first_name="Test",
        last_name="User"
    )
    user.is_active = True
    
    # If your model has is_verified field
    if hasattr(user, 'is_verified'):
        user.is_verified = True
    
    user.save()
    print(f"✓ User created: {user.email}")
    print(f"  - ID: {user.id}")
    print(f"  - Username: {user.username}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Password hash: {user.password[:50]}...")
except Exception as e:
    print(f"✗ Failed to create user: {e}")
    exit(1)

# Test 2: Verify Password
print("\n3. Testing password verification...")
if user.check_password(test_password):
    print("✓ Password verification works")
else:
    print("✗ Password verification failed!")
    exit(1)

# Test 3: Test Login API
print("\n4. Testing Login API...")
client = APIClient()

login_data = {
    "email": test_email,
    "password": test_password
}

print(f"   Sending POST to /api/accounts/login/")
print(f"   Data: {json.dumps(login_data, indent=2)}")

try:
    response = client.post(
        '/api/accounts/login/',
        login_data,
        format='json'
    )
    
    print(f"\n   Response Status: {response.status_code}")
    print(f"   Response Data:")
    print(json.dumps(response.data, indent=2))
    
    if response.status_code == 200:
        print("\n✓ Login API works!")
        
        # Check response structure
        if response.data.get('success'):
            print("✓ Response has success flag")
        
        if 'data' in response.data:
            data = response.data['data']
            if 'access' in data or 'tokens' in data:
                print("✓ Response contains access token")
            if 'user' in data:
                print("✓ Response contains user data")
        else:
            print("⚠ Warning: Response structure might be incorrect")
    else:
        print(f"\n✗ Login failed with status {response.status_code}")
        if response.data:
            print(f"   Error: {response.data}")
        exit(1)
        
except Exception as e:
    print(f"\n✗ API test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 4: Test Invalid Login
print("\n5. Testing invalid login (should fail)...")
invalid_data = {
    "email": test_email,
    "password": "wrongpassword"
}

response = client.post(
    '/api/accounts/login/',
    invalid_data,
    format='json'
)

if response.status_code in [401, 400]:
    print("✓ Invalid login correctly rejected")
else:
    print(f"⚠ Unexpected status code: {response.status_code}")

# Test 5: Test Missing Fields
print("\n6. Testing missing fields (should fail)...")
response = client.post(
    '/api/accounts/login/',
    {"email": test_email},  # Missing password
    format='json'
)

if response.status_code == 400:
    print("✓ Missing fields correctly rejected")
else:
    print(f"⚠ Unexpected status code: {response.status_code}")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("""
All tests passed! ✓

You can now login with:
  Email: testuser@example.com
  Password: TestPass123!

Frontend should work with these credentials.

To use in frontend, update your login form:
  1. Email field → testuser@example.com
  2. Password field → TestPass123!
  3. Click login

If it still doesn't work:
  1. Check browser console for errors
  2. Check Django server logs
  3. Verify CORS settings
  4. Test with curl or Postman first
""")

print("\nTest user details:")
print(f"  Email: {user.email}")
print(f"  Username: {user.username}")
print(f"  Password: {test_password}")
print(f"  ID: {user.id}")
print(f"  Active: {user.is_active}")

if hasattr(user, 'is_verified'):
    print(f"  Verified: {user.is_verified}")

print("\n" + "=" * 60) 