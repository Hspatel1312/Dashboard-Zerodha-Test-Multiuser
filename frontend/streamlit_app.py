# frontend/streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import requests
import json
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Investment System Dashboard",
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

class InvestmentAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def get_investment_requirements(self) -> Dict:
        """Get investment requirements from your investment service"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/requirements", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    error_text = response.text
                st.error(f"API Error {response.status_code}: {error_text}")
                return None
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return None
    
    def calculate_investment_plan(self, investment_amount: float) -> Dict:
        """Calculate investment plan using your investment calculator"""
        try:
            data = {"investment_amount": investment_amount}
            response = requests.post(
                f"{self.base_url}/api/investment/calculate-plan",
                json=data,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    error_text = response.text
                st.error(f"API Error {response.status_code}: {error_text}")
                return None
        except Exception as e:
            st.error(f"Error calculating plan: {str(e)}")
            return None
    
    def execute_initial_investment(self, investment_amount: float) -> Dict:
        """Execute initial investment using your investment service"""
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
                error_text = ""
                try:
                    error_data = response.json()
                    error_text = error_data.get('detail', response.text)
                except:
                    error_text = response.text
                st.error(f"API Error {response.status_code}: {error_text}")
                return None
        except Exception as e:
            st.error(f"Error executing investment: {str(e)}")
            return None
    
    def check_rebalancing_needed(self) -> Dict:
        """Check if rebalancing is needed using your rebalancing logic"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/rebalancing-check", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error checking rebalancing: {str(e)}")
            return None
    
    def calculate_rebalancing_plan(self, additional_investment: float = 0) -> Dict:
        """Calculate rebalancing plan"""
        try:
            data = {"additional_investment": additional_investment}
            response = requests.post(
                f"{self.base_url}/api/investment/calculate-rebalancing",
                json=data,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error calculating rebalancing: {str(e)}")
            return None
    
    def execute_rebalancing(self, additional_investment: float = 0) -> Dict:
        """Execute rebalancing plan"""
        try:
            data = {"additional_investment": additional_investment}
            response = requests.post(
                f"{self.base_url}/api/investment/execute-rebalancing",
                json=data,
                timeout=60
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error executing rebalancing: {str(e)}")
            return None
    
    def get_portfolio_status(self) -> Dict:
        """Get system portfolio status (from your portfolio construction service)"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/portfolio-status", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error getting portfolio status: {str(e)}")
            return None
    
    def get_csv_stocks(self) -> Dict:
        """Get current CSV stocks with live prices"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/csv-stocks", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error getting CSV stocks: {str(e)}")
            return None
    
    def get_system_orders(self) -> Dict:
        """Get all system orders history"""
        try:
            response = requests.get(f"{self.base_url}/api/investment/system-orders", timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error getting system orders: {str(e)}")
            return None

# Initialize API client
api_client = InvestmentAPIClient(API_BASE_URL)

def main():
    st.title("📈 Investment System Dashboard")
    st.markdown("*Sophisticated portfolio construction and rebalancing system*")
    
    # Check backend connection
    backend_connected = False
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            backend_connected = True
            health_data = response.json()
            # Check if investment service is available
            if not health_data.get('services', {}).get('investment_service', False):
                st.error("❌ Investment service not initialized in backend. Please check backend logs.")
                with st.expander("Health Check Details"):
                    st.json(health_data)
                return
        else:
            st.error(f"❌ Backend returned status {response.status_code}. Please check backend.")
            return
    except Exception as e:
        st.error(f"❌ Cannot connect to backend: {str(e)}")
        st.info("Please ensure the backend is running:")
        st.code("cd backend && python -m uvicorn app.main:app --reload")
        return
    
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
        st.subheader("📊 Quick Status")
        
        # Quick status check
        portfolio_status = api_client.get_portfolio_status()
        if portfolio_status and portfolio_status.get('success'):
            data = portfolio_status['data']
            if data['status'] == 'active':
                st.success("✅ Portfolio Active")
                st.metric("💰 Total Value", f"₹{data['portfolio_summary']['current_value']:,.0f}")
                st.metric("📈 Returns", f"₹{data['portfolio_summary']['total_returns']:,.0f}")
            else:
                st.info("📭 No Portfolio Yet")
        else:
            st.warning("⚠️ Status Unknown")
        
        # Manual refresh
        if st.button("🔄 Refresh Data"):
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
            st.markdown('<div class="error-alert">❌ <strong>Portfolio Status Unknown</strong><br>Please check system</div>', unsafe_allow_html=True)
    
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
            st.markdown('<div class="warning-alert">⚠️ <strong>Rebalancing Status Unknown</strong></div>', unsafe_allow_html=True)
    
    with col3:
        if csv_stocks and csv_stocks.get('success'):
            data = csv_stocks['data']
            st.markdown('<div class="success-alert">✅ <strong>CSV Data Connected</strong><br>Live prices available</div>', unsafe_allow_html=True)
            st.metric("📊 CSV Stocks", f"{data['total_stocks']}")
            st.metric("💰 Price Success", f"{data['price_data_status']['success_rate']:.1f}%")
            st.caption(f"Source: {data['price_data_status']['market_data_source']}")
        else:
            st.markdown('<div class="error-alert">❌ <strong>CSV Data Issues</strong><br>Cannot fetch stocks</div>', unsafe_allow_html=True)
    
    # Current CSV stocks table
    if csv_stocks and csv_stocks.get('success'):
        st.subheader("📊 Current CSV Stocks (Live Prices)")
        
        stocks_data = csv_stocks['data']['stocks']
        if stocks_data:
            df = pd.DataFrame(stocks_data)
            
            # Format for display
            df['price_fmt'] = df['price'].apply(lambda x: f"₹{x:,.2f}")
            df['score'] = df.get('score', 0)
            
            display_df = df[['symbol', 'price_fmt', 'score']].rename(columns={
                'symbol': 'Stock Symbol',
                'price_fmt': 'Current Price',
                'score': 'Momentum Score'
            })
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # CSV info
            csv_info = csv_stocks['data']['csv_info']
            st.caption(f"CSV fetched: {csv_info['fetch_time'][:19]} | Hash: {csv_info['csv_hash']}")

def show_initial_investment():
    """Initial investment interface using your investment service"""
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
        st.error("❌ Cannot get investment requirements. Please check backend connection.")
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
            st.error("❌ Failed to calculate investment plan")
    
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
                    st.error("❌ Failed to execute investment")

def show_rebalancing():
    """Rebalancing interface using your rebalancing service"""
    st.header("⚖️ Portfolio Rebalancing")
    
    # Check rebalancing status
    with st.spinner("Checking rebalancing requirements..."):
        rebalancing_check = api_client.check_rebalancing_needed()
    
    if not rebalancing_check or not rebalancing_check.get('success'):
        st.error("❌ Cannot check rebalancing status")
        return
    
    rebalance_data = rebalancing_check['data']
    
    # Rebalancing status
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if rebalance_data['rebalancing_needed']:
            st.markdown('<div class="warning-alert">⚠️ <strong>Rebalancing Needed</strong></div>', unsafe_allow_html=True)
            st.write(f"**Reason**: {rebalance_data['reason']}")
            
            if rebalance_data.get('new_stocks'):
                st.write(f"**New stocks to add**: {', '.join(rebalance_data['new_stocks'])}")
            
            if rebalance_data.get('removed_stocks'):
                st.write(f"**Stocks to remove**: {', '.join(rebalance_data['removed_stocks'])}")
            
        else:
            st.markdown('<div class="success-alert">✅ <strong>Portfolio is balanced</strong></div>', unsafe_allow_html=True)
            st.write(f"**Status**: {rebalance_data['reason']}")
            
            if not rebalance_data.get('is_first_time', False):
                st.info("You can still add additional investment if desired.")
    
    with col2:
        st.subheader("💰 Additional Investment")
        additional_investment = st.number_input(
            "Additional Amount (₹)",
            min_value=0,
            value=0,
            step=10000,
            help="Optional additional investment during rebalancing"
        )
    
    # Calculate rebalancing plan
    if rebalance_data['rebalancing_needed'] or additional_investment > 0:
        st.subheader("🧮 Rebalancing Plan")
        
        if st.button("📊 Calculate Rebalancing Plan", type="primary"):
            with st.spinner("Calculating rebalancing plan..."):
                rebalancing_plan = api_client.calculate_rebalancing_plan(additional_investment)
            
            if rebalancing_plan and rebalancing_plan.get('success'):
                st.session_state.rebalancing_plan = rebalancing_plan['data']
                st.success("✅ Rebalancing plan calculated!")
            else:
                st.error("❌ Failed to calculate rebalancing plan")
    
    # Show rebalancing plan
    if 'rebalancing_plan' in st.session_state:
        plan = st.session_state.rebalancing_plan
        
        # Plan summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Current Value", f"₹{plan['current_value']:,.0f}")
        
        with col2:
            st.metric("➕ Additional", f"₹{plan['additional_investment']:,.0f}")
        
        with col3:
            st.metric("🎯 Target Value", f"₹{plan['target_value']:,.0f}")
        
        with col4:
            st.metric("📊 Status", plan['status'])
        
        # Show allocation plan if available
        if 'allocation_plan' in plan:
            allocation = plan['allocation_plan']
            
            st.subheader("📋 Proposed Allocation")
            
            if allocation.get('allocations'):
                allocations_df = pd.DataFrame(allocation['allocations'])
                allocations_df['price_fmt'] = allocations_df['price'].apply(lambda x: f"₹{x:.2f}")
                allocations_df['value_fmt'] = allocations_df['value'].apply(lambda x: f"₹{x:,.0f}")
                allocations_df['allocation_fmt'] = allocations_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
                
                display_df = allocations_df[['symbol', 'shares', 'price_fmt', 'value_fmt', 'allocation_fmt']].rename(columns={
                    'symbol': 'Stock',
                    'shares': 'Target Shares',
                    'price_fmt': 'Current Price',
                    'value_fmt': 'Target Value',
                    'allocation_fmt': 'Allocation %'
                })
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Execute rebalancing
        if plan['status'] == 'READY_FOR_EXECUTION':
            st.subheader("🚀 Execute Rebalancing")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info("💡 This will update system orders but NOT place live trades")
            
            with col2:
                if st.button("🚀 Execute Rebalancing", type="primary", use_container_width=True):
                    with st.spinner("Executing rebalancing..."):
                        result = api_client.execute_rebalancing(additional_investment)
                    
                    if result and result.get('success'):
                        st.success("✅ Rebalancing executed successfully!")
                        del st.session_state.rebalancing_plan
                        st.rerun()
                    else:
                        st.error("❌ Failed to execute rebalancing")

def show_order_history():
    """Order history from your system orders"""
    st.header("📋 System Order History")
    
    with st.spinner("Loading order history..."):
        orders_result = api_client.get_system_orders()
    
    if not orders_result or not orders_result.get('success'):
        st.error("❌ Cannot load order history")
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
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        session_types = df['session_type'].unique()
        selected_sessions = st.multiselect("Session Type", session_types, default=session_types)
    
    with col2:
        actions = df['action'].unique()
        selected_actions = st.multiselect("Action", actions, default=actions)
    
    with col3:
        symbols = df['symbol'].unique()
        selected_symbols = st.multiselect("Stocks", symbols, default=symbols[:10] if len(symbols) > 10 else symbols)
    
    # Apply filters
    filtered_df = df[
        (df['session_type'].isin(selected_sessions)) &
        (df['action'].isin(selected_actions)) &
        (df['symbol'].isin(selected_symbols))
    ]
    
    # Display table
    display_df = filtered_df[['execution_time', 'symbol', 'action', 'shares', 'price_fmt', 'value_fmt', 'allocation_fmt', 'session_type']].rename(columns={
        'execution_time': 'Date/Time',
        'symbol': 'Stock',
        'action': 'Action',
        'shares': 'Shares',
        'price_fmt': 'Price',
        'value_fmt': 'Value',
        'allocation_fmt': 'Allocation %',
        'session_type': 'Session'
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Order timeline chart
    if len(filtered_df) > 0:
        st.subheader("📈 Order Timeline")
        
        # Group by date
        daily_orders = filtered_df.groupby(filtered_df['execution_time'].str[:10]).agg({
            'value': 'sum',
            'order_id': 'count'
        }).reset_index()
        daily_orders.columns = ['date', 'total_value', 'order_count']
        
        fig = px.bar(
            daily_orders,
            x='date',
            y='total_value',
            title='Daily Investment Value',
            hover_data=['order_count']
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Investment Value (₹)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_portfolio_status():
    """Portfolio status from your portfolio construction service"""
    st.header("📊 System Portfolio Status")
    
    with st.spinner("Loading portfolio status..."):
        portfolio_result = api_client.get_portfolio_status()
    
    if not portfolio_result or not portfolio_result.get('success'):
        st.error("❌ Cannot load portfolio status")
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
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    st.success("✅ Backend connected successfully!")
                    
                    with st.expander("Health Check Details"):
                        st.json(health_data)
                else:
                    st.error(f"❌ Backend responded with status {response.status_code}")
            except Exception as e:
                st.error(f"❌ Backend connection failed: {str(e)}")
    
    with col2:
        if st.button("🔄 Test Zerodha Connection"):
            try:
                response = requests.get(f"{API_BASE_URL}/api/test-auth", timeout=30)
                if response.status_code == 200:
                    auth_data = response.json()
                    if auth_data.get('success'):
                        st.success(f"✅ {auth_data.get('message')}")
                        if auth_data.get('profile_name'):
                            st.info(f"Profile: {auth_data.get('profile_name')}")
                    else:
                        st.error(f"❌ {auth_data.get('message')}")
                        if auth_data.get('error'):
                            st.error(f"Error: {auth_data.get('error')}")
                else:
                    st.error(f"❌ Auth test failed with status {response.status_code}")
            except Exception as e:
                st.error(f"❌ Auth test failed: {str(e)}")
    
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
            st.metric("❌ Excluded", data['excluded_symbols'])
        
        st.info(f"**CSV Source**: {csv_info['source_url']}")
        st.info(f"**Last Fetched**: {csv_info['fetch_time'][:19]}")
        st.info(f"**Data Source**: {price_status['market_data_source']}")
    else:
        st.error("❌ Cannot fetch CSV data status")
    
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
            st.info("All data will be refreshed on next page load")
            st.rerun()
    
    # System status summary
    st.subheader("📊 System Status Summary")
    
    status_data = {
        "Component": ["Backend API", "Zerodha Auth", "CSV Data", "Portfolio", "Order System"],
        "Status": ["🟢 Connected", "⚠️ Check Required", "🟢 Active", "📊 Check Portfolio", "🟢 Active"],
        "Last Check": [datetime.now().strftime('%H:%M:%S')] * 5
    }
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()