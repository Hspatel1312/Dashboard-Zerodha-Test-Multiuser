# backend/app/services/portfolio_metrics_service.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

class PortfolioMetricsService:
    """
    Service responsible for calculating all portfolio metrics and analytics
    """
    
    def __init__(self):
        self.risk_free_rate = 6.0  # 6% risk-free rate assumption
    
    def calculate_comprehensive_metrics(self, holdings: Dict, current_prices: Dict, construction_data: Dict) -> Dict:
        """
        Calculate comprehensive portfolio metrics including CAGR, Sharpe ratio, etc.
        
        Args:
            holdings: Portfolio holdings from construction service
            current_prices: Current market prices for all symbols
            construction_data: Portfolio construction metadata
            
        Returns:
            Complete metrics dictionary
        """
        print("📈 Calculating comprehensive portfolio metrics...")
        
        try:
            # Calculate individual stock metrics
            holdings_with_metrics = self._calculate_individual_stock_metrics(holdings, current_prices)
            
            # Calculate portfolio-level aggregations
            portfolio_totals = self._calculate_portfolio_totals(holdings_with_metrics)
            
            # Calculate time-based metrics (CAGR, etc.)
            time_metrics = self._calculate_time_based_metrics(
                portfolio_totals, construction_data
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(holdings_with_metrics, portfolio_totals)
            
            # Calculate allocation metrics
            allocation_metrics = self._calculate_allocation_metrics(holdings_with_metrics)
            
            # Find best/worst performers
            performance_rankings = self._calculate_performance_rankings(holdings_with_metrics)
            
            # Combine all metrics
            comprehensive_metrics = {
                'holdings_with_metrics': holdings_with_metrics,
                'total_investment': portfolio_totals['total_investment'],
                'current_value': portfolio_totals['current_value'],
                'total_returns': portfolio_totals['total_returns'],
                'returns_percentage': portfolio_totals['returns_percentage'],
                'cagr': time_metrics['cagr'],
                'investment_period_days': time_metrics['investment_period_days'],
                'investment_period_years': time_metrics['investment_period_years'],
                'best_performer': performance_rankings['best_performer'],
                'worst_performer': performance_rankings['worst_performer'],
                'avg_return': performance_rankings['avg_return'],
                'volatility_score': risk_metrics['volatility_score'],
                'sharpe_ratio': risk_metrics['sharpe_ratio'],
                'allocation_stats': allocation_metrics['allocation_stats'],
                'allocation_deviation': allocation_metrics['allocation_deviation'],
                'rebalancing_needed': allocation_metrics['rebalancing_needed']
            }
            
            print(f"✅ Portfolio metrics calculated successfully:")
            print(f"   Holdings: {len(holdings_with_metrics)}")
            print(f"   Total investment: ₹{portfolio_totals['total_investment']:,.2f}")
            print(f"   Current value: ₹{portfolio_totals['current_value']:,.2f}")
            print(f"   CAGR: {time_metrics['cagr']:.2f}%")
            print(f"   Investment period: {time_metrics['investment_period_days']} days")
            
            return comprehensive_metrics
            
        except Exception as e:
            print(f"❌ Error calculating portfolio metrics: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to calculate portfolio metrics: {str(e)}")
    
    def _calculate_individual_stock_metrics(self, holdings: Dict, current_prices: Dict) -> Dict:
        """Calculate metrics for each individual stock"""
        print("   📊 Calculating individual stock metrics...")
        
        holdings_with_metrics = {}
        
        for symbol, holding in holdings.items():
            try:
                shares = int(holding.get('total_shares', holding.get('shares', 0)))
                avg_price = float(holding.get('avg_price', 0))
                investment_value = float(holding.get('total_investment', 0))
                
                # Get current price (with fallback)
                current_price = float(current_prices.get(symbol, avg_price))
                current_holding_value = shares * current_price
                
                # Calculate returns
                absolute_return = current_holding_value - investment_value
                percentage_return = (absolute_return / investment_value) * 100 if investment_value > 0 else 0
                
                # Calculate holding period with better error handling
                days_held, years_held = self._calculate_holding_period(holding)
                
                # Calculate annualized return (CAGR) for this stock
                stock_cagr = self._calculate_stock_cagr(
                    investment_value, current_holding_value, years_held
                )
                
                holdings_with_metrics[symbol] = {
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'investment_value': investment_value,
                    'current_value': current_holding_value,
                    'absolute_return': absolute_return,
                    'percentage_return': percentage_return,
                    'allocation_percent': 0,  # Will calculate after getting totals
                    'days_held': days_held,
                    'years_held': years_held,
                    'annualized_return': stock_cagr,
                    'first_purchase_date': holding.get('first_purchase_date', ''),
                    'last_transaction_date': holding.get('last_transaction_date', ''),
                    'transaction_count': len(holding.get('transactions', []))
                }
                
                print(f"      ✅ {symbol}: ₹{investment_value:,.0f} → ₹{current_holding_value:,.0f} ({percentage_return:.1f}%, {days_held}d)")
                
            except Exception as e:
                print(f"      ❌ Error calculating metrics for {symbol}: {e}")
                # Create a safe fallback entry
                holdings_with_metrics[symbol] = {
                    'shares': 0,
                    'avg_price': 0,
                    'current_price': 0,
                    'investment_value': 0,
                    'current_value': 0,
                    'absolute_return': 0,
                    'percentage_return': 0,
                    'allocation_percent': 0,
                    'days_held': 1,
                    'years_held': 1/365.25,
                    'annualized_return': 0,
                    'first_purchase_date': '',
                    'last_transaction_date': '',
                    'transaction_count': 0
                }
        
        return holdings_with_metrics
    
    def _calculate_holding_period(self, holding: Dict) -> Tuple[int, float]:
        """Calculate holding period in days and years with better error handling"""
        try:
            first_purchase_date = holding.get('first_purchase_date')
            if not first_purchase_date:
                return 30, 30/365.25  # Default to 30 days
            
            # Parse datetime flexibly
            if isinstance(first_purchase_date, str):
                if 'T' in first_purchase_date:
                    # ISO format: 2023-12-01T10:30:00.123456
                    first_purchase = datetime.fromisoformat(first_purchase_date.replace('Z', ''))
                else:
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
                        try:
                            first_purchase = datetime.strptime(first_purchase_date, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # If all formats fail, default to 30 days ago
                        first_purchase = datetime.now() - timedelta(days=30)
            else:
                # If it's already a datetime object
                first_purchase = first_purchase_date
            
            days_held = max(1, (datetime.now() - first_purchase).days)
            years_held = max(days_held / 365.25, 1/365.25)
            
            return days_held, years_held
            
        except Exception as e:
            print(f"      ⚠️ Error calculating holding period: {e}")
            return 30, 30/365.25  # Default to 30 days
    
    def _calculate_stock_cagr(self, investment_value: float, current_value: float, years_held: float) -> float:
        """Calculate CAGR for individual stock with better error handling"""
        try:
            if investment_value <= 0 or current_value <= 0 or years_held <= 0:
                return 0.0
            
            # CAGR = (Ending Value / Beginning Value)^(1/years) - 1
            cagr_ratio = current_value / investment_value
            if cagr_ratio > 0:
                # Handle very small time periods
                if years_held < 1/365.25:  # Less than 1 day
                    years_held = 1/365.25
                
                try:
                    cagr = ((cagr_ratio ** (1 / years_held)) - 1) * 100
                    # Cap extreme values to prevent display issues
                    cagr = max(-99.9, min(999.9, cagr))
                    return cagr
                except (OverflowError, ZeroDivisionError):
                    # Fallback to simple return annualized
                    simple_return = ((current_value - investment_value) / investment_value) * 100
                    return simple_return / years_held if years_held > 0 else simple_return
            else:
                return -99.9  # Near total loss
                
        except (OverflowError, ZeroDivisionError, ValueError) as e:
            print(f"      ⚠️ CAGR calculation error: {e}")
            # Fallback to simple return
            if investment_value > 0:
                return ((current_value - investment_value) / investment_value) * 100
            return 0.0
    
    def _calculate_portfolio_totals(self, holdings_with_metrics: Dict) -> Dict:
        """Calculate portfolio-level totals"""
        print("   💰 Calculating portfolio totals...")
        
        total_investment = sum(holding['investment_value'] for holding in holdings_with_metrics.values())
        current_value = sum(holding['current_value'] for holding in holdings_with_metrics.values())
        total_returns = current_value - total_investment
        returns_percentage = (total_returns / total_investment) * 100 if total_investment > 0 else 0
        
        # Calculate allocation percentages
        for holding in holdings_with_metrics.values():
            holding['allocation_percent'] = (
                (holding['current_value'] / current_value) * 100 
                if current_value > 0 else 0
            )
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'total_returns': total_returns,
            'returns_percentage': returns_percentage
        }
    
    def _calculate_time_based_metrics(self, portfolio_totals: Dict, construction_data: Dict) -> Dict:
        """Calculate time-based metrics like CAGR"""
        print("   ⏰ Calculating time-based metrics...")
        
        try:
            first_order_date_str = construction_data.get('first_order_date')
            if not first_order_date_str:
                return {
                    'investment_period_days': 30,  # Default to 30 days
                    'investment_period_years': 30/365.25,
                    'cagr': portfolio_totals.get('returns_percentage', 0)
                }
            
            # Parse first investment date
            if 'T' in first_order_date_str:
                first_order_date = datetime.fromisoformat(first_order_date_str.replace('Z', ''))
            else:
                try:
                    first_order_date = datetime.strptime(first_order_date_str, '%Y-%m-%d')
                except ValueError:
                    # If parsing fails, use 30 days ago
                    first_order_date = datetime.now() - timedelta(days=30)
            
            investment_period_days = max(1, (datetime.now() - first_order_date).days)
            investment_period_years = max(investment_period_days / 365.25, 1/365.25)
            
            # Calculate portfolio CAGR
            current_value = portfolio_totals['current_value']
            total_investment = portfolio_totals['total_investment']
            
            if current_value > 0 and total_investment > 0 and investment_period_years > 0:
                cagr_ratio = current_value / total_investment
                if cagr_ratio > 0:
                    try:
                        cagr = ((cagr_ratio ** (1 / investment_period_years)) - 1) * 100
                        cagr = max(-99.9, min(999.9, cagr))  # Cap extreme values
                    except (OverflowError, ZeroDivisionError):
                        # Fallback to simple annualized return
                        simple_return = portfolio_totals.get('returns_percentage', 0)
                        cagr = simple_return / investment_period_years if investment_period_years > 0 else simple_return
                else:
                    cagr = -99.9
            else:
                cagr = 0.0
            
            return {
                'investment_period_days': investment_period_days,
                'investment_period_years': investment_period_years,
                'cagr': cagr
            }
            
        except Exception as e:
            print(f"      ⚠️ Error calculating time metrics: {e}")
            return {
                'investment_period_days': 30,
                'investment_period_years': 30/365.25,
                'cagr': portfolio_totals.get('returns_percentage', 0)
            }
    
    def _calculate_risk_metrics(self, holdings_with_metrics: Dict, portfolio_totals: Dict) -> Dict:
        """Calculate risk metrics like volatility and Sharpe ratio"""
        print("   ⚠️ Calculating risk metrics...")
        
        if not holdings_with_metrics:
            return {
                'volatility_score': 0.0,
                'sharpe_ratio': 0.0
            }
        
        returns_data = [holding['percentage_return'] for holding in holdings_with_metrics.values()]
        
        # Calculate volatility (standard deviation of returns)
        if len(returns_data) > 1:
            try:
                mean_return = sum(returns_data) / len(returns_data)
                variance = sum((ret - mean_return) ** 2 for ret in returns_data) / (len(returns_data) - 1)
                volatility_score = math.sqrt(max(0, variance))
                volatility_score = min(volatility_score, 100)  # Cap at 100%
            except (ValueError, OverflowError, ZeroDivisionError):
                volatility_score = 0.0
        else:
            volatility_score = 0.0
        
        # Calculate Sharpe ratio
        portfolio_return = portfolio_totals.get('returns_percentage', 0)
        if volatility_score > 0:
            try:
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / volatility_score
                sharpe_ratio = max(-10, min(10, sharpe_ratio))  # Cap extreme values
            except (OverflowError, ZeroDivisionError):
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
        
        return {
            'volatility_score': volatility_score,
            'sharpe_ratio': sharpe_ratio
        }
    
    def _calculate_allocation_metrics(self, holdings_with_metrics: Dict) -> Dict:
        """Calculate allocation analysis metrics"""
        print("   ⚖️ Calculating allocation metrics...")
        
        if not holdings_with_metrics:
            return {
                'allocation_stats': {
                    'target_allocation': 0,
                    'min_allocation': 0,
                    'max_allocation': 0,
                    'avg_allocation': 0
                },
                'allocation_deviation': 0,
                'rebalancing_needed': False
            }
        
        allocations = [holding['allocation_percent'] for holding in holdings_with_metrics.values()]
        
        target_allocation = 100 / len(allocations)
        allocation_deviation = sum(abs(alloc - target_allocation) for alloc in allocations) / len(allocations)
        rebalancing_needed = allocation_deviation > 2.0
        
        allocation_stats = {
            'target_allocation': target_allocation,
            'min_allocation': min(allocations),
            'max_allocation': max(allocations),
            'avg_allocation': sum(allocations) / len(allocations)
        }
        
        return {
            'allocation_stats': allocation_stats,
            'allocation_deviation': allocation_deviation,
            'rebalancing_needed': rebalancing_needed
        }
    
    def _calculate_performance_rankings(self, holdings_with_metrics: Dict) -> Dict:
        """Calculate best/worst performers and averages"""
        print("   🏆 Calculating performance rankings...")
        
        if not holdings_with_metrics:
            return {
                'best_performer': None,
                'worst_performer': None,
                'avg_return': 0.0
            }
        
        # Find best and worst performers
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
        
        # Calculate weighted average return
        total_investment = sum(holding['investment_value'] for holding in holdings_with_metrics.values())
        if total_investment > 0:
            weighted_return = sum(
                holding['percentage_return'] * holding['investment_value'] 
                for holding in holdings_with_metrics.values()
            ) / total_investment
        else:
            weighted_return = 0.0
        
        return {
            'best_performer': best_performer,
            'worst_performer': worst_performer,
            'avg_return': weighted_return
        }