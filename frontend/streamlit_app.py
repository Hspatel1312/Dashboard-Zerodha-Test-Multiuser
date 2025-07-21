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
        st.markdown('<div class="error-box">❌ Amount below minimum required!</div>', unsafe_allow_html=True)
    elif investment_amount < recommended:
        st.markdown('<div class="warning-box">⚠️ Consider recommended amount for better allocation</div>', unsafe_allow_html=True)
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
    """Show improved rebalancing interface"""
    comparison = rebalancing_info['comparison']
    
    # Main rebalancing status
    st.markdown('<div class="warning-box">⚖️ <strong>Rebalancing Required</strong><br>Your portfolio needs adjustment due to CSV changes.</div>', unsafe_allow_html=True)
    
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
    
    # Stock changes in a cleaner format
    if comparison['new_stocks'] or comparison['removed_stocks']:
        col1, col2 = st.columns(2)
        
        with col1:
            if comparison['new_stocks']:
                st.write("### 🟢 **Stocks to ADD**")
                for stock in comparison['new_stocks']:
                    st.write(f"• **{stock}**")
            else:
                st.write("### ✅ **No new stocks to add**")
        
        with col2:
            if comparison['removed_stocks']:
                st.write("### 🔴 **Stocks to SELL**")
                for stock in comparison['removed_stocks']:
                    st.write(f"• **{stock}**")
            else:
                st.write("### ✅ **No stocks to remove**")
    
    # Current portfolio value
    if 'current_portfolio_value' in rebalancing_info:
        current_value = rebalancing_info['current_portfolio_value']
        st.subheader("💰 Current Portfolio Value")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💼 Portfolio Value", f"₹{current_value:,.0f}")
        with col2:
            st.info("This will be rebalanced across the new stock list")
    
    # Additional investment section
    st.subheader("💰 Additional Investment (Optional)")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        additional_investment = st.number_input(
            "Add more funds during rebalancing (₹)",
            min_value=0,
            value=0,
            step=25000,
            help="Optional: Add more money to invest along with rebalancing"
        )
    
    with col2:
        if additional_investment > 0:
            total_after = current_value + additional_investment if 'current_portfolio_value' in rebalancing_info else additional_investment
            st.metric("💼 Total After", f"₹{total_after:,.0f}")
        
        st.markdown("**Common amounts:**")
        col2a, col2b = st.columns(2)
        with col2a:
            if st.button("+ ₹1L", key="add_1l"):
                additional_investment = 100000
        with col2b:
            if st.button("+ ₹2L", key="add_2l"):
                additional_investment = 200000
    
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
                # Store and display plan (similar to initial investment)
                # Implementation would be similar to show_investment_plan()
            else:
                st.error(f"Calculation failed: {plan_data.get('detail', 'Unknown error')}")
        else:
            st.error(f"API Error: {response.status_code}")
    except Exception as e:
        st.error(f"Error calculating rebalancing: {e}")

def show_portfolio_status():
    """Enhanced portfolio status with beautiful visualizations"""
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
                
                # Extract data
                portfolio_summary = status['portfolio_summary']
                performance_metrics = status['performance_metrics']
                allocation_analysis = status['allocation_analysis']
                holdings = status['holdings']
                timeline = status['timeline']
                
                # Portfolio Header with Key Metrics
                show_portfolio_header(portfolio_summary, performance_metrics, timeline)
                
                # Portfolio Performance Charts
                show_performance_section(holdings, portfolio_summary, performance_metrics)
                
                # Holdings Heatmap
                show_holdings_heatmap(holdings)
                
                # Detailed Holdings Table
                show_detailed_holdings_table(holdings)
                
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
        current_value = portfolio_summary['current_value']
        st.metric(
            "💰 Portfolio Value",
            f"₹{current_value:,.0f}",
            help="Current market value of all holdings"
        )
    
    with col2:
        total_investment = portfolio_summary['total_investment']
        total_returns = portfolio_summary['total_returns']
        st.metric(
            "📈 Total Returns",
            f"₹{total_returns:,.0f}",
            delta=f"{portfolio_summary['returns_percentage']:.2f}%",
            help="Absolute returns since inception"
        )
    
    with col3:
        cagr = portfolio_summary['cagr']
        delta_color = "normal" if cagr >= 0 else "inverse"
        st.metric(
            "🎯 CAGR",
            f"{cagr:.2f}%",
            delta=f"vs 6% risk-free",
            delta_color=delta_color,
            help="Compound Annual Growth Rate"
        )
    
    with col4:
        investment_period = portfolio_summary['investment_period_days']
        st.metric(
            "⏱️ Investment Period",
            f"{investment_period} days",
            delta=f"{portfolio_summary['investment_period_years']:.1f} years",
            help="Time since first investment"
        )
    
    with col5:
        sharpe_ratio = performance_metrics['sharpe_ratio']
        st.metric(
            "📊 Sharpe Ratio",
            f"{sharpe_ratio:.2f}",
            help="Risk-adjusted returns"
        )
    
    # Performance summary
    best_performer = performance_metrics['best_performer']
    worst_performer = performance_metrics['worst_performer']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if best_performer:
            st.success(f"🏆 **Best Performer**: {best_performer['symbol']} (+{best_performer['percentage_return']:.2f}%)")
        else:
            st.info("🏆 **Best Performer**: N/A")
    
    with col2:
        if worst_performer:
            if worst_performer['percentage_return'] < 0:
                st.error(f"📉 **Worst Performer**: {worst_performer['symbol']} ({worst_performer['percentage_return']:.2f}%)")
            else:
                st.info(f"📉 **Worst Performer**: {worst_performer['symbol']} (+{worst_performer['percentage_return']:.2f}%)")
        else:
            st.info("📉 **Worst Performer**: N/A")
    
    with col3:
        volatility = performance_metrics['volatility_score']
        volatility_status = "Low" if volatility < 10 else "Medium" if volatility < 20 else "High"
        st.info(f"📊 **Volatility**: {volatility:.1f}% ({volatility_status})")

def show_performance_section(holdings, portfolio_summary, performance_metrics):
    """Show performance charts and analysis"""
    
    st.subheader("📈 Performance Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Returns comparison chart
        holdings_data = []
        for symbol, holding in holdings.items():
            holdings_data.append({
                'Stock': symbol,
                'Current Value': holding['current_value'],
                'Investment': holding['investment_value'],
                'Return %': holding['percentage_return'],
                'CAGR %': holding['annualized_return'],
                'Days Held': holding['days_held']
            })
        
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
    
    with col2:
        # Portfolio composition pie chart
        fig = px.pie(
            holdings_df,
            values='Current Value',
            names='Stock',
            title='Portfolio Composition',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Value: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def show_holdings_heatmap(holdings):
    """Show beautiful holdings heatmap"""
    
    st.subheader("🔥 Holdings Heatmap")
    
    # Prepare data for heatmap
    heatmap_data = []
    for symbol, holding in holdings.items():
        heatmap_data.append({
            'Stock': symbol,
            'Value': holding['current_value'],
            'Return %': holding['percentage_return'],
            'CAGR %': holding['annualized_return'],
            'Days Held': holding['days_held'],
            'Allocation %': holding['allocation_percent']
        })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    
    # Create treemap for holdings
    fig = px.treemap(
        heatmap_df,
        path=['Stock'],
        values='Value',
        color='Return %',
        color_continuous_scale='RdYlGn',
        color_continuous_midpoint=0,
        title='Holdings Treemap (Size = Value, Color = Returns)',
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
    
    fig.update_layout(
        height=500,
        font=dict(size=14),
        coloraxis_colorbar=dict(
            title="Returns (%)",
            titleside="right"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional performance matrix
    if len(heatmap_df) > 1:
        st.subheader("📊 Performance Matrix")
        
        # Create scatter plot matrix
        fig = px.scatter(
            heatmap_df,
            x='Days Held',
            y='Return %',
            size='Value',
            color='CAGR %',
            hover_name='Stock',
            title='Risk-Return Analysis (Bubble Size = Investment Value)',
            color_continuous_scale='RdYlGn',
            size_max=60
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Days Held",
            yaxis_title="Total Return (%)"
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
        st.plotly_chart(fig, use_container_width=True)

def show_detailed_holdings_table(holdings):
    """Show detailed holdings table with enhanced formatting"""
    
    st.subheader("📋 Detailed Holdings")
    
    # Prepare detailed table data
    table_data = []
    for symbol, holding in holdings.items():
        
        # Determine return color
        return_pct = holding['percentage_return']
        cagr_pct = holding['annualized_return']
        
        table_data.append({
            'Stock': symbol,
            'Shares': f"{holding['shares']:,}",
            'Avg Price': f"₹{holding['avg_price']:,.2f}",
            'Current Price': f"₹{holding['current_price']:,.2f}",
            'Investment': f"₹{holding['investment_value']:,.0f}",
            'Current Value': f"₹{holding['current_value']:,.0f}",
            'Absolute P&L': f"₹{holding['absolute_return']:,.0f}",
            'Return %': f"{return_pct:.2f}%",
            'CAGR %': f"{cagr_pct:.2f}%",
            'Allocation %': f"{holding['allocation_percent']:.2f}%",
            'Days Held': holding['days_held'],
            'First Purchase': holding['first_purchase_date'][:10],
            'Transactions': holding['transaction_count']
        })
    
    table_df = pd.DataFrame(table_data)
    
    # Display table
    st.dataframe(table_df, use_container_width=True, hide_index=True)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_return = sum(float(data['Return %'].replace('%', '')) for data in table_data) / len(table_data)
        st.metric("📊 Average Return", f"{avg_return:.2f}%")
    
    with col2:
        avg_cagr = sum(float(data['CAGR %'].replace('%', '')) for data in table_data) / len(table_data)
        st.metric("🎯 Average CAGR", f"{avg_cagr:.2f}%")
    
    with col3:
        positive_returns = sum(1 for data in table_data if float(data['Return %'].replace('%', '')) > 0)
        win_rate = (positive_returns / len(table_data)) * 100
        st.metric("🏆 Win Rate", f"{win_rate:.1f}%")
    
    with col4:
        avg_holding_period = sum(holding['days_held'] for holding in holdings.values()) / len(holdings)
        st.metric("⏱️ Avg Holding Period", f"{avg_holding_period:.0f} days")

def show_advanced_analytics(allocation_analysis, performance_metrics, timeline):
    """Show advanced analytics section"""
    
    st.subheader("🧠 Advanced Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ⚖️ Allocation Analysis")
        
        allocation_stats = allocation_analysis['allocation_stats']
        st.write(f"**Target Allocation**: {allocation_stats['target_allocation']:.2f}%")
        st.write(f"**Current Range**: {allocation_stats['min_allocation']:.2f}% - {allocation_stats['max_allocation']:.2f}%")
        st.write(f"**Average Allocation**: {allocation_stats['avg_allocation']:.2f}%")
        st.write(f"**Deviation Score**: {allocation_analysis['allocation_deviation']:.2f}%")
        
        if allocation_analysis['rebalancing_needed']:
            st.warning("⚠️ Portfolio may need rebalancing")
        else:
            st.success("✅ Portfolio allocation is balanced")
        
        st.write("### 📊 Risk Metrics")
        st.write(f"**Volatility**: {performance_metrics['volatility_score']:.2f}%")
        st.write(f"**Sharpe Ratio**: {performance_metrics['sharpe_ratio']:.2f}")
        
        # Risk assessment
        volatility = performance_metrics['volatility_score']
        if volatility < 10:
            risk_level = "🟢 Low Risk"
        elif volatility < 20:
            risk_level = "🟡 Medium Risk"
        else:
            risk_level = "🔴 High Risk"
        
        st.write(f"**Risk Level**: {risk_level}")
    
    with col2:
        st.write("### 📅 Investment Timeline")
        
        st.write(f"**First Investment**: {timeline['first_investment'][:10]}")
        st.write(f"**Last Investment**: {timeline['last_investment'][:10]}")
        st.write(f"**Total Orders**: {timeline['total_orders']}")
        st.write(f"**Last Updated**: {timeline['last_updated'][:10]}")
        
        st.write("### 🎯 Performance Benchmarks")
        
        # Get CAGR from portfolio summary
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
        
        st.write("### 💡 Insights")
        
        # Generate insights
        best_performer = performance_metrics.get('best_performer')
        worst_performer = performance_metrics.get('worst_performer')
        
        if best_performer and worst_performer:
            performance_spread = best_performer['percentage_return'] - worst_performer['percentage_return']
            st.write(f"**Performance Spread**: {performance_spread:.2f}%")
            
            if performance_spread > 20:
                st.info("💡 High performance variation suggests selective stock picking")
            else:
                st.info("💡 Consistent performance across holdings")
        
        # Investment frequency
        total_orders = timeline['total_orders']
        first_investment_date = datetime.fromisoformat(timeline['first_investment'])
        days_active = (datetime.now() - first_investment_date).days
        avg_orders_per_month = (total_orders / max(days_active, 1)) * 30
        
        st.write(f"**Investment Frequency**: {avg_orders_per_month:.1f} orders/month")

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