# backend/app/main.py - FIXED VERSION
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

# Initialize services with proper error handling
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
    
    print("🎉 All services initialized successfully")
    
except Exception as e:
    print(f"❌ Service initialization failed: {e}")
    print(f"❌ Traceback: {traceback.format_exc()}")

# Root endpoint
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
            "/health",
            "/api/investment/requirements",
            "/api/investment/portfolio-status", 
            "/api/investment/rebalancing-check",
            "/api/investment/csv-stocks",
            "/api/investment/system-orders",
            "/api/investment/csv-status",
            "/api/investment/calculate-plan",
            "/api/investment/execute-initial",
            "/api/investment/force-csv-refresh"
        ]
    }

@app.get("/health")
async def health():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "investment_service": investment_service is not None,
            "zerodha_auth": zerodha_auth is not None
        }
    }
    
    # Add service health details
    if investment_service:
        try:
            service_status = investment_service.get_service_status()
            health_status["service_details"] = service_status
        except Exception as e:
            health_status["service_error"] = str(e)
    
    return health_status

# Investment endpoints - DIRECT implementation with proper error handling
@app.get("/api/investment/requirements")
async def get_investment_requirements():
    """Get investment requirements with comprehensive error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        requirements = investment_service.get_investment_requirements()
        return {"success": True, "data": requirements}
    except Exception as e:
        print(f"❌ Requirements error: {e}")
        error_details = {
            "error_type": "REQUIREMENTS_ERROR",
            "error_message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        return {"success": False, "error": error_details}

@app.get("/api/investment/portfolio-status")
async def get_portfolio_status():
    """Get portfolio status with error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        status = investment_service.get_system_portfolio_status()
        return {"success": True, "data": status}
    except Exception as e:
        print(f"❌ Portfolio status error: {e}")
        return {
            "success": False, 
            "error": {
                "error_type": "PORTFOLIO_STATUS_ERROR",
                "error_message": str(e)
            }
        }

@app.get("/api/investment/rebalancing-check")
async def check_rebalancing():
    """Check rebalancing status with error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        result = investment_service.check_rebalancing_needed()
        return {"success": True, "data": result}
    except Exception as e:
        print(f"❌ Rebalancing check error: {e}")
        return {
            "success": False,
            "error": {
                "error_type": "REBALANCING_CHECK_ERROR", 
                "error_message": str(e)
            }
        }

@app.get("/api/investment/csv-stocks")
async def get_csv_stocks():
    """Get CSV stocks with comprehensive error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        stocks_data = investment_service.csv_service.get_stocks_with_prices()
        return {"success": True, "data": stocks_data}
    except Exception as e:
        print(f"❌ CSV stocks error: {e}")
        # Return structured error response
        return {
            "success": False,
            "error": {
                "error_type": "CSV_STOCKS_ERROR",
                "error_message": str(e)
            },
            "data": {
                "stocks": [],
                "total_stocks": 0,
                "error": "CSV_DATA_UNAVAILABLE",
                "price_data_status": {
                    "live_prices_used": False,
                    "market_data_source": "UNAVAILABLE"
                }
            }
        }

@app.get("/api/investment/system-orders")
async def get_system_orders():
    """Get system orders with error handling"""
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
        return {
            "success": False,
            "error": {
                "error_type": "SYSTEM_ORDERS_ERROR",
                "error_message": str(e)
            },
            "data": {
                "orders": [],
                "total_orders": 0
            }
        }

@app.get("/api/investment/csv-status")
async def get_csv_status():
    """Get CSV status with error handling"""
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
                    "fetch_time": cached_data.get('fetch_time') if cached_data else None,
                    "csv_hash": cached_data.get('csv_hash') if cached_data else None,
                    "total_symbols": len(cached_data.get('symbols', [])) if cached_data else 0,
                    "source_url": cached_data.get('source_url') if cached_data else None
                },
                "connection_status": connection_status
            }
        }
    except Exception as e:
        print(f"❌ CSV status error: {e}")
        return {
            "success": False,
            "error": {
                "error_type": "CSV_STATUS_ERROR",
                "error_message": str(e)
            },
            "data": {
                "current_csv": {
                    "available": False,
                    "total_symbols": 0
                },
                "connection_status": {"error": str(e)}
            }
        }

@app.post("/api/investment/calculate-plan")
async def calculate_plan(request: dict):
    """Calculate investment plan with error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        investment_amount = request.get("investment_amount", 0)
        if investment_amount <= 0:
            return {
                "success": False,
                "error": {
                    "error_type": "VALIDATION_ERROR",
                    "error_message": "Investment amount must be greater than 0"
                }
            }
        
        plan = investment_service.calculate_initial_investment_plan(investment_amount)
        return {"success": True, "data": plan}
    except Exception as e:
        print(f"❌ Calculate plan error: {e}")
        return {
            "success": False,
            "error": {
                "error_type": "PLAN_CALCULATION_ERROR",
                "error_message": str(e)
            }
        }

@app.post("/api/investment/execute-initial")
async def execute_initial(request: dict):
    """Execute initial investment with error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        investment_amount = request.get("investment_amount", 0)
        if investment_amount <= 0:
            return {
                "success": False,
                "error": {
                    "error_type": "VALIDATION_ERROR",
                    "error_message": "Investment amount must be greater than 0"
                }
            }
        
        # Calculate plan first
        plan = investment_service.calculate_initial_investment_plan(investment_amount)
        
        # Check if plan calculation failed
        if 'error' in plan:
            return {"success": False, "error": plan}
        
        # Execute plan
        result = investment_service.execute_initial_investment(plan)
        
        return {"success": True, "data": result}
    except Exception as e:
        print(f"❌ Execute initial error: {e}")
        return {
            "success": False,
            "error": {
                "error_type": "EXECUTION_ERROR", 
                "error_message": str(e)
            }
        }

@app.post("/api/investment/force-csv-refresh")
async def force_csv_refresh():
    """Force CSV refresh with error handling"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not available")
    
    try:
        csv_service = investment_service.csv_service
        
        # Get old data for comparison
        old_cached_data = csv_service._get_cached_csv()
        old_hash = old_cached_data.get('csv_hash') if old_cached_data else None
        
        # Refresh CSV data
        new_data = csv_service.fetch_csv_data(force_refresh=True)
        new_hash = new_data.get('csv_hash')
        
        csv_changed = old_hash != new_hash
        
        # Check rebalancing if changed
        rebalancing_check = None
        if csv_changed:
            try:
                rebalancing_check = investment_service.check_rebalancing_needed()
            except Exception as rebal_error:
                print(f"⚠️ Rebalancing check failed: {rebal_error}")
                rebalancing_check = {"error": str(rebal_error)}
        
        return {
            "success": True,
            "data": {
                "csv_refreshed": True,
                "csv_changed": csv_changed,
                "change_details": {
                    "old_hash": old_hash,
                    "new_hash": new_hash,
                    "old_symbols": len(old_cached_data.get('symbols', [])) if old_cached_data else 0,
                    "new_symbols": len(new_data.get('symbols', []))
                },
                "rebalancing_check": rebalancing_check
            }
        }
    except Exception as e:
        print(f"❌ Force refresh error: {e}")
        return {
            "success": False,
            "error": {
                "error_type": "CSV_REFRESH_ERROR",
                "error_message": str(e)
            }
        }

# Test endpoint for debugging
@app.get("/api/test/zerodha")
async def test_zerodha_connection():
    """Test Zerodha connection"""
    if not zerodha_auth:
        return {"connected": False, "error": "ZerodhaAuth not available"}
    
    try:
        status = zerodha_auth.get_auth_status()
        return {"connected": True, "status": status}
    except Exception as e:
        return {"connected": False, "error": str(e)}

# Debug endpoints
@app.get("/api/debug/services")
async def debug_services():
    """Debug service status"""
    debug_info = {
        "investment_service": {
            "available": investment_service is not None,
            "type": str(type(investment_service)) if investment_service else None
        },
        "zerodha_auth": {
            "available": zerodha_auth is not None,
            "type": str(type(zerodha_auth)) if zerodha_auth else None
        }
    }
    
    # Add detailed service info if available
    if investment_service:
        try:
            debug_info["investment_service"]["has_csv_service"] = hasattr(investment_service, 'csv_service')
            debug_info["investment_service"]["has_zerodha_auth"] = hasattr(investment_service, 'zerodha_auth')
        except Exception as e:
            debug_info["investment_service"]["error"] = str(e)
    
    if zerodha_auth:
        try:
            debug_info["zerodha_auth"]["authenticated"] = zerodha_auth.is_authenticated()
        except Exception as e:
            debug_info["zerodha_auth"]["error"] = str(e)
    
    return debug_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)