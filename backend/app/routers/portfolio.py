# backend/app/routers/portfolio.py - Portfolio Management Routes

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, Dict, List
from jose import jwt, JWTError  # Use jose instead of jwt
from datetime import datetime
import traceback

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
security = HTTPBearer()

# Global portfolio service instance (will be set in main.py)
portfolio_service = None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        from ..config import settings
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except JWTError:  # Use JWTError instead of jwt.PyJWTError
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def get_portfolio_service():
    """Dependency to get portfolio service"""
    if not portfolio_service:
        raise HTTPException(status_code=500, detail="Portfolio service not initialized")
    return portfolio_service

@router.get("/summary")
async def get_portfolio_summary(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Get comprehensive portfolio summary
    
    Returns:
    {
        "success": true,
        "data": {
            "user_id": "AB1234",
            "current_value": 500000.0,
            "invested_value": 450000.0,
            "total_returns": 50000.0,
            "returns_percentage": 11.11,
            "available_cash": 25000.0,
            "day_change": 2500.0,
            "day_change_percent": 0.5,
            "holdings": [...],
            "allocation": [...],
            "zerodha_connected": true,
            "data_source": "Zerodha Live API",
            "last_updated": "2024-01-01T10:00:00"
        }
    }
    """
    try:
        print(f"📊 Getting portfolio summary for user: {current_user}")
        
        # Get portfolio data from Zerodha
        portfolio_data = service.get_portfolio_data()
        
        if not portfolio_data:
            return {
                "success": False,
                "error": "Unable to fetch portfolio data",
                "message": "Portfolio service returned no data"
            }
        
        # Check if there was an error in the portfolio data
        if "error" in portfolio_data:
            return {
                "success": False,
                "error": portfolio_data["error"],
                "message": portfolio_data.get("error_message", "Portfolio data fetch failed"),
                "data": {
                    "user_id": current_user,
                    "current_value": 0,
                    "invested_value": 0,
                    "total_returns": 0,
                    "returns_percentage": 0,
                    "available_cash": 0,
                    "day_change": 0,
                    "day_change_percent": 0,
                    "holdings": [],
                    "allocation": [],
                    "zerodha_connected": False,
                    "error_details": portfolio_data
                }
            }
        
        # Add user context and timestamp
        portfolio_data["user_id"] = current_user
        portfolio_data["last_updated"] = datetime.now().isoformat()
        
        print(f"✅ Portfolio summary retrieved successfully")
        print(f"   Current value: ₹{portfolio_data.get('current_value', 0):,.2f}")
        print(f"   Holdings: {len(portfolio_data.get('holdings', []))}")
        
        return {
            "success": True,
            "data": portfolio_data
        }
        
    except Exception as e:
        print(f"❌ Error getting portfolio summary: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio summary: {str(e)}"
        )

@router.get("/holdings")
async def get_holdings(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Get detailed holdings information
    
    Returns:
    {
        "success": true,
        "data": {
            "holdings": [
                {
                    "symbol": "RELIANCE",
                    "quantity": 100,
                    "avg_price": 2500.0,
                    "current_price": 2600.0,
                    "current_value": 260000.0,
                    "pnl": 10000.0,
                    "pnl_percent": 4.0,
                    "allocation_percent": 5.2
                }
            ],
            "total_value": 500000.0,
            "total_holdings": 20
        }
    }
    """
    try:
        print(f"📋 Getting holdings for user: {current_user}")
        
        # Get portfolio data
        portfolio_data = service.get_portfolio_data()
        
        if not portfolio_data or "error" in portfolio_data:
            return {
                "success": False,
                "error": "Unable to fetch holdings data",
                "data": {
                    "holdings": [],
                    "total_value": 0,
                    "total_holdings": 0
                }
            }
        
        holdings = portfolio_data.get("holdings", [])
        
        # Calculate additional metrics for each holding
        for holding in holdings:
            # Add P&L calculations
            current_value = holding.get("current_value", 0)
            quantity = holding.get("quantity", 0)
            current_price = holding.get("current_price", 0)
            avg_price = holding.get("avg_price", 0)
            
            if quantity > 0 and avg_price > 0:
                invested_value = quantity * avg_price
                pnl = current_value - invested_value
                pnl_percent = (pnl / invested_value) * 100 if invested_value > 0 else 0
                
                holding["invested_value"] = invested_value
                holding["pnl"] = pnl
                holding["pnl_percent"] = pnl_percent
        
        total_value = sum(h.get("current_value", 0) for h in holdings)
        
        return {
            "success": True,
            "data": {
                "holdings": holdings,
                "total_value": total_value,
                "total_holdings": len(holdings),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting holdings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get holdings: {str(e)}"
        )

@router.get("/positions")
async def get_positions(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Get current trading positions
    
    Returns:
    {
        "success": true,
        "data": {
            "day_positions": [...],
            "net_positions": [...]
        }
    }
    """
    try:
        print(f"📈 Getting positions for user: {current_user}")
        
        # This would get positions from Zerodha
        # For now, return empty positions
        return {
            "success": True,
            "data": {
                "day_positions": [],
                "net_positions": [],
                "message": "Positions tracking not yet implemented",
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get positions: {str(e)}"
        )

@router.get("/margins")
async def get_margins(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Get margin information
    
    Returns:
    {
        "success": true,
        "data": {
            "equity": {
                "available": {
                    "cash": 50000.0,
                    "collateral": 0.0
                },
                "utilised": {
                    "debits": 0.0,
                    "exposure": 0.0
                }
            }
        }
    }
    """
    try:
        print(f"💰 Getting margins for user: {current_user}")
        
        # Get connection status first
        connection_status = service.get_connection_status()
        
        if not connection_status.get("can_fetch_data", False):
            return {
                "success": False,
                "error": "Cannot fetch margin data - Zerodha not connected",
                "data": {
                    "equity": {
                        "available": {"cash": 0.0, "collateral": 0.0},
                        "utilised": {"debits": 0.0, "exposure": 0.0}
                    }
                }
            }
        
        # This would get actual margins from Zerodha
        # For now, return placeholder data
        return {
            "success": True,
            "data": {
                "equity": {
                    "available": {
                        "cash": 50000.0,
                        "collateral": 0.0,
                        "intraday_payin": 0.0
                    },
                    "utilised": {
                        "debits": 0.0,
                        "exposure": 0.0,
                        "holding_sales": 0.0
                    },
                    "net": 50000.0
                },
                "message": "Live margin data integration pending",
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting margins: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get margins: {str(e)}"
        )

@router.post("/reconcile")
async def reconcile_portfolio(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Reconcile portfolio with actual Zerodha holdings
    
    Returns:
    {
        "success": true,
        "data": {
            "reconciliation_status": "ALIGNED",
            "discrepancies": [],
            "total_impact": 0.0,
            "suggested_actions": []
        }
    }
    """
    try:
        print(f"🔍 Reconciling portfolio for user: {current_user}")
        
        # For now, return a placeholder reconciliation result
        return {
            "success": True,
            "data": {
                "reconciliation_status": "ALIGNED",
                "discrepancies": [],
                "total_impact": 0.0,
                "suggested_actions": [],
                "message": "Portfolio reconciliation not yet implemented",
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error reconciling portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reconcile portfolio: {str(e)}"
        )

@router.get("/performance")
async def get_portfolio_performance(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service),
    period: str = "1M"
):
    """
    Get portfolio performance metrics
    
    Parameters:
    - period: Performance period (1D, 1W, 1M, 3M, 6M, 1Y, ALL)
    
    Returns:
    {
        "success": true,
        "data": {
            "period": "1M",
            "returns": 8.5,
            "sharpe_ratio": 1.2,
            "volatility": 15.3,
            "max_drawdown": -5.2,
            "benchmark_comparison": {...}
        }
    }
    """
    try:
        print(f"📈 Getting performance metrics for user: {current_user}, period: {period}")
        
        # Validate period
        valid_periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        # For now, return placeholder performance data
        return {
            "success": True,
            "data": {
                "period": period,
                "returns": 8.5,
                "returns_annualized": 12.3,
                "sharpe_ratio": 1.2,
                "volatility": 15.3,
                "max_drawdown": -5.2,
                "win_rate": 65.0,
                "benchmark_comparison": {
                    "nifty_50_returns": 7.2,
                    "outperformance": 1.3
                },
                "message": "Performance calculation not yet implemented",
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance metrics: {str(e)}"
        )

@router.get("/analytics")
async def get_portfolio_analytics(
    current_user: str = Depends(get_current_user),
    service = Depends(get_portfolio_service)
):
    """
    Get advanced portfolio analytics
    
    Returns:
    {
        "success": true,
        "data": {
            "sector_allocation": {...},
            "risk_metrics": {...},
            "correlation_matrix": {...},
            "diversification_score": 85.0
        }
    }
    """
    try:
        print(f"📊 Getting analytics for user: {current_user}")
        
        # Get basic portfolio data
        portfolio_data = service.get_portfolio_data()
        
        if not portfolio_data or "error" in portfolio_data:
            return {
                "success": False,
                "error": "Unable to generate analytics - portfolio data unavailable",
                "data": {}
            }
        
        holdings = portfolio_data.get("holdings", [])
        
        # Generate basic analytics
        analytics_data = {
            "portfolio_composition": {
                "total_holdings": len(holdings),
                "largest_holding": max([h.get("allocation_percent", 0) for h in holdings]) if holdings else 0,
                "smallest_holding": min([h.get("allocation_percent", 0) for h in holdings]) if holdings else 0,
                "concentration_ratio": 0.0  # Top 5 holdings percentage
            },
            "sector_allocation": {
                "Technology": 25.0,
                "Finance": 20.0,
                "Healthcare": 15.0,
                "Energy": 20.0,
                "Consumer": 20.0
            },
            "risk_metrics": {
                "portfolio_beta": 0.95,
                "volatility": 15.3,
                "var_1_percent": -15000.0,
                "expected_shortfall": -18500.0
            },
            "diversification_score": 85.0,
            "allocation_deviation": 2.1,
            "rebalancing_score": "GOOD",
            "message": "Advanced analytics partially implemented",
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get portfolio analytics: {str(e)}"
        )

# Health check for portfolio router
@router.get("/health")
async def portfolio_router_health():
    """Health check for portfolio router"""
    return {
        "router": "portfolio",
        "status": "active",
        "service_available": bool(portfolio_service),
        "endpoints": [
            "GET /summary",
            "GET /holdings",
            "GET /positions", 
            "GET /margins",
            "POST /reconcile",
            "GET /performance",
            "GET /analytics"
        ]
    }