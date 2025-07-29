# backend/app/routers/auth_simple.py - Simplified Zerodha Auth
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from ..auth import ZerodhaAuth
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Global auth instance
zerodha_auth = ZerodhaAuth()

class RequestTokenRequest(BaseModel):
    request_token: str

@router.get("/zerodha-login-url")
async def get_zerodha_login_url():
    """Get Zerodha login URL for manual authentication"""
    try:
        login_url = f"https://kite.trade/connect/login?v=3&api_key={settings.ZERODHA_API_KEY}"
        
        return {
            "success": True,
            "data": {
                "login_url": login_url,
                "api_key": settings.ZERODHA_API_KEY,
                "instructions": [
                    "1. Click the login URL above",
                    "2. Login to your Zerodha account",
                    "3. After successful login, copy the 'request_token' from the redirect URL",
                    "4. Paste the request_token below to complete authentication"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate login URL: {str(e)}")

@router.post("/exchange-token")
async def exchange_request_token(request: RequestTokenRequest):
    """Exchange request token for access token"""
    try:
        if not request.request_token:
            raise HTTPException(status_code=400, detail="Request token is required")
        
        # Generate session using request token
        session_data = zerodha_auth.kite.generate_session(
            request.request_token, 
            settings.ZERODHA_API_SECRET
        )
        
        access_token = session_data["access_token"]
        
        # Set access token
        zerodha_auth.kite.set_access_token(access_token)
        
        # Get and store profile
        profile = zerodha_auth.kite.profile()
        zerodha_auth.zerodha_profile_name = profile['user_name']
        zerodha_auth._authenticated = True
        
        # Save token to file for persistence
        os.makedirs(os.path.dirname(settings.ZERODHA_ACCESS_TOKEN_FILE) if os.path.dirname(settings.ZERODHA_ACCESS_TOKEN_FILE) else '.', exist_ok=True)
        with open(settings.ZERODHA_ACCESS_TOKEN_FILE, "w") as f:
            f.write(access_token)
        
        return {
            "success": True,
            "data": {
                "access_token": access_token,
                "profile_name": profile['user_name'],
                "user_id": profile['user_id'],
                "message": f"Successfully authenticated as {profile['user_name']}"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")

@router.get("/status")
async def get_auth_status():
    """Get current authentication status"""
    try:
        # Check if we have a valid token
        if os.path.exists(settings.ZERODHA_ACCESS_TOKEN_FILE):
            with open(settings.ZERODHA_ACCESS_TOKEN_FILE, "r") as f:
                access_token = f.read().strip()
            
            if access_token:
                try:
                    # Test the token
                    zerodha_auth.kite.set_access_token(access_token)
                    profile = zerodha_auth.kite.profile()
                    
                    zerodha_auth._authenticated = True
                    zerodha_auth.zerodha_profile_name = profile['user_name']
                    
                    return {
                        "success": True,
                        "data": {
                            "authenticated": True,
                            "profile_name": profile['user_name'],
                            "user_id": profile['user_id'],
                            "token_valid": True
                        }
                    }
                    
                except Exception as token_error:
                    # Token is invalid, remove it
                    try:
                        os.remove(settings.ZERODHA_ACCESS_TOKEN_FILE)
                    except:
                        pass
                    
                    return {
                        "success": True,
                        "data": {
                            "authenticated": False,
                            "profile_name": None,
                            "token_valid": False,
                            "message": "Stored token is invalid"
                        }
                    }
        
        # No token found
        return {
            "success": True,
            "data": {
                "authenticated": False,
                "profile_name": None,
                "token_valid": False,
                "message": "No authentication token found"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check auth status: {str(e)}")

@router.post("/logout")
async def logout():
    """Logout and clear stored token"""
    try:
        # Clear stored token
        if os.path.exists(settings.ZERODHA_ACCESS_TOKEN_FILE):
            os.remove(settings.ZERODHA_ACCESS_TOKEN_FILE)
        
        # Reset auth state
        zerodha_auth._authenticated = False
        zerodha_auth.zerodha_profile_name = None
        zerodha_auth.kite = None
        
        return {
            "success": True,
            "data": {
                "message": "Successfully logged out"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")