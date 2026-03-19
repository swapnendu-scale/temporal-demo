import uuid
from datetime import timedelta
from temporalio import workflow

# Import activity, passing it in through the environment or directly
with workflow.unsafe.imports_passed_through():
    from activities import charge_customer, bake_pizza, deliver_order

@workflow.defn
class KitchenWorkflow:
    @workflow.run
    async def prepare_food(self, pizza_type: str) -> str:
        # In a real app, this might have multiple steps: prep, bake, box
        # We use a child workflow to encapsulate this complexity.
        result = await workflow.execute_activity(
            bake_pizza,
            pizza_type,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return result

@workflow.defn
class PizzaOrderWorkflow:
    @workflow.run
    async def process_order(self, pizza_type: str, address: str, amount: int) -> str:
        # INTENTIONAL BUG 1: Non-deterministic code inside a workflow.
        # Workflows must be deterministic. Using uuid.uuid4() or requests.get() 
        # directly in the workflow code will break Temporal's replay mechanism.
        # This should be done inside an Activity or using workflow.uuid4().
        
        order_id = str(uuid.uuid4())
        
        workflow.logger.info(f"Starting pizza order {order_id}")
        
        # 1. Charge the customer (Activity)
        await workflow.execute_activity(
            charge_customer,
            amount,
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        # 2. Send to Kitchen (Child Workflow)
        # We use a child workflow here because the kitchen process is complex,
        # might take a long time, and we want to keep our main workflow history clean.
        await workflow.execute_child_workflow(
            KitchenWorkflow.prepare_food,
            pizza_type,
            id=f"kitchen-{order_id}",
        )
        
        # 3. Deliver the pizza (Activity)
        await workflow.execute_activity(
            deliver_order,
            address,
            start_to_close_timeout=timedelta(seconds=10),
        )
        
        return f"Order {order_id} complete!"
