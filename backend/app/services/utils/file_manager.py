# backend/app/services/utils/file_manager.py
"""
Centralized file management utilities for all investment services

This module provides standardized JSON file operations that are currently
duplicated across 6+ services. It's designed to be backward-compatible.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class FileManager:
    """Centralized file operations for all investment services"""
    
    @staticmethod
    def load_json_file(
        file_path: str,
        default_value: Any = None,
        logger_prefix: str = "",
        create_if_missing: bool = True
    ) -> Any:
        """
        Load JSON file with standardized error handling
        
        This replaces the duplicated pattern found in:
        - multiuser_investment_service.py _load_orders()
        - investment_service.py _load_system_orders()  
        - live_order_service.py _load_order_tracking()
        - csv_service.py (various load methods)
        - portfolio_*.py (various load methods)
        
        Args:
            file_path: Path to the JSON file
            default_value: Value to return if file doesn't exist (default: [])
            logger_prefix: Prefix for log messages (e.g., "User username")
            create_if_missing: Whether to create empty file if missing
            
        Returns:
            Loaded data or default_value
        """
        if default_value is None:
            default_value = []
            
        try:
            if not os.path.exists(file_path):
                if create_if_missing:
                    # Create empty file with default value
                    FileManager.save_json_file(file_path, default_value, logger_prefix)
                    if logger_prefix:
                        print(f"[INFO] {logger_prefix} - Created new file: {file_path}")
                    else:
                        print(f"[INFO] Created new file: {file_path}")
                
                return default_value
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Ensure data is in expected format (list for most cases)
            if isinstance(default_value, list) and not isinstance(data, list):
                if logger_prefix:
                    print(f"[WARNING] {logger_prefix} - File {file_path} contains non-list data, returning default")
                else:
                    print(f"[WARNING] File {file_path} contains non-list data, returning default")
                return default_value
                
            return data
            
        except json.JSONDecodeError as e:
            if logger_prefix:
                print(f"[ERROR] {logger_prefix} - JSON decode error in {file_path}: {e}")
            else:
                print(f"[ERROR] JSON decode error in {file_path}: {e}")
            return default_value
            
        except Exception as e:
            if logger_prefix:
                print(f"[ERROR] {logger_prefix} - Error loading {file_path}: {e}")
            else:
                print(f"[ERROR] Error loading {file_path}: {e}")
            return default_value
    
    @staticmethod
    def save_json_file(
        file_path: str,
        data: Any,
        logger_prefix: str = "",
        ensure_directory: bool = True,
        indent: int = 2
    ) -> bool:
        """
        Save JSON file with standardized error handling
        
        This replaces the duplicated pattern found across all services:
        - multiuser_investment_service.py _save_orders()
        - investment_service.py (various save methods)
        - live_order_service.py _save_order_tracking()
        - etc.
        
        Args:
            file_path: Path to save the JSON file
            data: Data to save
            logger_prefix: Prefix for log messages
            ensure_directory: Whether to create parent directories
            indent: JSON indentation (default: 2)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if ensure_directory:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            
            # Log success with appropriate format
            if isinstance(data, list):
                if logger_prefix:
                    print(f"[INFO] {logger_prefix} - Saved {len(data)} items to {os.path.basename(file_path)}")
                else:
                    print(f"[INFO] Saved {len(data)} items to {os.path.basename(file_path)}")
            else:
                if logger_prefix:
                    print(f"[INFO] {logger_prefix} - Saved data to {os.path.basename(file_path)}")
                else:
                    print(f"[INFO] Saved data to {os.path.basename(file_path)}")
                    
            return True
            
        except Exception as e:
            if logger_prefix:
                print(f"[ERROR] {logger_prefix} - Error saving {file_path}: {e}")
            else:
                print(f"[ERROR] Error saving {file_path}: {e}")
            return False
    
    @staticmethod
    def ensure_directories(*file_paths: str) -> bool:
        """
        Ensure all required directories exist for given file paths
        
        This replaces the _ensure_directories() pattern found in services
        
        Args:
            *file_paths: Variable number of file paths
            
        Returns:
            True if all directories created successfully
        """
        try:
            for file_path in file_paths:
                directory = os.path.dirname(file_path)
                if directory:  # Only create if directory path exists
                    os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create directories: {e}")
            return False
    
    @staticmethod
    def initialize_json_files(file_configs: Dict[str, Any], logger_prefix: str = "") -> bool:
        """
        Initialize multiple JSON files with default values
        
        This replaces the initialization logic found in _ensure_directories() methods
        
        Args:
            file_configs: Dict mapping file_path -> default_value
            logger_prefix: Prefix for log messages
            
        Returns:
            True if all files initialized successfully
        """
        try:
            all_file_paths = list(file_configs.keys())
            
            # Ensure directories exist
            if not FileManager.ensure_directories(*all_file_paths):
                return False
            
            # Initialize each file
            for file_path, default_value in file_configs.items():
                if not os.path.exists(file_path):
                    if not FileManager.save_json_file(file_path, default_value, logger_prefix):
                        return False
            
            if logger_prefix:
                print(f"[INFO] {logger_prefix} - Initialized {len(file_configs)} JSON files")
            else:
                print(f"[INFO] Initialized {len(file_configs)} JSON files")
                
            return True
            
        except Exception as e:
            if logger_prefix:
                print(f"[ERROR] {logger_prefix} - Failed to initialize files: {e}")
            else:
                print(f"[ERROR] Failed to initialize files: {e}")
            return False
    
    @staticmethod
    def backup_json_file(file_path: str, logger_prefix: str = "") -> bool:
        """
        Create timestamped backup of JSON file
        
        Useful for critical operations like order execution
        
        Args:
            file_path: Path to the file to backup
            logger_prefix: Prefix for log messages
            
        Returns:
            True if backup created successfully
        """
        try:
            if not os.path.exists(file_path):
                return True  # Nothing to backup
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(file_path)[0]
            backup_path = f"{base_name}_backup_{timestamp}.json"
            
            # Read and write to create backup
            data = FileManager.load_json_file(file_path, default_value=None, logger_prefix=logger_prefix)
            if data is not None:
                success = FileManager.save_json_file(backup_path, data, logger_prefix, indent=0)  # Compact backup
                if success:
                    if logger_prefix:
                        print(f"[INFO] {logger_prefix} - Created backup: {os.path.basename(backup_path)}")
                    else:
                        print(f"[INFO] Created backup: {os.path.basename(backup_path)}")
                return success
            return False
            
        except Exception as e:
            if logger_prefix:
                print(f"[ERROR] {logger_prefix} - Failed to create backup: {e}")
            else:
                print(f"[ERROR] Failed to create backup: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get file information (size, modification time, etc.)
        
        Useful for debugging and monitoring
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False}
                
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "readable": os.access(file_path, os.R_OK),
                "writable": os.access(file_path, os.W_OK)
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}


# Legacy compatibility helpers
class LegacyFilePatterns:
    """
    Helpers to match existing file operation patterns exactly
    
    This ensures we can drop-in replace existing code without changes
    """
    
    @staticmethod
    def load_orders_pattern(file_path: str, user_name: str = None) -> List[Dict]:
        """
        Exact pattern match for _load_orders() methods across services
        """
        logger_prefix = f"User {user_name}" if user_name else ""
        return FileManager.load_json_file(
            file_path=file_path,
            default_value=[],
            logger_prefix=logger_prefix
        )
    
    @staticmethod
    def save_orders_pattern(file_path: str, orders: List[Dict], user_name: str = None) -> bool:
        """
        Exact pattern match for _save_orders() methods across services
        """
        logger_prefix = f"User {user_name}" if user_name else ""
        return FileManager.save_json_file(
            file_path=file_path,
            data=orders,
            logger_prefix=logger_prefix
        )