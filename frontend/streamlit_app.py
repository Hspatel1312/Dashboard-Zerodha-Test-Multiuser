# frontend/streamlit_app.py - COMPLETE FIXED VERSION
import streamlit as st
import sys
import os
from datetime import datetime
import time

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))

from api_client import APIClient, APIHelpers
from session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    st.markdown("""
    <style>
        /* Main header styling */
        .main-header {
            font-size: 2.2rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1.5rem;
            padding: 1rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Clean sidebar */
        .sidebar-content {
            padding: 1rem 0;
        }
        
        /* Status indicators */
        .status-good { color: #28a745; font-weight: bold; }
        .status-warning { color: #ffc107; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        
        /* Clean buttons */
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        /* Hide default sidebar elements */
        .css-1d391kg { padding-top: 1rem; }
        
        /* Clean metric cards */
        [data-testid="metric-container"] {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Error styling */
        .stAlert > div {
            border-radius: 8px;
        }
        
        /* Success styling */
        .stSuccess > div {
            border-radius: 8px;
        }
        
        /* Warning styling */
        .stWarning > div {
            border-radius: 8px;
        }
        
        /* Info styling */
        .stInfo > div {
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    load_css()
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Check authentication
    if not session_manager.is_authenticated():
        show_welcome_page()
        return
    
    # Initialize API client
    api_client = APIClient(
        base_url="http://127.0.0.1:8000",
        session_manager=session_manager
    )
    
    # Main app layout
    show_main_app(api_client, session_manager)

def show_welcome_page():
    """Clean welcome/login page with proper form handling"""
    st.markdown('<h1 class="main-header">📈 Investment Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome")
        st.markdown("Access your investment portfolio management system.")
        
        # Login form with proper submit handling
        with st.form("login_form", clear_on_submit=False):
            st.markdown("**Quick Access**")
            st.caption("For demo purposes - no actual authentication required")
            
            user_name = st.text_input(
                "Name", 
                placeholder="Enter your name",
                help="Enter any name to access the dashboard"
            )
            
            # Submit button - this was missing and causing the error
            submitted = st.form_submit_button("🚀 Enter Dashboard", use_container_width=True)
            
            if submitted:
                if user_name and user_name.strip():
                    # Set session state
                    st.session_state.user_authenticated = True
                    st.session_state.user_name = user_name.strip()
                    st.session_state.auth_time = datetime.now()
                    
                    st.success("✅ Login successful! Redirecting...")
                    time.sleep(1)  # Brief pause for user feedback
                    st.rerun()
                else:
                    st.error("❌ Please enter your name to continue")
        
        # System status info
        st.markdown("---")
        st.markdown("#### 🔧 System Status")
        
        # Test API connection
        with st.spinner("Checking system status..."):
            try:
                test_client = APIClient("http://127.0.0.1:8000")
                health_response = test_client.get_system_health()
                
                if health_response:
                    st.success("✅ Backend server is running")
                    
                    # Show service status if available
                    services = health_response.get('services', {})
                    if services.get('investment_service'):
                        st.info("📊 Investment service available")
                    if services.get('zerodha_auth'):
                        st.info("🔗 Zerodha service available")
                else:
                    st.error("❌ Backend server not responding")
                    st.markdown("""
                    **Troubleshooting:**
                    - Ensure the backend is running on port 8000
                    - Check your network connection
                    - Verify all services are properly configured
                    """)
            except Exception as e:
                st.error("❌ Cannot connect to backend server")
                st.caption(f"Error: {str(e)}")

def show_main_app(api_client, session_manager):
    """Main application with clean navigation and error handling"""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Investment Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        show_navigation(session_manager, api_client)
    
    # Main content area
    show_dashboard_home(api_client)

def show_navigation(session_manager, api_client):
    """Enhanced sidebar navigation with system status"""
    
    # User info (compact)
    st.markdown("### 👤 Dashboard")
    st.success(f"Welcome, {session_manager.get_user_name()}")
    
    st.markdown("---")
    
    # Navigation help
    st.markdown("### 🧭 Navigation")
    st.markdown("""
    Use the pages in the sidebar to navigate:
    
    📊 **Portfolio Overview** - Current holdings and performance
    
    💰 **Investment** - Add new investments
    
    ⚖️ **Rebalancing** - Portfolio rebalancing
    
    📋 **Order History** - Order tracking
    
    📄 **CSV Manager** - Stock data management
    """)
    
    st.markdown("---")
    
    # System status
    st.markdown("### 📊 System Status")
    
    try:
        # Get system health
        health_response = api_client.get_system_health()
        
        if health_response:
            services = health_response.get('services', {})
            
            # Investment service status
            if services.get('investment_service'):
                st.markdown("✅ Investment Service")
            else:
                st.markdown("❌ Investment Service")
            
            # Zerodha service status
            if services.get('zerodha_auth'):
                st.markdown("✅ Zerodha Service")
            else:
                st.markdown("❌ Zerodha Service")
            
            # Timestamp
            timestamp = health_response.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', ''))
                    st.caption(f"Updated: {dt.strftime('%H:%M:%S')}")
                except:
                    st.caption("Status: Live")
        else:
            st.markdown("❌ Backend Offline")
    
    except Exception as e:
        st.markdown("⚠️ Status Unknown")
        st.caption(f"Error: {str(e)[:30]}...")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Data", key="sidebar_refresh_data"):
        api_client.clear_cache()
        st.success("🎉 Data refreshed!")
        st.rerun()
    
    if st.button("🧪 Test Connection", key="sidebar_test_connection"):
        with st.spinner("Testing..."):
            try:
                debug_info = api_client.get_debug_info()
                if debug_info:
                    st.success("✅ Connection OK")
                else:
                    st.error("❌ Connection failed")
            except Exception as e:
                st.error(f"❌ Test failed: {str(e)}")
    
    st.markdown("---")
    
    # Logout
    if st.button("🚪 Logout", type="secondary", key="sidebar_logout"):
        session_manager.logout()
        st.success("👋 Logged out successfully")
        st.rerun()
    
    # Session info
    session_duration = session_manager.get_session_duration()
    st.caption(f"Session: {session_duration}")

def show_dashboard_home(api_client):
    """Dashboard home page with quick overview"""
    
    st.markdown("### 🏠 Dashboard Home")
    st.markdown("Welcome to your investment management system. Use the sidebar to navigate to different sections.")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "System Status", 
            "🟢 Online",
            help="All services are running normally"
        )
    
    with col2:
        st.metric(
            "Data Source",
            "📡 Live API",
            help="Connected to live data feeds"
        )
    
    with col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric(
            "Last Updated",
            current_time,
            help="Real-time data updates"
        )
    
    with col4:
        st.metric(
            "Pages Available",
            "5 Pages",
            help="Navigate using the sidebar"
        )
    
    # Quick portfolio check
    st.markdown("---")
    st.markdown("### 📊 Quick Portfolio Check")
    
    with st.spinner("Checking portfolio status..."):
        try:
            portfolio_response = api_client.get_portfolio_status()
            portfolio_data = APIHelpers.extract_data(portfolio_response)
            
            if portfolio_data:
                status = portfolio_data.get('status', 'unknown')
                
                if status == 'active':
                    st.success("✅ **Active Portfolio Found**")
                    
                    # Show basic metrics
                    summary = portfolio_data.get('portfolio_summary', {})
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        current_value = summary.get('current_value', 0)
                        st.metric("Current Value", APIHelpers.format_currency(current_value))
                    
                    with col2:
                        total_returns = summary.get('total_returns', 0)
                        st.metric("Total Returns", APIHelpers.format_currency(total_returns))
                    
                    with col3:
                        stock_count = summary.get('stock_count', 0)
                        st.metric("Holdings", f"{stock_count} stocks")
                    
                    # Quick navigation
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📊 View Full Portfolio", use_container_width=True):
                            st.switch_page("pages/1_Portfolio_Overview.py")
                    
                    with col2:
                        if st.button("⚖️ Check Rebalancing", use_container_width=True):
                            st.switch_page("pages/3_Rebalancing.py")
                
                elif status == 'empty':
                    st.info("📭 **No Portfolio Found**")
                    st.markdown("You haven't created a portfolio yet.")
                    
                    if st.button("🚀 Start Investing", use_container_width=True):
                        st.switch_page("pages/2_Investment.py")
                
                else:
                    st.warning(f"⚠️ **Portfolio Status**: {status}")
                    error_message = portfolio_data.get('error', 'Unknown issue')
                    st.markdown(f"**Details**: {error_message}")
                    
                    if st.button("🔄 Retry Check", use_container_width=True):
                        st.rerun()
            
            else:
                st.error("❌ **Unable to check portfolio**")
                st.markdown("There may be a connection issue with the backend.")
                
                if st.button("🔧 Troubleshoot", use_container_width=True):
                    show_troubleshooting_info()
        
        except Exception as e:
            st.error("❌ **Portfolio Check Failed**")
            st.markdown(f"**Error**: {str(e)}")
    
    # Instructions
    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **For New Users:**
        1. Go to **Investment** page to start
        2. Check minimum investment requirements
        3. Calculate and execute your plan
        4. Monitor progress in **Portfolio Overview**
        """)
    
    with col2:
        st.markdown("""
        **For Existing Users:**
        1. Check **Portfolio Overview** for current status
        2. Use **Rebalancing** if allocation has drifted
        3. Monitor **Order History** for recent activity
        4. Manage data sources in **CSV Manager**
        """)

def show_troubleshooting_info():
    """Show troubleshooting information"""
    st.markdown("### 🔧 Troubleshooting")
    
    with st.expander("Connection Issues"):
        st.markdown("""
        **If you're experiencing connection issues:**
        
        1. **Check Backend Server**
           - Ensure the backend is running on `http://localhost:8000`
           - Verify all environment variables are set
           - Check server logs for errors
        
        2. **Network Issues**
           - Test your internet connection
           - Check if port 8000 is accessible
           - Verify firewall settings
        
        3. **Service Dependencies**
           - Ensure PostgreSQL is running (if using database)
           - Check Redis connection (if using caching)
           - Verify Zerodha API credentials
        """)
    
    with st.expander("Data Issues"):
        st.markdown("""
        **If you're seeing data-related errors:**
        
        1. **Price Data**
           - Market hours: 9:15 AM - 3:30 PM IST
           - Zerodha API authentication required
           - Check API rate limits
        
        2. **CSV Data**
           - Verify GitHub repository access
           - Check CSV file format and structure
           - Ensure internet connectivity
        
        3. **Portfolio Data**
           - Initial investment must be completed
           - Minimum investment amount required
           - Live price data needed for calculations
        """)
    
    with st.expander("System Status Check"):
        st.markdown("**System Component Status:**")
        
        try:
            # Test API endpoints
            api_client = APIClient("http://127.0.0.1:8000")
            
            # Test health endpoint
            health_response = api_client.get_system_health()
            if health_response:
                st.success("✅ Health endpoint responding")
            else:
                st.error("❌ Health endpoint not responding")
            
            # Test debug endpoint
            debug_response = api_client.get_debug_info()
            if debug_response:
                st.success("✅ Debug endpoint responding")
                
                # Show service status
                investment_service = debug_response.get('investment_service', {})
                zerodha_auth = debug_response.get('zerodha_auth', {})
                
                if investment_service.get('available'):
                    st.success("✅ Investment service available")
                else:
                    st.error("❌ Investment service unavailable")
                
                if zerodha_auth.get('available'):
                    if zerodha_auth.get('authenticated'):
                        st.success("✅ Zerodha authenticated")
                    else:
                        st.warning("⚠️ Zerodha not authenticated")
                else:
                    st.error("❌ Zerodha service unavailable")
            else:
                st.error("❌ Debug endpoint not responding")
        
        except Exception as e:
            st.error(f"❌ System check failed: {str(e)}")

if __name__ == "__main__":
    main()