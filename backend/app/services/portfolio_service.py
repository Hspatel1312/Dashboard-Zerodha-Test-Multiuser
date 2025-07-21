# backend/app/services/portfolio_service.py
from ..auth import ZerodhaAuth

class PortfolioService:
    def __init__(self, zerodha_auth: ZerodhaAuth):
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance()
    
    def get_portfolio_data(self):
        """Get real portfolio data from Zerodha"""
        if not self.kite:
            print("❌ No Zerodha connection available")
            return None
        
        try:
            print("📊 Fetching live data from Zerodha...")
            
            # Get holdings and margins
            holdings = self.kite.holdings()
            margins = self.kite.margins()
            
            print(f"📈 Retrieved {len(holdings)} holdings from Zerodha")
            
            # Process holdings data (including collateral/pledged shares)
            portfolio_holdings = []
            total_investment = 0
            current_value = 0
            
            for holding in holdings:
                symbol = holding['tradingsymbol']
                
                # Handle ALL shares: regular + t1 + collateral (pledged)
                # Your shares are all in collateral_quantity (pledged)
                regular_qty = holding.get('quantity', 0)
                t1_qty = holding.get('t1_quantity', 0)  
                collateral_qty = holding.get('collateral_quantity', 0)
                total_quantity = regular_qty + t1_qty + collateral_qty
                
                print(f"Processing {symbol}: regular={regular_qty}, t1={t1_qty}, collateral={collateral_qty}, total={total_quantity}")
                
                # Include ALL holdings that have any shares (including pledged ones)
                if total_quantity > 0:
                    avg_price = holding['average_price']
                    current_price = holding['last_price']
                    holding_value = total_quantity * current_price
                    investment_value = total_quantity * avg_price
                    pnl = holding_value - investment_value
                    pnl_percent = (pnl / investment_value) * 100 if investment_value > 0 else 0
                    
                    portfolio_holdings.append({
                        "symbol": symbol,
                        "quantity": total_quantity,
                        "regular_quantity": regular_qty,
                        "t1_quantity": t1_qty,
                        "collateral_quantity": collateral_qty,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "current_value": holding_value,
                        "allocation_percent": 0,  # Will calculate later
                        "pnl": pnl,
                        "pnl_percent": pnl_percent,
                        "exchange": holding.get('exchange', 'NSE'),
                        "day_change": holding.get('day_change', 0),
                        "day_change_percentage": holding.get('day_change_percentage', 0),
                        "close_price": holding.get('close_price', current_price)
                    })
                    
                    total_investment += investment_value
                    current_value += holding_value
                    
                    print(f"✅ Added {symbol}: ₹{holding_value:,.2f} value, {pnl_percent:.2f}% P&L")
            
            print(f"📊 Total processed holdings: {len(portfolio_holdings)}")
            print(f"📊 Total current value: ₹{current_value:,.2f}")
            
            if len(portfolio_holdings) == 0:
                print("❌ No valid holdings found after processing")
                return None
            
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
            
            # Calculate day change for portfolio
            day_change = sum(
                holding.get('day_change', 0) * portfolio_holdings[i]['quantity']
                for i, holding in enumerate(holdings)
                if i < len(portfolio_holdings)
            )
            day_change_percent = (day_change / current_value) * 100 if current_value > 0 else 0
            
            print(f"✅ Portfolio processed successfully:")
            print(f"   📊 Holdings: {len(portfolio_holdings)}")
            print(f"   💰 Current Value: ₹{current_value:,.2f}")
            print(f"   📈 Total Returns: ₹{total_returns:,.2f} ({returns_percentage:.2f}%)")
            print(f"   💵 Available Cash: ₹{available_cash:,.2f}")
            
            return {
                "user_id": 1,
                "current_value": current_value,
                "invested_value": total_investment,
                "total_returns": total_returns,
                "returns_percentage": returns_percentage,
                "available_cash": available_cash,
                "holdings": portfolio_holdings,
                "allocation": portfolio_holdings,  # Add this for frontend compatibility
                "day_change": day_change,
                "day_change_percent": day_change_percent,
                "total_invested": total_investment,  # Add this for frontend compatibility
                "total_holdings": len(portfolio_holdings),
                "zerodha_connected": True
            }
            
        except Exception as e:
            print(f"❌ Error getting portfolio data: {e}")
            import traceback
            print(f"❌ Full error: {traceback.format_exc()}")
            return None
    
    def get_sample_data(self):
        """Fallback sample data"""
        print("📊 Using sample portfolio data")
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
            ],
            "total_holdings": 1
        }