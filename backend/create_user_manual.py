# backend/create_user_manual.py - Create user with your actual API credentials
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal, UserService
from app.models import UserCreate

def create_user_with_real_credentials():
    """Create a user with real API credentials for testing"""
    
    print("🔐 Create User with Your Zerodha API Credentials")
    print("=" * 50)
    print("Get your API credentials from: https://developers.zerodha.com/")
    print()
    
    # Get user input
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username required")
        return False
        
    email = input("Enter email: ").strip() 
    if not email:
        print("❌ Email required")
        return False
        
    full_name = input("Enter full name: ").strip()
    if not full_name:
        print("❌ Full name required") 
        return False
        
    password = input("Enter password: ").strip()
    if not password:
        print("❌ Password required")
        return False
    
    print("\n🔑 Zerodha API Credentials:")
    api_key = input("Enter your Zerodha API Key: ").strip()
    if not api_key:
        print("❌ API Key required")
        return False
        
    api_secret = input("Enter your Zerodha API Secret: ").strip() 
    if not api_secret:
        print("❌ API Secret required")
        return False
    
    # Create user
    user_data = UserCreate(
        username=username,
        email=email,
        full_name=full_name,
        password=password,
        role="user",
        zerodha_api_key=api_key,
        zerodha_api_secret=api_secret
    )
    
    db = SessionLocal()
    
    try:
        user = UserService.create_user(db, user_data)
        print(f"\n✅ User created successfully!")
        print(f"   - Username: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Full Name: {user.full_name}")
        print(f"   - User ID: {user.id}")
        print(f"   - Data Directory: {user.user_data_directory}")
        print(f"   - API Key: {api_key[:10]}...")
        print()
        print("🚀 You can now login with:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        
        return True
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        db.close()

def main():
    print("👤 Manual User Creation Tool")
    print("This tool helps you create a user with your real Zerodha API credentials.")
    print()
    
    try:
        success = create_user_with_real_credentials()
        if success:
            print("\n🎉 Ready to test!")
            print("   1. Start the backend: python -m app.main_multiuser_v2")
            print("   2. Start the frontend: START-DASHBOARD-FAST.bat")
            print("   3. Login with your new credentials")
        else:
            print("\n❌ User creation failed.")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()