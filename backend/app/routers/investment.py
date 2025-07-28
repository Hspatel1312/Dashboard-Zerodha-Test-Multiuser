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
        print(f"❌ Investment requirements error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ Investment plan calculation error: {error_msg}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ Initial investment execution error: {error_msg}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ Rebalancing check error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ Portfolio status error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ CSV stocks error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
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
        print(f"❌ System orders error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system orders: {str(e)}"
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
            print(f"⚠️ Could not load CSV history: {history_error}")
        
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
        print(f"❌ CSV status error: {e}")
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
        
        print(f"🔄 Force refreshing CSV data (current hash: {old_hash})")
        
        # Force refresh CSV data
        new_data = csv_service.fetch_csv_data(force_refresh=True)
        new_hash = new_data['csv_hash']
        
        # Check if CSV changed
        csv_changed = old_hash != new_hash
        
        print(f"📊 CSV refresh complete:")
        print(f"   Old hash: {old_hash}")
        print(f"   New hash: {new_hash}")
        print(f"   Changed: {csv_changed}")
        
        # If CSV changed, check rebalancing automatically
        rebalancing_check = None
        portfolio_impact = None
        
        if csv_changed:
            print(f"🔄 CSV changed, checking rebalancing requirements...")
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
                print(f"⚠️ Could not get portfolio impact: {portfolio_error}")
                portfolio_impact = {"has_active_portfolio": False, "error": str(portfolio_error)}
        
        # Update CSV history
        try:
            investment_service._update_csv_history(new_data)
        except Exception as history_error:
            print(f"⚠️ Could not update CSV history: {history_error}")
        
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
                "next_steps": self._get_next_steps(csv_changed, rebalancing_check, portfolio_impact)
            }
        }
    except Exception as e:
        print(f"❌ Force CSV refresh error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh CSV: {str(e)}"
        )

def _get_next_steps(csv_changed: bool, rebalancing_check: dict, portfolio_impact: dict) -> list:
    """Generate next steps based on CSV refresh results"""
    steps = []
    
    if not csv_changed:
        steps.append("✅ No changes detected - portfolio remains aligned")
        return steps
    
    if not portfolio_impact or not portfolio_impact.get("has_active_portfolio"):
        steps.append("📋 CSV updated but no active portfolio found")
        steps.append("💰 Consider starting with Initial Investment")
        return steps
    
    if rebalancing_check and rebalancing_check.get("rebalancing_needed"):
        steps.append("⚖️ Rebalancing needed due to CSV changes")
        
        new_stocks = rebalancing_check.get("new_stocks", [])
        removed_stocks = rebalancing_check.get("removed_stocks", [])
        
        if new_stocks:
            steps.append(f"📈 New stocks to add: {', '.join(new_stocks[:3])}{'...' if len(new_stocks) > 3 else ''}")
        
        if removed_stocks:
            steps.append(f"📉 Stocks to remove: {', '.join(removed_stocks[:3])}{'...' if len(removed_stocks) > 3 else ''}")
        
        steps.append("🚀 Go to Rebalancing page to review and execute")
    else:
        steps.append("✅ CSV updated but no rebalancing needed")
        steps.append("📊 Portfolio remains well-aligned")
    
    return steps

@router.post("/execute-rebalancing")
async def execute_rebalancing(request: RebalancingRequest):
    """Execute rebalancing with optional additional investment"""
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        # First check if rebalancing is needed
        rebalancing_check = investment_service.check_rebalancing_needed()
        
        if not rebalancing_check.get("rebalancing_needed", False):
            return {
                "success": False,
                "message": "No rebalancing needed",
                "reason": rebalancing_check.get("reason", "Portfolio is aligned")
            }
        
        # This is a placeholder for actual rebalancing execution
        # In a real implementation, this would:
        # 1. Calculate new optimal allocation
        # 2. Generate buy/sell orders
        # 3. Execute orders through Zerodha API
        # 4. Update portfolio state
        
        return {
            "success": True,
            "message": "Rebalancing execution not yet implemented",
            "data": {
                "rebalancing_check": rebalancing_check,
                "additional_investment": request.additional_investment,
                "status": "PENDING_IMPLEMENTATION"
            }
        }
        
    except Exception as e:
        print(f"❌ Rebalancing execution error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute rebalancing: {str(e)}"
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
            "GET /requirements",
            "POST /calculate-plan", 
            "POST /execute-initial",
            "GET /rebalancing-check",
            "GET /portfolio-status",
            "GET /csv-stocks",
            "GET /system-orders",
            "GET /csv-status",
            "POST /force-csv-refresh",
            "POST /execute-rebalancing"
        ]
    }