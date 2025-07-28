  
# frontend/pages/2_Investment.py
import streamlit as st
import pandas as pd
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from api_client import APIClient, APIHelpers
from session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="Investment",
    page_icon="💰",
    layout="wide"
)

def main():
    # Check authentication
    session_manager = SessionManager()
    if not session_manager.is_authenticated():
        st.error("🔒 Please login through the main page")
        st.stop()
    
    # Initialize API client
    api_client = APIClient("http://127.0.0.1:8000", session_manager)
    
    # Page header
    st.title("💰 Investment")
    st.markdown("Set up your initial investment or add funds to existing portfolio")
    
    # Check if user already has portfolio
    check_existing_portfolio(api_client)

def check_existing_portfolio(api_client):
    """Check if user has existing portfolio"""
    with st.spinner("Checking portfolio status..."):
        portfolio_response = api_client.get_portfolio_status()
    
    portfolio_data = APIHelpers.extract_data(portfolio_response)
    
    if portfolio_data and portfolio_data.get('status') == 'active':
        show_additional_investment_flow(api_client, portfolio_data)
    else:
        show_initial_investment_flow(api_client)

def show_initial_investment_flow(api_client):
    """Show initial investment setup flow"""
    st.subheader("🚀 Initial Investment Setup")
    
    # Step 1: Get requirements
    st.markdown("### Step 1: Investment Requirements")
    
    with st.spinner("Loading investment requirements..."):
        req_response = api_client.get_investment_requirements()
    
    requirements_data = APIHelpers.extract_data(req_response)
    
    if not requirements_data:
        st.error("❌ Unable to load investment requirements")
        return
    
    # Show requirements
    show_investment_requirements(requirements_data)
    
    # Step 2: Choose investment amount
    st.markdown("### Step 2: Choose Investment Amount")
    investment_amount = choose_investment_amount(requirements_data)
    
    # Step 3: Calculate and execute plan
    if investment_amount > 0:
        st.markdown("### Step 3: Investment Plan")
        show_investment_plan(api_client, investment_amount)

def show_additional_investment_flow(api_client, portfolio_data):
    """Show additional investment flow for existing portfolio"""
    st.subheader("📈 Add to Existing Portfolio")
    
    summary = portfolio_data.get('portfolio_summary', {})
    
    # Show current portfolio summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Value", APIHelpers.format_currency(summary.get('current_value', 0)))
    with col2:
        st.metric("Total Invested", APIHelpers.format_currency(summary.get('total_investment', 0)))
    with col3:
        st.metric("Total Returns", APIHelpers.format_currency(summary.get('total_returns', 0)))
    
    st.info("ℹ️ You have an existing portfolio. Additional investments will trigger rebalancing.")
    
    if st.button("➡️ Go to Rebalancing Page", use_container_width=True):
        st.switch_page("pages/3_Rebalancing.py")

def show_investment_requirements(requirements_data):
    """Display investment requirements"""
    stocks_data = requirements_data.get('stocks_data', {})
    min_investment_info = requirements_data.get('minimum_investment', {})
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📊 Current Market Data")
        
        total_stocks = stocks_data.get('total_stocks', 0)
        data_source = stocks_data.get('price_data_status', {}).get('market_data_source', 'Unknown')
        success_rate = stocks_data.get('price_data_status', {}).get('success_rate', 0)
        
        st.success(f"✅ **{total_stocks} stocks** available for investment")
        st.info(f"📡 **Data Source**: {data_source} ({success_rate:.1f}% success rate)")
        
        # Show strategy
        st.markdown("""
        **Investment Strategy:**
        - **Equal Weight Allocation**: Each stock gets approximately 5% allocation
        - **Allocation Range**: 4-7% per stock (with flexibility for price constraints)
        - **Diversification**: Spread across multiple sectors and market caps
        """)
    
    with col2:
        st.markdown("#### 💰 Investment Requirements")
        
        min_amount = min_investment_info.get('minimum_investment', 0)
        recommended_amount = min_investment_info.get('recommended_minimum', 0)
        most_expensive = min_investment_info.get('most_expensive_stock', {})
        
        st.metric("Minimum Required", APIHelpers.format_currency(min_amount))
        st.metric("Recommended Minimum", APIHelpers.format_currency(recommended_amount))
        
        if most_expensive:
            st.caption(f"Based on most expensive stock: {most_expensive.get('symbol', 'N/A')} at ₹{most_expensive.get('price', 0):,.2f}")

def choose_investment_amount(requirements_data):
    """Investment amount selection"""
    min_investment_info = requirements_data.get('minimum_investment', {})
    min_amount = min_investment_info.get('minimum_investment', 200000)
    recommended_amount = min_investment_info.get('recommended_minimum', 200000)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Investment amount input
        investment_amount = st.number_input(
            "Investment Amount (₹)",
            min_value=int(min_amount),
            value=int(recommended_amount),
            step=10000,
            help=f"Minimum required: ₹{min_amount:,.0f}"
        )
        
        # Show allocation preview
        if investment_amount > 0:
            total_stocks = requirements_data.get('stocks_data', {}).get('total_stocks', 20)
            avg_per_stock = investment_amount / total_stocks
            
            st.info(f"📊 **Allocation Preview**: ~₹{avg_per_stock:,.0f} per stock ({total_stocks} stocks)")
    
    with col2:
        st.markdown("**Quick Options:**")
        
        quick_amounts = [
            ("Minimum", min_amount),
            ("Recommended", recommended_amount),
            ("₹3 Lakhs", 300000),
            ("₹5 Lakhs", 500000),
            ("₹10 Lakhs", 1000000)
        ]
        
        for label, amount in quick_amounts:
            if st.button(f"{label}\n₹{amount:,.0f}", use_container_width=True):
                st.session_state.selected_amount = amount
                st.rerun()
        
        # Use selected amount if available
        if 'selected_amount' in st.session_state:
            investment_amount = st.session_state.selected_amount
            del st.session_state.selected_amount
    
    return investment_amount

def show_investment_plan(api_client, investment_amount):
    """Calculate and show investment plan"""
    
    # Calculate plan button
    if st.button("🧮 Calculate Investment Plan", type="primary", use_container_width=True):
        with st.spinner("Calculating optimal allocation..."):
            plan_response = api_client.calculate_investment_plan(investment_amount)
        
        plan_data = APIHelpers.extract_data(plan_response)
        
        if plan_data:
            st.session_state.investment_plan = plan_data
            st.rerun()
    
    # Show plan if available
    if 'investment_plan' in st.session_state:
        plan_data = st.session_state.investment_plan
        
        # Plan summary
        show_plan_summary(plan_data)
        
        # Orders table
        show_plan_orders(plan_data)
        
        # Execution section
        show_plan_execution(api_client, investment_amount, plan_data)

def show_plan_summary(plan_data):
    """Show investment plan summary"""
    st.markdown("#### 📋 Investment Plan Summary")
    
    summary = plan_data.get('summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", summary.get('total_orders', 0))
    with col2:
        st.metric("Stocks", summary.get('total_stocks', 0))
    with col3:
        st.metric("Investment Value", APIHelpers.format_currency(summary.get('total_investment_value', 0)))
    with col4:
        st.metric("Remaining Cash", APIHelpers.format_currency(summary.get('remaining_cash', 0)))
    
    # Validation status
    validation = plan_data.get('validation', {})
    success_rate = validation.get('success_rate', 0)
    
    if success_rate == 100:
        st.success(f"✅ All stocks within target allocation (4-7%)")
    else:
        st.warning(f"⚠️ {success_rate:.1f}% of stocks in target range")
        
        violations = validation.get('violations', [])
        if violations:
            with st.expander("View Allocation Issues"):
                for violation in violations:
                    st.write(f"• {violation}")

def show_plan_orders(plan_data):
    """Show planned orders table"""
    st.markdown("#### 📝 Planned Orders")
    
    orders = plan_data.get('orders', [])
    
    if not orders:
        st.info("No orders to display")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(orders)
    
    # Format for display
    display_df = df.copy()
    display_df['price'] = display_df['price'].apply(lambda x: f"₹{x:.2f}")
    display_df['value'] = display_df['value'].apply(lambda x: f"₹{x:,.0f}")
    display_df['allocation_percent'] = display_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
    
    # Rename columns
    display_df = display_df.rename(columns={
        'symbol': 'Stock',
        'shares': 'Shares',
        'price': 'Price',
        'value': 'Investment',
        'allocation_percent': 'Allocation %'
    })
    
    st.dataframe(
        display_df[['Stock', 'Shares', 'Price', 'Investment', 'Allocation %']],
        use_container_width=True,
        hide_index=True
    )

def show_plan_execution(api_client, investment_amount, plan_data):
    """Show plan execution section"""
    st.markdown("#### 🚀 Execute Investment")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("💡 **Ready to Execute**: Your investment plan is ready. This will create system orders for tracking.")
        st.markdown("""
        **What happens next:**
        1. System orders will be created for each stock
        2. Portfolio state will be updated
        3. You can track progress in the Portfolio Overview
        """)
    
    with col2:
        if st.button("🚀 Execute Investment", type="primary", use_container_width=True):
            execute_investment_plan(api_client, investment_amount)

def execute_investment_plan(api_client, investment_amount):
    """Execute the investment plan"""
    with st.spinner("Executing investment plan..."):
        result_response = api_client.execute_initial_investment(investment_amount)
    
    if APIHelpers.show_api_status(result_response, "Investment executed successfully!"):
        result_data = APIHelpers.extract_data(result_response)
        
        if result_data:
            # Show execution results
            st.balloons()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Orders Executed", result_data.get('orders_executed', 0))
            with col2:
                st.metric("Total Investment", APIHelpers.format_currency(result_data.get('total_investment', 0)))
            with col3:
                st.metric("Utilization", f"{result_data.get('utilization_percent', 0):.1f}%")
            
            # Clear the plan from session
            if 'investment_plan' in st.session_state:
                del st.session_state.investment_plan
            
            # Navigation options
            st.markdown("### 🎉 Investment Complete!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 View Portfolio", use_container_width=True):
                    st.switch_page("pages/1_Portfolio_Overview.py")
            
            with col2:
                if st.button("📋 View Orders", use_container_width=True):
                    st.switch_page("pages/4_Order_History.py")

if __name__ == "__main__":
    main()