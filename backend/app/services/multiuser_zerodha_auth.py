# backend/app/services/multiuser_zerodha_auth.py - User-Specific Zerodha Authentication
import os
import json
import pyotp
import requests
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from typing import Dict, Optional
from ..config import settings
from ..database import UserDB, UserService

# Import our foundation utilities for better error handling and logging
from .utils.error_handler import ErrorHandler
from .utils.logger import LoggerFactory
from .utils.date_time_utils import DateTimeUtils
from .utils.config import InvestmentConfig, ErrorCodes
from .base.base_service import BaseService

class MultiUserZerodhaAuth(BaseService):
    """User-specific Zerodha authentication - each user has their own API key/secret"""
    
    def __init__(self, user: UserDB):
        # Initialize base service with user context
        super().__init__(
            service_name="multiuser_zerodha_auth",
            user_context=f"User {user.username}"
        )
        
        self.user = user
        
        # Get user's decrypted Zerodha credentials
        try:
            credentials = UserService.get_decrypted_zerodha_credentials(user)
            self.api_key = credentials["api_key"]
            self.api_secret = credentials["api_secret"]
        except Exception as e:
            self.log_error("credential_decryption", e)
            raise
        
        # User-specific token file
        self.access_token_file = user.zerodha_access_token_file
        
        # Ensure user directory exists
        try:
            os.makedirs(os.path.dirname(self.access_token_file), exist_ok=True)
        except Exception as e:
            self.log_error("directory_creation", e)
        
        # Instance variables
        self.kite = None
        self._authenticated = False
        self.zerodha_profile_name = None
        self._last_auth_attempt = None
    
    def authenticate(self, manual_request_token=None):
        """User-specific Zerodha authentication - MANUAL LOGIN ONLY"""
        with self.operation_context("authenticate") as ctx:
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
                            self._last_auth_attempt = DateTimeUtils.get_current_timestamp()
                            self.kite = kite
                            self.log_success("existing_token_auth", f"Zerodha Profile: {self.zerodha_profile_name}")
                            ctx.set_result(kite)
                            return kite
                    except Exception as e:
                        self.log_warning("existing_token_validation", f"Saved token invalid: {str(e)}")

                # MANUAL AUTHENTICATION ONLY - Require request token
                if not manual_request_token:
                    error_msg = "Manual request token required. Please use the login URL to get request token."
                    self.log_error("manual_auth_required", Exception(error_msg))
                    raise Exception(error_msg)

                self.log_info("manual_authentication", "Using manual request token")
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
                    self._last_auth_attempt = DateTimeUtils.get_current_timestamp()
                    self.kite = kite
                    self.log_success("manual_auth", f"Authentication successful: {self.zerodha_profile_name}")
                    ctx.set_result(kite)
                    return kite
                except Exception as e:
                    self.log_error("manual_auth_failed", e)
                    raise Exception(f"Manual authentication failed: {str(e)}")
            
            except Exception as e:
                self._authenticated = False
                self.kite = None
                self.zerodha_profile_name = None
                raise Exception(f"Zerodha authentication failed: {str(e)}")
    
    def get_kite_instance(self):
        return self.kite if self._authenticated else None
    
    def is_authenticated(self):
        return self._authenticated
    
    def validate_existing_token(self):
        """Validate existing token without triggering full authentication"""
        with self.operation_context("validate_existing_token") as ctx:
            try:
                if not os.path.exists(self.access_token_file):
                    self.log_info("token_validation", "No access token file found")
                    ctx.set_result(False)
                    return False
                
                with open(self.access_token_file, "r", encoding="utf-8") as f:
                    access_token = f.read().strip()
                
                if not access_token:
                    self.log_info("token_validation", "Access token file is empty")
                    ctx.set_result(False)
                    return False
                
                self.log_info("token_validation", "Validating existing access token...")
                
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
                    self._last_auth_attempt = DateTimeUtils.get_current_timestamp()
                    
                    self.log_success("token_validation", f"Token valid, Profile: {self.zerodha_profile_name}")
                    ctx.set_result(True)
                    return True
                    
                except Exception as e:
                    self.log_error("token_validation", e)
                    # Clean up invalid state
                    self._authenticated = False
                    self.kite = None
                    self.zerodha_profile_name = None
                    ctx.set_result(False)
                    return False
                    
            except Exception as e:
                self.log_error("validate_existing_token", e)
                ctx.set_result(False)
                return False
    
    def get_auth_status(self):
        """Get detailed authentication status for this user"""
        try:
            return {
                "user_id": self.user.id,
                "username": self.user.username,
                "authenticated": self._authenticated,
                "profile_name": self.zerodha_profile_name,
                "has_kite_instance": self.kite is not None,
                "last_auth_attempt": self._last_auth_attempt if isinstance(self._last_auth_attempt, str) else (self._last_auth_attempt.isoformat() if self._last_auth_attempt else None),
                "token_file_exists": os.path.exists(self.access_token_file),
                "service_info": self.get_service_info(),
                "timestamp": self.get_current_timestamp()
            }
        except Exception as e:
            self.log_error("get_auth_status", e)
            return {
                "user_id": self.user.id if self.user else None,
                "username": self.user.username if self.user else None,
                "authenticated": False,
                "error": str(e)
            }
    
    def force_refresh_token(self):
        """Force refresh token by clearing cache and re-validating"""
        with self.operation_context("force_refresh_token") as ctx:
            try:
                self.log_info("force_refresh", "Forcing token refresh")
                
                # Clear current authentication state
                self._authenticated = False
                self.kite = None
                self.zerodha_profile_name = None
                
                # Try to validate existing token (this will refresh if needed)
                success = self.validate_existing_token()
                
                if success and self.kite:
                    self.log_success("force_refresh", "Token refresh successful")
                    ctx.set_result(self.kite)
                    return self.kite
                else:
                    self.log_warning("force_refresh", "Token refresh failed - manual authentication required")
                    ctx.set_result(None)
                    return None
                    
            except Exception as e:
                self.log_error("force_refresh_token", e)
                ctx.set_result(None)
                return None

    @property
    def profile_name(self):
        return self.zerodha_profile_name


# User-specific Zerodha authentication manager
class ZerodhaAuthManager(BaseService):
    """Manages Zerodha authentication instances for multiple users"""
    
    def __init__(self):
        super().__init__(service_name="zerodha_auth_manager")
        self._user_auths: Dict[str, MultiUserZerodhaAuth] = {}
    
    def get_user_auth(self, user: UserDB) -> MultiUserZerodhaAuth:
        """Get or create user-specific Zerodha auth instance"""
        try:
            if user.id not in self._user_auths:
                self.log_info("create_user_auth", f"Creating auth instance for user: {user.username}")
                self._user_auths[user.id] = MultiUserZerodhaAuth(user)
            return self._user_auths[user.id]
        except Exception as e:
            self.log_error("get_user_auth", e, user_id=user.id, username=user.username)
            raise
    
    def remove_user_auth(self, user_id: str) -> None:
        """Remove user auth instance (e.g., on logout)"""
        try:
            if user_id in self._user_auths:
                auth_instance = self._user_auths[user_id]
                username = auth_instance.user.username if hasattr(auth_instance, 'user') else "unknown"
                del self._user_auths[user_id]
                self.log_info("remove_user_auth", f"Removed auth instance for user: {username}")
            else:
                self.log_info("remove_user_auth", f"No auth instance found for user_id: {user_id}")
        except Exception as e:
            self.log_error("remove_user_auth", e, user_id=user_id)
    
    def get_all_authenticated_users(self) -> Dict[str, str]:
        """Get all currently authenticated users"""
        try:
            authenticated = {}
            for user_id, auth in self._user_auths.items():
                if auth.is_authenticated():
                    authenticated[user_id] = auth.profile_name
            
            self.log_info("get_authenticated_users", f"Found {len(authenticated)} authenticated users")
            return authenticated
        except Exception as e:
            self.log_error("get_all_authenticated_users", e)
            return {}

# Global auth manager instance
zerodha_auth_manager = ZerodhaAuthManager()