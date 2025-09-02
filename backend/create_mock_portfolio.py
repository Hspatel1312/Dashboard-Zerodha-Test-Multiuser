#!/usr/bin/env python3
"""
Create a mock successful portfolio for testing rebalancing
"""
import json
import os
from datetime import datetime

def create_mock_portfolio():
    """Create mock successful orders to test rebalancing"""
    
    # Path to test2 user data
    user_data_dir = "user_data/32df6628-9ee6-40b3-9b5d-0027ff312e2b"
    orders_file = os.path.join(user_data_dir, "system_orders.json")
    
    # Create mock successful orders
    mock_orders = [
        {
            "order_id": 1,
            "symbol": "JSWHL",
            "action": "BUY",
            "shares": 1,
            "price": 17898.0,
            "value": 17898.0,
            "allocation_percent": 51.14,
            "execution_time": "2025-09-02T12:00:00.000000",
            "session_type": "INITIAL_INVESTMENT",
            "status": "EXECUTED",  # Make it successful
            "can_retry": True,
            "retry_count": 0,
            "retry_history": [],
            "zerodha_order_id": "MOCK001",
            "live_execution_status": "COMPLETE"
        },
        {
            "order_id": 2,
            "symbol": "NIFTY",
            "action": "BUY",
            "shares": 202,
            "price": 86.61,
            "value": 17495.22,
            "allocation_percent": 49.99,
            "execution_time": "2025-09-02T12:00:00.000000",
            "session_type": "INITIAL_INVESTMENT",
            "status": "EXECUTED",  # Make it successful
            "can_retry": True,
            "retry_count": 0,
            "retry_history": [],
            "zerodha_order_id": "MOCK002",
            "live_execution_status": "COMPLETE"
        }
    ]
    
    # Save mock orders
    with open(orders_file, 'w') as f:
        json.dump(mock_orders, f, indent=2)
    
    print(f"[SUCCESS] Created mock successful portfolio:")
    print(f"   JSWHL: 1 share @ Rs.17,898 = Rs.17,898")
    print(f"   NIFTY: 202 shares @ Rs.86.61 = Rs.17,495")
    print(f"   Total portfolio value: Rs.35,393")
    print(f"")
    print(f"Saved to: {orders_file}")
    print(f"")
    print(f"Now you can test rebalancing scenarios:")
    print(f"   1. Add additional investment (e.g., Rs.10,000)")
    print(f"   2. Change CSV stocks (add/remove stocks)")
    print(f"   3. Test rebalancing calculations and execution")

if __name__ == "__main__":
    create_mock_portfolio()