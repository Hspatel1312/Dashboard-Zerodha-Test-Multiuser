# frontend/streamlit_app.py
import streamlit as st
import sys
import os
from datetime import datetime

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'components'))

from api_client import APIClient
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
    """Clean welcome/login page"""
    st.markdown('<h1 class="main-header">📈 Investment Dashboard</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome")
        st.markdown("Access your investment portfolio management system.")
        
        with st.form("quick_access"):
            st.markdown("**Quick Access**")
            st.caption("For demo purposes - no actual authentication required")
            
            user_name = st.text_input("Name", placeholder="Enter your name")
            
            if st.button("Enter Dashboard", use_container_width=True, key="login_submit"):
                if user_name.strip():
                    st.session_state.user_authenticated = True
                    st.session_state.user_name = user_name.strip()
                    st.session_state.auth_time = datetime.now()
                    st.rerun()
                else:
                    st.error("Please enter your name")

def show_main_app(api_client, session_manager):
    """Main application with clean navigation"""
    
    # Header
    st.markdown('<h1 class="main-header">📈 Investment Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        show_navigation(session_manager)
    
    # Main content area - no page selection here, handled by page files
    st.info("ℹ️ Select a page from the sidebar to get started")
    
    # Quick stats in main area
    show_quick_overview(api_client)

def show_navigation(session_manager):
    """Clean sidebar navigation"""
    
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
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Data", key="sidebar_refresh_data"):
        st.cache_data.clear()
        st.success("Data refreshed!")
        
    if st.button("📊 System Status", key="sidebar_system_status"):
        st.info("All systems operational")
    
    st.markdown("---")
    
    # Logout
    if st.button("🚪 Logout", type="secondary", key="sidebar_logout"):
        session_manager.logout()
        st.rerun()
    
    # Session info
    st.caption(f"Session: {session_manager.get_session_duration()}").markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.success("Data refreshed!")
        
    if st.button("📊 System Status"):
        st.info("All systems operational")
    
    st.markdown("---")
    
    # Logout
    if st.button("🚪 Logout", type="secondary"):
        session_manager.logout()
        st.rerun()
    
    # Session info
    st.caption(f"Session: {session_manager.get_session_duration()}")

def show_quick_overview(api_client):
    """Quick overview in main area"""
    
    st.markdown("### 📊 Quick Overview")
    
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
        st.metric(
            "Last Updated",
            datetime.now().strftime("%H:%M:%S"),
            help="Real-time data updates"
        )
    
    with col4:
        st.metric(
            "Pages Available",
            "5 Pages",
            help="Navigate using the sidebar"
        )
    
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
        """)
    
    with col2:
        st.markdown("""
        **For Existing Users:**
        1. Check **Portfolio Overview** for current status
        2. Use **Rebalancing** if needed
        3. Monitor **Orders** for recent activity
        """)

if __name__ == "__main__":
    main()