# backend/app/auth.py - FIXED VERSION using working debug script method

import os
import json
import pyotp
import requests
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from .config import settings
from datetime import datetime, timedelta

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
        self._last_auth_attempt = None
        self._auth_retry_delay = 60
    
    def authenticate(self, manual_request_token=None):
        """Zerodha login flow: use manual request token if automatic extraction fails."""
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
            # Automated login flow
            print("🔐 Generating new Zerodha token...")
            http_session = requests.Session()
            url = http_session.get(url=f'https://kite.trade/connect/login?v=3&api_key={self.api_key}').url
            print(f"🔗 Redirected to: {url}")
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={'user_id': self.user_id, 'password': self.password}
            )
            try:
                resp_dict = json.loads(response.content)
            except Exception:
                resp_dict = None
            if not resp_dict or resp_dict.get("status") != "success":
                print("❌ Automatic login failed. Please provide request token manually.")
                if manual_request_token:
                    print(f"🔑 Using manual request token: {manual_request_token}")
                    data = self.kite.generate_session(manual_request_token, self.api_secret)
                    access_token = data["access_token"]
                    self.kite.set_access_token(access_token)
                    os.makedirs(os.path.dirname(self.access_token_file) if os.path.dirname(self.access_token_file) else '.', exist_ok=True)
                    with open(self.access_token_file, "w") as f:
                        f.write(access_token)
                    print(f"💾 Access token saved to: {self.access_token_file}")
                    profile = self.kite.profile()
                    self.zerodha_profile_name = profile['user_name']
                    self._authenticated = True
                    print(f"✅ Authentication successful! Profile: {self.zerodha_profile_name}")
                    return self.kite
                else:
                    print("❗ Please login to Zerodha manually and provide the request token.")
                    self._authenticated = False
                    return None
            totp_value = pyotp.TOTP(self.totp_key).now()
            twofa_response = http_session.post(
                url='https://kite.zerodha.com/api/twofa',
                data={
                    'user_id': self.user_id,
                    'request_id': resp_dict["data"]["request_id"],
                    'twofa_value': totp_value
                }
            )
            url = url + "&skip_session=true"
            final_response = http_session.get(url=url, allow_redirects=True).url
            parsed_url = urlparse(final_response)
            query_params = parse_qs(parsed_url.query)
            if 'request_token' not in query_params:
                print("❌ Automatic request token extraction failed. Please provide request token manually.")
                if manual_request_token:
                    print(f"🔑 Using manual request token: {manual_request_token}")
                    data = self.kite.generate_session(manual_request_token, self.api_secret)
                    access_token = data["access_token"]
                    self.kite.set_access_token(access_token)
                    os.makedirs(os.path.dirname(self.access_token_file) if os.path.dirname(self.access_token_file) else '.', exist_ok=True)
                    with open(self.access_token_file, "w") as f:
                        f.write(access_token)
                    print(f"💾 Access token saved to: {self.access_token_file}")
                    profile = self.kite.profile()
                    self.zerodha_profile_name = profile['user_name']
                    self._authenticated = True
                    print(f"✅ Authentication successful! Profile: {self.zerodha_profile_name}")
                    return self.kite
                else:
                    print("❗ Please login to Zerodha manually and provide the request token.")
                    self._authenticated = False
                    return None
            request_token = query_params['request_token'][0]
            data = self.kite.generate_session(request_token, self.api_secret)
            access_token = data["access_token"]
            self.kite.set_access_token(access_token)
            os.makedirs(os.path.dirname(self.access_token_file) if os.path.dirname(self.access_token_file) else '.', exist_ok=True)
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            print(f"💾 Access token saved to: {self.access_token_file}")
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