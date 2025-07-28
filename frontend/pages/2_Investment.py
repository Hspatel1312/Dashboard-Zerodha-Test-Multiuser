# frontend/pages/2_Investment.py - FIXED VERSION
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
    """Check if user has existing portfolio with better error handling"""
    with st.spinner("Checking portfolio status..."):
        portfolio_response = api_client.get_portfolio_status()
    
    portfolio_data = APIHelpers.extract_data(portfolio_response)
    
    # Handle different portfolio states
    if not portfolio_data:
        st.error("❌ Unable to check portfolio status. Please check your connection.")
        return
    
    portfolio_status = portfolio_data.get('status', 'unknown')
    
    if portfolio_status == 'active':
        show_additional_investment_flow(api_client, portfolio_data)
    else:
        show_initial_investment_flow(api_client)

def show_initial_investment_flow(api_client):
    """Show initial investment setup flow with comprehensive error handling"""
    st.subheader("🚀 Initial Investment Setup")
    
    # Step 1: Get requirements
    st.markdown("### Step 1: Investment Requirements")
    
    with st.spinner("Loading investment requirements..."):
        req_response = api_client.get_investment_requirements()
    
    requirements_data = APIHelpers.extract_data(req_response)
    
    if not requirements_data:
        st.error("❌ Unable to load investment requirements")
        show_connection_help()
        return
    
    # Check for various error states
    error_type = requirements_data.get('error')
    if error_type:
        show_requirements_error(requirements_data, error_type)
        return
    
    # Show requirements if data is valid
    show_investment_requirements(requirements_data)
    
    # Step 2: Choose investment amount
    st.markdown("### Step 2: Choose Investment Amount")
    investment_amount = choose_investment_amount(requirements_data)
    
    # Step 3: Calculate and execute plan
    if investment_amount > 0:
        st.markdown("### Step 3: Investment Plan")
        show_investment_plan(api_client, investment_amount)

def show_requirements_error(error_data, error_type):
    """Show appropriate error message based on error type"""
    error_message = error_data.get('error_message', 'Unknown error occurred')
    
    if error_type == 'PRICE_DATA_UNAVAILABLE':
        st.error("🚫 **Live Price Data Required**")
        
        st.markdown(f"""
        ### ⚠️ Cannot Proceed Without Live Prices
        
        **Issue**: {error_message}
        
        **Why This Matters**: 
        - Investment calculations require accurate, real-time stock prices
        - Using outdated or fake prices could lead to incorrect investment decisions
        - This system only works with live market data to ensure accuracy
        """)
        
        # Show data quality info if available
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
            
            st.markdown("""
            **Steps to Resolve**:
            1. Ensure Zerodha is properly authenticated
            2. Check if market is open (9:15 AM - 3:30 PM)
            3. Verify internet connection
            4. Try refreshing the page
            """)
        
        # Show CSV info if available
        csv_info = error_data.get('stocks_data', {})
        if csv_info and csv_info.get('total_symbols', 0) > 0:
            st.markdown("#### 📄 CSV Data Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Stocks Available", csv_info.get('total_symbols', 0))
            
            with col2:
                st.info("📄 CSV data is available, but live prices are needed for calculations")
        
        # Retry button
        if st.button("🔄 Retry Connection", type="primary", use_container_width=True):
            st.rerun()
    
    elif error_type == 'REQUIREMENTS_ERROR':
        st.error(f"❌ **System Error**")
        st.markdown(f"**Details**: {error_message}")
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.rerun()
    
    else:
        st.error(f"❌ **Unexpected Error**")
        st.markdown(f"**Details**: {error_message}")
        st.markdown("**Error Type**: " + error_type)
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

def show_connection_help():
    """Show connection help information"""
    st.markdown("""
    ### 🔧 Connection Help
    
    **Common Issues:**
    - Backend server may not be running
    - Network connectivity problems
    - API endpoints not responding
    
    **Solutions:**
    1. Check if the backend server is running on port 8000
    2. Verify your internet connection
    3. Try refreshing the page
    4. Contact system administrator if problems persist
    """)

def show_additional_investment_flow(api_client, portfolio_data):
    """Show additional investment flow for existing portfolio"""
    st.subheader("📈 Add to Existing Portfolio")
    
    # Check portfolio data quality
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
        current_value = summary.get('current_value', 0)
        st.metric("Current Value", APIHelpers.format_currency(current_value))
    
    with col2:
        total_investment = summary.get('total_investment', 0)
        st.metric("Total Invested", APIHelpers.format_currency(total_investment))
    
    with col3:
        total_returns = summary.get('total_returns', 0)
        st.metric("Total Returns", APIHelpers.format_currency(total_returns))
    
    # Show data quality info
    price_source = data_quality.get('price_source', 'Unknown')
    if 'Live' in price_source:
        st.success(f"✅ Portfolio calculated with live prices from {price_source}")
    else:
        st.warning(f"⚠️ Portfolio calculated with {price_source}")
    
    st.info("ℹ️ You have an existing portfolio. Additional investments will trigger rebalancing.")
    
    if st.button("➡️ Go to Rebalancing Page", use_container_width=True):
        st.switch_page("pages/3_Rebalancing.py")

def show_investment_requirements(requirements_data):
    """Display investment requirements with error handling"""
    stocks_data = requirements_data.get('stocks_data', {})
    min_investment_info = requirements_data.get('minimum_investment', {})
    
    # Handle missing or invalid data
    if not stocks_data or stocks_data.get('total_stocks', 0) == 0:
        st.warning("⚠️ No stock data available. Cannot proceed with investment.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### 📊 Current Market Data")
        
        total_stocks = stocks_data.get('total_stocks', 0)
        price_status = stocks_data.get('price_data_status', {})
        data_source = price_status.get('market_data_source', 'Unknown')
        success_rate = price_status.get('success_rate', 0)
        data_quality_level = price_status.get('data_quality', 'Unknown')
        
        if total_stocks > 0:
            st.success(f"✅ **{total_stocks} stocks** available for investment")
        else:
            st.error("❌ No stocks available for investment")
            return
        
        if 'Live' in data_source:
            st.success(f"📡 **Data Source**: {data_source} ({success_rate:.1f}% success rate)")
        else:
            st.warning(f"📡 **Data Source**: {data_source} ({success_rate:.1f}% success rate)")
        
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
        
        if min_investment_info:
            min_amount = min_investment_info.get('minimum_investment', 0)
            recommended_amount = min_investment_info.get('recommended_minimum', 0)
            most_expensive = min_investment_info.get('most_expensive_stock', {})
            
            st.metric("Minimum Required", APIHelpers.format_currency(min_amount))
            st.metric("Recommended Minimum", APIHelpers.format_currency(recommended_amount))
            
            if most_expensive:
                symbol = most_expensive.get('symbol', 'N/A')
                price = most_expensive.get('price', 0)
                st.caption(f"Based on most expensive stock: {symbol} at ₹{price:,.2f}")
        else:
            st.warning("⚠️ Unable to calculate minimum investment requirements")
        
        # Data quality indicator
        data_quality = requirements_data.get('data_quality', {})
        if data_quality.get('live_data_available', False):
            st.success("✅ Live data available")
        else:
            st.error("❌ Live data unavailable")

def choose_investment_amount(requirements_data):
    """Investment amount selection with validation"""
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
            if total_stocks > 0:
                avg_per_stock = investment_amount / total_stocks
                
                st.info(f"📊 **Allocation Preview**: ~₹{avg_per_stock:,.0f} per stock ({total_stocks} stocks)")
                st.success(f"✅ **All calculations use live prices**")
            else:
                st.warning("⚠️ No stocks available for allocation preview")
    
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
            if st.button(f"{label}\n₹{amount:,.0f}", use_container_width=True, key=f"quick_{amount}"):
                st.session_state.selected_amount = amount
                st.rerun()
        
        # Use selected amount if available
        if 'selected_amount' in st.session_state:
            investment_amount = st.session_state.selected_amount
            del st.session_state.selected_amount
    
    return investment_amount

def show_investment_plan(api_client, investment_amount):
    """Calculate and show investment plan with comprehensive error handling"""
    
    # Calculate plan button
    if st.button("🧮 Calculate Investment Plan", type="primary", use_container_width=True):
        with st.spinner("Calculating optimal allocation with live prices..."):
            plan_response = api_client.calculate_investment_plan(investment_amount)
        
        plan_data = APIHelpers.extract_data(plan_response)
        
        if not plan_data:
            st.error("❌ Unable to calculate investment plan. Please try again.")
            return
        
        # Check for errors in plan calculation
        if plan_data.get('error'):
            show_plan_error(plan_data)
            return
        
        # Store valid plan
        st.session_state.investment_plan = plan_data
        st.rerun()
    
    # Show plan if available
    if 'investment_plan' in st.session_state:
        plan_data = st.session_state.investment_plan
        
        # Verify plan has valid data
        if plan_data.get('error'):
            show_plan_error(plan_data)
            return
        
        data_quality = plan_data.get('data_quality', {})
        if not data_quality.get('live_data_available', False):
            st.error("🚫 **Invalid Plan - Missing Live Price Data**")
            st.markdown("This plan was not created with live prices and cannot be executed.")
            
            if st.button("🔄 Recalculate with Live Data"):
                if 'investment_plan' in st.session_state:
                    del st.session_state.investment_plan
                st.rerun()
            return
        
        # Plan summary
        show_plan_summary(plan_data)
        
        # Orders table
        show_plan_orders(plan_data)
        
        # Execution section
        show_plan_execution(api_client, investment_amount, plan_data)

def show_plan_error(plan_data):
    """Show plan calculation errors"""
    error_type = plan_data.get('error')
    error_message = plan_data.get('error_message', 'Unknown error')
    
    if error_type == 'PRICE_DATA_UNAVAILABLE':
        st.error("🚫 **Cannot Calculate Plan - Live Prices Required**")
        st.markdown(f"**Issue**: {error_message}")
        
        if st.button("🔄 Retry with Live Data", use_container_width=True):
            st.rerun()
    
    elif error_type == 'PLAN_ERROR' or error_type == 'PLAN_CALCULATION_ERROR':
        st.error("❌ **Plan Calculation Failed**")
        st.markdown(f"**Details**: {error_message}")
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.rerun()
    
    else:
        st.error(f"❌ **Unexpected Error**: {error_type}")
        st.markdown(f"**Details**: {error_message}")

def show_plan_summary(plan_data):
    """Show investment plan summary with error handling"""
    st.markdown("#### 📋 Investment Plan Summary")
    
    summary = plan_data.get('summary', {})
    data_quality = plan_data.get('data_quality', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = summary.get('total_orders', 0)
        st.metric("Total Orders", total_orders)
    
    with col2:
        total_stocks = summary.get('total_stocks', 0)
        st.metric("Stocks", total_stocks)
    
    with col3:
        investment_value = summary.get('total_investment_value', 0)
        st.metric("Investment Value", APIHelpers.format_currency(investment_value))
    
    with col4:
        remaining_cash = summary.get('remaining_cash', 0)
        st.metric("Remaining Cash", APIHelpers.format_currency(remaining_cash))
    
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
    """Show planned orders table with error handling"""
    st.markdown("#### 📝 Planned Orders")
    
    orders = plan_data.get('orders', [])
    
    if not orders:
        st.info("No orders to display")
        return
    
    try:
        # Convert to DataFrame
        df = pd.DataFrame(orders)
        
        # Format for display
        display_df = df.copy()
        
        # Safe formatting with error handling
        if 'price' in display_df.columns:
            display_df['price_fmt'] = display_df['price'].apply(lambda x: f"₹{float(x):.2f}" if pd.notnull(x) else "₹0.00")
        
        if 'value' in display_df.columns:
            display_df['value_fmt'] = display_df['value'].apply(lambda x: f"₹{float(x):,.0f}" if pd.notnull(x) else "₹0")
        
        if 'allocation_percent' in display_df.columns:
            display_df['allocation_fmt'] = display_df['allocation_percent'].apply(lambda x: f"{float(x):.2f}%" if pd.notnull(x) else "0.00%")
        
        # Add price type indicator
        if 'price_type' in display_df.columns:
            display_df['price_with_type'] = display_df.apply(
                lambda row: f"{row.get('price_fmt', '₹0.00')} ({row.get('price_type', 'UNKNOWN')})", axis=1
            )
        else:
            display_df['price_with_type'] = display_df.get('price_fmt', '₹0.00')
        
        # Select and rename columns
        columns_to_show = []
        column_mapping = {}
        
        if 'symbol' in display_df.columns:
            columns_to_show.append('symbol')
            column_mapping['symbol'] = 'Stock'
        
        if 'shares' in display_df.columns:
            columns_to_show.append('shares')
            column_mapping['shares'] = 'Shares'
        elif 'quantity' in display_df.columns:
            columns_to_show.append('quantity')
            column_mapping['quantity'] = 'Shares'
        
        if 'price_with_type' in display_df.columns:
            columns_to_show.append('price_with_type')
            column_mapping['price_with_type'] = 'Price (Type)'
        
        if 'value_fmt' in display_df.columns:
            columns_to_show.append('value_fmt')
            column_mapping['value_fmt'] = 'Investment'
        
        if 'allocation_fmt' in display_df.columns:
            columns_to_show.append('allocation_fmt')
            column_mapping['allocation_fmt'] = 'Allocation %'
        
        # Create final dataframe
        final_df = display_df[columns_to_show].rename(columns=column_mapping)
        
        st.dataframe(
            final_df,
            use_container_width=True,
            hide_index=True
        )
    
    except Exception as e:
        st.error(f"❌ Error displaying orders table: {str(e)}")
        # Fallback: show raw data
        st.json(orders)

def show_plan_execution(api_client, investment_amount, plan_data):
    """Show plan execution section with error handling"""
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
                if 'investment_plan' in st.session_state:
                    del st.session_state.investment_plan
                st.rerun()

def execute_investment_plan(api_client, investment_amount):
    """Execute the investment plan with comprehensive error handling"""
    with st.spinner("Executing investment plan with live data..."):
        result_response = api_client.execute_initial_investment(investment_amount)
    
    if not result_response:
        st.error("❌ No response from server during execution")
        return
    
    # Check if execution was successful
    if not APIHelpers.show_api_status(result_response, "Investment executed successfully!"):
        # Error was already shown by show_api_status
        return
    
    result_data = APIHelpers.extract_data(result_response)
    
    if not result_data:
        st.error("❌ No result data received from execution")
        return
    
    # Check for execution errors
    if result_data.get('error'):
        error_type = result_data.get('error')
        error_message = result_data.get('error_message', 'Execution failed')
        
        st.error(f"❌ **Execution Failed**: {error_type}")
        st.markdown(f"**Details**: {error_message}")
        return
    
    # Show successful execution results
    st.balloons()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        orders_executed = result_data.get('orders_executed', 0)
        st.metric("Orders Executed", orders_executed)
    
    with col2:
        total_investment = result_data.get('total_investment', 0)
        st.metric("Total Investment", APIHelpers.format_currency(total_investment))
    
    with col3:
        utilization = result_data.get('utilization_percent', 0)
        st.metric("Utilization", f"{utilization:.1f}%")
    
    # Data quality confirmation
    data_quality = result_data.get('data_quality', {})
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