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
        """EXACT method from your working Jupyter notebook"""
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

            # Use EXACT method from your working notebook
            print("🔐 Generating new Zerodha token...")
            http_session = requests.Session()
            
            # Step 1: EXACT as notebook
            url = http_session.get(url=f'https://kite.trade/connect/login?v=3&api_key={self.api_key}').url
            print(f"🔗 Login URL: {url}")
            
            # Step 2: EXACT as notebook  
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={'user_id': self.user_id, 'password': self.password}
            )
            print(f"📝 Login response status: {response.status_code}")
            
            # Step 3: EXACT as notebook - this is what works!
            resp_dict = json.loads(response.content)
            print(f"📋 Login response: {resp_dict}")
            
            if resp_dict.get("status") != "success":
                raise Exception(f"❌ Zerodha login failed: {resp_dict.get('message', 'Unknown error')}")

            # Step 4: TOTP - EXACT as notebook
            totp_value = pyotp.TOTP(self.totp_key).now()
            print(f"🔑 Generated TOTP: {totp_value}")
            
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': self.user_id,
                    'request_id': resp_dict["data"]["request_id"],
                    'twofa_value': totp_value
                }
            )
            print(f"📝 2FA response status: {twofa_response.status_code}")

            # Step 5: Get token - EXACT as notebook
            url = url + "&skip_session=true"
            print(f"🔗 Final auth URL: {url}")
            
            final_response = http_session.get(url=url, allow_redirects=True).url
            print(f"🔗 Final redirect URL: {final_response}")
            
            # Step 6: Parse token - EXACT as notebook
            parsed_url = urlparse(final_response)
            query_params = parse_qs(parsed_url.query)
            
            if 'request_token' not in query_params:
                raise Exception(f"❌ Zerodha request token not found: {final_response}")

            request_token = query_params['request_token'][0]
            print(f"🎫 Request token: {request_token}")
            
            # Step 7: Generate access token - EXACT as notebook
            data = self.kite.generate_session(request_token, self.api_secret)
            access_token = data["access_token"]
            self.kite.set_access_token(access_token)
            print(f"✅ Access token: {access_token}")

            # Step 8: Save and verify
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            print(f"💾 Access token saved")

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