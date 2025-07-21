# backend/app/services/investment_service.py
from typing import Dict, List, Optional
from datetime import datetime
import json
import os
from .csv_service import CSVService
from .investment_calculator import InvestmentCalculator

class InvestmentService:
    def __init__(self, zerodha_auth):
        self.zerodha_auth = zerodha_auth
        self.csv_service = CSVService(zerodha_auth)
        self.calculator = InvestmentCalculator()
        
        # File paths for storing system state
        self.orders_file = "system_orders.json"
        self.portfolio_state_file = "system_portfolio_state.json"
        self.csv_history_file = "csv_history.json"
    
    def get_investment_requirements(self) -> Dict:
        """
        Get minimum investment requirements based on current CSV
        This is for first-time setup
        """
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
        """
        Calculate initial investment plan for given amount
        """
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
        """
        Execute initial investment (store orders, don't place on Zerodha yet)
        """
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
        """
        Check if rebalancing is needed by comparing current CSV with system portfolio
        """
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
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0.0) -> Dict:
        """
        Calculate rebalancing plan for portfolio transition
        """
        try:
            print(f"⚖️ Calculating rebalancing plan...")
            print(f"   Additional investment: ₹{additional_investment:,.0f}")
            
            # Get current portfolio state and value
            portfolio_state = self._get_current_portfolio_state()
            current_portfolio_value = self._calculate_current_portfolio_value(portfolio_state)
            
            # Total value for rebalancing
            total_investment = current_portfolio_value + additional_investment
            
            print(f"   Current portfolio: ₹{current_portfolio_value:,.0f}")
            print(f"   Total for rebalancing: ₹{total_investment:,.0f}")
            
            # Get new CSV stocks with prices
            stocks_data = self.csv_service.get_stocks_with_prices()
            
            # Calculate new optimal allocation
            new_allocation = self.calculator.calculate_optimal_allocation(
                total_investment, stocks_data['stocks']
            )
            
            # Generate transition orders
            transition_orders = self._calculate_transition_orders(
                portfolio_state, new_allocation, stocks_data['stocks']
            )
            
            rebalancing_plan = {
                'current_portfolio_value': current_portfolio_value,
                'additional_investment': additional_investment,
                'total_investment': total_investment,
                'new_allocation': new_allocation,
                'transition_orders': transition_orders,
                'csv_info': stocks_data['csv_info'],
                'rebalancing_summary': self._summarize_rebalancing(transition_orders)
            }
            
            print(f"✅ Rebalancing plan calculated:")
            print(f"   Buy orders: {rebalancing_plan['rebalancing_summary']['buy_orders']}")
            print(f"   Sell orders: {rebalancing_plan['rebalancing_summary']['sell_orders']}")
            print(f"   Net cash required: ₹{rebalancing_plan['rebalancing_summary']['net_cash_required']:,.0f}")
            
            return rebalancing_plan
            
        except Exception as e:
            print(f"❌ Error calculating rebalancing plan: {e}")
            raise Exception(f"Failed to calculate rebalancing plan: {str(e)}")
    
    # Helper methods continue below...
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
    
    def _calculate_transition_orders(self, current_portfolio: Dict, new_allocation: Dict, stocks_data: List[Dict]) -> List[Dict]:
        """Calculate orders needed to transition from current to new portfolio"""
        orders = []
        current_holdings = current_portfolio.get('holdings', {}) if current_portfolio else {}
        
        # Create price lookup
        price_lookup = {stock['symbol']: stock['price'] for stock in stocks_data}
        
        # Track all symbols (current + new)
        all_symbols = set(current_holdings.keys())
        new_symbols = {alloc['symbol'] for alloc in new_allocation['allocations']}
        all_symbols.update(new_symbols)
        
        for symbol in all_symbols:
            current_shares = current_holdings.get(symbol, {}).get('shares', 0)
            
            # Find target shares from new allocation
            target_shares = 0
            for alloc in new_allocation['allocations']:
                if alloc['symbol'] == symbol:
                    target_shares = alloc['shares']
                    break
            
            shares_diff = target_shares - current_shares
            
            if shares_diff != 0 and symbol in price_lookup:
                price = price_lookup[symbol]
                
                order = {
                    'symbol': symbol,
                    'action': 'BUY' if shares_diff > 0 else 'SELL',
                    'current_shares': current_shares,
                    'target_shares': target_shares,
                    'shares': abs(shares_diff),
                    'price': price,
                    'value': abs(shares_diff) * price
                }
                orders.append(order)
        
        return orders
    
    def _summarize_rebalancing(self, transition_orders: List[Dict]) -> Dict:
        """Summarize rebalancing orders"""
        buy_orders = [o for o in transition_orders if o['action'] == 'BUY']
        sell_orders = [o for o in transition_orders if o['action'] == 'SELL']
        
        total_buy_value = sum(o['value'] for o in buy_orders)
        total_sell_value = sum(o['value'] for o in sell_orders)
        
        return {
            'total_orders': len(transition_orders),
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'total_buy_value': total_buy_value,
            'total_sell_value': total_sell_value,
            'net_cash_required': total_buy_value - total_sell_value,
            'buy_order_details': buy_orders,
            'sell_order_details': sell_orders
        }
    
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