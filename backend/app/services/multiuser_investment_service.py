# backend/app/services/multiuser_investment_service.py - User-Specific Investment Service
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import math
from .csv_service import CSVService
from .investment_calculator import InvestmentCalculator
from .portfolio_construction_service import PortfolioConstructionService
from .portfolio_metrics_service import PortfolioMetricsService
from .portfolio_comparison_service import PortfolioComparisonService
from .multiuser_zerodha_auth import MultiUserZerodhaAuth
from ..database import UserDB

class MultiUserInvestmentService:
    """User-specific investment service - each user has their own portfolio and orders"""
    
    def __init__(self, user: UserDB, zerodha_auth: MultiUserZerodhaAuth):
        self.user = user
        self.zerodha_auth = zerodha_auth
        
        # User-specific directory for all data
        self.user_data_dir = user.user_data_directory
        
        # Initialize services with user-specific auth
        self.csv_service = CSVService(zerodha_auth)
        self.investment_calculator = InvestmentCalculator()
        self.portfolio_construction = PortfolioConstructionService()
        self.portfolio_metrics = PortfolioMetricsService()
        
        # Import portfolio service here to avoid circular imports
        from .portfolio_service import PortfolioService
        self.portfolio_service = PortfolioService(zerodha_auth)
        self.portfolio_comparison = PortfolioComparisonService(self.portfolio_service, self)
        
        # Import live order service
        from .live_order_service import LiveOrderService
        self.live_order_service = LiveOrderService(zerodha_auth, self.user_data_dir)
        
        # User-specific file paths
        self.orders_file = os.path.join(self.user_data_dir, "system_orders.json")
        self.portfolio_state_file = os.path.join(self.user_data_dir, "system_portfolio_state.json")
        self.csv_history_file = os.path.join(self.user_data_dir, "csv_history.json")
        self.failed_orders_file = os.path.join(self.user_data_dir, "failed_orders.json")
        self.live_orders_file = os.path.join(self.user_data_dir, "live_orders.json")
        
        # Configuration - Updated for ±1.5% flexibility
        self.min_investment = 200000
        self.target_allocation = 5.0
        self.min_allocation = 3.5  # 5% - 1.5%
        self.max_allocation = 6.5  # 5% + 1.5%
        self.rebalancing_threshold = 10000
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Auto-start monitoring if there are pending orders
        self._auto_start_monitoring()
    
    def _ensure_directories(self):
        """Ensure all required directories and files exist"""
        try:
            os.makedirs(self.user_data_dir, exist_ok=True)
            
            # Initialize empty files if they don't exist
            for file_path in [self.orders_file, self.portfolio_state_file, 
                             self.csv_history_file, self.failed_orders_file, self.live_orders_file]:
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)
                        
            print(f"[INFO] User {self.user.username} - Data directory initialized: {self.user_data_dir}")
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to create directories: {e}")
    
    def _auto_start_monitoring(self):
        """Auto-start monitoring if there are pending orders"""
        try:
            pending_orders = self.get_live_orders()
            if pending_orders.get('orders') and len(pending_orders['orders']) > 0:
                print(f"[INFO] User {self.user.username} - Auto-starting order monitoring...")
                self.live_order_service.start_order_monitoring()
        except Exception as e:
            print(f"[WARNING] User {self.user.username} - Could not auto-start monitoring: {e}")
    
    # All the existing methods from InvestmentService, but with user-specific file paths
    # and logging that includes the username
    
    def get_investment_status(self):
        """Get user's investment status"""
        print(f"[DEBUG] User {self.user.username} - ENTERING get_investment_status method")
        try:
            if not self.zerodha_auth.is_authenticated():
                return {
                    "success": False,
                    "error": "Zerodha authentication required",
                    "status": "AUTHENTICATION_REQUIRED"
                }
            
            # Check if user has any existing orders
            orders = self._load_orders()
            if not orders:
                # Get calculated minimum investment instead of using hardcoded default
                try:
                    requirements = self.get_investment_requirements()
                    if requirements and not requirements.get('error'):
                        calculated_min = requirements.get('minimum_investment', {}).get('minimum_investment', self.min_investment)
                    else:
                        calculated_min = self.min_investment  # Fallback to default if calculation fails
                except Exception as e:
                    print(f"[WARNING] User {self.user.username} - Could not get calculated minimum investment: {e}")
                    calculated_min = self.min_investment
                
                response = {
                    "success": True,
                    "data": {
                        "status": "FIRST_INVESTMENT",
                        "message": "Ready for first investment",
                        "min_investment": calculated_min,
                        "user": self.user.username
                    },
                    "status": "FIRST_INVESTMENT",
                    "message": "Ready for first investment", 
                    "min_investment": calculated_min,
                    "user": self.user.username
                }
                print(f"[DEBUG] User {self.user.username} - Investment status: FIRST_INVESTMENT (no orders found)")
                print(f"[DEBUG] Using calculated minimum investment: Rs.{calculated_min:,}")
                print(f"[DEBUG] Full response: {response}")
                return response
            
            # Get portfolio status to determine if rebalancing is needed
            portfolio_status = self.get_portfolio_status()
            if portfolio_status.get("success"):
                portfolio_data = portfolio_status.get("data", {})
                portfolio_summary = portfolio_data.get("portfolio_summary", {})
                needs_rebalancing = portfolio_summary.get("rebalancing_needed", False)
                
                print(f"[DEBUG] User {self.user.username} - Investment status check:")
                print(f"   Portfolio status success: {portfolio_status.get('success')}")
                print(f"   Portfolio summary keys: {list(portfolio_summary.keys())}")
                print(f"   rebalancing_needed value: {needs_rebalancing}")
                
                if needs_rebalancing:
                    result = {
                        "success": True,
                        "status": "REBALANCING_NEEDED",
                        "message": "Portfolio needs rebalancing",
                        "user": self.user.username
                    }
                    print(f"[DEBUG] User {self.user.username} - Returning REBALANCING_NEEDED status")
                    return result
                else:
                    result = {
                        "success": True,
                        "status": "BALANCED",
                        "message": "Portfolio is balanced",
                        "user": self.user.username
                    }
                    print(f"[DEBUG] User {self.user.username} - Returning BALANCED status")
                    return result
            else:
                return {
                    "success": True,
                    "status": "REBALANCING_NEEDED",
                    "message": "Unable to determine portfolio status, rebalancing recommended",
                    "user": self.user.username
                }
                
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Investment status error: {e}")
            return {
                "success": False,
                "error": f"Failed to get investment status: {str(e)}",
                "user": self.user.username
            }
    
    def _load_orders(self):
        """Load user's orders from their specific file"""
        try:
            if os.path.exists(self.orders_file):
                with open(self.orders_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Error loading orders: {e}")
            return []
    
    def _save_orders(self, orders):
        """Save user's orders to their specific file"""
        try:
            with open(self.orders_file, 'w', encoding='utf-8') as f:
                json.dump(orders, f, indent=2, ensure_ascii=False, default=str)
            print(f"[INFO] User {self.user.username} - Orders saved: {len(orders)} orders")
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Error saving orders: {e}")
    
    def get_portfolio_status(self):
        """Get user's portfolio status for dashboard"""
        try:
            print(f"[DEBUG] User {self.user.username} - ENTERING get_portfolio_status method")
            print(f"[INFO] User {self.user.username} - Getting portfolio status...")
            
            # Get CSV stocks first
            csv_stocks_result = self.get_csv_stocks()
            if not csv_stocks_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to get CSV stocks data",
                    "user": self.user.username
                }
            
            csv_stocks = csv_stocks_result["data"]
            
            # Get system orders
            orders = self._load_orders()
            
            # Calculate portfolio metrics
            print(f"[DEBUG] User {self.user.username} - About to calculate portfolio summary")
            portfolio_summary = self.portfolio_metrics.calculate_portfolio_summary(orders, csv_stocks)
            print(f"[DEBUG] User {self.user.username} - Portfolio summary calculated")
            
            # Check if rebalancing is needed (stock list changes)
            try:
                print(f"[DEBUG] User {self.user.username} - About to call check_rebalancing_needed()")
                rebalancing_check = self.check_rebalancing_needed()
                print(f"[DEBUG] User {self.user.username} - Rebalancing check result: {rebalancing_check}")
                portfolio_summary['rebalancing_needed'] = rebalancing_check.get('rebalancing_needed', False)
                portfolio_summary['rebalancing_reason'] = rebalancing_check.get('reason', 'Unknown')
            except Exception as e:
                print(f"[ERROR] User {self.user.username} - Error in rebalancing check: {e}")
                portfolio_summary['rebalancing_needed'] = False
                portfolio_summary['rebalancing_reason'] = f'Error: {str(e)}'
            
            # Get comparison data
            try:
                comparison_result = self.portfolio_comparison.get_comparison_data()
                comparison_data = comparison_result.get("data") if comparison_result.get("success") else None
            except Exception as e:
                print(f"[WARNING] User {self.user.username} - Could not get comparison data: {e}")
                comparison_data = None
            
            response_data = {
                "success": True,
                "data": {
                    "portfolio_summary": portfolio_summary,
                    "comparison_data": comparison_data,
                    "total_orders": len(orders),
                    "csv_stocks_count": len(csv_stocks.get('stocks', [])) if isinstance(csv_stocks, dict) else len(csv_stocks),
                    "user": self.user.username,
                    # Expose holdings at top level for frontend compatibility
                    "holdings": portfolio_summary.get('holdings', {})
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Debug: Log portfolio status response
            print(f"[DEBUG] User {self.user.username} - Portfolio status response:")
            print(f"[DEBUG]   Orders loaded: {len(orders)}")
            print(f"[DEBUG]   Portfolio current value: {portfolio_summary.get('current_value', 0)}")
            print(f"[DEBUG]   Total investment: {portfolio_summary.get('total_investment', 0)}")
            print(f"[DEBUG]   Holdings count: {portfolio_summary.get('stock_count', 0)}")
            print(f"[DEBUG]   *** HOLDINGS DATA DEBUG ***: {portfolio_summary.get('holdings', {})}")
            print(f"[DEBUG]   *** EXPOSING AT TOP LEVEL ***: {len(portfolio_summary.get('holdings', {}))}")
            
            return response_data
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Portfolio status error: {e}")
            return {
                "success": False,
                "error": f"Failed to get portfolio status: {str(e)}",
                "user": self.user.username
            }
    
    def get_csv_stocks(self):
        """Get CSV stocks with current prices (shared across all users)"""
        try:
            print(f"[INFO] User {self.user.username} - Getting CSV stocks...")
            
            if not self.zerodha_auth.is_authenticated():
                return {
                    "success": False,
                    "error": "Zerodha authentication required",
                    "user": self.user.username
                }
            
            # Use the updated get_stocks_with_prices method instead of get_csv_data
            stocks_data = self.csv_service.get_stocks_with_prices(force_refresh=False)
            
            # Check if there was an error fetching the data
            if 'error' in stocks_data:
                print(f"[WARNING] User {self.user.username} - CSV service returned error: {stocks_data.get('error_message', 'Unknown error')}")
                return {
                    "success": False,
                    "error": stocks_data.get('error_message', 'Failed to fetch CSV stocks data'),
                    "user": self.user.username,
                    "debug_info": {
                        "error_type": stocks_data.get('error'),
                        "price_status": stocks_data.get('price_data_status', {})
                    }
                }
            
            # Ensure data structure matches what frontend expects
            response_data = {
                "success": True,
                "data": {
                    "stocks": stocks_data.get('stocks', []),
                    "csv_info": stocks_data.get('csv_info', {}),
                    "price_data_status": stocks_data.get('price_data_status', {})
                },
                "total_stocks": stocks_data.get('total_stocks', 0),
                "timestamp": datetime.now().isoformat(),
                "user": self.user.username
            }
            
            # Debug: Log what we're returning to frontend
            print(f"[DEBUG] User {self.user.username} - Returning CSV stocks response:")
            print(f"[DEBUG]   Success: {response_data['success']}")
            print(f"[DEBUG]   Total stocks: {response_data['total_stocks']}")
            print(f"[DEBUG]   Stocks count: {len(response_data['data']['stocks'])}")
            if response_data['data']['stocks']:
                print(f"[DEBUG]   First stock: {response_data['data']['stocks'][0]['symbol']} at Rs.{response_data['data']['stocks'][0]['price']}")
            
            return response_data
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - CSV stocks error: {e}")
            return {
                "success": False,
                "error": f"Failed to get CSV stocks: {str(e)}",
                "user": self.user.username
            }
    
    def get_system_orders(self):
        """Get user's system orders"""
        try:
            orders = self._load_orders()
            return {
                "success": True,
                "data": orders,
                "total_orders": len(orders),
                "user": self.user.username
            }
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - System orders error: {e}")
            return {
                "success": False,
                "error": f"Failed to get system orders: {str(e)}",
                "user": self.user.username
            }
    
    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed (from original single-user logic)"""
        try:
            orders = self._load_orders()
            
            if not orders:
                return {
                    'rebalancing_needed': False,
                    'reason': 'No system portfolio found - initial investment needed',
                    'is_first_time': True
                }
            
            # Get current portfolio holdings
            portfolio_summary = self.portfolio_metrics.calculate_portfolio_summary(orders, [])
            current_holdings = portfolio_summary.get('holdings', {})
            
            if not current_holdings:
                return {
                    'rebalancing_needed': False,
                    'reason': 'No system portfolio found - initial investment needed',
                    'is_first_time': True
                }
            
            # Compare with current CSV
            current_symbols = set(current_holdings.keys())
            
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
                csv_symbols = set(stock['symbol'] for stock in stocks_data.get('stocks', []))
            except Exception as e:
                print(f"[WARNING] User {self.user.username} - Could not fetch current CSV: {e}")
                return {
                    'rebalancing_needed': False,
                    'reason': 'Cannot fetch current CSV data',
                    'is_first_time': False,
                    'error': str(e)
                }
            
            new_stocks = csv_symbols - current_symbols
            removed_stocks = current_symbols - csv_symbols
            
            rebalancing_needed = len(new_stocks) > 0 or len(removed_stocks) > 0
            
            print(f"[INFO] User {self.user.username} - Rebalancing check:")
            print(f"   CSV stocks: {sorted(csv_symbols)}")
            print(f"   Portfolio stocks: {sorted(current_symbols)}")
            print(f"   New stocks: {sorted(new_stocks) if new_stocks else 'None'}")
            print(f"   Removed stocks: {sorted(removed_stocks) if removed_stocks else 'None'}")
            print(f"   Rebalancing needed: {rebalancing_needed}")
            
            if rebalancing_needed:
                return {
                    'rebalancing_needed': True,
                    'reason': f'Stock changes: +{len(new_stocks)} new, -{len(removed_stocks)} removed',
                    'new_stocks': list(new_stocks),
                    'removed_stocks': list(removed_stocks),
                    'is_first_time': False
                }
            else:
                return {
                    'rebalancing_needed': False,
                    'reason': 'Portfolio matches CSV stocks exactly',
                    'is_first_time': False
                }
                
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Rebalancing check error: {e}")
            return {
                'rebalancing_needed': False,
                'reason': f'Error checking rebalancing: {str(e)}',
                'is_first_time': False,
                'error': str(e)
            }

    # User-specific utility methods
    
    def _get_next_order_id(self) -> int:
        """Get next order ID for this user"""
        orders = self._load_orders()
        if not orders:
            return 1
        # Find max order_id, defaulting to 0 if no order_id exists
        max_id = 0
        for order in orders:
            if isinstance(order, dict) and 'order_id' in order:
                max_id = max(max_id, order['order_id'])
        return max_id + 1
    
    def get_live_orders(self):
        """Get user's live orders with current status from Zerodha"""
        try:
            print(f"[INFO] User {self.user.username} - Getting live orders...")
            
            # Get all tracked orders with updated status
            live_orders = self.live_order_service.get_all_live_orders()
            
            return {
                "success": True,
                "orders": live_orders,
                "total_orders": len(live_orders),
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to get live orders: {e}")
            return {
                "success": False,
                "error": f"Failed to get live orders: {str(e)}",
                "orders": [],
                "user": self.user.username
            }
    
    def get_failed_orders(self):
        """Get user's failed orders"""
        try:
            print(f"[INFO] User {self.user.username} - Getting failed orders...")
            
            # Load system orders and filter for failed ones
            orders = self._load_orders()
            failed_orders = [order for order in orders if order.get('status') in ['FAILED', 'FAILED_TO_PLACE', 'REJECTED', 'CANCELLED']]
            
            return {
                "success": True,
                "orders": failed_orders,
                "total_orders": len(failed_orders),
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to get failed orders: {e}")
            return {
                "success": False,
                "error": f"Failed to get failed orders: {str(e)}",
                "orders": [],
                "user": self.user.username
            }
    
    def get_investment_requirements(self) -> Dict:
        """Get investment requirements for initial setup"""
        try:
            print(f"[INFO] User {self.user.username} - Getting investment requirements...")
            
            # Get stocks with prices directly from CSV service (same as original)
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                print(f"[ERROR] User {self.user.username} - Failed to get stocks with prices: {e}")
                raise Exception(f"Unable to fetch stock data: {str(e)}")
            
            # Check if we got an error response (no live prices available)
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print(f"[ERROR] User {self.user.username} - PRICE_DATA_UNAVAILABLE - returning error response")
                
                # Return structured error response
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data unavailable'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'price_data_status': stocks_data.get('price_data_status', {}),
                    'user': self.user.username
                }
            
            stocks = stocks_data.get('stocks', [])
            
            # Use InvestmentCalculator to calculate minimum investment
            minimum_investment_result = self.investment_calculator.calculate_minimum_investment(stocks)
            
            requirements = {
                "minimum_investment": minimum_investment_result,
                "stock_count": len(stocks),
                "csv_info": stocks_data.get('csv_info', {}),
                "price_data_status": stocks_data.get('price_data_status', {}),
                "user": self.user.username
            }
            
            print(f"[INFO] User {self.user.username} - Investment requirements calculated successfully")
            return requirements
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Error getting investment requirements: {e}")
            
            # Check if it's a price data error
            if "price data" in str(e).lower() or "stock data" in str(e).lower():
                return {
                    "minimum_investment": {
                        "minimum_investment": self.min_investment,
                        "recommended_minimum": self.min_investment,
                        "note": "Calculated without current market prices"
                    },
                    "error": "Current market prices unavailable, using default minimums",
                    "ready_for_investment": False,
                    "user": self.user.username
                }
            
            raise Exception(f"Cannot provide investment requirements: {str(e)}")
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan"""
        try:
            print(f"[INFO] User {self.user.username} - Calculating investment plan for Rs.{investment_amount}")
            
            # Get stocks with prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Check if we got an error response (no live prices available)
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print(f"[ERROR] User {self.user.username} - PRICE_DATA_UNAVAILABLE - cannot calculate plan")
                
                # Return structured error response
                return {
                    'success': False,
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data unavailable'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'price_data_status': stocks_data.get('price_data_status', {}),
                    'data_quality': {
                        'live_data_available': False,
                        'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()) if self.zerodha_auth else False,
                        'error_reason': stocks_data.get('error_message', 'Live price data unavailable')
                    },
                    'user': self.user.username
                }
            
            # Validate minimum investment
            min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(f"Investment amount Rs.{investment_amount:,.0f} is below minimum required Rs.{min_investment_info['minimum_investment']:,.0f}")
            
            # Calculate allocation using the sophisticated algorithm
            allocation_result = self.investment_calculator.calculate_optimal_allocation(investment_amount, stocks_data['stocks'])
            
            # Generate orders from allocation
            orders = []
            for allocation in allocation_result['allocations']:
                if allocation['shares'] > 0:
                    orders.append({
                        'symbol': allocation['symbol'],
                        'action': 'BUY',
                        'shares': allocation['shares'],
                        'price': allocation['price'],
                        'value': allocation['value'],
                        'allocation_percent': allocation['allocation_percent']
                    })
            
            plan = {
                'investment_amount': investment_amount,
                'allocation_plan': allocation_result,
                'orders': orders,
                'total_stocks': len(stocks_data['stocks']),
                'csv_info': stocks_data.get('csv_info', {}),
                'price_data_status': stocks_data.get('price_data_status', {})
            }
            
            return {
                "success": True,
                "plan": plan,
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to calculate initial investment plan: {e}")
            return {
                "success": False,
                "error": f"Failed to calculate investment plan: {str(e)}",
                "user": self.user.username
            }
    
    def execute_initial_investment(self, investment_amount: float) -> Dict:
        """Execute initial investment"""
        try:
            print(f"[INFO] User {self.user.username} - Executing initial investment for {investment_amount}")
            
            # Calculate the investment plan first
            plan_response = self.calculate_initial_investment_plan(investment_amount)
            if not plan_response.get("success"):
                return plan_response
            
            plan = plan_response["plan"]
            orders = plan.get("orders", [])
            
            if not orders:
                return {
                    "success": False,
                    "error": "No orders to execute",
                    "user": self.user.username
                }
            
            # Execute orders on Zerodha and save to user's file
            print(f"[INFO] User {self.user.username} - Executing {len(orders)} orders on Zerodha...")
            
            executed_orders = []
            execution_time = datetime.now().isoformat()
            order_id = self._get_next_order_id()
            
            for order in orders:
                try:
                    # Prepare system order with execution metadata
                    system_order = {
                        'order_id': order_id,
                        'symbol': order['symbol'],
                        'action': order['action'],
                        'shares': order['shares'],
                        'price': order['price'],
                        'value': order['value'],
                        'allocation_percent': order['allocation_percent'],
                        'execution_time': execution_time,
                        'session_type': 'INITIAL_INVESTMENT'
                    }
                    
                    # Execute on Zerodha (LIVE trading)
                    try:
                        print(f"[INFO] User {self.user.username} - Executing {order['action']} {order['shares']} shares of {order['symbol']} at Rs.{order['price']}")
                    except UnicodeEncodeError:
                        print(f"[INFO] User {self.user.username} - Executing {order['action']} {order['shares']} shares of {order['symbol']} at Rs.{order['price']}".encode('utf-8', errors='replace').decode('utf-8'))
                    
                    if self.zerodha_auth.kite:
                        try:
                            # Place order on Zerodha
                            zerodha_order = self.zerodha_auth.kite.place_order(
                                variety=self.zerodha_auth.kite.VARIETY_REGULAR,
                                exchange=self.zerodha_auth.kite.EXCHANGE_NSE,
                                tradingsymbol=order['symbol'],
                                transaction_type=self.zerodha_auth.kite.TRANSACTION_TYPE_BUY if order['action'] == 'BUY' else self.zerodha_auth.kite.TRANSACTION_TYPE_SELL,
                                quantity=order['shares'],
                                product=self.zerodha_auth.kite.PRODUCT_CNC,  # Cash and Carry for long-term investment
                                order_type=self.zerodha_auth.kite.ORDER_TYPE_MARKET
                            )
                            
                            system_order['zerodha_order_id'] = zerodha_order.get('order_id')
                            system_order['status'] = 'EXECUTED'
                            try:
                                print(f"[SUCCESS] User {self.user.username} - Order {order_id} placed successfully on Zerodha. Order ID: {zerodha_order.get('order_id')}")
                            except UnicodeEncodeError:
                                print(f"[SUCCESS] User {self.user.username} - Order {order_id} placed successfully on Zerodha")
                        except Exception as zerodha_error:
                            # Handle Zerodha API errors with Unicode safety
                            try:
                                zerodha_error_msg = str(zerodha_error)
                            except UnicodeEncodeError:
                                zerodha_error_msg = "Zerodha API error (Unicode issue in message)"
                            
                            system_order['status'] = 'FAILED' 
                            system_order['error'] = f"Zerodha API error: {zerodha_error_msg}"
                            try:
                                print(f"[ERROR] User {self.user.username} - Zerodha API error for order {order_id}: {zerodha_error_msg}")
                            except UnicodeEncodeError:
                                print(f"[ERROR] User {self.user.username} - Zerodha API error for order {order_id}: Unicode error")
                    else:
                        system_order['status'] = 'FAILED'
                        system_order['error'] = 'Zerodha connection not available'
                        try:
                            print(f"[ERROR] User {self.user.username} - Failed to execute order {order_id}: No Zerodha connection")
                        except UnicodeEncodeError:
                            print(f"[ERROR] User {self.user.username} - Failed to execute order {order_id}: No Zerodha connection (Unicode error)")
                    
                    executed_orders.append(system_order)
                    order_id += 1
                    
                except Exception as order_error:
                    # Handle Unicode encoding issues in error messages
                    try:
                        error_msg = str(order_error)
                    except UnicodeEncodeError:
                        error_msg = "Unicode encoding error in order execution"
                    
                    try:
                        print(f"[ERROR] User {self.user.username} - Failed to execute order {order_id}: {error_msg}")
                    except UnicodeEncodeError:
                        print(f"[ERROR] User {self.user.username} - Failed to execute order {order_id}: Unicode error in message")
                    
                    system_order['status'] = 'FAILED'
                    system_order['error'] = error_msg
                    executed_orders.append(system_order)
                    order_id += 1
            
            # Save executed orders to user's file
            self._save_orders(executed_orders)
            
            successful_orders = [o for o in executed_orders if o.get('status') == 'EXECUTED']
            failed_orders = [o for o in executed_orders if o.get('status') == 'FAILED']
            
            return {
                "success": len(successful_orders) > 0,
                "message": f"Executed {len(successful_orders)} orders successfully, {len(failed_orders)} failed",
                "orders_executed": len(successful_orders),
                "orders_failed": len(failed_orders),
                "total_orders": len(executed_orders),
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to execute initial investment: {e}")
            return {
                "success": False,
                "error": f"Failed to execute initial investment: {str(e)}",
                "user": self.user.username
            }
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0.0) -> Dict:
        """Calculate rebalancing plan for multiuser (adapted from working single-user logic)"""
        try:
            print(f"[INFO] User {self.user.username} - Calculating rebalancing with additional investment: Rs.{additional_investment:,.0f}")
            
            # Step 1: Get current portfolio status with allocations
            portfolio_response = self.get_portfolio_status()
            if not portfolio_response.get("success"):
                return {
                    "success": False,
                    "error": "Unable to get portfolio status for rebalancing",
                    "user": self.user.username
                }
            
            portfolio_data = portfolio_response.get("data", {})
            current_holdings = portfolio_data.get("portfolio_summary", {}).get("holdings", {})
            current_portfolio_value = portfolio_data.get("portfolio_summary", {}).get("current_value", 0)
            
            if not current_holdings:
                return {
                    "success": False,
                    "error": "No current holdings found for rebalancing",
                    "user": self.user.username
                }
            
            print(f"[INFO] User {self.user.username} - Current portfolio value: Rs.{current_portfolio_value:,.0f}")
            
            # Step 2: Add additional investment if provided
            total_rebalancing_value = current_portfolio_value + additional_investment
            print(f"[INFO] User {self.user.username} - Total value for rebalancing: Rs.{total_rebalancing_value:,.0f}")
            
            # Step 3: Get current CSV stocks with prices
            csv_response = self.get_csv_stocks()
            if not csv_response.get("success"):
                return {
                    "success": False,
                    "error": "Cannot get CSV stocks for rebalancing",
                    "user": self.user.username
                }
            
            csv_stocks = csv_response.get("data", {}).get("stocks", [])
            if not csv_stocks:
                return {
                    "success": False,
                    "error": "No stocks found in CSV",
                    "user": self.user.username
                }
            
            print(f"[INFO] User {self.user.username} - Rebalancing to {len(csv_stocks)} stocks from CSV")
            
            # Step 4: Calculate optimal allocation using investment calculator
            allocation_result = self.investment_calculator.calculate_optimal_allocation(
                total_rebalancing_value, csv_stocks
            )
            
            # Step 5: Create target portfolio plan
            target_portfolio = {}
            total_target_value = allocation_result['total_allocated']
            
            for allocation in allocation_result['allocations']:
                if allocation['shares'] > 0:
                    target_portfolio[allocation['symbol']] = {
                        'shares': allocation['shares'],
                        'price': allocation['price'],
                        'value': allocation['value'],
                        'allocation_percent': allocation['allocation_percent']
                    }
            
            print(f"[INFO] User {self.user.username} - Target portfolio: {len(target_portfolio)} stocks, Rs.{total_target_value:,.0f} total value")
            
            # Step 6: Check for stock list changes and calculate orders
            buy_orders = []
            sell_orders = []
            
            csv_symbols = set(stock['symbol'] for stock in csv_stocks)
            portfolio_symbols = set(current_holdings.keys())
            
            print(f"[INFO] User {self.user.username} - CSV stocks: {sorted(csv_symbols)}")
            print(f"[INFO] User {self.user.username} - Portfolio stocks: {sorted(portfolio_symbols)}")
            
            # New stocks to add (in CSV but not in portfolio)
            new_stocks = csv_symbols - portfolio_symbols
            if new_stocks:
                print(f"[INFO] User {self.user.username} - New stocks to add: {sorted(new_stocks)}")
                for symbol in new_stocks:
                    target_info = target_portfolio[symbol]
                    buy_orders.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "shares": target_info['shares'],
                        "price": target_info['price'],
                        "value": target_info['value'],
                        "reason": "New stock added to CSV list"
                    })
            
            # Stocks to remove (in portfolio but not in CSV)
            removed_stocks = portfolio_symbols - csv_symbols
            if removed_stocks:
                print(f"[INFO] User {self.user.username} - Stocks to remove: {sorted(removed_stocks)}")
                for symbol in removed_stocks:
                    if symbol in current_holdings:
                        holding = current_holdings[symbol]
                        shares = holding.get('quantity', holding.get('shares', 0))
                        current_price = holding.get('current_price', 0)
                        if shares > 0:
                            sell_orders.append({
                                "symbol": symbol,
                                "action": "SELL",
                                "shares": shares,
                                "price": current_price,
                                "value": shares * current_price,
                                "reason": "Stock removed from CSV list"
                            })
            
            # Handle additional investment by proportionally increasing existing positions
            if additional_investment > 0:
                print(f"[INFO] User {self.user.username} - Adding proportional investment of Rs.{additional_investment:,.0f} to existing stocks")
                
                common_stocks = csv_symbols & portfolio_symbols
                if common_stocks:
                    additional_per_stock = additional_investment / len(common_stocks)
                    
                    for symbol in common_stocks:
                        target_info = target_portfolio[symbol]
                        current_price = target_info['price']
                        additional_shares = int(additional_per_stock / current_price)
                        
                        if additional_shares > 0:
                            buy_orders.append({
                                "symbol": symbol,
                                "action": "BUY",
                                "shares": additional_shares,
                                "price": current_price,
                                "value": additional_shares * current_price,
                                "reason": f"Additional investment (Rs.{additional_per_stock:,.0f} allocated)"
                            })
            
            total_buy_value = sum(order['value'] for order in buy_orders)
            total_sell_value = sum(order['value'] for order in sell_orders)
            net_investment_needed = total_buy_value - total_sell_value
            
            rebalancing_needed = len(buy_orders) > 0 or len(sell_orders) > 0
            
            if not rebalancing_needed and additional_investment == 0:
                return {
                    'success': True,
                    'message': 'Portfolio matches CSV stocks exactly - no rebalancing needed',
                    'plan': {
                        'buy_orders': [],
                        'sell_orders': [],
                        'plan_summary': {
                            'rebalancing_needed': False,
                            'current_portfolio_value': current_portfolio_value,
                            'additional_investment': additional_investment,
                            'total_rebalancing_value': current_portfolio_value,
                            'buy_orders_count': 0,
                            'sell_orders_count': 0,
                            'total_buy_value': 0,
                            'total_sell_value': 0,
                            'net_investment_needed': 0
                        }
                    },
                    "user": self.user.username
                }
            
            plan_summary = {
                "current_portfolio_value": current_portfolio_value,
                "additional_investment": additional_investment,
                "total_rebalancing_value": total_rebalancing_value,
                "target_portfolio_value": total_target_value,
                "remaining_cash": allocation_result['remaining_cash'],
                "total_stocks": len(target_portfolio),
                "buy_orders_count": len(buy_orders),
                "sell_orders_count": len(sell_orders),
                "total_buy_value": total_buy_value,
                "total_sell_value": total_sell_value,
                "net_investment_needed": net_investment_needed,
                "rebalancing_needed": rebalancing_needed
            }
            
            print(f"[SUCCESS] User {self.user.username} - Rebalancing plan calculated:")
            print(f"   Buy orders: {len(buy_orders)} (Rs.{total_buy_value:,.0f})")
            print(f"   Sell orders: {len(sell_orders)} (Rs.{total_sell_value:,.0f})")
            
            return {
                "success": True,
                "message": "Rebalancing plan calculated successfully",
                "plan": {
                    "plan_summary": plan_summary,
                    "target_portfolio": target_portfolio,
                    "allocation_result": allocation_result,
                    "buy_orders": buy_orders,
                    "sell_orders": sell_orders,
                    "stock_changes": buy_orders + sell_orders
                },
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to calculate rebalancing: {e}")
            return {
                "success": False,
                "error": f"Failed to calculate rebalancing: {str(e)}",
                "user": self.user.username
            }
    
    def execute_rebalancing(self, additional_investment: float = 0.0) -> Dict:
        """Execute rebalancing (adapted from working single-user logic)"""
        try:
            print(f"[INFO] User {self.user.username} - Executing rebalancing with additional investment: Rs.{additional_investment:,.0f}")
            
            # Calculate the rebalancing plan first
            plan_response = self.calculate_rebalancing_plan(additional_investment)
            if not plan_response.get("success"):
                return plan_response
            
            plan = plan_response["plan"]
            buy_orders = plan.get("buy_orders", [])
            sell_orders = plan.get("sell_orders", [])
            
            if not buy_orders and not sell_orders:
                return {
                    "success": True,
                    "message": "No rebalancing needed",
                    "user": self.user.username
                }
            
            # Load existing orders and create new ones
            existing_orders = self._load_orders()
            new_orders = []
            order_id = self._get_next_order_id()
            execution_time = datetime.now().isoformat()
            
            # Add sell orders first
            for sell_order in sell_orders:
                order = {
                    "order_id": order_id,
                    "symbol": sell_order['symbol'],
                    "action": "SELL",
                    "shares": sell_order['shares'],
                    "price": sell_order['price'],
                    "value": sell_order['value'],
                    "allocation_percent": 0,  # Will be calculated later
                    "execution_time": execution_time,
                    "session_type": "REBALANCING",
                    "status": "PENDING",
                    "can_retry": True,
                    "retry_count": 0,
                    "retry_history": []
                }
                
                new_orders.append(order)
                order_id += 1
                print(f"   SELL {sell_order['shares']} {sell_order['symbol']} @ Rs.{sell_order['price']:.2f} - {sell_order.get('reason', '')}")
            
            # Add buy orders
            for buy_order in buy_orders:
                order = {
                    "order_id": order_id,
                    "symbol": buy_order['symbol'],
                    "action": "BUY", 
                    "shares": buy_order['shares'],
                    "price": buy_order['price'],
                    "value": buy_order['value'],
                    "allocation_percent": 0,  # Will be calculated later
                    "execution_time": execution_time,
                    "session_type": "REBALANCING",
                    "status": "PENDING",
                    "can_retry": True,
                    "retry_count": 0,
                    "retry_history": []
                }
                
                new_orders.append(order)
                order_id += 1
                print(f"   BUY {buy_order['shares']} {buy_order['symbol']} @ Rs.{buy_order['price']:.2f} - {buy_order.get('reason', '')}")
            
            # Save new orders to user's file
            all_orders = existing_orders + new_orders
            self._save_orders(all_orders)
            
            plan_summary = plan.get("plan_summary", {})
            
            result = {
                "success": True,
                "message": f"Rebalancing executed with {len(new_orders)} new orders",
                "execution_successful": True,
                "orders_executed": len(new_orders),
                "buy_orders": len(buy_orders),
                "sell_orders": len(sell_orders),
                "total_buy_value": plan_summary.get('total_buy_value', 0),
                "total_sell_value": plan_summary.get('total_sell_value', 0),
                "net_investment": plan_summary.get('net_investment_needed', 0),
                "additional_investment_used": additional_investment,
                "execution_time": execution_time,
                "new_portfolio_stocks": plan_summary.get('total_stocks', 0),
                "target_portfolio_value": plan_summary.get('target_portfolio_value', 0),
                "remaining_cash": plan_summary.get('remaining_cash', 0),
                "user": self.user.username
            }
            
            print(f"[SUCCESS] User {self.user.username} - Rebalancing executed successfully!")
            print(f"   New orders executed: {result['orders_executed']}")
            print(f"   Buy orders: {result['buy_orders']}, Sell orders: {result['sell_orders']}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to execute rebalancing: {e}")
            return {
                "success": False,
                "error": f"Failed to execute rebalancing: {str(e)}",
                "user": self.user.username
            }
    
    def retry_failed_orders(self, order_ids: list = None) -> Dict:
        """Retry failed orders"""
        try:
            print(f"[INFO] User {self.user.username} - Retrying failed orders: {order_ids}")
            
            # Use live order service to retry failed orders
            result = self.live_order_service.retry_failed_orders(order_ids)
            
            return {
                "success": True,
                "result": result,
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to retry failed orders: {e}")
            return {
                "success": False,
                "error": f"Failed to retry failed orders: {str(e)}",
                "user": self.user.username
            }
    
    def get_orders_with_retry_history(self) -> list:
        """Get all orders grouped by parent with their retry history"""
        try:
            print(f"[DEBUG] User {self.user.username} - get_orders_with_retry_history called")
            # Load system orders (which contain retry history)
            orders = self._load_orders()
            print(f"[DEBUG] User {self.user.username} - Loaded {len(orders)} orders")
            
            # Transform to the format expected by frontend
            orders_with_retry_history = []
            
            for order in orders:
                # Check if this order has retry history
                retry_history = order.get('retry_history', [])
                has_retries = len(retry_history) > 0
                total_attempts = (order.get('retry_count', 0)) + 1  # Original attempt + retries
                
                order_group = {
                    "main_order": {
                        "order_id": order.get('order_id'),
                        "symbol": order.get('symbol'),
                        "action": order.get('action'),
                        "shares": order.get('shares'),
                        "price": order.get('price'),
                        "value": order.get('value'),
                        "execution_time": order.get('execution_time'),
                        "status": order.get('status')
                    },
                    "has_retries": has_retries,
                    "total_attempts": total_attempts,
                    "latest_status": order.get('status', 'UNKNOWN'),
                    "retry_history": []
                }
                
                # Add retry attempts if they exist
                if has_retries:
                    for retry in retry_history:
                        order_group["retry_history"].append({
                            "retry_number": retry.get('retry_number', 0),
                            "retry_time": retry.get('retry_time'),
                            "zerodha_order_id": retry.get('zerodha_order_id'),
                            "status": retry.get('status', 'UNKNOWN'),
                            "failure_reason": retry.get('failure_reason')
                        })
                
                orders_with_retry_history.append(order_group)
            
            print(f"[DEBUG] User {self.user.username} - Created {len(orders_with_retry_history)} order groups")
            for i, group in enumerate(orders_with_retry_history):
                print(f"[DEBUG] Group {i+1}: Order {group['main_order']['order_id']}, has_retries={group['has_retries']}, total_attempts={group['total_attempts']}")
            
            return orders_with_retry_history
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to get orders with retry history: {e}")
            return []
    
    def get_monitoring_status(self) -> dict:
        """Get current monitoring status with live order tracking"""
        try:
            print(f"[INFO] User {self.user.username} - Getting monitoring status...")
            
            # Get live orders to check for pending ones
            live_orders = self.live_order_service.get_all_live_orders()
            pending_orders = [
                order for order in live_orders 
                if order.get('status') in ['PLACED', 'OPEN', 'TRIGGER PENDING']
            ]
            completed_orders = [
                order for order in live_orders 
                if order.get('status') in ['COMPLETE', 'CANCELLED', 'REJECTED']
            ]
            
            monitoring_active = self.live_order_service.monitoring_active
            
            return {
                "monitoring_active": monitoring_active,
                "last_check": datetime.now().isoformat(),
                "pending_orders": len(pending_orders),
                "completed_orders": len(completed_orders),
                "total_tracked_orders": len(live_orders),
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to get monitoring status: {e}")
            return {
                "monitoring_active": False,
                "last_check": None,
                "pending_orders": 0,
                "completed_orders": 0,
                "error": str(e),
                "user": self.user.username
            }
    
    def force_csv_refresh(self) -> dict:
        """Force refresh of CSV stocks data"""
        try:
            print(f"[INFO] User {self.user.username} - Forcing CSV refresh...")
            
            # Force refresh using get_stocks_with_prices with force_refresh=True
            stocks_data = self.csv_service.get_stocks_with_prices(force_refresh=True)
            
            if 'error' in stocks_data:
                return {
                    "success": False,
                    "error": stocks_data.get('error_message', 'Failed to refresh CSV data'),
                    "user": self.user.username
                }
            
            return {
                "success": True,
                "message": "CSV data refreshed successfully",
                "total_stocks": stocks_data.get('total_stocks', 0),
                "user": self.user.username,
                "data": stocks_data
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to force CSV refresh: {e}")
            return {
                "success": False,
                "error": f"Failed to refresh CSV: {str(e)}",
                "user": self.user.username
            }
    
    def start_order_monitoring(self) -> dict:
        """Start automatic order monitoring for this user"""
        try:
            print(f"[INFO] User {self.user.username} - Starting order monitoring...")
            
            # Start monitoring with 15-second intervals
            self.live_order_service.start_order_monitoring(check_interval=15)
            
            return {
                "success": True,
                "message": "Order monitoring started successfully",
                "monitoring_active": True,
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to start monitoring: {e}")
            return {
                "success": False,
                "error": f"Failed to start monitoring: {str(e)}",
                "user": self.user.username
            }
    
    def stop_order_monitoring(self) -> dict:
        """Stop automatic order monitoring for this user"""
        try:
            print(f"[INFO] User {self.user.username} - Stopping order monitoring...")
            
            self.live_order_service.stop_order_monitoring()
            
            return {
                "success": True,
                "message": "Order monitoring stopped successfully",
                "monitoring_active": False,
                "user": self.user.username
            }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to stop monitoring: {e}")
            return {
                "success": False,
                "error": f"Failed to stop monitoring: {str(e)}",
                "user": self.user.username
            }
    
    def update_order_status_from_zerodha(self, zerodha_order_id: str = None) -> dict:
        """Manually update order status from Zerodha API"""
        try:
            print(f"[INFO] User {self.user.username} - Updating order status from Zerodha...")
            
            if zerodha_order_id:
                # Update specific order
                result = self.live_order_service.update_order_status(zerodha_order_id)
                return {
                    "success": result.get('success', False),
                    "message": f"Updated status for order {zerodha_order_id}",
                    "result": result,
                    "user": self.user.username
                }
            else:
                # Update all orders with Zerodha order IDs (including retry history)
                updated_count = 0
                total_checked = 0
                
                # Get all orders with retry history
                orders = self._load_orders()
                zerodha_orders_to_check = []
                
                for order in orders:
                    # Check main order for Zerodha order ID
                    if order.get('zerodha_order_id'):
                        zerodha_orders_to_check.append({
                            'zerodha_order_id': order['zerodha_order_id'],
                            'status': order.get('status'),
                            'order_type': 'main',
                            'order_id': order.get('order_id')
                        })
                    
                    # Check retry history for Zerodha order IDs
                    retry_history = order.get('retry_history', [])
                    for retry in retry_history:
                        if retry.get('zerodha_order_id'):
                            zerodha_orders_to_check.append({
                                'zerodha_order_id': retry['zerodha_order_id'],
                                'status': retry.get('status'),
                                'order_type': 'retry',
                                'order_id': order.get('order_id'),
                                'retry_number': retry.get('retry_number')
                            })
                
                print(f"[INFO] User {self.user.username} - Found {len(zerodha_orders_to_check)} orders with Zerodha IDs to check")
                
                # Update each order with Zerodha order ID
                for order_info in zerodha_orders_to_check:
                    zerodha_id = order_info['zerodha_order_id']
                    current_status = order_info['status']
                    
                    # Skip if already in final state
                    if current_status in ['COMPLETE', 'CANCELLED', 'REJECTED', 'FAILED_TO_PLACE']:
                        print(f"[DEBUG] User {self.user.username} - Skipping order {zerodha_id} with final status: {current_status}")
                        continue
                    
                    total_checked += 1
                    print(f"[DEBUG] User {self.user.username} - Checking status for Zerodha order {zerodha_id} (current: {current_status})")
                    
                    # Call Zerodha API to get current status
                    result = self.live_order_service.update_order_status(zerodha_id)
                    if result.get('success'):
                        # Also update the system orders file with the new status
                        new_status = result.get('order_details', {}).get('status')
                        if new_status:
                            self._update_system_order_status(order_info, new_status)
                        
                        updated_count += 1
                        print(f"[INFO] User {self.user.username} - Updated order {zerodha_id} successfully to status: {new_status}")
                    else:
                        print(f"[WARNING] User {self.user.username} - Failed to update order {zerodha_id}: {result.get('message', 'Unknown error')}")
                
                return {
                    "success": True,
                    "message": f"Updated {updated_count} orders from Zerodha",
                    "updated_count": updated_count,
                    "total_checked": total_checked,
                    "user": self.user.username
                }
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to update order status: {e}")
            return {
                "success": False,
                "error": f"Failed to update order status: {str(e)}",
                "user": self.user.username
            }
    
    def _update_system_order_status(self, order_info: dict, new_status: str) -> None:
        """Update the system orders file with new status from Zerodha"""
        try:
            orders = self._load_orders()
            
            for order in orders:
                if order_info['order_type'] == 'main' and order.get('order_id') == order_info['order_id']:
                    # Update main order status
                    old_status = order.get('status')
                    order['status'] = new_status
                    print(f"[DEBUG] User {self.user.username} - Updated main order {order_info['order_id']} status: {old_status} -> {new_status}")
                    
                elif order_info['order_type'] == 'retry' and order.get('order_id') == order_info['order_id']:
                    # Update retry history status
                    retry_history = order.get('retry_history', [])
                    for retry in retry_history:
                        if (retry.get('zerodha_order_id') == order_info['zerodha_order_id'] and 
                            retry.get('retry_number') == order_info['retry_number']):
                            old_status = retry.get('status')
                            retry['status'] = new_status
                            print(f"[DEBUG] User {self.user.username} - Updated retry #{order_info['retry_number']} status: {old_status} -> {new_status}")
                            
                            # Update main order status with latest retry status
                            order['status'] = new_status
                            print(f"[DEBUG] User {self.user.username} - Updated main order {order_info['order_id']} to match retry status: {new_status}")
                            break
            
            # Save updated orders
            self._save_orders(orders)
            print(f"[INFO] User {self.user.username} - System orders file updated with new status: {new_status}")
            
        except Exception as e:
            print(f"[ERROR] User {self.user.username} - Failed to update system order status: {e}")


# Manager for user-specific investment services
class InvestmentServiceManager:
    """Manages investment service instances for multiple users"""
    
    def __init__(self):
        self._user_services: Dict[str, MultiUserInvestmentService] = {}
    
    def get_user_service(self, user: UserDB, zerodha_auth: MultiUserZerodhaAuth) -> MultiUserInvestmentService:
        """Get or create user-specific investment service instance"""
        if user.id not in self._user_services:
            self._user_services[user.id] = MultiUserInvestmentService(user, zerodha_auth)
        return self._user_services[user.id]
    
    def remove_user_service(self, user_id: str) -> None:
        """Remove user service instance (e.g., on logout)"""
        if user_id in self._user_services:
            del self._user_services[user_id]

# Global investment service manager
investment_service_manager = InvestmentServiceManager()