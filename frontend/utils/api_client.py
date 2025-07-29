  
# frontend/utils/api_client.py
import requests
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import json

class APIClient:
    """Clean API client with proper error handling and caching"""
    
    def __init__(self, base_url: str, session_manager=None):
        self.base_url = base_url.rstrip('/')
        self.session_manager = session_manager
        self.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
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
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("⏰ Request timeout - API is taking too long to respond")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error - Cannot reach the API server")
            return None
        except Exception as e:
            st.error(f"❌ API request failed: {str(e)}")
            return None
    
    @st.cache_data(ttl=60)  # Cache for 1 minute
    def get_system_health(_self) -> Optional[Dict]:
        """Get system health status"""
        return _self._make_request('GET', '/health')
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_csv_stocks(_self) -> Optional[Dict]:
        """Get CSV stocks with prices"""
        return _self._make_request('GET', '/api/investment/csv-stocks')
    
    @st.cache_data(ttl=120)  # Cache for 2 minutes
    def get_portfolio_status(_self) -> Optional[Dict]:
        """Get current portfolio status"""
        return _self._make_request('GET', '/api/investment/portfolio-status')
    
    def get_investment_requirements(self) -> Optional[Dict]:
        """Get investment requirements (don't cache - needs fresh data)"""
        return self._make_request('GET', '/api/investment/requirements')
    
    def calculate_investment_plan(self, investment_amount: float) -> Optional[Dict]:
        """Calculate investment plan"""
        data = {"investment_amount": investment_amount}
        return self._make_request('POST', '/api/investment/calculate-plan', data=data)
    
    def execute_initial_investment(self, investment_amount: float) -> Optional[Dict]:
        """Execute initial investment"""
        data = {"investment_amount": investment_amount}
        return self._make_request('POST', '/api/investment/execute-initial', data=data)
    
    def check_rebalancing_needed(self) -> Optional[Dict]:
        """Check if rebalancing is needed"""
        return self._make_request('GET', '/api/investment/rebalancing-check')
    
    @st.cache_data(ttl=60)
    def get_system_orders(_self) -> Optional[Dict]:
        """Get system orders history"""
        return _self._make_request('GET', '/api/investment/system-orders')
    
    @st.cache_data(ttl=300)
    def get_csv_status(_self) -> Optional[Dict]:
        """Get CSV tracking status"""
        return _self._make_request('GET', '/api/investment/csv-status')
    
    def force_csv_refresh(self) -> Optional[Dict]:
        """Force refresh CSV data"""
        return self._make_request('POST', '/api/investment/force-csv-refresh')
    
    def test_zerodha_connection(self) -> Optional[Dict]:
        """Test Zerodha connection"""
        return self._make_request('GET', '/api/test-nifty')
    
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
        """Safely extract data from API response"""
        if not response:
            return default
        
        if response.get('success'):
            return response.get('data', default)
        else:
            error_msg = response.get('error', 'Unknown error')
            st.error(f"API Error: {error_msg}")
            return default
    
    @staticmethod
    def show_api_status(response: Optional[Dict], success_msg: str = "Operation successful"):
        """Show API response status"""
        if not response:
            st.error("❌ No response from server")
            return False
        
        if response.get('success'):
            st.success(f"✅ {success_msg}")
            return True
        else:
            error_msg = response.get('error', 'Unknown error')
            st.error(f"❌ {error_msg}")
            return False
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency for display"""
        if amount >= 10000000:  # 1 crore
            return f"₹{amount/10000000:.2f}Cr"
        elif amount >= 100000:  # 1 lakh
            return f"₹{amount/100000:.2f}L"
        else:
            return f"₹{amount:,.0f}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage for display"""
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
            'empty': '#6c757d'
        }
        return status_colors.get(status.lower(), '#6c757d')