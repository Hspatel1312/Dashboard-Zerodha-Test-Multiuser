# backend/app/services/portfolio_service.py

# Foundation imports
from .base.base_service import BaseService
from .base.zerodha_integration_mixin import DataFetchingZerodhaIntegrationMixin
from .utils.error_handler import ErrorHandler
from .utils.financial_calculations import FinancialCalculations
from .utils.logger import LoggerFactory

class PortfolioService(DataFetchingZerodhaIntegrationMixin, BaseService):
    def __init__(self, zerodha_auth):
        BaseService.__init__(self, service_name="portfolio_service")
        DataFetchingZerodhaIntegrationMixin.__init__(self, zerodha_auth)
        self.zerodha_auth = zerodha_auth
    
    def get_portfolio_data(self):
        """Get portfolio data from Zerodha with professional error handling"""
        with self.handle_operation_error("get_portfolio_data"):
            # Validate and get Kite instance
            kite = self.get_validated_kite_instance()
            if not kite:
                return self._create_empty_portfolio_response("Authentication failed")
        
            # Fetch data from Zerodha
            holdings, margins = self._fetch_zerodha_data(kite)
            
            if not holdings:
                return self._create_empty_portfolio_response("No holdings found in Zerodha account")
            
            # Process holdings data
            portfolio_holdings, total_investment, current_value = self._process_holdings_data(holdings)
            
            if not portfolio_holdings:
                return self._create_empty_portfolio_response("No valid holdings found after processing")
            
            # Calculate portfolio metrics
            portfolio_metrics = self._calculate_portfolio_metrics(portfolio_holdings, total_investment, current_value, margins, holdings)
            
            # Build final response
            return self._build_portfolio_response(portfolio_holdings, portfolio_metrics)
            
    def _fetch_zerodha_data(self, kite):
        """Fetch holdings and margins from Zerodha API"""
        self.logger.info("Fetching live portfolio data from Zerodha...")
        
        holdings = self.execute_kite_operation(
            lambda: kite.holdings(),
            operation_name="fetch_holdings"
        )
        
        margins = self.execute_kite_operation(
            lambda: kite.margins(),
            operation_name="fetch_margins",
            allow_failure=True  # Margins are optional
        )
        
        return holdings, margins
    
    def _process_holdings_data(self, holdings):
        """Process raw holdings data into portfolio holdings"""
        self.logger.success(f"Retrieved {len(holdings)} holdings from Zerodha")
        
        portfolio_holdings = []
        total_investment = 0
        current_value = 0
        
        for holding in holdings:
            processed_holding = self._process_single_holding(holding)
            if processed_holding:
                portfolio_holdings.append(processed_holding)
                total_investment += processed_holding['investment_value']
                current_value += processed_holding['current_value']
                
                symbol = processed_holding['symbol']
                pnl_percent = processed_holding['pnl_percent']
                holding_value = processed_holding['current_value']
                self.logger.success(f"Added {symbol}: Rs.{holding_value:,.2f} value, {pnl_percent:.2f}% P&L")
        
        self.logger.info(f"Total processed holdings: {len(portfolio_holdings)}")
        self.logger.info(f"Total current value: Rs.{current_value:,.2f}")
        
        return portfolio_holdings, total_investment, current_value
    
    def _process_single_holding(self, holding):
        """Process a single holding from Zerodha API"""
        symbol = holding['tradingsymbol']
        
        # Handle ALL shares: regular + t1 + collateral (pledged)
        regular_qty = holding.get('quantity', 0)
        t1_qty = holding.get('t1_quantity', 0)  
        collateral_qty = holding.get('collateral_quantity', 0)
        total_quantity = regular_qty + t1_qty + collateral_qty
        
        self.logger.info(f"Processing {symbol}: regular={regular_qty}, t1={t1_qty}, collateral={collateral_qty}, total={total_quantity}")
        
        # Skip holdings with no shares
        if total_quantity <= 0:
            self.logger.info(f"{symbol}: No shares to process (qty=0)")
            return None
        
        avg_price = holding['average_price']
        current_price = holding['last_price']
        
        # Validate prices
        if avg_price <= 0 or current_price <= 0:
            self.logger.warning(f"{symbol}: Invalid prices - avg_price={avg_price}, current_price={current_price}")
            return None
        
        holding_value = total_quantity * current_price
        investment_value = total_quantity * avg_price
        pnl = holding_value - investment_value
        pnl_percent = FinancialCalculations.calculate_returns_percentage(
            investment_value, holding_value
        )
        
        return {
            "symbol": symbol,
            "quantity": total_quantity,
            "regular_quantity": regular_qty,
            "t1_quantity": t1_qty,
            "collateral_quantity": collateral_qty,
            "avg_price": avg_price,
            "current_price": current_price,
            "current_value": holding_value,
            "investment_value": investment_value,
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
        }
    
    def _calculate_portfolio_metrics(self, portfolio_holdings, total_investment, current_value, margins, raw_holdings):
        """Calculate portfolio-level metrics"""
        # Calculate allocation percentages using FinancialCalculations
        for holding in portfolio_holdings:
            holding["allocation_percent"] = FinancialCalculations.calculate_allocation_percent(
                holding["current_value"], current_value
            )
        
        # Calculate overall returns
        total_returns = current_value - total_investment
        returns_percentage = FinancialCalculations.calculate_returns_percentage(
            total_investment, current_value
        )
        
        # Get available cash with error handling
        available_cash = self._get_available_cash(margins)
        
        # Calculate day change for portfolio
        day_change = self._calculate_day_change(portfolio_holdings, raw_holdings)
        day_change_percent = FinancialCalculations.calculate_returns_percentage(
            current_value - day_change, current_value
        ) if current_value > 0 else 0
        
        # Calculate portfolio breakdown
        free_value = sum(
            h['free_quantity'] * h['current_price'] 
            for h in portfolio_holdings
        )
        pledged_value = sum(
            h['pledged_quantity'] * h['current_price'] 
            for h in portfolio_holdings
        )
        
        self.logger.success("Portfolio processed successfully:")
        self.logger.info(f"Holdings: {len(portfolio_holdings)}")
        self.logger.info(f"Current Value: Rs.{current_value:,.2f}")
        self.logger.success(f"Total Returns: Rs.{total_returns:,.2f} ({returns_percentage:.2f}%)")
        self.logger.info(f"Available Cash: Rs.{available_cash:,.2f}")
        self.logger.info(f"Free Shares Value: Rs.{free_value:,.2f}")
        self.logger.info(f"Pledged Shares Value: Rs.{pledged_value:,.2f}")
        
        return {
            'total_returns': total_returns,
            'returns_percentage': returns_percentage,
            'available_cash': available_cash,
            'day_change': day_change,
            'day_change_percent': day_change_percent,
            'free_value': free_value,
            'pledged_value': pledged_value,
            'total_investment': total_investment,
            'current_value': current_value
        }
    
    def _get_available_cash(self, margins):
        """Get available cash with error handling"""
        try:
            return margins['equity']['available']['cash'] if margins else 0
        except Exception as e:
            self.logger.warning(f"Could not fetch cash margin: {e}")
            return 0
    
    def _calculate_day_change(self, portfolio_holdings, raw_holdings):
        """Calculate portfolio day change"""
        try:
            return sum(
                holding.get('day_change', 0) * portfolio_holdings[i]['quantity']
                for i, holding in enumerate(raw_holdings)
                if i < len(portfolio_holdings)
            )
        except Exception as e:
            self.logger.warning(f"Could not calculate day change: {e}")
            return 0
    
    def _build_portfolio_response(self, portfolio_holdings, metrics):
        """Build the final portfolio response"""
        return {
            "user_id": 1,
            "current_value": metrics['current_value'],
            "invested_value": metrics['total_investment'],
            "total_returns": metrics['total_returns'],
            "returns_percentage": metrics['returns_percentage'],
            "available_cash": metrics['available_cash'],
            "holdings": portfolio_holdings,
            "allocation": portfolio_holdings,  # Frontend compatibility
            "day_change": metrics['day_change'],
            "day_change_percent": metrics['day_change_percent'],
            "total_invested": metrics['total_investment'],  # Frontend compatibility
            "total_holdings": len(portfolio_holdings),
            "zerodha_connected": True,
            "data_source": "Zerodha Live API",
            "zerodha_profile": self.zerodha_auth.profile_name if self.zerodha_auth else "Unknown",
            "free_shares_value": metrics['free_value'],
            "pledged_shares_value": metrics['pledged_value'],
            "portfolio_breakdown": {
                "free_holdings": [h for h in portfolio_holdings if h['free_quantity'] > 0],
                "pledged_only_holdings": [h for h in portfolio_holdings if h['free_quantity'] == 0 and h['pledged_quantity'] > 0],
                "mixed_holdings": [h for h in portfolio_holdings if h['free_quantity'] > 0 and h['pledged_quantity'] > 0]
            }
        }
    
    def _create_empty_portfolio_response(self, message):
        """Create standardized empty portfolio response"""
        return ErrorHandler.create_error_response(
            error_message=message,
            operation="get_portfolio_data"
        ) | {
            "user_id": 1,
            "current_value": 0,
            "invested_value": 0,
            "total_invested": 0,
            "total_returns": 0,
            "returns_percentage": 0,
            "available_cash": 0,
            "day_change": 0,
            "day_change_percent": 0,
            "zerodha_connected": bool(self.zerodha_auth),
            "holdings": [],
            "allocation": [],
            "total_holdings": 0,
            "message": message
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