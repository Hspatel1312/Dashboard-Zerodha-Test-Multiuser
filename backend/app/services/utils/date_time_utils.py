# backend/app/services/utils/date_time_utils.py
"""
Centralized date/time utilities for all investment services

This module consolidates date/time handling logic that is currently
inconsistent across 8+ services. Each method replaces specific patterns
found in the codebase.
"""

from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Tuple, Dict, Any
import re
from .config import InvestmentConfig


class DateTimeUtils:
    """Centralized date/time operations for all investment services"""
    
    # Common date format patterns found across services
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
    ISO_FORMAT_WITH_MS = "%Y-%m-%dT%H:%M:%S.%f"
    DATE_ONLY_FORMAT = "%Y-%m-%d"
    DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"
    CSV_DATE_FORMAT = "%d/%m/%Y"
    
    @staticmethod
    def get_current_timestamp() -> str:
        """
        Get standardized current timestamp
        
        This replaces the repeated pattern found across all services:
        datetime.now().isoformat()
        
        Found in:
        - multiuser_investment_service.py (lines 255, 645, 984)
        - investment_service.py (multiple places)
        - live_order_service.py (timestamp generation)
        - portfolio_metrics_service.py (timestamp fields)
        
        Returns:
            ISO format timestamp string
        """
        return datetime.now().isoformat()
    
    @staticmethod
    def safe_parse_date(
        date_input: Union[str, datetime, None], 
        default: Optional[datetime] = None,
        formats_to_try: Optional[list] = None
    ) -> datetime:
        """
        Safely parse date from various formats with fallback
        
        This replaces the complex date parsing logic found in:
        - portfolio_metrics_service.py _calculate_holding_period() (lines 153-187)
        - Multiple services with inconsistent date parsing
        
        Args:
            date_input: Date in various formats (string, datetime, or None)
            default: Default datetime if parsing fails (default: now)
            formats_to_try: List of date formats to attempt
            
        Returns:
            Parsed datetime object
        """
        if default is None:
            default = datetime.now()
        
        # If already datetime, return as-is
        if isinstance(date_input, datetime):
            return date_input
        
        # If None or empty, return default
        if not date_input:
            return default
        
        # If not string, try to convert
        if not isinstance(date_input, str):
            try:
                return datetime.fromisoformat(str(date_input))
            except (ValueError, TypeError):
                return default
        
        date_str = date_input.strip()
        if not date_str:
            return default
        
        # Default formats to try (based on patterns found in codebase)
        if formats_to_try is None:
            formats_to_try = [
                DateTimeUtils.ISO_FORMAT_WITH_MS,  # 2023-12-01T10:30:00.123456
                DateTimeUtils.ISO_FORMAT,          # 2023-12-01T10:30:00
                DateTimeUtils.DISPLAY_FORMAT,      # 2023-12-01 10:30:00
                DateTimeUtils.DATE_ONLY_FORMAT,    # 2023-12-01
                DateTimeUtils.CSV_DATE_FORMAT,     # 01/12/2023
                "%d-%m-%Y",                        # 01-12-2023
                "%Y/%m/%d",                        # 2023/01/12
                "%m/%d/%Y"                         # 12/01/2023
            ]
        
        # Try ISO format first (most common in our codebase)
        try:
            # Handle Z timezone suffix
            clean_date = date_str.replace('Z', '')
            return datetime.fromisoformat(clean_date)
        except ValueError:
            pass
        
        # Try each format
        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all parsing fails, return default
        return default
    
    @staticmethod
    def calculate_days_between(start_date: Union[str, datetime], end_date: Union[str, datetime] = None) -> int:
        """
        Calculate days between two dates
        
        This replaces the date difference calculations found in:
        - portfolio_metrics_service.py (holding period calculations)
        - Various services calculating investment periods
        
        Args:
            start_date: Start date (string or datetime)
            end_date: End date (string or datetime, default: now)
            
        Returns:
            Number of days between dates (minimum 1)
        """
        if end_date is None:
            end_date = datetime.now()
        
        start_dt = DateTimeUtils.safe_parse_date(start_date)
        end_dt = DateTimeUtils.safe_parse_date(end_date)
        
        try:
            delta = end_dt - start_dt
            return max(1, delta.days)  # Minimum 1 day (matches existing logic)
        except (TypeError, ValueError):
            return 1  # Fallback to 1 day
    
    @staticmethod
    def calculate_years_between(start_date: Union[str, datetime], end_date: Union[str, datetime] = None) -> float:
        """
        Calculate years between two dates (for CAGR calculations)
        
        This replaces the years calculation found in:
        - portfolio_metrics_service.py (CAGR calculations)
        - investment_service.py (annualized return calculations)
        
        Args:
            start_date: Start date
            end_date: End date (default: now)
            
        Returns:
            Number of years as float (minimum 1/365.25 for 1 day)
        """
        days = DateTimeUtils.calculate_days_between(start_date, end_date)
        return max(1/365.25, days / 365.25)  # Minimum ~0.003 years (1 day)
    
    @staticmethod
    def format_timestamp_for_display(timestamp: Union[str, datetime], format_type: str = "display") -> str:
        """
        Format timestamp for consistent display
        
        This standardizes timestamp display found across services
        
        Args:
            timestamp: Timestamp to format
            format_type: Type of format ('display', 'date_only', 'iso', 'filename_safe')
            
        Returns:
            Formatted timestamp string
        """
        dt = DateTimeUtils.safe_parse_date(timestamp)
        
        format_mapping = {
            'display': DateTimeUtils.DISPLAY_FORMAT,      # 2023-12-01 10:30:00
            'date_only': DateTimeUtils.DATE_ONLY_FORMAT,  # 2023-12-01
            'iso': DateTimeUtils.ISO_FORMAT,              # 2023-12-01T10:30:00
            'filename_safe': "%Y%m%d_%H%M%S",             # 20231201_103000
            'csv': DateTimeUtils.CSV_DATE_FORMAT          # 01/12/2023
        }
        
        fmt = format_mapping.get(format_type, DateTimeUtils.DISPLAY_FORMAT)
        
        try:
            return dt.strftime(fmt)
        except (ValueError, TypeError):
            return str(dt)
    
    @staticmethod
    def is_same_day(date1: Union[str, datetime], date2: Union[str, datetime]) -> bool:
        """
        Check if two dates are on the same day
        
        Useful for grouping operations by day
        
        Args:
            date1: First date
            date2: Second date
            
        Returns:
            True if dates are on same day
        """
        dt1 = DateTimeUtils.safe_parse_date(date1)
        dt2 = DateTimeUtils.safe_parse_date(date2)
        
        return dt1.date() == dt2.date()
    
    @staticmethod
    def get_date_range_description(start_date: Union[str, datetime], end_date: Union[str, datetime] = None) -> str:
        """
        Get human-readable description of date range
        
        This creates consistent date range descriptions for logging and display
        
        Args:
            start_date: Start date
            end_date: End date (default: now)
            
        Returns:
            Human-readable date range description
        """
        if end_date is None:
            end_date = datetime.now()
        
        days = DateTimeUtils.calculate_days_between(start_date, end_date)
        
        if days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days < 30:
            weeks = days // 7
            remaining_days = days % 7
            if remaining_days == 0:
                return f"{weeks} week{'s' if weeks != 1 else ''}"
            else:
                return f"{weeks} week{'s' if weeks != 1 else ''} and {remaining_days} day{'s' if remaining_days != 1 else ''}"
        elif days < 365:
            months = days // 30
            remaining_days = days % 30
            if remaining_days < 7:
                return f"{months} month{'s' if months != 1 else ''}"
            else:
                return f"{months}+ month{'s' if months != 1 else ''}"
        else:
            years = days / 365.25
            return f"{years:.1f} year{'s' if years > 1 else ''}"
    
    @staticmethod
    def create_execution_time_data() -> Dict[str, Any]:
        """
        Create execution time data structure used across services
        
        This replaces the pattern found in investment services:
        execution_time = datetime.now().isoformat()
        
        Returns:
            Dict with timestamp data for order/operation tracking
        """
        now = datetime.now()
        return {
            'execution_time': now.isoformat(),
            'timestamp': now.isoformat(),
            'date': now.strftime(DateTimeUtils.DATE_ONLY_FORMAT),
            'formatted_time': now.strftime(DateTimeUtils.DISPLAY_FORMAT)
        }
    
    @staticmethod
    def calculate_holding_period_info(first_purchase_date: Union[str, datetime, None]) -> Dict[str, Any]:
        """
        Calculate comprehensive holding period information
        
        This replaces the holding period logic found in:
        - portfolio_metrics_service.py _calculate_holding_period()
        
        Args:
            first_purchase_date: Date of first purchase
            
        Returns:
            Dict with holding period details
        """
        if not first_purchase_date:
            # Default to 30 days ago (matches existing logic)
            default_date = datetime.now() - timedelta(days=30)
            first_purchase_dt = default_date
            is_estimated = True
        else:
            first_purchase_dt = DateTimeUtils.safe_parse_date(
                first_purchase_date, 
                default=datetime.now() - timedelta(days=30)
            )
            is_estimated = False
        
        now = datetime.now()
        days_held = DateTimeUtils.calculate_days_between(first_purchase_dt, now)
        years_held = DateTimeUtils.calculate_years_between(first_purchase_dt, now)
        
        return {
            'first_purchase_date': first_purchase_dt.isoformat(),
            'days_held': days_held,
            'years_held': years_held,
            'is_estimated': is_estimated,
            'holding_period_description': DateTimeUtils.get_date_range_description(first_purchase_dt, now),
            'formatted_first_purchase': DateTimeUtils.format_timestamp_for_display(first_purchase_dt, 'date_only')
        }
    
    @staticmethod
    def is_market_hours() -> bool:
        """
        Check if current time is during market hours
        
        This is useful for determining when to fetch live prices
        Note: This is a basic implementation - real market hours checking
        would need to consider holidays, timezone, etc.
        
        Returns:
            True if during basic market hours (9:15 AM to 3:30 PM IST on weekdays)
        """
        now = datetime.now()
        
        # Basic check - weekday and between 9:15 AM and 3:30 PM
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    @staticmethod
    def get_cache_expiry_time(duration_seconds: int = None) -> datetime:
        """
        Get cache expiry time
        
        This standardizes cache expiry calculations found across services
        
        Args:
            duration_seconds: Cache duration (default from config)
            
        Returns:
            DateTime when cache should expire
        """
        if duration_seconds is None:
            duration_seconds = InvestmentConfig.CSV_CACHE_DURATION_SECONDS
        
        return datetime.now() + timedelta(seconds=duration_seconds)
    
    @staticmethod
    def is_cache_expired(cache_time: Union[str, datetime]) -> bool:
        """
        Check if cache timestamp has expired
        
        This standardizes cache expiry checks across services
        
        Args:
            cache_time: Cache timestamp
            
        Returns:
            True if cache has expired
        """
        cache_dt = DateTimeUtils.safe_parse_date(cache_time)
        return datetime.now() > cache_dt


class TimestampTracker:
    """Utility for tracking operation timestamps across services"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = datetime.now()
        self.checkpoints = []
    
    def checkpoint(self, checkpoint_name: str):
        """Add a checkpoint timestamp"""
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds()
        self.checkpoints.append({
            'name': checkpoint_name,
            'timestamp': now.isoformat(),
            'elapsed_seconds': elapsed
        })
    
    def get_duration_summary(self) -> Dict[str, Any]:
        """Get summary of operation duration"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        return {
            'operation': self.operation_name,
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_seconds': total_duration,
            'checkpoints': self.checkpoints,
            'formatted_duration': f"{total_duration:.2f} seconds"
        }


class DateTimeValidation:
    """Validation utilities for date/time operations"""
    
    @staticmethod
    def validate_date_range(
        start_date: Union[str, datetime], 
        end_date: Union[str, datetime],
        max_range_days: int = 3650  # ~10 years
    ) -> Dict[str, Any]:
        """
        Validate date range for reasonableness
        
        Args:
            start_date: Start date
            end_date: End date
            max_range_days: Maximum allowed range in days
            
        Returns:
            Dict with validation results
        """
        start_dt = DateTimeUtils.safe_parse_date(start_date)
        end_dt = DateTimeUtils.safe_parse_date(end_date)
        
        errors = []
        warnings = []
        
        if start_dt > end_dt:
            errors.append("Start date is after end date")
        
        days_diff = (end_dt - start_dt).days
        if days_diff > max_range_days:
            errors.append(f"Date range too large: {days_diff} days (max: {max_range_days})")
        
        if days_diff < 1:
            warnings.append("Date range is less than 1 day")
        
        # Check if dates are too far in the future
        now = datetime.now()
        if start_dt > now + timedelta(days=1):
            warnings.append("Start date is in the future")
        if end_dt > now + timedelta(days=1):
            warnings.append("End date is in the future")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'days_difference': days_diff,
            'message': 'Valid date range' if len(errors) == 0 else f"{len(errors)} validation errors"
        }
    
    @staticmethod
    def validate_timestamp_format(timestamp_str: str) -> Dict[str, Any]:
        """
        Validate timestamp string format
        
        Args:
            timestamp_str: Timestamp string to validate
            
        Returns:
            Dict with validation results
        """
        if not isinstance(timestamp_str, str):
            return {
                'is_valid': False,
                'error': 'Timestamp must be a string',
                'parsed_date': None
            }
        
        parsed_date = DateTimeUtils.safe_parse_date(timestamp_str)
        
        # Check if parsing actually worked (not just defaulted)
        try:
            # Try to parse with strict ISO format
            datetime.fromisoformat(timestamp_str.replace('Z', ''))
            format_recognized = True
        except ValueError:
            format_recognized = False
        
        return {
            'is_valid': format_recognized,
            'parsed_date': parsed_date,
            'original_string': timestamp_str,
            'recognized_format': format_recognized,
            'message': 'Valid timestamp format' if format_recognized else 'Timestamp format not recognized'
        }