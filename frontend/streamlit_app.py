import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("📈 Investment Portfolio Manager")
    
    # Test backend connection with Zerodha status
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            health_data = response.json()
            
            # Debug info (you can remove this later)
            st.write("🔧 Debug - Health data:", health_data)
            
            if health_data.get('zerodha_connected'):
                st.markdown('<div class="success-box">✅ Backend connected successfully! 🔗 Zerodha Connected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-box">✅ Backend connected successfully! ⚠️ Zerodha Disconnected - Using Sample Data</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Backend connection failed")
            return
    except Exception as e:
        st.error(f"❌ Cannot connect to backend: {e}")
        return
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Portfolio Overview", "Rebalancing", "Order History", "Settings"]
    )
    
    if page == "Portfolio Overview":
        show_portfolio_overview()
    elif page == "Rebalancing":
        st.header("⚖️ Portfolio Rebalancing")
        st.info("Rebalancing features coming soon!")
    elif page == "Order History":
        st.header("📋 Order History")
        st.info("Order history features coming soon!")
    elif page == "Settings":
        st.header("🔧 Settings")
        st.info("Settings features coming soon!")

def show_portfolio_overview():
    st.header("📊 Portfolio Overview")
    
    # Fetch portfolio data
    try:
        response = requests.get("http://127.0.0.1:8000/api/portfolio/summary/1")
        if response.status_code == 200:
            portfolio_data = response.json()
        else:
            st.error("Failed to fetch portfolio data")
            return
    except Exception as e:
        st.error(f"Error fetching portfolio data: {e}")
        return
    
    # Portfolio metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Current Value",
            f"₹{portfolio_data['current_value']:,.0f}",
            delta=f"₹{portfolio_data['total_returns']:,.0f}"
        )
    
    with col2:
        st.metric(
            "📥 Invested Value",
            f"₹{portfolio_data['invested_value']:,.0f}"
        )
    
    with col3:
        st.metric(
            "📈 Total Returns",
            f"₹{portfolio_data['total_returns']:,.0f}",
            delta=f"{portfolio_data['returns_percentage']:.2f}%"
        )
    
    with col4:
        st.metric(
            "📊 Day Change",
            f"₹{portfolio_data.get('day_change', 0):,.0f}",
            delta=f"{portfolio_data.get('day_change_percent', 0):.2f}%"
        )
    
    # Charts section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Portfolio Performance")
        
        # Fetch performance data
        try:
            perf_response = requests.get("http://127.0.0.1:8000/api/portfolio/performance/1")
            if perf_response.status_code == 200:
                perf_data = perf_response.json()
                perf_df = pd.DataFrame(perf_data['performance_data'])
                
                fig = px.line(
                    perf_df,
                    x='date',
                    y='value',
                    title='Portfolio Value Over Time'
                )
                fig.update_layout(height=400)
                fig.update_traces(line_color='#667eea', line_width=3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Failed to fetch performance data")
        except Exception as e:
            st.error(f"Error fetching performance data: {e}")
    
    with col2:
        st.subheader("🥧 Asset Allocation")
        
        holdings_df = pd.DataFrame(portfolio_data['holdings'])
        
        if not holdings_df.empty:
            fig = px.pie(
                holdings_df,
                values='current_value',
                names='symbol',
                title='Current Allocation'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No holdings data available")
    
    # Holdings table
    st.subheader("📋 Current Holdings")
    
    if not holdings_df.empty:
        # Format holdings data for display
        holdings_df['Current Value'] = holdings_df['current_value'].apply(lambda x: f"₹{x:,.0f}")
        holdings_df['Avg Price'] = holdings_df['avg_price'].apply(lambda x: f"₹{x:.2f}")
        holdings_df['Current Price'] = holdings_df['current_price'].apply(lambda x: f"₹{x:.2f}")
        holdings_df['P&L'] = holdings_df['pnl'].apply(lambda x: f"₹{x:,.0f}")
        holdings_df['P&L %'] = holdings_df['pnl_percent'].apply(lambda x: f"{x:.2f}%")
        holdings_df['Allocation %'] = holdings_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
        
        display_df = holdings_df[['symbol', 'quantity', 'Avg Price', 'Current Price', 'Current Value', 'Allocation %', 'P&L', 'P&L %']]
        display_df.columns = ['Stock', 'Quantity', 'Avg Price', 'Current Price', 'Current Value', 'Allocation %', 'P&L', 'P&L %']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Portfolio insights
        st.subheader("💡 Portfolio Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("🏆 **Top Performers**")
            portfolio_holdings = portfolio_data['holdings']
            if portfolio_holdings:
                # Sort by P&L percentage
                sorted_holdings = sorted(portfolio_holdings, key=lambda x: x['pnl_percent'], reverse=True)
                for i, holding in enumerate(sorted_holdings[:3]):
                    st.write(f"• {holding['symbol']}: +{holding['pnl_percent']:.2f}%")
        
        with col2:
            st.write("⚖️ **Allocation Analysis**")
            allocation_values = [h['allocation_percent'] for h in portfolio_holdings]
            if allocation_values:
                allocation_std = pd.Series(allocation_values).std()
                target_allocation = 100 / len(allocation_values)
                st.write(f"• Target allocation: {target_allocation:.2f}%")
                st.write(f"• Current deviation: {allocation_std:.2f}%")
                
                if allocation_std > 2.0:
                    st.warning("⚠️ Portfolio needs rebalancing")
                else:
                    st.success("✅ Portfolio is well-balanced")
    else:
        st.info("📭 No holdings found.")

if __name__ == "__main__":
    main()