# backend/app/main.py
from fastapi import FastAPI
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
    "error_message": None
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
    
    print("⏸️ Authentication will be done on first API call")
    
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
    # Test Zerodha connection status
    zerodha_connected = False
    if zerodha_auth:
        try:
            # Try to authenticate if not already done
            if not zerodha_auth.is_authenticated():
                zerodha_auth.authenticate()
            zerodha_connected = zerodha_auth.is_authenticated()
        except Exception as e:
            print(f"Health check auth error: {e}")
            zerodha_connected = False
    
    # Update initialization status
    initialization_status["auth_successful"] = zerodha_connected
    
    return {
        "status": "healthy", 
        "zerodha_connected": zerodha_connected,
        "initialization": initialization_status,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/api/test-auth")
async def test_auth():
    """Test Zerodha authentication separately"""
    if not zerodha_auth:
        return {"error": "ZerodhaAuth not initialized", "status": initialization_status}
    
    try:
        print("🔄 Testing Zerodha authentication...")
        kite = zerodha_auth.authenticate()
        
        if zerodha_auth.is_authenticated():
            return {
                "success": True,
                "message": "Zerodha authentication successful!",
                "profile_name": zerodha_auth.profile_name
            }
        else:
            return {
                "success": False,
                "message": "Zerodha authentication failed",
                "error": "Authentication returned False"
            }
    except Exception as e:
        error_msg = f"Auth test error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "message": "Authentication error",
            "error": error_msg
        }

@app.get("/api/portfolio/summary/{user_id}")
async def get_portfolio_summary(user_id: int):
    """Get portfolio summary with authentication check"""
    
    print(f"🔍 PORTFOLIO SUMMARY CALLED for user {user_id}")
    
    # First check if we can authenticate
    if not zerodha_auth:
        print("❌ ZerodhaAuth not available")
        return get_sample_data()
    
    try:
        # Try authentication if not already done
        if not zerodha_auth.is_authenticated():
            print("🔄 Authenticating with Zerodha...")
            kite = zerodha_auth.authenticate()
            
            if not zerodha_auth.is_authenticated():
                print("❌ Authentication failed, using sample data")
                return get_sample_data()
        
        print(f"✅ Authentication status: {zerodha_auth.is_authenticated()}")
        
        # Import portfolio service fresh to avoid caching issues
        from .services.portfolio_service import PortfolioService
        fresh_portfolio_service = PortfolioService(zerodha_auth)
        
        print("📊 Using fresh portfolio service instance...")
        real_data = fresh_portfolio_service.get_portfolio_data()
        
        if real_data:
            print(f"📊 SUCCESS! Returning real portfolio data with {len(real_data.get('holdings', []))} holdings")
            print(f"📊 Total value: ₹{real_data.get('current_value', 0):,.2f}")
            return real_data
        else:
            print("❌ Portfolio service returned None, using sample data")
            return get_sample_data()
        
    except Exception as e:
        error_msg = f"Portfolio error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return get_sample_data()

@app.get("/api/test-portfolio-direct")
async def test_portfolio_direct():
    """Test portfolio service by importing and calling it directly"""
    try:
        # Import and create portfolio service fresh
        from .services.portfolio_service import PortfolioService
        
        # Ensure authentication
        if not zerodha_auth.is_authenticated():
            print("🔄 Authenticating...")
            zerodha_auth.authenticate()
        
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
                "first_holding": result.get('holdings', [{}])[0] if result.get('holdings') else None
            }
        else:
            return {
                "success": False,
                "message": "Fresh portfolio service returned None"
            }
        
    except Exception as e:
        error_msg = f"Fresh portfolio test error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

@app.get("/api/debug/holdings")
async def debug_holdings():
    """Debug endpoint to check raw holdings data"""
    if not zerodha_auth:
        return {"error": "ZerodhaAuth not available"}
    
    try:
        # Ensure authentication
        if not zerodha_auth.is_authenticated():
            kite = zerodha_auth.authenticate()
        
        if not zerodha_auth.is_authenticated():
            return {"error": "Authentication failed"}
        
        # Get raw holdings
        kite = zerodha_auth.get_kite_instance()
        if not kite:
            return {"error": "Kite instance not available"}
        
        holdings = kite.holdings()
        margins = kite.margins()
        
        return {
            "holdings_count": len(holdings),
            "holdings": holdings[:3] if holdings else [],  # First 3 for testing
            "margins": {
                "cash": margins['equity']['available']['cash'] if margins else 0
            },
            "authentication_working": True
        }
        
    except Exception as e:
        error_msg = f"Debug error: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

@app.get("/api/portfolio/performance/{user_id}")
async def get_portfolio_performance(user_id: int):
    """Get portfolio performance data"""
    base_date = datetime.now().date() - timedelta(days=30)
    performance_data = []
    
    base_value = 450000
    for i in range(31):
        date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        value = base_value + (i * 1000) + (i % 3 * 500)
        performance_data.append({
            "date": date_str,
            "value": value
        })
    
    return {
        "performance_data": performance_data,
        "period": "30_days"
    }

def get_sample_data():
    """Sample data for fallback"""
    return {
        "user_id": 1,
        "current_value": 485000,
        "invested_value": 450000,
        "total_invested": 450000,
        "total_returns": 35000,
        "returns_percentage": 7.78,
        "available_cash": 25000,
        "day_change": 5200,
        "day_change_percent": 1.08,
        "zerodha_connected": False,
        "holdings": [
            {
                "symbol": "SAMPLE",
                "quantity": 10,
                "avg_price": 100,
                "current_price": 110,
                "current_value": 1100,
                "allocation_percent": 5.0,
                "pnl": 100,
                "pnl_percent": 10.0
            }
        ],
        "allocation": [
            {
                "symbol": "SAMPLE",
                "quantity": 10,
                "avg_price": 100,
                "current_price": 110,
                "current_value": 1100,
                "allocation": 5.0
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)