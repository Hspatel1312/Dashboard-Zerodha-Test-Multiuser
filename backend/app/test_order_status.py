#!/usr/bin/env python3
"""
Test script to manually fetch order status from Zerodha API
"""

import sys
import os
import json
from pathlib import Path

from .database import get_db, UserDB
from .services.multiuser_zerodha_auth import MultiUserZerodhaAuth

def test_order_status():
    """Test fetching order status for specific order ID"""
    
    # Test order ID
    test_order_id = "250902600174774"
    print(f"Testing order status fetch for order ID: {test_order_id}")
    print("=" * 60)
    
    try:
        # Get database session
        db = next(get_db())
        
        # Find test2 user
        user = db.query(UserDB).filter(UserDB.username == "test2").first()
        if not user:
            print("ERROR: test2 user not found!")
            return
            
        print(f"Found user: {user.username} (ID: {user.id})")
        
        # Initialize Zerodha auth for this user
        zerodha_auth = MultiUserZerodhaAuth(user)
        
        # Test if we can get kite instance
        try:
            kite = zerodha_auth.get_kite_instance()
            if not kite:
                print("ERROR: Could not get Kite instance. User may not be authenticated.")
                return
                
            print("✅ Kite instance obtained successfully")
            
            # Get user profile to verify connection
            profile = kite.profile()
            print(f"✅ Connected as: {profile.get('user_name', 'Unknown')}")
            
        except Exception as e:
            print(f"ERROR: Failed to get Kite instance: {e}")
            return
        
        # Fetch order status directly from Zerodha
        print(f"\nFetching order status from Zerodha API...")
        try:
            # Get order history for the specific order
            order_history = kite.order_history(order_id=test_order_id)
            
            print(f"✅ Order history fetched successfully!")
            print(f"Number of order updates: {len(order_history)}")
            print("\nOrder History Details:")
            print("-" * 40)
            
            for i, order_update in enumerate(order_history):
                print(f"Update {i+1}:")
                print(f"  Order ID: {order_update.get('order_id')}")
                print(f"  Status: {order_update.get('status')}")
                print(f"  Status Message: {order_update.get('status_message', 'N/A')}")
                print(f"  Order Timestamp: {order_update.get('order_timestamp')}")
                print(f"  Exchange Timestamp: {order_update.get('exchange_timestamp')}")
                print(f"  Symbol: {order_update.get('tradingsymbol')}")
                print(f"  Transaction Type: {order_update.get('transaction_type')}")
                print(f"  Quantity: {order_update.get('quantity')}")
                print(f"  Price: {order_update.get('price')}")
                print("")
            
            # Get the latest status
            if order_history:
                latest_order = order_history[-1]  # Last update is usually the current status
                latest_status = latest_order.get('status')
                print(f"🎯 LATEST STATUS: {latest_status}")
                print(f"🎯 STATUS MESSAGE: {latest_order.get('status_message', 'N/A')}")
                
                # Compare with our stored status
                print(f"\n📊 COMPARISON:")
                print(f"  Zerodha API Status: {latest_status}")
                print(f"  Our stored status: LIVE_PLACED (main order) / PLACED (retry)")
                
                if latest_status.upper() == "REJECTED":
                    print("❌ MISMATCH DETECTED: Zerodha shows REJECTED but our system shows PLACED")
                else:
                    print(f"ℹ️  Zerodha API returns: {latest_status}")
            
        except Exception as e:
            print(f"ERROR: Failed to fetch order history: {e}")
            print(f"Error type: {type(e).__name__}")
            
            # Try alternative method - get all orders and find this one
            print("\nTrying alternative method - fetching all orders...")
            try:
                all_orders = kite.orders()
                matching_orders = [o for o in all_orders if o.get('order_id') == test_order_id]
                
                if matching_orders:
                    print(f"✅ Found {len(matching_orders)} matching orders")
                    for order in matching_orders:
                        print(f"  Status: {order.get('status')}")
                        print(f"  Status Message: {order.get('status_message', 'N/A')}")
                else:
                    print(f"❌ Order {test_order_id} not found in current orders list")
                    
            except Exception as e2:
                print(f"ERROR: Alternative method also failed: {e2}")
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_order_status()