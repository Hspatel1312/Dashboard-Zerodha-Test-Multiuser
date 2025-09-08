# backend/app/services/portfolio_metrics_service.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

# Foundation imports
from .base.base_service import BaseService
from .utils.financial_calculations import FinancialCalculations, PortfolioMetricsCalculator
from .utils.date_time_utils import DateTimeUtils
from .utils.error_handler import ErrorHandler
from .utils.logger import LoggerFactory

class PortfolioMetricsService(BaseService):
    """
    Service responsible for calculating all portfolio metrics and analytics
    """
    
    def __init__(self):
        BaseService.__init__(self, service_name="portfolio_metrics_service")
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
        with self.handle_operation_error("calculate_comprehensive_metrics"):
            self.logger.success("Calculating comprehensive portfolio metrics...")
            
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
            
            self.logger.success("Portfolio metrics calculated successfully:")
            self.logger.info(f"Holdings: {len(holdings_with_metrics)}")
            self.logger.info(f"Total investment: Rs.{portfolio_totals['total_investment']:,.2f}")
            self.logger.info(f"Current value: Rs.{portfolio_totals['current_value']:,.2f}")
            self.logger.info(f"CAGR: {time_metrics['cagr']:.2f}%")
            self.logger.info(f"Investment period: {time_metrics['investment_period_days']} days")
            
            return comprehensive_metrics
    
    def _calculate_individual_stock_metrics(self, holdings: Dict, current_prices: Dict) -> Dict:
        """Calculate metrics for each individual stock"""
        self.logger.info("Calculating individual stock metrics...")
        
        holdings_with_metrics = {}
        
        for symbol, holding in holdings.items():
            try:
                shares = int(holding.get('total_shares', holding.get('shares', 0)))
                avg_price = float(holding.get('avg_price', 0))
                investment_value = float(holding.get('total_investment', 0))
                
                # Get current price (with fallback)
                current_price = float(current_prices.get(symbol, avg_price))
                current_holding_value = shares * current_price
                
                # Calculate returns using FinancialCalculations
                absolute_return = current_holding_value - investment_value
                percentage_return = FinancialCalculations.calculate_returns_percentage(
                    investment_value, current_holding_value
                )
                
                # Calculate holding period using DateTimeUtils
                days_held, years_held = self._calculate_holding_period(holding)
                
                # Calculate CAGR using FinancialCalculations
                stock_cagr = FinancialCalculations.calculate_cagr(
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
                
                self.logger.success(f"{symbol}: Rs.{investment_value:,.0f} to Rs.{current_holding_value:,.0f} ({percentage_return:.1f}%, {days_held}d)")
                
            except Exception as e:
                self.logger.error(f"Error calculating metrics for {symbol}: {e}")
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
        """Calculate holding period using DateTimeUtils"""
        first_purchase_date = holding.get('first_purchase_date')
        if not first_purchase_date:
            return 30, 30/365.25  # Default to 30 days
        
        try:
            first_purchase = DateTimeUtils.safe_parse_date(first_purchase_date)
            days_held, years_held = DateTimeUtils.calculate_days_and_years_between(
                first_purchase, datetime.now()
            )
            return days_held, years_held
        except Exception as e:
            self.logger.warning(f"Error calculating holding period: {e}")
            return 30, 30/365.25  # Default to 30 days
    
    # REMOVED: _calculate_stock_cagr - now using FinancialCalculations.calculate_cagr()
    
    def _calculate_portfolio_totals(self, holdings_with_metrics: Dict) -> Dict:
        """Calculate portfolio-level totals using FinancialCalculations"""
        self.logger.info("Calculating portfolio totals...")
        
        # Use FinancialCalculations for portfolio totals
        portfolio_totals = FinancialCalculations.calculate_portfolio_totals(holdings_with_metrics)
        
        return portfolio_totals
    
    def _calculate_time_based_metrics(self, portfolio_totals: Dict, construction_data: Dict) -> Dict:
        """Calculate time-based metrics like CAGR"""
        self.logger.info("Calculating time-based metrics...")
        
        try:
            first_order_date_str = construction_data.get('first_order_date')
            if not first_order_date_str:
                return {
                    'investment_period_days': 30,  # Default to 30 days
                    'investment_period_years': 30/365.25,
                    'cagr': portfolio_totals.get('returns_percentage', 0)
                }
            
            # Parse first investment date using DateTimeUtils
            first_order_date = DateTimeUtils.safe_parse_date(first_order_date_str)
            
            investment_period_days, investment_period_years = DateTimeUtils.calculate_days_and_years_between(
                first_order_date, datetime.now()
            )
            
            # Calculate portfolio CAGR using FinancialCalculations
            current_value = portfolio_totals['current_value']
            total_investment = portfolio_totals['total_investment']
            
            cagr = FinancialCalculations.calculate_cagr(
                total_investment, current_value, investment_period_years
            )
            
            return {
                'investment_period_days': investment_period_days,
                'investment_period_years': investment_period_years,
                'cagr': cagr
            }
            
        except Exception as e:
            self.logger.warning(f"Error calculating time metrics: {e}")
            return {
                'investment_period_days': 30,
                'investment_period_years': 30/365.25,
                'cagr': portfolio_totals.get('returns_percentage', 0)
            }
    
    def _calculate_risk_metrics(self, holdings_with_metrics: Dict, portfolio_totals: Dict) -> Dict:
        """Calculate risk metrics like volatility and Sharpe ratio"""
        self.logger.info("Calculating risk metrics...")
        
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
        self.logger.info("Calculating allocation metrics...")
        
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
        self.logger.info("Calculating performance rankings...")
        
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
        
        # Calculate weighted average return using FinancialCalculations
        weighted_return = PortfolioMetricsCalculator.calculate_weighted_average_return(
            holdings_with_metrics
        )
        
        return {
            'best_performer': best_performer,
            'worst_performer': worst_performer,
            'avg_return': weighted_return
        }
    
    def calculate_portfolio_summary(self, orders: list, csv_stocks: list) -> dict:
        """Calculate basic portfolio summary for dashboard display"""
        try:
            if not orders:
                return {
                    'current_value': 0,
                    'total_investment': 0,
                    'returns_percentage': 0.0,
                    'stock_count': 0,
                    'holdings': {}
                }
            
            # Calculate basic totals from orders
            total_investment = 0
            current_value = 0
            holdings = {}
            
            for order in orders:
                # Only include successfully executed orders in portfolio calculation
                if order.get('status') != 'EXECUTED':
                    continue
                    
                symbol = order.get('symbol', '')
                shares = order.get('shares', 0)
                price = order.get('price', 0)
                order_value = shares * price
                
                total_investment += order_value
                current_value += order_value  # Without live prices, assume same value
                
                if symbol not in holdings:
                    holdings[symbol] = {
                        'symbol': symbol,
                        'shares': 0,
                        'investment_value': 0,
                        'current_value': 0,
                        'avg_price': 0
                    }
                
                holdings[symbol]['shares'] += shares
                holdings[symbol]['investment_value'] += order_value
                holdings[symbol]['current_value'] += order_value
                
                if holdings[symbol]['shares'] > 0:
                    holdings[symbol]['avg_price'] = holdings[symbol]['investment_value'] / holdings[symbol]['shares']
            
            # Calculate returns
            returns_percentage = 0.0
            if total_investment > 0:
                returns_percentage = ((current_value - total_investment) / total_investment) * 100
            
            return {
                'current_value': current_value,
                'total_investment': total_investment,
                'returns_percentage': returns_percentage,
                'stock_count': len(holdings),
                'holdings': holdings
            }
            
        except Exception as e:
            self.logger.error(f"Portfolio summary calculation failed: {e}")
            return {
                'current_value': 0,
                'total_investment': 0,
                'returns_percentage': 0.0,
                'stock_count': 0,
                'holdings': {}
            }