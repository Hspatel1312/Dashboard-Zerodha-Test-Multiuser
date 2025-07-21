# backend/app/services/portfolio_construction_service.py
from typing import Dict, List, Optional
from datetime import datetime
import json

class PortfolioConstructionService:
    """
    Service responsible for constructing portfolio from order history
    """
    
    def __init__(self):
        pass
    
    def construct_portfolio_from_orders(self, all_orders: List[Dict]) -> Dict:
        """
        Construct current portfolio state from all orders placed till date
        
        Returns:
        {
            'holdings': Dict[symbol, holding_data],
            'order_timeline': List[order_data],
            'total_cash_outflow': float,
            'first_order_date': str,
            'last_order_date': str,
            'total_orders': int
        }
        """
        print("🏗️ Constructing portfolio from order history...")
        
        if not all_orders:
            print("   ⚠️ No orders provided")
            return {
                'holdings': {},
                'order_timeline': [],
                'total_cash_outflow': 0,
                'first_order_date': None,
                'last_order_date': None,
                'total_orders': 0
            }
        
        holdings = {}
        order_timeline = []
        total_cash_flow = 0
        
        # Sort orders by execution time
        try:
            sorted_orders = sorted(all_orders, key=lambda x: x.get('execution_time', ''))
            print(f"   📊 Processing {len(sorted_orders)} orders...")
        except Exception as e:
            print(f"   ⚠️ Error sorting orders: {e}")
            sorted_orders = all_orders
        
        for order_idx, order in enumerate(sorted_orders):
            try:
                symbol = order.get('symbol', f'UNKNOWN_{order_idx}')
                action = order.get('action', 'BUY')
                shares = int(order.get('shares', 0))
                price = float(order.get('price', 0))
                value = float(order.get('value', shares * price))
                execution_time = order.get('execution_time', datetime.now().isoformat())
                
                print(f"   📝 Processing: {symbol} {action} {shares} @ ₹{price:.2f}")
                
                # Initialize holding if not exists
                if symbol not in holdings:
                    holdings[symbol] = {
                        'total_shares': 0,
                        'total_investment': 0.0,
                        'avg_price': 0.0,
                        'transactions': [],
                        'first_purchase_date': None,
                        'last_transaction_date': None
                    }
                
                holding = holdings[symbol]
                
                if action.upper() == 'BUY':
                    # Add to position
                    old_total_investment = holding['total_investment']
                    old_total_shares = holding['total_shares']
                    
                    holding['total_shares'] += shares
                    holding['total_investment'] += value
                    
                    # Calculate new average price
                    if holding['total_shares'] > 0:
                        holding['avg_price'] = holding['total_investment'] / holding['total_shares']
                    
                    # Set first purchase date
                    if holding['first_purchase_date'] is None:
                        holding['first_purchase_date'] = execution_time
                    
                    total_cash_flow += value  # Cash outflow
                    
                    print(f"      ✅ BUY: {symbol} now has {holding['total_shares']} shares at avg ₹{holding['avg_price']:.2f}")
                    
                elif action.upper() == 'SELL':
                    # Reduce position
                    if holding['total_shares'] >= shares:
                        holding['total_shares'] -= shares
                        
                        if holding['total_shares'] > 0:
                            # Reduce investment proportionally (maintain avg price)
                            holding['total_investment'] = holding['total_shares'] * holding['avg_price']
                        else:
                            # Position closed
                            holding['total_investment'] = 0.0
                            holding['avg_price'] = 0.0
                            print(f"      📉 SELL: {symbol} position closed")
                    else:
                        print(f"      ⚠️ SELL: Insufficient shares for {symbol} (have {holding['total_shares']}, trying to sell {shares})")
                    
                    total_cash_flow -= value  # Cash inflow
                
                # Record transaction
                transaction = {
                    'date': execution_time,
                    'action': action,
                    'shares': shares,
                    'price': price,
                    'value': value
                }
                holding['transactions'].append(transaction)
                holding['last_transaction_date'] = execution_time
                
                # Record for timeline
                order_timeline.append({
                    'date': execution_time,
                    'action': action,
                    'symbol': symbol,
                    'shares': shares,
                    'price': price,
                    'value': value
                })
                
            except Exception as e:
                print(f"   ❌ Error processing order {order_idx}: {e}")
                print(f"      Order data: {order}")
                continue
        
        # Remove positions with zero or negative shares
        active_holdings = {}
        for symbol, holding in holdings.items():
            if holding['total_shares'] > 0:
                active_holdings[symbol] = holding
                print(f"   📊 Active holding: {symbol} - {holding['total_shares']} shares, ₹{holding['total_investment']:,.2f} invested")
            else:
                print(f"   🗑️ Removing zero position: {symbol}")
        
        # Determine date range
        first_order_date = None
        last_order_date = None
        
        if sorted_orders:
            try:
                first_order_date = sorted_orders[0].get('execution_time')
                last_order_date = sorted_orders[-1].get('execution_time')
            except Exception as e:
                print(f"   ⚠️ Error getting date range: {e}")
        
        construction_result = {
            'holdings': active_holdings,
            'order_timeline': order_timeline,
            'total_cash_outflow': total_cash_flow,
            'first_order_date': first_order_date,
            'last_order_date': last_order_date,
            'total_orders': len(all_orders)
        }
        
        print(f"   ✅ Portfolio construction complete:")
        print(f"      Total orders processed: {len(all_orders)}")
        print(f"      Active holdings: {len(active_holdings)}")
        print(f"      Total cash outflow: ₹{total_cash_flow:,.2f}")
        print(f"      Date range: {first_order_date} to {last_order_date}")
        
        return construction_result
    
    def validate_portfolio_construction(self, construction_result: Dict) -> Dict:
        """
        Validate the constructed portfolio for consistency
        """
        print("🔍 Validating portfolio construction...")
        
        holdings = construction_result.get('holdings', {})
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'summary': {}
        }
        
        total_investment = 0
        total_shares = 0
        
        for symbol, holding in holdings.items():
            try:
                shares = holding.get('total_shares', 0)
                investment = holding.get('total_investment', 0)
                avg_price = holding.get('avg_price', 0)
                
                # Validate calculations
                expected_investment = shares * avg_price
                investment_diff = abs(investment - expected_investment)
                
                if investment_diff > 1:  # Allow small rounding errors
                    validation_results['warnings'].append(
                        f"{symbol}: Investment calculation mismatch (Expected: ₹{expected_investment:.2f}, Actual: ₹{investment:.2f})"
                    )
                
                # Check for negative values
                if shares < 0:
                    validation_results['errors'].append(f"{symbol}: Negative shares ({shares})")
                    validation_results['is_valid'] = False
                
                if investment < 0:
                    validation_results['errors'].append(f"{symbol}: Negative investment (₹{investment:.2f})")
                    validation_results['is_valid'] = False
                
                # Check for missing transaction data
                transactions = holding.get('transactions', [])
                if not transactions:
                    validation_results['warnings'].append(f"{symbol}: No transaction history found")
                
                total_investment += investment
                total_shares += shares
                
            except Exception as e:
                validation_results['errors'].append(f"{symbol}: Error validating holding - {str(e)}")
                validation_results['is_valid'] = False
        
        validation_results['summary'] = {
            'total_holdings': len(holdings),
            'total_investment': total_investment,
            'total_shares': total_shares,
            'avg_investment_per_stock': total_investment / len(holdings) if holdings else 0
        }
        
        if validation_results['warnings']:
            print(f"   ⚠️ {len(validation_results['warnings'])} warnings found")
        
        if validation_results['errors']:
            print(f"   ❌ {len(validation_results['errors'])} errors found")
            validation_results['is_valid'] = False
        else:
            print(f"   ✅ Portfolio construction validation passed")
        
        return validation_results