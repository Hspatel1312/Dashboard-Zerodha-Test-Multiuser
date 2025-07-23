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

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
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
    
    .info-alert {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'backend_status' not in st.session_state:
    st.session_state.backend_status = None

class InvestmentAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 30

    def check_backend_health(self) -> Dict:
        """Check backend health and initialization status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                return {
                    'connected': True,
                    'data': response.json(),
                    'error': None
                }
            else:
                return {
                    'connected': False,
                    'data': None,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'connected': False,
                'data': None,
                'error': str(e)
            }

    def test_zerodha_auth(self) -> Dict:
        """Test Zerodha authentication"""
        try:
            response = requests.get(f"{self.base_url}/api/test-auth", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'message': 'Authentication test failed'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to authentication service'
            }

    def get_investment_requirements(self) -> Dict:
        """Get investment requirements"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/requirements", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                error_text = response.text
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    pass
                return {
                    'success': False,
                    'error': f"API Error {response.status_code}: {error_text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection error: {str(e)}"
            }

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
                return {
                    'success': False,
                    'error': f"API Error {response.status_code}: {error_text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error calculating plan: {str(e)}"
            }

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
                return {
                    'success': False,
                    'error': f"API Error {response.status_code}: {error_text}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error executing investment: {str(e)}"
            }

    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/rebalancing-check", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error checking rebalancing: {str(e)}"
            }

    def get_portfolio_status(self) -> Dict:
        """Get system portfolio status"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/portfolio-status", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting portfolio status: {str(e)}"
            }

    def get_csv_stocks(self) -> Dict:
        """Get current CSV stocks with live prices"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/csv-stocks", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting CSV stocks: {str(e)}"
            }

    def get_system_orders(self) -> Dict:
        """Get all system orders history"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/system-orders", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting system orders: {str(e)}"
            }

# Initialize API client
api_client = InvestmentAPIClient(API_BASE_URL)

def check_backend_connection():
    """Check and display backend connection status"""
    health_check = api_client.check_backend_health()
    st.session_state.backend_status = health_check
    
    if not health_check['connected']:
        st.error(f"❌ Cannot connect to backend: {health_check['error']}")
        with st.expander("Troubleshooting"):
            st.write("**Backend Connection Issues:**")
            st.write("1. Ensure the backend is running:")
            st.code("cd backend && python -m uvicorn app.main:app --reload")
            st.write("2. Check if the API is accessible:")
            st.code(f"curl {API_BASE_URL}/health")
            st.write("3. Verify no firewall/port issues")
        return False
    
    health_data = health_check['data']
    
    # Check initialization status
    init_status = health_data.get('initialization', {})
    
    if not init_status.get('investment_service_created', False):
        st.error("❌ Investment service not initialized in backend")
        with st.expander("Backend Initialization Details"):
            st.json(init_status)
        return False
    
    return True

def show_connection_status():
    """Show detailed connection status in sidebar"""
    with st.sidebar:
        st.subheader("🔌 Connection Status")
        
        if st.session_state.backend_status and st.session_state.backend_status['connected']:
            st.success("✅ Backend Connected")
            
            health_data = st.session_state.backend_status['data']
            zerodha_status = health_data.get('zerodha_connection', {})
            
            if zerodha_status.get('authenticated', False):
                st.success("✅ Zerodha Connected")
            else:
                st.warning("⚠️ Zerodha Not Connected")
                if st.button("🔄 Test Zerodha Auth"):
                    with st.spinner("Testing Zerodha authentication..."):
                        auth_result = api_client.test_zerodha_auth()
                        if auth_result.get('success'):
                            st.success(f"✅ {auth_result.get('message')}")
                            if auth_result.get('profile_name'):
                                st.info(f"Profile: {auth_result.get('profile_name')}")
                        else:
                            st.error(f"❌ {auth_result.get('message')}")
        else:
            st.error("❌ Backend Disconnected")
        
        st.caption(f"Last checked: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

def main():
    st.markdown('<h1 class="main-header">📈 Investment System Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("*Sophisticated portfolio construction and rebalancing system*")
    
    # Check backend connection first
    backend_ok = check_backend_connection()
    
    if not backend_ok:
        st.stop()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        
        page = st.selectbox(
            "Select Page",
            [
                "🏠 System Overview",
                "💰 Initial Investment", 
                "⚖️ Rebalancing",
                "📋 Order History",
                "📊 Portfolio Status",
                "🔧 System Settings"
            ]
        )
        
        st.markdown("---")
        
        # Show connection status
        show_connection_status()
        
        st.markdown("---")
        
        # Manual refresh
        if st.button("🔄 Refresh Data"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    # Route to appropriate page
    if page == "🏠 System Overview":
        show_system_overview()
    elif page == "💰 Initial Investment":
        show_initial_investment()
    elif page == "⚖️ Rebalancing":
        show_rebalancing()
    elif page == "📋 Order History":
        show_order_history()
    elif page == "📊 Portfolio Status":
        show_portfolio_status()
    elif page == "🔧 System Settings":
        show_system_settings()

def show_system_overview():
    """System overview showing current state"""
    st.header("🏠 System Overview")
    
    # Get current system state
    with st.spinner("Loading system overview..."):
        portfolio_status = api_client.get_portfolio_status()
        rebalancing_check = api_client.check_rebalancing_needed()
        csv_stocks = api_client.get_csv_stocks()
    
    # System status cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if portfolio_status and portfolio_status.get('success'):
            data = portfolio_status['data']
            if data['status'] == 'active':
                st.markdown('<div class="success-alert">✅ <strong>Investment System Active</strong><br>Portfolio is operational</div>', unsafe_allow_html=True)
                
                # Portfolio metrics
                summary = data['portfolio_summary']
                st.metric("💰 Current Value", f"₹{summary['current_value']:,.0f}")
                st.metric("📈 Total Returns", f"₹{summary['total_returns']:,.0f}", f"{summary['returns_percentage']:.2f}%")
                st.metric("📊 Holdings", f"{summary['stock_count']} stocks")
            else:
                st.markdown('<div class="info-alert">📭 <strong>No Portfolio</strong><br>Ready for initial investment</div>', unsafe_allow_html=True)
                st.info("Click 'Initial Investment' to start")
        else:
            error_msg = portfolio_status.get('error', 'Unknown error') if portfolio_status else 'Failed to fetch'
            st.markdown('<div class="error-alert">❌ <strong>Portfolio Status Unknown</strong><br>Please check system</div>', unsafe_allow_html=True)
            st.caption(f"Error: {error_msg}")
    
    with col2:
        if rebalancing_check and rebalancing_check.get('success'):
            data = rebalancing_check['data']
            if data['rebalancing_needed']:
                st.markdown('<div class="warning-alert">⚠️ <strong>Rebalancing Needed</strong><br>CSV has been updated</div>', unsafe_allow_html=True)
                st.write(f"**Reason**: {data['reason']}")
                if data.get('new_stocks'):
                    st.write(f"**New stocks**: {', '.join(data['new_stocks'][:3])}...")
                if data.get('removed_stocks'):
                    st.write(f"**Removed stocks**: {', '.join(data['removed_stocks'][:3])}...")
            else:
                st.markdown('<div class="success-alert">✅ <strong>Portfolio Balanced</strong><br>No rebalancing needed</div>', unsafe_allow_html=True)
                st.write(f"**Reason**: {data['reason']}")
        else:
            error_msg = rebalancing_check.get('error', 'Unknown error') if rebalancing_check else 'Failed to fetch'
            st.markdown('<div class="warning-alert">⚠️ <strong>Rebalancing Status Unknown</strong></div>', unsafe_allow_html=True)
            st.caption(f"Error: {error_msg}")
    
    with col3:
        if csv_stocks and csv_stocks.get('success'):
            data = csv_stocks['data']
            st.markdown('<div class="success-alert">✅ <strong>CSV Data Connected</strong><br>Live prices available</div>', unsafe_allow_html=True)
            st.metric("📊 CSV Stocks", f"{data['total_stocks']}")
            st.metric("💰 Price Success", f"{data['price_data_status']['success_rate']:.1f}%")
            st.caption(f"Source: {data['price_data_status']['market_data_source']}")
        else:
            error_msg = csv_stocks.get('error', 'Unknown error') if csv_stocks else 'Failed to fetch'
            st.markdown('<div class="error-alert">❌ <strong>CSV Data Issues</strong><br>Cannot fetch stocks</div>', unsafe_allow_html=True)
            st.caption(f"Error: {error_msg}")
    
    # Current CSV stocks table
    if csv_stocks and csv_stocks.get('success'):
        st.subheader("📊 Current CSV Stocks (Live Prices)")
        
        stocks_data = csv_stocks['data']['stocks']
        if stocks_data:
            df = pd.DataFrame(stocks_data)
            
            # Format for display
            df['price_fmt'] = df['price'].apply(lambda x: f"₹{x:,.2f}")
            
            display_df = df[['symbol', 'price_fmt']].rename(columns={
                'symbol': 'Stock Symbol',
                'price_fmt': 'Current Price'
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # CSV info
            csv_info = csv_stocks['data']['csv_info']
            st.caption(f"CSV fetched: {csv_info['fetch_time'][:19]} | Hash: {csv_info['csv_hash']}")

def show_initial_investment():
    """Initial investment interface"""
    st.header("💰 Initial Investment Setup")
    
    # Check if already have portfolio
    portfolio_status = api_client.get_portfolio_status()
    if portfolio_status and portfolio_status.get('success'):
        data = portfolio_status['data']
        if data['status'] == 'active':
            st.warning("⚠️ You already have an active portfolio. Use the Rebalancing page to make changes.")
            
            if st.checkbox("Show current portfolio anyway"):
                show_portfolio_summary(data)
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
        - **Most Expensive Stock**: {min_investment_info['most_expensive_stock']} at ₹{min_investment_info['most_expensive_price']:,.2f}
        
        **Calculation Basis**: {min_investment_info['calculation_basis']}
        """)
        
        # Show stocks table
        if st.checkbox("Show all stocks", value=False):
            df = pd.DataFrame(stocks_data)
            df['price_fmt'] = df['price'].apply(lambda x: f"₹{x:,.2f}")
            
            display_df = df[['symbol', 'price_fmt']].rename(columns={
                'symbol': 'Stock Symbol',
                'price_fmt': 'Current Price'
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
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
        
        # Execute investment
        st.subheader("🚀 Execute Investment")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 This will create system orders but NOT place live trades on Zerodha")
        
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

def show_rebalancing():
    """Rebalancing interface"""
    st.header("⚖️ Portfolio Rebalancing")
    st.info("🚧 Rebalancing functionality will be implemented in the next version")

def show_order_history():
    """Order history from system orders"""
    st.header("📋 System Order History")
    
    with st.spinner("Loading order history..."):
        orders_result = api_client.get_system_orders()
    
    if not orders_result or not orders_result.get('success'):
        st.error(f"❌ Cannot load order history: {orders_result.get('error', 'Unknown error') if orders_result else 'No response'}")
        return
    
    orders_data = orders_result['data']
    orders = orders_data['orders']
    
    if not orders:
        st.info("📭 No orders found. Start with Initial Investment.")
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
    
    # Orders table
    st.subheader("📊 All Orders")
    
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

def show_portfolio_status():
    """Portfolio status from portfolio construction service"""
    st.header("📊 System Portfolio Status")
    
    with st.spinner("Loading portfolio status..."):
        portfolio_result = api_client.get_portfolio_status()
    
    if not portfolio_result or not portfolio_result.get('success'):
        st.error(f"❌ Cannot load portfolio status: {portfolio_result.get('error', 'Unknown error') if portfolio_result else 'No response'}")
        return
    
    portfolio_data = portfolio_result['data']
    
    if portfolio_data['status'] == 'empty':
        st.info("📭 No portfolio found. Please complete initial investment first.")
        st.markdown(portfolio_data['message'])
        return
    elif portfolio_data['status'] == 'error':
        st.error(f"❌ Portfolio error: {portfolio_data['error']}")
        return
    
    # Portfolio is active
    show_portfolio_summary(portfolio_data)

def show_portfolio_summary(portfolio_data):
    """Show detailed portfolio summary"""
    holdings = portfolio_data['holdings']
    summary = portfolio_data['portfolio_summary']
    
    # Portfolio metrics
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
    
    # Holdings table
    if holdings:
        st.subheader("📋 Current Holdings")
        
        # Convert holdings to DataFrame
        holdings_list = []
        for symbol, holding in holdings.items():
            holdings_list.append({
                'symbol': symbol,
                'shares': holding['shares'],
                'avg_price': holding['avg_price'],
                'current_price': holding['current_price'],
                'investment_value': holding['investment_value'],
                'current_value': holding['current_value'],
                'pnl': holding['pnl'],
                'pnl_percent': holding['pnl_percent']
            })
        
        df = pd.DataFrame(holdings_list)
        
        # Format for display
        df['avg_price_fmt'] = df['avg_price'].apply(lambda x: f"₹{x:.2f}")
        df['current_price_fmt'] = df['current_price'].apply(lambda x: f"₹{x:.2f}")
        df['investment_fmt'] = df['investment_value'].apply(lambda x: f"₹{x:,.0f}")
        df['current_fmt'] = df['current_value'].apply(lambda x: f"₹{x:,.0f}")
        df['pnl_fmt'] = df['pnl'].apply(lambda x: f"₹{x:,.0f}")
        df['allocation_percent'] = (df['current_value'] / df['current_value'].sum() * 100)
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
        
        # Portfolio analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🥧 Current Allocation")
            
            fig = px.pie(
                df,
                values='current_value',
                names='symbol',
                title='Portfolio Allocation by Value'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Performance Analysis")
            
            # Top performers
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

def show_system_settings():
    """System settings and configuration"""
    st.header("🔧 System Settings")
    
    # Backend connection test
    st.subheader("🔗 Backend Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Test Backend Connection"):
            with st.spinner("Testing backend connection..."):
                health_check = api_client.check_backend_health()
                if health_check['connected']:
                    st.success("✅ Backend connected successfully!")
                    
                    with st.expander("Health Check Details"):
                        st.json(health_check['data'])
                else:
                    st.error(f"❌ Backend connection failed: {health_check['error']}")
    
    with col2:
        if st.button("🔄 Test Zerodha Connection"):
            with st.spinner("Testing Zerodha authentication..."):
                auth_result = api_client.test_zerodha_auth()
                if auth_result.get('success'):
                    st.success(f"✅ {auth_result.get('message')}")
                    if auth_result.get('profile_name'):
                        st.info(f"Profile: {auth_result.get('profile_name')}")
                else:
                    st.error(f"❌ {auth_result.get('message')}")
                    if auth_result.get('error'):
                        st.error(f"Error: {auth_result.get('error')}")
    
    # CSV data status
    st.subheader("📊 CSV Data Status")
    
    csv_result = api_client.get_csv_stocks()
    if csv_result and csv_result.get('success'):
        data = csv_result['data']
        csv_info = data['csv_info']
        price_status = data['price_data_status']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Total Stocks", data['total_stocks'])
        
        with col2:
            st.metric("✅ Valid Prices", f"{price_status['success_rate']:.1f}%")
        
        with col3:
            st.metric("❌ Excluded", data.get('excluded_symbols', 0))
        
        st.info(f"**CSV Source**: {csv_info['source_url']}")
        st.info(f"**Last Fetched**: {csv_info['fetch_time'][:19]}")
        st.info(f"**Data Source**: {price_status['market_data_source']}")
    else:
        st.error(f"❌ Cannot fetch CSV data status: {csv_result.get('error', 'Unknown error') if csv_result else 'No response'}")
    
    # System configuration
    st.subheader("⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Allocation Settings:**")
        st.text("• Min Allocation: 4.0%")
        st.text("• Target Allocation: 5.0%") 
        st.text("• Max Allocation: 7.0%")
        st.text("• Equal weight strategy")
    
    with col2:
        st.write("**System Settings:**")
        st.text("• No live trading (simulation mode)")
        st.text("• Portfolio tracking via system orders")
        st.text("• Live price integration")
        st.text("• CSV-based stock selection")
    
    # Data management
    st.subheader("📁 Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Portfolio Data"):
            portfolio_result = api_client.get_portfolio_status()
            if portfolio_result and portfolio_result.get('success'):
                st.download_button(
                    "💾 Download Portfolio JSON",
                    data=json.dumps(portfolio_result['data'], indent=2),
                    file_name=f"portfolio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with col2:
        if st.button("📋 Export Order History"):
            orders_result = api_client.get_system_orders()
            if orders_result and orders_result.get('success'):
                st.download_button(
                    "💾 Download Orders JSON",
                    data=json.dumps(orders_result['data'], indent=2),
                    file_name=f"order_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with col3:
        if st.button("🔄 Refresh All Data"):
            st.session_state.last_refresh = datetime.now()
            st.success("✅ Data refreshed!")
            st.rerun()
    
    # System status summary
    st.subheader("📊 System Status Summary")
    
    # Get current status for each component
    backend_status = "🟢 Connected" if st.session_state.backend_status and st.session_state.backend_status['connected'] else "🔴 Disconnected"
    
    # Test other components
    zerodha_status = "⚠️ Check Required"
    csv_status = "🟢 Active" if csv_result and csv_result.get('success') else "🔴 Failed"
    portfolio_status_check = api_client.get_portfolio_status()
    portfolio_status = "🟢 Active" if portfolio_status_check and portfolio_status_check.get('success') else "🔴 Error"
    orders_status_check = api_client.get_system_orders()
    orders_status = "🟢 Active" if orders_status_check and orders_status_check.get('success') else "🔴 Error"
    
    status_data = {
        "Component": ["Backend API", "Zerodha Auth", "CSV Data", "Portfolio", "Order System"],
        "Status": [backend_status, zerodha_status, csv_status, portfolio_status, orders_status],
        "Last Check": [datetime.now().strftime('%H:%M:%S')] * 5
    }
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()