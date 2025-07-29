# frontend/pages/2_Investment.py - Updated with price data error handling
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
    
    # Check if we have a price data error
    if 'error' in requirements_data and requirements_data['error'] == 'PRICE_DATA_UNAVAILABLE':
        show_price_data_unavailable_error(requirements_data)
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

def show_price_data_unavailable_error(error_data):
    """Show error when price data is unavailable"""
    st.error("🚫 **Live Price Data Required**")
    
    error_message = error_data.get('error_message', 'Price data unavailable')
    
    # Main error display
    st.markdown(f"""
    ### ⚠️ Cannot Proceed Without Live Prices
    
    **Issue**: {error_message}
    
    **Why This Matters**: 
    - Investment calculations require accurate, real-time stock prices
    - Using outdated or fake prices could lead to incorrect investment decisions
    - This system only works with live market data to ensure accuracy
    """)
    
    # Data quality info
    data_quality = error_data.get('data_quality', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 System Status")
        
        zerodha_connected = data_quality.get('zerodha_connected', False)
        if zerodha_connected:
            st.success("✅ Zerodha service available")
        else:
            st.error("❌ Zerodha not connected")
        
        st.info(f"📊 **Data Policy**: Strict - Real data only")
        st.info(f"🚫 **No Fallbacks**: Fake prices disabled")
    
    with col2:
        st.markdown("#### 🛠️ Solutions")
        
        solution = data_quality.get('solution', 'Check connection and try again')
        st.markdown(f"**Recommended Action**: {solution}")
        
        st.markdown("""
        **Steps to Resolve**:
        1. Ensure Zerodha is properly authenticated
        2. Check if market is open (9:15 AM - 3:30 PM)
        3. Verify internet connection
        4. Try refreshing the page
        """)
    
    # CSV info if available
    csv_info = error_data.get('csv_info', {})
    if csv_info:
        st.markdown("#### 📄 CSV Data Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Stocks in CSV", csv_info.get('total_symbols', 'Unknown'))
        
        with col2:
            fetch_time = csv_info.get('fetch_time', 'Unknown')
            if fetch_time != 'Unknown':
                try:
                    fetch_dt = pd.to_datetime(fetch_time)
                    time_display = fetch_dt.strftime('%H:%M:%S')
                except:
                    time_display = "Unknown"
            else:
                time_display = "Unknown"
            st.metric("CSV Updated", time_display)
        
        with col3:
            csv_hash = csv_info.get('csv_hash', 'Unknown')
            display_hash = csv_hash[:8] + "..." if len(csv_hash) > 8 else csv_hash
            st.metric("Version", display_hash)
        
        st.info("📄 CSV data is available, but live prices are needed for calculations")
    
    # Retry button
    if st.button("🔄 Retry Connection", type="primary", use_container_width=True):
        st.rerun()

def show_additional_investment_flow(api_client, portfolio_data):
    """Show additional investment flow for existing portfolio"""
    st.subheader("📈 Add to Existing Portfolio")
    
    # Check if portfolio has price data issues
    data_quality = portfolio_data.get('data_quality', {})
    
    if not data_quality.get('live_data_available', True):
        st.error("🚫 **Portfolio Value Cannot Be Calculated**")
        
        error_reason = data_quality.get('error_reason', 'Live price data unavailable')
        st.markdown(f"""
        **Issue**: {error_reason}
        
        Your portfolio exists, but current values cannot be calculated without live prices.
        """)
        
        if st.button("🔄 Refresh Price Data", use_container_width=True):
            st.rerun()
        
        return
    
    summary = portfolio_data.get('portfolio_summary', {})
    
    # Show current portfolio summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Value", APIHelpers.format_currency(summary.get('current_value', 0)))
    with col2:
        st.metric("Total Invested", APIHelpers.format_currency(summary.get('total_investment', 0)))
    with col3:
        st.metric("Total Returns", APIHelpers.format_currency(summary.get('total_returns', 0)))
    
    # Show data quality info
    price_source = data_quality.get('price_source', 'Unknown')
    if price_source == 'Zerodha Live API':
        st.success(f"✅ Portfolio calculated with live prices from {price_source}")
    else:
        st.warning(f"⚠️ Portfolio calculated with {price_source}")
    
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
        price_status = stocks_data.get('price_data_status', {})
        data_source = price_status.get('market_data_source', 'Unknown')
        success_rate = price_status.get('success_rate', 0)
        data_quality_level = price_status.get('data_quality_level', 'Unknown')
        
        st.success(f"✅ **{total_stocks} stocks** available for investment")
        st.success(f"📡 **Data Source**: {data_source} ({success_rate:.1f}% success rate)")
        st.info(f"🔬 **Data Quality**: {data_quality_level}")
        
        # Show strategy
        st.markdown("""
        **Investment Strategy:**
        - **Equal Weight Allocation**: Each stock gets approximately 5% allocation
        - **Allocation Range**: 4-7% per stock (with flexibility for price constraints)
        - **Diversification**: Spread across multiple sectors and market caps
        - **Live Prices Only**: All calculations use real-time market data
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
        
        # Data quality indicator
        data_quality = requirements_data.get('data_quality', {})
        if data_quality.get('live_data_available', False):
            st.success("✅ Live data available")
        else:
            st.error("❌ Live data unavailable")

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
            st.success(f"✅ **All calculations use live prices**")
    
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
        with st.spinner("Calculating optimal allocation with live prices..."):
            plan_response = api_client.calculate_investment_plan(investment_amount)
        
        plan_data = APIHelpers.extract_data(plan_response)
        
        if plan_data:
            # Check if plan has price data errors
            if 'error' in plan_data and plan_data['error'] == 'PRICE_DATA_UNAVAILABLE':
                st.error("🚫 **Cannot Calculate Plan - Live Prices Required**")
                error_message = plan_data.get('error_message', 'Price data unavailable')
                st.markdown(f"**Issue**: {error_message}")
                
                if st.button("🔄 Retry with Live Data"):
                    st.rerun()
                return
            
            st.session_state.investment_plan = plan_data
            st.rerun()
    
    # Show plan if available
    if 'investment_plan' in st.session_state:
        plan_data = st.session_state.investment_plan
        
        # Verify plan has live data
        data_quality = plan_data.get('data_quality', {})
        if not data_quality.get('live_data_available', False):
            st.error("🚫 **Invalid Plan - Missing Live Price Data**")
            st.markdown("This plan was not created with live prices and cannot be executed.")
            
            if st.button("🔄 Recalculate with Live Data"):
                del st.session_state.investment_plan
                st.rerun()
            return
        
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
    data_quality = plan_data.get('data_quality', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Orders", summary.get('total_orders', 0))
    with col2:
        st.metric("Stocks", summary.get('total_stocks', 0))
    with col3:
        st.metric("Investment Value", APIHelpers.format_currency(summary.get('total_investment_value', 0)))
    with col4:
        st.metric("Remaining Cash", APIHelpers.format_currency(summary.get('remaining_cash', 0)))
    
    # Data quality display
    if data_quality.get('live_data_available', False):
        data_source = data_quality.get('data_source', 'Unknown')
        quality_level = data_quality.get('data_quality_level', 'Unknown')
        st.success(f"✅ Plan created with live prices from {data_source}")
        st.info(f"🔬 Data Quality: {quality_level}")
    else:
        st.error("❌ Plan lacks live price data")
    
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
    
    # Add price type indicator
    if 'price_type' in display_df.columns:
        display_df['price_with_type'] = display_df.apply(
            lambda row: f"{row['price']} ({row.get('price_type', 'UNKNOWN')})", axis=1
        )
    else:
        display_df['price_with_type'] = display_df['price']
    
    # Rename columns
    display_df = display_df.rename(columns={
        'symbol': 'Stock',
        'shares': 'Shares',
        'price_with_type': 'Price (Type)',
        'value': 'Investment',
        'allocation_percent': 'Allocation %'
    })
    
    st.dataframe(
        display_df[['Stock', 'Shares', 'Price (Type)', 'Investment', 'Allocation %']],
        use_container_width=True,
        hide_index=True
    )

def show_plan_execution(api_client, investment_amount, plan_data):
    """Show plan execution section"""
    st.markdown("#### 🚀 Execute Investment")
    
    data_quality = plan_data.get('data_quality', {})
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if data_quality.get('live_data_available', False):
            st.success("✅ **Ready to Execute with Live Data**")
            st.markdown("""
            **What happens next:**
            1. System orders will be created for each stock using live prices
            2. Portfolio state will be updated with current market data
            3. You can track progress in the Portfolio Overview
            """)
            
            quality_level = data_quality.get('data_quality_level', 'Unknown')
            st.info(f"🔬 **Data Quality**: {quality_level}")
        else:
            st.error("❌ **Cannot Execute - Missing Live Data**")
            st.markdown("""
            **Issue**: This plan was not created with live price data.
            
            **Solution**: Recalculate the plan with current live prices.
            """)
    
    with col2:
        if data_quality.get('live_data_available', False):
            if st.button("🚀 Execute Investment", type="primary", use_container_width=True):
                execute_investment_plan(api_client, investment_amount)
        else:
            if st.button("🔄 Recalculate with Live Data", use_container_width=True):
                del st.session_state.investment_plan
                st.rerun()

def execute_investment_plan(api_client, investment_amount):
    """Execute the investment plan"""
    with st.spinner("Executing investment plan with live data..."):
        result_response = api_client.execute_initial_investment(investment_amount)
    
    if APIHelpers.show_api_status(result_response, "Investment executed successfully!"):
        result_data = APIHelpers.extract_data(result_response)
        
        if result_data:
            # Check execution data quality
            data_quality = result_data.get('data_quality', {})
            
            # Show execution results
            st.balloons()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Orders Executed", result_data.get('orders_executed', 0))
            with col2:
                st.metric("Total Investment", APIHelpers.format_currency(result_data.get('total_investment', 0)))
            with col3:
                st.metric("Utilization", f"{result_data.get('utilization_percent', 0):.1f}%")
            
            # Data quality confirmation
            if data_quality.get('live_data_used', False):
                st.success(f"✅ **Execution completed with live data**")
                quality_level = data_quality.get('data_quality_level', 'Unknown')
                st.info(f"🔬 **Data Quality**: {quality_level}")
            else:
                st.warning("⚠️ Execution completed but data quality uncertain")
            
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