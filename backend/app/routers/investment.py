# backend/app/routers/investment.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import traceback

router = APIRouter(prefix="/investment", tags=["investment"])

# Global investment service instance (will be set in main.py)
investment_service = None

def get_investment_service():
    """Dependency to get investment service"""
    if not investment_service:
        raise HTTPException(status_code=500, detail="Investment service not initialized")
    return investment_service

class InvestmentRequest(BaseModel):
    investment_amount: float

class RebalancingRequest(BaseModel):
    additional_investment: float = 0.0

@router.get("/status")
async def get_investment_status():
    """Get current investment status - determines if first investment or rebalancing needed"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        status = investment_service.get_investment_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        print(f"[ERROR] Investment status error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get investment status: {str(e)}"
        )

@router.get("/requirements")
async def get_investment_requirements():
    """Get investment requirements for initial setup"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        requirements = investment_service.get_investment_requirements()
        return {
            "success": True,
            "data": requirements
        }
    except Exception as e:
        print(f"[ERROR] Investment requirements error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get investment requirements: {str(e)}"
        )

@router.post("/calculate-plan")
async def calculate_investment_plan(request: InvestmentRequest):
    """Calculate initial investment plan for given amount"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        plan = investment_service.calculate_initial_investment_plan(request.investment_amount)
        return {
            "success": True,
            "data": plan
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Investment plan calculation error: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400 if "below minimum" in error_msg else 500,
            detail=error_msg
        )

@router.post("/execute-initial")
async def execute_initial_investment(request: InvestmentRequest):
    """Execute initial investment (calculate plan and store orders)"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        # First calculate the plan
        plan = investment_service.calculate_initial_investment_plan(request.investment_amount)
        
        # Then execute it
        result = investment_service.execute_initial_investment(plan)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Initial investment execution error: {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400 if "below minimum" in error_msg else 500,
            detail=error_msg
        )

@router.get("/rebalancing-check")
async def check_rebalancing_needed():
    """Check if rebalancing is needed based on CSV changes"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        result = investment_service.check_rebalancing_needed()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        print(f"[ERROR] Rebalancing check error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check rebalancing: {str(e)}"
        )

@router.get("/portfolio-status")
async def get_portfolio_status():
    """Get current system portfolio status (built from order history)"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        status = investment_service.get_system_portfolio_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        print(f"[ERROR] Portfolio status error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio status: {str(e)}"
        )

@router.get("/csv-stocks")
async def get_csv_stocks():
    """Get current stocks from CSV with live prices"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        stocks_data = investment_service.csv_service.get_stocks_with_prices()
        return {
            "success": True,
            "data": stocks_data
        }
    except Exception as e:
        print(f"[ERROR] CSV stocks error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CSV stocks: {str(e)}"
        )

@router.get("/system-orders")
async def get_system_orders():
    """Get all system orders history"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        orders = investment_service._load_system_orders()
        return {
            "success": True,
            "data": {
                "orders": orders,
                "total_orders": len(orders)
            }
        }
    except Exception as e:
        print(f"[ERROR] System orders error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system orders: {str(e)}"
        )

@router.post("/reset-orders")
async def reset_system_orders():
    """Reset all system orders (for testing purposes)"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        # Clear orders file
        import os
        orders_file = "system_orders.json"
        if os.path.exists(orders_file):
            with open(orders_file, 'w') as f:
                import json
                json.dump([], f)
        
        print("[INFO] System orders have been reset")
        
        return {
            "success": True,
            "message": "All system orders have been reset",
            "orders_count": 0
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to reset system orders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset system orders: {str(e)}"
        )

@router.get("/csv-status")
async def get_csv_tracking_status():
    """Get CSV tracking and change detection status"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        csv_service = investment_service.csv_service
        
        # Get current cached data
        cached_data = csv_service._get_cached_csv()
        
        # Get CSV history from investment service
        csv_history = []
        try:
            import json
            import os
            if os.path.exists(investment_service.csv_history_file):
                with open(investment_service.csv_history_file, 'r') as f:
                    csv_history = json.load(f)[-5:]  # Last 5 entries
        except Exception as history_error:
            print(f"[WARNING] Could not load CSV history: {history_error}")
        
        # Get connection status
        connection_status = csv_service.get_connection_status()
        
        # Check if rebalancing is needed
        rebalancing_status = investment_service.check_rebalancing_needed()
        
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
                "csv_history": csv_history,
                "connection_status": connection_status,
                "rebalancing_status": rebalancing_status,
                "auto_tracking": True,
                "last_check": connection_status.get('last_check')
            }
        }
    except Exception as e:
        print(f"[ERROR] CSV status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CSV status: {str(e)}"
        )

@router.post("/force-csv-refresh")
async def force_csv_refresh():
    """Force refresh CSV data and check for changes"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        csv_service = investment_service.csv_service
        
        # Get old data for comparison
        old_cached_data = csv_service._get_cached_csv()
        old_hash = old_cached_data['csv_hash'] if old_cached_data else None
        
        print(f"[INFO] Force refreshing CSV data (current hash: {old_hash})")
        
        # Force refresh CSV data
        new_data = csv_service.fetch_csv_data(force_refresh=True)
        new_hash = new_data['csv_hash']
        
        # Check if CSV changed
        csv_changed = old_hash != new_hash
        
        print(f"[INFO] CSV refresh complete:")
        print(f"   Old hash: {old_hash}")
        print(f"   New hash: {new_hash}")
        print(f"   Changed: {csv_changed}")
        
        # If CSV changed, check rebalancing automatically
        rebalancing_check = None
        portfolio_impact = None
        
        if csv_changed:
            print(f"[INFO] CSV changed, checking rebalancing requirements...")
            rebalancing_check = investment_service.check_rebalancing_needed()
            
            # Get portfolio status to show impact
            try:
                portfolio_status = investment_service.get_system_portfolio_status()
                if portfolio_status['status'] == 'active':
                    portfolio_impact = {
                        "has_active_portfolio": True,
                        "current_stocks": len(portfolio_status['holdings']),
                        "current_value": portfolio_status['portfolio_summary']['current_value']
                    }
                else:
                    portfolio_impact = {"has_active_portfolio": False}
            except Exception as portfolio_error:
                print(f"[WARNING] Could not get portfolio impact: {portfolio_error}")
                portfolio_impact = {"has_active_portfolio": False, "error": str(portfolio_error)}
        
        # Update CSV history
        try:
            investment_service._update_csv_history(new_data)
        except Exception as history_error:
            print(f"[WARNING] Could not update CSV history: {history_error}")
        
        return {
            "success": True,
            "data": {
                "csv_refreshed": True,
                "csv_changed": csv_changed,
                "change_details": {
                    "old_hash": old_hash,
                    "new_hash": new_hash,
                    "old_symbols": len(old_cached_data['symbols']) if old_cached_data else 0,
                    "new_symbols": len(new_data['symbols'])
                },
                "fetch_info": {
                    "fetch_time": new_data['fetch_time'],
                    "source_url": new_data.get('source_url'),
                    "total_symbols": len(new_data['symbols'])
                },
                "rebalancing_check": rebalancing_check,
                "portfolio_impact": portfolio_impact,
                "next_steps": get_next_steps(csv_changed, rebalancing_check, portfolio_impact)
            }
        }
    except Exception as e:
        print(f"[ERROR] Force CSV refresh error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh CSV: {str(e)}"
        )

def get_next_steps(csv_changed: bool, rebalancing_check: dict, portfolio_impact: dict) -> list:
    """Generate next steps based on CSV refresh results - FIXED: Added proper function definition"""
    steps = []
    
    if not csv_changed:
        steps.append("[SUCCESS] No changes detected - portfolio remains aligned")
        return steps
    
    if not portfolio_impact or not portfolio_impact.get("has_active_portfolio"):
        steps.append("[INFO] CSV updated but no active portfolio found")
        steps.append("[INFO] Consider starting with Initial Investment")
        return steps
    
    if rebalancing_check and rebalancing_check.get("rebalancing_needed"):
        steps.append("[INFO] Rebalancing needed due to CSV changes")
        
        new_stocks = rebalancing_check.get("new_stocks", [])
        removed_stocks = rebalancing_check.get("removed_stocks", [])
        
        if new_stocks:
            steps.append(f"[SUCCESS] New stocks to add: {', '.join(new_stocks[:3])}{'...' if len(new_stocks) > 3 else ''}")
        
        if removed_stocks:
            steps.append(f"[WARNING] Stocks to remove: {', '.join(removed_stocks[:3])}{'...' if len(removed_stocks) > 3 else ''}")
        
        steps.append("[INFO] Go to Rebalancing page to review and execute")
    else:
        steps.append("[SUCCESS] CSV updated but no rebalancing needed")
        steps.append("[INFO] Portfolio remains well-aligned")
    
    return steps

@router.post("/calculate-rebalancing")
async def calculate_rebalancing(request: RebalancingRequest):
    """Calculate rebalancing plan with optional additional investment"""
    try:
        print(f"[DEBUG] Received rebalancing request: {request}")
        print(f"[DEBUG] Additional investment: {request.additional_investment}")
        
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        rebalancing_plan = investment_service.calculate_rebalancing_plan(
            additional_investment=request.additional_investment
        )
        return {
            "success": True,
            "data": rebalancing_plan
        }
    except Exception as e:
        print(f"[ERROR] Rebalancing calculation error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate rebalancing: {str(e)}"
        )

@router.post("/execute-rebalancing")
async def execute_rebalancing(request: RebalancingRequest):
    """Execute rebalancing with optional additional investment"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        result = investment_service.execute_rebalancing(
            additional_investment=request.additional_investment
        )
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"[ERROR] Rebalancing execution error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute rebalancing: {str(e)}"
        )

@router.get("/portfolio-comparison")
async def get_portfolio_comparison():
    """Compare dashboard portfolio with live Zerodha portfolio"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        comparison_result = investment_service.portfolio_comparison.compare_portfolios()
        return {
            "success": True,
            "data": comparison_result
        }
    except Exception as e:
        print(f"[ERROR] Portfolio comparison error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare portfolios: {str(e)}"
        )

@router.get("/rebalancing-portfolio-value")
async def get_rebalancing_portfolio_value():
    """Get portfolio value to use for rebalancing (considering Zerodha vs dashboard differences)"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        value_info = investment_service.portfolio_comparison.get_rebalancing_portfolio_value()
        return {
            "success": True,
            "data": value_info
        }
    except Exception as e:
        print(f"[ERROR] Rebalancing portfolio value error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get rebalancing portfolio value: {str(e)}"
        )

@router.get("/zerodha-portfolio")
async def get_zerodha_portfolio():
    """Get live Zerodha portfolio data"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        zerodha_data = investment_service.portfolio_service.get_portfolio_data()
        return {
            "success": True,
            "data": zerodha_data
        }
    except Exception as e:
        print(f"[ERROR] Zerodha portfolio error: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Zerodha portfolio: {str(e)}"
        )

# Health check for this router
@router.get("/health")
async def investment_router_health():
    """Health check for investment router"""
    return {
        "router": "investment",
        "status": "active",
        "service_available": bool(investment_service),
        "endpoints": [
            "GET /status",
            "GET /requirements",
            "POST /calculate-plan", 
            "POST /execute-initial",
            "POST /calculate-rebalancing (with additional_investment)",
            "POST /execute-rebalancing (with additional_investment)",
            "GET /portfolio-status",
            "GET /portfolio-comparison",
            "GET /rebalancing-portfolio-value",
            "GET /zerodha-portfolio",
            "GET /system-orders"
        ]
    }