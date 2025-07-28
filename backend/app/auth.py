# backend/app/auth.py - FIXED VERSION

import os
import json
import pyotp
import requests
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from .config import settings
import time
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
        self._auth_retry_delay = 60  # Wait 60 seconds between auth attempts
        
    def authenticate(self):
        """Enhanced authentication with better error handling and retry logic"""
        try:
            # Check if we recently failed authentication
            if self._last_auth_attempt:
                time_since_last = (datetime.now() - self._last_auth_attempt).total_seconds()
                if time_since_last < self._auth_retry_delay:
                    remaining = self._auth_retry_delay - time_since_last
                    print(f"⏰ Authentication retry cooldown: {remaining:.0f}s remaining")
                    return None
            
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Step 1: Try existing token first
            if self._try_existing_token():
                return self.kite
            
            print("🔐 Generating new Zerodha access token...")
            
            # Step 2: Check if we have all required credentials
            if not all([self.api_key, self.api_secret, self.user_id, self.password, self.totp_key]):
                raise Exception("Missing required Zerodha credentials. Please check your configuration.")
            
            # Step 3: Perform authentication flow
            access_token = self._perform_auth_flow()
            
            if access_token:
                # Step 4: Save and verify token
                self._save_and_verify_token(access_token)
                self._authenticated = True
                print(f"✅ Authentication successful! Profile: {self.zerodha_profile_name}")
                return self.kite
            else:
                raise Exception("Failed to obtain access token")
                
        except Exception as e:
            self._last_auth_attempt = datetime.now()
            print(f"❌ Zerodha authentication failed: {e}")
            self._authenticated = False
            return None
    
    def _try_existing_token(self) -> bool:
        """Try to use existing saved token"""
        try:
            if os.path.exists(self.access_token_file):
                with open(self.access_token_file, "r") as f:
                    access_token = f.read().strip()
                
                if access_token:
                    self.kite.set_access_token(access_token)
                    
                    # Verify token by getting profile
                    profile = self.kite.profile()
                    self.zerodha_profile_name = profile['user_name']
                    self._authenticated = True
                    print(f"✅ Using existing token. Profile: {self.zerodha_profile_name}")
                    return True
                    
        except Exception as e:
            print(f"⚠️ Existing token invalid: {str(e)}")
            # Clean up invalid token file
            if os.path.exists(self.access_token_file):
                try:
                    os.remove(self.access_token_file)
                except:
                    pass
        
        return False
    
    def _perform_auth_flow(self) -> str:
        """Perform the complete Zerodha authentication flow using the WORKING method from notebook"""
        try:
            # Use the EXACT method from your working Jupyter notebook
            http_session = requests.Session()
            
            # Step 1: Get login URL (EXACTLY like notebook)
            url = http_session.get(url=f'https://kite.trade/connect/login?v=3&api_key={self.api_key}').url
            print(f"🌐 Login URL obtained: {url}")
            
            # Step 2: Login with credentials (EXACTLY like notebook)
            print(f"🔐 Logging in with user ID: {self.user_id}")
            response = http_session.post(
                url='https://kite.zerodha.com/api/login',
                data={'user_id': self.user_id, 'password': self.password}
            )
            
            print(f"📝 Login response status: {response.status_code}")
            
            # Parse response - EXACTLY like notebook
            try:
                resp_dict = json.loads(response.content)
                print(f"📋 Login response parsed successfully")
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse login response: {e}")
                print(f"❌ Raw response content type: {type(response.content)}")
                print(f"❌ Raw response headers: {dict(response.headers)}")
                
                # Try to handle compressed response
                try:
                    import gzip
                    decompressed = gzip.decompress(response.content)
                    resp_dict = json.loads(decompressed.decode('utf-8'))
                    print(f"✅ Successfully decompressed and parsed response")
                except Exception as decomp_error:
                    print(f"❌ Decompression failed: {decomp_error}")
                    raise Exception("Could not parse login response")
            
            if resp_dict.get("status") != "success":
                error_msg = resp_dict.get('message', 'Unknown login error')
                print(f"❌ Login failed: {error_msg}")
                raise Exception(f"Zerodha login failed: {error_msg}")

            print(f"✅ Login successful, request_id: {resp_dict['data']['request_id']}")

            # Step 3: TOTP verification (EXACTLY like notebook)
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

            # Step 4: Get authorization (EXACTLY like notebook)
            print(f"🎫 Getting authorization...")
            url = url + "&skip_session=true"
            final_response = http_session.get(url=url, allow_redirects=True).url
            
            print(f"🔗 Final redirect URL: {final_response}")
            
            # Step 5: Parse URL for request token (EXACTLY like notebook)
            parsed_url = urlparse(final_response)
            query_params = parse_qs(parsed_url.query)
            
            print(f"📋 Query Parameters: {query_params}")
            
            if 'request_token' not in query_params:
                print(f"❌ No request token found in final URL: {final_response}")
                raise Exception(f"No request token found: {final_response}")

            request_token = query_params['request_token'][0]
            print(f"✅ Found request_token: {request_token}")

            # Step 6: Generate access token (EXACTLY like notebook)
            print("🔐 Generating access token...")
            try:
                data = self.kite.generate_session(request_token, self.api_secret)
                access_token = data["access_token"]
                print(f"✅ Access token generated successfully")
                return access_token
            except Exception as e:
                print(f"❌ Failed to generate session: {e}")
                raise Exception(f"Failed to generate access token: {str(e)}")
                
        except Exception as e:
            print(f"❌ Authentication flow failed: {e}")
            raise
    
    def _save_and_verify_token(self, access_token: str):
        """Save token and verify by getting profile"""
        try:
            # Set token
            self.kite.set_access_token(access_token)

            # Verify with profile
            profile = self.kite.profile()
            self.zerodha_profile_name = profile['user_name']
            
            # Save token to file
            os.makedirs(os.path.dirname(self.access_token_file) if os.path.dirname(self.access_token_file) else '.', exist_ok=True)
            with open(self.access_token_file, "w") as f:
                f.write(access_token)
            print(f"💾 Access token saved to: {self.access_token_file}")
            
        except Exception as e:
            print(f"❌ Failed to save/verify token: {e}")
            raise
    
    def get_kite_instance(self):
        """Get KiteConnect instance if authenticated"""
        return self.kite if self._authenticated else None
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        if not self._authenticated or not self.kite:
            return False
        
        try:
            # Verify authentication by making a simple API call
            profile = self.kite.profile()
            return True
        except Exception as e:
            print(f"⚠️ Authentication verification failed: {e}")
            self._authenticated = False
            return False
    
    def get_profile(self) -> dict:
        """Get user profile information"""
        if not self.is_authenticated():
            return {}
        
        try:
            return self.kite.profile()
        except Exception as e:
            print(f"❌ Failed to get profile: {e}")
            return {}
    
    def get_margins(self) -> dict:
        """Get margin information"""
        if not self.is_authenticated():
            return {}
        
        try:
            return self.kite.margins()
        except Exception as e:
            print(f"❌ Failed to get margins: {e}")
            return {}
    
    def get_holdings(self) -> list:
        """Get holdings information"""
        if not self.is_authenticated():
            return []
        
        try:
            return self.kite.holdings()
        except Exception as e:
            print(f"❌ Failed to get holdings: {e}")
            return []
    
    def get_positions(self) -> dict:
        """Get positions information"""
        if not self.is_authenticated():
            return {}
        
        try:
            return self.kite.positions()
        except Exception as e:
            print(f"❌ Failed to get positions: {e}")
            return {}
    
    def quote(self, instruments: list) -> dict:
        """Get quote for instruments"""
        if not self.is_authenticated():
            return {}
        
        try:
            return self.kite.quote(instruments)
        except Exception as e:
            print(f"❌ Failed to get quotes: {e}")
            return {}
    
    def force_refresh_token(self):
        """Force refresh the access token"""
        print("🔄 Forcing token refresh...")
        
        # Remove existing token file
        if os.path.exists(self.access_token_file):
            try:
                os.remove(self.access_token_file)
                print("🗑️ Removed existing token file")
            except Exception as e:
                print(f"⚠️ Could not remove token file: {e}")
        
        # Reset authentication state
        self._authenticated = False
        self.kite = None
        self.zerodha_profile_name = None
        self._last_auth_attempt = None  # Reset cooldown
        
        # Attempt new authentication
        return self.authenticate()
    
    def get_auth_status(self) -> dict:
        """Get detailed authentication status"""
        status = {
            'authenticated': self._authenticated,
            'kite_instance': bool(self.kite),
            'profile_name': self.zerodha_profile_name,
            'token_file_exists': os.path.exists(self.access_token_file),
            'last_auth_attempt': self._last_auth_attempt.isoformat() if self._last_auth_attempt else None,
            'credentials_configured': bool(self.api_key and self.api_secret and self.user_id),
            'can_retry': True
        }
        
        # Check if we're in retry cooldown
        if self._last_auth_attempt:
            time_since_last = (datetime.now() - self._last_auth_attempt).total_seconds()
            if time_since_last < self._auth_retry_delay:
                status['can_retry'] = False
                status['retry_in_seconds'] = self._auth_retry_delay - time_since_last
        
        return status
    
    @property
    def profile_name(self):
        """Get profile name"""
        return self.zerodha_profile_name