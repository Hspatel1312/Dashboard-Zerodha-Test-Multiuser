# backend/app/services/base/base_service.py
"""
Base service class providing common functionality for all investment services

This class consolidates common patterns found across all services:
- Standardized error handling and logging
- Response formatting
- Configuration access
- Performance tracking
- User context management
"""

from abc import ABC
from typing import Dict, Any, Optional, Union
from datetime import datetime

# Import our foundation utilities
from ..utils.error_handler import ErrorHandler
from ..utils.logger import LoggerFactory, ServiceLogger
from ..utils.config import InvestmentConfig, ErrorCodes
from ..utils.date_time_utils import DateTimeUtils, TimestampTracker


class BaseService(ABC):
    """
    Base service class that all investment services should inherit from
    
    Provides:
    - Standardized error handling and response formatting
    - Consistent logging across all services
    - Configuration access
    - User context management
    - Performance tracking
    """
    
    def __init__(
        self, 
        service_name: str = None,
        user_context: Optional[str] = None,
        enable_performance_tracking: bool = False
    ):
        """
        Initialize base service
        
        Args:
            service_name: Name of the service (auto-detected if not provided)
            user_context: User context for multiuser services
            enable_performance_tracking: Whether to track operation performance
        """
        # Auto-detect service name from class name if not provided
        if service_name is None:
            service_name = self.__class__.__name__.lower().replace('service', '_service')
        
        self.service_name = service_name
        self.user_context = user_context
        self.enable_performance_tracking = enable_performance_tracking
        
        # Initialize logger
        self.logger = LoggerFactory.get_logger(service_name, user_context)
        
        # Performance tracking
        self._operation_trackers = {}
        
        # Configuration access
        self.config = InvestmentConfig()
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """
        Override this method in child classes for service-specific initialization
        This is called after base initialization is complete
        """
        pass
    
    # Standardized Response Methods
    
    def create_success_response(
        self, 
        data: Any = None,
        message: str = "Operation completed successfully",
        operation: str = None,
        **additional_data
    ) -> Dict[str, Any]:
        """
        Create standardized success response
        
        This replaces the inconsistent response formats across services
        
        Args:
            data: Response data
            message: Success message
            operation: Operation name for logging
            **additional_data: Additional fields to include
            
        Returns:
            Standardized success response
        """
        return ErrorHandler.create_success_response(
            data=data,
            message=message,
            operation=operation or "unknown_operation",
            user=self.user_context,
            additional_data=additional_data
        )
    
    def create_error_response(
        self,
        error_message: str,
        operation: str = None,
        error_code: str = None,
        **additional_data
    ) -> Dict[str, Any]:
        """
        Create standardized error response
        
        This replaces the inconsistent error formats across services
        
        Args:
            error_message: Error message
            operation: Operation that failed
            error_code: Specific error code
            **additional_data: Additional error context
            
        Returns:
            Standardized error response
        """
        return ErrorHandler.create_error_response(
            error_message=error_message,
            operation=operation or "unknown_operation",
            user=self.user_context,
            error_code=error_code,
            additional_data=additional_data
        )
    
    def handle_operation_error(
        self,
        operation: str,
        exception: Exception,
        context: Optional[Dict] = None,
        include_traceback: bool = None
    ) -> Dict[str, Any]:
        """
        Handle operation error with logging and response creation
        
        This replaces the repetitive try/except/log/return patterns across all services
        
        Args:
            operation: Operation name
            exception: The exception that occurred
            context: Additional context for debugging
            include_traceback: Whether to include traceback in logs
            
        Returns:
            Standardized error response
        """
        if include_traceback is None:
            include_traceback = self.config.debug_mode if hasattr(self.config, 'debug_mode') else False
            
        return ErrorHandler.log_and_create_error_response(
            exception=exception,
            operation=operation,
            user=self.user_context,
            context=context,
            include_traceback=include_traceback
        )
    
    # Specialized Error Response Methods
    
    def create_authentication_error(self, operation: str = "authentication") -> Dict[str, Any]:
        """Create standardized authentication error response"""
        return ErrorHandler.handle_authentication_error(
            user=self.user_context,
            operation=operation
        )
    
    def create_price_data_error(self, error_data: Dict) -> Dict[str, Any]:
        """Create standardized price data unavailable error response"""
        return ErrorHandler.handle_price_data_error(
            error_data=error_data,
            user=self.user_context
        )
    
    # Logging Methods
    
    def log_info(self, operation: str, message: str = "", **details):
        """Log info message with optional details"""
        if details:
            self.logger.log_operation_start(operation, details)
        else:
            self.logger.info(operation, message)
    
    def log_success(self, operation: str, message: str = "", **details):
        """Log success message with optional details"""
        if details:
            self.logger.log_operation_success(operation, details)
        else:
            self.logger.success(operation, message)
    
    def log_error(self, operation: str, exception: Exception, **context):
        """Log error with context"""
        self.logger.log_operation_error(operation, exception, context)
    
    def log_warning(self, operation: str, message: str = ""):
        """Log warning message"""
        self.logger.warning(operation, message)
    
    def log_debug(self, operation: str, message: str = ""):
        """Log debug message (only in debug mode)"""
        self.logger.debug(operation, message)
    
    def log_data_operation(self, operation: str, count: int, item_type: str = "items"):
        """Log data operations (loading/saving files, etc.)"""
        self.logger.log_data_operation(operation, count, item_type)
    
    def log_financial_metric(self, metric_name: str, value: float, symbol: str = "", format_as_currency: bool = False):
        """Log financial metrics consistently"""
        self.logger.log_financial_metric(metric_name, value, symbol, format_as_currency)
    
    # Performance Tracking Methods
    
    def start_operation_tracking(self, operation_name: str) -> str:
        """
        Start tracking operation performance
        
        Args:
            operation_name: Name of the operation to track
            
        Returns:
            Tracking ID for this operation
        """
        if not self.enable_performance_tracking:
            return None
            
        tracker_id = f"{operation_name}_{datetime.now().timestamp()}"
        self._operation_trackers[tracker_id] = TimestampTracker(operation_name)
        return tracker_id
    
    def add_tracking_checkpoint(self, tracker_id: str, checkpoint_name: str):
        """Add checkpoint to operation tracking"""
        if tracker_id and tracker_id in self._operation_trackers:
            self._operation_trackers[tracker_id].checkpoint(checkpoint_name)
    
    def finish_operation_tracking(self, tracker_id: str) -> Optional[Dict[str, Any]]:
        """
        Finish operation tracking and get summary
        
        Args:
            tracker_id: Tracking ID from start_operation_tracking
            
        Returns:
            Performance summary or None if tracking disabled
        """
        if not tracker_id or tracker_id not in self._operation_trackers:
            return None
            
        tracker = self._operation_trackers.pop(tracker_id)
        summary = tracker.get_duration_summary()
        
        # Log performance summary if operation took more than 1 second
        if summary['total_duration_seconds'] > 1.0:
            self.log_info(
                "performance_tracking", 
                f"{summary['operation']} took {summary['formatted_duration']}"
            )
        
        return summary
    
    # Utility Methods
    
    def get_current_timestamp(self) -> str:
        """Get standardized current timestamp"""
        return DateTimeUtils.get_current_timestamp()
    
    def safe_get_user_context(self) -> str:
        """Get user context safely for logging"""
        return self.user_context or "system"
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get service information for debugging"""
        return {
            'service_name': self.service_name,
            'user_context': self.user_context,
            'performance_tracking_enabled': self.enable_performance_tracking,
            'active_trackers': len(self._operation_trackers),
            'initialized_at': self.get_current_timestamp()
        }
    
    # Configuration Helper Methods
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback"""
        return getattr(self.config, key, default)
    
    def validate_investment_amount(self, amount: float) -> Dict[str, Any]:
        """Validate investment amount using configuration"""
        min_investment = self.get_config_value('DEFAULT_MIN_INVESTMENT', 200000)
        
        return {
            'is_valid': amount >= min_investment,
            'amount': amount,
            'min_required': min_investment,
            'message': (f"Valid investment amount: Rs.{amount:,.0f}" if amount >= min_investment
                       else f"Amount Rs.{amount:,.0f} below minimum Rs.{min_investment:,.0f}")
        }
    
    # Context Manager Support for Operations
    
    def operation_context(self, operation_name: str, track_performance: bool = None):
        """
        Context manager for operations with automatic error handling and logging
        
        Usage:
            with self.operation_context("fetch_portfolio_data") as ctx:
                # Operation code here
                ctx.set_result(data)
        """
        return ServiceOperationContext(
            service=self,
            operation_name=operation_name,
            track_performance=track_performance
        )


class ServiceOperationContext:
    """Context manager for service operations with automatic error handling"""
    
    def __init__(self, service: BaseService, operation_name: str, track_performance: bool = None):
        self.service = service
        self.operation_name = operation_name
        self.track_performance = track_performance if track_performance is not None else service.enable_performance_tracking
        self.tracker_id = None
        self.result = None
        self.error = None
    
    def __enter__(self):
        self.service.log_info(self.operation_name, "Starting operation")
        
        if self.track_performance:
            self.tracker_id = self.service.start_operation_tracking(self.operation_name)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred
            self.error = exc_val
            self.service.log_error(self.operation_name, exc_val)
        else:
            # Operation completed successfully
            self.service.log_success(self.operation_name, "Operation completed")
        
        if self.track_performance and self.tracker_id:
            self.service.finish_operation_tracking(self.tracker_id)
        
        return False  # Don't suppress exceptions
    
    def set_result(self, result: Any):
        """Set operation result"""
        self.result = result
    
    def checkpoint(self, checkpoint_name: str):
        """Add checkpoint to performance tracking"""
        if self.tracker_id:
            self.service.add_tracking_checkpoint(self.tracker_id, checkpoint_name)
    
    def get_result(self) -> Any:
        """Get operation result"""
        return self.result
    
    def has_error(self) -> bool:
        """Check if operation had an error"""
        return self.error is not None


# Backward Compatibility Helper
class LegacyServicePatterns:
    """
    Helper class to maintain backward compatibility while migrating services
    
    This allows gradual migration from existing patterns to the new base service
    """
    
    @staticmethod
    def wrap_existing_service_method(service_instance, method_name: str):
        """
        Wrap existing service method to use base service logging
        
        This allows existing services to benefit from standardized logging
        without changing their code structure
        """
        original_method = getattr(service_instance, method_name)
        
        def wrapped_method(*args, **kwargs):
            try:
                service_instance.log_info(method_name, f"Executing {method_name}")
                result = original_method(*args, **kwargs)
                service_instance.log_success(method_name, f"{method_name} completed")
                return result
            except Exception as e:
                service_instance.log_error(method_name, e)
                raise
        
        return wrapped_method