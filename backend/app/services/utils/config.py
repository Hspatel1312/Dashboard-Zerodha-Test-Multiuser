# backend/app/services/utils/config.py
"""
Centralized configuration for all investment services

This module consolidates all hardcoded configuration values that are currently
scattered across services. It provides a single place to manage all settings
while maintaining backward compatibility.
"""

from typing import Dict, Any
import os


class InvestmentConfig:
    """Main configuration class for investment services"""
    
    # Investment Amount Settings (from investment_calculator.py and services)
    DEFAULT_MIN_INVESTMENT = 200000  # Rs.2,00,000
    
    # Allocation Settings (from investment_calculator.py)
    DEFAULT_TARGET_ALLOCATION_PERCENT = 5.0  # 5% per stock
    DEFAULT_MIN_ALLOCATION_PERCENT = 3.5     # 5% - 1.5%
    DEFAULT_MAX_ALLOCATION_PERCENT = 6.5     # 5% + 1.5%
    ALLOCATION_FLEXIBILITY_PERCENT = 2.0     # ±2% flexibility around target
    
    # Special Stock Settings (GOLDBEES from investment_calculator.py)
    GOLDBEES_ALLOCATION_PERCENT = 50.0       # 50% allocation to GOLDBEES
    GOLDBEES_SYMBOL = "GOLDBEES"
    
    # Rebalancing Settings (from investment services)
    REBALANCING_THRESHOLD = 10000            # Rs.10,000 minimum for rebalancing
    
    # Price Validation Settings (from csv_service.py)
    MIN_VALID_PRICE = 0.1                    # Rs.0.10 minimum
    MAX_VALID_PRICE = 100000                 # Rs.1,00,000 maximum
    
    # Cache Settings (from various services)
    CSV_CACHE_DURATION_SECONDS = 300        # 5 minutes
    PRICE_CACHE_DURATION_SECONDS = 30       # 30 seconds
    
    # API Settings (from services)
    ZERODHA_TIMEOUT_SECONDS = 30            # 30 seconds timeout
    ZERODHA_BATCH_SIZE = 15                 # Batch size for bulk operations
    
    # Order Monitoring Settings (from live_order_service.py)
    ORDER_MONITORING_INTERVAL_SECONDS = 15  # Check every 15 seconds
    MAX_RETRY_ATTEMPTS = 3                  # Maximum retry attempts for failed orders
    
    # File Settings
    JSON_INDENT = 2                         # Standard JSON indentation
    BACKUP_RETENTION_DAYS = 30              # Keep backups for 30 days
    
    # Financial Calculation Settings
    CAGR_MIN_VALUE = -99.9                  # Minimum CAGR value for display
    CAGR_MAX_VALUE = 999.9                  # Maximum CAGR value for display
    PERCENTAGE_PRECISION = 2                # Decimal places for percentages
    
    # Logging Settings
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MAX_LOG_MESSAGE_LENGTH = 1000           # Truncate long log messages


class FilePathConfig:
    """Configuration for file paths used across services"""
    
    # Base directories
    USER_DATA_BASE_DIR = "user_data"
    GLOBAL_DATA_DIR = "data"
    BACKUP_DIR = "backups"
    LOGS_DIR = "logs"
    
    # File names (used in user-specific directories)
    SYSTEM_ORDERS_FILE = "system_orders.json"
    PORTFOLIO_STATE_FILE = "system_portfolio_state.json"
    CSV_HISTORY_FILE = "csv_history.json"
    FAILED_ORDERS_FILE = "failed_orders.json"
    LIVE_ORDERS_FILE = "live_orders.json"
    
    # Global files (shared across all users)
    GLOBAL_CSV_CACHE_FILE = os.path.join(GLOBAL_DATA_DIR, "csv_cache.json")
    GLOBAL_PRICE_CACHE_FILE = os.path.join(GLOBAL_DATA_DIR, "price_cache.json")
    
    @staticmethod
    def get_user_file_path(user_data_dir: str, file_type: str) -> str:
        """
        Get file path for user-specific files
        
        Args:
            user_data_dir: User's data directory
            file_type: Type of file ('orders', 'portfolio_state', 'csv_history', etc.)
            
        Returns:
            Full file path
        """
        file_mapping = {
            'orders': FilePathConfig.SYSTEM_ORDERS_FILE,
            'portfolio_state': FilePathConfig.PORTFOLIO_STATE_FILE,
            'csv_history': FilePathConfig.CSV_HISTORY_FILE,
            'failed_orders': FilePathConfig.FAILED_ORDERS_FILE,
            'live_orders': FilePathConfig.LIVE_ORDERS_FILE
        }
        
        file_name = file_mapping.get(file_type, f"{file_type}.json")
        return os.path.join(user_data_dir, file_name)


class ErrorCodes:
    """Standardized error codes used across services"""
    
    # Authentication errors
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Data errors
    PRICE_DATA_UNAVAILABLE = "PRICE_DATA_UNAVAILABLE"
    CSV_DATA_UNAVAILABLE = "CSV_DATA_UNAVAILABLE"
    INVALID_STOCK_DATA = "INVALID_STOCK_DATA"
    
    # Investment errors
    INSUFFICIENT_INVESTMENT_AMOUNT = "INSUFFICIENT_INVESTMENT_AMOUNT"
    PORTFOLIO_NOT_FOUND = "PORTFOLIO_NOT_FOUND"
    REBALANCING_NOT_NEEDED = "REBALANCING_NOT_NEEDED"
    
    # Order errors
    ORDER_PLACEMENT_FAILED = "ORDER_PLACEMENT_FAILED"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ORDER_ALREADY_EXECUTED = "ORDER_ALREADY_EXECUTED"
    
    # File errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    JSON_DECODE_ERROR = "JSON_DECODE_ERROR"
    
    # System errors
    SYSTEM_ERROR = "SYSTEM_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class LoggingConfig:
    """Configuration for logging across all services"""
    
    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    
    # Log prefixes for different contexts
    SINGLE_USER_PREFIX = ""
    MULTIUSER_PREFIX_FORMAT = "User {username} - "
    
    # Log message templates
    OPERATION_START_TEMPLATE = "[{level}] {prefix}Starting {operation}..."
    OPERATION_SUCCESS_TEMPLATE = "[SUCCESS] {prefix}{operation} completed successfully"
    OPERATION_ERROR_TEMPLATE = "[ERROR] {prefix}{operation} failed: {error}"
    
    @staticmethod
    def format_log_message(
        level: str,
        operation: str,
        message: str = "",
        user: str = None,
        include_timestamp: bool = False
    ) -> str:
        """
        Format log message consistently across services
        
        Args:
            level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR)
            operation: The operation being logged
            message: Additional message
            user: Username for multiuser services
            include_timestamp: Whether to include timestamp
            
        Returns:
            Formatted log message
        """
        prefix = LoggingConfig.MULTIUSER_PREFIX_FORMAT.format(username=user) if user else ""
        
        if include_timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime(InvestmentConfig.LOG_DATE_FORMAT)
            base_message = f"[{timestamp}] [{level}] {prefix}{operation}"
        else:
            base_message = f"[{level}] {prefix}{operation}"
            
        if message:
            return f"{base_message}: {message}"
        return base_message


class EnvironmentConfig:
    """Environment-specific configuration"""
    
    def __init__(self):
        # Read from environment variables with fallbacks
        self.debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Override settings for development
        if self.debug_mode:
            InvestmentConfig.CSV_CACHE_DURATION_SECONDS = 60  # Shorter cache in debug
            InvestmentConfig.ORDER_MONITORING_INTERVAL_SECONDS = 5  # More frequent monitoring
            
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug_mode
    
    def get_log_level(self) -> str:
        """Get current log level"""
        return self.log_level


# Global environment config instance
ENV_CONFIG = EnvironmentConfig()


class ConfigValidator:
    """Validate configuration values"""
    
    @staticmethod
    def validate_investment_amount(amount: float) -> bool:
        """Validate investment amount is above minimum"""
        return amount >= InvestmentConfig.DEFAULT_MIN_INVESTMENT
    
    @staticmethod
    def validate_allocation_percent(percent: float) -> bool:
        """Validate allocation percentage is within reasonable bounds"""
        return 0.1 <= percent <= 100.0
    
    @staticmethod
    def validate_price(price: float) -> bool:
        """Validate price is within acceptable range"""
        return InvestmentConfig.MIN_VALID_PRICE <= price <= InvestmentConfig.MAX_VALID_PRICE
    
    @staticmethod
    def get_validation_summary() -> Dict[str, Any]:
        """Get summary of all configuration validation rules"""
        return {
            "min_investment": InvestmentConfig.DEFAULT_MIN_INVESTMENT,
            "price_range": {
                "min": InvestmentConfig.MIN_VALID_PRICE,
                "max": InvestmentConfig.MAX_VALID_PRICE
            },
            "allocation_range": {
                "min": InvestmentConfig.DEFAULT_MIN_ALLOCATION_PERCENT,
                "target": InvestmentConfig.DEFAULT_TARGET_ALLOCATION_PERCENT,
                "max": InvestmentConfig.DEFAULT_MAX_ALLOCATION_PERCENT,
                "flexibility": InvestmentConfig.ALLOCATION_FLEXIBILITY_PERCENT
            },
            "special_allocations": {
                "goldbees_percent": InvestmentConfig.GOLDBEES_ALLOCATION_PERCENT,
                "goldbees_symbol": InvestmentConfig.GOLDBEES_SYMBOL
            }
        }


# Export commonly used configurations for easy importing
MIN_INVESTMENT = InvestmentConfig.DEFAULT_MIN_INVESTMENT
TARGET_ALLOCATION = InvestmentConfig.DEFAULT_TARGET_ALLOCATION_PERCENT
ALLOCATION_FLEXIBILITY = InvestmentConfig.ALLOCATION_FLEXIBILITY_PERCENT
GOLDBEES_ALLOCATION = InvestmentConfig.GOLDBEES_ALLOCATION_PERCENT