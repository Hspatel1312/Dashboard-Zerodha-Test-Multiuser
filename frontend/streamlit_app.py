# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import time
from typing import Dict, List
import json

# Page configuration
st.set_page_config(
    page_title="Investment Portfolio Manager",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .success-alert {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    
    .warning-alert {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .error-alert {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    
    .connection-status-connected {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
    
    .connection-status-disconnected {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

def check_backend_connection():
    """Check backend connection and return status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

def check_zerodha_connection():
    """Check Zerodha connection status"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/connection-status", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"overall_status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"overall_status": "error", "error": str(e)}

def show_connection_status():
    """Show current connection status"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔗 Backend Connection")
        backend_connected, backend_status = check_backend_connection()
        
        if backend_connected:
            st.markdown('<div class="connection-status-connected">✅ <strong>Backend Connected</strong><br>API server is running and responding</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="connection-status-disconnected">❌ <strong>Backend Disconnected</strong><br>Error: {backend_status.get("error", "Unknown error")}</div>', unsafe_allow_html=True)
            return False
    
    with col2:
        st.subheader("📊 Zerodha Connection")
        zerodha_status = check_zerodha_connection()
        
        if zerodha_status.get("overall_status") == "connected":
            profile_name = zerodha_status.get("services", {}).get("zerodha_auth", {}).get("profile_name", "Unknown")
            st.markdown(f'<div class="connection-status-connected">✅ <strong>Zerodha Connected</strong><br>Profile: {profile_name}</div>', unsafe_allow_html=True)
            return True
        else:
            error_msg = zerodha_status.get("error", "Authentication failed")
            zerodha_error = zerodha_status.get("services", {}).get("zerodha_auth", {}).get("error", "Unknown error")
            st.markdown(f'<div class="connection-status-disconnected">❌ <strong>Zerodha Disconnected</strong><br>Error: {zerodha_error}</div>', unsafe_allow_html=True)
            return False

# Create proper pages using Streamlit's native page system
def main_page():
    """Main dashboard page"""
    st.title("📈 Investment System Manager")
    
    # Show connection status
    zerodha_connected = show_connection_status()
    
    if not zerodha_connected:
        st.markdown("---")
        st.error("⚠️ **Zerodha Connection Required**")
        st.write("To use this system, you need a working Zerodha connection.")
        
        if st.button("🔄 Test Zerodha Connection"):
            with st.spinner("Testing Zerodha connection..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/api/test-auth", timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            st.success(f"✅ {result.get('message')}")
                            st.rerun()
                        else:
                            st.error(f"❌ {result.get('message')}: {result.get('error')}")
                    else:
                        st.error(f"❌ Connection test failed: HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection test error: {e}")
        return
    
    # Main dashboard content when connected
    st.markdown("---")
    st.subheader("🎛️ Dashboard")
    
    # Quick stats
    try:
        response = requests.get(f"{API_BASE_URL}/api/portfolio/summary/1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("💰 Portfolio Value", f"₹{data.get('current_value', 0):,.0f}")
                
                with col2:
                    st.metric("📈 Total Returns", f"₹{data.get('total_returns', 0):,.0f}")
                
                with col3:
                    st.metric("💵 Available Cash", f"₹{data.get('available_cash', 0):,.0f}")
                
                with col4:
                    st.metric("📊 Holdings", f"{data.get('total_holdings', 0)}")
                
                # Portfolio breakdown
                if data.get('holdings'):
                    st.subheader("📋 Top Holdings")
                    holdings_df = pd.DataFrame(data['holdings'][:10])  # Top 10
                    
                    # Format for display
                    display_df = pd.DataFrame({
                        'Stock': holdings_df['symbol'],
                        'Quantity': holdings_df['quantity'],
                        'Current Value': holdings_df['current_value'].apply(lambda x: f"₹{x:,.0f}"),
                        'P&L %': holdings_df['pnl_percent'].apply(lambda x: f"{x:.2f}%")
                    })
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("No portfolio data available")
        else:
            st.info("Portfolio data loading...")
    except:
        st.info("Loading portfolio data...")

# Page routing based on URL query params
def get_page_from_url():
    """Get current page from URL parameters"""
    try:
        query_params = st.query_params
        return query_params.get('page', 'main')
    except:
        return 'main'

def navigate_to(page):
    """Navigate to a specific page"""
    st.query_params['page'] = page
    st.rerun()

# Main app logic
def main():
    """Main app function"""
    
    # Get current page
    current_page = get_page_from_url()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navigation")
        
        # Navigation buttons
        if st.button("🏠 Main Dashboard", use_container_width=True):
            navigate_to('main')
        
        if st.button("📊 Portfolio Overview", use_container_width=True):
            navigate_to('portfolio')
        
        if st.button("⚖️ Rebalancing", use_container_width=True):
            navigate_to('rebalancing')
        
        if st.button("📋 Order History", use_container_width=True):
            navigate_to('orders')
        
        if st.button("🔧 Settings", use_container_width=True):
            navigate_to('settings')
    
    # Route to appropriate page
    if current_page == 'portfolio':
        show_portfolio_page()
    elif current_page == 'rebalancing':
        show_rebalancing_page()
    elif current_page == 'orders':
        show_order_history_page()
    elif current_page == 'settings':
        show_settings_page()
    else:
        main_page()

def show_portfolio_page():
    """Portfolio Overview page"""
    st.title("📊 Portfolio Overview")
    
    try:
        with st.spinner("Loading portfolio data..."):
            response = requests.get(f"{API_BASE_URL}/api/portfolio/summary/1", timeout=30)
        
        if response.status_code == 200:
            portfolio_data = response.json()
            
            if portfolio_data.get("error"):
                st.error(f"❌ Error: {portfolio_data['error']}")
                st.info(portfolio_data.get('message', ''))
                return
            
            # Portfolio metrics
            st.subheader("📊 Portfolio Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                current_value = portfolio_data.get('current_value', 0)
                st.metric("💰 Portfolio Value", f"₹{current_value:,.0f}")
            
            with col2:
                total_returns = portfolio_data.get('total_returns', 0)
                returns_percentage = portfolio_data.get('returns_percentage', 0)
                st.metric("📈 Total Returns", f"₹{total_returns:,.0f}", delta=f"{returns_percentage:.2f}%")
            
            with col3:
                available_cash = portfolio_data.get('available_cash', 0)
                st.metric("💵 Available Cash", f"₹{available_cash:,.0f}")
            
            with col4:
                total_holdings = portfolio_data.get('total_holdings', 0)
                st.metric("📊 Holdings", f"{total_holdings}")
            
            # Holdings table
            holdings = portfolio_data.get('holdings', [])
            if holdings:
                st.subheader("📋 Current Holdings")
                
                holdings_data = []
                for holding in holdings:
                    holdings_data.append({
                        'Stock': holding.get('symbol', ''),
                        'Quantity': f"{holding.get('quantity', 0):,}",
                        'Avg Price': f"₹{holding.get('avg_price', 0):.2f}",
                        'Current Price': f"₹{holding.get('current_price', 0):.2f}",
                        'Current Value': f"₹{holding.get('current_value', 0):,.0f}",
                        'P&L': f"₹{holding.get('pnl', 0):,.0f}",
                        'P&L %': f"{holding.get('pnl_percent', 0):.2f}%"
                    })
                
                holdings_df = pd.DataFrame(holdings_data)
                st.dataframe(holdings_df, use_container_width=True, hide_index=True)
            else:
                st.info("📭 No holdings data available")
                
        else:
            st.error(f"API Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error fetching portfolio status: {e}")

def show_rebalancing_page():
    """Rebalancing page"""
    st.title("⚖️ Portfolio Rebalancing")
    
    st.info("🚧 Rebalancing feature coming soon...")
    st.write("This page will show rebalancing opportunities and allow you to execute rebalancing trades.")

def show_order_history_page():
    """Order History page"""
    st.title("📋 Order History")
    
    st.info("🚧 Order history feature coming soon...")
    st.write("This page will show all your trading orders and their status.")

def show_settings_page():
    """Settings page"""
    st.title("🔧 Settings")
    
    # Connection test section
    st.subheader("🔗 Connection Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Test Backend Connection"):
            with st.spinner("Testing backend connection..."):
                connected, status = check_backend_connection()
                if connected:
                    st.success("✅ Backend connected successfully!")
                    st.json(status)
                else:
                    st.error(f"❌ Backend connection failed: {status.get('error')}")
    
    with col2:
        if st.button("🔄 Test Zerodha Connection"):
            with st.spinner("Testing Zerodha connection..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/api/test-auth", timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success"):
                            st.success(f"✅ {result.get('message')}")
                            if result.get('profile_name'):
                                st.info(f"Profile: {result.get('profile_name')}")
                        else:
                            st.error(f"❌ {result.get('message')}")
                            if result.get('error'):
                                st.error(f"Error: {result.get('error')}")
                    else:
                        st.error(f"❌ HTTP {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection test error: {e}")
    
    # Configuration display
    st.subheader("⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
        st.selectbox("Environment", ["Development", "Production"], index=0, disabled=True)
    
    with col2:
        st.number_input("Request Timeout (seconds)", min_value=5, max_value=60, value=30, disabled=True)
        st.checkbox("Debug Mode", value=True, disabled=True)

if __name__ == "__main__":
    main()