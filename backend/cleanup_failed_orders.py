
import json

# Load orders
with open("system_orders.json", "r") as f:
    orders = json.load(f)

# Fix the test orders back to EXECUTED_SYSTEM
for order in orders[:2]:
    if order.get("status") == "FAILED":
        order["status"] = "EXECUTED_SYSTEM"
        order.pop("failure_reason", None)
        order.pop("retry_count", None) 
        order.pop("can_retry", None)
        order.pop("failed_time", None)

# Save fixed orders
with open("system_orders.json", "w") as f:
    json.dump(orders, f, indent=2)

print("Orders restored to original state")
