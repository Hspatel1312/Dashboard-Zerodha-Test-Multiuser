# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import traceback

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
    "csv_service_status": "not_initialized"
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
    
    print("Step 3: Creating portfolio service...")
    from .services.portfolio_service import PortfolioService
    portfolio_service = PortfolioService(zerodha_auth)
    initialization_status["service_created"] = True
    print("✅ Portfolio service created")
    
    print("Step 4: Creating investment service...")
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
    print("Step 5: Setting up routers...")
    
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
            "/health - Health check with CSV tracking status",
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
    """Comprehensive health check with CSV tracking status"""
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
    
    # Test Zerodha connection if available
    if zerodha_auth:
        try:
            print("🔍 Testing Zerodha connection...")
            
            if zerodha_auth.is_authenticated():
                health_status["zerodha_connection"]["available"] = True
                health_status["zerodha_connection"]["authenticated"] = True
                health_status["zerodha_connection"]["can_fetch_data"] = True
                initialization_status["zerodha_connection_status"] = "connected"
                print("✅ Zerodha already authenticated")
            else:
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
                        health_status["zerodha_connection"]["error_message"] = "Authentication failed"
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
                "last_check": connection_status.get('last_check')
            })
            
        except Exception as csv_error:
            health_status["csv_service"]["error_message"] = str(csv_error)
    
    # Update initialization status
    initialization_status["auth_successful"] = health_status["zerodha_connection"]["authenticated"]
    
    return health_status

# Add new endpoints for CSV management
@app.get("/api/csv-status")
async def get_csv_status():
    """Get detailed CSV tracking status"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        csv_service = investment_service.csv_service
        
        # Get connection status
        connection_status = csv_service.get_connection_status()
        
        # Get cached data info
        cached_data = csv_service._get_cached_csv()
        
        # Get CSV history
        csv_history = []
        try:
            with open(investment_service.csv_history_file, 'r') as f:
                import json
                csv_history = json.load(f)[-10:]  # Last 10 entries
        except:
            csv_history = []
        
        return {
            "success": True,
            "data": {
                "connection_status": connection_status,
                "cached_data_info": {
                    "available": bool(cached_data),
                    "fetch_time": cached_data['fetch_time'] if cached_data else None,
                    "csv_hash": cached_data['csv_hash'] if cached_data else None,
                    "total_symbols": len(cached_data['symbols']) if cached_data else 0
                },
                "csv_history": csv_history,
                "auto_refresh_enabled": True,
                "refresh_interval_minutes": 5
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CSV status: {str(e)}")

@app.post("/api/force-csv-refresh")
async def force_csv_refresh():
    """Force refresh CSV data and check for changes"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        csv_service = investment_service.csv_service
        
        # Force refresh CSV data
        old_cached_data = csv_service._get_cached_csv()
        old_hash = old_cached_data['csv_hash'] if old_cached_data else None
        
        # Fetch fresh data
        new_data = csv_service.fetch_csv_data(force_refresh=True)
        new_hash = new_data['csv_hash']
        
        # Check if CSV changed
        csv_changed = old_hash != new_hash
        
        # If CSV changed, check rebalancing
        rebalancing_check = None
        if csv_changed:
            print(f"🔄 CSV changed from {old_hash} to {new_hash}, checking rebalancing...")
            rebalancing_check = investment_service.check_rebalancing_needed()
        
        return {
            "success": True,
            "data": {
                "csv_refreshed": True,
                "csv_changed": csv_changed,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "fetch_time": new_data['fetch_time'],
                "total_symbols": len(new_data['symbols']),
                "rebalancing_check": rebalancing_check
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh CSV: {str(e)}")

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