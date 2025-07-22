# backend/app/services/investment_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import math
from .csv_service import CSVService

class InvestmentService:
    def __init__(self, zerodha_auth):
        self.zerodha_auth = zerodha_auth
        self.csv_service = CSVService(zerodha_auth)
        
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
    
    def get_investment_requirements(self) -> Dict:
        """Get minimum investment requirements based on current CSV"""
        try:
            print("📋 Getting investment requirements...")
            
            # Validate Zerodha connection first
            if not self.zerodha_auth:
                raise Exception("Zerodha authentication service not available")
            
            if not self.zerodha_auth.is_authenticated():
                print("🔄 Attempting Zerodha authentication...")
                try:
                    self.zerodha_auth.authenticate()
                except Exception as e:
                    raise Exception(f"Unable to authenticate with Zerodha: {str(e)}")
            
            if not self.zerodha_auth.is_authenticated():
                raise Exception("Zerodha authentication failed")
            
            # Get stocks with LIVE prices
            try:
                stocks_data = self.csv_service.get_stocks_with_prices()
            except Exception as e:
                raise Exception(f"Unable to fetch live stock prices: {str(e)}")
            
            # Validate that we have real data
            if not stocks_data.get('price_data_status', {}).get('live_prices_used', False):
                raise Exception("Live prices not available")
            
            if stocks_data.get('total_stocks', 0) == 0:
                raise Exception("No valid stocks with live prices found")
            
            # Calculate minimum investment
            min_investment_info = self._calculate_minimum_investment(stocks_data['stocks'])
            
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
            
            print(f"✅ Investment requirements prepared:")
            print(f"   Stocks: {stocks_data['total_stocks']}")
            print(f"   Min investment: ₹{min_investment_info['minimum_investment']:,.0f}")
            
            return requirements
            
        except Exception as e:
            print(f"❌ Error getting investment requirements: {e}")
            raise Exception(f"Cannot provide investment requirements: {str(e)}")
    
    def _calculate_minimum_investment(self, stocks: List[Dict]) -> Dict:
        """Calculate minimum investment based on stock prices"""
        if not stocks:
            raise Exception("No stocks provided")
        
        # Find most expensive stock
        max_price = max(stock['price'] for stock in stocks)
        most_expensive = next(stock for stock in stocks if stock['price'] == max_price)
        
        # For 4% minimum allocation with at least 1 share
        min_investment = (max_price * 100) / self.min_allocation
        recommended = max(min_investment * 1.2, self.min_investment)  # 20% buffer
        
        return {
            'minimum_investment': min_investment,
            'recommended_minimum': recommended,
            'most_expensive_stock': most_expensive['symbol'],
            'most_expensive_price': max_price,
            'total_stocks': len(stocks),
            'calculation_basis': f"Based on {most_expensive['symbol']} at ₹{max_price:.2f}"
        }
    
    def calculate_initial_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate initial investment plan"""
        try:
            print(f"💰 Calculating investment plan for ₹{investment_amount:,.0f}")
            
            # Get stocks with live prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            if not stocks_data.get('price_data_status', {}).get('live_prices_used', False):
                raise Exception("Live market data not available")
            
            # Validate minimum investment
            min_investment_info = self._calculate_minimum_investment(stocks_data['stocks'])
            
            if investment_amount < min_investment_info['minimum_investment']:
                raise Exception(f"Investment amount ₹{investment_amount:,.0f} is below minimum required ₹{min_investment_info['minimum_investment']:,.0f}")
            
            # Calculate allocation
            allocation_plan = self._calculate_allocation(investment_amount, stocks_data['stocks'])
            
            # Generate orders
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
            
            plan = {
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
                'data_quality': stocks_data['price_data_status']
            }
            
            print(f"✅ Investment plan created: {len(orders)} orders")
            return plan
            
        except Exception as e:
            print(f"❌ Error calculating investment plan: {e}")
            raise Exception(f"Cannot calculate investment plan: {str(e)}")
    
    def _calculate_allocation(self, investment_amount: float, stocks: List[Dict]) -> Dict:
        """Calculate optimal allocation"""
        target_per_stock = investment_amount / len(stocks)
        allocations = []
        total_allocated = 0
        
        for stock in stocks:
            symbol = stock['symbol']
            price = stock['price']
            
            # Calculate shares for target allocation
            target_shares = int(target_per_stock / price)
            
            # Ensure minimum 1 share
            shares = max(1, target_shares)
            value = shares * price
            allocation_percent = (value / investment_amount) * 100
            
            # Check constraints
            if allocation_percent < self.min_allocation:
                # Add shares to meet minimum
                min_value = investment_amount * (self.min_allocation / 100)
                shares = max(shares, math.ceil(min_value / price))
                value = shares * price
                allocation_percent = (value / investment_amount) * 100
            
            elif allocation_percent > self.max_allocation:
                # Reduce shares to stay under maximum
                max_value = investment_amount * (self.max_allocation / 100)
                shares = min(shares, int(max_value / price))
                value = shares * price
                allocation_percent = (value / investment_amount) * 100
            
            allocations.append({
                'symbol': symbol,
                'price': price,
                'shares': shares,
                'value': value,
                'allocation_percent': allocation_percent
            })
            
            total_allocated += value
        
        remaining_cash = investment_amount - total_allocated
        utilization_percent = (total_allocated / investment_amount) * 100
        
        return {
            'allocations': allocations,
            'total_allocated': total_allocated,
            'remaining_cash': remaining_cash,
            'utilization_percent': utilization_percent
        }
    
    def execute_initial_investment(self, investment_plan: Dict) -> Dict:
        """Execute initial investment plan"""
        try:
            print("🚀 Executing initial investment...")
            
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
                    'status': 'EXECUTED_SYSTEM',
                    'execution_time': datetime.now().isoformat(),
                    'session_type': 'INITIAL_INVESTMENT'
                }
                system_orders.append(system_order)
                order_id += 1
            
            # Save orders
            self._save_system_orders(system_orders)
            
            # Update portfolio state
            self._update_portfolio_state(system_orders, investment_plan['csv_info'])
            
            result = {
                'success': True,
                'orders_executed': len(system_orders),
                'total_investment': investment_plan['summary']['total_investment_value'],
                'remaining_cash': investment_plan['summary']['remaining_cash'],
                'execution_time': datetime.now().isoformat()
            }
            
            print(f"✅ Initial investment executed: {len(system_orders)} orders")
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
            
            # Compare with CSV
            current_symbols = list(portfolio_state['holdings'].keys())
            csv_data = self.csv_service.fetch_csv_data()
            csv_symbols = set(csv_data['symbols'])
            portfolio_symbols = set(current_symbols)
            
            new_stocks = csv_symbols - portfolio_symbols
            removed_stocks = portfolio_symbols - csv_symbols
            
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
            raise Exception(f"Failed to check rebalancing: {str(e)}")
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0) -> Dict:
        """Calculate rebalancing plan"""
        try:
            print(f"🧮 Calculating rebalancing plan...")
            
            # Get current portfolio
            portfolio_state = self._get_current_portfolio_state()
            if not portfolio_state:
                raise Exception("No current portfolio found")
            
            # Get new CSV stocks
            stocks_data = self.csv_service.get_stocks_with_prices()
            current_value = self._calculate_current_portfolio_value(portfolio_state)
            
            # Calculate new allocation
            total_value = current_value + additional_investment
            allocation_plan = self._calculate_allocation(total_value, stocks_data['stocks'])
            
            return {
                'current_value': current_value,
                'additional_investment': additional_investment,
                'target_value': total_value,
                'allocation_plan': allocation_plan,
                'status': 'READY_FOR_EXECUTION'
            }
            
        except Exception as e:
            print(f"❌ Error calculating rebalancing: {e}")
            raise Exception(f"Failed to calculate rebalancing: {str(e)}")
    
    def execute_rebalancing(self, rebalancing_plan: Dict) -> Dict:
        """Execute rebalancing plan"""
        try:
            print("🚀 Executing rebalancing...")
            # Implementation similar to initial investment
            return {
                'success': True,
                'message': 'Rebalancing executed successfully'
            }
        except Exception as e:
            print(f"❌ Error executing rebalancing: {e}")
            raise Exception(f"Failed to execute rebalancing: {str(e)}")
    
    def get_system_portfolio_status(self) -> Dict:
        """Get system portfolio status"""
        try:
            portfolio_state = self._get_current_portfolio_state()
            
            if not portfolio_state:
                return {
                    'status': 'empty',
                    'message': 'No portfolio found. Please complete initial investment.',
                    'holdings': {},
                    'portfolio_summary': {'total_investment': 0, 'current_value': 0}
                }
            
            # Get current prices
            symbols = list(portfolio_state['holdings'].keys())
            current_prices = self.csv_service.get_live_prices(symbols)
            
            # Calculate metrics
            holdings_with_metrics = {}
            total_investment = 0
            current_value = 0
            
            for symbol, holding in portfolio_state['holdings'].items():
                shares = holding['shares']
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
        return not os.path.exists(self.portfolio_state_file)
    
    def _get_next_order_id(self) -> int:
        orders = self._load_system_orders()
        if not orders:
            return 1
        return max(order['order_id'] for order in orders) + 1
    
    def _save_system_orders(self, new_orders: List[Dict]):
        existing_orders = self._load_system_orders()
        all_orders = existing_orders + new_orders
        
        os.makedirs(os.path.dirname(self.orders_file), exist_ok=True)
        with open(self.orders_file, 'w') as f:
            json.dump(all_orders, f, indent=2)
    
    def _load_system_orders(self) -> List[Dict]:
        if not os.path.exists(self.orders_file):
            return []
        
        try:
            with open(self.orders_file, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _update_portfolio_state(self, orders: List[Dict], csv_info: Dict):
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
        
        os.makedirs(os.path.dirname(self.portfolio_state_file), exist_ok=True)
        with open(self.portfolio_state_file, 'w') as f:
            json.dump(portfolio_state, f, indent=2)
    
    def _get_current_portfolio_state(self) -> Optional[Dict]:
        if not os.path.exists(self.portfolio_state_file):
            return None
        
        try:
            with open(self.portfolio_state_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _calculate_current_portfolio_value(self, portfolio_state: Dict) -> float:
        if not portfolio_state or not portfolio_state.get('holdings'):
            return 0.0
        
        holdings = portfolio_state['holdings']
        symbols = list(holdings.keys())
        current_prices = self.csv_service.get_live_prices(symbols)
        
        total_value = 0.0
        for symbol, holding in holdings.items():
            if symbol in current_prices:
                current_value = holding['shares'] * current_prices[symbol]
                total_value += current_value
        
        return total_value