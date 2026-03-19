import asyncio
from temporalio.client import Client
from workflows import PizzaOrderWorkflow

async def main():
    # Connect to the local Temporal server
    client = await Client.connect("localhost:7233")
    
    print("Starting Pizza Order Workflow...")
    
    # Execute the workflow
    result = await client.execute_workflow(
        PizzaOrderWorkflow.process_order,
        args=["Pepperoni", "123 Main St", 20],
        id="pizza-order-1",
        task_queue="pizza-tasks",
    )
    
    print(f"Workflow result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
