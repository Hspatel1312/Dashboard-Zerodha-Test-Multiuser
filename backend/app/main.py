# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import traceback

app = FastAPI(title="Investment Rebalancing WebApp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to track initialization
initialization_status = {
    "config_loaded": False,
    "auth_created": False,
    "auth_successful": False,
    "service_created": False,
    "investment_service_created": False,
    "error_message": None,
    "zerodha_connection_status": "not_checked"
}

zerodha_auth = None
portfolio_service = None
investment_service = None

# Try to initialize step by step with error tracking
try:
    print("Step 1: Loading configuration...")
    from .config import settings
    initialization_status["config_loaded"] = True
    print("✅ Configuration loaded successfully")
    
    print("Step 2: Creating ZerodhaAuth instance...")
    from .auth import ZerodhaAuth
    zerodha_auth = ZerodhaAuth()
    initialization_status["auth_created"] = True
    print("✅ ZerodhaAuth instance created")
    
    print("Step 3: Creating portfolio service...")
    from .services.portfolio_service import PortfolioService
    portfolio_service = PortfolioService(zerodha_auth)
    initialization_status["service_created"] = True
    print("✅ Portfolio service created")
    
    print("Step 4: Creating investment service...")
    from .services.investment_service import InvestmentService
    investment_service = InvestmentService(zerodha_auth)
    initialization_status["investment_service_created"] = True
    print("✅ Investment service created")
    
    # Set up investment router dependency
    from .routers import investment
    investment.investment_service = investment_service
    
    print("⏸️ Authentication will be attempted on first API call")
    
except Exception as e:
    error_msg = f"Initialization error: {str(e)}\n{traceback.format_exc()}"
    print(f"❌ {error_msg}")
    initialization_status["error_message"] = error_msg

# Include investment router
try:
    from .routers.investment import router as investment_router
    app.include_router(investment_router)
    print("✅ Investment routes added")
except Exception as e:
    print(f"⚠️ Could not add investment routes: {e}")

@app.get("/")
async def root():
    return {"message": "Investment Rebalancing WebApp API", "status": initialization_status}

@app.get("/health")
async def health_check():
    """Comprehensive health check with honest status reporting"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "initialization": initialization_status.copy(),
        "zerodha_connection": {
            "available": False,
            "authenticated": False,
            "can_fetch_data": False,
            "error_message": None
        },
        "services": {
            "portfolio_service": bool(portfolio_service),
            "investment_service": bool(investment_service),
            "zerodha_auth": bool(zerodha_auth)
        }
    }
    
    # Test Zerodha connection if available
    if zerodha_auth:
        try:
            print("🔍 Testing Zerodha connection...")
            
            # Check if already authenticated
            if zerodha_auth.is_authenticated():
                health_status["zerodha_connection"]["available"] = True
                health_status["zerodha_connection"]["authenticated"] = True
                health_status["zerodha_connection"]["can_fetch_data"] = True
                initialization_status["zerodha_connection_status"] = "connected"
                print("✅ Zerodha already authenticated")
            else:
                # Try to authenticate
                print("🔄 Attempting Zerodha authentication...")
                try:
                    kite = zerodha_auth.authenticate()
                    if zerodha_auth.is_authenticated():
                        health_status["zerodha_connection"]["available"] = True
                        health_status["zerodha_connection"]["authenticated"] = True
                        health_status["zerodha_connection"]["can_fetch_data"] = True
                        initialization_status["zerodha_connection_status"] = "connected"
                        initialization_status["auth_successful"] = True
                        print("✅ Zerodha authentication successful")
                    else:
                        health_status["zerodha_connection"]["error_message"] = "Authentication failed - returned False"
                        initialization_status["zerodha_connection_status"] = "authentication_failed"
                        print("❌ Zerodha authentication failed")
                except Exception as auth_error:
                    health_status["zerodha_connection"]["error_message"] = str(auth_error)
                    initialization_status["zerodha_connection_status"] = f"error: {str(auth_error)}"
                    print(f"❌ Zerodha authentication error: {auth_error}")
        except Exception as e:
            health_status["zerodha_connection"]["error_message"] = str(e)
            initialization_status["zerodha_connection_status"] = f"error: {str(e)}"
            print(f"❌ Zerodha connection test error: {e}")
    else:
        health_status["zerodha_connection"]["error_message"] = "ZerodhaAuth service not initialized"
        initialization_status["zerodha_connection_status"] = "service_not_available"
    
    # Update initialization status
    initialization_status["auth_successful"] = health_status["zerodha_connection"]["authenticated"]
    
    return health_status

@app.get("/api/test-auth")
async def test_auth():
    """Test Zerodha authentication separately with detailed feedback"""
    if not zerodha_auth:
        return {
            "success": False,
            "error": "ZerodhaAuth service not initialized",
            "details": "The Zerodha authentication service could not be created. Check your configuration.",
            "initialization_status": initialization_status
        }
    
    try:
        print("🔄 Testing Zerodha authentication...")
        
        # Check current status
        if zerodha_auth.is_authenticated():
            return {
                "success": True,
                "message": "Already authenticated with Zerodha",
                "profile_name": getattr(zerodha_auth, 'profile_name', 'Unknown'),
                "status": "authenticated"
            }
        
        # Try to authenticate
        print("🔐 Attempting new authentication...")
        kite = zerodha_auth.authenticate()
        
        if zerodha_auth.is_authenticated():
            return {
                "success": True,
                "message": "Zerodha authentication successful!",
                "profile_name": getattr(zerodha_auth, 'profile_name', 'Unknown'),
                "status": "newly_authenticated"
            }
        else:
            return {
                "success": False,
                "message": "Zerodha authentication failed",
                "error": "Authentication method returned False",
                "details": "The authentication process completed but did not result in a valid session.",
                "status": "authentication_failed"
            }
    except Exception as e:
        error_msg = f"Auth test error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": "Authentication error occurred",
            "error": str(e),
            "details": "An exception occurred during the authentication process. Check your API credentials and network connection.",
            "traceback": traceback.format_exc() if app.debug else None,
            "status": "error"
        }

@app.get("/api/portfolio/summary/{user_id}")
async def get_portfolio_summary(user_id: int):
    """Get portfolio summary with strict no-fake-data policy"""
    
    print(f"🔍 PORTFOLIO SUMMARY CALLED for user {user_id}")
    
    # Check if services are available
    if not zerodha_auth:
        print("❌ ZerodhaAuth not available")
        return {
            "error": "Zerodha authentication service not available",
            "connected": False,
            "message": "Please check your Zerodha API configuration and restart the service",
            "data": None
        }
    
    if not portfolio_service:
        print("❌ Portfolio service not available")
        return {
            "error": "Portfolio service not available",
            "connected": False,
            "message": "Portfolio service could not be initialized",
            "data": None
        }
    
    try:
        # Check authentication status first
        if not zerodha_auth.is_authenticated():
            print("🔄 Attempting Zerodha authentication...")
            try:
                kite = zerodha_auth.authenticate()
                if not zerodha_auth.is_authenticated():
                    print("❌ Authentication failed")
                    return {
                        "error": "Zerodha authentication failed",
                        "connected": False,
                        "message": "Unable to authenticate with Zerodha. Please check your API credentials.",
                        "data": None
                    }
            except Exception as auth_error:
                print(f"❌ Authentication error: {auth_error}")
                return {
                    "error": f"Authentication error: {str(auth_error)}",
                    "connected": False,
                    "message": "Failed to connect to Zerodha. Please check your internet connection and API credentials.",
                    "data": None
                }
        
        print(f"✅ Authentication status: {zerodha_auth.is_authenticated()}")
        
        # Try to get real portfolio data
        print("📊 Fetching real portfolio data...")
        portfolio_data = portfolio_service.get_portfolio_data()
        
        if portfolio_data:
            print(f"📊 SUCCESS! Returning real portfolio data with {len(portfolio_data.get('holdings', []))} holdings")
            print(f"📊 Total value: ₹{portfolio_data.get('current_value', 0):,.2f}")
            return portfolio_data
        else:
            print("❌ Portfolio service returned None")
            return {
                "error": "No portfolio data available",
                "connected": True,
                "message": "Connected to Zerodha but no portfolio data found. This could mean:\n1. No holdings in your account\n2. Market is closed\n3. Data fetch failed",
                "data": None
            }
        
    except Exception as e:
        error_msg = f"Portfolio error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "error": str(e),
            "connected": False,
            "message": "An error occurred while fetching portfolio data",
            "data": None
        }

@app.get("/api/test-portfolio-direct")
async def test_portfolio_direct():
    """Test portfolio service by importing and calling it directly"""
    if not zerodha_auth:
        return {
            "error": "ZerodhaAuth not available",
            "details": "Authentication service not initialized"
        }
    
    try:
        # Import and create portfolio service fresh
        from .services.portfolio_service import PortfolioService
        
        # Ensure authentication
        if not zerodha_auth.is_authenticated():
            print("🔄 Authenticating...")
            zerodha_auth.authenticate()
        
        if not zerodha_auth.is_authenticated():
            return {
                "error": "Authentication failed",
                "details": "Could not authenticate with Zerodha"
            }
        
        # Create a fresh portfolio service instance
        fresh_portfolio_service = PortfolioService(zerodha_auth)
        
        print("🧪 Testing fresh portfolio service instance...")
        result = fresh_portfolio_service.get_portfolio_data()
        
        if result:
            return {
                "success": True,
                "message": "Fresh portfolio service works!",
                "holdings_count": len(result.get('holdings', [])),
                "current_value": result.get('current_value', 0),
                "zerodha_connected": result.get('zerodha_connected', False),
                "data_source": result.get('data_source', 'unknown')
            }
        else:
            return {
                "success": False,
                "message": "Fresh portfolio service returned None",
                "details": "Service is working but no data was returned"
            }
        
    except Exception as e:
        error_msg = f"Fresh portfolio test error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "error": str(e),
            "traceback": error_msg
        }

@app.get("/api/debug/holdings")
async def debug_holdings():
    """Debug endpoint to check raw holdings data"""
    if not zerodha_auth:
        return {"error": "ZerodhaAuth not available"}
    
    try:
        # Ensure authentication
        if not zerodha_auth.is_authenticated():
            print("🔄 Authenticating for debug...")
            kite = zerodha_auth.authenticate()
        
        if not zerodha_auth.is_authenticated():
            return {"error": "Authentication failed"}
        
        # Get raw holdings
        kite = zerodha_auth.get_kite_instance()
        if not kite:
            return {"error": "Kite instance not available"}
        
        print("🔍 Fetching raw holdings for debug...")
        holdings = kite.holdings()
        margins = kite.margins()
        
        return {
            "holdings_count": len(holdings) if holdings else 0,
            "raw_holdings": holdings[:3] if holdings else [],  # First 3 for testing
            "margins_available": bool(margins),
            "cash_available": margins['equity']['available']['cash'] if margins else 0,
            "authentication_working": True,
            "message": "Raw data fetch successful"
        }
        
    except Exception as e:
        error_msg = f"Debug error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "error": str(e),
            "traceback": error_msg,
            "authentication_working": False
        }

@app.get("/api/portfolio/performance/{user_id}")
async def get_portfolio_performance(user_id: int):
    """Get portfolio performance data - only if real data is available"""
    
    # Check if we have authenticated connection
    if not zerodha_auth or not zerodha_auth.is_authenticated():
        return {
            "error": "No authenticated Zerodha connection",
            "message": "Please ensure Zerodha is connected to view performance data",
            "performance_data": [],
            "period": "unavailable"
        }
    
    try:
        # In a real implementation, this would fetch historical data
        # For now, we'll return an error since we don't have historical data API
        return {
            "error": "Historical performance data not available",
            "message": "Historical performance tracking will be available once the system has been running and collecting data",
            "performance_data": [],
            "period": "not_implemented",
            "note": "Performance tracking requires historical data collection which is not yet implemented"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Error fetching performance data",
            "performance_data": [],
            "period": "error"
        }

@app.get("/api/connection-status")
async def get_connection_status():
    """Get comprehensive connection status"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {
            "zerodha_auth": {
                "available": bool(zerodha_auth),
                "authenticated": False,
                "profile_name": None,
                "error": None
            },
            "portfolio_service": {
                "available": bool(portfolio_service),
                "can_fetch_data": False
            },
            "investment_service": {
                "available": bool(investment_service)
            }
        },
        "overall_status": "disconnected"
    }
    
    # Test Zerodha connection
    if zerodha_auth:
        try:
            if zerodha_auth.is_authenticated():
                status["services"]["zerodha_auth"]["authenticated"] = True
                status["services"]["zerodha_auth"]["profile_name"] = getattr(zerodha_auth, 'profile_name', None)
                status["services"]["portfolio_service"]["can_fetch_data"] = True
                status["overall_status"] = "connected"
            else:
                status["services"]["zerodha_auth"]["error"] = "Not authenticated"
        except Exception as e:
            status["services"]["zerodha_auth"]["error"] = str(e)
    else:
        status["services"]["zerodha_auth"]["error"] = "Service not available"
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)