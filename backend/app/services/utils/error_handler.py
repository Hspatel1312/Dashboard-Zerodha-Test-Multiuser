# backend/app/services/utils/error_handler.py
"""
Centralized error handling utilities for all investment services

This module provides standardized error handling patterns that are currently
duplicated across all services. It's designed to be backward-compatible
and non-intrusive - existing code will continue to work unchanged.
"""

from typing import Dict, Optional, Any
from datetime import datetime
import traceback


class ErrorHandler:
    """Standardized error handling for all investment services"""
    
    @staticmethod
    def create_error_response(
        error_message: str,
        operation: str = "unknown_operation",
        user: Optional[str] = None,
        error_code: Optional[str] = None,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error response format
        
        Args:
            error_message: The error message
            operation: The operation that failed
            user: Username (for multiuser services)
            error_code: Specific error code (e.g., 'PRICE_DATA_UNAVAILABLE')
            additional_data: Any additional data to include
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            "success": False,
            "error": error_message,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        
        if user:
            response["user"] = user
            
        if error_code:
            response["error_code"] = error_code
            
        if additional_data:
            response.update(additional_data)
            
        return response
    
    @staticmethod
    def create_success_response(
        data: Any = None,
        message: str = "Operation completed successfully",
        operation: str = "unknown_operation", 
        user: Optional[str] = None,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create standardized success response format
        
        Args:
            data: The response data
            message: Success message
            operation: The operation that succeeded
            user: Username (for multiuser services)
            additional_data: Any additional data to include
            
        Returns:
            Standardized success response dictionary
        """
        response = {
            "success": True,
            "message": message,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
            
        if user:
            response["user"] = user
            
        if additional_data:
            response.update(additional_data)
            
        return response
    
    @staticmethod
    def log_and_create_error_response(
        exception: Exception,
        operation: str,
        user: Optional[str] = None,
        context: Optional[Dict] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """
        Log error and create standardized error response
        
        This method handles the common pattern found across all services:
        1. Log the error with proper formatting
        2. Create standardized error response
        3. Handle Unicode encoding issues
        
        Args:
            exception: The exception that occurred
            operation: The operation that failed
            user: Username (for multiuser services)
            context: Additional context for logging
            include_traceback: Whether to include full traceback
            
        Returns:
            Standardized error response dictionary
        """
        try:
            error_message = str(exception)
        except UnicodeEncodeError:
            error_message = "Unicode encoding error in exception message"
            
        # Create log message with proper user context
        if user:
            log_prefix = f"[ERROR] User {user} - {operation}"
        else:
            log_prefix = f"[ERROR] {operation}"
            
        # Log the error
        try:
            print(f"{log_prefix}: {error_message}")
            
            if context:
                print(f"   Context: {context}")
                
            if include_traceback:
                print(f"   Traceback: {traceback.format_exc()}")
                
        except UnicodeEncodeError:
            print(f"{log_prefix}: Unicode error in error message")
            
        # Create standardized response
        return ErrorHandler.create_error_response(
            error_message=f"Failed to {operation}: {error_message}",
            operation=operation,
            user=user,
            additional_data=context
        )
    
    @staticmethod
    def handle_price_data_error(
        error_data: Dict,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle the common PRICE_DATA_UNAVAILABLE error pattern
        
        This is used across multiple services when Zerodha price data is unavailable
        """
        return ErrorHandler.create_error_response(
            error_message=error_data.get('error_message', 'Live price data unavailable'),
            operation="price_data_fetch",
            user=user,
            error_code='PRICE_DATA_UNAVAILABLE',
            additional_data={
                'csv_info': error_data.get('csv_info', {}),
                'price_data_status': error_data.get('price_data_status', {}),
                'data_quality': {
                    'live_data_available': False,
                    'error_reason': error_data.get('error_message', 'Live price data unavailable')
                }
            }
        )
    
    @staticmethod
    def handle_authentication_error(
        user: Optional[str] = None,
        operation: str = "authentication"
    ) -> Dict[str, Any]:
        """
        Handle the common Zerodha authentication error pattern
        """
        return ErrorHandler.create_error_response(
            error_message="Zerodha authentication required",
            operation=operation,
            user=user,
            error_code="AUTHENTICATION_REQUIRED",
            additional_data={
                "status": "AUTHENTICATION_REQUIRED"
            }
        )
    
    @staticmethod
    def safe_unicode_print(message: str, fallback_message: str = "Unicode encoding error"):
        """
        Safely print messages that might have Unicode issues
        
        This addresses the Unicode encoding problems found across services
        """
        try:
            print(message)
        except UnicodeEncodeError:
            print(fallback_message)


# Backward compatibility - provide the old error response patterns
class LegacyErrorPatterns:
    """
    Legacy error response patterns for backward compatibility
    
    This ensures existing code continues to work while we migrate
    """
    
    @staticmethod
    def investment_service_error(error_message: str) -> Dict[str, Any]:
        """Legacy investment_service.py error format"""
        return {
            "status": "ERROR",
            "action_needed": "fix_error", 
            "message": f"Error: {error_message}",
            "error": error_message
        }
    
    @staticmethod
    def multiuser_service_error(error_message: str, user: str, operation: str) -> Dict[str, Any]:
        """Legacy multiuser_investment_service.py error format"""
        return {
            "success": False,
            "error": f"Failed to {operation}: {error_message}",
            "user": user
        }