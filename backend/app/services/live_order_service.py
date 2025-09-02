# backend/app/services/live_order_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

class LiveOrderService:
    def __init__(self, zerodha_auth, user_data_dir=None):
        self.zerodha_auth = zerodha_auth
        self.user_data_dir = user_data_dir or ""
        self.live_orders_file = os.path.join(self.user_data_dir, "live_orders.json") if user_data_dir else "live_orders.json"
        self.order_status_cache = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure order tracking files exist"""
        if not os.path.exists(self.live_orders_file):
            with open(self.live_orders_file, 'w') as f:
                json.dump([], f)
    
    def _get_kite_instance(self):
        """Get authenticated Kite instance"""
        try:
            if not self.zerodha_auth or not self.zerodha_auth.is_authenticated():
                print("[ERROR] Zerodha not authenticated for live trading")
                return None
            
            kite = self.zerodha_auth.get_kite_instance()
            if not kite:
                print("[ERROR] No Kite instance available")
                return None
            
            # Test connection
            try:
                profile = kite.profile()
                print(f"[SUCCESS] Kite connection verified for user: {profile.get('user_name', 'Unknown')}")
                return kite
            except Exception as e:
                print(f"[ERROR] Kite connection test failed: {e}")
                return None
        except Exception as e:
            print(f"[ERROR] Error getting Kite instance: {e}")
            return None
    
    def place_live_order(self, order_data: Dict) -> Dict:
        """Place a live order on Zerodha and track it"""
        try:
            kite = self._get_kite_instance()
            if not kite:
                return {
                    "success": False,
                    "error": "ZERODHA_CONNECTION_FAILED",
                    "message": "Cannot connect to Zerodha for live trading"
                }
            
            # Prepare order parameters for Zerodha API
            order_params = {
                "variety": "regular",  # Required: regular, bo, co, amo
                "tradingsymbol": order_data["symbol"],
                "exchange": "NSE",
                "transaction_type": "BUY" if order_data["action"] == "BUY" else "SELL",
                "quantity": order_data["shares"],
                "order_type": "MARKET",  # Can be changed to LIMIT for limit orders
                "product": "CNC",  # Cash and Carry for delivery
                "validity": "DAY"
            }
            
            # For limit orders, add price
            if order_data.get("order_type") == "LIMIT":
                order_params["order_type"] = "LIMIT"
                order_params["price"] = order_data["price"]
            
            print(f"[INFO] Placing live order: {order_params}")
            
            # Place the order
            order_id = kite.place_order(**order_params)
            
            # Create tracking record with retry information
            tracking_record = {
                "system_order_id": order_data.get("system_order_id"),
                "zerodha_order_id": order_id,
                "symbol": order_data["symbol"],
                "action": order_data["action"],
                "shares": order_data["shares"],
                "order_type": order_params["order_type"],
                "price": order_data.get("price"),
                "status": "PLACED",
                "placed_time": datetime.now().isoformat(),
                "last_checked": datetime.now().isoformat(),
                "order_params": order_params,
                "execution_details": None,
                # Add retry tracking information
                "parent_order_id": order_data.get("system_order_id"),
                "is_retry": bool(order_data.get("current_retry_attempt")),
                "retry_info": order_data.get("current_retry_attempt") if order_data.get("current_retry_attempt") else None
            }
            
            # Save to tracking file
            self._save_order_tracking(tracking_record)
            
            print(f"[SUCCESS] Live order placed: {order_id} for {order_data['symbol']}")
            
            return {
                "success": True,
                "zerodha_order_id": order_id,
                "status": "PLACED",
                "tracking_record": tracking_record
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Failed to place live order: {error_msg}")
            
            # Create failed tracking record with retry information
            failed_record = {
                "system_order_id": order_data.get("system_order_id"),
                "zerodha_order_id": None,
                "symbol": order_data["symbol"],
                "action": order_data["action"],
                "shares": order_data["shares"],
                "status": "FAILED_TO_PLACE",
                "placed_time": datetime.now().isoformat(),
                "error": error_msg,
                "execution_details": None,
                # Add retry tracking information
                "parent_order_id": order_data.get("system_order_id"),
                "is_retry": bool(order_data.get("current_retry_attempt")),
                "retry_info": order_data.get("current_retry_attempt") if order_data.get("current_retry_attempt") else None
            }
            
            self._save_order_tracking(failed_record)
            
            return {
                "success": False,
                "error": "ORDER_PLACEMENT_FAILED",
                "message": error_msg,
                "tracking_record": failed_record
            }
    
    def get_order_status(self, zerodha_order_id: str) -> Dict:
        """Get current status of a specific order"""
        try:
            kite = self._get_kite_instance()
            if not kite:
                return {"status": "CONNECTION_ERROR", "error": "Cannot connect to Zerodha"}
            
            # Get order history for this order
            orders = kite.order_history(zerodha_order_id)
            
            if not orders:
                return {"status": "NOT_FOUND", "error": "Order not found"}
            
            # Get the latest order status
            latest_order = orders[-1]
            
            order_status = {
                "order_id": zerodha_order_id,
                "status": latest_order.get("status"),
                "tradingsymbol": latest_order.get("tradingsymbol"),
                "transaction_type": latest_order.get("transaction_type"),
                "quantity": latest_order.get("quantity"),
                "filled_quantity": latest_order.get("filled_quantity", 0),
                "pending_quantity": latest_order.get("pending_quantity", 0),
                "average_price": latest_order.get("average_price"),
                "order_timestamp": latest_order.get("order_timestamp"),
                "exchange_timestamp": latest_order.get("exchange_timestamp"),
                "status_message": latest_order.get("status_message", ""),
                "full_history": orders
            }
            
            return {"success": True, "order_details": order_status}
            
        except Exception as e:
            print(f"[ERROR] Error getting order status for {zerodha_order_id}: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def update_order_status(self, zerodha_order_id: str) -> Dict:
        """Update status for a tracked order"""
        try:
            # Get current status from Zerodha
            status_result = self.get_order_status(zerodha_order_id)
            
            if not status_result.get("success"):
                return status_result
            
            order_details = status_result["order_details"]
            
            # Update tracking record
            tracking_records = self._load_order_tracking()
            updated = False
            
            for record in tracking_records:
                if record.get("zerodha_order_id") == zerodha_order_id:
                    record["status"] = order_details["status"]
                    record["last_checked"] = datetime.now().isoformat()
                    record["execution_details"] = order_details
                    
                    # Mark completion time if order is complete
                    if order_details["status"] in ["COMPLETE", "CANCELLED", "REJECTED"]:
                        record["completion_time"] = datetime.now().isoformat()
                    
                    updated = True
                    break
            
            if updated:
                self._save_order_tracking_list(tracking_records)
                return {"success": True, "updated": True, "order_details": order_details}
            else:
                return {"success": False, "error": "Order not found in tracking"}
                
        except Exception as e:
            print(f"[ERROR] Error updating order status: {e}")
            return {"success": False, "error": str(e)}
    
    def get_all_live_orders(self) -> List[Dict]:
        """Get all tracked live orders with current status"""
        try:
            tracking_records = self._load_order_tracking()
            
            # Update status for pending orders
            for record in tracking_records:
                if (record.get("zerodha_order_id") and 
                    record.get("status") not in ["COMPLETE", "CANCELLED", "REJECTED", "FAILED_TO_PLACE"]):
                    
                    # Update status if not checked recently (within last 30 seconds)
                    last_checked = record.get("last_checked")
                    if last_checked:
                        last_checked_time = datetime.fromisoformat(last_checked)
                        if (datetime.now() - last_checked_time).total_seconds() > 30:
                            self.update_order_status(record["zerodha_order_id"])
            
            return self._load_order_tracking()  # Reload after updates
            
        except Exception as e:
            print(f"[ERROR] Error getting all live orders: {e}")
            return []
    
    def start_order_monitoring(self, check_interval: int = 10):
        """Start background monitoring of live orders"""
        if self.monitoring_active:
            print("[INFO] Order monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_orders, args=(check_interval,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        print(f"[INFO] Started live order monitoring (checking every {check_interval}s)")
    
    def stop_order_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("[INFO] Stopped live order monitoring")
    
    def _monitor_orders(self, check_interval: int):
        """Background thread to monitor order status"""
        while self.monitoring_active:
            try:
                tracking_records = self._load_order_tracking()
                pending_orders = [
                    r for r in tracking_records 
                    if (r.get("zerodha_order_id") and 
                        r.get("status") not in ["COMPLETE", "CANCELLED", "REJECTED", "FAILED_TO_PLACE"])
                ]
                
                if pending_orders:
                    print(f"[INFO] Monitoring {len(pending_orders)} pending orders...")
                    
                    for record in pending_orders:
                        try:
                            self.update_order_status(record["zerodha_order_id"])
                        except Exception as e:
                            print(f"[ERROR] Error monitoring order {record['zerodha_order_id']}: {e}")
                    
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"[ERROR] Error in order monitoring: {e}")
                time.sleep(check_interval)
    
    def get_orders_by_parent(self) -> Dict:
        """Get orders grouped by their parent order ID"""
        try:
            tracking_records = self._load_order_tracking()
            orders_by_parent = {}
            
            for record in tracking_records:
                parent_id = record.get("parent_order_id", "unknown")
                
                if parent_id not in orders_by_parent:
                    orders_by_parent[parent_id] = {
                        "parent_order_id": parent_id,
                        "original_order": None,
                        "retry_attempts": [],
                        "total_attempts": 0,
                        "latest_status": "UNKNOWN",
                        "latest_zerodha_order_id": None
                    }
                
                # Check if this is a retry or original order
                if record.get("is_retry"):
                    orders_by_parent[parent_id]["retry_attempts"].append(record)
                else:
                    orders_by_parent[parent_id]["original_order"] = record
                
                # Update latest status
                orders_by_parent[parent_id]["total_attempts"] += 1
                orders_by_parent[parent_id]["latest_status"] = record.get("status", "UNKNOWN")
                
                # Update latest Zerodha order ID if available
                if record.get("zerodha_order_id"):
                    orders_by_parent[parent_id]["latest_zerodha_order_id"] = record.get("zerodha_order_id")
            
            # Sort retry attempts by retry number
            for parent_data in orders_by_parent.values():
                parent_data["retry_attempts"].sort(
                    key=lambda x: x.get("retry_info", {}).get("retry_number", 0)
                )
            
            return orders_by_parent
            
        except Exception as e:
            print(f"[ERROR] Error getting orders by parent: {e}")
            return {}

    def get_order_summary(self) -> Dict:
        """Get summary of all orders"""
        try:
            tracking_records = self._load_order_tracking()
            
            summary = {
                "total_orders": len(tracking_records),
                "pending": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "orders_by_status": {},
                "orders_by_symbol": {},
                "total_value": 0,
                "retry_summary": {
                    "orders_with_retries": 0,
                    "total_retry_attempts": 0,
                    "successful_retries": 0,
                    "failed_retries": 0
                }
            }
            
            orders_by_parent = self.get_orders_by_parent()
            
            for record in tracking_records:
                status = record.get("status", "UNKNOWN")
                symbol = record.get("symbol", "UNKNOWN")
                
                # Count by status
                if status in ["OPEN", "TRIGGER PENDING", "PLACED"]:
                    summary["pending"] += 1
                elif status == "COMPLETE":
                    summary["completed"] += 1
                elif status in ["CANCELLED", "REJECTED"]:
                    summary["cancelled"] += 1
                elif status in ["FAILED_TO_PLACE"]:
                    summary["failed"] += 1
                
                summary["orders_by_status"][status] = summary["orders_by_status"].get(status, 0) + 1
                summary["orders_by_symbol"][symbol] = summary["orders_by_symbol"].get(symbol, 0) + 1
                
                # Calculate value
                if record.get("execution_details"):
                    avg_price = record["execution_details"].get("average_price")
                    filled_qty = record["execution_details"].get("filled_quantity", 0)
                    if avg_price and filled_qty:
                        summary["total_value"] += avg_price * filled_qty
                        
                # Count retry statistics
                if record.get("is_retry"):
                    summary["retry_summary"]["total_retry_attempts"] += 1
                    if status in ["COMPLETE", "PLACED"]:
                        summary["retry_summary"]["successful_retries"] += 1
                    else:
                        summary["retry_summary"]["failed_retries"] += 1
            
            # Count orders with retries
            summary["retry_summary"]["orders_with_retries"] = len([
                parent_data for parent_data in orders_by_parent.values()
                if len(parent_data["retry_attempts"]) > 0
            ])
            
            return summary
            
        except Exception as e:
            print(f"[ERROR] Error getting order summary: {e}")
            return {"error": str(e)}
    
    def _save_order_tracking(self, tracking_record: Dict):
        """Save a single order tracking record"""
        tracking_records = self._load_order_tracking()
        tracking_records.append(tracking_record)
        self._save_order_tracking_list(tracking_records)
    
    def _load_order_tracking(self) -> List[Dict]:
        """Load order tracking records"""
        try:
            if os.path.exists(self.live_orders_file):
                with open(self.live_orders_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"[ERROR] Error loading order tracking: {e}")
            return []
    
    def retry_failed_orders(self, order_ids: list = None) -> Dict:
        """Retry failed orders from system orders"""
        try:
            print(f"[INFO] LiveOrderService - Starting retry process for orders: {order_ids}")
            
            # Load system orders from the user-specific orders file (not live_orders.json)
            system_orders_file = os.path.join(self.user_data_dir, "system_orders.json") if self.user_data_dir else "system_orders.json"
            if not os.path.exists(system_orders_file):
                return {
                    'success': False,
                    'error': 'No system orders file found',
                    'message': 'Cannot retry orders - no system orders file exists'
                }
            
            with open(system_orders_file, 'r') as f:
                orders = json.load(f)
            
            print(f"[DEBUG] LiveOrderService - Loaded {len(orders)} orders from {system_orders_file}")
            for i, order in enumerate(orders):
                print(f"[DEBUG] Order {i+1}: id={order.get('order_id')}, status={order.get('status')}, can_retry={order.get('can_retry', True)}")
            
            # Filter orders to retry (handle both int and string order_ids)
            if order_ids:
                # Convert order_ids to both int and string for comparison
                order_ids_to_match = []
                for oid in order_ids:
                    order_ids_to_match.append(oid)  # original
                    order_ids_to_match.append(str(oid))  # string version
                    try:
                        order_ids_to_match.append(int(oid))  # int version
                    except (ValueError, TypeError):
                        pass
                
                orders_to_retry = [
                    order for order in orders 
                    if order.get('order_id') in order_ids_to_match 
                    and order.get('status') in ['FAILED', 'CANCELLED', 'REJECTED'] 
                    and order.get('can_retry', True)
                ]
                print(f"[INFO] Retrying specific orders: {order_ids}")
                print(f"[DEBUG] Order IDs to match: {order_ids_to_match}")
                
                # Debug each order's matching
                for order in orders:
                    order_id = order.get('order_id')
                    status = order.get('status')
                    can_retry = order.get('can_retry', True)
                    id_match = order_id in order_ids_to_match
                    status_match = status in ['FAILED', 'CANCELLED', 'REJECTED']
                    
                    print(f"[DEBUG] Order {order_id}: status={status}, can_retry={can_retry}, id_match={id_match}, status_match={status_match}")
                
                print(f"[DEBUG] Found {len(orders_to_retry)} orders matching criteria")
            else:
                orders_to_retry = [
                    order for order in orders 
                    if order.get('status') in ['FAILED', 'CANCELLED', 'REJECTED'] 
                    and order.get('can_retry', True)
                ]
                print(f"[INFO] Retrying all failed orders")
                print(f"[DEBUG] Found {len(orders_to_retry)} orders matching criteria")
            
            if not orders_to_retry:
                return {
                    'success': True,
                    'message': 'No failed orders found to retry',
                    'data': {
                        'retried_count': 0,
                        'successful_retries': 0,
                        'failed_retries': 0,
                        'orders': []
                    }
                }
            
            print(f"[INFO] Found {len(orders_to_retry)} orders to retry")
            
            # Execute retry for each order
            retry_results = []
            successful_retries = 0
            failed_retries = 0
            
            for order in orders_to_retry:
                print(f"[INFO] Retrying order {order['order_id']}: {order['action']} {order['symbol']}")
                
                # Initialize retry_history if not exists
                if 'retry_history' not in order:
                    order['retry_history'] = []
                
                # Increment retry count
                current_retry_count = order.get('retry_count', 0) + 1
                order['retry_count'] = current_retry_count
                order['last_retry_time'] = datetime.now().isoformat()
                
                # Check retry limits
                max_retries = 3
                if current_retry_count > max_retries:
                    print(f"[WARNING] Order {order['order_id']} exceeded max retries ({max_retries})")
                    order['can_retry'] = False
                    order['status'] = 'FAILED_MAX_RETRIES'
                    failed_retries += 1
                    retry_results.append({
                        'order_id': order['order_id'],
                        'symbol': order['symbol'],
                        'success': False,
                        'reason': f"Exceeded maximum retry attempts ({max_retries})"
                    })
                    continue
                
                # Create retry attempt record
                retry_attempt = {
                    'retry_number': current_retry_count,
                    'retry_time': datetime.now().isoformat(),
                    'original_order_id': order['order_id'],
                    'zerodha_order_id': None,
                    'status': 'PENDING',
                    'failure_reason': None,
                    'current_retry_attempt': {
                        'retry_number': current_retry_count,
                        'retry_time': datetime.now().isoformat(),
                        'parent_order_id': order['order_id']
                    }
                }
                
                # Prepare order data for retry
                order_data = {
                    'system_order_id': order['order_id'],
                    'symbol': order['symbol'],
                    'action': order['action'],
                    'shares': order['shares'],
                    'price': order.get('price'),
                    'order_type': 'MARKET',
                    'current_retry_attempt': retry_attempt['current_retry_attempt']
                }
                
                # Execute the retry using live order placement
                retry_result = self.place_live_order(order_data)
                
                # Update the retry attempt with results
                retry_attempt.update({
                    'zerodha_order_id': retry_result.get('zerodha_order_id'),
                    'status': 'PLACED' if retry_result.get('success') else 'FAILED',
                    'failure_reason': retry_result.get('message') if not retry_result.get('success') else None
                })
                
                # Add retry attempt to history
                order['retry_history'].append(retry_attempt)
                
                # Update main order with latest retry results
                if retry_result.get('success'):
                    order['status'] = 'LIVE_PLACED'
                    order['zerodha_order_id'] = retry_result.get('zerodha_order_id')
                    order['execution_time'] = datetime.now().isoformat()
                    successful_retries += 1
                    retry_results.append({
                        'order_id': order['order_id'],
                        'symbol': order['symbol'],
                        'success': True,
                        'reason': 'Retry successful - order placed',
                        'zerodha_order_id': retry_result.get('zerodha_order_id'),
                        'retry_number': current_retry_count
                    })
                else:
                    order['status'] = 'FAILED'
                    order['error'] = retry_result.get('message', 'Retry failed')
                    failed_retries += 1
                    retry_results.append({
                        'order_id': order['order_id'],
                        'symbol': order['symbol'],
                        'success': False,
                        'reason': retry_result.get('message', 'Retry failed'),
                        'retry_number': current_retry_count
                    })
            
            # Save updated orders back to system_orders.json
            with open(system_orders_file, 'w') as f:
                json.dump(orders, f, indent=2)
            
            print(f"[SUCCESS] Retry complete: {successful_retries} successful, {failed_retries} failed")
            
            return {
                'success': True,
                'message': f'Retry completed: {successful_retries} successful, {failed_retries} failed',
                'data': {
                    'retried_count': len(orders_to_retry),
                    'successful_retries': successful_retries,
                    'failed_retries': failed_retries,
                    'orders': retry_results
                }
            }
            
        except Exception as e:
            print(f"[ERROR] LiveOrderService - Failed to retry orders: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retry orders due to system error'
            }

    def _save_order_tracking_list(self, tracking_records: List[Dict]):
        """Save order tracking records"""
        try:
            # Clean the data to ensure JSON serialization
            cleaned_records = []
            for record in tracking_records:
                cleaned_record = {}
                for key, value in record.items():
                    # Convert any datetime objects to strings
                    if hasattr(value, 'isoformat'):
                        cleaned_record[key] = value.isoformat()
                    elif isinstance(value, dict):
                        # Clean nested dictionaries
                        cleaned_dict = {}
                        for nested_key, nested_value in value.items():
                            if hasattr(nested_value, 'isoformat'):
                                cleaned_dict[nested_key] = nested_value.isoformat()
                            else:
                                cleaned_dict[nested_key] = nested_value
                        cleaned_record[key] = cleaned_dict
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)
            
            with open(self.live_orders_file, 'w') as f:
                json.dump(cleaned_records, f, indent=2, default=str)
        except Exception as e:
            print(f"[ERROR] Error saving order tracking: {e}")