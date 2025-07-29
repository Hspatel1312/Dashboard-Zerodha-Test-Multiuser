# frontend/utils/api_client.py - Simplified API Client
import requests
import streamlit as st
from typing import Dict, Optional
from datetime import datetime

class APIClient:
    """Simplified API client for the investment dashboard"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response.json() if response.status_code == 200 else None
                
        except requests.exceptions.Timeout:
            st.error("⏰ Request timeout - API is taking too long")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🔌 Connection error - Cannot reach API server")
            return None
        except Exception as e:
            st.error(f"❌ API Error: {str(e)}")
            return None
    
    def check_zerodha_status(self) -> Optional[Dict]:
        """Check Zerodha connection status"""
        return self._make_request('GET', '/api/test-nifty')
    
    def get_portfolio_status(self) -> Optional[Dict]:
        """Get portfolio status"""
        return self._make_request('GET', '/api/investment/portfolio-status')
    
    def get_system_orders(self) -> Optional[Dict]:
        """Get system orders"""
        return self._make_request('GET', '/api/investment/system-orders')
    
    def get_health_status(self) -> Optional[Dict]:
        """Get system health status"""
        return self._make_request('GET', '/health')
    
    def get_csv_status(self) -> Optional[Dict]:
        """Get CSV status"""
        return self._make_request('GET', '/api/investment/csv-status')
    
    def force_csv_refresh(self) -> Optional[Dict]:
        """Force refresh CSV data"""
        return self._make_request('POST', '/api/investment/force-csv-refresh')

def format_currency(amount: float) -> str:
    """Format currency for display"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f}L"
    else:
        return f"₹{amount:,.0f}"

def format_percentage(value: float) -> str:
    """Format percentage for display"""
    return f"{value:+.2f}%"

def show_status_alert(success: bool, message: str, alert_type: str = "info"):
    """Show styled status alert"""
    if success:
        st.markdown(f"""
        <div class="success-alert">
        ✅ <strong>Success</strong><br>{message}
        </div>
        """, unsafe_allow_html=True)
    else:
        color_class = f"{alert_type}-alert"
        icon = "❌" if alert_type == "error" else "⚠️" if alert_type == "warning" else "ℹ️"
        st.markdown(f"""
        <div class="{color_class}">
        {icon} <strong>Alert</strong><br>{message}
        </div>
        """, unsafe_allow_html=True)