#!/usr/bin/env python3
"""
Cleanup duplicate orders from system_orders.json
This script removes duplicate orders while preserving the latest status for each order_id
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def cleanup_duplicate_orders():
    """Remove duplicate orders and keep the latest status for each order_id"""
    orders_file = 'system_orders.json'
    
    if not os.path.exists(orders_file):
        print("No orders file found")
        return
    
    # Load all orders
    with open(orders_file, 'r') as f:
        all_orders = json.load(f)
    
    print(f"Total orders before cleanup: {len(all_orders)}")
    
    # Group orders by order_id and keep the latest status
    orders_by_id = defaultdict(list)
    for order in all_orders:
        orders_by_id[order['order_id']].append(order)
    
    # For each order_id, keep the most recent version
    cleaned_orders = []
    for order_id, order_versions in orders_by_id.items():
        if len(order_versions) == 1:
            # No duplicates, keep as is
            cleaned_orders.append(order_versions[0])
        else:
            print(f"Order {order_id}: Found {len(order_versions)} versions")
            
            # Sort by execution_time to get the latest version
            try:
                sorted_versions = sorted(order_versions, key=lambda x: x.get('execution_time', ''))
                latest_order = sorted_versions[-1]
                
                # If latest is successful, use it; otherwise check if any succeeded
                if latest_order.get('status') in ['EXECUTED_SYSTEM', 'EXECUTED_LIVE']:
                    cleaned_orders.append(latest_order)
                    print(f"  Keeping latest successful version: {latest_order.get('status')}")
                else:
                    # Look for any successful version
                    successful_versions = [v for v in order_versions if v.get('status') in ['EXECUTED_SYSTEM', 'EXECUTED_LIVE']]
                    if successful_versions:
                        # Keep the latest successful version
                        latest_successful = sorted(successful_versions, key=lambda x: x.get('execution_time', ''))[-1]
                        cleaned_orders.append(latest_successful)
                        print(f"  Keeping latest successful version: {latest_successful.get('status')}")
                    else:
                        # No successful versions, keep latest failed
                        cleaned_orders.append(latest_order)
                        print(f"  Keeping latest failed version: {latest_order.get('status')}")
                        
            except Exception as e:
                print(f"  Error processing order {order_id}: {e}")
                # Fallback: keep first version
                cleaned_orders.append(order_versions[0])
    
    print(f"Total orders after cleanup: {len(cleaned_orders)}")
    
    # Create backup
    backup_file = f'system_orders_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w') as f:
        json.dump(all_orders, f, indent=2)
    print(f"Created backup: {backup_file}")
    
    # Save cleaned orders
    with open(orders_file, 'w') as f:
        json.dump(cleaned_orders, f, indent=2)
    
    print("Cleanup completed!")
    
    # Show summary
    failed_orders = [o for o in cleaned_orders if o.get('status') == 'FAILED']
    successful_orders = [o for o in cleaned_orders if o.get('status') in ['EXECUTED_SYSTEM', 'EXECUTED_LIVE']]
    
    print(f"\nSummary:")
    print(f"  Total orders: {len(cleaned_orders)}")
    print(f"  Successful: {len(successful_orders)}")
    print(f"  Failed: {len(failed_orders)}")
    
    if failed_orders:
        print(f"\nRemaining failed orders:")
        for order in failed_orders:
            print(f"  Order {order['order_id']} ({order['symbol']}): {order.get('failure_reason', 'No reason')}")

if __name__ == "__main__":
    cleanup_duplicate_orders()