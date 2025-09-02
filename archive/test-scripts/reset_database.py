# backend/reset_database.py - Clean database for fresh start
import sys
import os
sys.path.append(os.path.dirname(__file__))

import shutil
from app.database import Base, engine

def reset_database():
    """Reset database and user data for fresh start"""
    print("🗂️ Resetting Multi-User Database...")
    
    try:
        # Check if database is in use
        db_file = "users.db"
        if os.path.exists(db_file):
            print("⚠️ Database file exists, checking if it's in use...")
            
            # Try to rename first (this fails if file is locked)
            try:
                temp_name = f"{db_file}.old.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(db_file, temp_name)
                print(f"✅ Moved old database to {temp_name}")
                
                # Try to remove the temp file
                try:
                    os.remove(temp_name)
                    print("✅ Removed old database file")
                except:
                    print(f"ℹ️ Old database kept as {temp_name} (couldn't remove)")
                    
            except PermissionError:
                print("❌ Database file is locked by another process!")
                print("\n🔧 SOLUTIONS:")
                print("   1. Close any running backend servers")
                print("   2. Close database browsers/editors")
                print("   3. Restart your command prompt")
                print("   4. Or just run: python -c \"from app.database import Base, engine; Base.metadata.create_all(bind=engine)\"")
                return False
        
        # Remove user data directory
        user_data_dir = "user_data"
        if os.path.exists(user_data_dir):
            try:
                shutil.rmtree(user_data_dir)
                print("✅ Removed old user data directory")
            except Exception as e:
                print(f"⚠️ Couldn't remove user data directory: {e}")
        
        # Remove encryption key (will be regenerated)
        encryption_file = "encryption.key"
        if os.path.exists(encryption_file):
            try:
                os.remove(encryption_file)
                print("✅ Removed old encryption key")
            except Exception as e:
                print(f"⚠️ Couldn't remove encryption key: {e}")
        
        # Create fresh database with new schema
        print("📦 Creating fresh database with new schema...")
        from datetime import datetime
        Base.metadata.create_all(bind=engine)
        print("✅ Fresh database created successfully!")
        
        print("\n🎉 Database reset complete!")
        print("   - Fresh users.db created")
        print("   - New encryption key will be generated") 
        print("   - Ready for user registration")
        
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("\n📋 Next steps:")
        print("   1. Run: python create_test_user.py (optional)")
        print("   2. Run: python -c \"from app.main_multiuser_v2 import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)\"")
        print("   3. Open frontend and register new users")
    sys.exit(0 if success else 1)