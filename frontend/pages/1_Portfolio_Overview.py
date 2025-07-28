# frontend/pages/1_Portfolio_Overview.py - COMPLETE FIXED VERSION
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from api_client import APIClient, APIHelpers
from session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="Portfolio Overview",
    page_icon="📊",
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
    st.title("📊 Portfolio Overview")
    st.markdown("Your complete portfolio status and performance metrics")
    
    # Load portfolio data
    with st.spinner("Loading portfolio data..."):
        portfolio_response = api_client.get_portfolio_status()
    
    portfolio_data = APIHelpers.extract_data(portfolio_response)
    
    if not portfolio_data:
        st.error("❌ Unable to load portfolio data")
        show_connection_troubleshooting()
        return
    
    # Handle different portfolio states
    portfolio_status = portfolio_data.get('status', 'unknown')
    
    if portfolio_status == 'empty':
        show_empty_portfolio()
        return
    elif portfolio_status in ['error', 'price_data_unavailable', 'calculation_error']:
        show_portfolio_error(portfolio_data, portfolio_status)
        return
    elif portfolio_status == 'active':
        show_portfolio_dashboard(portfolio_data)
    else:
        st.warning(f"⚠️ Unknown portfolio status: {portfolio_status}")
        show_raw_portfolio_data(portfolio_data)

def show_empty_portfolio():
    """Show empty portfolio state"""
    st.info("📭 No portfolio found")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### 🚀 Get Started
        
        You don't have an active portfolio yet. To get started:
        
        1. **Go to Investment page** to create your first portfolio
        2. **Check minimum requirements** for initial investment
        3. **Calculate and execute** your investment plan
        
        Your portfolio will appear here once you complete your first investment.
        """)
        
        if st.button("➡️ Go to Investment Page", use_container_width=True):
            st.switch_page("pages/2_Investment.py")

def show_portfolio_error(portfolio_data, status):
    """Show portfolio error states"""
    error_message = portfolio_data.get('error', 'Unknown error occurred')
    
    if status == 'price_data_unavailable':
        st.error("🚫 **Portfolio Value Cannot Be Calculated**")
        
        st.markdown(f"""
        **Issue**: {error_message}
        
        **Why This Happens**: 
        - Live price data is required to calculate current portfolio values
        - The system cannot show accurate portfolio metrics without real-time prices
        - This ensures you always see correct, up-to-date information
        """)
        
        # Show what data is available
        data_quality = portfolio_data.get('data_quality', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔍 System Status")
            
            if data_quality.get('zerodha_connected', False):
                st.success("✅ Zerodha service available")
            else:
                st.error("❌ Zerodha not connected")
            
            # Show basic portfolio info if available
            portfolio_summary = portfolio_data.get('portfolio_summary', {})
            stock_count = portfolio_summary.get('stock_count', 0)
            if stock_count > 0:
                st.info(f"📊 Portfolio has {stock_count} holdings")
        
        with col2:
            st.markdown("#### 🛠️ Solutions")
            
            st.markdown("""
            **Steps to Resolve**:
            1. Ensure Zerodha is properly authenticated
            2. Check if market is open (9:15 AM - 3:30 PM)
            3. Verify internet connection
            4. Try refreshing the data
            """)
        
        # Retry button
        if st.button("🔄 Refresh Portfolio Data", type="primary", use_container_width=True):
            st.rerun()
    
    elif status == 'calculation_error':
        st.error("❌ **Portfolio Calculation Error**")
        st.markdown(f"**Details**: {error_message}")
        
        if st.button("🔄 Retry Calculation", use_container_width=True):
            st.rerun()
    
    else:
        st.error("❌ **Portfolio Error**")
        st.markdown(f"**Status**: {status}")
        st.markdown(f"**Details**: {error_message}")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

def show_connection_troubleshooting():
    """Show connection troubleshooting information"""
    st.markdown("""
    ### 🔧 Troubleshooting
    
    **If you're seeing this error:**
    1. Check if the backend server is running
    2. Verify the API endpoint is accessible
    3. Check your network connection
    4. Try refreshing the page
    
    **Need Help?**
    - Check the browser console for detailed error messages
    - Ensure all services are properly configured
    """)

def show_portfolio_dashboard(portfolio_data):
    """Show main portfolio dashboard with error handling"""
    try:
        # Key metrics row
        show_key_metrics(portfolio_data)
        
        st.markdown("---")
        
        # Main content in two columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            show_holdings_table(portfolio_data)
        
        with col2:
            show_allocation_chart(portfolio_data)
            show_performance_summary(portfolio_data)
        
        # Additional insights
        st.markdown("---")
        show_portfolio_insights(portfolio_data)
    
    except Exception as e:
        st.error(f"❌ Error displaying portfolio dashboard: {str(e)}")
        st.markdown("**Debug Information:**")
        st.json(portfolio_data)

def show_key_metrics(portfolio_data):
    """Display key portfolio metrics with error handling"""
    summary = portfolio_data.get('portfolio_summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_value = summary.get('current_value', 0)
        try:
            current_value = float(current_value) if current_value is not None else 0
        except (TypeError, ValueError):
            current_value = 0
        
        st.metric(
            "💰 Current Value",
            APIHelpers.format_currency(current_value),
            help="Total current value of all holdings"
        )
    
    with col2:
        total_investment = summary.get('total_investment', 0)
        try:
            total_investment = float(total_investment) if total_investment is not None else 0
        except (TypeError, ValueError):
            total_investment = 0
        
        st.metric(
            "📥 Total Invested",
            APIHelpers.format_currency(total_investment),
            help="Total amount invested"
        )
    
    with col3:
        total_returns = summary.get('total_returns', 0)
        returns_pct = summary.get('returns_percentage', 0)
        
        try:
            total_returns = float(total_returns) if total_returns is not None else 0
            returns_pct = float(returns_pct) if returns_pct is not None else 0
        except (TypeError, ValueError):
            total_returns = 0
            returns_pct = 0
        
        st.metric(
            "📈 Total Returns",
            APIHelpers.format_currency(total_returns),
            delta=APIHelpers.format_percentage(returns_pct),
            help="Absolute and percentage returns"
        )
    
    with col4:
        stock_count = summary.get('stock_count', 0)
        cagr = summary.get('cagr')
        
        try:
            stock_count = int(stock_count) if stock_count is not None else 0
        except (TypeError, ValueError):
            stock_count = 0
        
        if cagr is not None:
            try:
                cagr = float(cagr)
                st.metric(
                    "📊 CAGR",
                    f"{cagr:.2f}%",
                    delta=f"{stock_count} stocks",
                    help="Compound Annual Growth Rate"
                )
            except (TypeError, ValueError):
                st.metric(
                    "📊 Holdings",
                    f"{stock_count} stocks",
                    help="Number of stocks in portfolio"
                )
        else:
            st.metric(
                "📊 Holdings",
                f"{stock_count} stocks",
                help="Number of stocks in portfolio"
            )

def show_holdings_table(portfolio_data):
    """Display holdings table with comprehensive error handling"""
    st.subheader("📋 Current Holdings")
    
    holdings = portfolio_data.get('holdings', {})
    
    if not holdings:
        st.info("No holdings data available")
        return
    
    try:
        # Convert to DataFrame with error handling
        holdings_list = []
        for symbol, holding in holdings.items():
            try:
                holding_data = {
                    'symbol': str(symbol),
                    'shares': safe_numeric(holding.get('shares', 0)),
                    'avg_price': safe_numeric(holding.get('avg_price', 0)),
                    'current_price': safe_numeric(holding.get('current_price', 0)),
                    'investment_value': safe_numeric(holding.get('investment_value', 0)),
                    'current_value': safe_numeric(holding.get('current_value', 0)),
                    'pnl': safe_numeric(holding.get('pnl', 0)),
                    'pnl_percent': safe_numeric(holding.get('pnl_percent', 0)),
                    'allocation_percent': safe_numeric(holding.get('allocation_percent', 0))
                }
                holdings_list.append(holding_data)
            except Exception as e:
                st.warning(f"⚠️ Error processing holding {symbol}: {str(e)}")
                continue
        
        if not holdings_list:
            st.info("No valid holdings data to display")
            return
        
        df = pd.DataFrame(holdings_list)
        
        # Format for display with error handling
        display_df = df.copy()
        
        # Safe formatting
        display_df['avg_price_fmt'] = display_df['avg_price'].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) else "₹0.00")
        display_df['current_price_fmt'] = display_df['current_price'].apply(lambda x: f"₹{x:.2f}" if pd.notnull(x) else "₹0.00")
        display_df['investment_value_fmt'] = display_df['investment_value'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "₹0")
        display_df['current_value_fmt'] = display_df['current_value'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "₹0")
        display_df['pnl_fmt'] = display_df['pnl'].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "₹0")
        display_df['allocation_fmt'] = display_df['allocation_percent'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "0.00%")
        
        # Rename columns
        display_df = display_df.rename(columns={
            'symbol': 'Stock',
            'shares': 'Shares',
            'avg_price_fmt': 'Avg Price',
            'current_price_fmt': 'Current Price',
            'investment_value_fmt': 'Invested',
            'current_value_fmt': 'Current Value',
            'pnl_fmt': 'P&L (₹)',
            'pnl_percent': 'P&L (%)',
            'allocation_fmt': 'Allocation'
        })
        
        # Select columns for display
        display_columns = ['Stock', 'Shares', 'Avg Price', 'Current Price', 'Invested', 'Current Value', 'P&L (₹)', 'P&L (%)', 'Allocation']
        available_columns = [col for col in display_columns if col in display_df.columns]
        
        # Show table
        st.dataframe(
            display_df[available_columns],
            use_container_width=True,
            hide_index=True
        )
    
    except Exception as e:
        st.error(f"❌ Error displaying holdings table: {str(e)}")
        # Fallback: show raw data
        with st.expander("Raw Holdings Data (Debug)"):
            st.json(holdings)

def show_allocation_chart(portfolio_data):
    """Display allocation pie chart with error handling"""
    st.subheader("🥧 Allocation")
    
    holdings = portfolio_data.get('holdings', {})
    
    if not holdings:
        st.info("No allocation data available")
        return
    
    try:
        # Prepare data for pie chart with error handling
        symbols = []
        values = []
        
        for symbol, holding in holdings.items():
            try:
                current_value = safe_numeric(holding.get('current_value', 0))
                if current_value > 0:
                    symbols.append(str(symbol))
                    values.append(current_value)
            except Exception as e:
                st.warning(f"⚠️ Error processing {symbol} for chart: {str(e)}")
                continue
        
        if not symbols or not values:
            st.info("No valid data for allocation chart")
            return
        
        # Create pie chart
        fig = px.pie(
            values=values,
            names=symbols,
            title="Portfolio Allocation by Value"
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Value: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error creating allocation chart: {str(e)}")
        st.info("📊 Chart temporarily unavailable - data shown in table above")

def show_performance_summary(portfolio_data):
    """Display performance summary with error handling"""
    st.subheader("📈 Performance")
    
    performance = portfolio_data.get('performance_metrics', {})
    summary = portfolio_data.get('portfolio_summary', {})
    
    if not performance:
        # Show basic performance from summary
        try:
            returns_pct = safe_numeric(summary.get('returns_percentage', 0))
            if returns_pct > 0:
                st.success(f"📈 Portfolio is up {returns_pct:.2f}%")
            elif returns_pct < 0:
                st.error(f"📉 Portfolio is down {abs(returns_pct):.2f}%")
            else:
                st.info("📊 Portfolio is flat")
        except Exception:
            st.info("📊 Performance data unavailable")
        return
    
    try:
        # Best and worst performers
        best = performance.get('best_performer', {})
        worst = performance.get('worst_performer', {})
        
        if best and best.get('symbol'):
            best_return = safe_numeric(best.get('percentage_return', 0))
            st.metric(
                "🏆 Best Performer",
                best.get('symbol', 'N/A'),
                delta=f"{best_return:.2f}%"
            )
        
        if worst and worst.get('symbol'):
            worst_return = safe_numeric(worst.get('percentage_return', 0))
            st.metric(
                "📉 Worst Performer", 
                worst.get('symbol', 'N/A'),
                delta=f"{worst_return:.2f}%"
            )
        
        # Risk metrics
        volatility = safe_numeric(performance.get('volatility_score', 0))
        sharpe = safe_numeric(performance.get('sharpe_ratio', 0))
        
        if volatility > 0:
            st.metric("📊 Volatility", f"{volatility:.2f}%")
        
        if sharpe != 0:
            st.metric("📈 Sharpe Ratio", f"{sharpe:.2f}")
    
    except Exception as e:
        st.error(f"❌ Error displaying performance metrics: {str(e)}")

def show_portfolio_insights(portfolio_data):
    """Display portfolio insights and recommendations with error handling"""
    st.subheader("💡 Portfolio Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Allocation Analysis")
        
        try:
            allocation_analysis = portfolio_data.get('allocation_analysis', {})
            
            if allocation_analysis.get('rebalancing_needed'):
                st.warning("⚖️ **Rebalancing Recommended**")
                st.markdown("Your portfolio allocation has drifted from targets.")
                if st.button("➡️ Go to Rebalancing", key="rebal_btn"):
                    st.switch_page("pages/3_Rebalancing.py")
            else:
                st.success("✅ **Well Balanced**")
                st.markdown("Your portfolio allocation is within target ranges.")
        except Exception as e:
            st.info("📊 Allocation analysis temporarily unavailable")
    
    with col2:
        st.markdown("#### 📈 Performance Insights")
        
        try:
            summary = portfolio_data.get('portfolio_summary', {})
            returns_pct = safe_numeric(summary.get('returns_percentage', 0))
            
            if returns_pct > 10:
                st.success("🚀 **Strong Performance**")
                st.markdown("Your portfolio is significantly outperforming.")
            elif returns_pct > 0:
                st.info("📈 **Positive Returns**")
                st.markdown("Your portfolio is generating positive returns.")
            elif returns_pct < -10:
                st.error("📉 **Significant Decline**")
                st.markdown("Consider reviewing your investment strategy.")
            else:
                st.info("📊 **Stable Performance**")
                st.markdown("Your portfolio is performing within normal ranges.")
        except Exception as e:
            st.info("📈 Performance insights temporarily unavailable")

def show_raw_portfolio_data(portfolio_data):
    """Show raw portfolio data for debugging"""
    st.subheader("🔧 Debug Information")
    st.markdown("Raw portfolio data (for troubleshooting):")
    
    with st.expander("View Raw Data"):
        st.json(portfolio_data)
    
    st.markdown("**If you see this consistently, please contact system administrator.**")

def safe_numeric(value, default=0):
    """Safely convert value to numeric type"""
    if value is None:
        return default
    
    try:
        # Try to convert to float first
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('₹', '').replace(',', '').strip()
            return float(cleaned)
        else:
            return default
    except (ValueError, TypeError):
        return default

if __name__ == "__main__":
    main()