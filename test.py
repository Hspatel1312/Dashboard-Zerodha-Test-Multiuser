# debug_auth.py - Run this standalone to debug Zerodha authentication
import requests
import json
import pyotp
from urllib.parse import urlparse, parse_qs

# Your credentials
API_KEY = "femohcxeam7tjt1p"
API_SECRET = "xjudlehzrnblhs1wznjvb95uhgtny54f"
USER_ID = "MSC739"
PASSWORD = "Pranjal@1006"
TOTP_KEY = "PHHXNLG7ZPS3C4GCOF7HLGCM7DV6HRAB"

def debug_zerodha_auth():
    """Debug Zerodha authentication step by step"""
    
    print("🔐 Starting Zerodha Authentication Debug...")
    http_session = requests.Session()
    
    try:
        # Step 1: Get login URL
        login_url = f'https://kite.trade/connect/login?v=3&api_key={API_KEY}'
        print(f"\n1️⃣ Getting login URL: {login_url}")
        
        initial_response = http_session.get(url=login_url)
        actual_url = initial_response.url
        print(f"   ✅ Redirected to: {actual_url}")
        print(f"   📊 Status Code: {initial_response.status_code}")
        print(f"   📋 Response Headers: {dict(initial_response.headers)}")
        
        # Step 2: Login with credentials
        print(f"\n2️⃣ Logging in with user ID: {USER_ID}")
        login_data = {
            'user_id': USER_ID, 
            'password': PASSWORD
        }
        
        login_response = http_session.post(
            url='https://kite.zerodha.com/api/login',
            data=login_data
        )
        
        print(f"   📊 Login Status Code: {login_response.status_code}")
        print(f"   📋 Login Response Headers: {dict(login_response.headers)}")
        
        try:
            login_result = json.loads(login_response.content)
            print(f"   📄 Login Response: {json.dumps(login_result, indent=2)}")
        except json.JSONDecodeError:
            print(f"   ❌ Could not parse login response as JSON")
            print(f"   📄 Raw Response: {login_response.text[:500]}")
            return
        
        if login_result.get("status") != "success":
            print(f"   ❌ Login failed: {login_result.get('message', 'Unknown error')}")
            return
        
        request_id = login_result["data"]["request_id"]
        print(f"   ✅ Login successful, request_id: {request_id}")
        
        # Step 3: TOTP verification
        print(f"\n3️⃣ Performing TOTP verification...")
        totp_value = pyotp.TOTP(TOTP_KEY).now()
        print(f"   🔑 Generated TOTP: {totp_value}")
        
        twofa_data = {
            'user_id': USER_ID,
            'request_id': request_id,
            'twofa_value': totp_value
        }
        
        twofa_response = http_session.post(
            url='https://kite.zerodha.com/api/twofa',
            data=twofa_data
        )
        
        print(f"   📊 2FA Status Code: {twofa_response.status_code}")
        print(f"   📋 2FA Response Headers: {dict(twofa_response.headers)}")
        
        try:
            twofa_result = json.loads(twofa_response.content)
            print(f"   📄 2FA Response: {json.dumps(twofa_result, indent=2)}")
        except json.JSONDecodeError:
            print(f"   ⚠️ Could not parse 2FA response as JSON")
            print(f"   📄 Raw 2FA Response: {twofa_response.text[:500]}")
        
        # Step 4: Get authorization - try different approaches
        print(f"\n4️⃣ Getting authorization...")
        
        # Method 1: Standard approach
        auth_url = actual_url + "&skip_session=true"
        print(f"   🔗 Trying auth URL: {auth_url}")
        
        final_response = http_session.get(url=auth_url, allow_redirects=True)
        final_url = final_response.url
        
        print(f"   📊 Final Status Code: {final_response.status_code}")
        print(f"   🔗 Final URL: {final_url}")
        print(f"   📋 Final Headers: {dict(final_response.headers)}")
        
        # Method 2: Try without skip_session
        if 'request_token' not in final_url:
            print(f"\n   🔄 Trying without skip_session...")
            auth_url_2 = actual_url
            final_response_2 = http_session.get(url=auth_url_2, allow_redirects=True)
            final_url_2 = final_response_2.url
            print(f"   🔗 Alternative Final URL: {final_url_2}")
            if 'request_token' in final_url_2:
                final_url = final_url_2
                final_response = final_response_2
        
        # Method 3: Check response content for clues
        print(f"\n   📄 Response Content Preview:")
        content_preview = final_response.text[:1000]
        print(f"   {content_preview}")
        
        # Step 5: Parse URL for request token
        print(f"\n5️⃣ Parsing URL for request token...")
        parsed_url = urlparse(final_url)
        query_params = parse_qs(parsed_url.query)
        
        print(f"   🔍 URL Components:")
        print(f"     Scheme: {parsed_url.scheme}")
        print(f"     Netloc: {parsed_url.netloc}")
        print(f"     Path: {parsed_url.path}")
        print(f"     Query: {parsed_url.query}")
        print(f"     Fragment: {parsed_url.fragment}")
        print(f"   📋 Query Parameters: {query_params}")
        
        # Look for request token in different places
        request_token = None
        
        # Check query parameters
        if 'request_token' in query_params:
            request_token = query_params['request_token'][0]
            print(f"   ✅ Found request_token in query: {request_token}")
        
        # Check fragment
        elif parsed_url.fragment:
            fragment_params = parse_qs(parsed_url.fragment)
            print(f"   📋 Fragment Parameters: {fragment_params}")
            if 'request_token' in fragment_params:
                request_token = fragment_params['request_token'][0]
                print(f"   ✅ Found request_token in fragment: {request_token}")
        
        # Manual search in URL
        elif 'request_token=' in final_url:
            try:
                token_start = final_url.find('request_token=') + len('request_token=')
                token_end = final_url.find('&', token_start)
                if token_end == -1:
                    token_end = len(final_url)
                request_token = final_url[token_start:token_end]
                print(f"   ✅ Manually extracted request_token: {request_token}")
            except Exception as e:
                print(f"   ❌ Failed to manually extract: {e}")
        
        # Check for other token names
        elif 'auth_token' in query_params:
            request_token = query_params['auth_token'][0]
            print(f"   ✅ Found auth_token: {request_token}")
        
        if not request_token:
            print(f"   ❌ No request token found!")
            print(f"   🔍 All query params: {list(query_params.keys())}")
            
            # Check if there's an error in the URL
            if 'error' in query_params:
                print(f"   ❌ Error in URL: {query_params['error']}")
            
            # Check response content for errors
            if 'error' in final_response.text.lower():
                print(f"   ❌ Error detected in response content")
                error_start = final_response.text.lower().find('error')
                error_context = final_response.text[max(0, error_start-100):error_start+200]
                print(f"   📄 Error context: {error_context}")
            
            return None
        
        print(f"\n✅ Authentication debug completed successfully!")
        print(f"🎫 Request Token: {request_token}")
        return request_token
        
    except Exception as e:
        print(f"\n❌ Debug failed with error: {e}")
        import traceback
        print(f"📋 Full traceback:\n{traceback.format_exc()}")
        return None

if __name__ == "__main__":
    token = debug_zerodha_auth()
    if token:
        print(f"\n🎉 SUCCESS! You can use this request token: {token}")
        
        # Try to generate access token
        try:
            from kiteconnect import KiteConnect
            kite = KiteConnect(api_key=API_KEY)
            session_data = kite.generate_session(token, API_SECRET)
            access_token = session_data["access_token"]
            print(f"🔑 Generated access token: {access_token}")
            
            # Test the token
            kite.set_access_token(access_token)
            profile = kite.profile()
            print(f"👤 Profile: {profile['user_name']}")
            print(f"\n🎊 COMPLETE SUCCESS! Authentication working perfectly!")
            
        except Exception as e:
            print(f"❌ Failed to generate access token: {e}")
    else:
        print(f"\n💔 FAILED! Could not extract request token.")
        print(f"🔧 Possible issues:")
        print(f"   1. Check if your TOTP key is correct")
        print(f"   2. Verify your user ID and password")
        print(f"   3. Check if your API key is active")
        print(f"   4. Ensure 2FA is properly configured")