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
        self.profile_name = None
        
    def authenticate(self):
        """Main authentication method with automatic login"""
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Try existing token first
            if self._try_existing_token():
                self._authenticated = True
                print(f"✅ Using existing token for: {self.profile_name}")
                return self.kite
            
            # Generate new token using automatic login
            if self._generate_new_token():
                self._authenticated = True
                print(f"✅ New token generated for: {self.profile_name}")
                return self.kite
                
            return None
            
        except Exception as e:
            print(f"❌ Zerodha authentication failed: {e}")
            self._authenticated = False
            return None
    
    def _try_existing_token(self):
        """Try to use existing saved token"""
        if os.path.exists(self.access_token_file):
            try:
                with open(self.access_token_file, "r") as f:
                    access_token = f.read().strip()
                
                if access_token:
                    self.kite.set_access_token(access_token)
                    profile = self.kite.profile()
                    self.profile_name = profile['user_name']
                    return True
                    
            except Exception as e:
                print(f"⚠️ Existing token invalid: {e}")
                return False
        return False
    
    def _generate_new_token(self):
        """Generate new access token using automatic login (from your notebook)"""
        try:
            # Step 1: Initial login setup
            http_session = requests.Session()
            url = http_session.get(
                url=f'https://kite.trade/connect/login?v=3&api_key={self.api_key}'
            ).url
            
            # Step 2: Username/Password login
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={
                    'user_id': self.user_id, 
                    'password': self.password
                }
            )
            resp_dict = json.loads(response.content)
            
            if resp_dict.get("status") != "success":
                raise Exception(f"Login failed: {resp_dict.get('message', 'Unknown error')}")
            
            # Step 3: TOTP authentication
            totp_value = pyotp.TOTP(self.totp_key).now()
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': self.user_id,
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
            data = self.kite.generate_session(request_token, self.api_secret)
            access_token = data["access_token"]
            self.kite.set_access_token(access_token)
            
            # Step 6: Save token
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            
            # Step 7: Get profile
            profile = self.kite.profile()
            self.profile_name = profile['user_name']
            
            print(f"✅ Access token saved: {access_token}")
            return True
            
        except Exception as e:
            print(f"❌ Token generation failed: {e}")
            return False
    
    def get_kite_instance(self):
        """Get authenticated KiteConnect instance"""
        return self.kite if self._authenticated else None
    
    def is_authenticated(self):
        """Check if authentication is successful"""
        return self._authenticated