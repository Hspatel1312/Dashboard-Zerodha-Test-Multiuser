# backend/app/services/utils/financial_calculations.py
"""
Centralized financial calculations for all investment services

This module consolidates financial calculation logic that is currently
duplicated across 7+ services. Each method replaces specific duplicate
patterns found in the codebase.
"""

import math
from typing import Union, List, Dict, Any, Optional, Tuple
from .config import InvestmentConfig


class FinancialCalculations:
    """Centralized financial calculations used across all investment services"""
    
    @staticmethod
    def calculate_cagr(
        initial_value: float, 
        current_value: float, 
        years: float,
        cap_extreme_values: bool = True
    ) -> float:
        """
        Calculate CAGR (Compound Annual Growth Rate)
        
        This replaces duplicate CAGR calculations found in:
        - portfolio_metrics_service.py _calculate_stock_cagr() (lines 235-250)
        - portfolio_metrics_service.py _calculate_time_based_metrics() (lines 345-365)
        - investment_service.py (multiple places with CAGR calculations)
        
        Args:
            initial_value: Starting investment value
            current_value: Current portfolio value
            years: Time period in years (must be > 0)
            cap_extreme_values: Whether to cap values to prevent display issues
            
        Returns:
            CAGR percentage (-99.9 to 999.9 if capped, or actual value)
        """
        try:
            if initial_value <= 0 or current_value <= 0 or years <= 0:
                return 0.0
            
            cagr_ratio = current_value / initial_value
            if cagr_ratio > 0:
                if years < 1.0:
                    # For periods less than 1 year, use simple annualized return
                    simple_return = ((current_value - initial_value) / initial_value) * 100
                    cagr = simple_return / years if years > 0 else simple_return
                else:
                    # Standard CAGR formula: (Ending Value / Beginning Value)^(1/years) - 1
                    cagr = ((cagr_ratio ** (1 / years)) - 1) * 100
                
                # Cap extreme values to prevent display issues (matching existing pattern)
                if cap_extreme_values:
                    cagr = max(InvestmentConfig.CAGR_MIN_VALUE, 
                              min(InvestmentConfig.CAGR_MAX_VALUE, cagr))
                
                return cagr
            else:
                return InvestmentConfig.CAGR_MIN_VALUE if cap_extreme_values else -100.0
                
        except (OverflowError, ZeroDivisionError, ValueError):
            return 0.0
    
    @staticmethod
    def calculate_allocation_percent(value: float, total_value: float) -> float:
        """
        Calculate allocation percentage with safe division
        
        This replaces the repeated pattern found across 8+ services:
        (value / total_value) * 100 if total_value > 0 else 0
        
        Found in:
        - portfolio_service.py (lines 156, 174)
        - investment_service.py (lines 623, 665)
        - multiuser_investment_service.py (multiple places)
        - portfolio_metrics_service.py (lines 285, 420)
        - investment_calculator.py (lines 220, 340)
        
        Args:
            value: Individual value
            total_value: Total value for percentage calculation
            
        Returns:
            Percentage (0.0 to 100.0)
        """
        try:
            return (value / total_value) * 100 if total_value > 0 else 0.0
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_returns_percentage(current_value: float, investment_value: float) -> float:
        """
        Calculate percentage returns with safe division
        
        This replaces the duplicate pattern found in:
        - portfolio_service.py: pnl_percent = (pnl / investment_value) * 100
        - investment_service.py: returns_percent = (total_returns / total_investment) * 100  
        - portfolio_metrics_service.py: percentage_return = (absolute_return / investment_value) * 100
        
        Args:
            current_value: Current value
            investment_value: Original investment value
            
        Returns:
            Returns percentage (positive for gains, negative for losses)
        """
        try:
            if investment_value <= 0:
                return 0.0
            return ((current_value - investment_value) / investment_value) * 100
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_pnl_percent(pnl: float, investment_value: float) -> float:
        """
        Calculate PnL percentage (alternative name for returns percentage)
        
        This matches the exact pattern used in portfolio_service.py:
        pnl_percent = (pnl / investment_value) * 100 if investment_value > 0 else 0
        
        Args:
            pnl: Profit/Loss amount (can be negative)
            investment_value: Original investment value
            
        Returns:
            PnL percentage
        """
        try:
            return (pnl / investment_value) * 100 if investment_value > 0 else 0.0
        except (ZeroDivisionError, TypeError):
            return 0.0
    
    @staticmethod
    def validate_price_range(
        price: Union[int, float], 
        min_price: float = None, 
        max_price: float = None
    ) -> bool:
        """
        Validate if price is within acceptable range
        
        This replaces the price validation logic found in:
        - csv_service.py (lines 440-445): if 0.1 <= last_price <= 100000
        - investment_calculator.py (price validation in multiple methods)
        
        Args:
            price: Price to validate
            min_price: Minimum acceptable price (default from config)
            max_price: Maximum acceptable price (default from config)
            
        Returns:
            True if price is valid, False otherwise
        """
        if min_price is None:
            min_price = InvestmentConfig.MIN_VALID_PRICE
        if max_price is None:
            max_price = InvestmentConfig.MAX_VALID_PRICE
            
        try:
            return (isinstance(price, (int, float)) and 
                   min_price <= float(price) <= max_price)
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def safe_percentage_calculation(
        numerator: Union[int, float], 
        denominator: Union[int, float], 
        default: float = 0.0,
        multiply_by_100: bool = True
    ) -> float:
        """
        Safe percentage calculation with fallback
        
        This addresses the repeated pattern: x / y * 100 if y > 0 else 0
        found throughout all services
        
        Args:
            numerator: Top value
            denominator: Bottom value  
            default: Default value if calculation fails
            multiply_by_100: Whether to multiply by 100 for percentage
            
        Returns:
            Calculated percentage or default value
        """
        try:
            if denominator == 0:
                return default
            result = numerator / denominator
            return result * 100 if multiply_by_100 else result
        except (ZeroDivisionError, TypeError, ValueError):
            return default
    
    @staticmethod
    def calculate_simple_return_percent(current_value: float, initial_value: float) -> float:
        """
        Calculate simple return percentage (not annualized)
        
        This is used for short-term returns and in CAGR fallback calculations
        
        Args:
            current_value: Current value
            initial_value: Initial value
            
        Returns:
            Simple return percentage
        """
        return FinancialCalculations.calculate_returns_percentage(current_value, initial_value)
    
    @staticmethod
    def normalize_price_data(price_data: Any) -> float:
        """
        Normalize price data from various formats to float
        
        This handles the pattern found in csv_service.py and other services:
        - Extract price from dict formats
        - Handle string/numeric conversion
        - Return 0.0 for invalid data
        
        Args:
            price_data: Price data in various formats (dict, string, number)
            
        Returns:
            Normalized price as float
        """
        try:
            # Handle dict format (common in API responses)
            if isinstance(price_data, dict):
                price = price_data.get('price', price_data.get('last_price', 0))
                return float(price) if price else 0.0
            
            # Handle direct numeric values
            return float(price_data) if price_data else 0.0
            
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def calculate_target_allocation_ranges(
        target_percent: float,
        flexibility_percent: float = None
    ) -> Dict[str, float]:
        """
        Calculate min/max allocation ranges around target
        
        This replaces the allocation range calculations found in investment_calculator.py:
        - min_allocation = target - flexibility
        - max_allocation = target + flexibility
        
        Args:
            target_percent: Target allocation percentage
            flexibility_percent: Flexibility around target (default from config)
            
        Returns:
            Dict with 'min', 'target', 'max' allocation percentages
        """
        if flexibility_percent is None:
            flexibility_percent = InvestmentConfig.ALLOCATION_FLEXIBILITY_PERCENT
        
        return {
            'min': max(0.1, target_percent - flexibility_percent),  # Never below 0.1%
            'target': target_percent,
            'max': min(100.0, target_percent + flexibility_percent)  # Never above 100%
        }
    
    @staticmethod
    def is_allocation_within_target(
        actual_percent: float,
        target_percent: float, 
        flexibility_percent: float = None,
        tolerance: float = 0.5
    ) -> bool:
        """
        Check if allocation is within acceptable range of target
        
        This replaces the pattern found in investment_calculator.py:
        abs(allocation_percent - target_allocation_percent) < tolerance
        
        Args:
            actual_percent: Actual allocation percentage
            target_percent: Target allocation percentage
            flexibility_percent: Flexibility around target
            tolerance: Additional tolerance for "close enough"
            
        Returns:
            True if allocation is within acceptable range
        """
        if flexibility_percent is None:
            flexibility_percent = InvestmentConfig.ALLOCATION_FLEXIBILITY_PERCENT
        
        ranges = FinancialCalculations.calculate_target_allocation_ranges(
            target_percent, flexibility_percent
        )
        
        # Check if within strict range or within tolerance
        return (ranges['min'] <= actual_percent <= ranges['max'] or 
               abs(actual_percent - target_percent) < tolerance)


class PortfolioMetricsCalculator:
    """Specialized calculator for portfolio-level metrics"""
    
    @staticmethod
    def calculate_portfolio_totals(holdings: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate portfolio totals from holdings data
        
        This replaces the repeated pattern found across portfolio services
        for calculating total investment, current value, returns, etc.
        
        Args:
            holdings: Dict mapping symbol -> holding data
            
        Returns:
            Dict with portfolio totals
        """
        total_investment = 0.0
        current_value = 0.0
        
        for symbol, holding in holdings.items():
            # Handle different holding data formats
            investment = holding.get('investment_value', holding.get('total_investment', 0))
            current = holding.get('current_value', 0)
            
            total_investment += float(investment) if investment else 0.0
            current_value += float(current) if current else 0.0
        
        total_returns = current_value - total_investment
        returns_percentage = FinancialCalculations.calculate_returns_percentage(
            current_value, total_investment
        )
        
        return {
            'total_investment': total_investment,
            'current_value': current_value,
            'total_returns': total_returns,
            'returns_percentage': returns_percentage,
            'stock_count': len(holdings)
        }
    
    @staticmethod
    def calculate_allocation_statistics(allocations: List[float]) -> Dict[str, float]:
        """
        Calculate allocation distribution statistics
        
        This replaces the statistics calculations found in investment_calculator.py
        
        Args:
            allocations: List of allocation percentages
            
        Returns:
            Dict with min, max, average, std deviation
        """
        if not allocations:
            return {
                'min_allocation': 0.0,
                'max_allocation': 0.0, 
                'avg_allocation': 0.0,
                'std_deviation': 0.0
            }
        
        min_alloc = min(allocations)
        max_alloc = max(allocations)
        avg_alloc = sum(allocations) / len(allocations)
        
        # Calculate standard deviation
        if len(allocations) > 1:
            variance = sum((x - avg_alloc) ** 2 for x in allocations) / len(allocations)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0.0
        
        return {
            'min_allocation': min_alloc,
            'max_allocation': max_alloc,
            'avg_allocation': avg_alloc,
            'std_deviation': std_dev
        }


class InvestmentValidation:
    """Validation utilities for investment operations"""
    
    @staticmethod
    def validate_investment_amount(amount: float, min_investment: float = None) -> Dict[str, Any]:
        """
        Validate investment amount against minimum requirements
        
        This replaces validation logic found across investment services
        
        Args:
            amount: Investment amount to validate
            min_investment: Minimum required (default from config)
            
        Returns:
            Dict with validation result and details
        """
        if min_investment is None:
            min_investment = InvestmentConfig.DEFAULT_MIN_INVESTMENT
        
        is_valid = amount >= min_investment
        
        return {
            'is_valid': is_valid,
            'amount': amount,
            'min_required': min_investment,
            'shortfall': max(0, min_investment - amount) if not is_valid else 0,
            'message': (f"Investment amount Rs.{amount:,.0f} is valid" if is_valid 
                       else f"Investment amount Rs.{amount:,.0f} is below minimum Rs.{min_investment:,.0f}")
        }
    
    @staticmethod
    def validate_stock_data(stock_data: Dict) -> Dict[str, Any]:
        """
        Validate stock data structure and values
        
        This consolidates stock data validation found across services
        
        Args:
            stock_data: Stock data dictionary
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ['symbol', 'price']
        for field in required_fields:
            if field not in stock_data or not stock_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate price
        if 'price' in stock_data:
            price = stock_data['price']
            normalized_price = FinancialCalculations.normalize_price_data(price)
            
            if normalized_price <= 0:
                errors.append(f"Invalid price: {price}")
            elif not FinancialCalculations.validate_price_range(normalized_price):
                warnings.append(f"Price {normalized_price} outside normal range")
        
        # Validate symbol
        if 'symbol' in stock_data:
            symbol = stock_data['symbol']
            if not isinstance(symbol, str) or len(symbol.strip()) == 0:
                errors.append(f"Invalid symbol: {symbol}")
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'message': 'Valid stock data' if is_valid else f"{len(errors)} validation errors"
        }