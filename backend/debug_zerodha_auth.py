# backend/debug_zerodha_auth.py - Quick diagnostic script

import os
import sys
sys.path.append('.')

from app.auth import ZerodhaAuth
from app.config import settings

def debug_zerodha_auth():
    """Debug Zerodha authentication step by step"""
    print("🔍 ZERODHA AUTHENTICATION DIAGNOSTIC")
    print("=" * 50)
    
    # Step 1: Check configuration
    print("\n1️⃣ CHECKING CONFIGURATION:")
    print(f"   API Key: {'✅ Set' if settings.ZERODHA_API_KEY else '❌ Missing'} ({settings.ZERODHA_API_KEY[:10]}...)")
    print(f"   API Secret: {'✅ Set' if settings.ZERODHA_API_SECRET else '❌ Missing'} ({'*' * 10})")
    print(f"   User ID: {'✅ Set' if settings.ZERODHA_USER_ID else '❌ Missing'} ({settings.ZERODHA_USER_ID})")
    print(f"   Password: {'✅ Set' if settings.ZERODHA_PASSWORD else '❌ Missing'} ({'*' * len(settings.ZERODHA_PASSWORD)})")
    print(f"   TOTP Key: {'✅ Set' if settings.ZERODHA_TOTP_KEY else '❌ Missing'} ({'*' * 10})")
    
    # Step 2: Check token file
    print("\n2️⃣ CHECKING TOKEN FILE:")
    token_file = settings.ZERODHA_ACCESS_TOKEN_FILE
    print(f"   Token file path: {token_file}")
    
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
            print(f"   ✅ Token file exists: {token[:20]}...")
            print(f"   Token length: {len(token)} characters")
        except Exception as e:
            print(f"   ❌ Error reading token file: {e}")
    else:
        print(f"   ⚠️ Token file does not exist")
    
    # Step 3: Test authentication
    print("\n3️⃣ TESTING AUTHENTICATION:")
    try:
        auth = ZerodhaAuth()
        print(f"   ZerodhaAuth instance created: ✅")
        
        # Check if already authenticated
        if auth.is_authenticated():
            print(f"   ✅ Already authenticated: {auth.profile_name}")
            return auth
        else:
            print(f"   ⚠️ Not authenticated, attempting login...")
            
            # Try authentication
            result = auth.authenticate()
            if result:
                print(f"   ✅ Authentication successful: {auth.profile_name}")
                return auth
            else:
                print(f"   ❌ Authentication failed")
                return None
                
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    auth = debug_zerodha_auth()
    
    if auth and auth.is_authenticated():
        print("\n4️⃣ TESTING API CALLS:")
        try:
            kite = auth.get_kite_instance()
            
            # Test basic quote
            print("   Testing quote API...")
            quote = kite.quote(["NSE:RELIANCE"])
            if quote:
                reliance_price = quote.get("NSE:RELIANCE", {}).get("last_price", 0)
                print(f"   ✅ Quote API works: RELIANCE = ₹{reliance_price}")
            else:
                print(f"   ❌ Quote API failed")
            
            # Test margins
            print("   Testing margins API...")
            margins = kite.margins()
            if margins:
                cash = margins.get('equity', {}).get('available', {}).get('cash', 0)
                print(f"   ✅ Margins API works: Available cash = ₹{cash:,.2f}")
            else:
                print(f"   ❌ Margins API failed")
                
        except Exception as e:
            print(f"   ❌ API test failed: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    
    if auth and auth.is_authenticated():
        print("🎉 ZERODHA CONNECTION: ✅ WORKING")
    else:
        print("💥 ZERODHA CONNECTION: ❌ FAILED")
        print("\n🔧 NEXT STEPS:")
        print("1. Check your Zerodha credentials in .env file")
        print("2. Ensure TOTP key is correct")
        print("3. Try deleting zerodha_access_token.txt and retry")
        print("4. Check if Zerodha API access is enabled")