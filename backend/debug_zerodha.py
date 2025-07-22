# backend/app/auth.py
import os
import json
import pyotp
import requests
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from .config import settings

class ZerodhaAuth:
    def __init__(self):
        self.api_key = settings.ZERODHA_API_KEY
        self.api_secret = settings.ZERODHA_API_SECRET
        self.user_id = settings.ZERODHA_USER_ID
        self.password = settings.ZERODHA_PASSWORD
        self.totp_key = settings.ZERODHA_TOTP_KEY
        self.access_token_file = settings.ZERODHA_ACCESS_TOKEN_FILE
        self.kite = None
        self._authenticated = False
        self.zerodha_profile_name = None
        
    def authenticate(self):
        """Authentication using EXACT method from working debug script"""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Try existing token first
            if os.path.exists(self.access_token_file):
                with open(self.access_token_file, "r") as f:
                    access_token = f.read().strip()
                if access_token:
                    self.kite.set_access_token(access_token)
                    try:
                        profile = self.kite.profile()
                        self.zerodha_profile_name = profile['user_name']
                        self._authenticated = True
                        print(f"✅ Zerodha Profile: {self.zerodha_profile_name}")
                        return self.kite
                    except Exception as e:
                        print(f"⚠️ Saved Zerodha token invalid: {str(e)}")

            # Generate new token using EXACT debug script method
            print("🔐 Generating new Zerodha token...")
            http_session = requests.Session()
            
            # Add the same browser headers as debug script
            http_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Step 1: Get login URL and initial session - EXACT as debug script
            login_url = f'https://kite.trade/connect/login?v=3&api_key={self.api_key}'
            print(f"🌐 Getting login URL: {login_url}")
            
            initial_response = http_session.get(url=login_url)
            actual_url = initial_response.url
            print(f"🔗 Redirected to: {actual_url}")
            
            # Step 2: Login with credentials - EXACT as debug script
            print(f"🔐 Logging in with user ID: {self.user_id}")
            login_response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={
                    'user_id': self.user_id, 
                    'password': self.password
                }
            )
            
            print(f"📝 Login response status: {login_response.status_code}")
            
            try:
                login_data = json.loads(login_response.content)
            except json.JSONDecodeError:
                print(f"❌ Failed to parse login response: {login_response.text}")
                raise Exception("Invalid response from Zerodha login API")
            
            print(f"📋 Login response: {login_data}")
            
            if login_data.get("status") != "success":
                error_msg = login_data.get('message', 'Unknown login error')
                print(f"❌ Login failed: {error_msg}")
                raise Exception(f"Zerodha login failed: {error_msg}")

            # Step 3: TOTP verification - EXACT as debug script
            totp_value = pyotp.TOTP(self.totp_key).now()
            print(f"🔑 Generated TOTP: {totp_value}")
            
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': self.user_id,
                    'request_id': login_data["data"]["request_id"],
                    'twofa_value': totp_value
                }
            )
            
            print(f"📝 2FA response status: {twofa_response.status_code}")
            
            try:
                twofa_data = json.loads(twofa_response.content)
                print(f"📋 2FA response: {twofa_data}")
            except json.JSONDecodeError:
                print(f"⚠️ Could not parse 2FA response, continuing...")

            # Step 4: Authorization - EXACT method from debug script that WORKS
            print(f"🎫 Getting authorization...")
            
            # This is the EXACT line that works in debug script
            auth_url = actual_url + "&skip_session=true"
            print(f"🔗 Trying auth URL: {auth_url}")
            
            final_response = http_session.get(url=auth_url, allow_redirects=True)
            final_url = final_response.url
            
            print(f"📊 Final Status Code: {final_response.status_code}")
            print(f"🔗 Final URL: {final_url}")
            print(f"📋 Final Headers: {dict(final_response.headers)}")
            
            print(f"\n📄 Response Content Preview:")
            print(f"{final_response.text[:500]}")

            # Step 5: Parse URL for request token - EXACT as debug script
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
            
            # Extract request token - EXACT logic from debug script
            request_token = None
            
            if 'request_token' in query_params:
                request_token = query_params['request_token'][0]
                print(f"   ✅ Found request_token in query: {request_token}")
            
            if not request_token:
                print(f"   ❌ No request token found!")
                print(f"   Expected redirect to google.com with request_token, but got: {final_url}")
                print(f"   Debug: This should match the debug script output exactly")
                raise Exception(f"No request token found. Debug script works but main app doesn't - check for differences.")

            print(f"✅ Authentication debug completed successfully!")
            print(f"🎫 Request Token: {request_token}")

            # Step 6: Generate access token - EXACT as debug script
            print("🔐 Generating access token...")
            try:
                session_data = self.kite.generate_session(request_token, self.api_secret)
                access_token = session_data["access_token"]
                print(f"✅ Access token generated: {access_token}")
            except Exception as e:
                print(f"❌ Failed to generate session: {e}")
                raise Exception(f"Failed to generate access token: {str(e)}")

            # Step 7: Set token and verify
            self.kite.set_access_token(access_token)

            # Step 8: Save token and get profile
            os.makedirs(os.path.dirname(self.access_token_file), exist_ok=True)
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            print(f"💾 Access token saved to: {self.access_token_file}")

            # Step 9: Verify with profile
            profile = self.kite.profile()
            self.zerodha_profile_name = profile['user_name']
            self._authenticated = True
            print(f"✅ Authentication successful! Profile: {self.zerodha_profile_name}")
            return self.kite
            
        except Exception as e:
            print(f"❌ Zerodha authentication failed: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            self._authenticated = False
            return None
    
    def get_kite_instance(self):
        return self.kite if self._authenticated else None
    
    def is_authenticated(self):
        return self._authenticated
    
    @property
    def profile_name(self):
        return self.zerodha_profile_name