# frontend/streamlit_app.py - Clean Dashboard (Fixed CSS)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Investment Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar completely and add styling
hide_sidebar_css = """
<style>
section[data-testid="stSidebar"] {
    display: none !important;
}

.main .block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

.dashboard-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.dashboard-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
}

.dashboard-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
    margin: 0.5rem 0 0 0;
}

.profile-connected {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    text-align: center;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.profile-disconnected {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    text-align: center;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
}

.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 1rem 2rem;
    font-weight: 700;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
    width: 100%;
}

.success-box {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
}

.error-box {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
}

.warning-box {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(245, 158, 11, 0.3);
}

.info-box {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-weight: 600;
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
}
</style>
"""

st.markdown(hide_sidebar_css, unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state
if 'zerodha_authenticated' not in st.session_state:
    st.session_state.zerodha_authenticated = False
if 'zerodha_profile' not in st.session_state:
    st.session_state.zerodha_profile = None
if 'last_auth_check' not in st.session_state:
    st.session_state.last_auth_check = None

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
    
    def _request(self, method, endpoint, data=None):
        try:
            url = f"{self.base_url}{endpoint}"
            if method == 'GET':
                response = requests.get(url, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=self.timeout)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def check_zerodha_status(self):
        return self._request('GET', '/api/test-nifty')
    
    def get_zerodha_login_url(self):
        return self._request('GET', '/auth/zerodha-login-url')
    
    def exchange_token(self, request_token):
        return self._request('POST', '/auth/exchange-token', {'request_token': request_token})
    
    def get_portfolio_status(self):
        return self._request('GET', '/api/investment/portfolio-status')
    
    def get_system_orders(self):
        return self._request('GET', '/api/investment/system-orders')
    
    def get_live_portfolio(self):
        return self._request('GET', '/api/portfolio/live')

api_client = APIClient(API_BASE_URL)

def main():
    # Header
    st.markdown("""
    <div class="dashboard-header">
        <h1 class="dashboard-title">📈 Investment Dashboard</h1>
        <p class="dashboard-subtitle">Portfolio Management & Live Trading</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check authentication
    check_authentication()
    
    # Show profile status
    show_profile_status()
    
    # Main content
    if st.session_state.zerodha_authenticated:
        show_main_dashboard()
    else:
        show_zerodha_login()

def check_authentication():
    """Check Zerodha authentication status"""
    now = datetime.now()
    if (st.session_state.last_auth_check is None or 
        (now - st.session_state.last_auth_check).seconds > 30):
        
        zerodha_status = api_client.check_zerodha_status()
        
        if zerodha_status and zerodha_status.get('success'):
            st.session_state.zerodha_authenticated = True
            st.session_state.zerodha_profile = zerodha_status.get('profile_name', 'Connected')
        else:
            st.session_state.zerodha_authenticated = False
            st.session_state.zerodha_profile = None
        
        st.session_state.last_auth_check = now

def show_profile_status():
    """Show connection status"""
    if st.session_state.zerodha_authenticated:
        st.markdown(f"""
        <div class="profile-connected">
            ✅ <strong>Zerodha Connected</strong> - {st.session_state.zerodha_profile}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="profile-disconnected">
            🔒 <strong>Zerodha Not Connected</strong> - Please login below
        </div>
        """, unsafe_allow_html=True)

def show_zerodha_login():
    """Zerodha login interface"""
    st.markdown("## 🔐 Connect to Zerodha")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Get login URL
        if st.button("🔗 Get Zerodha Login Link", use_container_width=True):
            with st.spinner("Getting login URL..."):
                url_response = api_client.get_zerodha_login_url()
                
                if url_response and url_response.get('success'):
                    login_url = url_response['data']['login_url']
                    
                    st.markdown("""
                    <div class="success-box">
                        <strong>✅ Login URL Generated</strong><br>
                        Click the link below to login to Zerodha
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.code(login_url)
                    st.markdown(f"[🔗 **Click here to login to Zerodha**]({login_url})")
                    
                    st.markdown("""
                    <div class="info-box">
                        <strong>Next Steps:</strong><br>
                        1. Click the link above<br>
                        2. Login to your Zerodha account<br>
                        3. Copy the 'request_token' from the URL<br>
                        4. Paste it below
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-box">
                        ❌ <strong>Failed to get login URL</strong><br>
                        Please check your API configuration
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Token exchange
        request_token = st.text_input(
            "🎫 Enter Request Token",
            placeholder="Paste the request_token from Zerodha redirect URL"
        )
        
        if st.button("✅ Connect Zerodha", use_container_width=True, disabled=not request_token):
            if request_token:
                with st.spinner("Connecting to Zerodha..."):
                    token_response = api_client.exchange_token(request_token)
                    
                    if token_response and token_response.get('success'):
                        profile_name = token_response['data']['profile_name']
                        
                        st.markdown(f"""
                        <div class="success-box">
                            🎉 <strong>Successfully Connected!</strong><br>
                            Welcome, {profile_name}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.zerodha_authenticated = True
                        st.session_state.zerodha_profile = profile_name
                        
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.markdown("""
                        <div class="error-box">
                            ❌ <strong>Connection Failed</strong><br>
                            Please check your request token and try again
                        </div>
                        """, unsafe_allow_html=True)

def show_main_dashboard():
    """Main dashboard with tabs"""
    tab1, tab2, tab3 = st.tabs(["📊 Portfolio", "📋 Orders", "🔄 System"])
    
    with tab1:
        show_portfolio_tab()
    
    with tab2:
        show_orders_tab()
    
    with tab3:
        show_system_tab()

def show_portfolio_tab():
    """Portfolio overview with live data"""
    st.markdown("### 📊 Portfolio Overview")
    
    with st.spinner("Loading live portfolio data..."):
        # Try live portfolio first
        live_portfolio = api_client.get_live_portfolio()
        
        if live_portfolio and live_portfolio.get('success'):
            show_live_portfolio(live_portfolio.get('data', {}))
        else:
            # Fallback to system portfolio
            portfolio_response = api_client.get_portfolio_status()
            if portfolio_response and portfolio_response.get('success'):
                show_system_portfolio(portfolio_response.get('data', {}))
            else:
                st.markdown("""
                <div class="warning-box">
                    📭 <strong>No Portfolio Data</strong><br>
                    Unable to fetch portfolio data from Zerodha.
                </div>
                """, unsafe_allow_html=True)

def show_live_portfolio(portfolio_data):
    """Show live portfolio from Zerodha"""
    if not portfolio_data or not portfolio_data.get('holdings'):
        st.markdown("""
        <div class="info-box">
            📭 <strong>Empty Portfolio</strong><br>
            No holdings found in your Zerodha account.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_value = portfolio_data.get('current_value', 0)
        st.metric("💰 Current Value", f"₹{current_value:,.0f}")
    
    with col2:
        total_invested = portfolio_data.get('total_invested', 0)
        st.metric("📥 Invested", f"₹{total_invested:,.0f}")
    
    with col3:
        total_returns = portfolio_data.get('total_returns', 0)
        returns_pct = portfolio_data.get('returns_percentage', 0)
        st.metric("📈 Returns", f"₹{total_returns:,.0f}", delta=f"{returns_pct:+.2f}%")
    
    with col4:
        stock_count = len(portfolio_data.get('holdings', []))
        st.metric("📊 Stocks", f"{stock_count}")
    
    # Live holdings
    holdings = portfolio_data.get('holdings', [])
    
    if holdings:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📋 Live Holdings (LTP Prices)")
            show_live_holdings_table(holdings)
            
            st.markdown("""
            <div class="success-box" style="margin-top: 1rem; padding: 0.5rem;">
                📡 <strong>Live Data from Zerodha</strong> - Real-time LTP prices
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 🥧 Live Allocation")
            show_live_allocation_chart(holdings)

def show_live_holdings_table(holdings):
    """Display live holdings with LTP"""
    holdings_data = []
    
    for holding in holdings:
        symbol = holding.get('symbol', 'Unknown')
        quantity = holding.get('quantity', 0)
        avg_price = holding.get('avg_price', 0)
        ltp = holding.get('current_price', holding.get('last_price', 0))
        current_value = holding.get('current_value', 0)
        pnl = holding.get('pnl', 0)
        pnl_percent = holding.get('pnl_percent', 0)
        day_change = holding.get('day_change', 0)
        day_change_percent = holding.get('day_change_percentage', 0)
        
        holdings_data.append({
            'Stock': symbol,
            'Qty': f"{quantity:,}",
            'Avg Price': f"₹{avg_price:.2f}",
            'LTP': f"₹{ltp:.2f}",
            'Day Change': f"₹{day_change:+.2f} ({day_change_percent:+.2f}%)",
            'Value': f"₹{current_value:,.0f}",
            'P&L': f"₹{pnl:,.0f}",
            'P&L %': f"{pnl_percent:+.2f}%"
        })
    
    if holdings_data:
        df = pd.DataFrame(holdings_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

def show_live_allocation_chart(holdings):
    """Display allocation chart"""
    symbols = [h.get('symbol', 'Unknown') for h in holdings]
    values = [h.get('current_value', 0) for h in holdings]
    
    if values and sum(values) > 0:
        fig = px.pie(
            values=values,
            names=symbols,
            title="Live Portfolio Allocation"
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            showlegend=False
        )
        
        fig.update_layout(height=400, margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)

def show_system_portfolio(portfolio_data):
    """Fallback system portfolio"""
    if portfolio_data.get('status') == 'empty':
        st.markdown("""
        <div class="info-box">
            📭 <strong>Empty Portfolio</strong><br>
            Start investing to see your portfolio here.
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>Using System Data</strong><br>
        Live Zerodha data unavailable. Showing cached portfolio.
    </div>
    """, unsafe_allow_html=True)
    
    # System portfolio metrics
    summary = portfolio_data.get('portfolio_summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_value = summary.get('current_value', 0)
        st.metric("💰 Current Value", f"₹{current_value:,.0f}")
    
    with col2:
        total_investment = summary.get('total_investment', 0)
        st.metric("📥 Invested", f"₹{total_investment:,.0f}")
    
    with col3:
        total_returns = summary.get('total_returns', 0)
        returns_pct = summary.get('returns_percentage', 0)
        st.metric("📈 Returns", f"₹{total_returns:,.0f}", delta=f"{returns_pct:+.2f}%")
    
    with col4:
        stock_count = summary.get('stock_count', 0)
        st.metric("📊 Stocks", f"{stock_count}")

def show_orders_tab():
    """Orders history"""
    st.markdown("### 📋 Order History")
    
    with st.spinner("Loading orders..."):
        orders_response = api_client.get_system_orders()
    
    if not orders_response or not orders_response.get('success'):
        st.markdown("""
        <div class="error-box">
            ❌ <strong>Unable to load orders</strong><br>
            Please check your connection.
        </div>
        """, unsafe_allow_html=True)
        return
    
    orders_data = orders_response.get('data', {})
    orders = orders_data.get('orders', [])
    
    if not orders:
        st.markdown("""
        <div class="info-box">
            📭 <strong>No Orders Found</strong><br>
            No trading orders have been placed yet.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Order summary
    total_orders = len(orders)
    buy_orders = len([o for o in orders if o.get('action') == 'BUY'])
    total_value = sum(o.get('value', 0) for o in orders if o.get('action') == 'BUY')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📝 Total Orders", f"{total_orders:,}")
    with col2:
        st.metric("📈 Buy Orders", f"{buy_orders:,}")
    with col3:
        st.metric("💰 Investment", f"₹{total_value:,.0f}")
    
    # Orders table
    st.markdown("#### 📋 Recent Orders")
    
    df = pd.DataFrame(orders)
    
    if not df.empty:
        # Format data
        if 'execution_time' in df.columns:
            df['Date'] = pd.to_datetime(df['execution_time']).dt.strftime('%d/%m/%Y')
            df['Time'] = pd.to_datetime(df['execution_time']).dt.strftime('%H:%M')
        
        # Display data
        display_data = []
        for _, row in df.iterrows():
            display_data.append({
                'Date': row.get('Date', 'Unknown'),
                'Stock': row.get('symbol', 'Unknown'),
                'Action': row.get('action', 'Unknown'),
                'Shares': f"{row.get('shares', 0):,}",
                'Price': f"₹{row.get('price', 0):.2f}",
                'Value': f"₹{row.get('value', 0):,.0f}"
            })
        
        # Show recent orders
        recent_orders = display_data[-20:] if len(display_data) > 20 else display_data
        df_display = pd.DataFrame(recent_orders)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

def show_system_tab():
    """System status and controls"""
    st.markdown("### 🔄 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📡 Connection Status")
        
        if st.session_state.zerodha_authenticated:
            st.markdown(f"""
            <div class="success-box">
                ✅ <strong>Zerodha Connected</strong><br>
                Profile: {st.session_state.zerodha_profile}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-box">
                🔒 <strong>Zerodha Disconnected</strong><br>
                Please reconnect to access data
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="info-box">
            ℹ️ <strong>System Status</strong><br>
            Last updated: {datetime.now().strftime('%H:%M:%S')}<br>
            Date: {datetime.now().strftime('%d/%m/%Y')}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🔧 Quick Actions")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            with st.spinner("Refreshing..."):
                st.session_state.last_auth_check = None
                check_authentication()
                st.success("✅ Data refreshed!")
                time.sleep(1)
                st.rerun()
        
        if st.button("🔌 Reconnect Zerodha", use_container_width=True):
            st.session_state.zerodha_authenticated = False
            st.session_state.zerodha_profile = None
            st.session_state.last_auth_check = None
            st.rerun()
        
        if st.button("🧪 Test Connection", use_container_width=True):
            with st.spinner("Testing..."):
                status = api_client.check_zerodha_status()
                if status and status.get('success'):
                    st.markdown("""
                    <div class="success-box">
                        ✅ <strong>Connection Test Passed</strong><br>
                        All systems operational
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="error-box">
                        ❌ <strong>Connection Test Failed</strong><br>
                        Please check your connection
                    </div>
                    """, unsafe_allow_html=True)
                
                time.sleep(2)
                st.rerun()

if __name__ == "__main__":
    main()