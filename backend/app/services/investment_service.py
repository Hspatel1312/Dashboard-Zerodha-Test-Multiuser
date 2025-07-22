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
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0) -> Dict:
        """Calculate rebalancing plan with optional additional investment"""
        try:
            print(f"🧮 Calculating rebalancing plan with additional investment: ₹{additional_investment:,.0f}")
            
            # Get current portfolio state
            portfolio_state = self._get_current_portfolio_state()
            if not portfolio_state:
                raise Exception("No current portfolio found")
            
            # Get new CSV stocks
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Calculate current portfolio value
            current_value = self._calculate_current_portfolio_value(portfolio_state)
            
            # Total value to allocate = current value + additional investment
            total_value = current_value + additional_investment
            
            # Calculate target allocation (equal weight)
            target_per_stock = total_value / len(stocks_data['stocks'])
            
            # Generate rebalancing orders
            orders = []
            for stock in stocks_data['stocks']:
                symbol = stock['symbol']
                current_price = stock['price']
                
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
                        'price': current_price,
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
                'status': 'READY_FOR_EXECUTION' if net_cash_required <= additional_investment else 'INSUFFICIENT_CASH'
            }
            
            print(f"✅ Rebalancing plan calculated:")
            print(f"   Orders: {len(orders)} total ({len(buy_orders)} BUY, {len(sell_orders)} SELL)")
            print(f"   Net cash required: ₹{net_cash_required:,.0f}")
            print(f"   Status: {rebalancing_plan['status']}")
            
            return rebalancing_plan
            
        except Exception as e:
            print(f"❌ Error calculating rebalancing plan: {e}")
            raise Exception(f"Failed to calculate rebalancing plan: {str(e)}")
    
    def execute_rebalancing(self, rebalancing_plan: Dict) -> Dict:
        """Execute rebalancing plan"""
        try:
            print(f"🚀 Executing rebalancing plan...")
            
            # Create system orders
            system_orders = []
            order_id = self._get_next_order_id()
            
            for order in rebalancing_plan['orders']:
                system_order = {
                    'order_id': order_id,
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order['price'],
                    'value': order['value'],
                    'allocation_percent': order['allocation_percent'],
                    'status': 'EXECUTED_SYSTEM',
                    'execution_time': datetime.now().isoformat(),
                    'session_type': 'REBALANCING'
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
                'execution_time': datetime.now().isoformat()
            }
            
            print(f"✅ Rebalancing executed:")
            print(f"   Orders stored: {len(system_orders)}")
            print(f"   Net investment: ₹{execution_result['net_investment']:,.0f}")
            
            return execution_result
            
        except Exception as e:
            print(f"❌ Error executing rebalancing: {e}")
            raise Exception(f"Failed to execute rebalancing: {str(e)}")
    
    def get_system_portfolio_status(self) -> Dict:
        """
        Get comprehensive system portfolio status with advanced metrics
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
                print(f"⚠️ Portfolio construction validation failed: {validation['errors']}")
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
                
                # Ensure all symbols have prices (use avg_price as fallback)
                for symbol in symbols:
                    if symbol not in current_prices:
                        current_prices[symbol] = holdings[symbol]['avg_price']
                        print(f"   🔄 Using avg price for {symbol}: ₹{current_prices[symbol]:.2f}")
                        
            except Exception as e:
                print(f"⚠️ Could not get live prices: {e}, using average prices")
                current_prices = {symbol: holding['avg_price'] for symbol, holding in holdings.items()}
            
            # Step 3: Calculate comprehensive metrics using dedicated service
            print("🔧 Step 3: Calculating comprehensive metrics...")
            try:
                portfolio_metrics = self.metrics_calculator.calculate_comprehensive_metrics(
                    holdings, current_prices, portfolio_construction
                )
            except Exception as e:
                print(f"❌ Error calculating metrics: {e}")
                # Create fallback metrics
                portfolio_metrics = self._create_fallback_metrics(holdings, current_prices, portfolio_construction)
            
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
    
    def _create_fallback_metrics(self, holdings: Dict, current_prices: Dict, construction_data: Dict) -> Dict:
        """Create fallback metrics when main calculation fails"""
        print("   🔄 Creating fallback metrics...")
        
        try:
            # Calculate basic metrics
            total_investment = 0
            current_value = 0
            holdings_with_metrics = {}
            
            for symbol, holding in holdings.items():
                shares = holding.get('total_shares', 0)
                avg_price = holding.get('avg_price', 0)
                investment_value = holding.get('total_investment', 0)
                current_price = current_prices.get(symbol, avg_price)
                
                current_holding_value = shares * current_price
                absolute_return = current_holding_value - investment_value
                percentage_return = (absolute_return / investment_value) * 100 if investment_value > 0 else 0
                
                holdings_with_metrics[symbol] = {
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'investment_value': investment_value,
                    'current_value': current_holding_value,
                    'absolute_return': absolute_return,
                    'percentage_return': percentage_return,
                    'allocation_percent': 0,  # Will calculate later
                    'days_held': 30,  # Default
                    'years_held': 30/365.25,
                    'annualized_return': percentage_return,
                    'first_purchase_date': construction_data.get('first_order_date', ''),
                    'last_transaction_date': construction_data.get('last_order_date', ''),
                    'transaction_count': 1
                }
                
                total_investment += investment_value
                current_value += current_holding_value
            
            # Calculate allocation percentages
            for holding in holdings_with_metrics.values():
                holding['allocation_percent'] = (
                    (holding['current_value'] / current_value) * 100 
                    if current_value > 0 else 0
                )
            
            # Calculate basic metrics
            total_returns = current_value - total_investment
            returns_percentage = (total_returns / total_investment) * 100 if total_investment > 0 else 0
            
            # Simple CAGR calculation
            try:
                first_order_date = construction_data.get('first_order_date')
                if first_order_date:
                    if 'T' in first_order_date:
                        first_date = datetime.fromisoformat(first_order_date.replace('Z', ''))
                    else:
                        first_date = datetime.strptime(first_order_date, '%Y-%m-%d')
                    
                    days_held = max(1, (datetime.now() - first_date).days)
                    years_held = max(days_held / 365.25, 1/365.25)
                    
                    if total_investment > 0 and current_value > 0:
                        cagr = ((current_value / total_investment) ** (1 / years_held) - 1) * 100
                        cagr = max(-99.9, min(999.9, cagr))
                    else:
                        cagr = 0
                else:
                    days_held = 30
                    years_held = 30/365.25
                    cagr = returns_percentage
            except:
                days_held = 30
                years_held = 30/365.25
                cagr = returns_percentage
            
            # Find best/worst performers
            if holdings_with_metrics:
                best_symbol = max(holdings_with_metrics.keys(), 
                                 key=lambda s: holdings_with_metrics[s]['percentage_return'])
                worst_symbol = min(holdings_with_metrics.keys(), 
                                  key=lambda s: holdings_with_metrics[s]['percentage_return'])
                
                best_performer = {
                    'symbol': best_symbol,
                    'percentage_return': holdings_with_metrics[best_symbol]['percentage_return']
                }
                worst_performer = {
                    'symbol': worst_symbol,
                    'percentage_return': holdings_with_metrics[worst_symbol]['percentage_return']
                }
            else:
                best_performer = None
                worst_performer = None
            
            return {
                'holdings_with_metrics': holdings_with_metrics,
                'total_investment': total_investment,
                'current_value': current_value,
                'total_returns': total_returns,
                'returns_percentage': returns_percentage,
                'cagr': cagr,
                'investment_period_days': days_held,
                'investment_period_years': years_held,
                'best_performer': best_performer,
                'worst_performer': worst_performer,
                'avg_return': returns_percentage,
                'volatility_score': 0.0,
                'sharpe_ratio': 0.0,
                'allocation_stats': {
                    'target_allocation': 100 / len(holdings_with_metrics) if holdings_with_metrics else 0,
                    'min_allocation': min([h['allocation_percent'] for h in holdings_with_metrics.values()]) if holdings_with_metrics else 0,
                    'max_allocation': max([h['allocation_percent'] for h in holdings_with_metrics.values()]) if holdings_with_metrics else 0,
                    'avg_allocation': sum([h['allocation_percent'] for h in holdings_with_metrics.values()]) / len(holdings_with_metrics) if holdings_with_metrics else 0
                },
                'allocation_deviation': 0.0,
                'rebalancing_needed': False
            }
            
        except Exception as e:
            print(f"   ❌ Error creating fallback metrics: {e}")
            return {
                'holdings_with_metrics': {},
                'total_investment': 0,
                'current_value': 0,
                'total_returns': 0,
                'returns_percentage': 0,
                'cagr': 0,
                'investment_period_days': 1,
                'investment_period_years': 1/365.25,
                'best_performer': None,
                'worst_performer': None,
                'avg_return': 0,
                'volatility_score': 0.0,
                'sharpe_ratio': 0.0,
                'allocation_stats': {'target_allocation': 0, 'min_allocation': 0, 'max_allocation': 0, 'avg_allocation': 0},
                'allocation_deviation': 0.0,
                'rebalancing_needed': False
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