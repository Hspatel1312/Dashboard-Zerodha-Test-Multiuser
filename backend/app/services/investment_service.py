# backend/app/services/investment_service.py - FIXED VERSION
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

class InvestmentService:
    def __init__(self, zerodha_auth):
        self.zerodha_auth = zerodha_auth
        self.csv_service = CSVService(zerodha_auth)
        self.investment_calculator = InvestmentCalculator()
        self.portfolio_construction = PortfolioConstructionService()
        self.portfolio_metrics = PortfolioMetricsService()
        
        # Import portfolio service here to avoid circular imports
        from .portfolio_service import PortfolioService
        self.portfolio_service = PortfolioService(zerodha_auth)
        self.portfolio_comparison = PortfolioComparisonService(self.portfolio_service, self)
        
        # File paths for storing system state
        self.orders_file = "system_orders.json"
        self.portfolio_state_file = "system_portfolio_state.json"
        self.csv_history_file = "csv_history.json"
        
        # Configuration - Updated for ±1.5% flexibility
        self.min_investment = 200000
        self.target_allocation = 5.0
        self.min_allocation = 3.5  # 5% - 1.5%
        self.max_allocation = 6.5  # 5% + 1.5%
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
            print(f"[WARNING] Warning: Could not create directories: {e}")
    
    def get_investment_requirements(self) -> Dict:
        """Get investment requirements for initial setup"""
        try:
            print("[INFO] Getting investment requirements...")
            
            # Get stocks with prices (will use fallback if Zerodha fails)
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                print(f"[ERROR] Failed to get stocks with prices: {e}")
                raise Exception(f"Unable to fetch stock data: {str(e)}")
            
            # Check if we got an error response (no live prices available)
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print("[ERROR] PRICE_DATA_UNAVAILABLE - returning error response")
                
                # Return structured error response
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data unavailable'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'price_data_status': stocks_data.get('price_data_status', {}),
                    'data_quality': {
                        'live_data_available': False,
                        'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()) if self.zerodha_auth else False,
                        'error_reason': stocks_data.get('error_message', 'Live price data unavailable'),
                        'solution': 'Ensure Zerodha is connected and authenticated, then retry'
                    }
                }
            
            # Validate that we have data
            if stocks_data.get('total_stocks', 0) == 0:
                raise Exception("No valid stocks found with price data")
            
            # Calculate minimum investment
            try:
                min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            except Exception as e:
                print(f"[ERROR] Failed to calculate minimum investment: {e}")
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
            
            print(f"[SUCCESS] Investment requirements prepared:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Min investment: Rs.{min_investment_info['minimum_investment']:,.0f}")
            print(f"   Data source: {stocks_data['price_data_status']['market_data_source']}")
            
            return requirements
            
        except Exception as e:
            print(f"[ERROR] Error getting investment requirements: {e}")
            
            # Check if it's a price data error
            if "PRICE_DATA_UNAVAILABLE" in str(e):
                # Try to get CSV info even if prices failed
                try:
                    csv_data = self.csv_service.fetch_csv_data(force_refresh=False)
                    csv_info = {
                        'fetch_time': csv_data['fetch_time'],
                        'csv_hash': csv_data['csv_hash'],
                        'source_url': csv_data['source_url'],
                        'total_symbols': len(csv_data['symbols'])
                    }
                except:
                    csv_info = {}
                
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': str(e),
                    'csv_info': csv_info,
                    'data_quality': {
                        'live_data_available': False,
                        'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()) if self.zerodha_auth else False,
                        'error_reason': str(e),
                        'solution': 'Ensure Zerodha is connected and authenticated, then retry'
                    }
                }
            
            raise Exception(f"Cannot provide investment requirements: {str(e)}")
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan"""
        try:
            print(f"[INFO] Calculating investment plan for Rs.{investment_amount:,.0f}")
            
            # Get stocks with prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Check if we got an error response (no live prices available)
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print("[ERROR] PRICE_DATA_UNAVAILABLE - cannot calculate plan")
                
                # Return structured error response
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data unavailable'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'price_data_status': stocks_data.get('price_data_status', {}),
                    'data_quality': {
                        'live_data_available': False,
                        'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()) if self.zerodha_auth else False,
                        'error_reason': stocks_data.get('error_message', 'Live price data unavailable')
                    }
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
                'summary': {
                    'total_orders': len(orders),
                    'total_stocks': len([o for o in orders if o['shares'] > 0]),
                    'total_investment_value': allocation_result['total_allocated'],
                    'remaining_cash': allocation_result['remaining_cash'],
                    'utilization_percent': allocation_result['utilization_percent']
                },
                'csv_info': stocks_data['csv_info'],
                'data_quality': {
                    'live_data_available': stocks_data['price_data_status']['live_prices_used'],
                    'data_source': stocks_data['price_data_status']['market_data_source'],
                    'data_quality_level': stocks_data['price_data_status'].get('data_quality', 'HIGH')
                },
                'validation': allocation_result['validation']
            }
            
            print(f"[SUCCESS] Investment plan created: {len(orders)} orders")
            print(f"   Total allocated: Rs.{allocation_result['total_allocated']:,.0f}")
            print(f"   Utilization: {allocation_result['utilization_percent']:.1f}%")
            print(f"   Stocks in range: {allocation_result['validation']['stocks_in_range']}/{len(orders)}")
            
            return plan
            
        except Exception as e:
            print(f"[ERROR] Error calculating investment plan: {e}")
            
            # Check if it's a price data error
            if "PRICE_DATA_UNAVAILABLE" in str(e):
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': str(e),
                    'data_quality': {
                        'live_data_available': False,
                        'error_reason': str(e)
                    }
                }
            
            raise Exception(f"Cannot calculate investment plan: {str(e)}")
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment plan"""
        try:
            print("[INFO] Executing initial investment...")
            
            # Check if plan has price data errors
            if 'error' in investment_plan and investment_plan['error'] == 'PRICE_DATA_UNAVAILABLE':
                raise Exception("Cannot execute plan: Live price data unavailable")
            
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
                'utilization_percent': investment_plan['summary']['utilization_percent'],
                'data_quality': investment_plan.get('data_quality', {})
            }
            
            print(f"[SUCCESS] Initial investment executed: {len(system_orders)} orders")
            print(f"   Total investment: Rs.{investment_plan['summary']['total_investment_value']:,.0f}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error executing initial investment: {e}")
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
                print(f"[WARNING] Could not fetch current CSV: {e}")
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
            print(f"[ERROR] Error checking rebalancing: {e}")
            return {
                'rebalancing_needed': False,
                'reason': 'Error checking rebalancing status',
                'is_first_time': False,
                'error': str(e)
            }
    
    def get_system_portfolio_status(self) -> Dict:
        """Get system portfolio status with comprehensive metrics"""
        try:
            # Get all orders for portfolio construction
            all_orders = self._load_system_orders()
            
            if not all_orders:
                return {
                    'status': 'empty',
                    'message': 'No orders found. Please complete initial investment.',
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0, 
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': 0
                    }
                }
            
            # Construct portfolio from orders
            construction_result = self.portfolio_construction.construct_portfolio_from_orders(all_orders)
            
            if not construction_result['holdings']:
                return {
                    'status': 'empty',
                    'message': 'No active holdings found in portfolio construction.',
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0,
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': 0
                    }
                }
            
            # Get current prices for all holdings
            symbols = list(construction_result['holdings'].keys())
            
            try:
                # Try to get live prices
                stocks_data = self.csv_service.get_stocks_with_prices()
                
                # Check if we got an error response (no live prices available)
                if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                    print("[WARNING] Live prices unavailable, cannot calculate current values")
                    
                    # Return portfolio state without current values
                    holdings_basic = {}
                    total_investment = 0
                    
                    for symbol, holding in construction_result['holdings'].items():
                        shares = holding['total_shares']
                        avg_price = holding['avg_price']
                        investment_value = holding['total_investment']
                        
                        holdings_basic[symbol] = {
                            'shares': shares,
                            'avg_price': avg_price,
                            'current_price': 0,  # Unknown
                            'investment_value': investment_value,
                            'current_value': 0,  # Cannot calculate
                            'pnl': 0,  # Cannot calculate
                            'pnl_percent': 0,  # Cannot calculate
                            'allocation_percent': 0
                        }
                        
                        total_investment += investment_value
                    
                    return {
                        'status': 'active',
                        'holdings': holdings_basic,
                        'portfolio_summary': {
                            'total_investment': total_investment,
                            'current_value': 0,  # Cannot calculate
                            'total_returns': 0,  # Cannot calculate
                            'returns_percentage': 0,  # Cannot calculate
                            'stock_count': len(holdings_basic)
                        },
                        'data_quality': {
                            'price_source': 'UNAVAILABLE',
                            'live_data_available': False,
                            'error_reason': stocks_data.get('error_message', 'Live price data unavailable'),
                            'last_updated': datetime.now().isoformat()
                        }
                    }
                
                # Extract prices from stocks data
                current_prices = {}
                for stock in stocks_data.get('stocks', []):
                    current_prices[stock['symbol']] = stock['price']
                
            except Exception as e:
                print(f"[WARNING] Could not get live prices, creating basic portfolio: {e}")
                
                # Create basic portfolio without current prices
                holdings_basic = {}
                total_investment = 0
                
                for symbol, holding in construction_result['holdings'].items():
                    shares = holding['total_shares']
                    avg_price = holding['avg_price']
                    investment_value = holding['total_investment']
                    
                    holdings_basic[symbol] = {
                        'shares': shares,
                        'avg_price': avg_price,
                        'current_price': avg_price,  # Use avg price as fallback
                        'investment_value': investment_value,
                        'current_value': investment_value,  # Use investment value
                        'pnl': 0,
                        'pnl_percent': 0,
                        'allocation_percent': 0
                    }
                    
                    total_investment += investment_value
                
                # Calculate allocation percentages
                for holding in holdings_basic.values():
                    holding['allocation_percent'] = (holding['current_value'] / total_investment * 100) if total_investment > 0 else 0
                
                return {
                    'status': 'active',
                    'holdings': holdings_basic,
                    'portfolio_summary': {
                        'total_investment': total_investment,
                        'current_value': total_investment,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': len(holdings_basic)
                    },
                    'data_quality': {
                        'price_source': 'Fallback (using avg prices)',
                        'live_data_available': False,
                        'error_reason': str(e),
                        'last_updated': datetime.now().isoformat()
                    }
                }
            
            # Calculate comprehensive metrics with live prices
            try:
                metrics = self.portfolio_metrics.calculate_comprehensive_metrics(
                    construction_result['holdings'],
                    current_prices,
                    construction_result
                )
                
                # Build response with proper error handling
                holdings_with_metrics = {}
                for symbol, holding_metrics in metrics['holdings_with_metrics'].items():
                    holdings_with_metrics[symbol] = {
                        'shares': int(holding_metrics.get('shares', 0)),
                        'avg_price': float(holding_metrics.get('avg_price', 0)),
                        'current_price': float(holding_metrics.get('current_price', 0)),
                        'investment_value': float(holding_metrics.get('investment_value', 0)),
                        'current_value': float(holding_metrics.get('current_value', 0)),
                        'pnl': float(holding_metrics.get('absolute_return', 0)),
                        'pnl_percent': float(holding_metrics.get('percentage_return', 0)),
                        'allocation_percent': float(holding_metrics.get('allocation_percent', 0)),
                        'days_held': int(holding_metrics.get('days_held', 0)),
                        'annualized_return': float(holding_metrics.get('annualized_return', 0))
                    }
                
                portfolio_summary = {
                    'total_investment': float(metrics.get('total_investment', 0)),
                    'current_value': float(metrics.get('current_value', 0)),
                    'total_returns': float(metrics.get('total_returns', 0)),
                    'returns_percentage': float(metrics.get('returns_percentage', 0)),
                    'stock_count': len(holdings_with_metrics),
                    'cagr': float(metrics.get('cagr', 0)),
                    'investment_period_days': int(metrics.get('investment_period_days', 0))
                }
                
                performance_metrics = {
                    'best_performer': metrics.get('best_performer', {}),
                    'worst_performer': metrics.get('worst_performer', {}),
                    'volatility_score': float(metrics.get('volatility_score', 0)),
                    'sharpe_ratio': float(metrics.get('sharpe_ratio', 0))
                }
                
                return {
                    'status': 'active',
                    'holdings': holdings_with_metrics,
                    'portfolio_summary': portfolio_summary,
                    'performance_metrics': performance_metrics,
                    'allocation_analysis': {
                        'allocation_stats': metrics.get('allocation_stats', {}),
                        'rebalancing_needed': metrics.get('rebalancing_needed', False)
                    },
                    'data_quality': {
                        'price_source': 'Live',
                        'live_data_available': True,
                        'construction_validation': construction_result.get('validation', {}),
                        'last_updated': datetime.now().isoformat()
                    }
                }
                
            except Exception as metrics_error:
                print(f"[WARNING] Could not calculate advanced metrics: {metrics_error}")
                
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
                        'pnl_percent': pnl_percent,
                        'allocation_percent': 0  # Will calculate after totals
                    }
                    
                    total_investment += investment_value
                    current_value += holding_value
                
                # Calculate allocation percentages
                for holding in holdings_with_metrics.values():
                    holding['allocation_percent'] = (holding['current_value'] / current_value * 100) if current_value > 0 else 0
                
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
                    },
                    'data_quality': {
                        'price_source': 'Live (Basic Calculation)',
                        'live_data_available': True,
                        'metrics_error': str(metrics_error),
                        'last_updated': datetime.now().isoformat()
                    }
                }
            
        except Exception as e:
            print(f"[ERROR] Error getting portfolio status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'holdings': {},
                'portfolio_summary': {
                    'total_investment': 0, 
                    'current_value': 0,
                    'total_returns': 0,
                    'returns_percentage': 0,
                    'stock_count': 0
                },
                'data_quality': {
                    'error': str(e),
                    'last_updated': datetime.now().isoformat()
                }
            }
    
    # Helper methods (keeping existing implementations)
    def _is_first_time_setup(self) -> bool:
        """Check if this is first time setup - based on orders file"""
        try:
            if not os.path.exists(self.orders_file):
                return True
            
            with open(self.orders_file, 'r') as f:
                orders = json.load(f)
                return len(orders) == 0
        except:
            return True
    
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
            
            print(f"[INFO] Saved {len(new_orders)} new orders (total: {len(all_orders)})")
        except Exception as e:
            print(f"[ERROR] Error saving system orders: {e}")
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
            print(f"[WARNING] Error loading system orders: {e}")
            return []
    
    def _update_portfolio_state(self, orders: List[Dict], csv_info: Dict):
        """Update portfolio state based on orders (legacy method for initial investment)"""
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
            
            print(f"[INFO] Portfolio state updated with {len(holdings)} holdings")
            
        except Exception as e:
            print(f"[ERROR] Error updating portfolio state: {e}")
            raise
    
    def _update_portfolio_state_from_all_orders(self, all_orders: List[Dict], csv_info: Dict):
        """Update portfolio state by reconstructing from all orders (for rebalancing)"""
        try:
            print(f"[INFO] Reconstructing portfolio state from {len(all_orders)} total orders...")
            
            # Use portfolio construction service to build current state
            construction_result = self.portfolio_construction.construct_portfolio_from_orders(all_orders)
            holdings = construction_result['holdings']
            
            # Convert to the format expected by portfolio state
            portfolio_holdings = {}
            for symbol, holding_data in holdings.items():
                portfolio_holdings[symbol] = {
                    'shares': holding_data['total_shares'],
                    'avg_price': holding_data['avg_price'],
                    'total_investment': holding_data['total_investment']
                }
            
            portfolio_state = {
                'holdings': portfolio_holdings,
                'last_updated': datetime.now().isoformat(),
                'csv_info': csv_info,
                'type': 'REBALANCED_PORTFOLIO',
                'total_orders_processed': len(all_orders),
                'construction_summary': {
                    'total_cash_outflow': construction_result['total_cash_outflow'],
                    'first_order_date': construction_result['first_order_date'],
                    'last_order_date': construction_result['last_order_date']
                }
            }
            
            with open(self.portfolio_state_file, 'w') as f:
                json.dump(portfolio_state, f, indent=2)
            
            print(f"[INFO] Portfolio state reconstructed with {len(portfolio_holdings)} holdings")
            print(f"   Total cash outflow: Rs.{construction_result['total_cash_outflow']:,.0f}")
            
        except Exception as e:
            print(f"[ERROR] Error updating portfolio state from all orders: {e}")
            raise
    
    def _get_current_portfolio_state(self) -> Optional[Dict]:
        """Get current portfolio state"""
        if not os.path.exists(self.portfolio_state_file):
            return None
        
        try:
            with open(self.portfolio_state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Error reading portfolio state: {e}")
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
            print(f"[WARNING] Error updating CSV history: {e}")
    
    def get_service_status(self) -> Dict:
        """Get comprehensive service status"""
        return {
            'csv_service': {
                'available': bool(self.csv_service),
                'connection_status': self.csv_service.get_connection_status()
            },
            'zerodha_auth': {
                'available': bool(self.zerodha_auth),
                'authenticated': self.zerodha_auth.is_authenticated() if self.zerodha_auth else False
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
    
    def get_investment_status(self) -> Dict:
        """Get simplified investment status - determines what action to take"""
        try:
            print("[INFO] Getting investment status...")
            
            # Check if first time (no orders)
            is_first_time = self._is_first_time_setup()
            
            if is_first_time:
                print("[INFO] First time investment detected")
                
                # Get investment requirements for first time
                requirements = self.get_investment_requirements()
                
                return {
                    "status": "FIRST_INVESTMENT",
                    "action_needed": "initial_investment",
                    "message": "Ready for your first investment",
                    "requirements": requirements
                }
            
            # Has orders - check if rebalancing needed
            print("[INFO] Existing portfolio detected - checking rebalancing")
            
            # Get current portfolio status
            portfolio_status = self.get_system_portfolio_status()
            
            # Get current CSV stocks
            csv_stocks_data = self.csv_service.get_stocks_with_prices()
            current_csv_stocks = set([stock['symbol'] for stock in csv_stocks_data.get('stocks', [])])
            
            # Get portfolio stocks
            portfolio_stocks = set()
            if portfolio_status['status'] == 'active':
                portfolio_stocks = set(portfolio_status['holdings'].keys())
            
            print(f"CSV stocks: {len(current_csv_stocks)}")
            print(f"Portfolio stocks: {len(portfolio_stocks)}")
            
            # Compare stocks and allocations
            if current_csv_stocks == portfolio_stocks:
                print("[INFO] Stock list matches CSV - checking allocation balance...")
                
                # Check if allocations are within ±1.5% tolerance
                target_allocation = 100.0 / len(portfolio_stocks)  # Equal weight
                tolerance = 1.5  # ±1.5% tolerance
                
                allocation_issues = []
                for symbol, holding in portfolio_status['holdings'].items():
                    current_allocation = holding.get('allocation_percent', 0)
                    deviation = abs(current_allocation - target_allocation)
                    
                    if deviation > tolerance:
                        allocation_issues.append({
                            'symbol': symbol,
                            'current_allocation': current_allocation,
                            'target_allocation': target_allocation,
                            'deviation': deviation
                        })
                
                if not allocation_issues:
                    print("[SUCCESS] Portfolio stocks and allocations are balanced")
                    return {
                        "status": "BALANCED",
                        "action_needed": "none",
                        "message": "Portfolio is balanced and up-to-date",
                        "portfolio_status": portfolio_status,
                        "csv_stocks_count": len(current_csv_stocks),
                        "portfolio_stocks_count": len(portfolio_stocks)
                    }
                else:
                    print(f"[INFO] Portfolio stocks match but {len(allocation_issues)} allocations need rebalancing")
                    for issue in allocation_issues[:3]:  # Show first 3
                        print(f"   {issue['symbol']}: {issue['current_allocation']:.2f}% (deviation: {issue['deviation']:.2f}%)")
                    
                    return {
                        "status": "REBALANCING_NEEDED",
                        "action_needed": "rebalancing",
                        "message": f"Portfolio needs rebalancing - {len(allocation_issues)} stocks have allocation drift beyond ±1.5%",
                        "portfolio_status": portfolio_status,
                        "csv_stocks_count": len(current_csv_stocks),
                        "portfolio_stocks_count": len(portfolio_stocks),
                        "allocation_issues": allocation_issues,
                        "rebalancing_reason": "allocation_drift"
                    }
            
            else:
                print("[INFO] Portfolio doesn't match CSV - rebalancing needed")
                
                new_stocks = current_csv_stocks - portfolio_stocks
                removed_stocks = portfolio_stocks - current_csv_stocks
                
                print(f"New stocks: {len(new_stocks)}")
                print(f"Removed stocks: {len(removed_stocks)}")
                
                return {
                    "status": "REBALANCING_NEEDED",
                    "action_needed": "rebalancing",
                    "message": "Portfolio needs rebalancing due to stock list changes",
                    "portfolio_status": portfolio_status,
                    "csv_stocks_count": len(current_csv_stocks),
                    "portfolio_stocks_count": len(portfolio_stocks),
                    "changes": {
                        "new_stocks": list(new_stocks),
                        "removed_stocks": list(removed_stocks),
                        "new_count": len(new_stocks),
                        "removed_count": len(removed_stocks)
                    }
                }
            
        except Exception as e:
            print(f"[ERROR] Error getting investment status: {e}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            
            return {
                "status": "ERROR",
                "action_needed": "fix_error",
                "message": f"Error determining investment status: {str(e)}",
                "error": str(e)
            }
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0.0) -> Dict:
        """Calculate rebalancing plan for paper trading (allocation-based)"""
        try:
            print(f"[INFO] Calculating PAPER TRADING rebalancing plan with additional investment: Rs.{additional_investment:,.0f}")
            
            # Step 1: Get current portfolio status with allocations
            print("[INFO] Step 1: Getting current paper portfolio allocations...")
            portfolio_status = self.get_system_portfolio_status()
            
            if portfolio_status['status'] != 'active':
                raise Exception(f"Portfolio not active: {portfolio_status.get('message', 'Unknown error')}")
            
            current_holdings = portfolio_status['holdings']
            current_portfolio_value = portfolio_status['portfolio_summary']['current_value']
            print(f"[INFO] Current portfolio value: Rs.{current_portfolio_value:,.0f}")
            
            # Step 2: Check if rebalancing is needed based on allocation drift
            target_allocation = 100.0 / len(current_holdings)  # Equal weight
            tolerance = 1.5  # ±1.5% tolerance
            
            rebalancing_needed = False
            allocation_issues = []
            
            for symbol, holding in current_holdings.items():
                current_allocation = holding.get('allocation_percent', 0)
                deviation = abs(current_allocation - target_allocation)
                
                if deviation > tolerance:
                    rebalancing_needed = True
                    allocation_issues.append({
                        'symbol': symbol,
                        'current_allocation': current_allocation,
                        'target_allocation': target_allocation,
                        'deviation': deviation,
                        'status': 'OVER_ALLOCATED' if current_allocation > target_allocation else 'UNDER_ALLOCATED'
                    })
            
            print(f"[INFO] Allocation analysis: {len(allocation_issues)} stocks need rebalancing")
            
            if not rebalancing_needed and additional_investment == 0:
                return {
                    'success': True,
                    'message': 'Portfolio is well balanced - no rebalancing needed',
                    'data': {
                        'buy_orders': [],
                        'sell_orders': [],
                        'plan_summary': {
                            'current_portfolio_value': current_portfolio_value,
                            'additional_investment': additional_investment,
                            'total_rebalancing_value': current_portfolio_value + additional_investment,
                            'target_portfolio_value': current_portfolio_value,
                            'remaining_cash': 0,
                            'total_stocks': len(current_holdings),
                            'buy_orders_count': 0,
                            'sell_orders_count': 0,
                            'total_buy_value': 0,
                            'total_sell_value': 0,
                            'net_investment_needed': 0,
                            'rebalancing_needed': False,
                            'portfolio_comparison_status': 'BALANCED'  # Fix: Add missing key
                        },
                        'allocation_analysis': allocation_issues
                    }
                }
            
            # Step 3: Add additional investment if provided
            total_rebalancing_value = current_portfolio_value + additional_investment
            print(f"[INFO] Total value for rebalancing: Rs.{total_rebalancing_value:,.0f}")
            
            # Step 4: Get current CSV stocks with prices
            csv_stocks_data = self.csv_service.get_stocks_with_prices()
            if 'error' in csv_stocks_data:
                raise Exception(f"Cannot get CSV stocks: {csv_stocks_data['error_message']}")
            
            csv_stocks = csv_stocks_data.get('stocks', [])
            if not csv_stocks:
                raise Exception("No stocks found in CSV")
            
            print(f"[INFO] Rebalancing to {len(csv_stocks)} stocks from CSV")
            
            # Step 5: Calculate optimal allocation using investment calculator (with ±1.5% flexibility)
            allocation_result = self.investment_calculator.calculate_optimal_allocation(
                total_rebalancing_value, csv_stocks
            )
            
            print(f"[INFO] Optimal allocation calculated for Rs.{total_rebalancing_value:,.0f}")
            
            # Step 6: Create target portfolio plan from allocation result
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
            
            print(f"[INFO] Target portfolio: {len(target_portfolio)} stocks, Rs.{total_target_value:,.0f} total value")
            
            # Step 7: Calculate buy/sell orders based on current paper portfolio vs target
            buy_orders = []
            sell_orders = []
            
            print(f"[INFO] Comparing target portfolio with current paper portfolio...")
            
            # Compare each target stock with current holdings
            for symbol, target_info in target_portfolio.items():
                target_shares = target_info['shares']
                target_price = target_info['price']
                current_shares = current_holdings.get(symbol, {}).get('shares', 0)
                
                print(f"   {symbol}: Target={target_shares}, Current={current_shares}")
                
                if target_shares > current_shares:
                    # Need to buy more
                    shares_to_buy = target_shares - current_shares
                    buy_orders.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "shares": shares_to_buy,
                        "price": target_price,
                        "value": shares_to_buy * target_price,
                        "reason": "Increase position for rebalancing"
                    })
                elif target_shares < current_shares:
                    # Need to sell some
                    shares_to_sell = current_shares - target_shares
                    current_price = current_holdings[symbol]['current_price']
                    sell_orders.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "shares": shares_to_sell,
                        "price": current_price,
                        "value": shares_to_sell * current_price,
                        "reason": "Reduce position for rebalancing"
                    })
                # If target_shares == current_shares, no action needed
            
            # Handle stocks in current portfolio but not in CSV (sell all)
            csv_symbols = set(target_portfolio.keys())
            for symbol, holding_info in current_holdings.items():
                if symbol not in csv_symbols and holding_info['shares'] > 0:
                    # Stock not in CSV anymore - sell all
                    shares_to_sell = holding_info['shares']
                    current_price = holding_info['current_price']
                    
                    sell_orders.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "shares": shares_to_sell,
                        "price": current_price,
                        "value": shares_to_sell * current_price,
                        "reason": "Stock removed from CSV list"
                    })
                    
                    print(f"   {symbol}: Not in CSV, selling all {shares_to_sell} shares")
            
            total_buy_value = sum(order['value'] for order in buy_orders)
            total_sell_value = sum(order['value'] for order in sell_orders)
            net_investment_needed = total_buy_value - total_sell_value
            
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
            
            print(f"[SUCCESS] Paper trading rebalancing plan calculated:")
            print(f"   Buy orders: {len(buy_orders)} (Rs.{total_buy_value:,.0f})")
            print(f"   Sell orders: {len(sell_orders)} (Rs.{total_sell_value:,.0f})")
            print(f"   Net investment needed: Rs.{net_investment_needed:,.0f}")
            
            return {
                "success": True,
                "message": "Paper trading rebalancing plan calculated successfully",
                "data": {
                    "plan_summary": plan_summary,
                    "target_portfolio": target_portfolio,
                    "allocation_result": allocation_result,
                    "buy_orders": buy_orders,
                    "sell_orders": sell_orders,
                    "allocation_analysis": allocation_issues,
                    "execution_ready": True,
                    "data_quality": allocation_result.get('data_quality', 'Unknown')
                }
            }
            
        except Exception as e:
            print(f"[ERROR] Error calculating rebalancing plan: {e}")
            raise Exception(f"Cannot calculate rebalancing plan: {str(e)}")
    
    def execute_rebalancing(self, additional_investment: float = 0.0) -> Dict:
        """Execute rebalancing by storing orders"""
        try:
            print(f"[INFO] Executing rebalancing with additional investment: Rs.{additional_investment:,.0f}")
            
            # Calculate the rebalancing plan
            plan_result = self.calculate_rebalancing_plan(additional_investment)
            
            if not plan_result['success']:
                raise Exception(f"Failed to calculate rebalancing plan: {plan_result.get('message', 'Unknown error')}")
            
            plan = plan_result['data']
            
            # Load existing orders
            existing_orders = self._load_system_orders()
            new_orders = []
            order_id = self._get_next_order_id()
            execution_time = datetime.now().isoformat()
            
            # Add sell orders first
            for sell_order in plan['sell_orders']:
                order = {
                    "order_id": order_id,
                    "symbol": sell_order['symbol'],
                    "action": "SELL",
                    "shares": sell_order['shares'],
                    "price": sell_order['price'],
                    "value": sell_order['value'],
                    "execution_time": execution_time,
                    "session_type": "REBALANCING",
                    "order_type": "REBALANCING_SELL",
                    "reason": sell_order.get('reason', 'Portfolio rebalancing'),
                    "status": "EXECUTED_SYSTEM"
                }
                new_orders.append(order)
                order_id += 1
                print(f"   SELL {sell_order['shares']} {sell_order['symbol']} @ Rs.{sell_order['price']:.2f} - {sell_order.get('reason', '')}")
            
            # Add buy orders
            for buy_order in plan['buy_orders']:
                order = {
                    "order_id": order_id,
                    "symbol": buy_order['symbol'],
                    "action": "BUY",
                    "shares": buy_order['shares'],
                    "price": buy_order['price'],
                    "value": buy_order['value'],
                    "execution_time": execution_time,
                    "session_type": "REBALANCING",
                    "order_type": "REBALANCING_BUY",
                    "reason": buy_order.get('reason', 'Portfolio rebalancing'),
                    "status": "EXECUTED_SYSTEM"
                }
                new_orders.append(order)
                order_id += 1
                print(f"   BUY {buy_order['shares']} {buy_order['symbol']} @ Rs.{buy_order['price']:.2f} - {buy_order.get('reason', '')}")
            
            # Save new orders
            self._save_system_orders(new_orders)
            
            # Update portfolio state with all orders (existing + new)
            all_orders = existing_orders + new_orders
            
            # Get current CSV info for portfolio state update
            csv_data = self.csv_service.fetch_csv_data(force_refresh=False)
            csv_info = {
                'fetch_time': csv_data['fetch_time'],
                'csv_hash': csv_data['csv_hash'],
                'source_url': csv_data['source_url'],
                'total_symbols': len(csv_data['symbols'])
            }
            
            # Update portfolio state
            self._update_portfolio_state_from_all_orders(all_orders, csv_info)
            
            # Update CSV history
            self._update_csv_history(csv_info)
            
            result = {
                "execution_successful": True,
                "orders_executed": len(new_orders),
                "buy_orders": len(plan['buy_orders']),
                "sell_orders": len(plan['sell_orders']),
                "total_buy_value": plan['plan_summary']['total_buy_value'],
                "total_sell_value": plan['plan_summary']['total_sell_value'],
                "net_investment": plan['plan_summary']['net_investment_needed'],
                "additional_investment_used": additional_investment,
                "execution_time": execution_time,
                "new_portfolio_stocks": plan['plan_summary']['total_stocks'],
                "portfolio_comparison_status": plan['plan_summary']['portfolio_comparison_status'],
                "target_portfolio_value": plan['plan_summary']['target_portfolio_value'],
                "remaining_cash": plan['plan_summary']['remaining_cash'],
                "data_quality": plan.get('data_quality', 'Unknown')
            }
            
            print(f"[SUCCESS] Rebalancing executed successfully!")
            print(f"   New orders executed: {result['orders_executed']}")
            print(f"   Buy orders: {result['buy_orders']}, Sell orders: {result['sell_orders']}")
            print(f"   Additional investment: Rs.{additional_investment:,.0f}")
            print(f"   New portfolio stocks: {result['new_portfolio_stocks']}")
            print(f"   Portfolio comparison status: {result['portfolio_comparison_status']}")
            print(f"   Target portfolio value: Rs.{result['target_portfolio_value']:,.0f}")
            print(f"   Remaining cash: Rs.{result['remaining_cash']:,.0f}")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] Error executing rebalancing: {e}")
            raise Exception(f"Cannot execute rebalancing: {str(e)}")