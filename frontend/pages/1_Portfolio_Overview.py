# frontend/pages/1_Portfolio_Overview.py
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
        show_empty_portfolio()
        return
    
    if portfolio_data.get('status') == 'empty':
        show_empty_portfolio()
        return
    elif portfolio_data.get('status') == 'error':
        st.error(f"❌ Portfolio Error: {portfolio_data.get('error', 'Unknown error')}")
        return
    
    # Show portfolio content
    show_portfolio_dashboard(portfolio_data)

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

def show_portfolio_dashboard(portfolio_data):
    """Show main portfolio dashboard"""
    
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

def show_key_metrics(portfolio_data):
    """Display key portfolio metrics"""
    summary = portfolio_data.get('portfolio_summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_value = summary.get('current_value', 0)
        st.metric(
            "💰 Current Value",
            APIHelpers.format_currency(current_value),
            help="Total current value of all holdings"
        )
    
    with col2:
        total_investment = summary.get('total_investment', 0)
        st.metric(
            "📥 Total Invested",
            APIHelpers.format_currency(total_investment),
            help="Total amount invested"
        )
    
    with col3:
        total_returns = summary.get('total_returns', 0)
        returns_pct = summary.get('returns_percentage', 0)
        st.metric(
            "📈 Total Returns",
            APIHelpers.format_currency(total_returns),
            delta=APIHelpers.format_percentage(returns_pct),
            help="Absolute and percentage returns"
        )
    
    with col4:
        stock_count = summary.get('stock_count', 0)
        if 'cagr' in summary:
            st.metric(
                "📊 CAGR",
                f"{summary['cagr']:.2f}%",
                delta=f"{stock_count} stocks",
                help="Compound Annual Growth Rate"
            )
        else:
            st.metric(
                "📊 Holdings",
                f"{stock_count} stocks",
                help="Number of stocks in portfolio"
            )

def show_holdings_table(portfolio_data):
    """Display holdings table"""
    st.subheader("📋 Current Holdings")
    
    holdings = portfolio_data.get('holdings', {})
    
    if not holdings:
        st.info("No holdings data available")
        return
    
    # Convert to DataFrame
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
    
    if df.empty:
        st.info("No holdings data to display")
        return
    
    # Format for display
    display_df = df.copy()
    display_df['avg_price'] = display_df['avg_price'].apply(lambda x: f"₹{x:.2f}")
    display_df['current_price'] = display_df['current_price'].apply(lambda x: f"₹{x:.2f}")
    display_df['investment_value'] = display_df['investment_value'].apply(lambda x: f"₹{x:,.0f}")
    display_df['current_value'] = display_df['current_value'].apply(lambda x: f"₹{x:,.0f}")
    display_df['pnl'] = display_df['pnl'].apply(lambda x: f"₹{x:,.0f}")
    display_df['allocation_percent'] = display_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
    
    # Rename columns
    display_df = display_df.rename(columns={
        'symbol': 'Stock',
        'shares': 'Shares',
        'avg_price': 'Avg Price',
        'current_price': 'Current Price',
        'investment_value': 'Invested',
        'current_value': 'Current Value',
        'pnl': 'P&L (₹)',
        'pnl_percent': 'P&L (%)',
        'allocation_percent': 'Allocation'
    })
    
    # Show table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

def show_allocation_chart(portfolio_data):
    """Display allocation pie chart"""
    st.subheader("🥧 Allocation")
    
    holdings = portfolio_data.get('holdings', {})
    
    if not holdings:
        st.info("No allocation data available")
        return
    
    # Prepare data for pie chart
    symbols = list(holdings.keys())
    values = [holding.get('current_value', 0) for holding in holdings.values()]
    
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

def show_performance_summary(portfolio_data):
    """Display performance summary"""
    st.subheader("📈 Performance")
    
    performance = portfolio_data.get('performance_metrics', {})
    summary = portfolio_data.get('portfolio_summary', {})
    
    if not performance:
        # Show basic performance from summary
        returns_pct = summary.get('returns_percentage', 0)
        if returns_pct > 0:
            st.success(f"📈 Portfolio is up {returns_pct:.2f}%")
        elif returns_pct < 0:
            st.error(f"📉 Portfolio is down {abs(returns_pct):.2f}%")
        else:
            st.info("📊 Portfolio is flat")
        return
    
    # Best and worst performers
    best = performance.get('best_performer', {})
    worst = performance.get('worst_performer', {})
    
    if best:
        st.metric(
            "🏆 Best Performer",
            best.get('symbol', 'N/A'),
            delta=f"{best.get('percentage_return', 0):.2f}%"
        )
    
    if worst:
        st.metric(
            "📉 Worst Performer", 
            worst.get('symbol', 'N/A'),
            delta=f"{worst.get('percentage_return', 0):.2f}%"
        )
    
    # Risk metrics
    volatility = performance.get('volatility_score', 0)
    sharpe = performance.get('sharpe_ratio', 0)
    
    if volatility > 0:
        st.metric("📊 Volatility", f"{volatility:.2f}%")
    
    if sharpe != 0:
        st.metric("📈 Sharpe Ratio", f"{sharpe:.2f}")

def show_portfolio_insights(portfolio_data):
    """Display portfolio insights and recommendations"""
    st.subheader("💡 Portfolio Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Allocation Analysis")
        
        allocation_analysis = portfolio_data.get('allocation_analysis', {})
        
        if allocation_analysis.get('rebalancing_needed'):
            st.warning("⚖️ **Rebalancing Recommended**")
            st.markdown("Your portfolio allocation has drifted from targets.")
            if st.button("➡️ Go to Rebalancing", key="rebal_btn"):
                st.switch_page("pages/3_Rebalancing.py")
        else:
            st.success("✅ **Well Balanced**")
            st.markdown("Your portfolio allocation is within target ranges.")
    
    with col2:
        st.markdown("#### 📈 Performance Insights")
        
        summary = portfolio_data.get('portfolio_summary', {})
        returns_pct = summary.get('returns_percentage', 0)
        
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

if __name__ == "__main__":
    main()