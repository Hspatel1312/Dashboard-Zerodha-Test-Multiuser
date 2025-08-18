# backend/app/services/portfolio_service.py - IMPROVED VERSION

class PortfolioService:
    def __init__(self, zerodha_auth):
        self.zerodha_auth = zerodha_auth
        self.kite = zerodha_auth.get_kite_instance() if zerodha_auth else None
    
    def get_portfolio_data(self):
        """Get portfolio data from Zerodha - Using the working method from your notebook"""
        if not self.zerodha_auth:
            print("[ERROR] No Zerodha authentication service available")
            return None
        
        if not self.zerodha_auth.is_authenticated():
            print("[ERROR] Zerodha not authenticated, attempting authentication...")
            try:
                result = self.zerodha_auth.authenticate()
                if not result:
                    print("[ERROR] Authentication failed")
                    return None
                self.kite = self.zerodha_auth.get_kite_instance()
            except Exception as e:
                print(f"[ERROR] Authentication error: {e}")
                return None
        
        if not self.kite:
            print("[ERROR] No Zerodha connection available")
            return None
        
        try:
            print("[INFO] Fetching live portfolio data from Zerodha...")
            
            # Get holdings and margins - EXACTLY like your notebook
            holdings = self.kite.holdings()
            positions_data = self.kite.positions()
            margins = self.kite.margins()
            
            if not holdings:
                print("[WARNING] No holdings found in Zerodha account")
                return {
                    "user_id": 1,
                    "current_value": 0,
                    "invested_value": 0,
                    "total_invested": 0,
                    "total_returns": 0,
                    "returns_percentage": 0,
                    "available_cash": margins['equity']['available']['cash'] if margins else 0,
                    "day_change": 0,
                    "day_change_percent": 0,
                    "zerodha_connected": True,
                    "holdings": [],
                    "allocation": [],
                    "total_holdings": 0,
                    "message": "No holdings found in your Zerodha account"
                }
            
            print(f"[SUCCESS] Retrieved {len(holdings)} holdings from Zerodha")
            
            # Process holdings data - INCLUDING pledged shares like your notebook
            portfolio_holdings = []
            total_investment = 0
            current_value = 0
            
            for holding in holdings:
                symbol = holding['tradingsymbol']
                
                # Handle ALL shares: regular + t1 + collateral (pledged) - EXACTLY like notebook
                regular_qty = holding.get('quantity', 0)
                t1_qty = holding.get('t1_quantity', 0)  
                collateral_qty = holding.get('collateral_quantity', 0)
                total_quantity = regular_qty + t1_qty + collateral_qty
                
                print(f"Processing {symbol}: regular={regular_qty}, t1={t1_qty}, collateral={collateral_qty}, total={total_quantity}")
                
                # Include ALL holdings that have any shares (including pledged ones)
                if total_quantity > 0:
                    avg_price = holding['average_price']
                    current_price = holding['last_price']
                    
                    # Validate prices
                    if avg_price <= 0 or current_price <= 0:
                        print(f"   [WARNING] {symbol}: Invalid prices - avg_price={avg_price}, current_price={current_price}")
                        continue
                    
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
                        "close_price": holding.get('close_price', current_price),
                        "pledged_status": "Pledged" if collateral_qty > 0 else "Free",
                        "free_quantity": regular_qty + t1_qty,
                        "pledged_quantity": collateral_qty
                    })
                    
                    total_investment += investment_value
                    current_value += holding_value
                    
                    print(f"[SUCCESS] Added {symbol}: Rs.{holding_value:,.2f} value, {pnl_percent:.2f}% P&L")
                else:
                    print(f"   [INFO] {symbol}: No shares to process (qty=0)")
            
            print(f"[INFO] Total processed holdings: {len(portfolio_holdings)}")
            print(f"[INFO] Total current value: Rs.{current_value:,.2f}")
            
            if len(portfolio_holdings) == 0:
                print("[ERROR] No valid holdings found after processing")
                return {
                    "user_id": 1,
                    "current_value": 0,
                    "invested_value": 0,
                    "total_invested": 0,
                    "total_returns": 0,
                    "returns_percentage": 0,
                    "available_cash": margins['equity']['available']['cash'] if margins else 0,
                    "day_change": 0,
                    "day_change_percent": 0,
                    "zerodha_connected": True,
                    "holdings": [],
                    "allocation": [],
                    "total_holdings": 0,
                    "message": "No valid holdings found (all holdings have zero quantity or invalid prices)"
                }
            
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
            
            # Get available cash with error handling
            available_cash = 0
            try:
                available_cash = margins['equity']['available']['cash'] if margins else 0
            except Exception as e:
                print(f"[WARNING] Could not fetch cash margin: {e}")
                available_cash = 0
            
            # Calculate day change for portfolio
            day_change = 0
            try:
                day_change = sum(
                    holding.get('day_change', 0) * portfolio_holdings[i]['quantity']
                    for i, holding in enumerate(holdings)
                    if i < len(portfolio_holdings)
                )
            except Exception as e:
                print(f"[WARNING] Could not calculate day change: {e}")
                day_change = 0
            
            day_change_percent = (day_change / current_value) * 100 if current_value > 0 else 0
            
            # Calculate portfolio metrics
            free_value = sum(
                h['free_quantity'] * h['current_price'] 
                for h in portfolio_holdings
            )
            pledged_value = sum(
                h['pledged_quantity'] * h['current_price'] 
                for h in portfolio_holdings
            )
            
            print(f"[SUCCESS] Portfolio processed successfully:")
            print(f"   [INFO] Holdings: {len(portfolio_holdings)}")
            print(f"   [INFO] Current Value: Rs.{current_value:,.2f}")
            print(f"   [SUCCESS] Total Returns: Rs.{total_returns:,.2f} ({returns_percentage:.2f}%)")
            print(f"   [INFO] Available Cash: Rs.{available_cash:,.2f}")
            print(f"   [INFO] Free Shares Value: Rs.{free_value:,.2f}")
            print(f"   [INFO] Pledged Shares Value: Rs.{pledged_value:,.2f}")
            
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
                "zerodha_connected": True,
                "data_source": "Zerodha Live API",
                "zerodha_profile": self.zerodha_auth.profile_name,
                "free_shares_value": free_value,
                "pledged_shares_value": pledged_value,
                "portfolio_breakdown": {
                    "free_holdings": [h for h in portfolio_holdings if h['free_quantity'] > 0],
                    "pledged_only_holdings": [h for h in portfolio_holdings if h['free_quantity'] == 0 and h['pledged_quantity'] > 0],
                    "mixed_holdings": [h for h in portfolio_holdings if h['free_quantity'] > 0 and h['pledged_quantity'] > 0]
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Error getting portfolio data: {e}")
            import traceback
            print(f"[ERROR] Full error: {traceback.format_exc()}")
            return {
                "error": "PORTFOLIO_DATA_UNAVAILABLE", 
                "error_message": str(e),
                "zerodha_connected": False,
                "user_id": 1,
                "current_value": 0,
                "invested_value": 0,
                "total_invested": 0,
                "total_returns": 0,
                "returns_percentage": 0,
                "available_cash": 0,
                "day_change": 0,
                "day_change_percent": 0,
                "holdings": [],
                "allocation": [],
                "total_holdings": 0,
                "message": f"Unable to fetch portfolio data: {str(e)}"
            }
    
    def get_connection_status(self):
        """Get detailed connection status"""
        return {
            "zerodha_auth_available": bool(self.zerodha_auth),
            "zerodha_authenticated": self.zerodha_auth.is_authenticated() if self.zerodha_auth else False,
            "kite_instance_available": bool(self.kite),
            "can_fetch_data": bool(self.zerodha_auth and self.zerodha_auth.is_authenticated() and self.kite),
            "profile_name": self.zerodha_auth.profile_name if self.zerodha_auth else None,
            "auth_status": self.zerodha_auth.get_auth_status() if self.zerodha_auth else {}
        }