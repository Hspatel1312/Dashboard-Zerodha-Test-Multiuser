# backend/app/services/service_hub.py
"""
ServiceHub - Single Access Point for All Services

This class provides ONE centralized access point for all services in the investment 
rebalancing system, eliminating confusion about where to get services from.

Instead of:
- zerodha_auth_manager.get_user_auth(user)
- investment_service_manager.get_user_service(user, auth)

Use:
- service_hub.get_zerodha_auth(user)  
- service_hub.get_investment_service(user)

Key Benefits:
1. Single source of truth for service access
2. Simplified service discovery and management
3. Centralized service lifecycle management
4. Better error handling and debugging
5. Future-proof architecture for new services
"""

from typing import Optional, Dict, Any
from datetime import datetime

from ..database import UserDB
from .multiuser_zerodha_auth import zerodha_auth_manager, MultiUserZerodhaAuth
from .multiuser_investment_service import investment_service_manager, MultiUserInvestmentService
from .base.base_service import BaseService


class ServiceHub(BaseService):
    """
    Central hub for accessing all services in the investment rebalancing system
    
    This class provides a single, consistent interface for obtaining instances of
    all services (Zerodha auth, investment service, portfolio services, etc.)
    
    Usage:
        service_hub = ServiceHub()
        
        # Get services for a user
        zerodha_auth = service_hub.get_zerodha_auth(user)
        investment_service = service_hub.get_investment_service(user)
        
        # Check service status
        status = service_hub.get_service_status()
    """
    
    def __init__(self):
        """Initialize the ServiceHub"""
        super().__init__(service_name="service_hub")
        
        # Track service instances for debugging
        self._service_access_log = []
        self._initialization_time = datetime.now()
        
        self.log_info("initialization", "ServiceHub initialized - centralizing service access")
    
    # === PRIMARY SERVICE ACCESS METHODS ===
    
    def get_zerodha_auth(self, user: UserDB) -> MultiUserZerodhaAuth:
        """
        Get Zerodha authentication service for a user
        
        Args:
            user: The user database object
            
        Returns:
            MultiUserZerodhaAuth instance for the user
            
        Raises:
            Exception: If user is invalid or service cannot be created
        """
        try:
            if not user:
                raise ValueError("User is required to get Zerodha auth service")
            
            self._log_service_access("zerodha_auth", user.username)
            
            # Get the user-specific Zerodha auth instance
            zerodha_auth = zerodha_auth_manager.get_user_auth(user)
            
            if not zerodha_auth:
                raise Exception(f"Failed to get Zerodha auth service for user {user.username}")
            
            self.log_success("get_zerodha_auth", f"Retrieved Zerodha auth for user {user.username}")
            return zerodha_auth
            
        except Exception as e:
            self.log_error("get_zerodha_auth", e)
            raise Exception(f"ServiceHub: Failed to get Zerodha auth for user {user.username}: {str(e)}")
    
    def get_investment_service(self, user: UserDB) -> MultiUserInvestmentService:
        """
        Get investment service for a user
        
        This method automatically handles getting the required Zerodha auth service
        and returns a fully configured investment service instance.
        
        Args:
            user: The user database object
            
        Returns:
            MultiUserInvestmentService instance for the user
            
        Raises:
            Exception: If user is invalid or service cannot be created
        """
        try:
            if not user:
                raise ValueError("User is required to get investment service")
            
            self._log_service_access("investment_service", user.username)
            
            # First get the Zerodha auth service (through our centralized method)
            zerodha_auth = self.get_zerodha_auth(user)
            
            # Get the user-specific investment service
            investment_service = investment_service_manager.get_user_service(user, zerodha_auth)
            
            if not investment_service:
                raise Exception(f"Failed to get investment service for user {user.username}")
            
            self.log_success("get_investment_service", f"Retrieved investment service for user {user.username}")
            return investment_service
            
        except Exception as e:
            self.log_error("get_investment_service", e)
            raise Exception(f"ServiceHub: Failed to get investment service for user {user.username}: {str(e)}")
    
    # === SERVICE STATUS AND MONITORING ===
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all services in the system
        
        Returns:
            Dict containing status information for all services
        """
        try:
            self.log_info("service_status", "Gathering comprehensive service status")
            
            # Get authenticated users from Zerodha auth manager
            authenticated_users = zerodha_auth_manager.get_all_authenticated_users()
            
            # Get active investment services count
            active_investment_services = len(investment_service_manager._user_services)
            
            # Calculate uptime
            uptime_seconds = (datetime.now() - self._initialization_time).total_seconds()
            
            status = {
                "service_hub": {
                    "status": "operational",
                    "initialization_time": self._initialization_time.isoformat(),
                    "uptime_seconds": uptime_seconds,
                    "total_service_requests": len(self._service_access_log)
                },
                "zerodha_auth": {
                    "status": "operational",
                    "authenticated_users_count": len(authenticated_users),
                    "authenticated_users": authenticated_users
                },
                "investment_services": {
                    "status": "operational", 
                    "active_services_count": active_investment_services,
                    "service_manager_initialized": investment_service_manager is not None
                },
                "system_health": {
                    "all_services_operational": True,
                    "last_status_check": datetime.now().isoformat()
                }
            }
            
            self.log_success("service_status", f"Service status compiled: {len(authenticated_users)} auth users, {active_investment_services} investment services")
            return status
            
        except Exception as e:
            self.log_error("service_status", e)
            return {
                "service_hub": {"status": "error", "error": str(e)},
                "system_health": {
                    "all_services_operational": False,
                    "error": str(e),
                    "last_status_check": datetime.now().isoformat()
                }
            }
    
    def get_user_service_summary(self, user: UserDB) -> Dict[str, Any]:
        """
        Get a summary of all services available for a specific user
        
        Args:
            user: The user database object
            
        Returns:
            Dict containing user-specific service information
        """
        try:
            self.log_info("user_service_summary", f"Getting service summary for user {user.username}")
            
            summary = {
                "user": {
                    "username": user.username,
                    "id": user.id,
                    "full_name": user.full_name
                },
                "services": {}
            }
            
            # Check Zerodha auth service
            try:
                zerodha_auth = self.get_zerodha_auth(user)
                summary["services"]["zerodha_auth"] = {
                    "status": "available",
                    "authenticated": zerodha_auth.is_authenticated() if zerodha_auth else False,
                    "profile_name": getattr(zerodha_auth, 'profile_name', None) if zerodha_auth else None
                }
            except Exception as e:
                summary["services"]["zerodha_auth"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Check investment service
            try:
                investment_service = self.get_investment_service(user)
                summary["services"]["investment_service"] = {
                    "status": "available",
                    "service_initialized": investment_service is not None,
                    "user_data_directory": getattr(investment_service, 'user_data_dir', None) if investment_service else None
                }
            except Exception as e:
                summary["services"]["investment_service"] = {
                    "status": "error", 
                    "error": str(e)
                }
            
            self.log_success("user_service_summary", f"Service summary completed for user {user.username}")
            return summary
            
        except Exception as e:
            self.log_error("user_service_summary", e)
            return {
                "user": {"username": user.username, "id": user.id},
                "services": {},
                "error": str(e)
            }
    
    # === CONVENIENCE METHODS ===
    
    def is_user_fully_setup(self, user: UserDB) -> bool:
        """
        Check if a user has all required services properly configured
        
        Args:
            user: The user database object
            
        Returns:
            True if user has all services configured, False otherwise
        """
        try:
            # Try to get both required services
            zerodha_auth = self.get_zerodha_auth(user)
            investment_service = self.get_investment_service(user)
            
            # Check if Zerodha auth is working
            is_zerodha_ready = zerodha_auth and zerodha_auth.is_authenticated()
            
            # Check if investment service is initialized
            is_investment_ready = investment_service is not None
            
            return is_zerodha_ready and is_investment_ready
            
        except Exception as e:
            self.log_warning("user_setup_check", f"User {user.username} setup check failed: {e}")
            return False
    
    def get_service_access_log(self) -> list:
        """
        Get the log of service access requests (for debugging)
        
        Returns:
            List of service access log entries
        """
        return self._service_access_log.copy()
    
    # === INTERNAL HELPER METHODS ===
    
    def _log_service_access(self, service_type: str, username: str):
        """Log service access for debugging and monitoring"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service_type": service_type,
            "username": username
        }
        
        self._service_access_log.append(log_entry)
        
        # Keep only the last 1000 entries to prevent memory issues
        if len(self._service_access_log) > 1000:
            self._service_access_log = self._service_access_log[-1000:]
        
        self.log_debug("service_access", f"Service access: {service_type} for user {username}")
    
    # === FUTURE EXTENSION POINTS ===
    
    def register_service(self, service_name: str, service_factory_function):
        """
        Future method for registering new services dynamically
        
        This is a placeholder for future extensibility where new services
        can be registered with the ServiceHub programmatically.
        """
        # Implementation placeholder for future use
        self.log_info("service_registration", f"Service registration requested: {service_name} (not implemented yet)")
        pass
    
    def get_all_available_services(self) -> Dict[str, str]:
        """
        Get list of all available services in the system
        
        Returns:
            Dict mapping service names to their descriptions
        """
        return {
            "zerodha_auth": "User-specific Zerodha API authentication service",
            "investment_service": "User-specific investment management and portfolio service", 
            "service_hub": "Central service access point (this service)"
        }


# === GLOBAL SINGLETON INSTANCE ===

# Create the global ServiceHub instance
service_hub = ServiceHub()

# For backward compatibility and easy access
def get_service_hub() -> ServiceHub:
    """
    Get the global ServiceHub instance
    
    This function provides access to the singleton ServiceHub instance
    that manages all services in the system.
    
    Returns:
        ServiceHub: The global service hub instance
    """
    return service_hub