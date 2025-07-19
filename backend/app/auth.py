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
        self.kite = None
        self.authenticated = False
        
    def authenticate(self):
        """Main authentication method"""
        try:
            self.kite = KiteConnect(api_key=settings.ZERODHA_API_KEY)
            
            # Try existing token first
            if self._try_existing_token():
                self.authenticated = True
                return self.kite
            
            # Generate new token
            if self._generate_new_token():
                self.authenticated = True
                return self.kite
                
            return None
            
        except Exception as e:
            print(f"❌ Zerodha authentication failed: {e}")
            self.authenticated = False
            return None
    
    def _try_existing_token(self):
        """Try to use existing saved token"""
        if os.path.exists(settings.ZERODHA_ACCESS_TOKEN_FILE):
            try:
                with open(settings.ZERODHA_ACCESS_TOKEN_FILE, "r") as f:
                    access_token = f.read().strip()
                
                self.kite.set_access_token(access_token)
                profile = self.kite.profile()
                print(f"✅ Using existing token for: {profile['user_name']}")
                return True
                
            except Exception:
                print("⚠️ Existing token invalid, generating new one")
                return False
        return False
    
    def _generate_new_token(self):
        """Generate new access token using automatic login"""
        try:
            # Step 1: Initial login
            http_session = requests.Session()
            url = http_session.get(
                url=f'https://kite.trade/connect/login?v=3&api_key={settings.ZERODHA_API_KEY}'
            ).url
            
            # Step 2: Username/Password login
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={
                    'user_id': settings.ZERODHA_USER_ID, 
                    'password': settings.ZERODHA_PASSWORD
                }
            )
            resp_dict = json.loads(response.content)
            
            if resp_dict.get("status") != "success":
                raise Exception(f"Login failed: {resp_dict.get('message', 'Unknown error')}")
            
            # Step 3: TOTP authentication
            totp_value = pyotp.TOTP(settings.ZERODHA_TOTP_KEY).now()
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': settings.ZERODHA_USER_ID,
                    'request_id': resp_dict["data"]["request_id"],
                    'twofa_value': totp_value
                }
            )
            
            # Step 4: Get request token
            url = url + "&skip_session=true"
            final_response = http_session.get(url=url, allow_redirects=True).url
            parsed_url = urlparse(final_response)
            query_params = parse_qs(parsed_url.query)
            
            if 'request_token' not in query_params:
                raise Exception(f"Request token not found: {final_response}")
            
            # Step 5: Generate access token
            request_token = query_params['request_token'][0]
            data = self.kite.generate_session(request_token, settings.ZERODHA_API_SECRET)
            access_token = data["access_token"]
            self.kite.set_access_token(access_token)
            
            # Step 6: Save token
            with open(settings.ZERODHA_ACCESS_TOKEN_FILE, "w") as f:
                f.write(access_token)
            
            profile = self.kite.profile()
            print(f"✅ New token generated for: {profile['user_name']}")
            return True
            
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return False
    
    def get_kite_instance(self):
        """Get authenticated KiteConnect instance"""
        return self.kite if self.authenticated else None
    
    def is_authenticated(self):
        """Check if authentication is successful"""
        return self.authenticated