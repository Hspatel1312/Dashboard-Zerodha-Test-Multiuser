# backend/app/services/portfolio_construction_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
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
        print("[INFO] Constructing portfolio from order history...")
        
        if not all_orders:
            print("   [WARNING] No orders provided")
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
        
        # Sort orders by execution time with better error handling
        try:
            sorted_orders = sorted(
                all_orders, 
                key=lambda x: self._parse_date_safely(x.get('execution_time', ''))
            )
            print(f"   [INFO] Processing {len(sorted_orders)} orders...")
        except Exception as e:
            print(f"   [WARNING] Error sorting orders: {e}")
            sorted_orders = all_orders
        
        # Track order processing statistics
        processed_count = 0
        error_count = 0
        
        for order_idx, order in enumerate(sorted_orders):
            try:
                # Extract order data with better validation
                symbol = str(order.get('symbol', f'UNKNOWN_{order_idx}')).strip()
                action = str(order.get('action', 'BUY')).upper().strip()
                
                # Handle both 'shares' and 'quantity' fields
                shares = int(order.get('shares', order.get('quantity', 0)))
                
                # Handle price with validation
                price_value = order.get('price', 0)
                if isinstance(price_value, str):
                    price = float(price_value.replace('Rs.', '').replace(',', ''))
                else:
                    price = float(price_value)
                
                # Calculate value with fallback
                value_from_order = order.get('value')
                if value_from_order:
                    if isinstance(value_from_order, str):
                        value = float(value_from_order.replace('Rs.', '').replace(',', ''))
                    else:
                        value = float(value_from_order)
                else:
                    value = shares * price
                
                execution_time = order.get('execution_time', datetime.now().isoformat())
                
                # Validate data
                if shares <= 0 or price <= 0:
                    print(f"   [WARNING] Invalid data for order {order_idx}: shares={shares}, price={price}")
                    error_count += 1
                    continue
                
                print(f"   [INFO] Processing: {symbol} {action} {shares} @ Rs.{price:.2f} = Rs.{value:.2f}")
                
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
                
                if action == 'BUY':
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
                    
                    print(f"      [SUCCESS] BUY: {symbol} now has {holding['total_shares']} shares at avg Rs.{holding['avg_price']:.2f}")
                    
                elif action == 'SELL':
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
                            print(f"      [WARNING] SELL: {symbol} position closed")
                    else:
                        print(f"      [WARNING] SELL: Insufficient shares for {symbol} (have {holding['total_shares']}, trying to sell {shares})")
                    
                    total_cash_flow -= value  # Cash inflow
                
                # Record transaction with better data
                transaction = {
                    'date': execution_time,
                    'action': action,
                    'shares': shares,
                    'price': price,
                    'value': value,
                    'order_id': order.get('order_id', f'order_{order_idx}')
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
                    'value': value,
                    'order_id': order.get('order_id', f'order_{order_idx}')
                })
                
                processed_count += 1
                
            except Exception as e:
                print(f"   [ERROR] Error processing order {order_idx}: {e}")
                print(f"      Order data: {order}")
                error_count += 1
                continue
        
        # Remove positions with zero or negative shares
        active_holdings = {}
        for symbol, holding in holdings.items():
            if holding['total_shares'] > 0:
                active_holdings[symbol] = holding
                print(f"   [INFO] Active holding: {symbol} - {holding['total_shares']} shares, Rs.{holding['total_investment']:,.2f} invested")
            else:
                print(f"   [INFO] Removing zero position: {symbol}")
        
        # Determine date range
        first_order_date = None
        last_order_date = None
        
        if sorted_orders:
            try:
                first_order_date = sorted_orders[0].get('execution_time')
                last_order_date = sorted_orders[-1].get('execution_time')
            except Exception as e:
                print(f"   [WARNING] Error getting date range: {e}")
        
        construction_result = {
            'holdings': active_holdings,
            'order_timeline': order_timeline,
            'total_cash_outflow': total_cash_flow,
            'first_order_date': first_order_date,
            'last_order_date': last_order_date,
            'total_orders': len(all_orders),
            'processed_orders': processed_count,
            'error_orders': error_count
        }
        
        print(f"   [SUCCESS] Portfolio construction complete:")
        print(f"      Total orders processed: {processed_count}/{len(all_orders)}")
        print(f"      Errors encountered: {error_count}")
        print(f"      Active holdings: {len(active_holdings)}")
        print(f"      Total cash outflow: Rs.{total_cash_flow:,.2f}")
        print(f"      Date range: {first_order_date} to {last_order_date}")
        
        return construction_result
    
    def _parse_date_safely(self, date_str: str) -> datetime:
        """Safely parse date string with multiple format support"""
        if not date_str:
            return datetime.now()
        
        try:
            # Try ISO format first
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', ''))
            
            # Try other common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If all fail, return current time
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def validate_portfolio_construction(self, construction_result: Dict) -> Dict:
        """
        Validate the constructed portfolio for consistency
        """
        print("[INFO] Validating portfolio construction...")
        
        holdings = construction_result.get('holdings', {})
        validation_results = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'summary': {},
            'data_quality': {}
        }
        
        total_investment = 0
        total_shares = 0
        price_anomalies = 0
        
        for symbol, holding in holdings.items():
            try:
                shares = holding.get('total_shares', 0)
                investment = holding.get('total_investment', 0)
                avg_price = holding.get('avg_price', 0)
                transactions = holding.get('transactions', [])
                
                # Validate calculations
                expected_investment = shares * avg_price
                investment_diff = abs(investment - expected_investment)
                
                if investment_diff > 1:  # Allow small rounding errors
                    validation_results['warnings'].append(
                        f"{symbol}: Investment calculation mismatch (Expected: Rs.{expected_investment:.2f}, Actual: Rs.{investment:.2f})"
                    )
                
                # Check for negative values
                if shares < 0:
                    validation_results['errors'].append(f"{symbol}: Negative shares ({shares})")
                    validation_results['is_valid'] = False
                
                if investment < 0:
                    validation_results['errors'].append(f"{symbol}: Negative investment (Rs.{investment:.2f})")
                    validation_results['is_valid'] = False
                
                # Check for unrealistic prices
                if avg_price > 50000:  # More than Rs.50,000 per share seems unusual
                    validation_results['warnings'].append(f"{symbol}: Unusually high average price (Rs.{avg_price:.2f})")
                    price_anomalies += 1
                
                if avg_price < 1:  # Less than Rs.1 per share seems unusual
                    validation_results['warnings'].append(f"{symbol}: Unusually low average price (Rs.{avg_price:.2f})")
                    price_anomalies += 1
                
                # Check for missing transaction data
                if not transactions:
                    validation_results['warnings'].append(f"{symbol}: No transaction history found")
                
                # Validate transaction consistency
                calculated_shares = sum(
                    t['shares'] if t['action'] == 'BUY' else -t['shares'] 
                    for t in transactions
                )
                
                if abs(calculated_shares - shares) > 0:
                    validation_results['warnings'].append(
                        f"{symbol}: Transaction shares ({calculated_shares}) don't match holding shares ({shares})"
                    )
                
                total_investment += investment
                total_shares += shares
                
            except Exception as e:
                validation_results['errors'].append(f"{symbol}: Error validating holding - {str(e)}")
                validation_results['is_valid'] = False
        
        # Calculate data quality metrics
        total_orders = construction_result.get('total_orders', 0)
        processed_orders = construction_result.get('processed_orders', 0)
        error_orders = construction_result.get('error_orders', 0)
        
        processing_success_rate = (processed_orders / total_orders * 100) if total_orders > 0 else 0
        
        validation_results['data_quality'] = {
            'processing_success_rate': processing_success_rate,
            'total_orders': total_orders,
            'processed_orders': processed_orders,
            'error_orders': error_orders,
            'price_anomalies': price_anomalies
        }
        
        validation_results['summary'] = {
            'total_holdings': len(holdings),
            'total_investment': total_investment,
            'total_shares': total_shares,
            'avg_investment_per_stock': total_investment / len(holdings) if holdings else 0,
            'warnings_count': len(validation_results['warnings']),
            'errors_count': len(validation_results['errors'])
        }
        
        # Overall validation status
        if validation_results['errors']:
            validation_results['is_valid'] = False
            print(f"   [ERROR] {len(validation_results['errors'])} critical errors found")
        
        if validation_results['warnings']:
            print(f"   [WARNING] {len(validation_results['warnings'])} warnings found")
        
        if validation_results['is_valid'] and not validation_results['warnings']:
            print(f"   [SUCCESS] Portfolio construction validation passed perfectly")
        elif validation_results['is_valid']:
            print(f"   [SUCCESS] Portfolio construction validation passed with warnings")
        
        print(f"   [INFO] Data quality: {processing_success_rate:.1f}% order processing success rate")
        
        return validation_results