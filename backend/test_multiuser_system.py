# backend/test_multiuser_system.py - Quick test of multi-user system
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test that all imports work correctly"""
    try:
        print("Testing imports...")
        
        from app.database import get_db, UserService, UserDB
        print("✅ Database imports OK")
        
        from app.models import UserCreate, LoginRequest, Token
        print("✅ Model imports OK")
        
        from app.auth_multiuser import create_access_token
        print("✅ Auth imports OK")
        
        from app.services.multiuser_zerodha_auth import zerodha_auth_manager
        print("✅ Zerodha auth imports OK")
        
        from app.services.multiuser_investment_service import investment_service_manager
        print("✅ Investment service imports OK")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """Test database operations"""
    try:
        print("\nTesting database...")
        
        from app.database import SessionLocal, UserService
        from app.models import UserCreate
        
        # Test database connection
        db = SessionLocal()
        
        # Test user creation (will fail if user exists, which is OK)
        test_user = UserCreate(
            username="test_api_user",
            email="test@example.com",
            full_name="Test API User",
            password="testpass123",
            zerodha_api_key="test_api_key",
            zerodha_api_secret="test_api_secret"
        )
        
        try:
            user = UserService.create_user(db, test_user)
            print(f"✅ Created test user: {user.username}")
            print(f"   - ID: {user.id}")
            print(f"   - Data dir: {user.user_data_directory}")
        except ValueError as e:
            print(f"ℹ️ User already exists: {e}")
        
        # Test user retrieval
        existing_user = UserService.get_user_by_username(db, "test_api_user")
        if existing_user:
            print(f"✅ Retrieved user: {existing_user.username}")
            
            # Test credential decryption
            creds = UserService.get_decrypted_zerodha_credentials(existing_user)
            print(f"✅ Decrypted credentials: API Key: {creds['api_key'][:10]}...")
        
        db.close()
        print("✅ Database operations successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_system():
    """Test authentication system"""
    try:
        print("\nTesting authentication system...")
        
        from app.auth_multiuser import create_access_token, verify_token
        from datetime import timedelta
        
        # Test token creation
        token = create_access_token(
            data={"sub": "test_user_id", "username": "test_user"},
            expires_delta=timedelta(minutes=30)
        )
        print(f"✅ Created JWT token: {token[:50]}...")
        
        # Test token verification
        token_data = verify_token(token)
        print(f"✅ Verified token: User ID: {token_data.user_id}")
        
        print("✅ Authentication system working!")
        return True
        
    except Exception as e:
        print(f"❌ Auth test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Multi-User Investment System")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Database Tests", test_database), 
        ("Authentication Tests", test_auth_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Multi-user system is ready.")
        print("\n📋 Next steps:")
        print("   1. Run: START-MULTIUSER-BACKEND.bat")
        print("   2. Run: START-DASHBOARD-FAST.bat")
        print("   3. Navigate to http://localhost:8080")
        print("   4. Register with your API key/secret")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)