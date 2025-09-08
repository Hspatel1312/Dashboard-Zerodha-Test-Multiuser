# backend/app/services/base/zerodha_integration_mixin.py
"""
Zerodha integration mixin for investment services

This mixin provides standardized Zerodha API integration that is currently
duplicated across 6+ services. Services can inherit this to get consistent
authentication handling, connection management, and error handling.
"""

from typing import Any, Dict, Optional, Union
from abc import ABC

# Import our foundation utilities
from ..utils.config import InvestmentConfig, ErrorCodes
from ..utils.date_time_utils import DateTimeUtils


class ZerodhaIntegrationMixin(ABC):
    """
    Mixin providing standardized Zerodha API integration for investment services
    
    This eliminates the duplicate Zerodha handling patterns found across:
    - csv_service.py _get_valid_kite_instance() (lines 244-292)
    - live_order_service.py _get_kite_instance() (lines 26-48)
    - multiuser_investment_service.py (Zerodha connection checks)
    - investment_service.py (Zerodha connection checks)
    - portfolio_service.py (Zerodha connection handling)
    
    Services can inherit this mixin to get:
    - Standardized authentication checking
    - Connection validation and retry logic
    - Consistent error handling
    - API timeout management
    - Connection pooling (future enhancement)
    """
    
    def __init__(self, zerodha_auth=None, *args, **kwargs):
        """
        Initialize mixin - must be called by inheriting class
        
        Args:
            zerodha_auth: Zerodha authentication service instance
        """
        super().__init__(*args, **kwargs)
        
        self.zerodha_auth = zerodha_auth
        self._kite_instance_cache = None
        self._last_connection_check = None
        self._connection_check_interval = InvestmentConfig.ORDER_MONITORING_INTERVAL_SECONDS
    
    # Core Authentication Methods
    
    def is_zerodha_authenticated(self) -> bool:
        """
        Check if Zerodha is authenticated
        
        This replaces the repeated pattern found across services:
        if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            return (self.zerodha_auth is not None and 
                   self.zerodha_auth.is_authenticated())
        except Exception as e:
            if hasattr(self, 'log_warning'):
                self.log_warning("authentication_check", f"Error checking authentication: {e}")
            return False
    
    def require_zerodha_authentication(self, operation: str = "zerodha_operation") -> Dict[str, Any]:
        """
        Check authentication and return error response if not authenticated
        
        This replaces the repeated pattern:
        if not self.zerodha_auth.is_authenticated():
            return {"success": False, "error": "Zerodha authentication required"}
        
        Args:
            operation: Name of operation requiring authentication
            
        Returns:
            None if authenticated, error response if not authenticated
        """
        if not self.is_zerodha_authenticated():
            if hasattr(self, 'create_authentication_error'):
                return self.create_authentication_error(operation)
            else:
                return {
                    "success": False,
                    "error": "Zerodha authentication required",
                    "error_code": ErrorCodes.AUTHENTICATION_REQUIRED,
                    "status": "AUTHENTICATION_REQUIRED"
                }
        return None
    
    # Connection Management
    
    def get_validated_kite_instance(
        self, 
        force_refresh: bool = False,
        test_connection: bool = True
    ) -> Optional[Any]:
        """
        Get validated Kite instance with connection testing
        
        This replaces the complex connection logic found in:
        - csv_service.py _get_valid_kite_instance() (lines 244-292)
        - live_order_service.py _get_kite_instance() (lines 26-48)
        
        Args:
            force_refresh: Whether to force refresh the connection
            test_connection: Whether to test the connection
            
        Returns:
            Validated Kite instance or None if unavailable
        """
        try:
            # Check authentication first
            if not self.is_zerodha_authenticated():
                if hasattr(self, 'log_error'):
                    self.log_error("kite_connection", Exception("Zerodha not authenticated"))
                return None
            
            # Check if we need to refresh cached instance
            if force_refresh or self._should_refresh_connection():
                self._kite_instance_cache = None
            
            # Use cached instance if available
            if self._kite_instance_cache and not force_refresh:
                return self._kite_instance_cache
            
            # Get fresh Kite instance
            kite = self.zerodha_auth.get_kite_instance()
            if not kite:
                if hasattr(self, 'log_error'):
                    self.log_error("kite_connection", Exception("No Kite instance available after authentication"))
                return None
            
            # Test connection if requested
            if test_connection:
                if self._test_kite_connection(kite):
                    self._kite_instance_cache = kite
                    self._last_connection_check = DateTimeUtils.get_current_timestamp()
                    return kite
                else:
                    # Connection test failed, try token refresh
                    return self._handle_connection_failure(kite)
            else:
                # Skip connection test, assume it works
                self._kite_instance_cache = kite
                return kite
                
        except Exception as e:
            if hasattr(self, 'log_error'):
                self.log_error("kite_connection", e)
            return None
    
    def _test_kite_connection(self, kite) -> bool:
        """
        Test Kite connection with profile call
        
        This replaces the connection testing pattern found across services
        """
        try:
            profile = kite.profile()
            username = profile.get('user_name', 'Unknown')
            
            if hasattr(self, 'log_success'):
                self.log_success("kite_connection_test", f"Connection verified for user: {username}")
            
            return True
            
        except Exception as e:
            if hasattr(self, 'log_warning'):
                self.log_warning("kite_connection_test", f"Connection test failed: {e}")
            return False
    
    def _handle_connection_failure(self, kite) -> Optional[Any]:
        """
        Handle connection failure by attempting token refresh
        
        This implements the retry logic found in csv_service.py
        """
        try:
            if hasattr(self, 'log_info'):
                self.log_info("kite_connection_retry", "Attempting token refresh...")
            
            # Try to refresh token
            refreshed_kite = self.zerodha_auth.force_refresh_token()
            if refreshed_kite:
                # Test the refreshed connection
                if self._test_kite_connection(refreshed_kite):
                    self._kite_instance_cache = refreshed_kite
                    self._last_connection_check = DateTimeUtils.get_current_timestamp()
                    
                    if hasattr(self, 'log_success'):
                        self.log_success("kite_connection_retry", "Token refreshed successfully")
                    
                    return refreshed_kite
            
            if hasattr(self, 'log_error'):
                self.log_error("kite_connection_retry", Exception("Token refresh failed"))
            return None
            
        except Exception as e:
            if hasattr(self, 'log_error'):
                self.log_error("kite_connection_retry", e)
            return None
    
    def _should_refresh_connection(self) -> bool:
        """Check if connection should be refreshed based on time interval"""
        if not self._last_connection_check:
            return True
        
        try:
            last_check = DateTimeUtils.safe_parse_date(self._last_connection_check)
            seconds_since_check = DateTimeUtils.calculate_days_between(last_check) * 24 * 3600
            return seconds_since_check > self._connection_check_interval
        except Exception:
            return True  # Refresh on error
    
    # API Operation Helpers
    
    def execute_kite_operation(
        self, 
        operation_name: str,
        kite_method: str,
        *args,
        retry_on_failure: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute Kite API operation with standardized error handling
        
        This provides a consistent pattern for all Zerodha API calls
        
        Args:
            operation_name: Name of operation for logging
            kite_method: Name of Kite method to call
            *args: Arguments for the Kite method
            retry_on_failure: Whether to retry on authentication failure
            **kwargs: Keyword arguments for the Kite method
            
        Returns:
            Dict with success status and result/error
        """
        try:
            # Get validated Kite instance
            kite = self.get_validated_kite_instance()
            if not kite:
                return {
                    "success": False,
                    "error": "Zerodha connection not available",
                    "error_code": ErrorCodes.AUTHENTICATION_REQUIRED
                }
            
            # Execute the operation
            method = getattr(kite, kite_method)
            result = method(*args, **kwargs)
            
            if hasattr(self, 'log_success'):
                self.log_success(operation_name, f"Kite {kite_method} executed successfully")
            
            return {
                "success": True,
                "result": result,
                "operation": operation_name
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's an authentication error
            if "authentication" in error_msg.lower() or "token" in error_msg.lower():
                if retry_on_failure:
                    # Try with fresh connection
                    if hasattr(self, 'log_info'):
                        self.log_info(operation_name, "Retrying with fresh connection...")
                    
                    return self.execute_kite_operation(
                        operation_name, kite_method, *args, 
                        retry_on_failure=False, **kwargs
                    )
                else:
                    error_code = ErrorCodes.AUTHENTICATION_FAILED
            else:
                error_code = ErrorCodes.NETWORK_ERROR
            
            if hasattr(self, 'log_error'):
                self.log_error(operation_name, e)
            
            return {
                "success": False,
                "error": f"Kite {kite_method} failed: {error_msg}",
                "error_code": error_code,
                "operation": operation_name
            }
    
    # Specialized API Methods
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Get Zerodha profile information"""
        return self.execute_kite_operation("get_profile", "profile")
    
    def get_margins_info(self) -> Dict[str, Any]:
        """Get margins information"""
        return self.execute_kite_operation("get_margins", "margins")
    
    def get_positions_info(self) -> Dict[str, Any]:
        """Get positions information"""
        return self.execute_kite_operation("get_positions", "positions")
    
    def get_holdings_info(self) -> Dict[str, Any]:
        """Get holdings information"""
        return self.execute_kite_operation("get_holdings", "holdings")
    
    def get_orders_info(self) -> Dict[str, Any]:
        """Get orders information"""
        return self.execute_kite_operation("get_orders", "orders")
    
    def get_quote_info(self, instruments: list) -> Dict[str, Any]:
        """
        Get quote information for instruments
        
        Args:
            instruments: List of instruments to get quotes for
            
        Returns:
            Dict with quote information
        """
        return self.execute_kite_operation("get_quote", "quote", instruments)
    
    def place_order_on_zerodha(self, order_params: Dict) -> Dict[str, Any]:
        """
        Place order on Zerodha with standardized error handling
        
        Args:
            order_params: Order parameters dict
            
        Returns:
            Dict with order placement result
        """
        return self.execute_kite_operation("place_order", "place_order", **order_params)
    
    def modify_order_on_zerodha(self, order_id: str, order_params: Dict) -> Dict[str, Any]:
        """
        Modify order on Zerodha
        
        Args:
            order_id: Order ID to modify
            order_params: Modified order parameters
            
        Returns:
            Dict with modification result
        """
        return self.execute_kite_operation("modify_order", "modify_order", 
                                         order_id=order_id, **order_params)
    
    def cancel_order_on_zerodha(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel order on Zerodha
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Dict with cancellation result
        """
        return self.execute_kite_operation("cancel_order", "cancel_order", order_id=order_id)
    
    def get_order_history(self, order_id: str) -> Dict[str, Any]:
        """
        Get order history from Zerodha
        
        Args:
            order_id: Order ID to get history for
            
        Returns:
            Dict with order history
        """
        return self.execute_kite_operation("get_order_history", "order_history", order_id=order_id)
    
    # Connection Health and Diagnostics
    
    def check_connection_health(self) -> Dict[str, Any]:
        """
        Check Zerodha connection health
        
        Returns:
            Dict with connection health information
        """
        health_info = {
            "authenticated": self.is_zerodha_authenticated(),
            "last_check": self._last_connection_check,
            "connection_cached": self._kite_instance_cache is not None,
            "check_interval": self._connection_check_interval
        }
        
        if health_info["authenticated"]:
            # Test connection
            kite = self.get_validated_kite_instance(test_connection=True)
            health_info["connection_valid"] = kite is not None
            
            if kite:
                # Get additional info
                profile_result = self.get_profile_info()
                if profile_result["success"]:
                    health_info["user_info"] = {
                        "username": profile_result["result"].get("user_name"),
                        "user_id": profile_result["result"].get("user_id"),
                        "broker": profile_result["result"].get("broker")
                    }
        else:
            health_info["connection_valid"] = False
        
        return health_info
    
    def reset_connection(self):
        """
        Reset connection cache and force fresh connection on next use
        """
        self._kite_instance_cache = None
        self._last_connection_check = None
        
        if hasattr(self, 'log_info'):
            self.log_info("connection_reset", "Zerodha connection cache reset")
    
    # Configuration and Settings
    
    def configure_connection_settings(
        self,
        check_interval: int = None,
        timeout: int = None,
        retry_attempts: int = None
    ):
        """
        Configure connection settings
        
        Args:
            check_interval: How often to check connection (seconds)
            timeout: API timeout (seconds)
            retry_attempts: Number of retry attempts
        """
        if check_interval is not None:
            self._connection_check_interval = check_interval
        
        # Additional configuration can be added here
        if hasattr(self, 'log_info'):
            self.log_info("connection_config", f"Updated connection settings")


# Specialized Mixins for Different Use Cases

class LiveTradingZerodhaIntegrationMixin(ZerodhaIntegrationMixin):
    """
    Specialized mixin for live trading operations
    
    Provides additional methods for order placement and monitoring
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._order_placement_timeout = InvestmentConfig.ZERODHA_TIMEOUT_SECONDS
    
    def place_market_order(
        self,
        symbol: str,
        action: str,  # "BUY" or "SELL"
        quantity: int,
        product: str = "CNC"
    ) -> Dict[str, Any]:
        """
        Place market order with standardized parameters
        
        Args:
            symbol: Trading symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            product: Product type (default: CNC for delivery)
            
        Returns:
            Dict with order placement result
        """
        try:
            kite = self.get_validated_kite_instance()
            if not kite:
                return {
                    "success": False,
                    "error": "Zerodha connection not available"
                }
            
            order_params = {
                "variety": kite.VARIETY_REGULAR,
                "exchange": kite.EXCHANGE_NSE,
                "tradingsymbol": symbol,
                "transaction_type": kite.TRANSACTION_TYPE_BUY if action == "BUY" else kite.TRANSACTION_TYPE_SELL,
                "quantity": quantity,
                "product": getattr(kite, f"PRODUCT_{product}", kite.PRODUCT_CNC),
                "order_type": kite.ORDER_TYPE_MARKET
            }
            
            return self.place_order_on_zerodha(order_params)
            
        except Exception as e:
            if hasattr(self, 'handle_operation_error'):
                return self.handle_operation_error("place_market_order", e)
            else:
                return {"success": False, "error": str(e)}


class DataFetchingZerodhaIntegrationMixin(ZerodhaIntegrationMixin):
    """
    Specialized mixin for data fetching operations (portfolio, prices, etc.)
    
    Optimized for read-only operations with caching
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data_cache = {}
        self._cache_timeout = 300  # 5 minutes default
    
    def get_cached_data(self, data_type: str, fetch_function, *args, **kwargs):
        """
        Get data with caching support
        
        Args:
            data_type: Type of data for caching
            fetch_function: Function to fetch fresh data
            *args: Arguments for fetch function
            **kwargs: Keyword arguments for fetch function
            
        Returns:
            Cached or fresh data
        """
        cache_key = f"{data_type}_{hash(str(args) + str(sorted(kwargs.items())))}"
        
        # Check if we have valid cached data
        if cache_key in self._data_cache:
            cached_item = self._data_cache[cache_key]
            cache_time = DateTimeUtils.safe_parse_date(cached_item['timestamp'])
            
            if not DateTimeUtils.is_cache_expired(cache_time):
                return cached_item['data']
        
        # Fetch fresh data
        fresh_data = fetch_function(*args, **kwargs)
        
        # Cache the result if successful
        if fresh_data.get('success'):
            self._data_cache[cache_key] = {
                'data': fresh_data,
                'timestamp': DateTimeUtils.get_current_timestamp()
            }
        
        return fresh_data