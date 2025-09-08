# backend/app/main_multiuser_v2.py - Multi-User Investment Rebalancing WebApp
from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import json

from .database import get_db, UserService, UserDB
from .models import UserCreate, LoginRequest, Token, AuthResponse, UserResponse, ZerodhaAuthRequest
from .auth_multiuser import create_access_token, get_current_user, get_current_admin_user
from .services.service_hub import service_hub
from .config import settings

app = FastAPI(title="Multi-User Investment Rebalancing WebApp", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status tracking
app_status = {
    "initialized": True,
    "multi_user_enabled": True,
    "database_connected": True,
    "active_users": 0,
    "total_registrations": 0
}

@app.get("/")
async def root():
    return {
        "message": "Multi-User Investment Rebalancing WebApp API v3.0",
        "status": app_status,
        "features": [
            "✅ Multi-user support with JWT authentication",
            "✅ User-specific Zerodha connections", 
            "✅ Isolated user data and portfolios",
            "✅ SQLite database with encrypted credentials",
            "✅ All existing features preserved per user"
        ],
        "available_endpoints": [
            "/health - System health check",
            "/api/register - Register new user",
            "/api/login - User login", 
            "/api/users/me - Get current user profile",
            "/api/auth-status - Get user auth status with Zerodha",
            "/api/zerodha-login-url - Get Zerodha login URL",
            "/api/exchange-token - Exchange Zerodha token",
            "/api/investment/* - All investment endpoints (user-specific)",
            "--- All existing single-user endpoints now work per-user ---"
        ]
    }

@app.get("/health")
async def health_check():
    """System health check"""
    db = next(get_db())
    try:
        # Count total users
        users = UserService.list_users(db)
        
        # Get service status from ServiceHub
        service_status = service_hub.get_service_status()
        
        app_status["total_registrations"] = len(users)
        app_status["active_users"] = len(service_status["zerodha_auth"]["authenticated_users"])
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "multi_user": app_status,
            "service_hub_status": service_status,
            "authenticated_users": service_status["zerodha_auth"]["authenticated_users"]
        }
    except Exception as e:
        return {
            "status": "degraded", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        db.close()

# === USER MANAGEMENT ENDPOINTS ===

@app.post("/api/register", response_model=AuthResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Create the user
        db_user = UserService.create_user(db, user_data)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user.id, "username": db_user.username},
            expires_delta=access_token_expires
        )
        
        token = Token(
            access_token=access_token,
            user_id=db_user.id,
            username=db_user.username,
            full_name=db_user.full_name
        )
        
        return AuthResponse(
            success=True,
            message=f"User {user_data.username} registered successfully",
            token=token,
            user={
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "is_active": db_user.is_active,
                "created_at": db_user.created_at
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/login", response_model=AuthResponse)
async def login_user(login_data: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    try:
        # Authenticate user
        user = UserService.authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        UserService.update_last_login(db, user.id)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "username": user.username},
            expires_delta=access_token_expires
        )
        
        token = Token(
            access_token=access_token,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name
        )
        
        return AuthResponse(
            success=True,
            message=f"Welcome back {user.full_name}!",
            token=token,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/api/users/me")
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Get current user information"""
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at,
            "last_login": current_user.last_login
        }
    }

# === ZERODHA AUTHENTICATION (USER-SPECIFIC) ===

@app.get("/api/auth-status")
async def get_user_auth_status(current_user: UserDB = Depends(get_current_user)):
    """Get user's Zerodha authentication status with real API validation"""
    try:
        # Get user's Zerodha auth instance through ServiceHub
        zerodha_auth = service_hub.get_zerodha_auth(current_user)
        
        # Always perform real API validation instead of just checking cached state
        is_auth = False
        profile_name = None
        
        # Test the actual Zerodha connection with a real API call
        try:
            if os.path.exists(zerodha_auth.access_token_file):
                print(f"[INFO] User {current_user.username} - Testing actual Zerodha API connection...")
                
                # Load the kite instance and test with a real API call
                kite = zerodha_auth.get_kite_instance()
                if kite:
                    # Test with actual API call to profile
                    profile = kite.profile()
                    if profile and profile.get('user_name'):
                        is_auth = True
                        profile_name = profile.get('user_name')
                        print(f"[OK] User {current_user.username} - Real API validation successful: {profile_name}")
                    else:
                        print(f"[ERROR] User {current_user.username} - API call returned invalid profile")
                else:
                    print(f"[ERROR] User {current_user.username} - Could not get kite instance")
            else:
                print(f"[INFO] User {current_user.username} - No token file exists")
                
        except Exception as api_error:
            print(f"[ERROR] User {current_user.username} - Real API validation failed: {api_error}")
            is_auth = False
            profile_name = None
        
        return {
            "success": True,
            "authenticated": is_auth,
            "profile_name": profile_name,
            "user": current_user.username,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "authenticated": False,
            "error": f"Status check error: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/zerodha-login-url")
async def get_zerodha_login_url(current_user: UserDB = Depends(get_current_user)):
    """Get Zerodha login URL for current user using their API key"""
    try:
        # Get user's API key through ServiceHub
        zerodha_auth = service_hub.get_zerodha_auth(current_user)
        user_api_key = zerodha_auth.api_key
        
        login_url = f"https://kite.zerodha.com/connect/login?api_key={user_api_key}"
        
        return {
            "success": True,
            "login_url": login_url,
            "user": current_user.username,
            "api_key": user_api_key[:10] + "..." if user_api_key else "Not set",
            "instructions": [
                "Click the login URL",
                "Login to your Zerodha account", 
                "After login, copy the 'request_token' from the redirect URL",
                "Use the request_token with the /api/exchange-token endpoint"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate login URL: {str(e)}"
        }

@app.post("/api/exchange-token")
async def exchange_zerodha_token(
    request_data: ZerodhaAuthRequest,
    current_user: UserDB = Depends(get_current_user)
):
    """Exchange request token for access token (user-specific)"""
    try:
        # Get user's Zerodha auth instance through ServiceHub
        zerodha_auth = service_hub.get_zerodha_auth(current_user)
        
        request_token = request_data.request_token if request_data else None
        
        # Authenticate with user's specific credentials
        if request_token:
            print(f"[INFO] User {current_user.username} - Using manual token: {request_token[:10]}...")
            kite = zerodha_auth.authenticate(manual_request_token=request_token)
        else:
            print(f"[INFO] User {current_user.username} - Attempting automatic authentication...")
            kite = zerodha_auth.authenticate()
        
        if zerodha_auth.is_authenticated():
            profile_name = zerodha_auth.profile_name
            print(f"[SUCCESS] User {current_user.username} - Authentication successful: {profile_name}")
            return {
                "success": True,
                "message": "Zerodha authentication successful",
                "profile_name": profile_name,
                "user": current_user.username,
                "authenticated": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Authentication failed - please check credentials",
                "user": current_user.username
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Authentication failed: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/auto-authenticate")
async def auto_authenticate_zerodha(current_user: UserDB = Depends(get_current_user)):
    """Trigger automatic Zerodha authentication for current user"""
    try:
        # Get user's Zerodha auth instance through ServiceHub
        zerodha_auth = service_hub.get_zerodha_auth(current_user)
        
        print(f"[INFO] User {current_user.username} - Starting automatic authentication...")
        kite = zerodha_auth.authenticate()
        
        if zerodha_auth.is_authenticated():
            profile_name = zerodha_auth.profile_name
            print(f"[SUCCESS] User {current_user.username} - Auto auth successful: {profile_name}")
            return {
                "success": True,
                "message": "Automatic authentication successful",
                "profile_name": profile_name,
                "user": current_user.username,
                "authenticated": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Automatic authentication failed",
                "user": current_user.username
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Automatic authentication failed: {str(e)}",
            "user": current_user.username
        }

# === USER-SPECIFIC INVESTMENT ENDPOINTS ===

@app.get("/api/investment/status")
async def get_investment_status(current_user: UserDB = Depends(get_current_user)):
    """Get user's investment status"""
    try:
        print(f"[DEBUG] API ENDPOINT - get_investment_status called for user {current_user.username}")
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        print(f"[DEBUG] API ENDPOINT - About to call investment_service.get_investment_status()")
        result = investment_service.get_investment_status()
        print(f"[DEBUG] API ENDPOINT - get_investment_status result: {result}")
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get investment status: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/portfolio-status")
async def get_portfolio_status(current_user: UserDB = Depends(get_current_user)):
    """Get user's portfolio status for dashboard"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        return investment_service.get_portfolio_status()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get portfolio status: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/system-orders")
async def get_system_orders(current_user: UserDB = Depends(get_current_user)):
    """Get user's system orders"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        return investment_service.get_system_orders()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get system orders: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/reset-orders")
async def reset_system_orders(current_user: UserDB = Depends(get_current_user)):
    """Reset user's system orders (for testing purposes)"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        # Reset user's orders by saving empty array
        user_orders_file = investment_service.orders_file
        with open(user_orders_file, 'w') as f:
            json.dump([], f)
        
        print(f"[INFO] User {current_user.username} - System orders have been reset")
        
        return {
            "success": True,
            "message": "User's system orders have been reset",
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to reset orders: {e}")
        return {
            "success": False,
            "error": f"Failed to reset system orders: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/csv-stocks")
async def get_csv_stocks(current_user: UserDB = Depends(get_current_user)):
    """Get CSV stocks with current prices (shared data but user-specific pricing)"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        return investment_service.get_csv_stocks()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get CSV stocks: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/live-orders")
async def get_live_orders(current_user: UserDB = Depends(get_current_user)):
    """Get user's live orders"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        return investment_service.get_live_orders()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get live orders: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/failed-orders")
async def get_failed_orders(current_user: UserDB = Depends(get_current_user)):
    """Get user's failed orders"""
    try:
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        return investment_service.get_failed_orders()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get failed orders: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/execute-live-orders")
async def execute_live_orders(current_user: UserDB = Depends(get_current_user)):
    """Execute all PENDING orders by sending them to Zerodha"""
    try:
        print(f"[INFO] User {current_user.username} - Executing live orders...")
        
        # Get user-specific investment service through ServiceHub
        investment_service = service_hub.get_investment_service(current_user)
        
        if not investment_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Get all PENDING orders
        orders = investment_service._load_orders()
        pending_orders = [order for order in orders if order.get('status') == 'PENDING']
        
        if not pending_orders:
            return {
                "success": True,
                "message": "No pending orders to execute",
                "orders_executed": 0,
                "user": current_user.username
            }
        
        print(f"[INFO] User {current_user.username} - Found {len(pending_orders)} pending orders to execute")
        
        # Use the professional execute orders method
        execution_result = investment_service._execute_orders_to_zerodha(pending_orders)
        
        # Save updated orders
        investment_service._save_orders(orders)
        
        return {
            "success": True,
            "message": execution_result['message'],
            "orders_executed": execution_result['orders_sent_successfully'],
            "orders_failed": execution_result['orders_failed'],
            "total_orders": execution_result['total_orders'],
            "execution_results": execution_result['execution_results'],
            "user": current_user.username
        }
        
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to execute live orders: {e}")
        return {
            "success": False,
            "error": f"Failed to execute live orders: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/requirements")
async def get_investment_requirements(
    current_user: UserDB = Depends(get_current_user)
):
    """Get investment requirements for initial setup"""
    try:
        print(f"[INFO] User {current_user.username} - Getting investment requirements...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        requirements = user_service.get_investment_requirements()
        return {
            "success": True,
            "requirements": requirements,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to get investment requirements: {e}")
        return {
            "success": False,
            "error": f"Failed to get investment requirements: {str(e)}",
            "user": current_user.username
        }

@app.get("/api/investment/orders-with-retries")
async def get_orders_with_retry_history(
    current_user: UserDB = Depends(get_current_user)
):
    """Get all orders grouped by parent with their retry history"""
    try:
        print(f"[INFO] User {current_user.username} - Getting orders with retry history...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Get orders with retries from the service
        orders_with_retries = []
        if hasattr(user_service, 'get_orders_with_retry_history'):
            orders_with_retries = user_service.get_orders_with_retry_history()
        else:
            # Fallback - return empty if method doesn't exist
            orders_with_retries = []
        
        return {
            "success": True,
            "data": {
                "orders_with_retry_history": orders_with_retries
            },
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to get orders with retries: {e}")
        return {
            "success": False,
            "error": f"Failed to get orders with retries: {str(e)}",
            "data": {
                "orders_with_retry_history": []
            },
            "user": current_user.username
        }

@app.get("/api/investment/monitoring-status")
async def get_monitoring_status(
    current_user: UserDB = Depends(get_current_user)
):
    """Get current monitoring status"""
    try:
        print(f"[INFO] User {current_user.username} - Getting monitoring status...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Get monitoring status from the service
        monitoring_status = {}
        if hasattr(user_service, 'get_monitoring_status'):
            monitoring_status = user_service.get_monitoring_status()
        else:
            # Fallback - return default status
            monitoring_status = {
                "monitoring_active": False,
                "last_check": None,
                "pending_orders": 0,
                "completed_orders": 0
            }
        
        return {
            "success": True,
            "monitoring_status": monitoring_status,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to get monitoring status: {e}")
        return {
            "success": False,
            "error": f"Failed to get monitoring status: {str(e)}",
            "monitoring_status": {"monitoring_active": False},
            "user": current_user.username
        }

@app.post("/api/investment/calculate-plan")
async def calculate_investment_plan(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Calculate initial investment plan"""
    try:
        investment_amount = request.get("investment_amount")
        if not investment_amount:
            raise HTTPException(status_code=400, detail="Investment amount is required")
            
        print(f"[INFO] User {current_user.username} - Calculating investment plan for amount: {investment_amount}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        plan = user_service.calculate_initial_investment_plan(investment_amount)
        return {
            "success": True,
            "plan": plan,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to calculate investment plan: {e}")
        return {
            "success": False,
            "error": f"Failed to calculate investment plan: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/execute-initial")
async def execute_initial_investment(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Execute initial investment"""
    try:
        investment_amount = request.get("investment_amount")
        if not investment_amount:
            raise HTTPException(status_code=400, detail="Investment amount is required")
            
        print(f"[INFO] User {current_user.username} - Executing initial investment for amount: {investment_amount}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        result = user_service.execute_initial_investment(investment_amount)
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to execute initial investment: {e}")
        return {
            "success": False,
            "error": f"Failed to execute initial investment: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/calculate-rebalancing")
async def calculate_rebalancing(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Calculate rebalancing plan"""
    try:
        additional_investment = request.get("additional_investment", 0)
        print(f"[INFO] User {current_user.username} - Calculating rebalancing with additional investment: {additional_investment}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        plan = user_service.calculate_rebalancing_plan(additional_investment)
        return {
            "success": True,
            "plan": plan,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to calculate rebalancing: {e}")
        return {
            "success": False,
            "error": f"Failed to calculate rebalancing: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/execute-rebalancing")
async def execute_rebalancing(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Execute rebalancing"""
    try:
        additional_investment = request.get("additional_investment", 0)
        print(f"[INFO] User {current_user.username} - Executing rebalancing with additional investment: {additional_investment}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        result = user_service.execute_rebalancing(additional_investment)
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to execute rebalancing: {e}")
        return {
            "success": False,
            "error": f"Failed to execute rebalancing: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/force-csv-refresh")
async def force_csv_refresh(
    current_user: UserDB = Depends(get_current_user)
):
    """Force refresh of CSV stocks data"""
    try:
        print(f"[INFO] User {current_user.username} - Forcing CSV refresh...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Force refresh CSV data
        if hasattr(user_service, 'force_csv_refresh'):
            result = user_service.force_csv_refresh()
        else:
            # Fallback - just return success
            result = {"message": "CSV refresh not implemented for user service"}
        
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to force CSV refresh: {e}")
        return {
            "success": False,
            "error": f"Failed to force CSV refresh: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/retry-orders")
async def retry_failed_orders(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Retry failed orders"""
    try:
        order_ids = request.get("order_ids", None)
        print(f"[INFO] User {current_user.username} - Retrying failed orders: {order_ids}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Retry failed orders
        if hasattr(user_service, 'retry_failed_orders'):
            result = user_service.retry_failed_orders(order_ids)
        else:
            # Fallback - just return success
            result = {"message": "Order retry not implemented for user service"}
        
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to retry failed orders: {e}")
        return {
            "success": False,
            "error": f"Failed to retry failed orders: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/start-monitoring")
async def start_order_monitoring(
    current_user: UserDB = Depends(get_current_user)
):
    """Start automatic order monitoring for current user"""
    # Test endpoint
    try:
        print(f"[INFO] User {current_user.username} - Starting order monitoring...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Start monitoring
        result = user_service.start_order_monitoring()
        
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to start monitoring: {e}")
        return {
            "success": False,
            "error": f"Failed to start monitoring: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/stop-monitoring")
async def stop_order_monitoring(
    current_user: UserDB = Depends(get_current_user)
):
    """Stop automatic order monitoring for current user"""
    try:
        print(f"[INFO] User {current_user.username} - Stopping order monitoring...")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Stop monitoring
        result = user_service.stop_order_monitoring()
        
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to stop monitoring: {e}")
        return {
            "success": False,
            "error": f"Failed to stop monitoring: {str(e)}",
            "user": current_user.username
        }

@app.post("/api/investment/update-order-status")
async def update_order_status_from_zerodha(
    request: dict = Body(...),
    current_user: UserDB = Depends(get_current_user)
):
    """Manually update order status from Zerodha API"""
    try:
        zerodha_order_id = request.get("zerodha_order_id", None)
        print(f"[INFO] User {current_user.username} - Updating order status from Zerodha: {zerodha_order_id}")
        
        # Get user-specific investment service through ServiceHub
        user_service = service_hub.get_investment_service(current_user)
        if not user_service:
            raise HTTPException(
                status_code=500, 
                detail="Investment service not initialized for user"
            )
        
        # Update order status
        result = user_service.update_order_status_from_zerodha(zerodha_order_id)
        
        return {
            "success": True,
            "result": result,
            "user": current_user.username
        }
    except Exception as e:
        print(f"[ERROR] User {current_user.username} - Failed to update order status: {e}")
        return {
            "success": False,
            "error": f"Failed to update order status: {str(e)}",
            "user": current_user.username
        }

# === ADMIN ENDPOINTS ===

@app.get("/api/admin/users")
async def list_all_users(
    current_admin: UserDB = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = UserService.list_users(db)
    return {
        "success": True,
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ],
        "total_users": len(users)
    }

@app.get("/api/admin/system-status")
async def get_system_status(current_admin: UserDB = Depends(get_current_admin_user)):
    """Get detailed system status (admin only)"""
    # Get comprehensive system status from ServiceHub
    service_status = service_hub.get_service_status()
    
    return {
        "success": True,
        "system_status": app_status,
        "service_hub_status": service_status,
        "authenticated_users": service_status["zerodha_auth"]["authenticated_users"],
        "active_services": service_status["investment_services"]["active_services_count"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)