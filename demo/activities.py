import random
import time
from temporalio import activity

@activity.defn
async def charge_customer(amount: int, order_id: str) -> str:
    """
    Simulates charging a customer.
    """
    # This activity is now idempotent.
    # We check if the order_id has already been processed before charging.
    
    try:
        with open("charges.txt", "r") as f:
            if f"Order {order_id}" in f.read():
                return f"Already charged ${amount} for {order_id}"
    except FileNotFoundError:
        pass # File doesn't exist yet, that's fine

    with open("charges.txt", "a") as f:
        f.write(f"Order {order_id}: Charged ${amount}\n")
    
    # Simulate some processing time
    time.sleep(1)
    
    # Randomly fail 50% of the time to trigger Temporal's automatic retries
    if random.random() < 0.5:
        raise Exception("Network error while confirming charge with bank!")
        
    return f"Successfully charged ${amount}"

@activity.defn
async def bake_pizza(pizza_type: str) -> str:
    """Simulates baking a pizza."""
    time.sleep(1)
    return f"Baked a delicious {pizza_type} pizza"

@activity.defn
async def deliver_order(address: str) -> str:
    """Simulates delivering the order."""
    time.sleep(1)
    return f"Delivered to {address}"
