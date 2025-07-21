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
async def get_investment_requirements(service = Depends(get_investment_service)):
    """
    Get investment requirements for initial setup
    Returns minimum investment amount and stock details
    """
    try:
        requirements = service.get_investment_requirements()
        return {
            "success": True,
            "data": requirements
        }
    except Exception as e:
        print(f"❌ Investment requirements error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get investment requirements: {str(e)}"
        )

@router.post("/calculate-plan")
async def calculate_investment_plan(
    request: InvestmentRequest, 
    service = Depends(get_investment_service)
):
    """
    Calculate initial investment plan for given amount
    """
    try:
        plan = service.calculate_initial_investment_plan(request.investment_amount)
        return {
            "success": True,
            "data": plan
        }
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Investment plan calculation error: {error_msg}")
        raise HTTPException(
            status_code=400 if "below minimum" in error_msg else 500,
            detail=error_msg
        )

@router.post("/execute-initial")
async def execute_initial_investment(
    request: InvestmentRequest,
    service = Depends(get_investment_service)
):
    """
    Execute initial investment (calculate plan and store orders)
    """
    try:
        # First calculate the plan
        plan = service.calculate_initial_investment_plan(request.investment_amount)
        
        # Then execute it
        result = service.execute_initial_investment(plan)
        
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
async def check_rebalancing_needed(service = Depends(get_investment_service)):
    """
    Check if rebalancing is needed based on CSV changes
    """
    try:
        result = service.check_rebalancing_needed()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        print(f"❌ Rebalancing check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check rebalancing: {str(e)}"
        )

@router.post("/calculate-rebalancing")
async def calculate_rebalancing_plan(
    request: RebalancingRequest,
    service = Depends(get_investment_service)
):
    """
    Calculate rebalancing plan with optional additional investment
    """
    try:
        plan = service.calculate_rebalancing_plan(request.additional_investment)
        return {
            "success": True,
            "data": plan
        }
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Rebalancing plan calculation error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@router.post("/execute-rebalancing")
async def execute_rebalancing(
    request: RebalancingRequest,
    service = Depends(get_investment_service)
):
    """
    Execute rebalancing plan
    """
    try:
        # First calculate the plan
        plan = service.calculate_rebalancing_plan(request.additional_investment)
        
        # Then execute it
        result = service.execute_rebalancing(plan)
        
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
async def get_portfolio_status(service = Depends(get_investment_service)):
    """
    Get current system portfolio status
    """
    try:
        status = service.get_system_portfolio_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        print(f"❌ Portfolio status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio status: {str(e)}"
        )

@router.get("/csv-stocks")
async def get_csv_stocks(service = Depends(get_investment_service)):
    """
    Get current stocks from CSV with live prices
    """
    try:
        stocks_data = service.csv_service.get_stocks_with_prices()
        return {
            "success": True,
            "data": stocks_data
        }
    except Exception as e:
        print(f"❌ CSV stocks error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CSV stocks: {str(e)}"
        )

@router.get("/system-orders")
async def get_system_orders(service = Depends(get_investment_service)):
    """
    Get all system orders history
    """
    try:
        orders = service._load_system_orders()
        return {
            "success": True,
            "data": {
                "orders": orders,
                "total_orders": len(orders)
            }
        }
    except Exception as e:
        print(f"❌ System orders error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system orders: {str(e)}"
        )