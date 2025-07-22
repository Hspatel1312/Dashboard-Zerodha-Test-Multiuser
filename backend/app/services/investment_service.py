# backend/app/services/investment_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import math
from .csv_service import CSVService
from .investment_calculator import InvestmentCalculator
from .portfolio_construction_service import PortfolioConstructionService
from .portfolio_metrics_service import PortfolioMetricsService

class InvestmentService:
    def __init__(self, zerodha_auth):
        self.zerodha_auth = zerodha_auth
        self.csv_service = CSVService(zerodha_auth)
        self.calculator = InvestmentCalculator()
        self.portfolio_constructor = PortfolioConstructionService()
        self.metrics_calculator = PortfolioMetricsService()
        
        # File paths for storing system state
        self.orders_file = "system_orders.json"
        self.portfolio_state_file = "system_portfolio_state.json"
        self.csv_history_file = "csv_history.json"
    
    def get_investment_requirements(self) -> Dict:
        """Get minimum investment requirements based on current CSV - STRICT NO FAKE DATA"""
        try:
            print("📋 Getting investment requirements...")
            
            # Validate Zerodha connection first
            if not self.zerodha_auth:
                raise Exception("Zerodha authentication service not available. Please configure your Zerodha API credentials.")
            
            if not self.zerodha_auth.is_authenticated():
                print("🔄 Attempting Zerodha authentication...")
                try:
                    self.zerodha_auth.authenticate()
                except Exception as e:
                    raise Exception(f"Unable to authenticate with Zerodha: {str(e)}. Please check your API credentials and network connection.")
            
            if not self.zerodha_auth.is_authenticated():
                raise Exception("Zerodha authentication failed. Cannot proceed without live market data connection.")
            
            # Get stocks with LIVE prices only - no fake data allowed
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                raise Exception(f"Unable to fetch live stock prices: {str(e)}. This could be due to:\n1. Market being closed (9:15 AM - 3:30 PM IST)\n2. Network connectivity issues\n3. Zerodha API rate limits\n4. Invalid stock symbols in CSV")
            
            # Validate that we have real data
            if not stocks_data.get('price_data_status', {}).get('live_prices_used', False):
                raise Exception("Live prices not available. Cannot proceed with investment calculations using outdated data.")
            
            if stocks_data.get('total_stocks', 0) == 0:
                raise Exception("No valid stocks with live prices found. Please check:\n1. CSV file accessibility\n2. Stock symbols validity\n3. Market hours\n4. Zerodha connection")
            
            # Calculate minimum investment using live prices
            min_investment_info = self.calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            # Prepare response with validation
            requirements = {
                'is_first_time': self._is_first_time_setup(),
                'stocks_data': stocks_data,
                'minimum_investment': min_investment_info,
                'csv_info': stocks_data['csv_info'],
                'system_status': 'ready_for_initial_investment',
                'data_quality': {
                    'live_data_confirmed': True,
                    'zerodha_connected': True,
                    'price_success_rate': stocks_data['price_data_status']['success_rate'],
                    'total_valid_stocks': stocks_data['total_stocks'],
                    'data_source': stocks_data['price_data_status']['market_data_source']
                }
            }
            
            print(f"✅ Investment requirements prepared with LIVE data:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Price success rate: {stocks_data['price_data_status']['success_rate']:.1f}%")
            print(f"   Minimum investment: ₹{min_investment_info['minimum_investment']:,.0f}")
            print(f"   Recommended: ₹{min_investment_info['recommended_minimum']:,.0f}")
            
            return requirements
            
        except Exception as e:
            print(f"❌ Error getting investment requirements: {e}")
            # Re-raise with context - no fallback to fake data
            raise Exception(f"Cannot provide investment requirements: {str(e)}")
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan for given amount - LIVE DATA ONLY"""
        try:
            print(f"💰 Calculating initial investment plan for ₹{investment_amount:,.0f}")
            
            # Validate Zerodha connection
            if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
                raise Exception("Zerodha connection required for live price calculations. Please ensure you're connected.")
            
            # Get stocks with LIVE prices - will fail if not available
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                raise Exception(f"Cannot get live stock prices for investment calculation: {str(e)}")
            
            # Validate data quality
            if not stocks_data.get('price_data_status', {}).get('live_prices_used', False):
                raise Exception("Live market data not available. Cannot calculate investment plan with stale data.")
            
            if stocks_data.get('price_data_status', {}).get('success_rate', 0) < 50:
                success_rate = stocks_data['price_data_status']['success_rate']
                raise Exception(f"Poor data quality (only {success_rate:.1f}% of stocks have live prices). Cannot proceed with investment calculation.")
            
            # Validate minimum investment using live prices
            min_investment_info = self.calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(
                    f"Investment amount ₹{investment_amount:,.0f} is below minimum required "
                    f"₹{min_investment_info['minimum_investment']:,.0f} based on current live market prices"
                )
            
            # Calculate optimal allocation using live prices
            allocation_plan = self.calculator.calculate_optimal_allocation(
                investment_amount, stocks_data['stocks']
            )
            
            # Generate order preview with live prices
            orders = []
            for allocation in allocation_plan['allocations']:
                if allocation['shares'] > 0:
                    orders.append({
                        'symbol': allocation['symbol'],
                        'action': 'BUY',
                        'shares': allocation['shares'],
                        'price': allocation['price'],  # Live price
                        'value': allocation['value'],
                        'allocation_percent': allocation['allocation_percent']
                    })
            
            investment_plan = {
                'investment_amount': investment_amount,
                'allocation_plan': allocation_plan,
                'orders': orders,
                'summary': {
                    'total_orders': len(orders),
                    'total_stocks': len([o for o in orders if o['shares'] > 0]),
                    'total_investment_value': sum(order['value'] for order in orders),
                    'remaining_cash': allocation_plan['remaining_cash'],
                    'utilization_percent': allocation_plan['utilization_percent']
                },
                'csv_info': stocks_data['csv_info'],
                'validation': allocation_plan['validation'],
                'data_quality': {
                    'live_prices_used': True,
                    'price_success_rate': stocks_data['price_data_status']['success_rate'],
                    'last_price_update': stocks_data['price_data_status']['last_updated'],
                    'market_data_source': stocks_data['price_data_status']['market_data_source']
                }
            }
            
            print(f"✅ Initial investment plan created using LIVE data:")
            print(f"   Orders: {len(orders)} BUY orders")
            print(f"   Investment: ₹{investment_plan['summary']['total_investment_value']:,.0f}")
            print(f"   Utilization: {investment_plan['summary']['utilization_percent']:.2f}%")
            print(f"   Price success rate: {stocks_data['price_data_status']['success_rate']:.1f}%")
            
            return investment_plan
            
        except Exception as e:
            print(f"❌ Error calculating investment plan: {e}")
            # Re-raise with context - no fallback to fake data
            raise Exception(f"Cannot calculate investment plan: {str(e)}")
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment (store orders with live price data)"""
        try:
            print(f"🚀 Executing initial investment...")
            
            # Validate that plan has live data
            if not investment_plan.get('data_quality', {}).get('live_prices_used', False):
                raise Exception("Cannot execute investment plan - live price data not confirmed")
            
            # Create system orders
            system_orders = []
            order_id = self._get_next_order_id()
            
            for order in investment_plan['orders']:
                system_order = {
                    'order_id': order_id,
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order['price'],  # Live price at time of calculation
                    'value': order['value'],
                    'allocation_percent': order['allocation_percent'],
                    'status': 'EXECUTED_SYSTEM',  # Not placed on Zerodha yet
                    'execution_time': datetime.now().isoformat(),
                    'session_type': 'INITIAL_INVESTMENT',
                    'data_source': 'LIVE_ZERODHA_PRICES',
                    'price_timestamp': investment_plan.get('data_quality', {}).get('last_price_update')
                }
                system_orders.append(system_order)
                order_id += 1
            
            # Save orders
            self._save_system_orders(system_orders)
            
            # Update portfolio state
            self._update_portfolio_state(system_orders, investment_plan['csv_info'])
            
            # Save CSV snapshot
            self._save_csv_snapshot(investment_plan['csv_info'])
            
            execution_result = {
                'success': True,
                'orders_executed': len(system_orders),
                'total_investment': investment_plan['summary']['total_investment_value'],
                'remaining_cash': investment_plan['summary']['remaining_cash'],
                'portfolio_state': self._get_current_portfolio_state(),
                'execution_time': datetime.now().isoformat(),
                'data_quality': investment_plan['data_quality']
            }
            
            print(f"✅ Initial investment executed with live data:")
            print(f"   Orders stored: {len(system_orders)}")
            print(f"   Total investment: ₹{execution_result['total_investment']:,.0f}")
            print(f"   All prices were live market prices")
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Error executing initial investment: {e}")
            raise Exception(f"Failed to execute initial investment: {str(e)}")
    
    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed - requires live data"""
        try:
            print("🔍 Checking if rebalancing is needed...")
            
            # Get current system portfolio
            portfolio_state = self._get_current_portfolio_state()
            
            if not portfolio_state or not portfolio_state.get('holdings'):
                return {
                    'rebalancing_needed': False,
                    'reason': 'No system portfolio found - initial investment needed',
                    'is_first_time': True
                }
            
            # Validate Zerodha connection for live comparison
            if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
                raise Exception("Zerodha connection required to check current portfolio state and CSV changes")
            
            # Get current portfolio symbols
            current_symbols = list(portfolio_state['holdings'].keys())
            
            # Compare with CSV using live data
            try:
                comparison = self.csv_service.compare_csv_with_portfolio(current_symbols)
            except Exception as e:
                raise Exception(f"Cannot compare portfolio with CSV: {str(e)}")
            
            if comparison['rebalancing_needed']:
                # Calculate current portfolio value using live prices
                try:
                    portfolio_value = self._calculate_current_portfolio_value(portfolio_state)
                except Exception as e:
                    raise Exception(f"Cannot calculate current portfolio value with live prices: {str(e)}")
                
                rebalancing_info = {
                    'rebalancing_needed': True,
                    'reason': 'CSV stocks differ from current portfolio',
                    'comparison': comparison,
                    'current_portfolio_value': portfolio_value,
                    'portfolio_state': portfolio_state,
                    'is_first_time': False,
                    'live_data_confirmed': True
                }
                
                print(f"🔄 Rebalancing needed!")
                print(f"   New stocks: {comparison['new_stocks']}")
                print(f"   Removed stocks: {comparison['removed_stocks']}")
                print(f"   Current portfolio value: ₹{portfolio_value:,.0f}")
                
                return rebalancing_info
            else:
                print(f"✅ No rebalancing needed - portfolio matches CSV")
                return {
                    'rebalancing_needed': False,
                    'reason': 'Portfolio matches current CSV',
                    'comparison': comparison,
                    'is_first_time': False,
                    'live_data_confirmed': True
                }
            
        except Exception as e:
            print(f"❌ Error checking rebalancing: {e}")
            raise Exception(f"Failed to check rebalancing requirements: {str(e)}")
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0) -> Dict:
        """Calculate rebalancing plan with live data only"""
        try:
            print(f"🧮 Calculating rebalancing plan with additional investment: ₹{additional_investment:,.0f}")
            
            # Validate Zerodha connection
            if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
                raise Exception("Zerodha connection required for live price-based rebalancing calculations")
            
            # Get current portfolio state
            portfolio_state = self._get_current_portfolio_state()
            if not portfolio_state:
                raise Exception("No current portfolio found")
            
            # Get new CSV stocks with live prices
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                raise Exception(f"Cannot get live stock prices for rebalancing: {str(e)}")
            
            # Validate live data
            if not stocks_data.get('price_data_status', {}).get('live_prices_used', False):
                raise Exception("Live market data not available for rebalancing calculations")
            
            # Calculate current portfolio value using live prices
            try:
                current_value = self._calculate_current_portfolio_value(portfolio_state)
            except Exception as e:
                raise Exception(f"Cannot calculate current portfolio value: {str(e)}")
            
            # Total value to allocate = current value + additional investment
            total_value = current_value + additional_investment
            
            # Calculate target allocation (equal weight)
            target_per_stock = total_value / len(stocks_data['stocks'])
            
            # Generate rebalancing orders using live prices
            orders = []
            for stock in stocks_data['stocks']:
                symbol = stock['symbol']
                current_price = stock['price']  # Live price
                
                # Current holding
                current_holding = portfolio_state['holdings'].get(symbol, {})
                current_shares = current_holding.get('shares', 0)
                current_stock_value = current_shares * current_price
                
                # Target shares
                target_shares = int(target_per_stock / current_price)
                target_value = target_shares * current_price
                
                # Calculate difference
                shares_difference = target_shares - current_shares
                value_difference = target_value - current_stock_value
                
                if shares_difference != 0:
                    order = {
                        'symbol': symbol,
                        'action': 'BUY' if shares_difference > 0 else 'SELL',
                        'shares': abs(shares_difference),
                        'price': current_price,  # Live price
                        'value': abs(value_difference),
                        'current_shares': current_shares,
                        'target_shares': target_shares,
                        'allocation_percent': (target_value / total_value) * 100
                    }
                    orders.append(order)
            
            # Calculate plan summary
            buy_orders = [o for o in orders if o['action'] == 'BUY']
            sell_orders = [o for o in orders if o['action'] == 'SELL']
            
            cash_required = sum(o['value'] for o in buy_orders)
            cash_generated = sum(o['value'] for o in sell_orders)
            net_cash_required = cash_required - cash_generated
            
            rebalancing_plan = {
                'current_value': current_value,
                'additional_investment': additional_investment,
                'target_value': total_value,
                'orders': orders,
                'summary': {
                    'total_orders': len(orders),
                    'buy_orders': len(buy_orders),
                    'sell_orders': len(sell_orders),
                    'cash_required': cash_required,
                    'cash_generated': cash_generated,
                    'net_cash_required': net_cash_required,
                    'additional_investment': additional_investment
                },
                'csv_info': stocks_data['csv_info'],
                'status': 'READY_FOR_EXECUTION' if net_cash_required <= additional_investment else 'INSUFFICIENT_CASH',
                'data_quality': {
                    'live_prices_used': True,
                    'price_success_rate': stocks_data['price_data_status']['success_rate'],
                    'market_data_source': stocks_data['price_data_status']['market_data_source']
                }
            }
            
            print(f"✅ Rebalancing plan calculated using live data:")
            print(f"   Orders: {len(orders)} total ({len(buy_orders)} BUY, {len(sell_orders)} SELL)")
            print(f"   Net cash required: ₹{net_cash_required:,.0f}")
            print(f"   Status: {rebalancing_plan['status']}")
            print(f"   Price success rate: {stocks_data['price_data_status']['success_rate']:.1f}%")
            
            return rebalancing_plan
            
        except Exception as e:
            print(f"❌ Error calculating rebalancing plan: {e}")
            raise Exception(f"Failed to calculate rebalancing plan: {str(e)}")
    
    def execute_rebalancing(self, rebalancing_plan: Dict) -> Dict:
        """Execute rebalancing plan with live data validation"""
        try:
            print(f"🚀 Executing rebalancing plan...")
            
            # Validate live data in plan
            if not rebalancing_plan.get('data_quality', {}).get('live_prices_used', False):
                raise Exception("Cannot execute rebalancing plan - live price data not confirmed")
            
            # Create system orders
            system_orders = []
            order_id = self._get_next_order_id()
            
            for order in rebalancing_plan['orders']:
                system_order = {
                    'order_id': order_id,
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order['price'],  # Live price
                    'value': order['value'],
                    'allocation_percent': order['allocation_percent'],
                    'status': 'EXECUTED_SYSTEM',
                    'execution_time': datetime.now().isoformat(),
                    'session_type': 'REBALANCING',
                    'data_source': 'LIVE_ZERODHA_PRICES'
                }
                system_orders.append(system_order)
                order_id += 1
            
            # Save orders
            self._save_system_orders(system_orders)
            
            # Update portfolio state
            self._update_portfolio_state(system_orders, rebalancing_plan['csv_info'])
            
            # Save CSV snapshot
            self._save_csv_snapshot(rebalancing_plan['csv_info'])
            
            execution_result = {
                'success': True,
                'orders_executed': len(system_orders),
                'total_investment': rebalancing_plan['summary']['cash_required'],
                'cash_generated': rebalancing_plan['summary']['cash_generated'],
                'net_investment': rebalancing_plan['summary']['net_cash_required'],
                'execution_time': datetime.now().isoformat(),
                'data_quality': rebalancing_plan['data_quality']
            }
            
            print(f"✅ Rebalancing executed with live data:")
            print(f"   Orders stored: {len(system_orders)}")
            print(f"   Net investment: ₹{execution_result['net_investment']:,.0f}")
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Error executing rebalancing: {e}")
            raise Exception(f"Failed to execute rebalancing: {str(e)}")
    
    def get_system_portfolio_status(self) -> Dict:
        """Get comprehensive system portfolio status - LIVE DATA ONLY"""
        try:
            print("📊 Getting comprehensive system portfolio status...")
            
            # Load all system orders
            all_orders = self._load_system_orders()
            
            if not all_orders:
                return {
                    'status': 'empty',
                    'message': 'No orders found. Please complete initial investment.',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                    'performance_metrics': {},
                    'allocation_analysis': {},
                    'timeline': {}
                }
            
            # Validate Zerodha connection for live calculations
            if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
                return {
                    'status': 'error',
                    'error': 'Zerodha connection required for live portfolio status',
                    'message': 'Please ensure Zerodha is connected to get current portfolio status',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                    'performance_metrics': {},
                    'allocation_analysis': {},
                    'timeline': {}
                }
            
            # Step 1: Construct portfolio from orders
            print("🔧 Step 1: Constructing portfolio from orders...")
            portfolio_construction = self.portfolio_constructor.construct_portfolio_from_orders(all_orders)
            
            # Validate construction
            validation = self.portfolio_constructor.validate_portfolio_construction(portfolio_construction)
            if not validation['is_valid']:
                print(f"⚠️ Portfolio construction validation failed: {validation['errors']}")
            
            if not portfolio_construction['holdings']:
                return {
                    'status': 'empty',
                    'message': 'No current holdings after processing all orders.',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                    'performance_metrics': {},
                    'allocation_analysis': {},
                    'timeline': {}
                }
            
            # Step 2: Get current live prices for all portfolio stocks
            print("🔧 Step 2: Getting live market prices...")
            holdings = portfolio_construction['holdings']
            symbols = list(holdings.keys())
            
            try:
                current_prices = self.csv_service.get_live_prices(symbols)
                print(f"   ✅ Got live prices for {len(current_prices)}/{len(symbols)} stocks")
                
                # Validate we got prices for all holdings
                missing_prices = [symbol for symbol in symbols if symbol not in current_prices]
                if missing_prices:
                    raise Exception(f"Missing live prices for {len(missing_prices)} stocks: {missing_prices[:3]}{'...' if len(missing_prices) > 3 else ''}. Cannot calculate accurate portfolio status.")
                        
            except Exception as e:
                print(f"❌ Could not get live prices: {e}")
                return {
                    'status': 'error',
                    'error': f'Live price data not available: {str(e)}',
                    'message': 'Cannot calculate portfolio status without current market prices',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                    'performance_metrics': {},
                    'allocation_analysis': {},
                    'timeline': {}
                }
            
            # Step 3: Calculate comprehensive metrics using live prices
            print("🔧 Step 3: Calculating comprehensive metrics with live data...")
            try:
                portfolio_metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                    holdings, current_prices, portfolio_construction
                )
            except Exception as e:
                print(f"❌ Error calculating metrics: {e}")
                return {
                    'status': 'error',
                    'error': f'Metrics calculation failed: {str(e)}',
                    'message': 'Could not calculate portfolio metrics',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                    'performance_metrics': {},
                    'allocation_analysis': {},
                    'timeline': {}
                }
            
            # Step 4: Format response for frontend with live data confirmation
            status_info = {
                'status': 'active',
                'holdings': portfolio_metrics['holdings_with_metrics'],
                'portfolio_summary': {
                    'total_investment': portfolio_metrics['total_investment'],
                    'current_value': portfolio_metrics['current_value'],
                    'total_returns': portfolio_metrics['total_returns'],
                    'returns_percentage': portfolio_metrics['returns_percentage'],
                    'cagr': portfolio_metrics['cagr'],
                    'stock_count': len(portfolio_metrics['holdings_with_metrics']),
                    'investment_period_days': portfolio_metrics['investment_period_days'],
                    'investment_period_years': portfolio_metrics['investment_period_years']
                },
                'performance_metrics': {
                    'best_performer': portfolio_metrics['best_performer'],
                    'worst_performer': portfolio_metrics['worst_performer'],
                    'avg_return': portfolio_metrics['avg_return'],
                    'volatility_score': portfolio_metrics['volatility_score'],
                    'sharpe_ratio': portfolio_metrics['sharpe_ratio']
                },
                'allocation_analysis': {
                    'allocation_stats': portfolio_metrics['allocation_stats'],
                    'rebalancing_needed': portfolio_metrics['rebalancing_needed'],
                    'allocation_deviation': portfolio_metrics['allocation_deviation']
                },
                'timeline': {
                    'first_investment': portfolio_construction['first_order_date'],
                    'last_investment': portfolio_construction['last_order_date'],
                    'total_orders': len(all_orders),
                    'last_updated': datetime.now().isoformat()
                },
                'data_quality': {
                    'live_prices_confirmed': True,
                    'zerodha_connected': True,
                    'price_data_timestamp': datetime.now().isoformat(),
                    'all_holdings_priced': len(current_prices) == len(symbols)
                },
                'validation': validation
            }
            
            print(f"✅ Comprehensive portfolio status calculated with LIVE data:")
            print(f"   Holdings: {len(portfolio_metrics['holdings_with_metrics'])}")
            print(f"   Total investment: ₹{portfolio_metrics['total_investment']:,.2f}")
            print(f"   Current value: ₹{portfolio_metrics['current_value']:,.2f}")
            print(f"   CAGR: {portfolio_metrics['cagr']:.2f}%")
            print(f"   All prices are live from Zerodha")
            
            return status_info
            
        except Exception as e:
            print(f"❌ Error getting portfolio status: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to get portfolio status',
                'holdings': {},
                'portfolio_summary': {'total_investment': 0, 'current_value': 0},
                'performance_metrics': {},
                'allocation_analysis': {},
                'timeline': {}
            }
    
    # Helper methods (keep all existing helper methods)
    def _is_first_time_setup(self) -> bool:
        """Check if this is first time setup"""
        return not os.path.exists(self.portfolio_state_file)
    
    def _get_next_order_id(self) -> int:
        """Get next order ID"""
        orders = self._load_system_orders()
        if not orders:
            return 1
        return max(order['order_id'] for order in orders) + 1
    
    def _save_system_orders(self, new_orders: List[Dict]):
        """Save system orders to file"""
        existing_orders = self._load_system_orders()
        all_orders = existing_orders + new_orders
        
        with open(self.orders_file, 'w') as f:
            json.dump(all_orders, f, indent=2)
    
    def _load_system_orders(self) -> List[Dict]:
        """Load system orders from file"""
        if not os.path.exists(self.orders_file):
            return []
        
        try:
            with open(self.orders_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _update_portfolio_state(self, orders: List[Dict], csv_info: Dict):
        """Update portfolio state after investment"""
        holdings = {}
        
        for order in orders:
            if order['action'] == 'BUY':
                holdings[order['symbol']] = {
                    'shares': order['shares'],
                    'avg_price': order['price'],
                    'total_investment': order['value']
                }
        
        portfolio_state = {
            'holdings': holdings,
            'last_updated': datetime.now().isoformat(),
            'csv_info': csv_info,
            'type': 'INITIAL_INVESTMENT' if orders[0].get('session_type') == 'INITIAL_INVESTMENT' else 'REBALANCING'
        }
        
        with open(self.portfolio_state_file, 'w') as f:
            json.dump(portfolio_state, f, indent=2)
    
    def _get_current_portfolio_state(self) -> Optional[Dict]:
        """Get current portfolio state"""
        if not os.path.exists(self.portfolio_state_file):
            return None
        
        try:
            with open(self.portfolio_state_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _calculate_current_portfolio_value(self, portfolio_state: Dict) -> float:
        """Calculate current value of portfolio using live prices ONLY"""
        if not portfolio_state or not portfolio_state.get('holdings'):
            return 0.0
        
        holdings = portfolio_state['holdings']
        symbols = list(holdings.keys())
        
        # Get live prices - will raise exception if not available
        try:
            current_prices = self.csv_service.get_live_prices(symbols)
            total_value = 0.0
            
            for symbol, holding in holdings.items():
                if symbol in current_prices:
                    current_value = holding['shares'] * current_prices[symbol]
                    total_value += current_value
                else:
                    raise Exception(f"Live price not available for {symbol}")
            
            return total_value
        except Exception as e:
            raise Exception(f"Cannot calculate portfolio value without live prices: {str(e)}")
    
    def _save_csv_snapshot(self, csv_info: Dict):
        """Save CSV snapshot for history tracking"""
        history = self._load_csv_history()
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'csv_hash': csv_info['csv_hash'],
            'fetch_time': csv_info['fetch_time']
        }
        
        history.append(snapshot)
        
        # Keep only last 50 snapshots
        if len(history) > 50:
            history = history[-50:]
        
        with open(self.csv_history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_csv_history(self) -> List[Dict]:
        """Load CSV history"""
        if not os.path.exists(self.csv_history_file):
            return []
        
        try:
            with open(self.csv_history_file, 'r') as f:
                return json.load(f)
        except:
            return []