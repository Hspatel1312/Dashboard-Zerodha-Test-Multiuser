# backend/app/services/portfolio_comparison_service.py
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

# Foundation imports
from .base.base_service import BaseService
from .utils.financial_calculations import FinancialCalculations
from .utils.error_handler import ErrorHandler
from .utils.logger import LoggerFactory

class PortfolioComparisonService(BaseService):
    """
    Service to compare dashboard portfolio with live Zerodha portfolio
    Implements the logic as specified:
    - Dashboard portfolio: Built from system orders
    - Zerodha portfolio: Live from Zerodha API (includes positions, pledged, collateral)
    - Comparison logic: Check if Zerodha has minimum quantities from dashboard
    """
    
    def __init__(self, portfolio_service, investment_service):
        BaseService.__init__(self, service_name="portfolio_comparison_service")
        self.portfolio_service = portfolio_service
        self.investment_service = investment_service
    
    def compare_portfolios(self) -> Dict:
        """
        Compare dashboard portfolio with live Zerodha portfolio
        
        Returns:
        {
            'comparison_status': 'MATCH' | 'MODIFIED' | 'ERROR',
            'dashboard_portfolio': {...},
            'zerodha_portfolio': {...},
            'comparison_details': {...},
            'recommended_action': str
        }
        """
        with self.handle_operation_error("compare_portfolios"):
            self.logger.info("Starting portfolio comparison between dashboard and Zerodha...")
            
            # Get dashboard portfolio (from system orders)
            dashboard_status = self.investment_service.get_system_portfolio_status()
            if dashboard_status['status'] != 'active':
                return self._create_error_response(
                    'No active dashboard portfolio found',
                    dashboard_status, {},
                    'Complete initial investment first'
                )
            
            dashboard_holdings = dashboard_status['holdings']
            self.logger.info(f"Dashboard portfolio: {len(dashboard_holdings)} stocks")
            
            # Get live Zerodha portfolio
            zerodha_data = self.portfolio_service.get_portfolio_data()
            if 'error' in zerodha_data:
                return self._create_error_response(
                    f'Cannot fetch Zerodha portfolio: {zerodha_data.get("error_message", "Unknown error")}',
                    dashboard_status, zerodha_data,
                    'Fix Zerodha connection and retry'
                )
            
            zerodha_holdings = {holding['symbol']: holding for holding in zerodha_data.get('holdings', [])}
            self.logger.info(f"Zerodha portfolio: {len(zerodha_holdings)} stocks")
            
            # Perform detailed comparison
            comparison_details = self._perform_detailed_comparison(dashboard_holdings, zerodha_holdings)
            
            # Determine comparison status
            comparison_status = self._determine_comparison_status(comparison_details)
            
            # Calculate usable portfolio value for rebalancing
            usable_portfolio_info = self._calculate_usable_portfolio_value(
                dashboard_holdings, zerodha_holdings, comparison_details
            )
            
            result = {
                'comparison_status': comparison_status,
                'dashboard_portfolio': dashboard_status,
                'zerodha_portfolio': zerodha_data,
                'comparison_details': comparison_details,
                'usable_portfolio_info': usable_portfolio_info,
                'recommended_action': self._get_recommended_action(comparison_status, comparison_details),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.success(f"Portfolio comparison completed: {comparison_status}")
            return result
    
    def _create_error_response(self, error_message: str, dashboard_portfolio: Dict, zerodha_portfolio: Dict, recommended_action: str) -> Dict:
        """Create standardized error response"""
        return {
            'comparison_status': 'ERROR',
            'error': error_message,
            'dashboard_portfolio': dashboard_portfolio,
            'zerodha_portfolio': zerodha_portfolio,
            'comparison_details': {},
            'recommended_action': recommended_action
        }
    
    def _perform_detailed_comparison(self, dashboard_holdings: Dict, zerodha_holdings: Dict) -> Dict:
        """
        Perform detailed stock-by-stock comparison
        
        Logic:
        - For each dashboard stock, check if Zerodha has at least the minimum quantity
        - If Zerodha has more, that's fine (user may have bought more)
        - If Zerodha has less, it's modified
        """
        self.logger.info("Performing detailed portfolio comparison...")
        
        comparison_details = {
            'matching_stocks': [],
            'excess_stocks': [],  # Zerodha has more than dashboard
            'deficit_stocks': [],  # Zerodha has less than dashboard
            'missing_stocks': [],  # Dashboard stocks not in Zerodha
            'extra_stocks': [],   # Zerodha stocks not in dashboard
            'total_dashboard_stocks': len(dashboard_holdings),
            'total_zerodha_stocks': len(zerodha_holdings),
            'portfolio_value_dashboard': 0,
            'portfolio_value_zerodha_matching': 0,
            'modification_summary': {}
        }
        
        total_dashboard_value = 0
        total_matching_value = 0
        
        # Check each dashboard stock
        for symbol, dashboard_holding in dashboard_holdings.items():
            dashboard_shares = dashboard_holding['shares']
            dashboard_current_price = dashboard_holding.get('current_price', dashboard_holding.get('avg_price', 0))
            dashboard_value = dashboard_shares * dashboard_current_price
            total_dashboard_value += dashboard_value
            
            if symbol in zerodha_holdings:
                zerodha_holding = zerodha_holdings[symbol]
                zerodha_shares = zerodha_holding['quantity']  # Total shares (regular + t1 + collateral)
                zerodha_price = zerodha_holding['current_price']
                
                self.logger.info(f"Comparing {symbol}: Dashboard={dashboard_shares}, Zerodha={zerodha_shares}")
                
                if zerodha_shares >= dashboard_shares:
                    if zerodha_shares == dashboard_shares:
                        comparison_details['matching_stocks'].append({
                            'symbol': symbol,
                            'dashboard_shares': dashboard_shares,
                            'zerodha_shares': zerodha_shares,
                            'status': 'EXACT_MATCH',
                            'dashboard_value': dashboard_value,
                            'zerodha_value': zerodha_shares * zerodha_price
                        })
                    else:
                        comparison_details['excess_stocks'].append({
                            'symbol': symbol,
                            'dashboard_shares': dashboard_shares,
                            'zerodha_shares': zerodha_shares,
                            'excess_shares': zerodha_shares - dashboard_shares,
                            'status': 'EXCESS_IN_ZERODHA',
                            'dashboard_value': dashboard_value,
                            'zerodha_value': zerodha_shares * zerodha_price
                        })
                    
                    # For matching purposes, count the dashboard quantity
                    total_matching_value += dashboard_shares * zerodha_price
                else:
                    # Zerodha has less than dashboard - this is a deficit
                    comparison_details['deficit_stocks'].append({
                        'symbol': symbol,
                        'dashboard_shares': dashboard_shares,
                        'zerodha_shares': zerodha_shares,
                        'deficit_shares': dashboard_shares - zerodha_shares,
                        'status': 'DEFICIT_IN_ZERODHA',
                        'dashboard_value': dashboard_value,
                        'zerodha_value': zerodha_shares * zerodha_price
                    })
                    
                    # For matching, only count what Zerodha actually has
                    total_matching_value += zerodha_shares * zerodha_price
            else:
                # Dashboard stock not in Zerodha at all
                comparison_details['missing_stocks'].append({
                    'symbol': symbol,
                    'dashboard_shares': dashboard_shares,
                    'zerodha_shares': 0,
                    'status': 'MISSING_IN_ZERODHA',
                    'dashboard_value': dashboard_value,
                    'zerodha_value': 0
                })
        
        # Check for extra stocks in Zerodha not in dashboard
        for symbol, zerodha_holding in zerodha_holdings.items():
            if symbol not in dashboard_holdings:
                comparison_details['extra_stocks'].append({
                    'symbol': symbol,
                    'zerodha_shares': zerodha_holding['quantity'],
                    'status': 'EXTRA_IN_ZERODHA',
                    'zerodha_value': zerodha_holding['quantity'] * zerodha_holding['current_price']
                })
        
        comparison_details['portfolio_value_dashboard'] = total_dashboard_value
        comparison_details['portfolio_value_zerodha_matching'] = total_matching_value
        
        # Create modification summary
        comparison_details['modification_summary'] = {
            'total_modifications': len(comparison_details['deficit_stocks']) + 
                                 len(comparison_details['missing_stocks']) + 
                                 len(comparison_details['extra_stocks']),
            'stocks_with_deficits': len(comparison_details['deficit_stocks']),
            'stocks_missing': len(comparison_details['missing_stocks']),
            'extra_stocks_count': len(comparison_details['extra_stocks']),
            'stocks_with_excess': len(comparison_details['excess_stocks']),
            'perfect_matches': len(comparison_details['matching_stocks'])
        }
        
        self.logger.info("Comparison details:")
        self.logger.info(f"Perfect matches: {comparison_details['modification_summary']['perfect_matches']}")
        self.logger.info(f"Excess in Zerodha: {comparison_details['modification_summary']['stocks_with_excess']}")
        self.logger.info(f"Deficits in Zerodha: {comparison_details['modification_summary']['stocks_with_deficits']}")
        self.logger.info(f"Missing in Zerodha: {comparison_details['modification_summary']['stocks_missing']}")
        self.logger.info(f"Extra in Zerodha: {comparison_details['modification_summary']['extra_stocks_count']}")
        
        return comparison_details
    
    def _determine_comparison_status(self, comparison_details: Dict) -> str:
        """Determine overall comparison status"""
        modifications = comparison_details['modification_summary']['total_modifications']
        
        if modifications == 0:
            return 'MATCH'
        elif comparison_details['modification_summary']['stocks_with_deficits'] > 0 or \
             comparison_details['modification_summary']['stocks_missing'] > 0:
            return 'MODIFIED'  # User has sold or reduced positions
        else:
            return 'MATCH'  # Only excess stocks, which is acceptable
    
    def _calculate_usable_portfolio_value(self, dashboard_holdings: Dict, zerodha_holdings: Dict, 
                                        comparison_details: Dict) -> Dict:
        """
        Calculate the usable portfolio value for rebalancing
        
        Logic from your requirement:
        - If X should be 10 and Y should be 20
        - But Zerodha has X=8 and Y=25
        - We take X=8 and Y=20 (only what dashboard expected)
        - Calculate portfolio value this way
        """
        self.logger.info("Calculating usable portfolio value for rebalancing...")
        
        usable_value = 0
        usable_holdings = {}
        
        for symbol, dashboard_holding in dashboard_holdings.items():
            dashboard_shares = dashboard_holding['shares']
            
            if symbol in zerodha_holdings:
                zerodha_holding = zerodha_holdings[symbol]
                zerodha_shares = zerodha_holding['quantity']
                zerodha_price = zerodha_holding['current_price']
                
                # Take minimum of dashboard expected and zerodha actual
                usable_shares = min(dashboard_shares, zerodha_shares)
                usable_stock_value = usable_shares * zerodha_price
                
                usable_holdings[symbol] = {
                    'shares': usable_shares,
                    'current_price': zerodha_price,
                    'value': usable_stock_value,
                    'dashboard_expected': dashboard_shares,
                    'zerodha_actual': zerodha_shares,
                    'using_logic': 'min(dashboard_expected, zerodha_actual)'
                }
                
                usable_value += usable_stock_value
                
                self.logger.info(f"{symbol}: Dashboard={dashboard_shares}, Zerodha={zerodha_shares}, Using={usable_shares}")
            else:
                # Stock missing in Zerodha - contributes 0 to usable value
                usable_holdings[symbol] = {
                    'shares': 0,
                    'current_price': 0,
                    'value': 0,
                    'dashboard_expected': dashboard_shares,
                    'zerodha_actual': 0,
                    'using_logic': 'missing_in_zerodha'
                }
                
                self.logger.info(f"{symbol}: Missing in Zerodha, contributing 0 to portfolio value")
        
        return {
            'usable_portfolio_value': usable_value,
            'usable_holdings': usable_holdings,
            'calculation_method': 'min(dashboard_expected, zerodha_actual) for each stock',
            'total_usable_stocks': len([h for h in usable_holdings.values() if h['shares'] > 0])
        }
    
    def _get_recommended_action(self, comparison_status: str, comparison_details: Dict) -> str:
        """Get recommended action based on comparison results"""
        if comparison_status == 'MATCH':
            return "Portfolio matches or has acceptable excess. Proceed with rebalancing using dashboard portfolio value."
        elif comparison_status == 'MODIFIED':
            modifications = comparison_details['modification_summary']
            actions = []
            
            if modifications['stocks_with_deficits'] > 0:
                actions.append(f"Warning: {modifications['stocks_with_deficits']} stocks have reduced quantities")
            
            if modifications['stocks_missing'] > 0:
                actions.append(f"Warning: {modifications['stocks_missing']} stocks are completely missing")
            
            actions.append("Portfolio has been manually modified. Rebalancing will use actual Zerodha quantities.")
            
            return " | ".join(actions)
        else:
            return "Unable to compare portfolios. Check system connectivity."

    def get_rebalancing_portfolio_value(self) -> Dict:
        """
        Get the portfolio value to use for rebalancing calculations
        This implements the logic specified in the requirements
        """
        try:
            comparison_result = self.compare_portfolios()
            
            if comparison_result['comparison_status'] == 'ERROR':
                raise Exception(f"Portfolio comparison failed: {comparison_result.get('error', 'Unknown error')}")
            
            usable_info = comparison_result['usable_portfolio_info']
            
            return {
                'success': True,
                'portfolio_value_for_rebalancing': usable_info['usable_portfolio_value'],
                'usable_holdings': usable_info['usable_holdings'],
                'comparison_status': comparison_result['comparison_status'],
                'portfolio_modifications_detected': comparison_result['comparison_status'] == 'MODIFIED',
                'modification_details': comparison_result['comparison_details']['modification_summary'],
                'recommended_action': comparison_result['recommended_action']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get rebalancing portfolio value: {e}")
            return {
                'success': False,
                'error': str(e),
                'portfolio_value_for_rebalancing': 0,
                'recommended_action': 'Fix errors and retry'
            }