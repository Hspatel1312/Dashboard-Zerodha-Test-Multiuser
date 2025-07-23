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
        self.investment_calculator = InvestmentCalculator()
        self.portfolio_construction = PortfolioConstructionService()
        self.portfolio_metrics = PortfolioMetricsService()
        
        # File paths for storing system state
        self.orders_file = "system_orders.json"
        self.portfolio_state_file = "system_portfolio_state.json"
        self.csv_history_file = "csv_history.json"
        
        # Configuration
        self.min_investment = 200000
        self.target_allocation = 5.0
        self.min_allocation = 4.0
        self.max_allocation = 7.0
        self.rebalancing_threshold = 10000
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories and files exist"""
        try:
            for file_path in [self.orders_file, self.portfolio_state_file, self.csv_history_file]:
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning: Could not create directories: {e}")
    
    def get_investment_requirements(self) -> Dict:
        """Get minimum investment requirements based on current CSV"""
        try:
            print("📋 Getting investment requirements...")
            
            # Validate Zerodha connection first
            if not self.zerodha_auth:
                print("⚠️ Zerodha authentication service not available, proceeding with fallback data")
            else:
                auth_status = self.zerodha_auth.get_auth_status()
                if not auth_status['authenticated']:
                    print("🔄 Attempting Zerodha authentication...")
                    try:
                        self.zerodha_auth.authenticate()
                    except Exception as e:
                        print(f"⚠️ Zerodha authentication failed, using fallback data: {str(e)}")
            
            # Get stocks with prices (will use fallback if Zerodha fails)
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                print(f"❌ Failed to get stocks with prices: {e}")
                raise Exception(f"Unable to fetch stock data: {str(e)}")
            
            # Validate that we have data
            if stocks_data.get('total_stocks', 0) == 0:
                raise Exception("No valid stocks found with price data")
            
            # Calculate minimum investment
            try:
                min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            except Exception as e:
                print(f"❌ Failed to calculate minimum investment: {e}")
                raise Exception(f"Unable to calculate investment requirements: {str(e)}")
            
            requirements = {
                'is_first_time': self._is_first_time_setup(),
                'stocks_data': stocks_data,
                'minimum_investment': min_investment_info,
                'csv_info': stocks_data['csv_info'],
                'system_status': 'ready_for_initial_investment',
                'data_quality': {
                    'live_data_available': stocks_data['price_data_status']['live_prices_used'],
                    'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()),
                    'price_success_rate': stocks_data['price_data_status']['success_rate'],
                    'total_valid_stocks': stocks_data['total_stocks'],
                    'data_source': stocks_data['price_data_status']['market_data_source']
                }
            }
            
            print(f"✅ Investment requirements prepared:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Min investment: ₹{min_investment_info['minimum_investment']:,.0f}")
            print(f"   Data source: {stocks_data['price_data_status']['market_data_source']}")
            
            return requirements
            
        except Exception as e:
            print(f"❌ Error getting investment requirements: {e}")
            raise Exception(f"Cannot provide investment requirements: {str(e)}")
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan"""
        try:
            print(f"💰 Calculating investment plan for ₹{investment_amount:,.0f}")
            
            # Get stocks with prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Validate minimum investment
            min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(f"Investment amount ₹{investment_amount:,.0f} is below minimum required ₹{min_investment_info['minimum_investment']:,.0f}")
            
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
                'summary': {
                    'total_orders': len(orders),
                    'total_stocks': len([o for o in orders if o['shares'] > 0]),
                    'total_investment_value': allocation_result['total_allocated'],
                    'remaining_cash': allocation_result['remaining_cash'],
                    'utilization_percent': allocation_result['utilization_percent']
                },
                'csv_info': stocks_data['csv_info'],
                'data_quality': stocks_data['price_data_status'],
                'validation': allocation_result['validation']
            }
            
            print(f"✅ Investment plan created: {len(orders)} orders")
            print(f"   Total allocated: ₹{allocation_result['total_allocated']:,.0f}")
            print(f"   Utilization: {allocation_result['utilization_percent']:.1f}%")
            print(f"   Stocks in range: {allocation_result['validation']['stocks_in_range']}/{len(orders)}")
            
            return plan
            
        except Exception as e:
            print(f"❌ Error calculating investment plan: {e}")
            raise Exception(f"Cannot calculate investment plan: {str(e)}")
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment plan"""
        try:
            print("🚀 Executing initial investment...")
            
            # Create system orders
            system_orders = []
            order_id = self._get_next_order_id()
            execution_time = datetime.now().isoformat()
            
            for order in investment_plan['orders']:
                system_order = {
                    'order_id': order_id,
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order['price'],
                    'value': order['value'],
                    'allocation_percent': order['allocation_percent'],
                    'status': 'EXECUTED_SYSTEM',
                    'execution_time': execution_time,
                    'session_type': 'INITIAL_INVESTMENT'
                }
                system_orders.append(system_order)
                order_id += 1
            
            # Save orders
            self._save_system_orders(system_orders)
            
            # Update portfolio state
            self._update_portfolio_state(system_orders, investment_plan.get('csv_info', {}))
            
            # Update CSV history
            self._update_csv_history(investment_plan.get('csv_info', {}))
            
            result = {
                'success': True,
                'orders_executed': len(system_orders),
                'total_investment': investment_plan['summary']['total_investment_value'],
                'remaining_cash': investment_plan['summary']['remaining_cash'],
                'execution_time': execution_time,
                'utilization_percent': investment_plan['summary']['utilization_percent']
            }
            
            print(f"✅ Initial investment executed: {len(system_orders)} orders")
            print(f"   Total investment: ₹{investment_plan['summary']['total_investment_value']:,.0f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error executing initial investment: {e}")
            raise Exception(f"Failed to execute initial investment: {str(e)}")
    
    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed"""
        try:
            portfolio_state = self._get_current_portfolio_state()
            
            if not portfolio_state or not portfolio_state.get('holdings'):
                return {
                    'rebalancing_needed': False,
                    'reason': 'No system portfolio found - initial investment needed',
                    'is_first_time': True
                }
            
            # Compare with current CSV
            current_symbols = set(portfolio_state['holdings'].keys())
            
            try:
                csv_data = self.csv_service.fetch_csv_data()
                csv_symbols = set(csv_data['symbols'])
            except Exception as e:
                print(f"⚠️ Could not fetch current CSV: {e}")
                return {
                    'rebalancing_needed': False,
                    'reason': 'Cannot fetch current CSV data',
                    'is_first_time': False,
                    'error': str(e)
                }
            
            new_stocks = csv_symbols - current_symbols
            removed_stocks = current_symbols - csv_symbols
            
            rebalancing_needed = len(new_stocks) > 0 or len(removed_stocks) > 0
            
            if rebalancing_needed:
                return {
                    'rebalancing_needed': True,
                    'reason': 'CSV stocks differ from current portfolio',
                    'new_stocks': list(new_stocks),
                    'removed_stocks': list(removed_stocks),
                    'is_first_time': False
                }
            else:
                return {
                    'rebalancing_needed': False,
                    'reason': 'Portfolio matches current CSV',
                    'is_first_time': False
                }
            
        except Exception as e:
            print(f"❌ Error checking rebalancing: {e}")
            return {
                'rebalancing_needed': False,
                'reason': 'Error checking rebalancing status',
                'is_first_time': False,
                'error': str(e)
            }
    
    def get_system_portfolio_status(self) -> Dict:
        """Get system portfolio status with comprehensive metrics"""
        try:
            portfolio_state = self._get_current_portfolio_state()
            
            if not portfolio_state:
                return {
                    'status': 'empty',
                    'message': 'No portfolio found. Please complete initial investment.',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0}
                }
            
            # Get current prices for all holdings
            symbols = list(portfolio_state['holdings'].keys())
            
            try:
                current_prices = self.csv_service.get_live_prices(symbols)
            except Exception as e:
                print(f"⚠️ Could not get live prices, using fallback: {e}")
                current_prices = self.csv_service._get_fallback_prices(symbols)
            
            # Get all orders for portfolio construction
            all_orders = self._load_system_orders()
            
            # Construct portfolio from orders
            construction_result = self.portfolio_construction.construct_portfolio_from_orders(all_orders)
            
            # Calculate comprehensive metrics
            try:
                metrics = self.portfolio_metrics.calculate_comprehensive_metrics(
                    construction_result['holdings'],
                    current_prices,
                    construction_result
                )
                
                return {
                    'status': 'active',
                    'holdings': metrics['holdings_with_metrics'],
                    'portfolio_summary': {
                        'total_investment': float(metrics['total_investment']),
                        'current_value': float(metrics['current_value']),
                        'total_returns': float(metrics['total_returns']),
                        'returns_percentage': float(metrics['returns_percentage']),
                        'stock_count': len(metrics['holdings_with_metrics']),
                        'cagr': float(metrics['cagr']),
                        'investment_period_days': metrics['investment_period_days']
                    },
                    'performance_metrics': {
                        'best_performer': metrics['best_performer'],
                        'worst_performer': metrics['worst_performer'],
                        'volatility_score': float(metrics['volatility_score']),
                        'sharpe_ratio': float(metrics['sharpe_ratio'])
                    },
                    'allocation_analysis': {
                        'allocation_stats': metrics['allocation_stats'],
                        'rebalancing_needed': metrics['rebalancing_needed']
                    },
                    'data_quality': {
                        'price_source': 'Live' if any('zerodha' in str(current_prices).lower() for _ in [1]) else 'Fallback',
                        'construction_validation': construction_result.get('validation', {}),
                        'last_updated': datetime.now().isoformat()
                    }
                }
                
            except Exception as e:
                print(f"⚠️ Could not calculate advanced metrics: {e}")
                
                # Fallback to basic calculation
                holdings_with_metrics = {}
                total_investment = 0
                current_value = 0
                
                for symbol, holding in construction_result['holdings'].items():
                    shares = holding['total_shares']
                    avg_price = holding['avg_price']
                    investment_value = holding['total_investment']
                    current_price = current_prices.get(symbol, avg_price)
                    
                    holding_value = shares * current_price
                    pnl = holding_value - investment_value
                    pnl_percent = (pnl / investment_value) * 100 if investment_value > 0 else 0
                    
                    holdings_with_metrics[symbol] = {
                        'shares': shares,
                        'avg_price': avg_price,
                        'current_price': current_price,
                        'investment_value': investment_value,
                        'current_value': holding_value,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent
                    }
                    
                    total_investment += investment_value
                    current_value += holding_value
                
                total_returns = current_value - total_investment
                returns_percent = (total_returns / total_investment) * 100 if total_investment > 0 else 0
                
                return {
                    'status': 'active',
                    'holdings': holdings_with_metrics,
                    'portfolio_summary': {
                        'total_investment': total_investment,
                        'current_value': current_value,
                        'total_returns': total_returns,
                        'returns_percentage': returns_percent,
                        'stock_count': len(holdings_with_metrics)
                    }
                }
            
        except Exception as e:
            print(f"❌ Error getting portfolio status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'holdings': {},
                'portfolio_summary': {'total_investment': 0, 'current_value': 0}
            }
    
    # Helper methods
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
        try:
            existing_orders = self._load_system_orders()
            all_orders = existing_orders + new_orders
            
            with open(self.orders_file, 'w') as f:
                json.dump(all_orders, f, indent=2)
            
            print(f"💾 Saved {len(new_orders)} new orders (total: {len(all_orders)})")
        except Exception as e:
            print(f"❌ Error saving system orders: {e}")
            raise
    
    def _load_system_orders(self) -> List[Dict]:
        """Load system orders from file"""
        if not os.path.exists(self.orders_file):
            return []
        
        try:
            with open(self.orders_file, 'r') as f:
                orders = json.load(f)
            return orders if isinstance(orders, list) else []
        except Exception as e:
            print(f"⚠️ Error loading system orders: {e}")
            return []
    
    def _update_portfolio_state(self, orders: List[Dict], csv_info: Dict):
        """Update portfolio state based on orders"""
        try:
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
            
            print(f"💾 Portfolio state updated with {len(holdings)} holdings")
            
        except Exception as e:
            print(f"❌ Error updating portfolio state: {e}")
            raise
    
    def _get_current_portfolio_state(self) -> Optional[Dict]:
        """Get current portfolio state"""
        if not os.path.exists(self.portfolio_state_file):
            return None
        
        try:
            with open(self.portfolio_state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading portfolio state: {e}")
            return None
    
    def _update_csv_history(self, csv_info: Dict):
        """Update CSV history tracking"""
        try:
            history = []
            if os.path.exists(self.csv_history_file):
                with open(self.csv_history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new entry
            history.append({
                'timestamp': datetime.now().isoformat(),
                'csv_hash': csv_info.get('csv_hash', ''),
                'fetch_time': csv_info.get('fetch_time', '')
            })
            
            # Keep only last 100 entries
            history = history[-100:]
            
            with open(self.csv_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error updating CSV history: {e}")
    
    def get_service_status(self) -> Dict:
        """Get comprehensive service status"""
        return {
            'csv_service': {
                'available': bool(self.csv_service),
                'connection_status': self.csv_service.get_connection_status()
            },
            'zerodha_auth': {
                'available': bool(self.zerodha_auth),
                'status': self.zerodha_auth.get_auth_status() if self.zerodha_auth else {}
            },
            'files': {
                'orders_file_exists': os.path.exists(self.orders_file),
                'portfolio_state_exists': os.path.exists(self.portfolio_state_file),
                'csv_history_exists': os.path.exists(self.csv_history_file)
            },
            'portfolio': {
                'has_portfolio': bool(self._get_current_portfolio_state()),
                'total_orders': len(self._load_system_orders()),
                'is_first_time': self._is_first_time_setup()
            }
        }