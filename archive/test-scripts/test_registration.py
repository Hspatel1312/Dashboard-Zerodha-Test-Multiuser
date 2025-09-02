# backend/test_registration.py - Test registration endpoint
import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
import json

def test_registration_endpoint():
    """Test the registration API endpoint"""
    print("Testing Registration Endpoint")
    print("=" * 40)
    
    # Test data
    test_user = {
        "username": "testuser123",
        "email": "testuser123@example.com",
        "full_name": "Test User 123",
        "password": "testpass123",
        "role": "user",
        "zerodha_api_key": "test_api_key_12345",
        "zerodha_api_secret": "test_api_secret_67890"
    }
    
    try:
        # Test backend health first
        print("1. Testing backend health...")
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   Health status: {health_response.status_code}")
        
        if health_response.status_code != 200:
            print("ERROR: Backend is not running or not healthy")
            return False
        
        # Test registration endpoint
        print("\n2. Testing registration endpoint...")
        print(f"   Sending data: {json.dumps(test_user, indent=2)}")
        
        response = requests.post(
            "http://localhost:8000/api/register",
            json=test_user,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   Response data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"   Raw response: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Registration endpoint is working!")
            return True
        else:
            print(f"ERROR: Registration failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend - is it running on port 8000?")
        return False
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out - backend is not responding")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        return False

def test_database_connection():
    """Test database connection directly"""
    print("\n3. Testing database connection...")
    
    try:
        from app.database import SessionLocal, UserService
        from app.models import UserCreate
        
        db = SessionLocal()
        
        # Try to create a test user directly
        test_user = UserCreate(
            username="direct_test_user",
            email="direct@example.com",
            full_name="Direct Test User",
            password="password123",
            zerodha_api_key="direct_test_key",
            zerodha_api_secret="direct_test_secret"
        )
        
        try:
            user = UserService.create_user(db, test_user)
            print(f"SUCCESS: Database user creation works - User ID: {user.id}")
            return True
        except ValueError as e:
            print(f"INFO: User creation failed (expected if user exists): {e}")
            return True  # This is actually OK
        except Exception as e:
            print(f"ERROR: Database error: {e}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"ERROR: Database connection error: {e}")
        return False

def main():
    print("Registration Troubleshooting Tool")
    print("This will help identify why registration is failing.")
    print()
    
    # Run tests
    backend_ok = test_registration_endpoint()
    db_ok = test_database_connection()
    
    print("\n" + "=" * 40)
    print("TEST SUMMARY:")
    print(f"   Backend API: {'Working' if backend_ok else 'Failed'}")
    print(f"   Database: {'Working' if db_ok else 'Failed'}")
    
    if backend_ok and db_ok:
        print("\nRegistration should work! Check browser console for frontend errors.")
    else:
        print("\nFound issues that need to be fixed first.")
    
    print("\nNext steps:")
    print("   1. Make sure backend is running: START-MULTIUSER-BACKEND-SIMPLE.bat")
    print("   2. Check browser console (F12) for frontend errors")
    print("   3. Try registration with debug logging enabled")

if __name__ == "__main__":
    main()