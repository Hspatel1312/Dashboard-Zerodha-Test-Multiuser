# frontend/utils/api_client.py - FIXED VERSION
import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import json

class APIClient:
    """Fixed API client with proper error handling and caching"""
    
    def __init__(self, base_url: str, session_manager=None):
        self.base_url = base_url.rstrip('/')
        self.session_manager = session_manager
        self.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with comprehensive error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON response from server")
                    return None
            else:
                error_msg = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        error_msg += f" - {error_data['detail']}"
                    elif 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    error_msg += f" - {response.text}"
                
                st.error(error_msg)
                return None
                
        except requests.exceptions.Timeout:
            st.error("⏰ Request timeout - API is taking too long to respond")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error - Cannot reach the API server. Please check if the backend is running.")
            return None
        except Exception as e:
            st.error(f"❌ API request failed: {str(e)}")
            return None
    
    @st.cache_data(ttl=60, show_spinner=False)
    def get_system_health(_self) -> Optional[Dict]:
        """Get system health status"""
        return _self._make_request('GET', '/health')
    
    @st.cache_data(ttl=300, show_spinner=False)
    def get_csv_stocks(_self) -> Optional[Dict]:
        """Get CSV stocks with prices"""
        response = _self._make_request('GET', '/api/investment/csv-stocks')
        if response and not response.get('success', False):
            # Handle API errors gracefully
            return {
                'success': False,
                'data': {
                    'stocks': [],
                    'total_stocks': 0,
                    'error': response.get('error', {}).get('error_type', 'UNKNOWN_ERROR'),
                    'error_message': response.get('error', {}).get('error_message', 'Unknown error'),
                    'price_data_status': {
                        'live_prices_used': False,
                        'market_data_source': 'UNAVAILABLE'
                    }
                }
            }
        return response
    
    @st.cache_data(ttl=120, show_spinner=False)
    def get_portfolio_status(_self) -> Optional[Dict]:
        """Get current portfolio status"""
        response = _self._make_request('GET', '/api/investment/portfolio-status')
        if response and not response.get('success', False):
            # Handle API errors gracefully
            return {
                'success': False,
                'data': {
                    'status': 'error',
                    'error': response.get('error', {}).get('error_message', 'Unable to fetch portfolio'),
                    'holdings': {},
                    'portfolio_summary': {
                        'total_investment': 0,
                        'current_value': 0,
                        'total_returns': 0,
                        'returns_percentage': 0,
                        'stock_count': 0
                    }
                }
            }
        return response
    
    def get_investment_requirements(self) -> Optional[Dict]:
        """Get investment requirements (don't cache - needs fresh data)"""
        response = self._make_request('GET', '/api/investment/requirements')
        if response and not response.get('success', False):
            # Handle API errors gracefully for requirements
            error_info = response.get('error', {})
            return {
                'success': False,
                'data': {
                    'error': error_info.get('error_type', 'REQUIREMENTS_ERROR'),
                    'error_message': error_info.get('error_message', 'Unable to fetch requirements'),
                    'stocks_data': {
                        'total_stocks': 0,
                        'error': 'REQUIREMENTS_UNAVAILABLE'
                    },
                    'data_quality': {
                        'live_data_available': False,
                        'error_type': error_info.get('error_type', 'UNKNOWN_ERROR')
                    }
                }
            }
        return response
    
    def calculate_investment_plan(self, investment_amount: float) -> Optional[Dict]:
        """Calculate investment plan"""
        data = {"investment_amount": investment_amount}
        response = self._make_request('POST', '/api/investment/calculate-plan', data=data)
        if response and not response.get('success', False):
            # Handle plan calculation errors
            error_info = response.get('error', {})
            return {
                'success': False,
                'data': {
                    'error': error_info.get('error_type', 'PLAN_ERROR'),
                    'error_message': error_info.get('error_message', 'Unable to calculate plan'),
                    'data_quality': {
                        'live_data_available': False
                    }
                }
            }
        return response
    
    def execute_initial_investment(self, investment_amount: float) -> Optional[Dict]:
        """Execute initial investment"""
        data = {"investment_amount": investment_amount}
        response = self._make_request('POST', '/api/investment/execute-initial', data=data)
        if response and not response.get('success', False):
            # Handle execution errors
            error_info = response.get('error', {})
            return {
                'success': False,
                'data': {
                    'error': error_info.get('error_type', 'EXECUTION_ERROR'),
                    'error_message': error_info.get('error_message', 'Unable to execute investment'),
                    'data_quality': {
                        'live_data_used': False
                    }
                }
            }
        return response
    
    def check_rebalancing_needed(self) -> Optional[Dict]:
        """Check if rebalancing is needed"""
        response = self._make_request('GET', '/api/investment/rebalancing-check')
        if response and not response.get('success', False):
            # Handle rebalancing check errors
            return {
                'success': False,
                'data': {
                    'rebalancing_needed': False,
                    'reason': 'Unable to check rebalancing status',
                    'error': response.get('error', {}).get('error_message', 'Unknown error'),
                    'is_first_time': True
                }
            }
        return response
    
    @st.cache_data(ttl=60, show_spinner=False)
    def get_system_orders(_self) -> Optional[Dict]:
        """Get system orders history"""
        response = _self._make_request('GET', '/api/investment/system-orders')
        if response and not response.get('success', False):
            # Handle orders fetch errors
            return {
                'success': False,
                'data': {
                    'orders': [],
                    'total_orders': 0,
                    'error': response.get('error', {}).get('error_message', 'Unable to fetch orders')
                }
            }
        return response
    
    @st.cache_data(ttl=300, show_spinner=False)
    def get_csv_status(_self) -> Optional[Dict]:
        """Get CSV tracking status"""
        response = _self._make_request('GET', '/api/investment/csv-status')
        if response and not response.get('success', False):
            # Handle CSV status errors
            return {
                'success': False,
                'data': {
                    'current_csv': {
                        'available': False,
                        'total_symbols': 0,
                        'error': response.get('error', {}).get('error_message', 'CSV status unavailable')
                    }
                }
            }
        return response
    
    def force_csv_refresh(self) -> Optional[Dict]:
        """Force refresh CSV data"""
        response = self._make_request('POST', '/api/investment/force-csv-refresh')
        if response and not response.get('success', False):
            # Handle refresh errors
            return {
                'success': False,
                'data': {
                    'csv_refreshed': False,
                    'error': response.get('error', {}).get('error_message', 'Unable to refresh CSV')
                }
            }
        return response
    
    def test_zerodha_connection(self) -> Optional[Dict]:
        """Test Zerodha connection"""
        return self._make_request('GET', '/api/test/zerodha')
    
    def get_debug_info(self) -> Optional[Dict]:
        """Get debug information"""
        return self._make_request('GET', '/api/debug/services')
    
    def clear_cache(self):
        """Clear all cached data"""
        st.cache_data.clear()
        if self.session_manager:
            self.session_manager.refresh_session()

# Helper functions for common API patterns
class APIHelpers:
    """Helper functions for API response handling"""
    
    @staticmethod
    def extract_data(response: Optional[Dict], default=None):
        """Safely extract data from API response with better error handling"""
        if not response:
            return default
        
        # Handle both old format and new format responses
        if 'success' in response:
            if response.get('success'):
                return response.get('data', default)
            else:
                # API returned success=False, show error but return safe default
                error_info = response.get('error', {})
                error_msg = error_info.get('error_message', 'Unknown API error')
                print(f"API Error: {error_msg}")  # Log for debugging
                
                # Return the data field even if success=False, as it might contain fallback data
                return response.get('data', default)
        else:
            # Old format or direct data
            return response if response is not None else default
    
    @staticmethod
    def show_api_status(response: Optional[Dict], success_msg: str = "Operation successful") -> bool:
        """Show API response status with better error handling"""
        if not response:
            st.error("❌ No response from server")
            return False
        
        if response.get('success', True):  # Default to True for backward compatibility
            st.success(f"✅ {success_msg}")
            return True
        else:
            error_info = response.get('error', {})
            error_msg = error_info.get('error_message', 'Unknown error')
            error_type = error_info.get('error_type', 'API_ERROR')
            
            # Show different error types with appropriate styling
            if error_type in ['PRICE_DATA_UNAVAILABLE', 'CSV_DATA_UNAVAILABLE']:
                st.warning(f"⚠️ {error_msg}")
            elif error_type in ['VALIDATION_ERROR']:
                st.error(f"❌ {error_msg}")
            else:
                st.error(f"❌ {error_msg}")
            
            return False
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency for display"""
        if pd.isna(amount) or amount == 0:
            return "₹0"
        elif amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.2f}Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.2f}L"
        else:
            return f"₹{amount:,.0f}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage for display"""
        if pd.isna(value):
            return "0.00%"
        return f"{value:+.2f}%"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color for status display"""
        status_colors = {
            'success': '#28a745',
            'completed': '#28a745',
            'active': '#28a745',
            'warning': '#ffc107',
            'pending': '#ffc107',
            'error': '#dc3545',
            'failed': '#dc3545',
            'empty': '#6c757d',
            'price_data_unavailable': '#fd7e14',
            'calculation_error': '#dc3545'
        }
        return status_colors.get(status.lower(), '#6c757d')
    
    @staticmethod
    def safe_get(data: Dict, key: str, default=None):
        """Safely get value from dict with nested key support"""
        try:
            if '.' in key:
                keys = key.split('.')
                value = data
                for k in keys:
                    value = value.get(k, {})
                return value if value != {} else default
            else:
                return data.get(key, default)
        except (AttributeError, TypeError):
            return default

# Import pandas for helper functions
try:
    import pandas as pd
except ImportError:
    # Fallback if pandas not available
    class pd:
        @staticmethod
        def isna(value):
            return value is None or (isinstance(value, float) and value != value)