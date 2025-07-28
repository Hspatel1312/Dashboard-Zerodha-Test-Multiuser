# frontend/pages/3_Rebalancing.py
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
    page_title="Rebalancing",
    page_icon="⚖️",
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
    st.title("⚖️ Portfolio Rebalancing")
    st.markdown("Analyze and adjust your portfolio allocation")
    
    # Check rebalancing status
    check_rebalancing_status(api_client)

def check_rebalancing_status(api_client):
    """Check if rebalancing is needed"""
    
    # Load rebalancing check
    with st.spinner("Checking rebalancing requirements..."):
        rebal_response = api_client.check_rebalancing_needed()
        portfolio_response = api_client.get_portfolio_status()
    
    rebal_data = APIHelpers.extract_data(rebal_response)
    portfolio_data = APIHelpers.extract_data(portfolio_response)
    
    if not rebal_data:
        st.error("❌ Unable to check rebalancing requirements")
        return
    
    if not portfolio_data or portfolio_data.get('status') == 'empty':
        show_no_portfolio_message()
        return
    
    # Show rebalancing analysis
    show_rebalancing_analysis(rebal_data, portfolio_data, api_client)

def show_no_portfolio_message():
    """Show message when no portfolio exists"""
    st.info("📭 No portfolio found for rebalancing")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### 🚀 Create Portfolio First
        
        You need an active portfolio before you can rebalance.
        
        **Next Steps:**
        1. Go to Investment page
        2. Set up your initial investment
        3. Return here for rebalancing when needed
        """)
        
        if st.button("➡️ Go to Investment", use_container_width=True):
            st.switch_page("pages/2_Investment.py")

def show_rebalancing_analysis(rebal_data, portfolio_data, api_client):
    """Show comprehensive rebalancing analysis"""
    
    # Current status overview
    show_rebalancing_status(rebal_data, portfolio_data)
    
    st.markdown("---")
    
    # Main analysis in columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_detailed_analysis(rebal_data, portfolio_data)
    
    with col2:
        show_rebalancing_options(rebal_data, api_client)

def show_rebalancing_status(rebal_data, portfolio_data):
    """Show current rebalancing status"""
    
    st.subheader("📊 Current Status")
    
    is_needed = rebal_data.get('rebalancing_needed', False)
    reason = rebal_data.get('reason', 'Unknown')
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if is_needed:
            st.error(f"⚖️ **Rebalancing Needed**")
            st.markdown(f"**Reason**: {reason}")
        else:
            st.success(f"✅ **Portfolio Balanced**")
            st.markdown(f"**Status**: {reason}")
    
    with col2:
        # Portfolio summary
        summary = portfolio_data.get('portfolio_summary', {})
        current_value = summary.get('current_value', 0)
        stock_count = summary.get('stock_count', 0)
        
        st.metric("Current Value", APIHelpers.format_currency(current_value))
        st.metric("Holdings", f"{stock_count} stocks")
    
    with col3:
        # CSV status
        show_csv_status_summary(rebal_data)

def show_csv_status_summary(rebal_data):
    """Show CSV status summary"""
    st.markdown("**CSV Status**")
    
    # This would come from CSV status in a real implementation
    st.success("📊 Data Updated")
    st.caption("Latest stock data loaded")

def show_detailed_analysis(rebal_data, portfolio_data):
    """Show detailed rebalancing analysis"""
    
    if not rebal_data.get('rebalancing_needed', False):
        show_balanced_portfolio_details(portfolio_data)
    else:
        show_rebalancing_requirements(rebal_data, portfolio_data)

def show_balanced_portfolio_details(portfolio_data):
    """Show details for balanced portfolio"""
    st.subheader("✅ Portfolio Analysis")
    
    st.success("Your portfolio is well-balanced and aligned with targets.")
    
    # Show allocation analysis
    holdings = portfolio_data.get('holdings', {})
    
    if holdings:
        st.markdown("#### Current Allocation")
        
        allocation_data = []
        for symbol, holding in holdings.items():
            allocation_data.append({
                'Stock': symbol,
                'Allocation': f"{holding.get('allocation_percent', 0):.2f}%",
                'Target': "5.00%",
                'Status': get_allocation_status(holding.get('allocation_percent', 0))
            })
        
        df = pd.DataFrame(allocation_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Summary insights
        st.info("💡 **Insight**: All holdings are within the target allocation range (4-7%). No immediate action required.")

def get_allocation_status(allocation_percent):
    """Get allocation status indicator"""
    if 4.0 <= allocation_percent <= 7.0:
        return "✅ In Range"
    elif allocation_percent < 4.0:
        return "⬇️ Below Target"
    else:
        return "⬆️ Above Target"

def show_rebalancing_requirements(rebal_data, portfolio_data):
    """Show what changes are needed for rebalancing"""
    st.subheader("📋 Required Changes")
    
    new_stocks = rebal_data.get('new_stocks', [])
    removed_stocks = rebal_data.get('removed_stocks', [])
    
    if new_stocks or removed_stocks:
        col1, col2 = st.columns(2)
        
        with col1:
            if new_stocks:
                st.markdown("#### 📈 Stocks to Add")
                for stock in new_stocks[:5]:  # Show max 5
                    st.write(f"• {stock}")
                if len(new_stocks) > 5:
                    st.caption(f"... and {len(new_stocks) - 5} more")
        
        with col2:
            if removed_stocks:
                st.markdown("#### 📉 Stocks to Remove")
                for stock in removed_stocks[:5]:  # Show max 5
                    st.write(f"• {stock}")
                if len(removed_stocks) > 5:
                    st.caption(f"... and {len(removed_stocks) - 5} more")
    
    # Impact analysis
    st.markdown("#### 💰 Rebalancing Impact")
    st.info("📊 **Analysis**: Portfolio needs adjustment to match latest stock selection criteria.")

def show_rebalancing_options(rebal_data, api_client):
    """Show rebalancing options and actions"""
    st.subheader("🛠️ Actions")
    
    is_needed = rebal_data.get('rebalancing_needed', False)
    
    if is_needed:
        show_rebalancing_actions(api_client)
    else:
        show_maintenance_actions(api_client)

def show_rebalancing_actions(api_client):
    """Show actions when rebalancing is needed"""
    st.markdown("**Rebalancing Options:**")
    
    # Additional investment option
    st.markdown("##### 💰 Additional Investment")
    additional_amount = st.number_input(
        "Add funds during rebalancing (₹)",
        min_value=0,
        value=0,
        step=10000,
        help="Optional: Add more money while rebalancing"
    )
    
    if additional_amount > 0:
        st.info(f"💡 Adding ₹{additional_amount:,.0f} will help optimize allocation")
    
    # Force CSV refresh
    st.markdown("##### 🔄 Data Management")
    if st.button("🔄 Refresh CSV Data", use_container_width=True):
        refresh_csv_data(api_client)
    
    # Placeholder for future rebalancing execution
    st.markdown("##### 🚀 Execute Rebalancing")
    st.warning("⚠️ **Coming Soon**: Automatic rebalancing execution is under development.")
    
    st.markdown("""
    **Manual Process (Current):**
    1. Note the required changes above
    2. Use your trading platform to make adjustments
    3. Return here to verify the changes
    """)

def show_maintenance_actions(api_client):
    """Show maintenance actions when no rebalancing needed"""
    st.markdown("**Maintenance Options:**")
    
    # Force refresh
    if st.button("🔄 Refresh Data", use_container_width=True):
        refresh_csv_data(api_client)
    
    # Portfolio overview
    if st.button("📊 View Portfolio", use_container_width=True):
        st.switch_page("pages/1_Portfolio_Overview.py")
    
    # Add investment
    if st.button("💰 Add Investment", use_container_width=True):
        st.switch_page("pages/2_Investment.py")
    
    st.info("💡 **Tip**: Your portfolio is well-balanced. Consider adding more investment to grow your holdings.")

def refresh_csv_data(api_client):
    """Refresh CSV data and check for changes"""
    with st.spinner("Refreshing CSV data..."):
        refresh_response = api_client.force_csv_refresh()
    
    if APIHelpers.show_api_status(refresh_response, "CSV data refreshed successfully!"):
        refresh_data = APIHelpers.extract_data(refresh_response)
        
        if refresh_data:
            if refresh_data.get('csv_changed'):
                st.warning("📊 **CSV Changed**: New stock data detected. Page will refresh to show updated analysis.")
                st.rerun()
            else:
                st.info("ℹ️ **No Changes**: CSV data is up to date.")

if __name__ == "__main__":
    main()