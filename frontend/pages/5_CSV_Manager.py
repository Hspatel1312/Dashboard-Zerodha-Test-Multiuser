# frontend/pages/5_CSV_Manager.py
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from api_client import APIClient, APIHelpers
from session_manager import SessionManager

# Page configuration
st.set_page_config(
    page_title="CSV Manager",
    page_icon="📄",
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
    st.title("📄 CSV Data Manager")
    st.markdown("Monitor and update stock data from CSV source")
    
    # Load and show CSV data
    show_csv_content(api_client)

def show_csv_content(api_client):
    """Show CSV data and management"""
    
    # Get CSV status
    with st.spinner("Loading CSV data..."):
        csv_response = api_client.get_csv_stocks()
        status_response = api_client.get_csv_status()
    
    csv_data = APIHelpers.extract_data(csv_response)
    status_data = APIHelpers.extract_data(status_response)
    
    # CSV Connection Status
    show_connection_status(status_data, api_client)
    
    st.markdown("---")
    
    # Current CSV Data
    if csv_data:
        show_current_csv_data(csv_data)
    else:
        st.error("❌ Unable to load CSV data")

def show_connection_status(status_data, api_client):
    """Show CSV connection and update status"""
    
    st.subheader("📡 CSV Connection Status")
    
    if not status_data:
        st.error("❌ Unable to check CSV status")
        return
    
    current_csv = status_data.get('current_csv', {})
    
    # Status metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if current_csv.get('available'):
            st.success("✅ **Connected**")
        else:
            st.error("❌ **Disconnected**")
    
    with col2:
        total_symbols = current_csv.get('total_symbols', 0)
        st.metric("📈 Stocks", total_symbols)
    
    with col3:
        fetch_time = current_csv.get('fetch_time')
        if fetch_time:
            try:
                fetch_dt = pd.to_datetime(fetch_time)
                time_display = fetch_dt.strftime('%H:%M:%S')
            except:
                time_display = "Unknown"
        else:
            time_display = "Unknown"
        st.metric("⏰ Updated", time_display)
    
    with col4:
        csv_hash = current_csv.get('csv_hash', 'Unknown')
        display_hash = csv_hash[:8] + "..." if len(csv_hash) > 8 else csv_hash
        st.metric("🔖 Version", display_hash)
    
    # Source URL
    source_url = current_csv.get('source_url')
    if source_url:
        st.info(f"📡 **Source**: {source_url}")
    
    # Refresh button
    st.markdown("### 🔄 Update Data")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("Check for the latest updates from the CSV source.")
    
    with col2:
        if st.button("🔄 Check for Updates", type="primary", use_container_width=True):
            refresh_csv_data(api_client)

def refresh_csv_data(api_client):
    """Check for CSV updates"""
    
    with st.spinner("Checking for updates..."):
        refresh_response = api_client.force_csv_refresh()
    
    if APIHelpers.show_api_status(refresh_response, "Update check completed!"):
        refresh_data = APIHelpers.extract_data(refresh_response)
        
        if refresh_data:
            if refresh_data.get('csv_changed'):
                st.success("🎉 **New Data Found!**")
                
                change_details = refresh_data.get('change_details', {})
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Previous**: {change_details.get('old_hash', 'Unknown')[:8]}...")
                    st.write(f"**Current**: {change_details.get('new_hash', 'Unknown')[:8]}...")
                
                with col2:
                    old_count = change_details.get('old_symbols', 0)
                    new_count = change_details.get('new_symbols', 0)
                    st.write(f"**Stocks**: {old_count} → {new_count}")
                
                st.balloons()
                st.rerun()
            else:
                st.info("ℹ️ **Up to Date** - No new changes found")

def show_current_csv_data(csv_data):
    """Show current CSV data table"""
    
    st.subheader("📋 Current Stock List")
    
    stocks = csv_data.get('stocks', [])
    
    if not stocks:
        st.info("📭 No stock data available")
        return
    
    # Data quality info
    price_status = csv_data.get('price_data_status', {})
    success_rate = price_status.get('success_rate', 0)
    data_source = price_status.get('market_data_source', 'Unknown')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Live' in data_source:
            st.success(f"📡 **Live Data**: {success_rate:.1f}% success rate")
        else:
            st.warning(f"🔄 **Fallback Data**: {success_rate:.1f}% success rate")
    
    with col2:
        market_open = price_status.get('market_open', False)
        if market_open:
            st.success("🟢 **Market Open**")
        else:
            st.info("🔴 **Market Closed**")
    
    # Convert to DataFrame
    df = pd.DataFrame(stocks)
    
    # Simple search
    search_term = st.text_input("🔍 Search stocks", placeholder="Enter stock symbol")
    
    # Apply search
    if search_term:
        df = df[df['symbol'].str.contains(search_term.upper(), na=False)]
    
    if df.empty:
        st.info("No stocks match your search")
        return
    
    # Format for display
    display_df = df.copy()
    display_df['Price'] = display_df['price'].apply(lambda x: f"₹{x:.2f}")
    
    # Select columns
    display_columns = ['symbol', 'Price']
    column_names = ['Stock', 'Current Price']
    
    # Add other columns if available
    if 'score' in display_df.columns:
        display_df['Score'] = display_df['score'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
        display_columns.append('Score')
        column_names.append('Score')
    
    # Rename columns
    final_df = display_df[display_columns].copy()
    final_df.columns = column_names
    
    # Show with pagination
    page_size = 25
    total_rows = len(final_df)
    
    if total_rows > page_size:
        total_pages = (total_rows - 1) // page_size + 1
        page = st.selectbox(
            f"Page (showing {total_rows} stocks)",
            range(1, total_pages + 1)
        )
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        final_df = final_df.iloc[start_idx:end_idx]
    
    # Display table
    st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True
    )
    
    st.caption(f"Showing {len(final_df)} of {total_rows} stocks")

if __name__ == "__main__":
    main()