# backend/app/services/investment_service.py - Updated to use separate services
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
    
    # ... (keep all existing methods: get_investment_requirements, calculate_initial_investment_plan, 
    # execute_initial_investment, check_rebalancing_needed, calculate_rebalancing_plan, execute_rebalancing)
    
    def get_investment_requirements(self) -> Dict:
        """Get minimum investment requirements based on current CSV"""
        try:
            print("📋 Getting investment requirements...")
            
            # Get stocks with live prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Calculate minimum investment
            min_investment_info = self.calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            # Prepare response
            requirements = {
                'is_first_time': self._is_first_time_setup(),
                'stocks_data': stocks_data,
                'minimum_investment': min_investment_info,
                'csv_info': stocks_data['csv_info'],
                'system_status': 'ready_for_initial_investment'
            }
            
            print(f"✅ Investment requirements prepared:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Minimum investment: ₹{min_investment_info['minimum_investment']:,.0f}")
            print(f"   Recommended: ₹{min_investment_info['recommended_minimum']:,.0f}")
            
            return requirements
            
        except Exception as e:
            print(f"❌ Error getting investment requirements: {e}")
            raise Exception(f"Failed to get investment requirements: {str(e)}")
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan for given amount"""
        try:
            print(f"💰 Calculating initial investment plan for ₹{investment_amount:,.0f}")
            
            # Get stocks with live prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Validate minimum investment
            min_investment_info = self.calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(
                    f"Investment amount ₹{investment_amount:,.0f} is below minimum required "
                    f"₹{min_investment_info['minimum_investment']:,.0f}"
                )
            
            # Calculate optimal allocation
            allocation_plan = self.calculator.calculate_optimal_allocation(
                investment_amount, stocks_data['stocks']
            )
            
            # Generate order preview
            orders = []
            for allocation in allocation_plan['allocations']:
                if allocation['shares'] > 0:
                    orders.append({
                        'symbol': allocation['symbol'],
                        'action': 'BUY',
                        'shares': allocation['shares'],
                        'price': allocation['price'],
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
                'validation': allocation_plan['validation']
            }
            
            print(f"✅ Initial investment plan created:")
            print(f"   Orders: {len(orders)} BUY orders")
            print(f"   Investment: ₹{investment_plan['summary']['total_investment_value']:,.0f}")
            print(f"   Utilization: {investment_plan['summary']['utilization_percent']:.2f}%")
            
            return investment_plan
            
        except Exception as e:
            print(f"❌ Error calculating investment plan: {e}")
            raise Exception(f"Failed to calculate investment plan: {str(e)}")
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment (store orders, don't place on Zerodha yet)"""
        try:
            print(f"🚀 Executing initial investment...")
            
            # Create system orders
            system_orders = []
            order_id = self._get_next_order_id()
            
            for order in investment_plan['orders']:
                system_order = {
                    'order_id': order_id,
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order['price'],
                    'value': order['value'],
                    'allocation_percent': order['allocation_percent'],
                    'status': 'EXECUTED_SYSTEM',  # Not placed on Zerodha
                    'execution_time': datetime.now().isoformat(),
                    'session_type': 'INITIAL_INVESTMENT'
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
                'execution_time': datetime.now().isoformat()
            }
            
            print(f"✅ Initial investment executed:")
            print(f"   Orders stored: {len(system_orders)}")
            print(f"   Total investment: ₹{execution_result['total_investment']:,.0f}")
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Error executing initial investment: {e}")
            raise Exception(f"Failed to execute initial investment: {str(e)}")
    
    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed by comparing current CSV with system portfolio"""
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
            
            # Get current portfolio symbols
            current_symbols = list(portfolio_state['holdings'].keys())
            
            # Compare with CSV
            comparison = self.csv_service.compare_csv_with_portfolio(current_symbols)
            
            if comparison['rebalancing_needed']:
                # Calculate current portfolio value
                portfolio_value = self._calculate_current_portfolio_value(portfolio_state)
                
                rebalancing_info = {
                    'rebalancing_needed': True,
                    'reason': 'CSV stocks differ from current portfolio',
                    'comparison': comparison,
                    'current_portfolio_value': portfolio_value,
                    'portfolio_state': portfolio_state,
                    'is_first_time': False
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
                    'is_first_time': False
                }
            
        except Exception as e:
            print(f"❌ Error checking rebalancing: {e}")
            raise Exception(f"Failed to check rebalancing: {str(e)}")
    
    def get_system_portfolio_status(self) -> Dict:
        """
        Get comprehensive system portfolio status with advanced metrics
        NOW USES SEPARATE SERVICES FOR CONSTRUCTION AND METRICS
        """
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
            
            # Step 1: Construct portfolio from orders using dedicated service
            print("🔧 Step 1: Constructing portfolio from orders...")
            portfolio_construction = self.portfolio_constructor.construct_portfolio_from_orders(all_orders)
            
            # Validate construction
            validation = self.portfolio_constructor.validate_portfolio_construction(portfolio_construction)
            if not validation['is_valid']:
                print(f"❌ Portfolio construction validation failed: {validation['errors']}")
                # Continue with warnings, but note the issues
            
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
            
            # Step 2: Get current prices for all portfolio stocks
            print("🔧 Step 2: Getting current market prices...")
            holdings = portfolio_construction['holdings']
            symbols = list(holdings.keys())
            
            try:
                current_prices = self.csv_service.get_live_prices(symbols)
                print(f"   ✅ Got prices for {len(current_prices)}/{len(symbols)} stocks")
            except Exception as e:
                print(f"⚠️ Could not get live prices: {e}, using average prices")
                current_prices = {symbol: holding['avg_price'] for symbol, holding in holdings.items()}
            
            # Step 3: Calculate comprehensive metrics using dedicated service
            print("🔧 Step 3: Calculating comprehensive metrics...")
            portfolio_metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                holdings, current_prices, portfolio_construction
            )
            
            # Step 4: Format response for frontend
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
                'validation': validation  # Include validation results for debugging
            }
            
            print(f"✅ Comprehensive portfolio status calculated:")
            print(f"   Holdings: {len(portfolio_metrics['holdings_with_metrics'])}")
            print(f"   Total investment: ₹{portfolio_metrics['total_investment']:,.2f}")
            print(f"   Current value: ₹{portfolio_metrics['current_value']:,.2f}")
            print(f"   CAGR: {portfolio_metrics['cagr']:.2f}%")
            print(f"   Investment period: {portfolio_metrics['investment_period_days']} days")
            
            return status_info
            
        except Exception as e:
            print(f"❌ Error getting portfolio status: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'error': str(e),
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
        """Update portfolio state after initial investment"""
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
            'type': 'INITIAL_INVESTMENT'
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
        """Calculate current value of portfolio using live prices"""
        if not portfolio_state or not portfolio_state.get('holdings'):
            return 0.0
        
        holdings = portfolio_state['holdings']
        symbols = list(holdings.keys())
        
        # Get current prices
        try:
            current_prices = self.csv_service.get_live_prices(symbols)
            total_value = 0.0
            
            for symbol, holding in holdings.items():
                if symbol in current_prices:
                    current_value = holding['shares'] * current_prices[symbol]
                    total_value += current_value
            
            return total_value
        except:
            # Fallback to investment value if can't get live prices
            return sum(holding['total_investment'] for holding in holdings.values())
    
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