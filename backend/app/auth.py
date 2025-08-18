# backend/app/auth.py - WORKING VERSION based on BBSC.ipynb method

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
        
        # Ensure access token file directory exists
        token_dir = os.path.dirname(self.access_token_file)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir, exist_ok=True)
    
    def authenticate(self, manual_request_token=None):
        """Fully automatic Zerodha authentication - exact method from working BBSC.ipynb"""
        try:
            kite = KiteConnect(api_key=self.api_key)
            
            # Try existing token first
            if os.path.exists(self.access_token_file):
                try:
                    with open(self.access_token_file, "r", encoding="utf-8") as f:
                        access_token = f.read().strip()
                    if access_token:
                        kite.set_access_token(access_token)
                        profile = kite.profile()
                        self.zerodha_profile_name = profile['user_name']
                        self._authenticated = True
                        self._last_auth_attempt = datetime.now()
                        self.kite = kite
                        print("[INFO] Zerodha Profile: {}".format(self.zerodha_profile_name))
                        return kite
                except Exception as e:
                    print("[WARNING] Saved Zerodha token invalid: {}, generating new one".format(str(e)))

            # If manual request token provided, use it directly
            if manual_request_token:
                print("[INFO] Using manual request token for authentication")
                try:
                    data = kite.generate_session(
                        request_token=manual_request_token,
                        api_secret=self.api_secret
                    )
                    access_token = data["access_token"]
                    
                    # Save the access token
                    with open(self.access_token_file, "w", encoding="utf-8") as f:
                        f.write(access_token)
                    
                    kite.set_access_token(access_token)
                    profile = kite.profile()
                    self.zerodha_profile_name = profile['user_name']
                    self._authenticated = True
                    self._last_auth_attempt = datetime.now()
                    self.kite = kite
                    print("[SUCCESS] Manual authentication successful - Profile: {}".format(self.zerodha_profile_name))
                    return kite
                except Exception as e:
                    print("[ERROR] Manual authentication failed: {}".format(str(e)))
                    raise Exception("Manual authentication failed: {}".format(str(e)))

            # Generate new token - fully automatic method from BBSC
            print("[INFO] Generating new Zerodha access token...")
            http_session = requests.Session()
            url = http_session.get(url='https://kite.trade/connect/login?v=3&api_key={}'.format(self.api_key)).url
            
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={'user_id': self.user_id, 'password': self.password}
            )
            
            resp_dict = json.loads(response.content)
            if resp_dict.get("status") != "success":
                error_msg = "[ERROR] Zerodha login failed: {}".format(resp_dict.get('message', 'Unknown error'))
                print(error_msg)
                raise Exception(error_msg)

            totp_value = pyotp.TOTP(self.totp_key).now()
            print("[INFO] Using TOTP value: {}".format(totp_value))
            
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
                error_msg = "[ERROR] Zerodha request token not found: {}".format(final_response)
                print(error_msg)
                raise Exception(error_msg)

            request_token = query_params['request_token'][0]
            print("[INFO] Request token obtained: {}".format(request_token[:20] + "..."))
            
            data = kite.generate_session(request_token, self.api_secret)
            access_token = data["access_token"]
            kite.set_access_token(access_token)

            with open(self.access_token_file, "w", encoding="utf-8") as f:
                f.write(access_token)
            print("[INFO] Zerodha Access Token Saved: {}".format(access_token[:20] + "..."))

            profile = kite.profile()
            self.zerodha_profile_name = profile['user_name']
            self._authenticated = True
            self._last_auth_attempt = datetime.now()
            self.kite = kite
            print("[INFO] Zerodha Profile: {}".format(self.zerodha_profile_name))
            return kite
        
        except Exception as e:
            error_msg = "[ERROR] Zerodha authentication failed: {}".format(str(e))
            print(error_msg)
            self._authenticated = False
            self.kite = None
            self.zerodha_profile_name = None
            raise Exception(error_msg)
    
    def get_kite_instance(self):
        return self.kite if self._authenticated else None
    
    def is_authenticated(self):
        return self._authenticated
    
    def validate_existing_token(self):
        """Validate existing token without triggering full authentication"""
        try:
            if not os.path.exists(self.access_token_file):
                print("[INFO] No access token file found")
                return False
            
            with open(self.access_token_file, "r", encoding="utf-8") as f:
                access_token = f.read().strip()
            
            if not access_token:
                print("[INFO] Access token file is empty")
                return False
            
            print("[INFO] Validating existing access token...")
            
            # Create KiteConnect instance and test the token
            test_kite = KiteConnect(api_key=self.api_key)
            test_kite.set_access_token(access_token)
            
            try:
                # Quick API call to test token validity
                profile = test_kite.profile()
                
                # Token is valid, set up the instance
                self.kite = test_kite
                self.zerodha_profile_name = profile['user_name']
                self._authenticated = True
                self._last_auth_attempt = datetime.now()
                
                print("[SUCCESS] Existing token is valid - Profile: {}".format(self.zerodha_profile_name))
                return True
                
            except Exception as e:
                # Handle Unicode errors safely
                try:
                    error_str = str(e)
                except UnicodeDecodeError:
                    error_str = str(e).encode('ascii', 'replace').decode('ascii')
                print("[ERROR] Existing token is invalid: {}".format(error_str))
                # Clean up invalid state
                self._authenticated = False
                self.kite = None
                self.zerodha_profile_name = None
                return False
                
        except Exception as e:
            # Handle Unicode errors safely
            try:
                error_str = str(e)
            except UnicodeDecodeError:
                error_str = str(e).encode('ascii', 'replace').decode('ascii')
            print("[ERROR] Error validating token: {}".format(error_str))
            return False
    
    def get_auth_status(self):
        """Get detailed authentication status"""
        return {
            "authenticated": self._authenticated,
            "profile_name": self.zerodha_profile_name,
            "has_kite_instance": self.kite is not None,
            "last_auth_attempt": self._last_auth_attempt.isoformat() if self._last_auth_attempt else None,
            "token_file_exists": os.path.exists(self.access_token_file)
        }
    
    @property
    def profile_name(self):
        return self.zerodha_profile_name