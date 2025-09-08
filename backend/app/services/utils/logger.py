# backend/app/services/utils/logger.py
"""
Centralized logging utilities for all investment services

This module provides standardized logging that is currently inconsistent
across all services. It maintains backward compatibility with existing
print() statements while providing enhanced logging capabilities.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Any, Dict
from .config import LoggingConfig, InvestmentConfig, ENV_CONFIG


class ServiceLogger:
    """Enhanced logging for investment services"""
    
    def __init__(
        self,
        service_name: str,
        user_context: Optional[str] = None,
        log_to_file: bool = True,
        console_output: bool = True
    ):
        """
        Initialize service logger
        
        Args:
            service_name: Name of the service (e.g., 'investment_service')
            user_context: User context for multiuser services (e.g., 'User john_doe')
            log_to_file: Whether to log to file
            console_output: Whether to output to console (maintains existing behavior)
        """
        self.service_name = service_name
        self.user_context = user_context
        self.console_output = console_output
        
        # Setup file logging if requested
        if log_to_file:
            self._setup_file_logging()
        else:
            self.file_logger = None
    
    def _setup_file_logging(self):
        """Setup file logging with rotation"""
        try:
            # Create logs directory
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # Create logger name
            logger_name = f"{self.service_name}"
            if self.user_context:
                # Sanitize user context for filename
                user_safe = self.user_context.replace(" ", "_").replace("/", "_")
                logger_name = f"{self.service_name}_{user_safe}"
            
            # Setup file logger
            self.file_logger = logging.getLogger(logger_name)
            self.file_logger.setLevel(getattr(logging, ENV_CONFIG.get_log_level(), logging.INFO))
            
            # Avoid duplicate handlers
            if not self.file_logger.handlers:
                # File handler with daily rotation
                log_file = os.path.join(log_dir, f"{logger_name}.log")
                handler = logging.FileHandler(log_file)
                
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt=InvestmentConfig.LOG_DATE_FORMAT
                )
                handler.setFormatter(formatter)
                self.file_logger.addHandler(handler)
                
        except Exception as e:
            print(f"[WARNING] Failed to setup file logging: {e}")
            self.file_logger = None
    
    def _format_message(self, level: str, operation: str, message: str = "") -> str:
        """Format message consistently with existing patterns"""
        return LoggingConfig.format_log_message(
            level=level,
            operation=operation,
            message=message,
            user=self.user_context
        )
    
    def _log_to_file(self, level: str, message: str):
        """Log to file if file logger is available"""
        if self.file_logger:
            try:
                log_method = getattr(self.file_logger, level.lower(), self.file_logger.info)
                log_method(message)
            except Exception:
                pass  # Silent failure for file logging
    
    def _safe_print(self, message: str):
        """Safely print message handling Unicode issues"""
        if self.console_output:
            try:
                print(message)
            except UnicodeEncodeError:
                print(message.encode('utf-8', errors='replace').decode('utf-8'))
    
    # Main logging methods that match existing patterns
    
    def info(self, operation: str, message: str = ""):
        """Log info message (replaces most print() statements)"""
        formatted = self._format_message("INFO", operation, message)
        self._safe_print(formatted)
        self._log_to_file("info", formatted)
    
    def success(self, operation: str, message: str = ""):
        """Log success message (replaces [SUCCESS] print statements)"""
        formatted = self._format_message("SUCCESS", operation, message)
        self._safe_print(formatted)
        self._log_to_file("info", formatted)
    
    def warning(self, operation: str, message: str = ""):
        """Log warning message (replaces [WARNING] print statements)"""
        formatted = self._format_message("WARNING", operation, message)
        self._safe_print(formatted)
        self._log_to_file("warning", formatted)
    
    def error(self, operation: str, message: str = "", exception: Optional[Exception] = None):
        """Log error message (replaces [ERROR] print statements)"""
        if exception:
            message = f"{message}: {str(exception)}" if message else str(exception)
        
        formatted = self._format_message("ERROR", operation, message)
        self._safe_print(formatted)
        self._log_to_file("error", formatted)
        
        # Log stack trace to file only
        if exception and self.file_logger and ENV_CONFIG.is_development():
            import traceback
            self.file_logger.error(f"Stack trace: {traceback.format_exc()}")
    
    def debug(self, operation: str, message: str = ""):
        """Log debug message (only in debug mode)"""
        if ENV_CONFIG.is_development():
            formatted = self._format_message("DEBUG", operation, message)
            self._safe_print(formatted)
            self._log_to_file("debug", formatted)
    
    # Specialized logging methods for common patterns
    
    def log_operation_start(self, operation: str, details: Optional[Dict] = None):
        """Log the start of an operation"""
        message = f"Starting {operation}"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"
        self.info(operation, message)
    
    def log_operation_success(self, operation: str, details: Optional[Dict] = None):
        """Log successful completion of an operation"""
        message = f"{operation} completed successfully"
        if details:
            detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({detail_str})"
        self.success(operation, message)
    
    def log_operation_error(self, operation: str, exception: Exception, context: Optional[Dict] = None):
        """Log operation failure"""
        message = f"{operation} failed"
        if context:
            context_str = ", ".join(f"{k}={v}" for k, v in context.items())
            message += f" (context: {context_str})"
        self.error(operation, message, exception)
    
    def log_data_operation(self, operation: str, count: int, item_type: str = "items"):
        """Log data operations (loading/saving files, etc.)"""
        message = f"{count} {item_type}"
        if operation.startswith("load"):
            self.info(operation, f"Loaded {message}")
        elif operation.startswith("save"):
            self.info(operation, f"Saved {message}")
        else:
            self.info(operation, f"Processed {message}")
    
    def log_financial_metric(self, metric_name: str, value: float, symbol: str = "", format_as_currency: bool = False):
        """Log financial metrics consistently"""
        if format_as_currency:
            formatted_value = f"Rs.{value:,.2f}"
        elif metric_name.lower().endswith(('percent', 'percentage', '%')):
            formatted_value = f"{value:.2f}%"
        else:
            formatted_value = f"{value:,.2f}"
            
        symbol_part = f" for {symbol}" if symbol else ""
        self.info("financial_metric", f"{metric_name}: {formatted_value}{symbol_part}")


class LoggerFactory:
    """Factory for creating service loggers"""
    
    _loggers = {}  # Cache for logger instances
    
    @classmethod
    def get_logger(
        cls,
        service_name: str,
        user_context: Optional[str] = None,
        **kwargs
    ) -> ServiceLogger:
        """
        Get or create a logger for a service
        
        Args:
            service_name: Name of the service
            user_context: User context for multiuser services
            **kwargs: Additional arguments for ServiceLogger
            
        Returns:
            ServiceLogger instance
        """
        cache_key = f"{service_name}_{user_context or 'global'}"
        
        if cache_key not in cls._loggers:
            cls._loggers[cache_key] = ServiceLogger(
                service_name=service_name,
                user_context=user_context,
                **kwargs
            )
        
        return cls._loggers[cache_key]
    
    @classmethod
    def get_investment_service_logger(cls, user_context: Optional[str] = None) -> ServiceLogger:
        """Get logger for investment services"""
        return cls.get_logger("investment_service", user_context)
    
    @classmethod
    def get_multiuser_investment_service_logger(cls, username: str) -> ServiceLogger:
        """Get logger for multiuser investment service"""
        return cls.get_logger("multiuser_investment_service", f"User {username}")
    
    @classmethod
    def get_csv_service_logger(cls) -> ServiceLogger:
        """Get logger for CSV service"""
        return cls.get_logger("csv_service")
    
    @classmethod
    def get_portfolio_service_logger(cls, user_context: Optional[str] = None) -> ServiceLogger:
        """Get logger for portfolio services"""
        return cls.get_logger("portfolio_service", user_context)
    
    @classmethod
    def get_live_order_service_logger(cls, user_context: Optional[str] = None) -> ServiceLogger:
        """Get logger for live order service"""
        return cls.get_logger("live_order_service", user_context)


# Backward compatibility - provide direct logging functions that match existing patterns
def log_info(message: str, service: str = "unknown", user: str = None):
    """Direct info logging function for backward compatibility"""
    logger = LoggerFactory.get_logger(service, f"User {user}" if user else None)
    logger.info("operation", message)


def log_success(message: str, service: str = "unknown", user: str = None):
    """Direct success logging function for backward compatibility"""
    logger = LoggerFactory.get_logger(service, f"User {user}" if user else None)
    logger.success("operation", message)


def log_error(message: str, service: str = "unknown", user: str = None, exception: Exception = None):
    """Direct error logging function for backward compatibility"""
    logger = LoggerFactory.get_logger(service, f"User {user}" if user else None)
    logger.error("operation", message, exception)


def log_warning(message: str, service: str = "unknown", user: str = None):
    """Direct warning logging function for backward compatibility"""
    logger = LoggerFactory.get_logger(service, f"User {user}" if user else None)
    logger.warning("operation", message)


def safe_print(message: str, fallback: str = "Unicode encoding error"):
    """Safe print function for Unicode issues (backward compatibility)"""
    try:
        print(message)
    except UnicodeEncodeError:
        print(fallback)