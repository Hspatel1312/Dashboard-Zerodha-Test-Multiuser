# backend/app/services/base/file_operations_mixin.py
"""
File operations mixin for investment services

This mixin provides standardized file operations that are currently
duplicated across 6+ services. Services can inherit this to get
consistent JSON file handling, backup capabilities, and error handling.
"""

import os
from typing import Any, Dict, List, Optional, Union
from abc import ABC

# Import our foundation utilities
from ..utils.file_manager import FileManager, LegacyFilePatterns
from ..utils.config import FilePathConfig


class FileOperationsMixin(ABC):
    """
    Mixin providing standardized file operations for investment services
    
    This eliminates the duplicate file I/O patterns found across:
    - multiuser_investment_service.py (_load_orders, _save_orders)
    - investment_service.py (_load_system_orders, _save_system_orders)
    - live_order_service.py (_load_order_tracking, _save_order_tracking)
    - csv_service.py (cache file operations)
    - portfolio_*.py (various file operations)
    
    Services can inherit this mixin to get:
    - Standardized JSON loading/saving
    - Automatic backup creation
    - Directory management
    - Error handling
    - Logging integration
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize mixin - must be called by inheriting class"""
        super().__init__(*args, **kwargs)
        
        # These will be provided by the inheriting service
        self._file_paths = {}  # Dict mapping file type -> file path
        self._default_values = {}  # Dict mapping file type -> default value
    
    # Core File Operations (Replace duplicate patterns)
    
    def load_json_data(
        self, 
        file_type: str, 
        default_value: Any = None,
        create_if_missing: bool = True
    ) -> Any:
        """
        Load JSON data for specified file type
        
        This replaces the pattern found across services:
        - multiuser_investment_service.py _load_orders()
        - investment_service.py _load_system_orders()
        - live_order_service.py _load_order_tracking()
        
        Args:
            file_type: Type of file ('orders', 'portfolio_state', etc.)
            default_value: Value to return if file doesn't exist
            create_if_missing: Whether to create file if missing
            
        Returns:
            Loaded data or default value
        """
        file_path = self._get_file_path(file_type)
        if not file_path:
            if hasattr(self, 'log_error'):
                self.log_error("load_json_data", Exception(f"No file path configured for type: {file_type}"))
            return default_value or []
        
        if default_value is None:
            default_value = self._get_default_value(file_type)
        
        logger_prefix = self._get_logger_prefix()
        
        return FileManager.load_json_file(
            file_path=file_path,
            default_value=default_value,
            logger_prefix=logger_prefix,
            create_if_missing=create_if_missing
        )
    
    def save_json_data(
        self, 
        file_type: str, 
        data: Any,
        create_backup: bool = False,
        ensure_directory: bool = True
    ) -> bool:
        """
        Save JSON data for specified file type
        
        This replaces the pattern found across services:
        - multiuser_investment_service.py _save_orders()
        - investment_service.py _save_system_orders() 
        - live_order_service.py _save_order_tracking()
        
        Args:
            file_type: Type of file ('orders', 'portfolio_state', etc.)
            data: Data to save
            create_backup: Whether to create backup before saving
            ensure_directory: Whether to create parent directories
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(file_type)
        if not file_path:
            if hasattr(self, 'log_error'):
                self.log_error("save_json_data", Exception(f"No file path configured for type: {file_type}"))
            return False
        
        logger_prefix = self._get_logger_prefix()
        
        # Create backup if requested
        if create_backup:
            FileManager.backup_json_file(file_path, logger_prefix)
        
        return FileManager.save_json_file(
            file_path=file_path,
            data=data,
            logger_prefix=logger_prefix,
            ensure_directory=ensure_directory
        )
    
    # Specialized Methods for Common Patterns
    
    def load_orders_data(self) -> List[Dict]:
        """
        Load orders data - standardized method for all services
        
        This provides the exact functionality of:
        - multiuser_investment_service.py _load_orders()
        - investment_service.py _load_system_orders()
        """
        return self.load_json_data('orders', default_value=[])
    
    def save_orders_data(self, orders: List[Dict], create_backup: bool = True) -> bool:
        """
        Save orders data - standardized method for all services
        
        This provides the exact functionality of:
        - multiuser_investment_service.py _save_orders()
        - investment_service.py _save_system_orders()
        """
        success = self.save_json_data('orders', orders, create_backup=create_backup)
        
        # Log using the same pattern as existing services
        if success and hasattr(self, 'log_data_operation'):
            self.log_data_operation("save_orders", len(orders), "orders")
        
        return success
    
    def load_live_orders_data(self) -> List[Dict]:
        """Load live orders data"""
        return self.load_json_data('live_orders', default_value=[])
    
    def save_live_orders_data(self, live_orders: List[Dict]) -> bool:
        """Save live orders data"""
        return self.save_json_data('live_orders', live_orders)
    
    def load_portfolio_state_data(self) -> Dict:
        """Load portfolio state data"""
        return self.load_json_data('portfolio_state', default_value={})
    
    def save_portfolio_state_data(self, state: Dict) -> bool:
        """Save portfolio state data"""
        return self.save_json_data('portfolio_state', state)
    
    def load_csv_history_data(self) -> List[Dict]:
        """Load CSV history data"""
        return self.load_json_data('csv_history', default_value=[])
    
    def save_csv_history_data(self, history: List[Dict]) -> bool:
        """Save CSV history data"""
        return self.save_json_data('csv_history', history)
    
    # File Path Management
    
    def configure_file_paths(self, file_path_config: Dict[str, str]):
        """
        Configure file paths for this service
        
        Args:
            file_path_config: Dict mapping file type -> file path
                              e.g., {'orders': '/path/to/orders.json'}
        """
        self._file_paths = file_path_config.copy()
    
    def configure_default_values(self, default_value_config: Dict[str, Any]):
        """
        Configure default values for file types
        
        Args:
            default_value_config: Dict mapping file type -> default value
                                  e.g., {'orders': [], 'portfolio_state': {}}
        """
        self._default_values = default_value_config.copy()
    
    def add_file_path(self, file_type: str, file_path: str, default_value: Any = None):
        """
        Add file path configuration for a specific file type
        
        Args:
            file_type: Type identifier (e.g., 'orders', 'portfolio_state')
            file_path: Full path to the file
            default_value: Default value if file doesn't exist
        """
        self._file_paths[file_type] = file_path
        if default_value is not None:
            self._default_values[file_type] = default_value
    
    # Directory Management
    
    def ensure_all_directories(self) -> bool:
        """
        Ensure all configured file directories exist
        
        This replaces _ensure_directories() methods found in services
        """
        try:
            file_paths = list(self._file_paths.values())
            return FileManager.ensure_directories(*file_paths)
        except Exception as e:
            if hasattr(self, 'log_error'):
                self.log_error("ensure_directories", e)
            return False
    
    def initialize_all_files(self) -> bool:
        """
        Initialize all configured files with default values
        
        This replaces the file initialization logic found in services
        """
        try:
            file_configs = {}
            
            for file_type, file_path in self._file_paths.items():
                default_value = self._get_default_value(file_type)
                file_configs[file_path] = default_value
            
            logger_prefix = self._get_logger_prefix()
            return FileManager.initialize_json_files(file_configs, logger_prefix)
            
        except Exception as e:
            if hasattr(self, 'log_error'):
                self.log_error("initialize_files", e)
            return False
    
    # Backup Operations
    
    def create_backup(self, file_type: str) -> bool:
        """
        Create backup of specified file
        
        Args:
            file_type: Type of file to backup
            
        Returns:
            True if backup created successfully
        """
        file_path = self._get_file_path(file_type)
        if not file_path:
            return False
        
        logger_prefix = self._get_logger_prefix()
        return FileManager.backup_json_file(file_path, logger_prefix)
    
    def create_all_backups(self) -> Dict[str, bool]:
        """
        Create backups of all configured files
        
        Returns:
            Dict mapping file_type -> backup success status
        """
        results = {}
        for file_type in self._file_paths.keys():
            results[file_type] = self.create_backup(file_type)
        return results
    
    # File Information and Diagnostics
    
    def get_file_info(self, file_type: str) -> Dict[str, Any]:
        """
        Get information about a file
        
        Args:
            file_type: Type of file to inspect
            
        Returns:
            Dict with file information
        """
        file_path = self._get_file_path(file_type)
        if not file_path:
            return {"exists": False, "error": "File path not configured"}
        
        return FileManager.get_file_info(file_path)
    
    def get_all_file_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all configured files
        
        Returns:
            Dict mapping file_type -> file info
        """
        results = {}
        for file_type in self._file_paths.keys():
            results[file_type] = self.get_file_info(file_type)
        return results
    
    def diagnose_file_issues(self) -> Dict[str, Any]:
        """
        Diagnose potential file operation issues
        
        Returns:
            Dict with diagnostic information
        """
        issues = []
        warnings = []
        
        # Check if any file paths are configured
        if not self._file_paths:
            issues.append("No file paths configured")
        
        # Check each configured file
        for file_type, file_path in self._file_paths.items():
            if not file_path:
                issues.append(f"Empty file path for type: {file_type}")
                continue
            
            # Check directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                warnings.append(f"Directory does not exist for {file_type}: {directory}")
            
            # Check file accessibility
            file_info = self.get_file_info(file_type)
            if file_info.get("exists") and not file_info.get("readable"):
                issues.append(f"File not readable: {file_type}")
            if file_info.get("exists") and not file_info.get("writable"):
                warnings.append(f"File not writable: {file_type}")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "configured_files": len(self._file_paths),
            "has_issues": len(issues) > 0,
            "all_files_info": self.get_all_file_info()
        }
    
    # Helper Methods
    
    def _get_file_path(self, file_type: str) -> Optional[str]:
        """Get file path for specified type"""
        return self._file_paths.get(file_type)
    
    def _get_default_value(self, file_type: str) -> Any:
        """Get default value for specified file type"""
        return self._default_values.get(file_type, [] if file_type.endswith('s') else {})
    
    def _get_logger_prefix(self) -> str:
        """Get logger prefix for file operations"""
        if hasattr(self, 'user_context') and self.user_context:
            return self.user_context
        elif hasattr(self, 'service_name'):
            return self.service_name
        else:
            return ""


# Helper Classes for Specific Use Cases

class UserSpecificFileOperationsMixin(FileOperationsMixin):
    """
    File operations mixin for user-specific services
    
    This provides the file operations pattern used by multiuser_investment_service.py
    """
    
    def __init__(self, user_data_dir: str, *args, **kwargs):
        """
        Initialize with user data directory
        
        Args:
            user_data_dir: User's data directory path
        """
        super().__init__(*args, **kwargs)
        self.user_data_dir = user_data_dir
        
        # Configure standard file paths for user-specific services
        self._configure_user_file_paths(user_data_dir)
    
    def _configure_user_file_paths(self, user_data_dir: str):
        """Configure file paths using user data directory"""
        file_paths = {
            'orders': FilePathConfig.get_user_file_path(user_data_dir, 'orders'),
            'portfolio_state': FilePathConfig.get_user_file_path(user_data_dir, 'portfolio_state'),
            'csv_history': FilePathConfig.get_user_file_path(user_data_dir, 'csv_history'),
            'failed_orders': FilePathConfig.get_user_file_path(user_data_dir, 'failed_orders'),
            'live_orders': FilePathConfig.get_user_file_path(user_data_dir, 'live_orders')
        }
        
        default_values = {
            'orders': [],
            'portfolio_state': {},
            'csv_history': [],
            'failed_orders': [],
            'live_orders': []
        }
        
        self.configure_file_paths(file_paths)
        self.configure_default_values(default_values)


class GlobalFileOperationsMixin(FileOperationsMixin):
    """
    File operations mixin for global/shared services
    
    This provides the file operations pattern used by csv_service.py and other global services
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with global file paths"""
        super().__init__(*args, **kwargs)
        
        # Configure standard global file paths
        self._configure_global_file_paths()
    
    def _configure_global_file_paths(self):
        """Configure file paths for global services"""
        file_paths = {
            'csv_cache': FilePathConfig.GLOBAL_CSV_CACHE_FILE,
            'price_cache': FilePathConfig.GLOBAL_PRICE_CACHE_FILE
        }
        
        default_values = {
            'csv_cache': {},
            'price_cache': {}
        }
        
        self.configure_file_paths(file_paths)
        self.configure_default_values(default_values)
        
    def load_cache_data(self, cache_type: str = 'csv_cache') -> Dict:
        """Load cache data"""
        return self.load_json_data(cache_type, default_value={})
    
    def save_cache_data(self, cache_data: Dict, cache_type: str = 'csv_cache') -> bool:
        """Save cache data"""
        return self.save_json_data(cache_type, cache_data)


# Backward Compatibility Helpers
class LegacyFileOperations:
    """
    Backward compatibility helpers for existing file operation patterns
    
    These allow existing services to use new file operations without changing their method signatures
    """
    
    @staticmethod
    def create_legacy_load_orders_method(service_instance):
        """
        Create _load_orders method compatible with existing services
        
        This allows existing services to use FileOperationsMixin without code changes
        """
        def _load_orders():
            return service_instance.load_orders_data()
        
        return _load_orders
    
    @staticmethod
    def create_legacy_save_orders_method(service_instance):
        """
        Create _save_orders method compatible with existing services
        """
        def _save_orders(orders):
            return service_instance.save_orders_data(orders)
        
        return _save_orders