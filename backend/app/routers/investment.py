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
    """
    Get investment requirements for initial setup
    Returns minimum investment amount and stock details
    """
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
    """
    Calculate initial investment plan for given amount
    """
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
    """
    Execute initial investment (calculate plan and store orders)
    """
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
    """
    Check if rebalancing is needed based on CSV changes
    """
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

@router.post("/calculate-rebalancing")
async def calculate_rebalancing_plan(request: RebalancingRequest):
    """
    Calculate rebalancing plan with optional additional investment
    """
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        plan = investment_service.calculate_rebalancing_plan(request.additional_investment)
        return {
            "success": True,
            "data": plan
        }
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Rebalancing plan calculation error: {error_msg}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/execute-rebalancing")
async def execute_rebalancing(request: RebalancingRequest):
    """
    Execute rebalancing plan
    """
    try:
        if not investment_service:
            raise HTTPException(status_code=500, detail="Investment service not initialized")
        
        # First calculate the plan
        plan = investment_service.calculate_rebalancing_plan(request.additional_investment)
        
        # Then execute it
        result = investment_service.execute_rebalancing(plan)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Rebalancing execution error: {error_msg}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.get("/portfolio-status")
async def get_portfolio_status():
    """
    Get current system portfolio status (built from order history)
    """
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
    """
    Get current stocks from CSV with live prices
    """
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
    """
    Get all system orders history
    """
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
            "POST /calculate-rebalancing",
            "POST /execute-rebalancing",
            "GET /portfolio-status",
            "GET /csv-stocks",
            "GET /system-orders"
        ]
    }