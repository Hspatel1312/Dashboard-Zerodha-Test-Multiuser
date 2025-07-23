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

# Custom CSS for clean styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
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
    
    .investment-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
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
        """Get CSV stocks (without live prices)"""
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

# Initialize API client
api_client = SimpleAPIClient(API_BASE_URL)

def main():
    st.markdown('<h1 class="main-header">📈 Investment System Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        
        page = st.selectbox(
            "Select Page",
            [
                "🏠 System Status",
                "💰 Initial Investment",
                "📊 Portfolio Overview", 
                "⚖️ Rebalancing",
                "📋 Order History",
                "📄 CSV Stocks",
                "⚙️ System Info"
            ]
        )
        
        st.markdown("---")
        
        # Manual refresh
        if st.button("🔄 Refresh Data"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    # Route to pages
    if page == "🏠 System Status":
        show_system_status()
    elif page == "💰 Initial Investment":
        show_initial_investment()
    elif page == "📊 Portfolio Overview":
        show_portfolio_overview()
    elif page == "⚖️ Rebalancing":
        show_rebalancing()
    elif page == "📋 Order History":
        show_order_history()
    elif page == "📄 CSV Stocks":
        show_csv_stocks()
    elif page == "⚙️ System Info":
        show_system_info()

def show_system_status():
    """System status dashboard"""
    st.header("🏠 System Status Dashboard")
    
    # Backend Connection Status
    st.subheader("🔌 Backend Connection")
    
    with st.spinner("Checking backend connection..."):
        backend_status = api_client.check_backend_health()
    
    if backend_status['connected']:
        st.markdown('<div class="status-card success-status">✅ <strong>Backend Connected</strong><br>API is responding normally</div>', unsafe_allow_html=True)
        
        health_data = backend_status.get('data', {})
        init_status = health_data.get('initialization', {})
        
        # Show initialization status
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Service Status:**")
            st.write(f"• Investment Service: {'✅' if init_status.get('investment_service_created', False) else '❌'}")
            st.write(f"• Auth Service: {'✅' if init_status.get('auth_created', False) else '❌'}")
            st.write(f"• Config Loaded: {'✅' if init_status.get('config_loaded', False) else '❌'}")
        
        with col2:
            zerodha_conn = health_data.get('zerodha_connection', {})
            st.write("**Zerodha Connection:**")
            st.write(f"• Available: {'✅' if zerodha_conn.get('available', False) else '❌'}")
            st.write(f"• Authenticated: {'✅' if zerodha_conn.get('authenticated', False) else '❌'}")
            st.write(f"• Can Fetch Data: {'✅' if zerodha_conn.get('can_fetch_data', False) else '❌'}")
    else:
        st.markdown(f'<div class="status-card error-status">❌ <strong>Backend Disconnected</strong><br>Error: {backend_status["error"]}</div>', unsafe_allow_html=True)
    
    # Zerodha Live Connection Test
    st.subheader("📈 Zerodha Live Data Test")
    
    if st.button("🧪 Test Nifty Price Fetch"):
        with st.spinner("Testing Zerodha connection..."):
            zerodha_test = api_client.test_zerodha_connection()
        
        if zerodha_test.get('success', False):
            st.markdown('<div class="status-card success-status">✅ <strong>Zerodha Live Data Working</strong></div>', unsafe_allow_html=True)
            
            # Show live prices
            if 'nifty_price' in zerodha_test:
                st.metric("📈 Nifty 50", f"{zerodha_test['nifty_price']:,.2f}")
            elif 'alternative_data' in zerodha_test:
                st.write("**Alternative Stock Prices:**")
                for symbol, data in zerodha_test['alternative_data'].items():
                    clean_symbol = symbol.replace('NSE:', '')
                    st.write(f"• {clean_symbol}: ₹{data['last_price']:,.2f}")
            
            profile_name = zerodha_test.get('profile_name', 'Unknown')
            st.info(f"Connected as: {profile_name}")
        else:
            error_msg = zerodha_test.get('error', 'Unknown error')
            st.markdown(f'<div class="status-card error-status">❌ <strong>Zerodha Connection Failed</strong><br>Error: {error_msg}</div>', unsafe_allow_html=True)

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

def show_rebalancing():
    """Rebalancing interface"""
    st.header("⚖️ Portfolio Rebalancing")
    
    # Check if we have a portfolio first
    portfolio_status = api_client.get_portfolio_status()
    if not portfolio_status or not portfolio_status.get('success'):
        st.error("❌ Cannot load portfolio status for rebalancing")
        return
    
    if portfolio_status['data']['status'] == 'empty':
        st.info("📭 No portfolio found. Please complete initial investment first.")
        if st.button("➡️ Go to Initial Investment"):
            st.switch_page("💰 Initial Investment")
        return
    
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
            st.markdown('<div class="status-card warning-status">⚠️ <strong>Rebalancing Needed</strong><br>Portfolio needs adjustment</div>', unsafe_allow_html=True)
            st.write(f"**Reason**: {rebal_data['reason']}")
            
            if rebal_data.get('new_stocks'):
                st.write(f"**New stocks to add**: {', '.join(rebal_data['new_stocks'][:5])}")
            if rebal_data.get('removed_stocks'):
                st.write(f"**Stocks to remove**: {', '.join(rebal_data['removed_stocks'][:5])}")
        else:
            st.markdown('<div class="status-card success-status">✅ <strong>Portfolio Balanced</strong><br>No rebalancing needed</div>', unsafe_allow_html=True)
            st.write(f"**Reason**: {rebal_data['reason']}")
    
    with col2:
        st.subheader("🔄 Rebalancing Options")
        
        if rebal_data['rebalancing_needed']:
            st.info("Rebalancing functionality coming soon!")
            st.write("**Future Features:**")
            st.write("• Calculate new allocation")
            st.write("• Generate buy/sell orders") 
            st.write("• Execute rebalancing")
        else:
            st.success("No action needed")
    
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

def show_portfolio_overview():
    """Portfolio overview built from orders"""
    st.header("📊 Portfolio Overview")
    
    with st.spinner("Loading portfolio data..."):
        portfolio_result = api_client.get_portfolio_status()
    
    if not portfolio_result or not portfolio_result.get('success'):
        st.error(f"❌ Cannot load portfolio: {portfolio_result.get('error', 'Unknown error') if portfolio_result else 'No response'}")
        return
    
    portfolio_data = portfolio_result['data']
    
    if portfolio_data['status'] == 'empty':
        st.info("📭 No portfolio found. Please complete initial investment first.")
        if st.button("➡️ Go to Initial Investment"):
            st.switch_page("💰 Initial Investment")
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
            st.switch_page("💰 Initial Investment")
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
        st.metric("🔖 CSV Hash", csv_hash)
    
    # CSV Source Info
    st.info(f"**CSV Source:** {csv_info.get('source_url', 'Unknown')}")
    
    # Stocks Table (without live prices)
    if stocks:
        st.subheader("📋 Stock List")
        
        # Create simplified display without live prices
        stocks_df = pd.DataFrame(stocks)
        
        # Basic stock info only
        display_columns = ['symbol']
        
        # Add any additional fields from CSV
        for col in ['momentum', 'volatility', 'score']:
            if col in stocks_df.columns:
                display_columns.append(col)
                stocks_df[f'{col}_fmt'] = stocks_df[col].apply(lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else str(x))
                display_columns[-1] = f'{col}_fmt'
        
        # Rename columns for display
        column_mapping = {
            'symbol': 'Stock Symbol',
            'momentum_fmt': 'Momentum',
            'volatility_fmt': 'Volatility', 
            'score_fmt': 'Score'
        }
        
        display_df = stocks_df[display_columns].rename(columns=column_mapping)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Simple stats
        st.subheader("📊 CSV Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Stock Count by Sector:**")
            if 'sector' in stocks_df.columns:
                sector_counts = stocks_df['sector'].value_counts()
                for sector, count in sector_counts.head(5).items():
                    st.write(f"• {sector}: {count}")
            else:
                st.write("• Sector information not available")
        
        with col2:
            st.write("**Score Distribution:**")
            if 'score' in stocks_df.columns:
                high_score = (stocks_df['score'] >= stocks_df['score'].quantile(0.75)).sum()
                medium_score = ((stocks_df['score'] >= stocks_df['score'].quantile(0.25)) & 
                              (stocks_df['score'] < stocks_df['score'].quantile(0.75))).sum()
                low_score = (stocks_df['score'] < stocks_df['score'].quantile(0.25)).sum()
                
                st.write(f"• High Score (75%+): {high_score}")
                st.write(f"• Medium Score (25-75%): {medium_score}")
                st.write(f"• Low Score (<25%): {low_score}")
            else:
                st.write("• Score information not available")

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
    
    # Create status summary
    checks = [
        ("Backend API", backend_status.get('connected', False)),
        ("Zerodha Connection", zerodha_test.get('success', False)),
        ("CSV Data", csv_result.get('success', False)),
        ("Order System", orders_result.get('success', False)),
        ("Portfolio Service", portfolio_result.get('success', False))
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
    
    # Available Endpoints
    st.subheader("🌐 Available API Endpoints")
    
    endpoints = [
        "/health - System health check",
        "/api/test-nifty - Test Zerodha with Nifty price",
        "/api/investment/requirements - Get investment requirements",
        "/api/investment/calculate-plan - Calculate investment plan",
        "/api/investment/execute-initial - Execute initial investment",
        "/api/investment/rebalancing-check - Check rebalancing status",
        "/api/investment/csv-stocks - Get CSV stocks",
        "/api/investment/system-orders - Get order history", 
        "/api/investment/portfolio-status - Get portfolio status"
    ]
    
    for endpoint in endpoints:
        st.write(f"• {endpoint}")
    
    # System Configuration
    st.subheader("⚙️ Configuration")
    
    config_info = {
        "API Base URL": API_BASE_URL,
        "Frontend Framework": "Streamlit",
        "Last Refresh": st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S'),
        "Session Started": "Active"
    }
    
    for key, value in config_info.items():
        st.write(f"**{key}:** {value}")

if __name__ == "__main__":
    main()