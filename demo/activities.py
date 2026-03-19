import random
import time
from temporalio import activity

@activity.defn
async def charge_customer(amount: int) -> str:
    """
    Simulates charging a customer.
    """
    # INTENTIONAL BUG 2: Non-idempotent activity that randomly fails.
    # Temporal will retry this activity on failure. Because it appends to a file
    # *before* the potential failure, retries will result in duplicate charges!
    # In a real system, this could mean charging a credit card multiple times.
    
    with open("charges.txt", "a") as f:
        f.write(f"Charged ${amount}\n")
    
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
