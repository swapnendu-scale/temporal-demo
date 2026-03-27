import uuid  # BUG 1: uuid.uuid4() is non-deterministic and blocked by Temporal's sandbox.
              # FIX: Remove this import and use workflow.uuid4() instead.
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from activities import charge_customer, prep_ingredients, bake_pizza, box_order, deliver_order

@workflow.defn
class KitchenWorkflow:
    @workflow.run
    async def prepare_food(self, pizza_type: str) -> str:
        await workflow.execute_activity(
            prep_ingredients,
            pizza_type,
            start_to_close_timeout=timedelta(seconds=30),
        )
        await workflow.execute_activity(
            bake_pizza,
            pizza_type,
            start_to_close_timeout=timedelta(seconds=30),
        )
        result = await workflow.execute_activity(
            box_order,
            pizza_type,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result

@workflow.defn
class PizzaOrderWorkflow:
    def __init__(self):
        self._stage = "received"

    @workflow.run
    async def process_order(self, customer_name: str, pizza_type: str, address: str, amount: int) -> str:
        # BUG 1: uuid.uuid4() is non-deterministic — Temporal's sandbox blocks it.
        # FIX: Replace with workflow.uuid4() which is deterministic across replays.
        order_id = str(uuid.uuid4())

        workflow.logger.info(f"Starting pizza order {order_id} for {customer_name}")

        self._stage = "charging"
        await workflow.execute_activity(
            charge_customer,
            args=[amount, order_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        self._stage = "kitchen"
        await workflow.execute_child_workflow(
            KitchenWorkflow.prepare_food,
            pizza_type,
            id=f"kitchen-{order_id}",
        )

        self._stage = "delivering"
        await workflow.execute_activity(
            deliver_order,
            address,
            start_to_close_timeout=timedelta(seconds=30),
        )

        self._stage = "complete"
        return f"Order for {customer_name} complete! 🍕"

    @workflow.query
    def stage(self) -> str:
        return self._stage
