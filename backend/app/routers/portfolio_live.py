# backend/app/routers/portfolio_live.py - Live Portfolio Endpoint
from fastapi import APIRouter, HTTPException
from typing import List
import traceback

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# This will be set in main.py
portfolio_service = None

def get_portfolio_service():
    """Dependency to get portfolio service"""
    if not portfolio_service:
        raise HTTPException(status_code=500, detail="Portfolio service not initialized")
    return portfolio_service

@router.get("/live")
async def get_live_portfolio():
    """Get live portfolio data directly from Zerodha"""
    try:
        if not portfolio_service:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")
        
        # Get live portfolio data
        portfolio_data = portfolio_service.get_portfolio_data()
        
        if not portfolio_data:
            return {
                "success": False,
                "error": "Unable to fetch live portfolio data",
                "data": {}
            }
        
        # Check if there's an error in the portfolio data
        if "error" in portfolio_data:
            return {
                "success": False,
                "error": portfolio_data.get("error_message", "Portfolio data unavailable"),
                "data": {}
            }
        
        return {
            "success": True,
            "data": portfolio_data
        }
        
    except Exception as e:
        print(f"❌ Live portfolio error: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get live portfolio: {str(e)}"
        )

@router.post("/live-prices")
async def get_live_prices(symbols: List[str]):
    """Get live prices for specific symbols"""
    try:
        if not portfolio_service:
            raise HTTPException(status_code=500, detail="Portfolio service not initialized")
        
        # This would use the Zerodha client to get live prices
        zerodha_client = portfolio_service.zerodha_auth
        
        if not zerodha_client or not zerodha_client.is_authenticated():
            return {
                "success": False,
                "error": "Zerodha not authenticated",
                "data": {}
            }
        
        kite = zerodha_client.get_kite_instance()
        if not kite:
            return {
                "success": False,
                "error": "Zerodha connection unavailable",
                "data": {}
            }
        
        # Format symbols for Zerodha API
        formatted_symbols = [f"NSE:{symbol}" for symbol in symbols]
        
        # Get quotes
        quotes = kite.quote(formatted_symbols)
        
        # Extract prices
        prices = {}
        for formatted_symbol, quote_data in quotes.items():
            original_symbol = formatted_symbol.replace("NSE:", "")
            prices[original_symbol] = {
                "ltp": quote_data.get("last_price", 0),
                "day_change": quote_data.get("net_change", 0),
                "day_change_percent": quote_data.get("net_change", 0) / quote_data.get("ohlc", {}).get("close", 1) * 100 if quote_data.get("ohlc", {}).get("close") else 0,
                "volume": quote_data.get("volume", 0),
                "ohlc": quote_data.get("ohlc", {})
            }
        
        return {
            "success": True,
            "data": {
                "prices": prices,
                "timestamp": traceback.format_exc(),
                "market_status": "open"  # You could add market status check here
            }
        }
        
    except Exception as e:
        print(f"❌ Live prices error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get live prices: {str(e)}"
        )