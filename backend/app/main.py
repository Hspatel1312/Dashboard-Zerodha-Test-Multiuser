# backend/app/main.py - SIMPLIFIED VERSION
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import traceback

app = FastAPI(title="Investment Rebalancing WebApp", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
zerodha_auth = None
investment_service = None

# Initialize services
try:
    print("🚀 Initializing services...")
    
    from .config import settings
    print("✅ Config loaded")
    
    from .auth import ZerodhaAuth
    zerodha_auth = ZerodhaAuth()
    print("✅ ZerodhaAuth created")
    
    from .services.investment_service import InvestmentService
    investment_service = InvestmentService(zerodha_auth)
    print("✅ InvestmentService created")
    
except Exception as e:
    print(f"❌ Service initialization failed: {e}")
    print(f"❌ Traceback: {traceback.format_exc()}")

# ============= DIRECT API ENDPOINTS =============

@app.get("/")
async def root():
    return {
        "message": "Investment Rebalancing WebApp API v2.0",
        "status": "running",
        "services": {
            "investment_service": investment_service is not None,
            "zerodha_auth": zerodha_auth is not None
        },
        "endpoints": [
            "/api/investment/requirements",
            "/api/investment/portfolio-status", 
            "/api/investment/rebalancing-check",
            "/api/investment/csv-stocks",
            "/api/investment/system-orders",
            "/api/investment/csv-status"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "investment_service": investment_service is not None,
            "zerodha_auth": zerodha_auth is not None
        }
    }

# Investment endpoints - DIRECT implementation
@app.get("/api/investment/requirements")
async def get_investment_requirements():
    """Get investment requirements"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        requirements = investment_service.get_investment_requirements()
        return {"success": True, "data": requirements}
    except Exception as e:
        print(f"❌ Requirements error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investment/portfolio-status")
async def get_portfolio_status():
    """Get portfolio status"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        status = investment_service.get_system_portfolio_status()
        return {"success": True, "data": status}
    except Exception as e:
        print(f"❌ Portfolio status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investment/rebalancing-check")
async def check_rebalancing():
    """Check rebalancing status"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        result = investment_service.check_rebalancing_needed()
        return {"success": True, "data": result}
    except Exception as e:
        print(f"❌ Rebalancing check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investment/csv-stocks")
async def get_csv_stocks():
    """Get CSV stocks with prices"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        stocks_data = investment_service.csv_service.get_stocks_with_prices()
        return {"success": True, "data": stocks_data}
    except Exception as e:
        print(f"❌ CSV stocks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investment/system-orders")
async def get_system_orders():
    """Get system orders"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        orders = investment_service._load_system_orders()
        return {
            "success": True, 
            "data": {
                "orders": orders,
                "total_orders": len(orders)
            }
        }
    except Exception as e:
        print(f"❌ System orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/investment/csv-status")
async def get_csv_status():
    """Get CSV status"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        csv_service = investment_service.csv_service
        cached_data = csv_service._get_cached_csv()
        connection_status = csv_service.get_connection_status()
        
        return {
            "success": True,
            "data": {
                "current_csv": {
                    "available": bool(cached_data),
                    "fetch_time": cached_data['fetch_time'] if cached_data else None,
                    "csv_hash": cached_data['csv_hash'] if cached_data else None,
                    "total_symbols": len(cached_data['symbols']) if cached_data else 0,
                    "source_url": cached_data.get('source_url') if cached_data else None
                },
                "connection_status": connection_status
            }
        }
    except Exception as e:
        print(f"❌ CSV status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investment/calculate-plan")
async def calculate_plan(request: dict):
    """Calculate investment plan"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        investment_amount = request.get("investment_amount", 0)
        plan = investment_service.calculate_initial_investment_plan(investment_amount)
        return {"success": True, "data": plan}
    except Exception as e:
        print(f"❌ Calculate plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investment/execute-initial")
async def execute_initial(request: dict):
    """Execute initial investment"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        investment_amount = request.get("investment_amount", 0)
        
        # Calculate plan first
        plan = investment_service.calculate_initial_investment_plan(investment_amount)
        
        # Execute plan
        result = investment_service.execute_initial_investment(plan)
        
        return {"success": True, "data": result}
    except Exception as e:
        print(f"❌ Execute initial error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/investment/force-csv-refresh")
async def force_csv_refresh():
    """Force CSV refresh"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        csv_service = investment_service.csv_service
        
        # Get old data
        old_cached_data = csv_service._get_cached_csv()
        old_hash = old_cached_data['csv_hash'] if old_cached_data else None
        
        # Refresh
        new_data = csv_service.fetch_csv_data(force_refresh=True)
        new_hash = new_data['csv_hash']
        
        csv_changed = old_hash != new_hash
        
        # Check rebalancing if changed
        rebalancing_check = None
        if csv_changed:
            rebalancing_check = investment_service.check_rebalancing_needed()
        
        return {
            "success": True,
            "data": {
                "csv_refreshed": True,
                "csv_changed": csv_changed,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "rebalancing_check": rebalancing_check
            }
        }
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Debug endpoints
@app.get("/api/debug/services")
async def debug_services():
    """Debug service status"""
    return {
        "investment_service": {
            "available": investment_service is not None,
            "type": str(type(investment_service)) if investment_service else None,
            "has_csv_service": bool(investment_service and hasattr(investment_service, 'csv_service')),
            "has_zerodha_auth": bool(investment_service and hasattr(investment_service, 'zerodha_auth'))
        },
        "zerodha_auth": {
            "available": zerodha_auth is not None,
            "type": str(type(zerodha_auth)) if zerodha_auth else None,
            "authenticated": zerodha_auth.is_authenticated() if zerodha_auth else False
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)