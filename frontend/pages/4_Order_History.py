# frontend/pages/4_Order_History.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from api_client import APIClient, APIHelpers
from session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="Order History",
    page_icon="📋",
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
    st.title("📋 Order History")
    st.markdown("Complete record of all your investment orders")
    
    # Load and display orders
    load_and_display_orders(api_client)

def load_and_display_orders(api_client):
    """Load and display order history"""
    
    with st.spinner("Loading order history..."):
        orders_response = api_client.get_system_orders()
    
    orders_data = APIHelpers.extract_data(orders_response)
    
    if not orders_data:
        st.error("❌ Unable to load order history")
        return
    
    orders = orders_data.get('orders', [])
    
    if not orders:
        show_empty_orders()
        return
    
    # Show orders table directly
    show_orders_table(orders)

def show_empty_orders():
    """Show message when no orders exist"""
    st.info("📭 No orders found")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### 🚀 Start Investing
        
        You haven't placed any orders yet.
        
        **Get Started:**
        1. Go to Investment page
        2. Set up your initial investment
        3. Your orders will appear here
        """)
        
        if st.button("➡️ Go to Investment", use_container_width=True):
            st.switch_page("pages/2_Investment.py")

def show_order_summary(orders_data):
    """Show order summary metrics"""
    
    st.subheader("📊 Order Summary")
    
    total_orders = orders_data.get('total_orders', 0)
    orders = orders_data.get('orders', [])
    
    # Calculate summary metrics
    buy_orders = len([o for o in orders if o.get('action') == 'BUY'])
    sell_orders = len([o for o in orders if o.get('action') == 'SELL'])
    total_value = sum(o.get('value', 0) for o in orders if o.get('action') == 'BUY')
    unique_stocks = len(set(o.get('symbol') for o in orders))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total Orders", total_orders)
    
    with col2:
        st.metric("📈 Buy Orders", buy_orders, delta=f"{sell_orders} sells")
    
    with col3:
        st.metric("💰 Total Investment", APIHelpers.format_currency(total_value))
    
    with col4:
        st.metric("📊 Unique Stocks", unique_stocks)

def show_orders_table(orders):
    """Display orders in a filterable table"""
    
    st.subheader("📋 Order Details")
    
    # Convert to DataFrame
    df = pd.DataFrame(orders)
    
    # Add filters
    show_order_filters(df)
    
    # Apply filters
    filtered_df = apply_order_filters(df)
    
    if filtered_df.empty:
        st.info("No orders match the current filters")
        return
    
    # Format for display
    display_df = format_orders_for_display(filtered_df)
    
    # Show table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Status': st.column_config.TextColumn(
                'Status',
                help="Order execution status"
            ),
            'Date': st.column_config.DatetimeColumn(
                'Date',
                format="DD/MM/YYYY HH:mm"
            )
        }
    )

def show_order_filters(df):
    """Show filter controls for orders"""
    
    st.markdown("##### 🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Status filter
        all_statuses = df['status'].unique().tolist() if 'status' in df.columns else ['EXECUTED_SYSTEM']
        selected_statuses = st.multiselect(
            "Status",
            options=all_statuses,
            default=all_statuses,
            key="status_filter"
        )
    
    with col2:
        # Action filter
        all_actions = df['action'].unique().tolist() if 'action' in df.columns else ['BUY']
        selected_actions = st.multiselect(
            "Action",
            options=all_actions,
            default=all_actions,
            key="action_filter"
        )
    
    with col3:
        # Stock filter
        all_stocks = sorted(df['symbol'].unique().tolist()) if 'symbol' in df.columns else []
        selected_stocks = st.multiselect(
            "Stocks",
            options=all_stocks,
            default=all_stocks,
            key="stock_filter"
        )
    
    with col4:
        # Date range
        if 'execution_time' in df.columns:
            try:
                df['execution_time'] = pd.to_datetime(df['execution_time'])
                min_date = df['execution_time'].min().date()
                max_date = df['execution_time'].max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="date_filter"
                )
            except:
                date_range = None
        else:
            date_range = None

def apply_order_filters(df):
    """Apply selected filters to the dataframe"""
    
    filtered_df = df.copy()
    
    # Status filter
    if 'status_filter' in st.session_state and st.session_state.status_filter:
        if 'status' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['status'].isin(st.session_state.status_filter)]
    
    # Action filter
    if 'action_filter' in st.session_state and st.session_state.action_filter:
        if 'action' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['action'].isin(st.session_state.action_filter)]
    
    # Stock filter
    if 'stock_filter' in st.session_state and st.session_state.stock_filter:
        if 'symbol' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['symbol'].isin(st.session_state.stock_filter)]
    
    # Date filter
    if 'date_filter' in st.session_state and st.session_state.date_filter:
        if 'execution_time' in filtered_df.columns:
            try:
                filtered_df['execution_time'] = pd.to_datetime(filtered_df['execution_time'])
                
                if isinstance(st.session_state.date_filter, tuple) and len(st.session_state.date_filter) == 2:
                    start_date, end_date = st.session_state.date_filter
                    filtered_df = filtered_df[
                        (filtered_df['execution_time'].dt.date >= start_date) &
                        (filtered_df['execution_time'].dt.date <= end_date)
                    ]
            except:
                pass
    
    return filtered_df

def format_orders_for_display(df):
    """Format orders dataframe for display"""
    
    display_df = df.copy()
    
    # Format execution time
    if 'execution_time' in display_df.columns:
        display_df['execution_time'] = pd.to_datetime(display_df['execution_time'])
        display_df['Date'] = display_df['execution_time'].dt.strftime('%d/%m/%Y %H:%M')
    else:
        display_df['Date'] = 'Unknown'
    
    # Format currency columns
    if 'price' in display_df.columns:
        display_df['Price'] = display_df['price'].apply(lambda x: f"₹{x:.2f}")
    
    if 'value' in display_df.columns:
        display_df['Value'] = display_df['value'].apply(lambda x: f"₹{x:,.0f}")
    
    if 'allocation_percent' in display_df.columns:
        display_df['Allocation'] = display_df['allocation_percent'].apply(lambda x: f"{x:.2f}%")
    
    # Rename columns
    column_mapping = {
        'symbol': 'Stock',
        'action': 'Action',
        'shares': 'Shares',
        'status': 'Status',
        'session_type': 'Session'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in display_df.columns:
            display_df[new_col] = display_df[old_col]
    
    # Select final columns for display
    final_columns = ['Date', 'Stock', 'Action', 'Shares']
    
    if 'Price' in display_df.columns:
        final_columns.append('Price')
    if 'Value' in display_df.columns:
        final_columns.append('Value')
    if 'Allocation' in display_df.columns:
        final_columns.append('Allocation')
    if 'Status' in display_df.columns:
        final_columns.append('Status')
    
    return display_df[final_columns]

def show_order_analytics(orders):
    """Show order analytics and insights"""
    
    st.subheader("📈 Analytics")
    
    if not orders:
        st.info("No data for analytics")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(orders)
    
    # Order timeline
    show_order_timeline(df)
    
    # Top stocks by value
    show_top_stocks_by_value(df)
    
    # Recent activity
    show_recent_activity(df)

def show_order_timeline(df):
    """Show order timeline chart"""
    
    if 'execution_time' not in df.columns:
        return
    
    try:
        # Convert to datetime and group by date
        df['execution_time'] = pd.to_datetime(df['execution_time'])
        df['date'] = df['execution_time'].dt.date
        
        daily_orders = df.groupby('date').agg({
            'value': 'sum',
            'order_id': 'count'
        }).reset_index()
        
        daily_orders = daily_orders.rename(columns={'order_id': 'count'})
        
        # Create timeline chart
        fig = px.bar(
            daily_orders,
            x='date',
            y='value',
            title='Daily Order Value',
            labels={'value': 'Order Value (₹)', 'date': 'Date'}
        )
        
        fig.update_layout(height=300, showlegend=False)
        fig.update_traces(marker_color='#667eea')
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating timeline: {str(e)}")

def show_top_stocks_by_value(df):
    """Show top stocks by investment value"""
    
    st.markdown("##### 🏆 Top Stocks by Value")
    
    try:
        # Group by stock and sum values for BUY orders
        buy_orders = df[df.get('action', '') == 'BUY'] if 'action' in df.columns else df
        
        if not buy_orders.empty:
            stock_values = buy_orders.groupby('symbol')['value'].sum().sort_values(ascending=False).head(5)
            
            for i, (stock, value) in enumerate(stock_values.items(), 1):
                st.write(f"{i}. **{stock}**: {APIHelpers.format_currency(value)}")
        else:
            st.info("No buy orders found")
            
    except Exception as e:
        st.error(f"Error calculating top stocks: {str(e)}")

def show_recent_activity(df):
    """Show recent order activity"""
    
    st.markdown("##### ⏰ Recent Activity")
    
    try:
        if 'execution_time' in df.columns:
            # Sort by execution time and get recent orders
            df['execution_time'] = pd.to_datetime(df['execution_time'])
            recent_orders = df.sort_values('execution_time', ascending=False).head(5)
            
            for _, order in recent_orders.iterrows():
                symbol = order.get('symbol', 'Unknown')
                action = order.get('action', 'Unknown')
                shares = order.get('shares', 0)
                value = order.get('value', 0)
                
                # Format time
                try:
                    time_str = order['execution_time'].strftime('%d/%m %H:%M')
                except:
                    time_str = 'Unknown'
                
                st.write(f"**{time_str}**: {action} {shares} {symbol} - {APIHelpers.format_currency(value)}")
        else:
            st.info("No recent activity data available")
            
    except Exception as e:
        st.error(f"Error loading recent activity: {str(e)}")

if __name__ == "__main__":
    main()