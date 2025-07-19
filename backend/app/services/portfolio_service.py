# backend/app/services/portfolio_service.py
from ..auth import ZerodhaAuth

class PortfolioService:
    def __init__(self, zerodha_auth: ZerodhaAuth):
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance()
    
    def get_portfolio_data(self):
        """Get real portfolio data from Zerodha"""
        if not self.kite:
            return None
        
        try:
            # Get holdings and margins
            holdings = self.kite.holdings()
            margins = self.kite.margins()
            
            # Process holdings data
            portfolio_holdings = []
            total_investment = 0
            current_value = 0
            
            for holding in holdings:
                symbol = holding['tradingsymbol']
                # Handle both regular and pledged shares
                quantity = (holding['quantity'] + 
                          holding['t1_quantity'] + 
                          holding.get('collateral_quantity', 0))
                
                if quantity > 0:
                    avg_price = holding['average_price']
                    current_price = holding['last_price']
                    holding_value = quantity * current_price
                    investment_value = quantity * avg_price
                    pnl = holding_value - investment_value
                    pnl_percent = (pnl / investment_value) * 100 if investment_value > 0 else 0
                    
                    portfolio_holdings.append({
                        "symbol": symbol,
                        "quantity": quantity,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "current_value": holding_value,
                        "allocation_percent": 0,  # Will calculate later
                        "pnl": pnl,
                        "pnl_percent": pnl_percent
                    })
                    
                    total_investment += investment_value
                    current_value += holding_value
            
            # Calculate allocation percentages
            for holding in portfolio_holdings:
                holding["allocation_percent"] = (
                    (holding["current_value"] / current_value) * 100 
                    if current_value > 0 else 0
                )
            
            # Calculate overall metrics
            total_returns = current_value - total_investment
            returns_percentage = (
                (total_returns / total_investment) * 100 
                if total_investment > 0 else 0
            )
            
            # Get available cash
            available_cash = margins['equity']['available']['cash']
            
            return {
                "user_id": 1,
                "current_value": current_value,
                "invested_value": total_investment,
                "total_returns": total_returns,
                "returns_percentage": returns_percentage,
                "available_cash": available_cash,
                "holdings": portfolio_holdings,
                "day_change": 0,
                "day_change_percent": 0
            }
            
        except Exception as e:
            print(f"Error getting portfolio data: {e}")
            return None
    
    def get_sample_data(self):
        """Fallback sample data"""
        return {
            "user_id": 1,
            "current_value": 485000,
            "invested_value": 450000,
            "total_returns": 35000,
            "returns_percentage": 7.78,
            "day_change": 5200,
            "day_change_percent": 1.08,
            "holdings": [
                {
                    "symbol": "RELIANCE",
                    "quantity": 20,
                    "avg_price": 2400,
                    "current_price": 2520,
                    "current_value": 50400,
                    "allocation_percent": 10.39,
                    "pnl": 2400,
                    "pnl_percent": 5.0
                },
                {
                    "symbol": "TCS",
                    "quantity": 15,
                    "current_price": 3480,
                    "avg_price": 3400,
                    "current_value": 52200,
                    "allocation_percent": 10.76,
                    "pnl": 1200,
                    "pnl_percent": 2.35
                }
            ]
        }