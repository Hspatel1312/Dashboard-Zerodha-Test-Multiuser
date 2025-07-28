# frontend/streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import requests
import json
from typing import Dict, List, Optional
import time

# Page configuration
st.set_page_config(
    page_title="Investment System Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .status-card-small {
        background: white;
        padding: 0.75rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    .success-status {
        border-left-color: #28a745;
        background-color: #f8fff9;
    }
    
    .error-status {
        border-left-color: #dc3545;
        background-color: #fff8f8;
    }
    
    .warning-status {
        border-left-color: #ffc107;
        background-color: #fffef8;
    }
    
    .info-status {
        border-left-color: #17a2b8;
        background-color: #f0fcff;
    }
    
    .csv-change-alert {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .rebalancing-needed {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    .sidebar-section {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .metric-compact {
        text-align: center;
        padding: 0.5rem;
        background: white;
        border-radius: 8px;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'investment_plan' not in st.session_state:
    st.session_state.investment_plan = None
if 'csv_change_detected' not in st.session_state:
    st.session_state.csv_change_detected = False
if 'last_csv_hash' not in st.session_state:
    st.session_state.last_csv_hash = None
if 'rebalancing_alert' not in st.session_state:
    st.session_state.rebalancing_alert = None

class SimpleAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 30

    def check_backend_health(self) -> Dict:
        """Check backend health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return {'connected': True, 'data': response.json()}
            else:
                return {'connected': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    def test_zerodha_connection(self) -> Dict:
        """Test Zerodha connection by getting Nifty price"""
        try:
            response = requests.get(f"{self.base_url}/api/test-nifty", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_csv_stocks(self) -> Dict:
        """Get CSV stocks"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/csv-stocks", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_system_orders(self) -> Dict:
        """Get all system orders"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/system-orders", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_portfolio_status(self) -> Dict:
        """Get portfolio status built from orders"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/portfolio-status", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_investment_requirements(self) -> Dict:
        """Get investment requirements"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/requirements", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def calculate_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate investment plan"""
        try:
            data = {"investment_amount": investment_amount}
            response = requests.post(
                f"{self.base_url}/api/investment/calculate-plan",
                json=data,
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    pass
                return {'success': False, 'error': error_text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def execute_initial_investment(self, investment_amount: float) -> Dict:
        """Execute initial investment"""
        try:
            data = {"investment_amount": investment_amount}
            response = requests.post(
                f"{self.base_url}/api/investment/execute-initial",
                json=data,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    pass
                return {'success': False, 'error': error_text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/rebalancing-check", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_csv_status(self) -> Dict:
        """Get CSV tracking status"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/csv-status", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def force_csv_refresh(self) -> Dict:
        """Force refresh CSV data"""
        try:
            response = requests.post(f"{self.base_url}/api/investment/force-csv-refresh", timeout=60)
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize API client
api_client = SimpleAPIClient(API_BASE_URL)

def main():
    st.markdown('<h1 class="main-header">📈 Investment System Dashboard</h1>', unsafe_allow_html=True)
    
    # Check for alerts at the top (compact)
    check_csv_changes_and_alerts()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        
        page = st.selectbox(
            "Select Page",
            [
                "🏠 Dashboard",
                "📊 CSV Manager", 
                "💰 Investment",
                "📈 Portfolio",
                "⚖️ Rebalancing",
                "📋 Orders",
                "📄 Stock Data",
                "⚙️ Settings"
            ]
        )
        
        st.markdown("---")
        
        # Compact CSV status
        show_compact_csv_status_sidebar()
        
        st.markdown("---")
        
        # Simple refresh
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        st.caption(f"Updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Route to pages
    if page == "🏠 Dashboard":
        show_system_status()
    elif page == "📊 CSV Manager":
        show_csv_tracking()
    elif page == "💰 Investment":
        show_initial_investment()
    elif page == "📈 Portfolio":
        show_portfolio_overview()
    elif page == "⚖️ Rebalancing":
        show_rebalancing()
    elif page == "📋 Orders":
        show_order_history()
    elif page == "📄 Stock Data":
        show_csv_stocks()
    elif page == "⚙️ Settings":
        show_system_info()

def check_csv_changes_and_alerts():
    """Check for changes and show compact alerts"""
    try:
        csv_status = api_client.get_csv_status()
        if csv_status and csv_status.get('success'):
            data = csv_status['data']
            current_csv = data.get('current_csv', {})
            current_hash = current_csv.get('csv_hash')
            
            # Check hash change
            if st.session_state.last_csv_hash and st.session_state.last_csv_hash != current_hash:
                st.session_state.csv_change_detected = True
            
            st.session_state.last_csv_hash = current_hash
            
            # Check rebalancing
            rebalancing_status = data.get('rebalancing_status', {})
            if rebalancing_status.get('rebalancing_needed'):
                st.session_state.rebalancing_alert = rebalancing_status
            
            # Show compact alerts
            if st.session_state.csv_change_detected:
                show_csv_change_alert()
            
            if (st.session_state.rebalancing_alert and 
                st.session_state.rebalancing_alert.get('rebalancing_needed')):
                show_rebalancing_alert()
                
    except Exception as e:
        pass

def show_csv_change_alert():
    """Compact CSV change alert"""
    st.markdown("""
    <div class="csv-change-alert">
        <strong>🔄 CSV Updated!</strong> Check CSV Manager for details.
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 View Changes", key="csv_alert_compact"):
        st.session_state.csv_change_detected = False
        st.rerun()

def show_rebalancing_alert():
    """Compact rebalancing alert"""
    st.markdown("""
    <div class="rebalancing-needed">
        <strong>⚖️ Rebalancing Needed!</strong> Portfolio requires adjustment.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("⚖️ Fix Now", key="rebal_alert_compact"):
            pass
    with col3:
        if st.button("✕", key="dismiss_compact", help="Dismiss"):
            st.session_state.rebalancing_alert = None
            st.rerun()

def show_compact_csv_status_sidebar():
    """Compact CSV status for sidebar"""
    try:
        csv_status = api_client.get_csv_status()
        if csv_status and csv_status.get('success'):
            data = csv_status['data']
            current_csv = data.get('current_csv', {})
            
            st.write("**📊 CSV Status**")
            
            if current_csv.get('available'):
                st.success("✅ Ready")
                st.caption(f"{current_csv.get('total_symbols', 0)} stocks")
                
                fetch_time = current_csv.get('fetch_time')
                if fetch_time:
                    try:
                        fetch_dt = pd.to_datetime(fetch_time)
                        st.caption(f"Updated: {fetch_dt.strftime('%H:%M')}")
                    except:
                        st.caption("Recently updated")
            else:
                st.error("❌ No data")
            
            # Rebalancing indicator
            rebalancing_status = data.get('rebalancing_status', {})
            if rebalancing_status.get('rebalancing_needed'):
                st.warning("⚖️ Rebalancing needed")
            else:
                st.info("✅ Aligned")
        else:
            st.error("❌ Unknown")
            
    except Exception as e:
        st.error("❌ Check failed")

def show_system_status():
    """Clean dashboard with no duplicates"""
    st.header("🏠 System Dashboard")
    
    # Single status check
    with st.spinner("Loading system status..."):
        backend_status = api_client.check_backend_health()
        zerodha_test = api_client.test_zerodha_connection()
    
    # Main dashboard layout
    show_main_dashboard(backend_status, zerodha_test)

def show_main_dashboard(backend_status, zerodha_test):
    """Main dashboard content"""
    
    # Top status summary - SINGLE LINE
    show_status_summary(backend_status, zerodha_test)
    
    st.markdown("---")
    
    # Main content in 3 columns
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        show_system_overview(backend_status)
    
    with col2:
        show_live_data(zerodha_test)
    
    with col3:
        show_quick_actions()

def show_status_summary(backend_status, zerodha_test):
    """Single status line - no duplicates"""
    
    # Determine overall status
    backend_ok = backend_status.get('connected', False)
    zerodha_ok = zerodha_test.get('success', False)
    
    if backend_ok and zerodha_ok:
        st.success("🟢 **System Online** - All services running normally")
    elif backend_ok:
        st.warning("🟡 **Partial Service** - Backend online, Zerodha connection issues")
    else:
        st.error("🔴 **System Issues** - Backend connection problems")
    
    # Key info in one line
    if backend_ok:
        health_data = backend_status.get('data', {})
        
        info_parts = []
        
        # Add profile if available
        if zerodha_ok:
            profile_name = zerodha_test.get('profile_name', 'User')
            if len(profile_name) > 12:
                profile_name = profile_name[:10] + "..."
            info_parts.append(f"👤 {profile_name}")
        
        # Add live price if available
        if zerodha_ok and 'nifty_price' in zerodha_test:
            info_parts.append(f"📈 Nifty: ₹{zerodha_test['nifty_price']:,.0f}")
        elif zerodha_ok and 'alternative_data' in zerodha_test:
            sample_data = list(zerodha_test['alternative_data'].values())[0]
            symbol = list(zerodha_test['alternative_data'].keys())[0].replace('NSE:', '')
            info_parts.append(f"📊 {symbol}: ₹{sample_data['last_price']:,.0f}")
        
        # Add CSV status
        csv_service = health_data.get('csv_service', {})
        if csv_service.get('available'):
            info_parts.append("📊 CSV Ready")
        
        if info_parts:
            st.caption(" • ".join(info_parts))

def show_system_overview(backend_status):
    """System overview without duplication"""
    st.subheader("⚙️ System Status")
    
    if not backend_status.get('connected', False):
        st.error("Backend service is offline")
        st.caption(f"Error: {backend_status.get('error', 'Unknown error')}")
        return
    
    health_data = backend_status.get('data', {})
    init_status = health_data.get('initialization', {})
    
    # Service status in compact format
    services = [
        ("Investment Service", init_status.get('investment_service_created', False)),
        ("Authentication", init_status.get('auth_created', False)),
        ("Configuration", init_status.get('config_loaded', False)),
        ("CSV Processing", health_data.get('csv_service', {}).get('available', False))
    ]
    
    working_count = sum(1 for _, status in services if status)
    total_count = len(services)
    
    # Status summary
    if working_count == total_count:
        st.success(f"✅ All systems operational ({working_count}/{total_count})")
    elif working_count > total_count // 2:
        st.warning(f"⚠️ Partial functionality ({working_count}/{total_count})")
    else:
        st.error(f"❌ Multiple issues detected ({working_count}/{total_count})")
    
    # Service details in expandable section
    with st.expander("🔍 Service Details", expanded=False):
        for service_name, is_working in services:
            if is_working:
                st.write(f"✅ {service_name}")
            else:
                st.write(f"❌ {service_name}")
    
    # Zerodha connection status
    zerodha_conn = health_data.get('zerodha_connection', {})
    if zerodha_conn.get('authenticated', False):
        st.info("🔗 **Zerodha API**: Connected and authenticated")
    else:
        error_msg = zerodha_conn.get('error_message', 'Not connected')
        st.warning(f"🔗 **Zerodha API**: {error_msg}")

def show_live_data(zerodha_test):
    """Live market data section"""
    st.subheader("📈 Live Data")
    
    if not zerodha_test.get('success', False):
        st.warning("⚠️ **No live data**")
        st.caption("Zerodha connection required")
        return
    
    # Show available market data
    if 'nifty_price' in zerodha_test:
        nifty_data = zerodha_test.get('nifty_data', {})
        
        # Main price display
        st.metric(
            "Nifty 50",
            f"₹{zerodha_test['nifty_price']:,.2f}",
            delta=f"{nifty_data.get('change', 0):,.2f}"
        )
        
        # Additional info
        ohlc = nifty_data.get('ohlc', {})
        if ohlc:
            st.caption(f"High: ₹{ohlc.get('high', 0):,.0f} | Low: ₹{ohlc.get('low', 0):,.0f}")
    
    elif 'alternative_data' in zerodha_test:
        # Show alternative stock data
        st.write("**Sample Market Data:**")
        
        for symbol, data in list(zerodha_test['alternative_data'].items())[:2]:
            clean_symbol = symbol.replace('NSE:', '')
            st.write(f"• {clean_symbol}: ₹{data['last_price']:,.2f}")
    
    else:
        st.success("🟢 **Connected**")
        st.caption("API connection established")
    
    # Connection timestamp
    if 'timestamp' in zerodha_test:
        timestamp = pd.to_datetime(zerodha_test['timestamp'])
        st.caption(f"Updated: {timestamp.strftime('%H:%M:%S')}")

def show_quick_actions():
    """Quick action buttons"""
    st.subheader("🚀 Actions")
    
    # Test connection
    if st.button("🧪 Test Connection", use_container_width=True, key="test_conn"):
        with st.spinner("Testing..."):
            result = api_client.test_zerodha_connection()
            if result.get('success'):
                st.success("✅ Test passed")
                if 'nifty_price' in result:
                    st.info(f"Live: ₹{result['nifty_price']:,.0f}")
            else:
                st.error("❌ Test failed")
    
    # Refresh system
    if st.button("🔄 Refresh System", use_container_width=True, key="refresh_sys"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    # Quick navigation
    st.markdown("**Quick Nav:**")
    
    nav_col1, nav_col2 = st.columns(2)
    
    with nav_col1:
        if st.button("📊", help="CSV Manager", use_container_width=True):
            pass
    
    with nav_col2:
        if st.button("💰", help="Investment", use_container_width=True):
            pass

def show_csv_tracking():
    """CSV tracking and change detection page"""
    st.header("📊 CSV Data Tracking")
    
    # CSV Status Overview
    with st.spinner("Loading CSV tracking data..."):
        csv_status = api_client.get_csv_status()
    
    if not csv_status or not csv_status.get('success'):
        st.error(f"❌ Cannot load CSV status: {csv_status.get('error', 'Unknown error') if csv_status else 'No response'}")
        return
    
    data = csv_status['data']
    current_csv = data.get('current_csv', {})
    csv_history = data.get('csv_history', [])
    connection_status = data.get('connection_status', {})
    rebalancing_status = data.get('rebalancing_status', {})
    
    # Current CSV Status
    st.subheader("📋 Current CSV Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if current_csv.get('available'):
            st.metric("📊 CSV Status", "✅ Available")
        else:
            st.metric("📊 CSV Status", "❌ Not Available")
    
    with col2:
        total_symbols = current_csv.get('total_symbols', 0)
        st.metric("📈 Total Stocks", total_symbols)
    
    with col3:
        csv_hash = current_csv.get('csv_hash', 'Unknown')
        st.metric("🔖 Data Hash", csv_hash[:8] + "..." if len(csv_hash) > 8 else csv_hash)
    
    with col4:
        fetch_time = current_csv.get('fetch_time')
        if fetch_time:
            fetch_dt = pd.to_datetime(fetch_time)
            time_str = fetch_dt.strftime('%H:%M:%S')
        else:
            time_str = "Unknown"
        st.metric("⏰ Last Update", time_str)
    
    # CSV Source Information
    if current_csv.get('source_url'):
        st.info(f"**Data Source:** {current_csv['source_url']}")
    
    # Force Refresh Section
    st.subheader("🔄 Manual CSV Refresh")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("Force refresh CSV data to check for the latest changes.")
        st.caption("This will fetch fresh data from the source and detect any changes.")
    
    with col2:
        if st.button("🔄 Force Refresh CSV", type="primary", use_container_width=True):
            with st.spinner("Refreshing CSV data..."):
                refresh_result = api_client.force_csv_refresh()
            
            if refresh_result and refresh_result.get('success'):
                refresh_data = refresh_result['data']
                
                if refresh_data.get('csv_changed'):
                    st.success("✅ CSV data refreshed - Changes detected!")
                    
                    # Show change details
                    change_details = refresh_data.get('change_details', {})
                    st.write("**Change Details:**")
                    st.write(f"• Old hash: {change_details.get('old_hash', 'Unknown')}")
                    st.write(f"• New hash: {change_details.get('new_hash', 'Unknown')}")
                    st.write(f"• Symbols: {change_details.get('old_symbols', 0)} → {change_details.get('new_symbols', 0)}")
                    
                    # Show next steps
                    next_steps = refresh_data.get('next_steps', [])
                    if next_steps:
                        st.write("**Next Steps:**")
                        for step in next_steps:
                            st.write(f"• {step}")
                    
                    # Update session state
                    st.session_state.csv_change_detected = True
                    st.session_state.last_csv_hash = change_details.get('new_hash')
                    
                    # Check rebalancing
                    rebalancing_check = refresh_data.get('rebalancing_check')
                    if rebalancing_check and rebalancing_check.get('rebalancing_needed'):
                        st.session_state.rebalancing_alert = rebalancing_check
                        st.warning("⚖️ Rebalancing is now needed due to CSV changes!")
                else:
                    st.info("ℹ️ CSV data refreshed - No changes detected")
                    st.write("The CSV data is up to date with no new changes.")
            else:
                st.error(f"❌ Failed to refresh CSV: {refresh_result.get('error', 'Unknown error') if refresh_result else 'No response'}")
    
    # Rebalancing Status
    st.subheader("⚖️ Rebalancing Status")
    
    if rebalancing_status.get('rebalancing_needed'):
        st.markdown('<div class="status-card-small warning-status">⚠️ <strong>Rebalancing Required</strong></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Reason:** {rebalancing_status.get('reason', 'Unknown')}")
            
            new_stocks = rebalancing_status.get('new_stocks', [])
            removed_stocks = rebalancing_status.get('removed_stocks', [])
            
            if new_stocks:
                st.write(f"**New stocks to add:** {', '.join(new_stocks[:5])}{'...' if len(new_stocks) > 5 else ''}")
            
            if removed_stocks:
                st.write(f"**Stocks to remove:** {', '.join(removed_stocks[:5])}{'...' if len(removed_stocks) > 5 else ''}")
        
        with col2:
            if st.button("⚖️ Go to Rebalancing", use_container_width=True):
                pass
    else:
        st.markdown('<div class="status-card-small success-status">✅ <strong>Portfolio Aligned</strong></div>', unsafe_allow_html=True)
        st.write(f"**Status:** {rebalancing_status.get('reason', 'Portfolio matches current CSV')}")
    
    # CSV History
    if csv_history:
        st.subheader("📈 CSV Change History")
        
        history_df = pd.DataFrame(csv_history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        history_df['csv_hash'] = history_df['csv_hash'].apply(lambda x: x[:8] + "..." if len(x) > 8 else x)
        
        display_history = history_df[['timestamp', 'csv_hash']].rename(columns={
            'timestamp': 'Timestamp',
            'csv_hash': 'Data Hash'
        })
        
        st.dataframe(display_history, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No CSV history available")
    
    # Connection Status
    st.subheader("🔗 Connection Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**CSV Source:**")
        if connection_status.get('csv_accessible'):
            st.success("✅ CSV source accessible")
        else:
            st.error("❌ CSV source not accessible")
    
    with col2:
        st.write("**Market Status:**")
        if connection_status.get('market_open'):
            st.info("🟢 Market Open")
        else:
            st.info("🔴 Market Closed")

def show_initial_investment():
    """Initial investment interface"""
    st.header("💰 Initial Investment Setup")
    
    # Check if already have portfolio
    portfolio_status = api_client.get_portfolio_status()
    if portfolio_status and portfolio_status.get('success'):
        data = portfolio_status['data']
        if data['status'] == 'active':
            st.warning("⚠️ You already have an active portfolio. Use the Rebalancing page to make changes.")
            
            # Show current portfolio summary
            summary = data['portfolio_summary']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("💰 Current Value", f"₹{summary['current_value']:,.0f}")
            with col2:
                st.metric("📥 Total Invested", f"₹{summary['total_investment']:,.0f}")
            with col3:
                st.metric("📈 Total Returns", f"₹{summary['total_returns']:,.0f}")
            
            return
    
    # Get investment requirements
    st.subheader("📋 Investment Requirements")
    
    with st.spinner("Getting investment requirements..."):
        requirements = api_client.get_investment_requirements()
    
    if not requirements or not requirements.get('success'):
        st.error(f"❌ Cannot get investment requirements: {requirements.get('error', 'Unknown error') if requirements else 'No response'}")
        return
    
    req_data = requirements['data']
    
    # Show requirements
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Current Market Data")
        
        stocks_data = req_data['stocks_data']['stocks']
        min_investment_info = req_data['minimum_investment']
        
        # Requirements summary
        st.markdown(f"""
        **Investment Requirements:**
        - **Minimum Investment**: ₹{min_investment_info['minimum_investment']:,.0f}
        - **Recommended Minimum**: ₹{min_investment_info['recommended_minimum']:,.0f}
        - **Total Stocks**: {min_investment_info['total_stocks']}
        - **Most Expensive Stock**: {min_investment_info['most_expensive_stock']['symbol']} at ₹{min_investment_info['most_expensive_stock']['price']:,.2f}
        
        **Strategy**: Equal weight allocation (4-7% per stock, targeting 5%)
        """)
        
        # Show data quality
        data_quality = req_data['data_quality']
        st.info(f"**Data Source**: {data_quality['data_source']} | **Success Rate**: {data_quality['price_success_rate']:.1f}%")
    
    with col2:
        st.subheader("💰 Investment Amount")
        
        min_amount = min_investment_info['minimum_investment']
        recommended_amount = min_investment_info['recommended_minimum']
        
        # Quick amount buttons
        st.write("**Quick Options:**")
        col2a, col2b = st.columns(2)
        
        with col2a:
            if st.button(f"Min\n₹{min_amount:,.0f}", use_container_width=True):
                st.session_state.investment_amount = min_amount
        
        with col2b:
            if st.button(f"Recommended\n₹{recommended_amount:,.0f}", use_container_width=True):
                st.session_state.investment_amount = recommended_amount
        
        # Manual input
        investment_amount = st.number_input(
            "Investment Amount (₹)",
            min_value=min_amount,
            value=st.session_state.get('investment_amount', recommended_amount),
            step=10000,
            help=f"Minimum required: ₹{min_amount:,.0f}"
        )
        
        st.session_state.investment_amount = investment_amount
    
    # Calculate investment plan
    st.subheader("🧮 Investment Plan")
    
    if st.button("📊 Calculate Investment Plan", type="primary", use_container_width=True):
        with st.spinner("Calculating optimal allocation..."):
            plan_result = api_client.calculate_investment_plan(investment_amount)
        
        if plan_result and plan_result.get('success'):
            st.session_state.investment_plan = plan_result['data']
            st.success("✅ Investment plan calculated!")
        else:
            st.error(f"❌ Failed to calculate investment plan: {plan_result.get('error', 'Unknown error') if plan_result else 'No response'}")
    
    # Show investment plan
    if 'investment_plan' in st.session_state:
        plan = st.session_state.investment_plan
        
        # Plan summary
        summary = plan['summary']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Total Investment", f"₹{summary['total_investment_value']:,.0f}")
        
        with col2:
            st.metric("📝 Total Orders", summary['total_orders'])
        
        with col3:
            st.metric("💵 Remaining Cash", f"₹{summary['remaining_cash']:,.0f}")
        
        with col4:
            st.metric("📊 Utilization", f"{summary['utilization_percent']:.1f}%")
        
        # Orders table
        st.subheader("📋 Proposed Orders")
        
        orders_df = pd.DataFrame(plan['orders'])
        orders_df['price_fmt'] = orders_df['price'].apply(lambda x: f"₹{x:.2f}")
        orders_df['value_fmt'] = orders_df['value'].apply(lambda x: f"₹{x:,.0f}")
        orders_df['allocation_fmt'] = orders_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
        
        display_orders = orders_df[['symbol', 'shares', 'price_fmt', 'value_fmt', 'allocation_fmt']].rename(columns={
            'symbol': 'Stock',
            'shares': 'Shares',
            'price_fmt': 'Price',
            'value_fmt': 'Investment',
            'allocation_fmt': 'Allocation %'
        })
        
        st.dataframe(display_orders, use_container_width=True, hide_index=True)
        
        # Validation results
        validation = plan['validation']
        if validation['stocks_in_range'] == len(plan['orders']):
            st.success(f"✅ All {validation['stocks_in_range']} stocks within target allocation range (4-7%)")
        else:
            st.warning(f"⚠️ {validation['stocks_in_range']}/{len(plan['orders'])} stocks in target range. {len(validation['violations'])} violations.")
            if validation['violations']:
                for violation in validation['violations']:
                    st.caption(f"• {violation}")
        
        # Execute investment
        st.subheader("🚀 Execute Investment")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 This will create system orders for tracking. No live trades will be placed on Zerodha.")
        
        with col2:
            if st.button("🚀 Execute Initial Investment", type="primary", use_container_width=True):
                with st.spinner("Executing investment..."):
                    result = api_client.execute_initial_investment(investment_amount)
                
                if result and result.get('success'):
                    st.success("✅ Initial investment executed successfully!")
                    st.balloons()
                    del st.session_state.investment_plan  # Clear the plan
                    st.rerun()
                else:
                    st.error(f"❌ Failed to execute investment: {result.get('error', 'Unknown error') if result else 'No response'}")

def show_portfolio_overview():
    """Portfolio overview built from orders"""
    st.header("📈 Portfolio Overview")
    
    with st.spinner("Loading portfolio data..."):
        portfolio_result = api_client.get_portfolio_status()
    
    if not portfolio_result or not portfolio_result.get('success'):
        st.error(f"❌ Cannot load portfolio: {portfolio_result.get('error', 'Unknown error') if portfolio_result else 'No response'}")
        return
    
    portfolio_data = portfolio_result['data']
    
    if portfolio_data['status'] == 'empty':
        st.info("📭 No portfolio found. Please complete initial investment first.")
        if st.button("➡️ Go to Initial Investment"):
            pass
        return
    elif portfolio_data['status'] == 'error':
        st.error(f"❌ Portfolio error: {portfolio_data['error']}")
        return
    
    # Portfolio Summary
    holdings = portfolio_data['holdings']
    summary = portfolio_data['portfolio_summary']
    
    st.subheader("💰 Portfolio Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Current Value", f"₹{summary['current_value']:,.0f}")
    
    with col2:
        st.metric("📥 Total Invested", f"₹{summary['total_investment']:,.0f}")
    
    with col3:
        returns_color = "normal" if summary['total_returns'] >= 0 else "inverse"
        st.metric("📈 Total Returns", f"₹{summary['total_returns']:,.0f}", 
                 delta=f"{summary['returns_percentage']:.2f}%", delta_color=returns_color)
    
    with col4:
        st.metric("📊 Stock Count", summary['stock_count'])
    
    # Performance Metrics (if available)
    if 'performance_metrics' in portfolio_data:
        metrics = portfolio_data['performance_metrics']
        
        st.subheader("📈 Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'cagr' in summary:
                st.metric("📊 CAGR", f"{summary.get('cagr', 0):.2f}%")
        
        with col2:
            if summary.get('investment_period_days'):
                st.metric("📅 Days Invested", summary['investment_period_days'])
        
        with col3:
            best_performer = metrics.get('best_performer', {})
            if best_performer:
                st.metric("🏆 Best Performer", 
                         best_performer.get('symbol', 'N/A'),
                         delta=f"{best_performer.get('percentage_return', 0):.2f}%")
        
        with col4:
            worst_performer = metrics.get('worst_performer', {})
            if worst_performer:
                st.metric("📉 Worst Performer", 
                         worst_performer.get('symbol', 'N/A'),
                         delta=f"{worst_performer.get('percentage_return', 0):.2f}%")
    
    # Holdings Table
    if holdings:
        st.subheader("📋 Current Holdings")
        
        holdings_list = []
        for symbol, holding in holdings.items():
            holdings_list.append({
                'symbol': symbol,
                'shares': holding.get('shares', 0),
                'avg_price': holding.get('avg_price', 0),
                'current_price': holding.get('current_price', 0),
                'investment_value': holding.get('investment_value', 0),
                'current_value': holding.get('current_value', 0),
                'pnl': holding.get('pnl', 0),
                'pnl_percent': holding.get('pnl_percent', 0),
                'allocation_percent': holding.get('allocation_percent', 0)
            })
        
        df = pd.DataFrame(holdings_list)
        
        # Format for display
        df['avg_price_fmt'] = df['avg_price'].apply(lambda x: f"₹{x:.2f}")
        df['current_price_fmt'] = df['current_price'].apply(lambda x: f"₹{x:.2f}")
        df['investment_fmt'] = df['investment_value'].apply(lambda x: f"₹{x:,.0f}")
        df['current_fmt'] = df['current_value'].apply(lambda x: f"₹{x:,.0f}")
        df['pnl_fmt'] = df['pnl'].apply(lambda x: f"₹{x:,.0f}")
        df['allocation_fmt'] = df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
        
        # Display table
        display_df = df[['symbol', 'shares', 'avg_price_fmt', 'current_price_fmt', 
                        'investment_fmt', 'current_fmt', 'pnl_fmt', 'pnl_percent', 'allocation_fmt']].rename(columns={
            'symbol': 'Stock',
            'shares': 'Shares',
            'avg_price_fmt': 'Avg Price',
            'current_price_fmt': 'Current Price',
            'investment_fmt': 'Invested',
            'current_fmt': 'Current Value',
            'pnl_fmt': 'P&L (₹)',
            'pnl_percent': 'P&L (%)',
            'allocation_fmt': 'Allocation'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Portfolio Visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Portfolio Allocation")
            
            fig = px.pie(
                df,
                values='current_value',
                names='symbol',
                title='Portfolio Allocation by Value'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Performance Overview")
            
            # Top gainers
            top_gainers = df.nlargest(3, 'pnl_percent')[['symbol', 'pnl_percent']]
            st.write("🏆 **Top Gainers:**")
            for _, row in top_gainers.iterrows():
                st.write(f"• {row['symbol']}: +{row['pnl_percent']:.2f}%")
            
            # Allocation analysis
            target_allocation = 100 / len(df)
            deviation = df['allocation_percent'].std()
            
            st.write("⚖️ **Allocation Analysis:**")
            st.write(f"• Target per stock: {target_allocation:.2f}%")
            st.write(f"• Current deviation: {deviation:.2f}%")
            
            if deviation > 1.5:
                st.warning("⚠️ High allocation deviation - consider rebalancing")
            else:
                st.success("✅ Well-balanced allocation")

def show_rebalancing():
    """Rebalancing interface with CSV change awareness"""
    st.header("⚖️ Portfolio Rebalancing")
    
    # Check if we have a portfolio first
    portfolio_status = api_client.get_portfolio_status()
    if not portfolio_status or not portfolio_status.get('success'):
        st.error("❌ Cannot load portfolio status for rebalancing")
        return
    
    if portfolio_status['data']['status'] == 'empty':
        st.info("📭 No portfolio found. Please complete initial investment first.")
        if st.button("➡️ Go to Initial Investment"):
            pass
        return
    
    # Check CSV status and changes
    st.subheader("📊 CSV Status & Changes")
    
    with st.spinner("Checking CSV status and changes..."):
        csv_status = api_client.get_csv_status()
    
    if csv_status and csv_status.get('success'):
        csv_data = csv_status['data']
        current_csv = csv_data.get('current_csv', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if current_csv.get('available'):
                st.success("✅ CSV Data Available")
                st.caption(f"Hash: {current_csv.get('csv_hash', 'Unknown')[:8]}...")
            else:
                st.error("❌ CSV Data Not Available")
        
        with col2:
            st.metric("📈 Current Stocks", current_csv.get('total_symbols', 0))
        
        with col3:
            fetch_time = current_csv.get('fetch_time')
            if fetch_time:
                fetch_dt = pd.to_datetime(fetch_time)
                st.metric("⏰ Last Update", fetch_dt.strftime('%H:%M'))
            else:
                st.metric("⏰ Last Update", "Unknown")
    
    # Check if rebalancing is needed
    st.subheader("📊 Rebalancing Status")
    
    with st.spinner("Checking rebalancing requirements..."):
        rebalancing_check = api_client.check_rebalancing_needed()
    
    if not rebalancing_check or not rebalancing_check.get('success'):
        st.error("❌ Cannot check rebalancing requirements")
        return
    
    rebal_data = rebalancing_check['data']
    
    # Show rebalancing status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if rebal_data['rebalancing_needed']:
            st.markdown('<div class="status-card-small warning-status">⚠️ <strong>Rebalancing Needed</strong><br>Portfolio needs adjustment</div>', unsafe_allow_html=True)
            st.write(f"**Reason**: {rebal_data['reason']}")
            
            if rebal_data.get('new_stocks'):
                st.write(f"**New stocks to add**: {', '.join(rebal_data['new_stocks'][:5])}")
            if rebal_data.get('removed_stocks'):
                st.write(f"**Stocks to remove**: {', '.join(rebal_data['removed_stocks'][:5])}")
        else:
            st.markdown('<div class="status-card-small success-status">✅ <strong>Portfolio Balanced</strong><br>No rebalancing needed</div>', unsafe_allow_html=True)
            st.write(f"**Reason**: {rebal_data['reason']}")
    
    with col2:
        st.subheader("🔄 Rebalancing Options")
        
        if rebal_data['rebalancing_needed']:
            if st.button("🔄 Force CSV Refresh", use_container_width=True):
                with st.spinner("Refreshing CSV data..."):
                    refresh_result = api_client.force_csv_refresh()
                
                if refresh_result and refresh_result.get('success'):
                    if refresh_result['data'].get('csv_changed'):
                        st.success("✅ CSV refreshed - Changes detected!")
                        st.rerun()
                    else:
                        st.info("ℹ️ CSV refreshed - No new changes")
                else:
                    st.error("❌ Failed to refresh CSV")
            
            st.info("💡 Rebalancing execution coming soon!")
            st.write("**Future Features:**")
            st.write("• Calculate new allocation")
            st.write("• Generate buy/sell orders") 
            st.write("• Execute rebalancing")
        else:
            st.success("✅ No action needed")
    
    # Show current portfolio summary for context
    portfolio_data = portfolio_status['data']
    summary = portfolio_data['portfolio_summary']
    
    st.subheader("💰 Current Portfolio Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Current Value", f"₹{summary['current_value']:,.0f}")
    with col2:
        st.metric("📥 Total Invested", f"₹{summary['total_investment']:,.0f}")
    with col3:
        st.metric("📈 Total Returns", f"₹{summary['total_returns']:,.0f}")
    with col4:
        st.metric("📊 Stock Count", summary['stock_count'])

def show_order_history():
    """Show all system orders"""
    st.header("📋 Order History")
    
    with st.spinner("Loading order history..."):
        orders_result = api_client.get_system_orders()
    
    if not orders_result or not orders_result.get('success'):
        st.error(f"❌ Cannot load orders: {orders_result.get('error', 'Unknown error') if orders_result else 'No response'}")
        return
    
    orders_data = orders_result['data']
    orders = orders_data['orders']
    
    if not orders:
        st.info("📭 No orders found. Start with Initial Investment.")
        if st.button("➡️ Go to Initial Investment"):
            pass
        return
    
    # Orders summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📝 Total Orders", orders_data['total_orders'])
    
    with col2:
        buy_orders = len([o for o in orders if o['action'] == 'BUY'])
        st.metric("📈 Buy Orders", buy_orders)
    
    with col3:
        total_value = sum(o['value'] for o in orders)
        st.metric("💰 Total Value", f"₹{total_value:,.0f}")
    
    # Convert to DataFrame
    df = pd.DataFrame(orders)
    
    # Format columns
    df['price_fmt'] = df['price'].apply(lambda x: f"₹{x:.2f}")
    df['value_fmt'] = df['value'].apply(lambda x: f"₹{x:,.0f}")
    df['allocation_fmt'] = df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
    df['execution_time'] = pd.to_datetime(df['execution_time']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Display table (showing recent orders first)
    display_df = df[['execution_time', 'symbol', 'action', 'shares', 'price_fmt', 'value_fmt', 'allocation_fmt', 'session_type']].rename(columns={
        'execution_time': 'Date/Time',
        'symbol': 'Stock',
        'action': 'Action',
        'shares': 'Shares',
        'price_fmt': 'Price',
        'value_fmt': 'Value',
        'allocation_fmt': 'Allocation %',
        'session_type': 'Session'
    }).sort_values('Date/Time', ascending=False)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Order Statistics
    st.subheader("📊 Order Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Orders by action
        action_counts = df['action'].value_counts()
        fig = px.pie(
            values=action_counts.values,
            names=action_counts.index,
            title='Orders by Action'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Value by stock
        stock_values = df.groupby('symbol')['value'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=stock_values.index,
            y=stock_values.values,
            title='Top 10 Stocks by Order Value'
        )
        fig.update_layout(xaxis_title="Stock", yaxis_title="Total Value (₹)")
        st.plotly_chart(fig, use_container_width=True)

def show_csv_stocks():
    """Show CSV stocks without live prices"""
    st.header("📄 CSV Stock List")
    
    with st.spinner("Loading CSV stocks..."):
        csv_result = api_client.get_csv_stocks()
    
    if not csv_result or not csv_result.get('success'):
        st.error(f"❌ Cannot load CSV stocks: {csv_result.get('error', 'Unknown error') if csv_result else 'No response'}")
        return
    
    data = csv_result['data']
    stocks = data.get('stocks', [])
    
    # CSV Info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total Stocks", data.get('total_stocks', 0))
    
    with col2:
        csv_info = data.get('csv_info', {})
        fetch_time = csv_info.get('fetch_time', 'Unknown')
        if fetch_time != 'Unknown':
            fetch_time = pd.to_datetime(fetch_time).strftime('%Y-%m-%d %H:%M')
        st.metric("📅 Last Updated", fetch_time)
    
    with col3:
        csv_hash = csv_info.get('csv_hash', 'Unknown')
        st.metric("🔖 CSV Hash", csv_hash[:8] + "..." if len(csv_hash) > 8 else csv_hash)
    
    # CSV Source Info
    if csv_info.get('source_url'):
        st.info(f"**CSV Source:** {csv_info['source_url']}")
    
    # Price data status
    price_status = data.get('price_data_status', {})
    if price_status.get('live_prices_used'):
        st.success(f"✅ Live prices from {price_status.get('market_data_source', 'Zerodha API')}")
    else:
        st.warning(f"⚠️ Using fallback prices - {price_status.get('price_fetch_reason', 'Unknown reason')}")
    
    # Stocks Table
    if stocks:
        st.subheader("📋 Stock List with Current Prices")
        
        # Create display dataframe
        stocks_df = pd.DataFrame(stocks)
        
        # Format price column
        stocks_df['price_fmt'] = stocks_df['price'].apply(lambda x: f"₹{x:.2f}")
        
        # Select display columns
        display_columns = ['symbol', 'price_fmt']
        column_mapping = {
            'symbol': 'Stock Symbol',
            'price_fmt': 'Current Price'
        }
        
        # Add additional fields from CSV if available
        for col in ['momentum', 'volatility', 'score']:
            if col in stocks_df.columns:
                stocks_df[f'{col}_fmt'] = stocks_df[col].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else str(x))
                display_columns.append(f'{col}_fmt')
                column_mapping[f'{col}_fmt'] = col.title()
        
        display_df = stocks_df[display_columns].rename(columns=column_mapping)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Price distribution chart
        if len(stocks) > 5:
            st.subheader("📊 Price Distribution")
            
            fig = px.histogram(
                stocks_df,
                x='price',
                title='Stock Price Distribution',
                nbins=20
            )
            fig.update_layout(xaxis_title="Price (₹)", yaxis_title="Number of Stocks")
            st.plotly_chart(fig, use_container_width=True)
        
        # Simple stats
        st.subheader("📊 CSV Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Price Statistics:**")
            st.write(f"• Minimum price: ₹{stocks_df['price'].min():.2f}")
            st.write(f"• Maximum price: ₹{stocks_df['price'].max():.2f}")
            st.write(f"• Average price: ₹{stocks_df['price'].mean():.2f}")
            st.write(f"• Median price: ₹{stocks_df['price'].median():.2f}")
        
        with col2:
            st.write("**Data Quality:**")
            st.write(f"• Total stocks: {len(stocks)}")
            st.write(f"• Price success rate: {price_status.get('success_rate', 0):.1f}%")
            st.write(f"• Data source: {price_status.get('market_data_source', 'Unknown')}")
            if price_status.get('market_open') is not None:
                market_status = "Open 🟢" if price_status['market_open'] else "Closed 🔴"
                st.write(f"• Market status: {market_status}")

def show_system_info():
    """System information and diagnostics"""
    st.header("⚙️ System Information")
    
    # Overall Health Check
    st.subheader("🏥 Health Check")
    
    with st.spinner("Running comprehensive health check..."):
        backend_status = api_client.check_backend_health()
        zerodha_test = api_client.test_zerodha_connection()
        csv_result = api_client.get_csv_stocks()
        orders_result = api_client.get_system_orders()
        portfolio_result = api_client.get_portfolio_status()
        csv_status = api_client.get_csv_status()
    
    # Create status summary
    checks = [
        ("Backend API", backend_status.get('connected', False)),
        ("Zerodha Connection", zerodha_test.get('success', False)),
        ("CSV Data", csv_result.get('success', False)),
        ("Order System", orders_result.get('success', False)),
        ("Portfolio Service", portfolio_result.get('success', False)),
        ("CSV Tracking", csv_status.get('success', False))
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**System Components:**")
        for check_name, status in checks:
            icon = "✅" if status else "❌"
            st.write(f"{icon} {check_name}")
    
    with col2:
        passed = sum(1 for _, status in checks if status)
        total = len(checks)
        health_percentage = (passed / total) * 100
        
        st.metric("🏥 Overall Health", f"{health_percentage:.0f}%", 
                 delta=f"{passed}/{total} checks passed")
    
    # Detailed System Info
    if backend_status.get('connected', False):
        st.subheader("🔧 Backend Details")
        
        health_data = backend_status.get('data', {})
        
        # Initialization status
        init_status = health_data.get('initialization', {})
        st.write("**Initialization Status:**")
        for key, value in init_status.items():
            if key != 'error_message':
                icon = "✅" if value else "❌"
                readable_key = key.replace('_', ' ').title()
                st.write(f"{icon} {readable_key}")
        
        # Error message if any
        if init_status.get('error_message'):
            st.error(f"**Initialization Error:** {init_status['error_message']}")
        
        # Zerodha connection details
        zerodha_conn = health_data.get('zerodha_connection', {})
        if zerodha_conn:
            st.write("**Zerodha Connection Details:**")
            for key, value in zerodha_conn.items():
                if key != 'error_message':
                    icon = "✅" if value else "❌"
                    readable_key = key.replace('_', ' ').title()
                    st.write(f"{icon} {readable_key}")
            
            if zerodha_conn.get('error_message'):
                st.warning(f"**Zerodha Error:** {zerodha_conn['error_message']}")
        
        # CSV Service details
        csv_service = health_data.get('csv_service', {})
        if csv_service:
            st.write("**CSV Service Details:**")
            for key, value in csv_service.items():
                if key != 'error_message':
                    icon = "✅" if value else "❌"
                    readable_key = key.replace('_', ' ').title()
                    st.write(f"{icon} {readable_key}")
            
            if csv_service.get('error_message'):
                st.warning(f"**CSV Service Error:** {csv_service['error_message']}")
    
    # CSV Tracking Details
    if csv_status and csv_status.get('success'):
        st.subheader("📊 CSV Tracking Details")
        
        csv_data = csv_status['data']
        current_csv = csv_data.get('current_csv', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Current CSV:**")
            st.write(f"• Available: {'✅' if current_csv.get('available') else '❌'}")
            st.write(f"• Hash: {current_csv.get('csv_hash', 'Unknown')[:12]}...")
            st.write(f"• Symbols: {current_csv.get('total_symbols', 0)}")
            st.write(f"• Last Fetch: {current_csv.get('fetch_time', 'Unknown')}")
        
        with col2:
            connection_status = csv_data.get('connection_status', {})
            st.write("**Connection Status:**")
            st.write(f"• CSV Accessible: {'✅' if connection_status.get('csv_accessible') else '❌'}")
            st.write(f"• Market Open: {'✅' if connection_status.get('market_open') else '❌'}")
            st.write(f"• Auto Tracking: {'✅' if csv_data.get('auto_tracking') else '❌'}")
        
        # CSV History
        csv_history = csv_data.get('csv_history', [])
        if csv_history:
            st.write("**Recent CSV Changes:**")
            for entry in csv_history[-3:]:  # Show last 3 entries
                timestamp = pd.to_datetime(entry['timestamp']).strftime('%Y-%m-%d %H:%M')
                st.write(f"• {timestamp}: {entry['csv_hash'][:8]}...")
    
    # Available Endpoints
    st.subheader("🌐 Available API Endpoints")
    
    endpoints = [
        "/health - System health check with CSV tracking",
        "/api/test-nifty - Test Zerodha with Nifty price",
        "/api/csv-status - Get CSV tracking status",
        "/api/force-csv-refresh - Force refresh CSV data",
        "/api/investment/requirements - Get investment requirements",
        "/api/investment/calculate-plan - Calculate investment plan",
        "/api/investment/execute-initial - Execute initial investment",
        "/api/investment/rebalancing-check - Check rebalancing status",
        "/api/investment/csv-stocks - Get CSV stocks with prices",
        "/api/investment/system-orders - Get order history", 
        "/api/investment/portfolio-status - Get portfolio status",
        "/api/investment/csv-status - Get detailed CSV status",
        "/api/investment/force-csv-refresh - Force CSV refresh",
        "/api/investment/execute-rebalancing - Execute rebalancing (coming soon)"
    ]
    
    for endpoint in endpoints:
        st.write(f"• {endpoint}")
    
    # System Configuration
    st.subheader("⚙️ Configuration")
    
    config_info = {
        "API Base URL": API_BASE_URL,
        "Frontend Framework": "Streamlit",
        "CSV Auto-Tracking": "Enabled",
        "Rebalancing Alerts": "Enabled",
        "Last Refresh": st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S'),
        "Session Started": "Active"
    }
    
    for key, value in config_info.items():
        st.write(f"**{key}:** {value}")
    
    # Debug Information
    with st.expander("🔧 Debug Information"):
        st.write("**Session State:**")
        debug_session = {
            "Last CSV Hash": st.session_state.get('last_csv_hash', 'None'),
            "CSV Change Detected": st.session_state.get('csv_change_detected', False),
            "Rebalancing Alert": bool(st.session_state.get('rebalancing_alert')),
            "Investment Plan": bool(st.session_state.get('investment_plan')),
            "Last Refresh": st.session_state.get('last_refresh', 'Unknown')
        }
        
        for key, value in debug_session.items():
            st.write(f"• {key}: {value}")
        
        if st.button("🗑️ Clear Session State"):
            for key in list(st.session_state.keys()):
                if key not in ['last_refresh']:  # Keep some essential state
                    del st.session_state[key]
            st.success("✅ Session state cleared!")
            st.rerun()

if __name__ == "__main__":
    main()