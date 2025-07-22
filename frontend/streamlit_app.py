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

st.set_page_config(
    page_title="Investment Portfolio Manager",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
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

# Initialize session state
if 'investment_plan' not in st.session_state:
    st.session_state.investment_plan = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'requirements'

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

def main():
    st.title("📈 Investment System Manager")
    
    # Show connection status at the top
    zerodha_connected = show_connection_status()
    
    if not zerodha_connected:
        st.markdown("---")
        st.error("⚠️ **Zerodha Connection Required**")
        st.write("To use this system, you need a working Zerodha connection. Please:")
        st.write("1. Check your Zerodha API credentials in the backend configuration")
        st.write("2. Ensure the backend server is running")
        st.write("3. Verify your internet connection")
        st.write("4. Check if markets are open (9:15 AM - 3:30 PM IST)")
        
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
        
        st.stop()
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Select Page",
            ["💰 Initial Investment", "⚖️ Rebalancing", "📊 Portfolio Status", "📋 Order History", "🔧 Settings"]
        )
        
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        
        # Try to get portfolio summary for quick stats
        try:
            response = requests.get(f"{API_BASE_URL}/api/portfolio/summary/1", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    st.metric("Portfolio Value", f"₹{data.get('current_value', 0):,.0f}")
                    st.metric("Total Returns", f"₹{data.get('total_returns', 0):,.0f}")
                    st.metric("Holdings", f"{data.get('total_holdings', 0)}")
                else:
                    st.info("Connect to view stats")
            else:
                st.info("Stats unavailable")
        except:
            st.info("Stats loading...")
    
    # Route to appropriate page
    if page == "💰 Initial Investment":
        show_initial_investment_page()
    elif page == "⚖️ Rebalancing":
        show_rebalancing_page()
    elif page == "📊 Portfolio Status":
        show_portfolio_status()
    elif page == "📋 Order History":
        show_order_history()
    elif page == "🔧 Settings":
        show_settings()

def show_initial_investment_page():
    """Initial Investment Flow"""
    st.header("💰 Initial Investment Setup")
    
    # Check investment requirements
    try:
        with st.spinner("Loading investment requirements..."):
            response = requests.get(f"{API_BASE_URL}/investment/requirements", timeout=30)
        
        if response.status_code == 200:
            requirements_data = response.json()
            if requirements_data.get('success'):
                requirements = requirements_data['data']
                
                # Display investment requirements
                st.subheader("📋 Investment Requirements")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    recommended = requirements['minimum_investment']['recommended_minimum']
                    st.metric(
                        "💡 Recommended Investment",
                        f"₹{recommended:,.0f}",
                        help="Recommended amount for optimal allocation across all stocks"
                    )
                
                with col2:
                    total_stocks = requirements['minimum_investment']['total_stocks']
                    st.metric(
                        "📊 Total Stocks",
                        f"{total_stocks}",
                        help="Number of stocks from CSV to invest in"
                    )
                
                # Show CSV stocks data
                st.subheader("📈 Current CSV Stocks (Live Prices)")
                
                stocks_df = pd.DataFrame(requirements['stocks_data']['stocks'])
                
                # Format the display
                display_df = pd.DataFrame({
                    'Stock Symbol': stocks_df['symbol'],
                    'Live Price': stocks_df['price'].apply(lambda x: f"₹{x:,.2f}"),
                    'Min Investment (4%)': (stocks_df['price'] * 25).apply(lambda x: f"₹{x:,.0f}"),
                    'Score': stocks_df.get('score', pd.Series([0]*len(stocks_df))).apply(lambda x: f"{x:.2f}")
                })
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Show data source info
                price_status = requirements['stocks_data']['price_data_status']
                if price_status.get('live_prices_used'):
                    st.success(f"✅ Using live prices from {price_status.get('market_data_source', 'Zerodha')} (Success rate: {price_status.get('success_rate', 0):.1f}%)")
                else:
                    st.error("❌ Live prices not available")
                
                # Investment amount input
                st.subheader("💰 Enter Investment Amount")
                
                min_investment = requirements['minimum_investment']['minimum_investment']
                recommended = requirements['minimum_investment']['recommended_minimum']
                
                investment_amount = st.number_input(
                    "Investment Amount (₹)",
                    min_value=float(min_investment),
                    value=float(recommended),
                    step=10000.0,
                    help=f"Minimum required: ₹{min_investment:,.0f}"
                )
                
                # Show status message
                if investment_amount < min_investment:
                    st.markdown('<div class="error-alert">❌ Amount below minimum required!</div>', unsafe_allow_html=True)
                elif investment_amount < recommended:
                    st.markdown('<div class="warning-alert">⚠️ Consider recommended amount for better allocation</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="success-alert">✅ Good investment amount</div>', unsafe_allow_html=True)
                
                # Calculate investment plan
                if st.button("🧮 Calculate Investment Plan", type="primary", use_container_width=True):
                    if investment_amount >= min_investment:
                        with st.spinner("Calculating optimal investment plan..."):
                            calculate_investment_plan(investment_amount)
                    else:
                        st.error(f"Investment amount must be at least ₹{min_investment:,.0f}")
                
                # Show investment plan if calculated
                if st.session_state.investment_plan:
                    show_investment_plan()
                    
            else:
                st.error(f"Failed to get investment requirements: {requirements_data.get('detail', 'Unknown error')}")
                return
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return
    except Exception as e:
        st.error(f"Error fetching requirements: {e}")
        st.write("This usually means:")
        st.write("- Backend server is not running")
        st.write("- Zerodha connection is not working")  
        st.write("- Network connectivity issues")
        return

def calculate_investment_plan(investment_amount):
    """Calculate and store investment plan"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/investment/calculate-plan",
            json={"investment_amount": investment_amount},
            timeout=30
        )
        
        if response.status_code == 200:
            plan_data = response.json()
            if plan_data.get('success'):
                st.session_state.investment_plan = plan_data['data']
                st.success("✅ Investment plan calculated successfully!")
                st.rerun()
            else:
                st.error(f"Calculation failed: {plan_data.get('detail', 'Unknown error')}")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Error calculating plan: {e}")

def show_investment_plan():
    """Display the calculated investment plan"""
    plan = st.session_state.investment_plan
    
    st.subheader("📋 Proposed Investment Plan")
    
    # Plan summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_investment = plan['summary']['total_investment_value']
        st.metric("💰 Total Investment", f"₹{total_investment:,.0f}")
    
    with col2:
        remaining_cash = plan['summary']['remaining_cash']
        st.metric("💵 Remaining Cash", f"₹{remaining_cash:,.0f}")
    
    with col3:
        utilization = plan['summary']['utilization_percent']
        st.metric("📊 Utilization", f"{utilization:.2f}%")
    
    with col4:
        total_orders = plan['summary']['total_orders']
        st.metric("📝 Buy Orders", f"{total_orders}")
    
    # Orders table
    st.subheader("📝 Proposed Orders")
    
    orders_df = pd.DataFrame(plan['orders'])
    
    # Format the orders for display
    orders_df['price_formatted'] = orders_df['price'].apply(lambda x: f"₹{x:.2f}")
    orders_df['value_formatted'] = orders_df['value'].apply(lambda x: f"₹{x:,.0f}")
    orders_df['allocation_formatted'] = orders_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
    
    display_orders = orders_df[['symbol', 'shares', 'price_formatted', 'value_formatted', 'allocation_formatted']].rename(columns={
        'symbol': 'Stock',
        'shares': 'Shares',
        'price_formatted': 'Live Price',
        'value_formatted': 'Investment',
        'allocation_formatted': 'Allocation'
    })
    
    st.dataframe(display_orders, use_container_width=True, hide_index=True)
    
    # Allocation visualization
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Allocation bar chart
        fig = px.bar(
            orders_df,
            x='symbol',
            y='allocation_percent',
            title='Allocation per Stock (%)',
            labels={'allocation_percent': 'Allocation %', 'symbol': 'Stock'},
            color='allocation_percent',
            color_continuous_scale='viridis'
        )
        fig.add_hline(y=4, line_dash="dash", line_color="red", annotation_text="Min 4%")
        fig.add_hline(y=5, line_dash="dash", line_color="green", annotation_text="Target 5%")
        fig.add_hline(y=7, line_dash="dash", line_color="red", annotation_text="Max 7%")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Allocation pie chart
        fig = px.pie(
            orders_df,
            values='value',
            names='symbol',
            title='Investment Distribution'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Execution buttons
    st.subheader("🚀 Execute Investment")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 Recalculate Plan", use_container_width=True):
            st.session_state.investment_plan = None
            st.rerun()
    
    with col2:
        if st.button("🚀 Execute Investment", type="primary", use_container_width=True):
            execute_initial_investment()

def execute_initial_investment():
    """Execute the initial investment plan"""
    plan = st.session_state.investment_plan
    
    with st.spinner("Executing investment plan..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/investment/execute-initial",
                json={"investment_amount": plan['investment_amount']},
                timeout=60
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if result_data.get('success'):
                    result = result_data['data']
                    
                    st.success("🎉 Investment executed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📝 Orders Executed", result['orders_executed'])
                    
                    with col2:
                        st.metric("💰 Total Invested", f"₹{result['total_investment']:,.0f}")
                    
                    with col3:
                        st.metric("💵 Remaining Cash", f"₹{result['remaining_cash']:,.0f}")
                    
                    st.markdown('<div class="success-alert">✅ <strong>Investment Complete!</strong><br>Your orders have been recorded in the system.</div>', unsafe_allow_html=True)
                    
                    # Clear the plan
                    st.session_state.investment_plan = None
                    
                else:
                    st.error(f"Execution failed: {result_data.get('detail', 'Unknown error')}")
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error executing investment: {e}")

def show_rebalancing_page():
    """Rebalancing page"""
    st.header("⚖️ Portfolio Rebalancing")
    
    # Check if rebalancing is needed
    try:
        with st.spinner("Checking rebalancing requirements..."):
            response = requests.get(f"{API_BASE_URL}/investment/rebalancing-check", timeout=30)
        
        if response.status_code == 200:
            rebalancing_data = response.json()
            if rebalancing_data.get('success'):
                rebalancing_info = rebalancing_data['data']
                
                if rebalancing_info.get('rebalancing_needed'):
                    st.markdown('<div class="warning-alert">⚖️ <strong>Rebalancing Needed!</strong><br>Your portfolio needs rebalancing due to CSV changes.</div>', unsafe_allow_html=True)
                    # Add rebalancing interface here
                else:
                    if rebalancing_info.get('is_first_time'):
                        st.markdown('<div class="info-alert">💡 <strong>First Time Setup</strong><br>Please complete your initial investment first.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-alert">✅ <strong>Portfolio Balanced</strong><br>No rebalancing needed at this time.</div>', unsafe_allow_html=True)
            else:
                st.error("Failed to check rebalancing status")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error checking rebalancing: {e}")
        st.write("This usually means Zerodha connection is not working or backend is down.")

def show_portfolio_status():
    """Portfolio status page with real data only"""
    st.header("📊 Portfolio Status")
    
    try:
        with st.spinner("Loading portfolio data..."):
            response = requests.get(f"{API_BASE_URL}/api/portfolio/summary/1", timeout=30)
        
        if response.status_code == 200:
            portfolio_data = response.json()
            
            if portfolio_data.get("error"):
                st.error(f"❌ Error: {portfolio_data['error']}")
                st.info(portfolio_data.get('message', ''))
                return
            
            # Display portfolio data
            show_portfolio_details(portfolio_data)
                
        else:
            st.error(f"API Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error fetching portfolio status: {e}")
        st.write("This usually means:")
        st.write("- Backend server is not running")
        st.write("- Zerodha connection is not working")
        st.write("- Network connectivity issues")

def show_portfolio_details(portfolio_data):
    """Show detailed portfolio information"""
    
    # Portfolio Header with Key Metrics
    st.subheader("📊 Portfolio Overview")
    
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
        
        # Prepare holdings data for display
        holdings_data = []
        for holding in holdings:
            holdings_data.append({
                'Stock': holding.get('symbol', ''),
                'Quantity': f"{holding.get('quantity', 0):,}",
                'Avg Price': f"₹{holding.get('avg_price', 0):.2f}",
                'Current Price': f"₹{holding.get('current_price', 0):.2f}",
                'Current Value': f"₹{holding.get('current_value', 0):,.0f}",
                'P&L': f"₹{holding.get('pnl', 0):,.0f}",
                'P&L %': f"{holding.get('pnl_percent', 0):.2f}%",
                'Allocation %': f"{holding.get('allocation_percent', 0):.2f}%"
            })
        
        holdings_df = pd.DataFrame(holdings_data)
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)
        
        # Performance charts
        if len(holdings) > 0:
            show_performance_charts(holdings)
    else:
        st.info("📭 No holdings data available")

def show_performance_charts(holdings):
    """Show performance charts"""
    st.subheader("📈 Performance Analysis")
    
    # Prepare data for charts
    chart_data = []
    for holding in holdings:
        chart_data.append({
            'Stock': holding.get('symbol', ''),
            'Current Value': holding.get('current_value', 0),
            'P&L %': holding.get('pnl_percent', 0),
            'Allocation %': holding.get('allocation_percent', 0)
        })
    
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # P&L bar chart
            fig = px.bar(
                chart_df,
                x='Stock',
                y='P&L %',
                title='Stock P&L (%)',
                color='P&L %',
                color_continuous_scale='RdYlGn'
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Allocation pie chart
            fig = px.pie(
                chart_df,
                values='Current Value',
                names='Stock',
                title='Portfolio Allocation'
            )
            st.plotly_chart(fig, use_container_width=True)

def show_order_history():
    """Order history page"""
    st.header("📋 Order History")
    
    try:
        with st.spinner("Loading order history..."):
            response = requests.get(f"{API_BASE_URL}/investment/system-orders", timeout=30)
        
        if response.status_code == 200:
            orders_data = response.json()
            if orders_data.get('success'):
                orders = orders_data['data']['orders']
                
                if orders:
                    orders_df = pd.DataFrame(orders)
                    
                    # Format for display
                    orders_df['value_formatted'] = orders_df['value'].apply(lambda x: f"₹{x:,.0f}")
                    orders_df['price_formatted'] = orders_df['price'].apply(lambda x: f"₹{x:.2f}")
                    orders_df['execution_time'] = pd.to_datetime(orders_df['execution_time']).dt.strftime('%Y-%m-%d %H:%M')
                    
                    display_orders = orders_df[['execution_time', 'symbol', 'action', 'shares', 'price_formatted', 'value_formatted', 'status']].rename(columns={
                        'execution_time': 'Time',
                        'symbol': 'Stock',
                        'action': 'Action',
                        'shares': 'Shares',
                        'price_formatted': 'Price',
                        'value_formatted': 'Value',
                        'status': 'Status'
                    })
                    
                    st.dataframe(display_orders, use_container_width=True, hide_index=True)
                    
                    # Order summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_orders = len(orders)
                        st.metric("📝 Total Orders", total_orders)
                    
                    with col2:
                        buy_orders = len([o for o in orders if o['action'] == 'BUY'])
                        st.metric("📈 Buy Orders", buy_orders)
                    
                    with col3:
                        total_value = sum(float(o['value']) for o in orders if o['action'] == 'BUY')
                        st.metric("💰 Total Investment", f"₹{total_value:,.0f}")
                    
                    with col4:
                        unique_stocks = len(set(o['symbol'] for o in orders))
                        st.metric("🏢 Unique Stocks", unique_stocks)
                    
                else:
                    st.info("📭 No orders found.")
            else:
                st.error("Failed to get order history")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching order history: {e}")

def show_settings():
    """Settings page"""
    st.header("🔧 Settings")
    
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
    
    # System configuration
    st.subheader("⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("API Base URL", value=API_BASE_URL, disabled=True)
        st.number_input("Request Timeout (seconds)", min_value=5, max_value=60, value=30)
    
    with col2:
        st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=1)
        st.checkbox("Enable Auto-refresh", value=False)
    
    # Portfolio settings
    st.subheader("📊 Portfolio Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Minimum Investment (₹)", min_value=100000, value=200000, step=50000)
        st.number_input("Target Allocation (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.1)
    
    with col2:
        st.number_input("Rebalancing Threshold (₹)", min_value=5000, value=10000, step=1000)
        st.slider("Allocation Tolerance (±%)", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

if __name__ == "__main__":
    main()