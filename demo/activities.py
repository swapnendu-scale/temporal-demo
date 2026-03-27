import random
import time
from temporalio import activity

@activity.defn
async def charge_customer(amount: int, order_id: str) -> str:
    try:
        with open("charges.txt", "r") as f:
            if f"Order {order_id}" in f.read():
                return f"Already charged ${amount} for {order_id}"
    except FileNotFoundError:
        pass

    with open("charges.txt", "a") as f:
        f.write(f"Order {order_id}: Charged ${amount}\n")

    time.sleep(random.uniform(2, 3))

    if random.random() < 0.5:
        raise Exception("Network error while confirming charge with bank!")

    return f"Successfully charged ${amount}"

@activity.defn
async def prep_ingredients(pizza_type: str) -> str:
    time.sleep(random.uniform(2, 4))
    return f"Prepped ingredients for {pizza_type}"

@activity.defn
async def bake_pizza(pizza_type: str) -> str:
    time.sleep(random.uniform(5, 8))
    return f"Baked a delicious {pizza_type} pizza"

@activity.defn
async def box_order(pizza_type: str) -> str:
    time.sleep(random.uniform(1, 2))
    return f"Boxed {pizza_type} pizza for delivery"

@activity.defn
async def deliver_order(address: str) -> str:
    time.sleep(random.uniform(3, 5))
    return f"Delivered to {address}"
