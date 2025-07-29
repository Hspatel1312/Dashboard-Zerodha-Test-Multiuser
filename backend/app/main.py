# backend/app/main.py - FIXED VERSION with proper Zerodha initialization

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import traceback
import asyncio

app = FastAPI(title="Investment Rebalancing WebApp", version="2.0.0")

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
    "zerodha_connection_status": "not_checked",
    "csv_service_status": "not_initialized",
    "kite_instance_available": False
}

zerodha_auth = None
portfolio_service = None
investment_service = None

# Initialize step by step with error tracking
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
    
    print("Step 3: Testing Zerodha authentication...")
    try:
        # Try authentication during startup
        kite_instance = zerodha_auth.authenticate()
        if kite_instance and zerodha_auth.is_authenticated():
            initialization_status["auth_successful"] = True
            initialization_status["zerodha_connection_status"] = "connected"
            initialization_status["kite_instance_available"] = True
            print(f"✅ Zerodha authentication successful: {zerodha_auth.profile_name}")
        else:
            print("⚠️ Zerodha authentication failed during startup - will retry on demand")
            initialization_status["zerodha_connection_status"] = "authentication_failed"
    except Exception as auth_error:
        print(f"⚠️ Zerodha authentication error during startup: {auth_error}")
        initialization_status["zerodha_connection_status"] = f"startup_error: {str(auth_error)}"
    
    print("Step 4: Creating portfolio service...")
    from .services.portfolio_service import PortfolioService
    portfolio_service = PortfolioService(zerodha_auth)
    initialization_status["service_created"] = True
    print("✅ Portfolio service created")
    
    print("Step 5: Creating investment service...")
    from .services.investment_service import InvestmentService
    investment_service = InvestmentService(zerodha_auth)
    initialization_status["investment_service_created"] = True
    initialization_status["csv_service_status"] = "initialized"
    print("✅ Investment service created")
    
except Exception as e:
    error_msg = f"Initialization error: {str(e)}\n{traceback.format_exc()}"
    print(f"❌ {error_msg}")
    initialization_status["error_message"] = error_msg

# Include routers AFTER services are created
try:
    print("Step 6: Setting up routers...")
    
    # Import and setup investment router
    from .routers.investment import router as investment_router
    
    # Set the investment service dependency BEFORE including router
    from .routers import investment
    investment.investment_service = investment_service
    
    # Include the router with proper prefix
    app.include_router(investment_router, prefix="/api")
    print("✅ Investment router included at /api/investment/*")
    
except Exception as e:
    print(f"⚠️ Could not set up routers: {e}")
    print(f"   Traceback: {traceback.format_exc()}")

@app.get("/")
async def root():
    return {
        "message": "Investment Rebalancing WebApp API v2.0", 
        "status": initialization_status,
        "available_endpoints": [
            "/health - Health check with detailed Zerodha status",
            "/api/test-live-prices - Test live price fetching",
            "/api/test-auth - Test Zerodha authentication",
            "/api/test-nifty - Simple Nifty price test",
            "/api/investment/requirements - Get investment requirements",
            "/api/investment/calculate-plan - Calculate investment plan",
            "/api/investment/execute-initial - Execute initial investment",
            "/api/investment/rebalancing-check - Check rebalancing status",
            "/api/investment/portfolio-status - Get portfolio status",
            "/api/investment/csv-stocks - Get CSV stocks with prices",
            "/api/investment/system-orders - Get system orders history",
            "/api/investment/csv-status - Get CSV tracking status",
            "/api/investment/force-csv-refresh - Force refresh CSV data"
        ]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check with enhanced Zerodha connection testing"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "initialization": initialization_status.copy(),
        "zerodha_connection": {
            "available": False,
            "authenticated": False,
            "can_fetch_data": False,
            "kite_instance_valid": False,
            "profile_name": None,
            "error_message": None,
            "last_test_time": None
        },
        "csv_service": {
            "available": bool(investment_service and investment_service.csv_service),
            "last_fetch_time": None,
            "cache_status": "unknown",
            "csv_hash": None,
            "auto_tracking": True
        },
        "services": {
            "portfolio_service": bool(portfolio_service),
            "investment_service": bool(investment_service),
            "zerodha_auth": bool(zerodha_auth)
        }
    }
    
    # ENHANCED: Test Zerodha connection thoroughly
    if zerodha_auth:
        try:
            print("🔍 Testing Zerodha connection comprehensively...")
            
            # Check if already authenticated
            if zerodha_auth.is_authenticated():
                print("✅ Zerodha already authenticated")
                
                # Test if Kite instance is actually working
                kite = zerodha_auth.get_kite_instance()
                if kite:
                    try:
                        # Test with a simple API call
                        profile = kite.profile()
                        print(f"✅ Kite instance working - Profile: {profile.get('user_name', 'Unknown')}")
                        
                        health_status["zerodha_connection"]["available"] = True
                        health_status["zerodha_connection"]["authenticated"] = True
                        health_status["zerodha_connection"]["kite_instance_valid"] = True
                        health_status["zerodha_connection"]["can_fetch_data"] = True
                        health_status["zerodha_connection"]["profile_name"] = profile.get('user_name')
                        health_status["zerodha_connection"]["last_test_time"] = datetime.now().isoformat()
                        
                        initialization_status["zerodha_connection_status"] = "connected_and_verified"
                        initialization_status["auth_successful"] = True
                        initialization_status["kite_instance_available"] = True
                        
                    except Exception as kite_error:
                        print(f"❌ Kite instance test failed: {kite_error}")
                        health_status["zerodha_connection"]["authenticated"] = True
                        health_status["zerodha_connection"]["kite_instance_valid"] = False
                        health_status["zerodha_connection"]["error_message"] = f"Kite instance error: {str(kite_error)}"
                        initialization_status["zerodha_connection_status"] = "authenticated_but_kite_failed"
                        initialization_status["kite_instance_available"] = False
                else:
                    print("❌ No Kite instance available despite authentication")
                    health_status["zerodha_connection"]["authenticated"] = True
                    health_status["zerodha_connection"]["kite_instance_valid"] = False
                    health_status["zerodha_connection"]["error_message"] = "No Kite instance available"
                    initialization_status["zerodha_connection_status"] = "authenticated_but_no_kite"
                    initialization_status["kite_instance_available"] = False
            else:
                print("🔄 Not authenticated, attempting authentication...")
                try:
                    kite = zerodha_auth.authenticate()
                    if zerodha_auth.is_authenticated() and kite:
                        # Test the new connection
                        try:
                            profile = kite.profile()
                            print(f"✅ New authentication successful - Profile: {profile.get('user_name', 'Unknown')}")
                            
                            health_status["zerodha_connection"]["available"] = True
                            health_status["zerodha_connection"]["authenticated"] = True
                            health_status["zerodha_connection"]["kite_instance_valid"] = True
                            health_status["zerodha_connection"]["can_fetch_data"] = True
                            health_status["zerodha_connection"]["profile_name"] = profile.get('user_name')
                            health_status["zerodha_connection"]["last_test_time"] = datetime.now().isoformat()
                            
                            initialization_status["zerodha_connection_status"] = "newly_connected"
                            initialization_status["auth_successful"] = True
                            initialization_status["kite_instance_available"] = True
                            
                        except Exception as new_kite_error:
                            print(f"❌ New Kite instance test failed: {new_kite_error}")
                            health_status["zerodha_connection"]["error_message"] = f"New auth failed: {str(new_kite_error)}"
                            initialization_status["zerodha_connection_status"] = "auth_succeeded_but_kite_failed"
                    else:
                        print("❌ Authentication attempt failed")
                        health_status["zerodha_connection"]["error_message"] = "Authentication failed"
                        initialization_status["zerodha_connection_status"] = "authentication_failed"
                        
                except Exception as auth_error:
                    print(f"❌ Authentication error: {auth_error}")
                    health_status["zerodha_connection"]["error_message"] = str(auth_error)
                    initialization_status["zerodha_connection_status"] = f"auth_error: {str(auth_error)}"
                    
        except Exception as e:
            print(f"❌ Health check Zerodha test error: {e}")
            health_status["zerodha_connection"]["error_message"] = str(e)
            initialization_status["zerodha_connection_status"] = f"health_check_error: {str(e)}"
    
    # Check CSV service status
    if investment_service and investment_service.csv_service:
        try:
            csv_service = investment_service.csv_service
            connection_status = csv_service.get_connection_status()
            
            # Get cache info
            cached_data = csv_service._get_cached_csv()
            if cached_data:
                health_status["csv_service"]["last_fetch_time"] = cached_data['fetch_time']
                health_status["csv_service"]["csv_hash"] = cached_data['csv_hash']
                health_status["csv_service"]["cache_status"] = "fresh"
            else:
                health_status["csv_service"]["cache_status"] = "no_cache"
            
            health_status["csv_service"].update({
                "csv_accessible": connection_status.get('csv_accessible', False),
                "market_open": connection_status.get('market_open', False),
                "last_check": connection_status.get('last_check'),
                "kite_instance_available": connection_status.get('kite_instance', False)
            })
            
        except Exception as csv_error:
            health_status["csv_service"]["error_message"] = str(csv_error)
    
    return health_status

@app.get("/api/test-auth")
async def test_zerodha_auth():
    """Test Zerodha authentication specifically"""
    if not zerodha_auth:
        return {
            "success": False,
            "error": "ZerodhaAuth service not initialized"
        }
    
    try:
        print("🔐 Testing Zerodha authentication step by step...")
        
        # Get current auth status
        auth_status = zerodha_auth.get_auth_status()
        print(f"📋 Current auth status: {auth_status}")
        
        # Test authentication
        if not zerodha_auth.is_authenticated():
            print("🔄 Attempting authentication...")
            kite = zerodha_auth.authenticate()
            
            if not kite:
                return {
                    "success": False,
                    "error": "Authentication failed",
                    "auth_status": zerodha_auth.get_auth_status()
                }
        
        # Test Kite instance
        kite = zerodha_auth.get_kite_instance()
        if not kite:
            return {
                "success": False,
                "error": "No Kite instance available",
                "auth_status": zerodha_auth.get_auth_status()
            }
        
        # Test API call
        try:
            profile = kite.profile()
            margins = kite.margins()
            
            return {
                "success": True,
                "message": "Zerodha authentication working perfectly",
                "profile": {
                    "user_name": profile.get('user_name'),
                    "user_id": profile.get('user_id'),
                    "email": profile.get('email')
                },
                "margins": {
                    "equity_cash": margins.get('equity', {}).get('available', {}).get('cash', 0)
                },
                "auth_status": zerodha_auth.get_auth_status(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as api_error:
            return {
                "success": False,
                "error": f"API test failed: {str(api_error)}",
                "auth_status": zerodha_auth.get_auth_status(),
                "kite_available": bool(kite)
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Authentication test error: {str(e)}",
            "traceback": traceback.format_exc()
        }

@app.get("/api/test-live-prices")
async def test_live_prices():
    """Test live price fetching capability"""
    if not investment_service:
        return {
            "success": False,
            "error": "Investment service not available"
        }
    
    try:
        print("💰 Testing live price fetching...")
        
        # Test with a small set of symbols
        test_symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        
        csv_service = investment_service.csv_service
        kite = csv_service._get_valid_kite_instance()
        
        if not kite:
            return {
                "success": False,
                "error": "No valid Kite instance for price testing",
                "zerodha_status": zerodha_auth.get_auth_status() if zerodha_auth else "No auth service"
            }
        
        prices = csv_service.get_live_prices(test_symbols, kite)
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(prices)} live prices",
            "test_prices": prices,
            "success_rate": f"{len(prices)}/{len(test_symbols)} ({len(prices)/len(test_symbols)*100:.1f}%)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Live price test failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

# Existing endpoints remain the same...
@app.get("/api/test-nifty")
async def test_nifty_price():
    """Simple test to get Nifty 50 price to verify Zerodha connection"""
    if not zerodha_auth:
        return {
            "success": False,
            "error": "ZerodhaAuth service not initialized"
        }
    
    try:
        print("🧪 Testing Nifty 50 price fetch...")
        
        # Check authentication first
        if not zerodha_auth.is_authenticated():
            print("🔄 Not authenticated, attempting authentication...")
            try:
                zerodha_auth.authenticate()
                if not zerodha_auth.is_authenticated():
                    return {
                        "success": False,
                        "error": "Zerodha authentication failed",
                        "details": "Cannot test Nifty price without authentication"
                    }
            except Exception as auth_error:
                return {
                    "success": False,
                    "error": f"Authentication failed: {str(auth_error)}"
                }
        
        kite = zerodha_auth.get_kite_instance()
        if not kite:
            return {
                "success": False,
                "error": "No kite instance available"
            }
        
        # Test with Nifty 50 index
        try:
            print("🔍 Testing Nifty 50 quote...")
            nifty_quote = kite.quote(["NSE:NIFTY 50"])
            
            if "NSE:NIFTY 50" in nifty_quote:
                nifty_data = nifty_quote["NSE:NIFTY 50"]
                nifty_price = nifty_data.get('last_price', 0)
                
                return {
                    "success": True,
                    "message": "Nifty 50 price fetched successfully",
                    "nifty_price": nifty_price,
                    "nifty_data": {
                        "last_price": nifty_data.get('last_price'),
                        "change": nifty_data.get('net_change'),
                        "timestamp": nifty_data.get('timestamp'),
                        "ohlc": nifty_data.get('ohlc', {})
                    },
                    "profile_name": getattr(zerodha_auth, 'profile_name', 'Unknown'),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Nifty 50 data not found in response",
                    "response_keys": list(nifty_quote.keys())
                }
                
        except Exception as quote_error:
            # Try alternative symbols
            try:
                print("🔄 Trying alternative symbols...")
                alt_quotes = kite.quote(["NSE:RELIANCE", "NSE:TCS"])
                
                if alt_quotes:
                    sample_data = {}
                    for symbol, data in alt_quotes.items():
                        if isinstance(data, dict):
                            sample_data[symbol] = {
                                'last_price': data.get('last_price'),
                                'timestamp': data.get('timestamp')
                            }
                    
                    return {
                        "success": True,
                        "message": "Alternative stock prices fetched (Nifty failed)",
                        "alternative_data": sample_data,
                        "nifty_error": str(quote_error),
                        "profile_name": getattr(zerodha_auth, 'profile_name', 'Unknown'),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Both Nifty and alternative quotes failed: {str(quote_error)}"
                    }
            except Exception as alt_error:
                return {
                    "success": False,
                    "error": f"All quote requests failed. Nifty: {str(quote_error)}, Alt: {str(alt_error)}"
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Nifty price test error: {str(e)}",
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)