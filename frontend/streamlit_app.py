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
</style>
""", unsafe_allow_html=True)

# API Configuration
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
                st.markdown('<div class="success-alert">✅ Backend connected! 🔗 Zerodha Connected</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-alert">✅ Backend connected! ⚠️ Zerodha using sample data</div>', unsafe_allow_html=True)
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
    st.subheader("📈 Current CSV Stocks")
    
    stocks_df = pd.DataFrame(requirements['stocks_data']['stocks'])
    
    # Format the display - use actual data from API
    display_df = pd.DataFrame({
        'Stock Symbol': stocks_df['symbol'],
        'Current Price': stocks_df['price'].apply(lambda x: f"₹{x:,.2f}"),
        'Min Investment (4%)': (stocks_df['price'] * 25).apply(lambda x: f"₹{x:,.0f}"),
        'Momentum Score': stocks_df['score'].apply(lambda x: f"{x:.2f}")
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
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
                    
                    st.markdown('<div class="success-alert">✅ <strong>Investment Complete!</strong><br>Your orders have been recorded in the system. You can now monitor your portfolio and check for rebalancing needs.</div>', unsafe_allow_html=True)
                    
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
                    st.markdown('<div class="warning-alert">⚖️ <strong>Rebalancing Needed!</strong><br>Your portfolio needs rebalancing due to CSV changes.</div>', unsafe_allow_html=True)
                    
                    # Show rebalancing interface
                    show_rebalancing_interface(rebalancing_info)
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

def show_rebalancing_interface(rebalancing_info):
    """Show rebalancing interface"""
    comparison = rebalancing_info['comparison']
    
    # Portfolio transition summary
    st.subheader("📊 Portfolio Transition")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        current_stocks = len(comparison['portfolio_stocks'])
        st.metric("📊 Current Stocks", current_stocks)
    
    with col2:
        new_stocks_count = len(comparison['new_stocks'])
        st.metric("📈 New Stocks", new_stocks_count, delta=f"+{new_stocks_count}")
    
    with col3:
        removed_stocks_count = len(comparison['removed_stocks'])
        st.metric("📉 Stocks to Exit", removed_stocks_count, delta=f"-{removed_stocks_count}")
    
    # Stock changes
    if comparison['new_stocks'] or comparison['removed_stocks']:
        col1, col2 = st.columns(2)
        
        with col1:
            if comparison['new_stocks']:
                st.write("### 🟢 **Stocks to ADD**")
                for stock in comparison['new_stocks']:
                    st.write(f"• **{stock}**")
        
        with col2:
            if comparison['removed_stocks']:
                st.write("### 🔴 **Stocks to SELL**")
                for stock in comparison['removed_stocks']:
                    st.write(f"• **{stock}**")
    
    # Additional investment section
    st.subheader("💰 Additional Investment (Optional)")
    
    additional_investment = st.number_input(
        "Add more funds during rebalancing (₹)",
        min_value=0,
        value=0,
        step=25000,
        help="Optional: Add more money to invest along with rebalancing"
    )
    
    # Calculate button
    if st.button("🧮 Calculate Rebalancing Plan", type="primary", use_container_width=True):
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
                # Implementation would be similar to show_investment_plan()
            else:
                st.error(f"Calculation failed: {plan_data.get('detail', 'Unknown error')}")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error calculating rebalancing: {e}")

def show_portfolio_status():
    """Enhanced portfolio status with beautiful visualizations - FIXED VERSION"""
    st.header("📊 Portfolio Status")
    
    try:
        response = requests.get(f"{API_BASE_URL}/investment/portfolio-status", timeout=30)
        if response.status_code == 200:
            status_data = response.json()
            if status_data['success']:
                status = status_data['data']
                
                if status['status'] == 'empty':
                    st.info("📭 No portfolio found. Please complete initial investment first.")
                    if st.button("🚀 Go to Initial Investment"):
                        st.rerun()
                    return
                elif status['status'] == 'error':
                    st.error(f"❌ Error loading portfolio: {status.get('error', 'Unknown error')}")
                    return
                
                # Extract data with better error handling
                portfolio_summary = status.get('portfolio_summary', {})
                performance_metrics = status.get('performance_metrics', {})
                allocation_analysis = status.get('allocation_analysis', {})
                holdings = status.get('holdings', {})
                timeline = status.get('timeline', {})
                
                # Portfolio Header with Key Metrics
                show_portfolio_header(portfolio_summary, performance_metrics, timeline)
                
                # Portfolio Performance Charts
                show_performance_section(holdings, portfolio_summary, performance_metrics)
                
                # Holdings Heatmap - FIXED VERSION
                show_holdings_heatmap_fixed(holdings)
                
                # Detailed Holdings Table
                show_detailed_holdings_table_fixed(holdings)
                
                # Advanced Analytics
                show_advanced_analytics(allocation_analysis, performance_metrics, timeline)
                
            else:
                st.error("Failed to get portfolio status")
        else:
            st.error(f"API Error: {response.status_code}")
            
    except Exception as e:
        st.error(f"Error fetching portfolio status: {e}")

def show_portfolio_header(portfolio_summary, performance_metrics, timeline):
    """Show portfolio header with key metrics"""
    
    # Main metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_value = portfolio_summary.get('current_value', 0)
        st.metric(
            "💰 Portfolio Value",
            f"₹{current_value:,.0f}",
            help="Current market value of all holdings"
        )
    
    with col2:
        total_returns = portfolio_summary.get('total_returns', 0)
        returns_percentage = portfolio_summary.get('returns_percentage', 0)
        st.metric(
            "📈 Total Returns",
            f"₹{total_returns:,.0f}",
            delta=f"{returns_percentage:.2f}%",
            help="Absolute returns since inception"
        )
    
    with col3:
        cagr = portfolio_summary.get('cagr', 0)
        delta_color = "normal" if cagr >= 0 else "inverse"
        st.metric(
            "🎯 CAGR",
            f"{cagr:.2f}%",
            delta=f"vs 6% risk-free",
            delta_color=delta_color,
            help="Compound Annual Growth Rate"
        )
    
    with col4:
        investment_period = portfolio_summary.get('investment_period_days', 0)
        investment_years = portfolio_summary.get('investment_period_years', 0)
        st.metric(
            "⏱️ Investment Period",
            f"{investment_period} days",
            delta=f"{investment_years:.1f} years",
            help="Time since first investment"
        )
    
    with col5:
        sharpe_ratio = performance_metrics.get('sharpe_ratio', 0)
        st.metric(
            "📊 Sharpe Ratio",
            f"{sharpe_ratio:.2f}",
            help="Risk-adjusted returns"
        )

def show_performance_section(holdings, portfolio_summary, performance_metrics):
    """Show performance charts and analysis"""
    
    st.subheader("📈 Performance Analysis")
    
    if not holdings:
        st.info("No holdings data available for performance analysis")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Returns comparison chart
        holdings_data = []
        for symbol, holding in holdings.items():
            try:
                holdings_data.append({
                    'Stock': str(symbol),
                    'Current Value': float(holding.get('current_value', 0)),
                    'Investment': float(holding.get('investment_value', 0)),
                    'Return %': float(holding.get('percentage_return', 0)),
                    'CAGR %': float(holding.get('annualized_return', 0)),
                    'Days Held': int(holding.get('days_held', 1))
                })
            except (ValueError, TypeError):
                continue
        
        if holdings_data:
            holdings_df = pd.DataFrame(holdings_data)
            
            # Performance bar chart
            fig = px.bar(
                holdings_df,
                x='Stock',
                y='Return %',
                title='Individual Stock Returns (%)',
                color='Return %',
                color_continuous_scale='RdYlGn',
                text='Return %'
            )
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                height=400,
                xaxis_title="Stocks",
                yaxis_title="Returns (%)",
                showlegend=False
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid performance data available")
    
    with col2:
        st.subheader("🥧 Asset Allocation")
        
        if holdings_data:
            # Portfolio composition pie chart
            fig = px.pie(
                holdings_df,
                values='Current Value',
                names='Stock',
                title='Portfolio Composition'
            )
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Value: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No allocation data available")

def show_holdings_heatmap_fixed(holdings):
    """Show beautiful holdings heatmap - COMPLETELY FIXED VERSION"""
    
    st.subheader("🔥 Holdings Heatmap")
    
    if not holdings:
        st.info("No holdings data available for heatmap")
        return
    
    # Prepare data for heatmap
    heatmap_data = []
    for symbol, holding in holdings.items():
        try:
            heatmap_data.append({
                'Stock': str(symbol),
                'Value': float(holding.get('current_value', 0)),
                'Return %': float(holding.get('percentage_return', 0)),
                'CAGR %': float(holding.get('annualized_return', 0)),
                'Days Held': int(holding.get('days_held', 1)),
                'Allocation %': float(holding.get('allocation_percent', 0))
            })
        except (ValueError, TypeError) as e:
            print(f"Error processing holding {symbol}: {e}")
            continue
    
    if not heatmap_data:
        st.info("No valid holdings data for heatmap visualization")
        return
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Create treemap for holdings with error handling
    try:
        fig = px.treemap(
            heatmap_df,
            path=['Stock'],
            values='Value',
            color='Return %',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            hover_data={
                'Value': ':,.0f',
                'Return %': ':.2f',
                'CAGR %': ':.2f',
                'Days Held': True,
                'Allocation %': ':.2f'
            }
        )
        
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>₹%{value:,.0f}<br>%{color:.1f}%",
            textposition="middle center",
            textfont_size=12
        )
        
        # COMPLETELY FIXED: Use only basic layout without colorbar customization
        fig.update_layout(
            title="Holdings Treemap (Size = Value, Color = Returns)",
            height=500,
            font=dict(size=14)
            # Removed all coloraxis_colorbar configurations
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating treemap: {e}")
        # Show alternative visualization
        show_alternative_holdings_chart(heatmap_df)
    
    # Additional performance matrix
    if len(heatmap_df) > 1:
        st.subheader("📊 Performance Matrix")
        
        try:
            # Create scatter plot matrix
            fig = px.scatter(
                heatmap_df,
                x='Days Held',
                y='Return %',
                size='Value',
                color='CAGR %',
                hover_name='Stock',
                color_continuous_scale='RdYlGn',
                size_max=60
            )
            
            fig.update_layout(
                title='Risk-Return Analysis (Bubble Size = Investment Value)',
                height=400,
                xaxis_title="Days Held",
                yaxis_title="Total Return (%)"
                # Removed coloraxis_colorbar configuration
            )
            
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating performance matrix: {e}")
            # Show simple bar chart as fallback
            fig = px.bar(
                heatmap_df,
                x='Stock',
                y='Return %',
                title='Stock Returns (%)',
                color='Return %',
                color_continuous_scale='RdYlGn'
            )
            # No colorbar customization for bar chart either
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 2 holdings for performance matrix visualization")

def show_alternative_holdings_chart(heatmap_df):
    """Alternative chart when treemap fails - SIMPLIFIED VERSION"""
    st.subheader("📊 Holdings Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Simple pie chart
        fig = px.pie(
            heatmap_df,
            values='Value',
            names='Stock',
            title='Portfolio Allocation by Value'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Bar chart of returns - simplified without colorbar customization
        fig = px.bar(
            heatmap_df,
            x='Stock',
            y='Return %',
            title='Returns by Stock',
            color='Return %',
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

def show_detailed_holdings_table_fixed(holdings):
    """Show detailed holdings table with enhanced formatting - FIXED VERSION"""
    
    st.subheader("📋 Detailed Holdings")
    
    if not holdings:
        st.info("No holdings data available")
        return
    
    # Prepare detailed table data with better error handling
    table_data = []
    for symbol, holding in holdings.items():
        try:
            # Safely extract values with defaults
            shares = int(holding.get('shares', 0))
            avg_price = float(holding.get('avg_price', 0))
            current_price = float(holding.get('current_price', 0))
            investment_value = float(holding.get('investment_value', 0))
            current_value = float(holding.get('current_value', 0))
            absolute_return = float(holding.get('absolute_return', 0))
            percentage_return = float(holding.get('percentage_return', 0))
            allocation_percent = float(holding.get('allocation_percent', 0))
            days_held = int(holding.get('days_held', 1))
            annualized_return = float(holding.get('annualized_return', 0))
            first_purchase = str(holding.get('first_purchase_date', ''))[:10]
            transaction_count = int(holding.get('transaction_count', 0))
            
            table_data.append({
                'Stock': str(symbol),
                'Shares': f"{shares:,}",
                'Avg Price': f"₹{avg_price:,.2f}",
                'Current Price': f"₹{current_price:,.2f}",
                'Investment': f"₹{investment_value:,.0f}",
                'Current Value': f"₹{current_value:,.0f}",
                'Absolute P&L': f"₹{absolute_return:,.0f}",
                'Return %': f"{percentage_return:.2f}%",
                'CAGR %': f"{annualized_return:.2f}%",
                'Allocation %': f"{allocation_percent:.2f}%",
                'Days Held': days_held,
                'First Purchase': first_purchase if first_purchase != '' else 'N/A',
                'Transactions': transaction_count
            })
            
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error processing holding {symbol} for table: {e}")
            # Add a safe fallback row
            table_data.append({
                'Stock': str(symbol),
                'Shares': 'Error',
                'Avg Price': 'Error',
                'Current Price': 'Error',
                'Investment': 'Error',
                'Current Value': 'Error',
                'Absolute P&L': 'Error',
                'Return %': 'Error',
                'CAGR %': 'Error',
                'Allocation %': 'Error',
                'Days Held': 'Error',
                'First Purchase': 'Error',
                'Transactions': 'Error'
            })
    
    if not table_data:
        st.warning("No valid holdings data to display")
        return
    
    table_df = pd.DataFrame(table_data)
    
    # Display table with custom styling
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Return %': st.column_config.TextColumn('Return %', help="Total percentage return"),
            'CAGR %': st.column_config.TextColumn('CAGR %', help="Compound Annual Growth Rate"),
            'Allocation %': st.column_config.TextColumn('Allocation %', help="Portfolio allocation percentage")
        }
    )
    
    # Summary statistics with error handling
    try:
        # Calculate summary stats from valid holdings only
        valid_returns = []
        valid_cagrs = []
        valid_holding_periods = []
        
        for holding in holdings.values():
            try:
                ret = float(holding.get('percentage_return', 0))
                cagr = float(holding.get('annualized_return', 0))
                days = int(holding.get('days_held', 1))
                
                valid_returns.append(ret)
                valid_cagrs.append(cagr)
                valid_holding_periods.append(days)
            except (ValueError, TypeError):
                continue
        
        if valid_returns:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_return = sum(valid_returns) / len(valid_returns)
                st.metric("📊 Average Return", f"{avg_return:.2f}%")
            
            with col2:
                avg_cagr = sum(valid_cagrs) / len(valid_cagrs)
                st.metric("🎯 Average CAGR", f"{avg_cagr:.2f}%")
            
            with col3:
                positive_returns = sum(1 for ret in valid_returns if ret > 0)
                win_rate = (positive_returns / len(valid_returns)) * 100
                st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
            
            with col4:
                avg_holding_period = sum(valid_holding_periods) / len(valid_holding_periods)
                st.metric("⏱️ Avg Holding Period", f"{avg_holding_period:.0f} days")
        
    except Exception as e:
        st.warning(f"Could not calculate summary statistics: {e}")

def show_advanced_analytics(allocation_analysis, performance_metrics, timeline):
    """Show advanced analytics section"""
    
    st.subheader("🧠 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ⚖️ Allocation Analysis")
        
        allocation_stats = allocation_analysis.get('allocation_stats', {})
        st.write(f"**Target Allocation**: {allocation_stats.get('target_allocation', 0):.2f}%")
        st.write(f"**Current Range**: {allocation_stats.get('min_allocation', 0):.2f}% - {allocation_stats.get('max_allocation', 0):.2f}%")
        st.write(f"**Average Allocation**: {allocation_stats.get('avg_allocation', 0):.2f}%")
        st.write(f"**Deviation Score**: {allocation_analysis.get('allocation_deviation', 0):.2f}%")
        
        if allocation_analysis.get('rebalancing_needed', False):
            st.warning("⚠️ Portfolio may need rebalancing")
        else:
            st.success("✅ Portfolio allocation is balanced")
        
        st.write("### 📊 Risk Metrics")
        st.write(f"**Volatility**: {performance_metrics.get('volatility_score', 0):.2f}%")
        st.write(f"**Sharpe Ratio**: {performance_metrics.get('sharpe_ratio', 0):.2f}")
        
        # Risk assessment
        volatility = performance_metrics.get('volatility_score', 0)
        if volatility < 10:
            risk_level = "🟢 Low Risk"
        elif volatility < 20:
            risk_level = "🟡 Medium Risk"
        else:
            risk_level = "🔴 High Risk"
        
        st.write(f"**Risk Level**: {risk_level}")
    
    with col2:
        st.write("### 📅 Investment Timeline")
        
        first_investment = timeline.get('first_investment', 'N/A')
        last_investment = timeline.get('last_investment', 'N/A')
        total_orders = timeline.get('total_orders', 0)
        last_updated = timeline.get('last_updated', 'N/A')
        
        st.write(f"**First Investment**: {first_investment[:10] if first_investment != 'N/A' else 'N/A'}")
        st.write(f"**Last Investment**: {last_investment[:10] if last_investment != 'N/A' else 'N/A'}")
        st.write(f"**Total Orders**: {total_orders}")
        st.write(f"**Last Updated**: {last_updated[:10] if last_updated != 'N/A' else 'N/A'}")
        
        st.write("### 🎯 Performance Benchmarks")
        
        # Get CAGR from performance metrics
        portfolio_cagr = performance_metrics.get('avg_return', 0)
        
        # Benchmark comparisons
        benchmarks = {
            "Fixed Deposit": 6.5,
            "Nifty 50 (Est.)": 12.0,
            "Small Cap Index": 15.0
        }
        
        for benchmark, rate in benchmarks.items():
            if portfolio_cagr > rate:
                st.success(f"✅ Outperforming {benchmark} ({rate}%)")
            else:
                st.error(f"❌ Underperforming {benchmark} ({rate}%)")

def show_order_history():
    """Order history page"""
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

if __name__ == "__main__":
    main()