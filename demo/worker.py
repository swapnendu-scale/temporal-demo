import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from activities import charge_customer, bake_pizza, deliver_order
from workflows import PizzaOrderWorkflow, KitchenWorkflow

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="pizza-tasks",
        workflows=[PizzaOrderWorkflow, KitchenWorkflow],
        activities=[charge_customer, bake_pizza, deliver_order],
    )
    print("Starting worker on task queue 'pizza-tasks'...")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
