# Temporal Pizza Delivery Demo

This is a simple Temporal demo designed for live debugging presentations. It simulates a Pizza Delivery application with intentional bugs to demonstrate Temporal's core concepts: **Determinism** and **Idempotency**.

## 🍕 What is the Demo About?

The demo consists of a `PizzaOrderWorkflow` that orchestrates three main steps:
1. **Charge Customer** (Activity)
2. **Prepare Food** (Child Workflow -> Activity)
3. **Deliver Order** (Activity)

### The Intentional Bugs
The code contains two intentional bugs that will cause the workflow to fail or behave incorrectly:
1. **The Determinism Bug:** The `PizzaOrderWorkflow` uses `uuid.uuid4()` directly inside the workflow code. This breaks Temporal's determinism rule and will cause a `NonDeterministicWorkflowError` when the workflow tries to replay.
2. **The Idempotency Bug:** The `charge_customer` activity blindly appends a charge to a local `charges.txt` file and then randomly fails 50% of the time. Because Temporal automatically retries failed activities, this lack of idempotency will result in the customer being double (or triple) charged!

---

## 🚀 How to Install and Run

This project uses `uv` for fast Python dependency management.

### 1. Install Dependencies
Make sure you are in the `demo/` directory, then run:
```bash
uv sync
```

### 2. Start a Local Temporal Server
You need a local Temporal server running. If you have the Temporal CLI installed, run this in a separate terminal:
```bash
temporal server start-dev
```

### 3. Run the Worker
In a new terminal window, start the Temporal worker. This process listens to the task queue and executes your code.
```bash
uv run worker.py
```

### 4. Start the Workflow
In another terminal window, trigger the workflow:
```bash
uv run starter.py
```

### 5. Observe the Chaos
1. Open the Temporal Web UI at `http://localhost:8233`.
2. Look at the running workflow. You will likely see it failing with a `NonDeterministicWorkflowError`.
3. Look at the `charges.txt` file in your directory. You will see multiple duplicate charges for the same order because the activity is retrying and failing.

---

## 🛠️ How to Fix the Issues (Live Debugging)

During the presentation, you will live-code the fixes for these bugs.

### Fix 1: The Determinism Bug
**Issue:** `workflows.py` uses `uuid.uuid4()`.
**Fix:** Replace the standard Python UUID generation with Temporal's deterministic UUID generator.

*In `workflows.py`:*
```python
# REMOVE THIS:
# order_id = str(uuid.uuid4())

# ADD THIS:
order_id = str(workflow.uuid4())
```

### Fix 2: The Idempotency Bug
**Issue:** `activities.py` blindly writes to `charges.txt` without checking if the charge already happened.
**Fix:** Pass the `order_id` to the activity, and check if that `order_id` already exists in the file before writing.

*In `workflows.py`:*
```python
# Update the activity call to pass the order_id
await workflow.execute_activity(
    charge_customer,
    args=[amount, order_id], # Pass order_id here
    start_to_close_timeout=timedelta(seconds=10),
)
```

*In `activities.py`:*
```python
# Update the activity signature and add the idempotency check
@activity.defn
async def charge_customer(amount: int, order_id: str) -> str:
    # --- IDEMPOTENCY CHECK ---
    # Check if we already charged this order
    try:
        with open("charges.txt", "r") as f:
            if f"Order {order_id}" in f.read():
                return f"Already charged ${amount} for {order_id}"
    except FileNotFoundError:
        pass # File doesn't exist yet, that's fine
    # -------------------------

    with open("charges.txt", "a") as f:
        f.write(f"Order {order_id}: Charged ${amount}\n")
    
    time.sleep(1)
    
    if random.random() < 0.5:
        raise Exception("Network error while confirming charge with bank!")
        
    return f"Successfully charged ${amount}"
```

Once you save these changes and restart the `worker.py`, Temporal will seamlessly pick up where it left off, successfully complete the workflow, and stop double-charging the customer!