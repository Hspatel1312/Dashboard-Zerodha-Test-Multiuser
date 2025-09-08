# backend/app/services/portfolio_construction_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

# Foundation imports
from .base.base_service import BaseService
from .base.file_operations_mixin import GlobalFileOperationsMixin
from .utils.error_handler import ErrorHandler
from .utils.date_time_utils import DateTimeUtils
from .utils.logger import LoggerFactory

class PortfolioConstructionService(GlobalFileOperationsMixin, BaseService):
    """
    Service responsible for constructing portfolio from order history
    """
    
    def __init__(self):
        BaseService.__init__(self, service_name="portfolio_construction_service")
        GlobalFileOperationsMixin.__init__(self)
    
    def construct_portfolio_from_orders(self, all_orders: List[Dict]) -> Dict:
        """
        Construct current portfolio state from SUCCESSFULLY EXECUTED orders only
        
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
        with self.handle_operation_error("construct_portfolio_from_orders"):
            self.logger.info("Constructing portfolio from order history...")
            
            if not all_orders:
                self.logger.warning("No orders provided")
                return {
                    'holdings': {},
                    'order_timeline': [],
                    'total_cash_outflow': 0,
                    'first_order_date': None,
                    'last_order_date': None,
                    'total_orders': 0
                }
        
            # Filter to only successfully executed orders
            successful_orders = self._filter_successful_orders(all_orders)
        
            if not successful_orders:
                self.logger.warning("No successfully executed orders found")
                return {
                    'holdings': {},
                    'order_timeline': [],
                    'total_cash_outflow': 0,
                    'first_order_date': None,
                    'last_order_date': None,
                    'total_orders': 0
                }
        
            # Process all successful orders
            holdings, order_timeline, total_cash_flow, processed_count, error_count = self._process_orders(successful_orders)
        
            # Clean up and finalize holdings
            active_holdings = self._finalize_holdings(holdings)
        
            # Determine date range
            first_order_date, last_order_date = self._get_date_range(successful_orders)
        
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
            
            self.logger.success("Portfolio construction complete:")
            self.logger.info(f"Total orders processed: {processed_count}/{len(all_orders)}")
            self.logger.info(f"Errors encountered: {error_count}")
            self.logger.info(f"Active holdings: {len(active_holdings)}")
            self.logger.info(f"Total cash outflow: Rs.{total_cash_flow:,.2f}")
            self.logger.info(f"Date range: {first_order_date} to {last_order_date}")
            
            return construction_result
    
    def _filter_successful_orders(self, all_orders: List[Dict]) -> List[Dict]:
        """Filter orders to only include successfully executed ones"""
        successful_orders = []
        for order in all_orders:
            status = order.get('status', '').upper()
            live_execution_status = order.get('live_execution_status', '').upper()
            
            # Include order if it's successfully executed
            if (status in ['EXECUTED_SYSTEM', 'EXECUTED_LIVE', 'COMPLETE'] or 
                live_execution_status in ['COMPLETE', 'EXECUTED'] or
                (status == 'LIVE_PLACED' and live_execution_status == 'COMPLETE')):
                successful_orders.append(order)
                self.logger.info(f"Including successful order: {order.get('symbol')} {order.get('action')} - Status: {status}, Live Status: {live_execution_status}")
            else:
                self.logger.warning(f"Excluding failed/pending order: {order.get('symbol')} {order.get('action')} - Status: {status}, Live Status: {live_execution_status}")
        
        self.logger.info(f"Portfolio construction: {len(successful_orders)} successful orders out of {len(all_orders)} total orders")
        return successful_orders
    
    def _process_orders(self, successful_orders: List[Dict]) -> tuple:
        """Process all successful orders to build holdings"""
        holdings = {}
        order_timeline = []
        total_cash_flow = 0
        processed_count = 0
        error_count = 0
        
        # Sort orders by execution time
        try:
            sorted_orders = sorted(
                successful_orders, 
                key=lambda x: DateTimeUtils.safe_parse_date(x.get('execution_time', ''))
            )
            self.logger.info(f"Processing {len(sorted_orders)} successful orders...")
        except Exception as e:
            self.logger.warning(f"Error sorting orders: {e}")
            sorted_orders = successful_orders
        
        for order_idx, order in enumerate(sorted_orders):
            try:
                # Extract and validate order data
                order_data = self._extract_order_data(order, order_idx)
                if not order_data:
                    error_count += 1
                    continue
                
                symbol, action, shares, price, value, execution_time = order_data
                
                self.logger.info(f"Processing: {symbol} {action} {shares} @ Rs.{price:.2f} = Rs.{value:.2f}")
                
                # Initialize or get holding
                holding = self._get_or_create_holding(holdings, symbol)
                
                # Process the transaction
                cash_flow_delta = self._process_transaction(holding, action, shares, price, value, execution_time)
                total_cash_flow += cash_flow_delta
                
                # Record transaction
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
                self.logger.error(f"Error processing order {order_idx}: {e}")
                self.logger.error(f"Order data: {order}")
                error_count += 1
                continue
        
        return holdings, order_timeline, total_cash_flow, processed_count, error_count
    
    def _extract_order_data(self, order: Dict, order_idx: int) -> Optional[tuple]:
        """Extract and validate order data"""
        try:
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
                self.logger.warning(f"Invalid data for order {order_idx}: shares={shares}, price={price}")
                return None
            
            return symbol, action, shares, price, value, execution_time
            
        except Exception as e:
            self.logger.error(f"Error extracting order data: {e}")
            return None
    
    def _get_or_create_holding(self, holdings: Dict, symbol: str) -> Dict:
        """Get existing holding or create new one"""
        if symbol not in holdings:
            holdings[symbol] = {
                'total_shares': 0,
                'total_investment': 0.0,
                'avg_price': 0.0,
                'transactions': [],
                'first_purchase_date': None,
                'last_transaction_date': None
            }
        return holdings[symbol]
    
    def _process_transaction(self, holding: Dict, action: str, shares: int, price: float, value: float, execution_time: str) -> float:
        """Process a single transaction and return cash flow delta"""
        if action == 'BUY':
            holding['total_shares'] += shares
            holding['total_investment'] += value
            
            # Calculate new average price
            if holding['total_shares'] > 0:
                holding['avg_price'] = holding['total_investment'] / holding['total_shares']
            
            # Set first purchase date
            if holding['first_purchase_date'] is None:
                holding['first_purchase_date'] = execution_time
            
            symbol = next((k for k, v in locals().items() if v is holding), 'UNKNOWN')
            self.logger.success(f"BUY: now has {holding['total_shares']} shares at avg Rs.{holding['avg_price']:.2f}")
            
            return value  # Cash outflow
            
        elif action == 'SELL':
            if holding['total_shares'] >= shares:
                holding['total_shares'] -= shares
                
                if holding['total_shares'] > 0:
                    # Reduce investment proportionally (maintain avg price)
                    holding['total_investment'] = holding['total_shares'] * holding['avg_price']
                else:
                    # Position closed
                    holding['total_investment'] = 0.0
                    holding['avg_price'] = 0.0
                    self.logger.warning("SELL: position closed")
            else:
                self.logger.warning(f"SELL: Insufficient shares (have {holding['total_shares']}, trying to sell {shares})")
            
            return -value  # Cash inflow
        
        return 0.0
    
    def _finalize_holdings(self, holdings: Dict) -> Dict:
        """Remove positions with zero or negative shares"""
        active_holdings = {}
        for symbol, holding in holdings.items():
            if holding['total_shares'] > 0:
                active_holdings[symbol] = holding
                self.logger.info(f"Active holding: {symbol} - {holding['total_shares']} shares, Rs.{holding['total_investment']:,.2f} invested")
            else:
                self.logger.info(f"Removing zero position: {symbol}")
        return active_holdings
    
    def _get_date_range(self, successful_orders: List[Dict]) -> tuple:
        """Get first and last order dates"""
        if not successful_orders:
            return None, None
        
        try:
            sorted_orders = sorted(
                successful_orders,
                key=lambda x: DateTimeUtils.safe_parse_date(x.get('execution_time', ''))
            )
            first_order_date = sorted_orders[0].get('execution_time')
            last_order_date = sorted_orders[-1].get('execution_time')
            return first_order_date, last_order_date
        except Exception as e:
            self.logger.warning(f"Error getting date range: {e}")
            return None, None
    
    def _parse_date_safely(self, date_str: str) -> datetime:
        """Safely parse date string - delegated to DateTimeUtils"""
        return DateTimeUtils.safe_parse_date(date_str)
    
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