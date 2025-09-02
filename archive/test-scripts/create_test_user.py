# backend/create_test_user.py - Create test users for multi-user system
import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy.orm import Session
from app.database import SessionLocal, UserService
from app.models import UserCreate

def create_test_users():
    """Create test users for development and testing"""
    
    # User 1 - Using API key/secret (replace with real values)
    user1_data = UserCreate(
        username="testuser1",
        email="testuser1@example.com",
        full_name="Test User One",
        password="testpass123",
        role="user",
        zerodha_api_key="femohcxeam7tjt1p",  # Replace with user's real API key
        zerodha_api_secret="xjudlehzrnblhs1wznjvb95uhgtny54f"  # Replace with user's real API secret
    )
    
    # User 2 - Needs different API credentials
    user2_data = UserCreate(
        username="testuser2", 
        email="testuser2@example.com",
        full_name="Test User Two",
        password="testpass123",
        role="user",
        zerodha_api_key="SECOND_USER_API_KEY",  # Replace with second user's API key
        zerodha_api_secret="SECOND_USER_API_SECRET"  # Replace with second user's API secret
    )
    
    # Admin user
    admin_data = UserCreate(
        username="admin",
        email="admin@example.com", 
        full_name="System Administrator",
        password="admin123",
        role="admin",
        zerodha_api_key="femohcxeam7tjt1p",  # Can reuse for admin
        zerodha_api_secret="xjudlehzrnblhs1wznjvb95uhgtny54f"
    )
    
    db = SessionLocal()
    
    try:
        # Create users
        for i, user_data in enumerate([user1_data, user2_data, admin_data], 1):
            try:
                user = UserService.create_user(db, user_data)
                print(f"✅ User {i} created successfully:")
                print(f"   - Username: {user.username}")
                print(f"   - Email: {user.email}")
                print(f"   - Full Name: {user.full_name}")
                print(f"   - Role: {user.role}")
                print(f"   - User ID: {user.id}")
                print(f"   - Data Directory: {user.user_data_directory}")
                print()
                
            except ValueError as e:
                print(f"⚠️ User {i} ({user_data.username}) already exists or error: {e}")
                
            except Exception as e:
                print(f"❌ Error creating user {i}: {e}")
                
    finally:
        db.close()
    
    print("🔐 Test user creation completed!")
    print("\n📋 Quick Test Login Credentials:")
    print("   Username: testuser1 | Password: testpass123")
    print("   Username: testuser2 | Password: testpass123") 
    print("   Username: admin | Password: admin123")
    print("\n⚠️  IMPORTANT: Update the Zerodha credentials above with real values!")

if __name__ == "__main__":
    create_test_users()