# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(
    page_title="Investment Portfolio Manager",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://127.0.0.1:8000"

# Initialize session state
if 'investment_plan' not in st.session_state:
    st.session_state.investment_plan = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'requirements'

def main():
    st.title("📈 Investment System Manager")
    
    # Test backend connection
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get('zerodha_connected'):
                st.markdown('<div class="success-box">✅ Backend connected! 🔗 Zerodha Connected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-box">✅ Backend connected! ⚠️ Zerodha using sample data</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Backend connection failed")
            return
    except Exception as e:
        st.error(f"❌ Cannot connect to backend: {e}")
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Navigation")
        page = st.selectbox(
            "Select Page",
            ["💰 Initial Investment", "⚖️ Rebalancing", "📊 Portfolio Status", "📋 Order History"]
        )
    
    # Route to appropriate page
    if page == "💰 Initial Investment":
        show_initial_investment_page()
    elif page == "⚖️ Rebalancing":
        show_rebalancing_page()
    elif page == "📊 Portfolio Status":
        show_portfolio_status()
    elif page == "📋 Order History":
        show_order_history()

def show_initial_investment_page():
    """Initial Investment Flow"""
    st.header("💰 Initial Investment Setup")
    
    # Check if this is first time or rebalancing needed
    try:
        response = requests.get(f"{API_BASE_URL}/investment/requirements")
        if response.status_code == 200:
            requirements_data = response.json()
            if requirements_data['success']:
                requirements = requirements_data['data']
            else:
                st.error("Failed to get investment requirements")
                return
        else:
            st.error(f"API Error: {response.status_code}")
            return
    except Exception as e:
        st.error(f"Error fetching requirements: {e}")
        return
    
    # Display investment requirements
    st.subheader("📋 Investment Requirements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_investment = requirements['minimum_investment']['minimum_investment']
        recommended = requirements['minimum_investment']['recommended_minimum']
        st.metric(
            "💸 Minimum Investment",
            f"₹{min_investment:,.0f}",
            help="Absolute minimum based on stock prices and 4% allocation"
        )
    
    with col2:
        st.metric(
            "💡 Recommended",
            f"₹{recommended:,.0f}",
            help="Recommended amount for better allocation (20% buffer)"
        )
    
    with col3:
        total_stocks = requirements['minimum_investment']['total_stocks']
        st.metric(
            "📊 Total Stocks",
            f"{total_stocks}",
            help="Number of stocks from CSV to invest in"
        )
    
    # Show CSV stocks data
    st.subheader("📈 Current CSV Stocks")
    
    stocks_df = pd.DataFrame(requirements['stocks_data']['stocks'])
    stocks_df['price_formatted'] = stocks_df['price'].apply(lambda x: f"₹{x:,.2f}")
    stocks_df['min_investment'] = stocks_df['price'] * 25  # For 4% allocation
    stocks_df['min_investment_formatted'] = stocks_df['min_investment'].apply(lambda x: f"₹{x:,.0f}")
    
    display_df = stocks_df[['symbol', 'price_formatted', 'min_investment_formatted', 'score']].rename(columns={
        'symbol': 'Stock Symbol',
        'price_formatted': 'Current Price',
        'min_investment_formatted': 'Min Investment (4%)',
        'score': 'Momentum Score'
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Investment amount input
    st.subheader("💰 Enter Investment Amount")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        investment_amount = st.number_input(
            "Investment Amount (₹)",
            min_value=float(min_investment),
            value=float(recommended),
            step=10000.0,
            help=f"Minimum: ₹{min_investment:,.0f}"
        )
        
        # Quick amount buttons
        st.write("Quick amounts:")
        col1a, col1b, col1c, col1d = st.columns(4)
        
        with col1a:
            if st.button("₹2L"):
                investment_amount = 200000
        with col1b:
            if st.button("₹5L"):
                investment_amount = 500000
        with col1c:
            if st.button("₹10L"):
                investment_amount = 1000000
        with col1d:
            if st.button("₹20L"):
                investment_amount = 2000000
    
    with col2:
        # Investment summary
        utilization = (investment_amount / recommended) * 100 if recommended > 0 else 0
        avg_per_stock = investment_amount / total_stocks
        
        st.metric("📊 Utilization", f"{utilization:.1f}%")
        st.metric("📈 Avg per Stock", f"₹{avg_per_stock:,.0f}")
        
        if investment_amount < min_investment:
            st.markdown('<div class="error-box">❌ Amount below minimum!</div>', unsafe_allow_html=True)
        elif investment_amount < recommended:
            st.markdown('<div class="warning-box">⚠️ Consider recommended amount</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ Good investment amount</div>', unsafe_allow_html=True)
    
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
            if plan_data['success']:
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
        'price_formatted': 'Price',
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
    
    # Validation status
    validation = plan['validation']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("📊 **Allocation Validation**")
        st.write(f"✅ Stocks in range (4-7%): {validation['stocks_in_range']}/{len(orders_df)}")
        if validation['stocks_below_min'] > 0:
            st.write(f"⚠️ Below minimum: {validation['stocks_below_min']}")
        if validation['stocks_above_max'] > 0:
            st.write(f"⚠️ Above maximum: {validation['stocks_above_max']}")
    
    with col2:
        st.write("💰 **Investment Summary**")
        st.write(f"💸 Total allocated: ₹{total_investment:,.0f}")
        st.write(f"💵 Cash remaining: ₹{remaining_cash:,.0f}")
        st.write(f"📊 Utilization: {utilization:.2f}%")
    
    # Execution buttons
    st.subheader("🚀 Execute Investment")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Recalculate Plan", use_container_width=True):
            st.session_state.investment_plan = None
            st.rerun()
    
    with col2:
        if st.button("💾 Save Plan", use_container_width=True):
            st.info("Plan saved for future reference")
    
    with col3:
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
                if result_data['success']:
                    result = result_data['data']
                    
                    st.success("🎉 Investment executed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📝 Orders Executed", result['orders_executed'])
                    
                    with col2:
                        st.metric("💰 Total Invested", f"₹{result['total_investment']:,.0f}")
                    
                    with col3:
                        st.metric("💵 Remaining Cash", f"₹{result['remaining_cash']:,.0f}")
                    
                    st.markdown('<div class="success-box">✅ <strong>Investment Complete!</strong><br>Your orders have been recorded in the system. You can now monitor your portfolio and check for rebalancing needs.</div>', unsafe_allow_html=True)
                    
                    # Clear the plan
                    st.session_state.investment_plan = None
                    
                    # Show next steps
                    st.subheader("🎯 Next Steps")
                    st.write("1. 📊 Check your portfolio status in the Portfolio Status page")
                    st.write("2. 📋 View your orders in the Order History page")
                    st.write("3. ⚖️ Monitor for rebalancing needs when CSV updates")
                    
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
        response = requests.get(f"{API_BASE_URL}/investment/rebalancing-check")
        if response.status_code == 200:
            rebalancing_data = response.json()
            if rebalancing_data['success']:
                rebalancing_info = rebalancing_data['data']
                
                if rebalancing_info['rebalancing_needed']:
                    st.markdown('<div class="warning-box">⚖️ <strong>Rebalancing Needed!</strong><br>Your portfolio needs rebalancing due to CSV changes.</div>', unsafe_allow_html=True)
                    
                    # Show rebalancing interface
                    show_rebalancing_interface(rebalancing_info)
                else:
                    if rebalancing_info.get('is_first_time'):
                        st.markdown('<div class="info-box">💡 <strong>First Time Setup</strong><br>Please complete your initial investment first.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="success-box">✅ <strong>Portfolio Balanced</strong><br>No rebalancing needed at this time.</div>', unsafe_allow_html=True)
            else:
                st.error("Failed to check rebalancing status")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error checking rebalancing: {e}")

def show_rebalancing_interface(rebalancing_info):
    """Show rebalancing interface"""
    st.subheader("📊 Rebalancing Required")
    
    comparison = rebalancing_info['comparison']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("📈 **New Stocks to Add:**")
        for stock in comparison['new_stocks']:
            st.write(f"• {stock}")
    
    with col2:
        st.write("📉 **Stocks to Remove:**")
        for stock in comparison['removed_stocks']:
            st.write(f"• {stock}")
    
    # Additional investment input
    st.subheader("💰 Additional Investment (Optional)")
    
    additional_investment = st.number_input(
        "Additional Amount (₹)",
        min_value=0,
        value=0,
        step=10000,
        help="Enter additional amount to invest during rebalancing"
    )
    
    # Calculate rebalancing plan
    if st.button("🧮 Calculate Rebalancing Plan", type="primary"):
        calculate_rebalancing_plan(additional_investment)

def calculate_rebalancing_plan(additional_investment):
    """Calculate rebalancing plan"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/investment/calculate-rebalancing",
            json={"additional_investment": additional_investment},
            timeout=30
        )
        
        if response.status_code == 200:
            plan_data = response.json()
            if plan_data['success']:
                st.success("✅ Rebalancing plan calculated!")
                # Store and display plan (similar to initial investment)
                # Implementation would be similar to show_investment_plan()
            else:
                st.error(f"Calculation failed: {plan_data.get('detail', 'Unknown error')}")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error calculating rebalancing: {e}")

def show_portfolio_status():
    """Show current portfolio status"""
    st.header("📊 Portfolio Status")
    
    try:
        response = requests.get(f"{API_BASE_URL}/investment/portfolio-status")
        if response.status_code == 200:
            status_data = response.json()
            if status_data['success']:
                status = status_data['data']
                
                if status:
                    # Display portfolio metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        total_value = sum(holding['total_investment'] for holding in status['holdings'].values())
                        st.metric("💰 Total Investment", f"₹{total_value:,.0f}")
                    
                    with col2:
                        stock_count = len(status['holdings'])
                        st.metric("📊 Holdings", f"{stock_count} stocks")
                    
                    with col3:
                        last_updated = status['last_updated']
                        st.metric("🕒 Last Updated", last_updated[:10])
                    
                    # Holdings table
                    holdings_data = []
                    for symbol, holding in status['holdings'].items():
                        holdings_data.append({
                            'Stock': symbol,
                            'Shares': holding['shares'],
                            'Avg Price': f"₹{holding['avg_price']:.2f}",
                            'Investment': f"₹{holding['total_investment']:,.0f}"
                        })
                    
                    holdings_df = pd.DataFrame(holdings_data)
                    st.dataframe(holdings_df, use_container_width=True, hide_index=True)
                else:
                    st.info("📭 No portfolio found. Please complete initial investment.")
            else:
                st.error("Failed to get portfolio status")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching portfolio status: {e}")

def show_order_history():
    """Show order history"""
    st.header("📋 Order History")
    
    try:
        response = requests.get(f"{API_BASE_URL}/investment/system-orders")
        if response.status_code == 200:
            orders_data = response.json()
            if orders_data['success']:
                orders = orders_data['data']['orders']
                
                if orders:
                    orders_df = pd.DataFrame(orders)
                    
                    # Format for display
                    orders_df['value_formatted'] = orders_df['value'].apply(lambda x: f"₹{x:,.0f}")
                    orders_df['price_formatted'] = orders_df['price'].apply(lambda x: f"₹{x:.2f}")
                    
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
                else:
                    st.info("📭 No orders found.")
            else:
                st.error("Failed to get order history")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error fetching order history: {e}")

if __name__ == "__main__":
    main()