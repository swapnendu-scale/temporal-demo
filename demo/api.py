import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from temporalio.client import Client, WorkflowExecutionStatus
from temporalio.worker import Worker

from activities import charge_customer, prep_ingredients, bake_pizza, box_order, deliver_order
from workflows import PizzaOrderWorkflow, KitchenWorkflow

TASK_QUEUE = "pizza-tasks"

PIZZA_PRICES = {
    "Pepperoni": 18,
    "Margherita": 15,
    "BBQ Chicken": 22,
    "Hawaiian": 17,
}

temporal_client: Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    worker = Worker(
        temporal_client,
        task_queue=TASK_QUEUE,
        workflows=[PizzaOrderWorkflow, KitchenWorkflow],
        activities=[charge_customer, prep_ingredients, bake_pizza, box_order, deliver_order],
    )
    worker_task = asyncio.create_task(worker.run())
    print(f"Worker listening on task queue '{TASK_QUEUE}'...")
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Pizza Delivery API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    customer_name: str
    pizza_type: str
    address: str


class OrderResponse(BaseModel):
    workflow_id: str
    customer_name: str
    pizza_type: str
    address: str
    amount: int
    stage: str
    status: str


@app.post("/orders", response_model=OrderResponse)
async def create_order(req: OrderRequest):
    amount = PIZZA_PRICES.get(req.pizza_type)
    if amount is None:
        raise HTTPException(400, f"Unknown pizza type: {req.pizza_type}. Choose from: {list(PIZZA_PRICES.keys())}")

    workflow_id = f"pizza-{req.customer_name.lower().replace(' ', '-')}-{int(time.time())}"

    await temporal_client.start_workflow(
        PizzaOrderWorkflow.process_order,
        args=[req.customer_name, req.pizza_type, req.address, amount],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    return OrderResponse(
        workflow_id=workflow_id,
        customer_name=req.customer_name,
        pizza_type=req.pizza_type,
        address=req.address,
        amount=amount,
        stage="received",
        status="RUNNING",
    )


@app.get("/orders", response_model=list[OrderResponse])
async def list_orders():
    orders = []
    async for wf in temporal_client.list_workflows('WorkflowType = "PizzaOrderWorkflow"'):
        stage = "unknown"
        status_name = wf.status.name if wf.status else "UNKNOWN"

        if wf.status == WorkflowExecutionStatus.RUNNING:
            try:
                handle = temporal_client.get_workflow_handle(wf.id)
                stage = await handle.query(PizzaOrderWorkflow.stage)
            except Exception:
                stage = "unknown"
        elif wf.status == WorkflowExecutionStatus.COMPLETED:
            stage = "complete"
        elif wf.status == WorkflowExecutionStatus.FAILED:
            stage = "failed"

        parts = wf.id.split("-")
        name = " ".join(parts[1:-1]).title() if len(parts) >= 3 else wf.id

        orders.append(OrderResponse(
            workflow_id=wf.id,
            customer_name=name,
            pizza_type="",
            address="",
            amount=0,
            stage=stage,
            status=status_name,
        ))

    return orders


@app.get("/orders/{workflow_id}", response_model=OrderResponse)
async def get_order(workflow_id: str):
    handle = temporal_client.get_workflow_handle(workflow_id)
    try:
        desc = await handle.describe()
    except Exception:
        raise HTTPException(404, "Order not found")

    status_name = desc.status.name if desc.status else "UNKNOWN"
    stage = "unknown"

    if desc.status == WorkflowExecutionStatus.RUNNING:
        try:
            stage = await handle.query(PizzaOrderWorkflow.stage)
        except Exception:
            stage = "unknown"
    elif desc.status == WorkflowExecutionStatus.COMPLETED:
        stage = "complete"
    elif desc.status == WorkflowExecutionStatus.FAILED:
        stage = "failed"

    parts = workflow_id.split("-")
    name = " ".join(parts[1:-1]).title() if len(parts) >= 3 else workflow_id

    return OrderResponse(
        workflow_id=workflow_id,
        customer_name=name,
        pizza_type="",
        address="",
        amount=0,
        stage=stage,
        status=status_name,
    )


class ChargeEntry(BaseModel):
    line: str
    amount: int
    order_id: str | None


class ChargesResponse(BaseModel):
    entries: list[ChargeEntry]
    total: int
    count: int


@app.get("/charges", response_model=ChargesResponse)
async def get_charges():
    entries = []
    try:
        with open("charges.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                amount = 0
                order_id = None
                if line.startswith("Order "):
                    parts = line.split(": Charged $")
                    if len(parts) == 2:
                        order_id = parts[0].replace("Order ", "")
                        amount = int(parts[1])
                elif line.startswith("Charged $"):
                    amount = int(line.replace("Charged $", ""))
                entries.append(ChargeEntry(line=line, amount=amount, order_id=order_id))
    except FileNotFoundError:
        pass

    return ChargesResponse(
        entries=entries,
        total=sum(e.amount for e in entries),
        count=len(entries),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
