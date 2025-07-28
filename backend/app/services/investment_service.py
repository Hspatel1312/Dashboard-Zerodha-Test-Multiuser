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
        """Get minimum investment requirements based on current CSV - STRICT: Live data only"""
        try:
            print("📋 Getting investment requirements with STRICT live data policy...")
            
            # Get stocks with LIVE prices only - no fallbacks allowed
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                print(f"❌ Failed to get stocks with live prices: {e}")
                
                # Check if this is a price data unavailable error
                if "PRICE_DATA_UNAVAILABLE" in str(e):
                    print("🚫 STRICT MODE: Cannot proceed without live price data")
                    
                    # Try to get basic CSV info for error reporting
                    try:
                        csv_data = self.csv_service.fetch_csv_data()
                        csv_info = {
                            'fetch_time': csv_data.get('fetch_time'),
                            'csv_hash': csv_data.get('csv_hash'),
                            'source_url': csv_data.get('source_url'),
                            'total_symbols': len(csv_data.get('symbols', []))
                        }
                    except:
                        csv_info = {}
                    
                    return {
                        'error': 'PRICE_DATA_UNAVAILABLE',
                        'error_message': str(e),
                        'csv_info': csv_info,
                        'data_quality': {
                            'live_data_available': False,
                            'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()),
                            'market_data_source': 'UNAVAILABLE',
                            'data_policy': 'STRICT - Real data only, no fallbacks',
                            'solution': 'Ensure Zerodha is authenticated and market is open'
                        }
                    }
                else:
                    raise Exception(f"Unable to fetch stock data: {str(e)}")
            
            # Check if we got an error response instead of valid data
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print("🚫 Received price data unavailable error from CSV service")
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data unavailable'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'data_quality': stocks_data.get('price_data_status', {})
                }
            
            # Validate that we have valid stock data with live prices
            if stocks_data.get('total_stocks', 0) == 0:
                raise Exception("No valid stocks found with live price data")
            
            # STRICT: Verify all data is from live sources
            price_data_status = stocks_data.get('price_data_status', {})
            if not price_data_status.get('live_prices_used', False):
                print("🚫 STRICT MODE: Data not from live sources")
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': 'Investment calculations require live price data',
                    'csv_info': stocks_data.get('csv_info', {}),
                    'data_quality': price_data_status
                }
            
            print(f"✅ Verified live data available for {stocks_data['total_stocks']} stocks")
            
            # Calculate minimum investment using LIVE data only
            try:
                min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            except Exception as e:
                print(f"❌ Failed to calculate minimum investment: {e}")
                
                # If calculation fails due to price data issues, return structured error
                if "PRICE_DATA_INVALID" in str(e):
                    return {
                        'error': 'PRICE_DATA_UNAVAILABLE',
                        'error_message': str(e),
                        'csv_info': stocks_data.get('csv_info', {}),
                        'data_quality': price_data_status
                    }
                else:
                    raise Exception(f"Unable to calculate investment requirements: {str(e)}")
            
            requirements = {
                'is_first_time': self._is_first_time_setup(),
                'stocks_data': stocks_data,
                'minimum_investment': min_investment_info,
                'csv_info': stocks_data['csv_info'],
                'system_status': 'ready_for_initial_investment',
                'data_quality': {
                    'live_data_available': True,
                    'zerodha_connected': bool(self.zerodha_auth and self.zerodha_auth.is_authenticated()),
                    'price_success_rate': price_data_status.get('success_rate', 0),
                    'total_valid_stocks': stocks_data['total_stocks'],
                    'data_source': price_data_status.get('market_data_source', 'Unknown'),
                    'data_quality_level': price_data_status.get('data_quality', 'Unknown'),
                    'market_open': price_data_status.get('market_open', False),
                    'data_policy': 'STRICT - Live data only'
                }
            }
            
            print(f"✅ Investment requirements prepared with LIVE data:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Min investment: ₹{min_investment_info['minimum_investment']:,.0f}")
            print(f"   Data source: {price_data_status.get('market_data_source')}")
            print(f"   Data quality: {price_data_status.get('data_quality', 'Unknown')}")
            
            return requirements
            
        except Exception as e:
            print(f"❌ Error getting investment requirements: {e}")
            # For any other errors, provide a structured response
            return {
                'error': 'CALCULATION_ERROR', 
                'error_message': f"Cannot provide investment requirements: {str(e)}",
                'data_quality': {
                    'live_data_available': False,
                    'error_type': 'CALCULATION_ERROR'
                }
            }
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan - STRICT: Live data only"""
        try:
            print(f"💰 Calculating investment plan for ₹{investment_amount:,.0f} with STRICT live data")
            
            # Get stocks with LIVE prices only
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Check if we got an error response
            if 'error' in stocks_data and stocks_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                print("🚫 Cannot calculate plan - live price data unavailable")
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': stocks_data.get('error_message', 'Live price data required for calculations'),
                    'csv_info': stocks_data.get('csv_info', {}),
                    'data_quality': stocks_data.get('price_data_status', {})
                }
            
            # STRICT: Verify data quality
            price_data_status = stocks_data.get('price_data_status', {})
            if not price_data_status.get('live_prices_used', False):
                print("🚫 Plan calculation requires live prices")
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': 'Investment plan calculation requires live market data',
                    'csv_info': stocks_data.get('csv_info', {}),
                    'data_quality': price_data_status
                }
            
            # Validate minimum investment with live data
            min_investment_info = self.investment_calculator.calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(f"Investment amount ₹{investment_amount:,.0f} is below minimum required ₹{min_investment_info['minimum_investment']:,.0f}")
            
            # Calculate allocation using LIVE prices only
            allocation_result = self.investment_calculator.calculate_optimal_allocation(investment_amount, stocks_data['stocks'])
            
            # STRICT: Verify allocation was calculated with live data
            if allocation_result.get('data_quality') != 'HIGH - All prices from live API':
                print("🚫 Allocation calculation did not use live data")
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': 'Allocation calculation requires live price data',
                    'data_quality': {'live_data_available': False}
                }
            
            # Generate orders from allocation - all with live prices
            orders = []
            for allocation in allocation_result['allocations']:
                if allocation['shares'] > 0:
                    # STRICT: Verify this allocation has live price data
                    if allocation.get('price_type') != 'LIVE':
                        print(f"🚫 Skipping {allocation['symbol']} - not live price")
                        continue
                    
                    orders.append({
                        'symbol': allocation['symbol'],
                        'action': 'BUY',
                        'shares': allocation['shares'],
                        'price': allocation['price'],
                        'value': allocation['value'],
                        'allocation_percent': allocation['allocation_percent'],
                        'price_type': allocation.get('price_type', 'LIVE')
                    })
            
            if len(orders) == 0:
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': 'No orders could be created - no live price data available',
                    'data_quality': {'live_data_available': False}
                }
            
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
                    'live_data_available': True,
                    'live_data_used': True,
                    'data_source': price_data_status.get('market_data_source'),
                    'data_quality_level': price_data_status.get('data_quality'),
                    'success_rate': price_data_status.get('success_rate'),
                    'market_open': price_data_status.get('market_open'),
                    'all_prices_live': all(order.get('price_type') == 'LIVE' for order in orders)
                },
                'validation': allocation_result['validation']
            }
            
            print(f"✅ Investment plan created with LIVE data: {len(orders)} orders")
            print(f"   Total allocated: ₹{allocation_result['total_allocated']:,.0f}")
            print(f"   Utilization: {allocation_result['utilization_percent']:.1f}%")
            print(f"   All prices LIVE: {plan['data_quality']['all_prices_live']}")
            
            return plan
            
        except Exception as e:
            print(f"❌ Error calculating investment plan: {e}")
            
            # Check if it's a price data error
            if "PRICE_DATA_INVALID" in str(e) or "PRICE_DATA_UNAVAILABLE" in str(e):
                return {
                    'error': 'PRICE_DATA_UNAVAILABLE',
                    'error_message': str(e),
                    'data_quality': {'live_data_available': False}
                }
            else:
                raise Exception(f"Cannot calculate investment plan: {str(e)}")
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment plan - STRICT: Only with live data"""
        try:
            print("🚀 Executing initial investment with STRICT live data validation...")
            
            # STRICT: Validate plan has live data before execution
            data_quality = investment_plan.get('data_quality', {})
            
            if not data_quality.get('live_data_available', False):
                print("🚫 EXECUTION BLOCKED: Plan lacks live data")
                return {
                    'error': 'EXECUTION_BLOCKED',
                    'error_message': 'Cannot execute plan without live price data',
                    'data_quality': data_quality
                }
            
            if not data_quality.get('all_prices_live', False):
                print("🚫 EXECUTION BLOCKED: Not all prices are live")
                return {
                    'error': 'EXECUTION_BLOCKED', 
                    'error_message': 'All order prices must be from live data',
                    'data_quality': data_quality
                }
            
            print(f"✅ Plan validation passed - executing with {data_quality.get('data_source')} data")
            
            # Create system orders with live price verification
            system_orders = []
            order_id = self._get_next_order_id()
            execution_time = datetime.now().isoformat()
            
            for order in investment_plan['orders']:
                # STRICT: Double-check each order has live price
                if order.get('price_type') != 'LIVE':
                    print(f"🚫 Skipping order for {order['symbol']} - not live price")
                    continue
                
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
                    'session_type': 'INITIAL_INVESTMENT',
                    'price_type': order.get('price_type', 'LIVE'),
                    'data_source': data_quality.get('data_source', 'Unknown')
                }
                system_orders.append(system_order)
                order_id += 1
            
            if len(system_orders) == 0:
                return {
                    'error': 'EXECUTION_BLOCKED',
                    'error_message': 'No valid orders with live prices to execute',
                    'data_quality': {'live_data_available': False}
                }
            
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
                'data_quality': {
                    'live_data_used': True,
                    'data_source': data_quality.get('data_source'),
                    'data_quality_level': data_quality.get('data_quality_level'),
                    'all_orders_live_priced': True,
                    'execution_validation': 'PASSED'
                }
            }
            
            print(f"✅ Initial investment executed with LIVE data: {len(system_orders)} orders")
            print(f"   Total investment: ₹{investment_plan['summary']['total_investment_value']:,.0f}")
            print(f"   Data source: {data_quality.get('data_source')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error executing initial investment: {e}")
            return {
                'error': 'EXECUTION_FAILED',
                'error_message': f"Failed to execute initial investment: {str(e)}",
                'data_quality': {'live_data_available': False}
            }
    
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
        """Get system portfolio status with comprehensive metrics - STRICT: Live prices only"""
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
            
            # Get current prices for all holdings - STRICT: Live prices only
            symbols = list(construction_result['holdings'].keys())
            
            try:
                print(f"🔍 Fetching LIVE prices for {len(symbols)} portfolio holdings...")
                current_prices = self.csv_service.get_live_prices(symbols)
                print(f"✅ Retrieved {len(current_prices)} live prices for portfolio")
                
                live_prices_used = True
                price_data_source = "Zerodha Live API"
                
            except Exception as e:
                print(f"❌ Could not get live prices for portfolio: {e}")
                
                # STRICT: No fallback prices for portfolio valuation
                return {
                    'status': 'price_data_unavailable',
                    'message': 'Portfolio value cannot be calculated without live price data',
                    'error_details': str(e),
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0,
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': len(construction_result['holdings'])
                    },
                    'data_quality': {
                        'live_data_available': False,
                        'error_reason': str(e),
                        'data_policy': 'STRICT - Live prices required for portfolio valuation'
                    }
                }
            
            # Verify we have prices for all holdings
            missing_prices = []
            for symbol in symbols:
                if symbol not in current_prices:
                    missing_prices.append(symbol)
            
            if missing_prices:
                print(f"⚠️ Missing live prices for {len(missing_prices)} holdings: {missing_prices[:5]}")
                
                # STRICT: Cannot calculate portfolio value without all prices
                return {
                    'status': 'incomplete_price_data',
                    'message': f'Live prices missing for {len(missing_prices)} holdings',
                    'missing_prices': missing_prices,
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0,
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': len(construction_result['holdings'])
                    },
                    'data_quality': {
                        'live_data_available': False,
                        'missing_prices_count': len(missing_prices),
                        'data_policy': 'STRICT - All holdings must have live prices'
                    }
                }
            
            # Calculate comprehensive metrics with LIVE prices only
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
                        'annualized_return': float(holding_metrics.get('annualized_return', 0)),
                        'price_type': 'LIVE'  # Mark all prices as live
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
                        'live_data_available': True,
                        'price_source': price_data_source,
                        'construction_validation': construction_result.get('validation', {}),
                        'last_updated': datetime.now().isoformat(),
                        'all_prices_live': True,
                        'data_policy': 'STRICT - All calculations use live prices'
                    }
                }
                
            except Exception as metrics_error:
                print(f"⚠️ Could not calculate advanced metrics with live data: {metrics_error}")
                
                # STRICT: No fallback calculations, return error state
                return {
                    'status': 'calculation_error',
                    'message': 'Portfolio metrics calculation failed with live data',
                    'error_details': str(metrics_error),
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0,
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': len(construction_result['holdings'])
                    },
                    'data_quality': {
                        'live_data_available': True,
                        'calculation_error': str(metrics_error),
                        'data_policy': 'STRICT - No fallback calculations allowed'
                    }
                }
            
        except Exception as e:
            print(f"❌ Error getting portfolio status: {e}")
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
                    'live_data_available': False,
                    'error_type': 'SYSTEM_ERROR'
                }
            }
    
    # Helper methods remain the same...
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
                        'total_investment': order['value'],
                        'price_type': order.get('price_type', 'LIVE'),
                        'data_source': order.get('data_source', 'Unknown')
                    }
            
            portfolio_state = {
                'holdings': holdings,
                'last_updated': datetime.now().isoformat(),
                'csv_info': csv_info,
                'type': 'INITIAL_INVESTMENT',
                'data_quality': {
                    'all_prices_live': all(
                        order.get('price_type') == 'LIVE' for order in orders
                    ),
                    'creation_time': datetime.now().isoformat(),
                    'data_policy': 'STRICT - Live data only'
                }
            }
            
            with open(self.portfolio_state_file, 'w') as f:
                json.dump(portfolio_state, f, indent=2)
            
            print(f"💾 Portfolio state updated with {len(holdings)} holdings (all live prices)")
            
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
            
            # Add new entry with data quality info
            history.append({
                'timestamp': datetime.now().isoformat(),
                'csv_hash': csv_info.get('csv_hash', ''),
                'fetch_time': csv_info.get('fetch_time', ''),
                'data_quality': 'LIVE_PRICES_USED'
            })
            
            # Keep only last 100 entries
            history = history[-100:]
            
            with open(self.csv_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Error updating CSV history: {e}")

    def get_service_status(self) -> Dict:
        """Get comprehensive service status with data quality info"""
        # Get CSV service connection status
        csv_connection_status = {}
        if self.csv_service:
            try:
                csv_connection_status = self.csv_service.get_connection_status()
            except Exception as e:
                csv_connection_status = {'error': str(e)}
        
        # Get Zerodha auth status
        zerodha_auth_status = {}
        if self.zerodha_auth:
            try:
                zerodha_auth_status = self.zerodha_auth.get_auth_status()
            except Exception as e:
                zerodha_auth_status = {'error': str(e)}
        
        return {
            'csv_service': {
                'available': bool(self.csv_service),
                'connection_status': csv_connection_status,
                'data_policy': 'STRICT - Live prices only'
            },
            'zerodha_auth': {
                'available': bool(self.zerodha_auth),
                'status': zerodha_auth_status,
                'required_for': 'Live price data and order execution'
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
            },
            'data_quality_policy': {
                'live_data_required': True,
                'fallback_prices_disabled': True,
                'strict_validation': True,
                'description': 'All calculations require live market data from Zerodha API'
            }
        }

    def get_stock_prices_for_rebalancing(self, symbols: List[str]) -> Dict:
        """Get live stock prices specifically for rebalancing - STRICT mode"""
        try:
            print(f"🔍 Getting live prices for rebalancing: {len(symbols)} symbols")
            
            # Use CSV service's strict live price fetching
            live_prices = self.csv_service.get_live_prices(symbols)
            
            # Verify we got prices for all symbols
            missing_symbols = []
            for symbol in symbols:
                if symbol not in live_prices:
                    missing_symbols.append(symbol)
            
            if missing_symbols:
                raise Exception(f"PRICE_DATA_UNAVAILABLE: Missing live prices for {len(missing_symbols)} symbols: {missing_symbols[:5]}")
            
            print(f"✅ Retrieved live prices for all {len(symbols)} symbols")
            
            return {
                'success': True,
                'prices': live_prices,
                'symbols_count': len(symbols),
                'prices_count': len(live_prices),
                'data_source': 'Zerodha Live API',
                'data_quality': 'HIGH - All live prices',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get live prices for rebalancing: {e}")
            return {
                'success': False,
                'error': str(e),
                'prices': {},
                'symbols_count': len(symbols),
                'prices_count': 0,
                'data_source': 'UNAVAILABLE',
                'data_quality': 'FAILED - No live prices available'
            }

    def validate_investment_data_quality(self, data: Dict) -> Dict:
        """Validate that investment data meets strict quality requirements"""
        validation_result = {
            'is_valid': False,
            'validation_type': 'STRICT_LIVE_DATA_ONLY',
            'issues': [],
            'data_source': 'Unknown',
            'quality_level': 'INVALID'
        }
        
        try:
            # Check for data quality indicators
            data_quality = data.get('data_quality', {})
            price_data_status = data.get('price_data_status', {})
            
            # Must have live data available
            if not data_quality.get('live_data_available', False) and not price_data_status.get('live_prices_used', False):
                validation_result['issues'].append('Live data not available')
                return validation_result
            
            # Check data source
            data_source = data_quality.get('data_source') or price_data_status.get('market_data_source', 'Unknown')
            validation_result['data_source'] = data_source
            
            if 'Live' not in data_source:
                validation_result['issues'].append(f'Data source is not live: {data_source}')
                return validation_result
            
            # Check stocks data if present
            stocks = data.get('stocks', [])
            if stocks:
                non_live_stocks = []
                for stock in stocks:
                    if stock.get('price_type') != 'LIVE':
                        non_live_stocks.append(stock.get('symbol', 'Unknown'))
                
                if non_live_stocks:
                    validation_result['issues'].append(f'Non-live prices for stocks: {non_live_stocks[:5]}')
                    return validation_result
            
            # Check orders if present
            orders = data.get('orders', [])
            if orders:
                non_live_orders = []
                for order in orders:
                    if order.get('price_type') != 'LIVE':
                        non_live_orders.append(order.get('symbol', 'Unknown'))
                
                if non_live_orders:
                    validation_result['issues'].append(f'Non-live prices in orders: {non_live_orders[:5]}')
                    return validation_result
            
            # All checks passed
            validation_result['is_valid'] = True
            validation_result['quality_level'] = 'HIGH'
            validation_result['issues'] = []
            
            print(f"✅ Data quality validation passed - {data_source}")
            return validation_result
            
        except Exception as e:
            validation_result['issues'].append(f'Validation error: {str(e)}')
            return validation_result

    def create_investment_session_metadata(self, session_type: str, data_quality: Dict) -> Dict:
        """Create metadata for investment sessions with data quality tracking"""
        return {
            'session_id': f"{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'session_type': session_type,
            'created_at': datetime.now().isoformat(),
            'data_quality': {
                'live_data_used': data_quality.get('live_data_available', False),
                'data_source': data_quality.get('data_source', 'Unknown'),
                'quality_level': data_quality.get('data_quality_level', 'Unknown'),
                'validation_status': 'STRICT_VALIDATED',
                'market_open': data_quality.get('market_open', False),
                'zerodha_connected': data_quality.get('zerodha_connected', False)
            },
            'system_info': {
                'data_policy': 'STRICT - Live prices only',
                'fallback_disabled': True,
                'validation_level': 'HIGH'
            }
        }