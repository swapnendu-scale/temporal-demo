# Presenter Notes: Temporal in Practice

**Context:** You are presenting to a mixed audience of Engineers, Engineering Directors, and PMs. Your goal is to move past theory and show them *how to survive* using Temporal, especially when using AI coding tools. Keep the tone engaging, practical, and a bit cautionary when talking about AI.

---

## 1. The Big Picture & The "Vibe-Coding" Era (10 mins)

**Slide 1: What is Temporal?**
*   **To the PMs/Directors:** "Imagine never having to write a retry loop or a complex cron job again. Temporal is our safety net. If a server goes up in flames while processing a user's file, Temporal remembers exactly where it was and picks up the pieces when the server comes back."
*   **To the Engineers:** "It's durable execution. You write standard Python code, but Temporal saves the state of every single variable and function call. It replaces message queues and state machines."
*   *Reference the Architecture Diagram:* Point out how the "Temporal Server" sits in the middle, just handing out tasks to our "Workers". Our code lives entirely in the Workers.

**Slide 2: The IPS Ecosystem**
*   "We rely on this heavily. Dex uses it for document parsing. Agentx uses it to orchestrate agents. If you are building a complex pipeline in IPS, you will likely interact with Temporal."

**Slide 3: AI & Temporal: The "Vibe-Coding" Dilemma**
*   *Tone change: A bit of a warning, but empowering.*
*   "We all love Cursor and Copilot. In fact, they probably write most of our code now. But Temporal has strict, unforgiving rules. If you ask an AI to 'write a workflow that charges a user and sends an email', it will generate code that looks 100% correct in standard Python."
*   "But if you don't understand Temporal's rules, that AI-generated code will fail catastrophically in production. It might charge the user 5 times because the AI didn't know to use an idempotency key."
*   "Your job as a modern engineer isn't just typing; it's being the architect. You need to know the best practices for Workflows, Activities, Workers, Task Queues, and Idempotency so you can review and guide the AI. Today is about giving you that architectural intuition."

---

## 2. Scope & Boundaries (5 mins)

**Slide 4: What we won't cover**
*   "I want to respect your time. We are not talking about Kubernetes, Cassandra, or how to deploy Temporal servers. We aren't looking at the Rust core."
*   "We are focusing entirely on the application layer: how you write code, how you debug it, and how to avoid footguns."

---

## 3. Introducing the Demo Scenario (5 mins)

**[🎬 SCREEN SWITCH: Switch screen share to IDE (Cursor/VSCode)]**

*   **Transition:** "Before we talk about the rules of Temporal, let's look at the code we will be using today."
*   **The Scenario:** "We have a relatable scenario: A Pizza Delivery App with a full web UI."
*   **The Code:** Show them `demo/workflows.py` and `demo/activities.py`.
    *   `PizzaOrderWorkflow`: The main orchestrator.
    *   `KitchenWorkflow`: A child workflow for preparing the food.
    *   `charge_customer`, `prep_ingredients`, `bake_pizza`, `box_order`, `deliver_order`: The activities.
*   "Don't worry about the bugs in here yet. Just understand the flow: Charge -> Kitchen (Prep -> Bake -> Box) -> Deliver."

**[🎬 SCREEN SWITCH: Switch screen share back to Presentation Slides]**

---

## 4. Core Concepts Grounded in Reality (15 mins)

**Slide 5: Workflows vs. Activities vs. Child Workflows**
*   "This is the most important slide of the day."
*   *Reference the Diagram:* Show how the Main Workflow schedules activities directly, but also spins off a Child Workflow for the kitchen.
*   "**Workflows are the orchestrator.** They are the brain. The golden rule: They must be 100% deterministic."
*   "What does deterministic mean? It means if Temporal replays your workflow code from the top, it must take the exact same path and schedule the exact same activities in the exact same order."
*   "A common misconception: People think an LLM call is non-deterministic because the text it generates might be different. While true, the real reason it breaks Temporal is because the network call might fail! If it fails with a 500 error during a replay, your workflow takes a different path (an exception block) than it did the first time. That crashes Temporal."
*   "Therefore: No random numbers, no API calls, no `datetime.now()`. If you break this rule, Temporal crashes."
*   "**Activities are the hands.** This is where the dirty work happens. Database calls, API requests, file I/O. If an activity fails, Temporal will retry it automatically."
*   "**Child Workflows are sub-orchestrators.** Why did we make the Kitchen a child workflow instead of just activities? Because the kitchen process is complex (prep, bake, box). If we put all that in the main workflow, the main event history gets huge. Child workflows keep the main history clean and allow us to reuse the kitchen logic for in-store orders."

**Slide 6: Idempotency**
*   "Because activities are retried automatically, they must be safe to run multiple times. This is called idempotency."
*   *Compare the two examples:* "Look at our demo's `charge_customer` activity. It blindly appends a charge to a file and then randomly fails. When Temporal retries it, it appends *another* charge. The customer gets double-charged! AI will write this bad version unless you tell it otherwise."
*   "The fix is simple: Pass a unique transaction ID. Before writing to the file or database, check if that ID has already been processed. If it has, return success immediately."

**Slide 7: Signals vs. Polling**
*   "How do we wait for a human to approve a charge, or an ML model to finish? You have two choices."
*   *Reference the Polling vs Signals Diagram:* Point out the loop vs the push model.
*   "Polling is a `while` loop that sleeps and checks a database. It's easy, but it clutters the history."
*   "Signals are the alternative. The workflow goes to sleep indefinitely until a user clicks 'Approve' in an email, which sends a webhook to wake it up. Choose wisely based on your architecture."

---

## 5. Interactive Live Debugging Demo (20 mins)

*   **Transition:** "Enough slides. We've seen the rules, now let's see what happens when we break them. I asked Copilot to write me a pizza delivery workflow. It looks perfectly fine to a standard Python developer. Let's run it and see what happens."

**[🎬 SCREEN SWITCH: Run `just broken`, open Pizza UI at localhost:3000, open Temporal UI at localhost:8233]**

*   **Place an order** through the Pizza UI so the audience can see a named workflow in the Temporal UI.

### Bug 1: The Determinism Bug

*   The workflow immediately fails. Show the error in the Temporal Web UI: `RestrictedWorkflowAccessError: Cannot access uuid.uuid4.__call__`
*   "Temporal's Python SDK includes a sandbox that catches non-deterministic calls before they even run. It saw `uuid.uuid4()` and blocked it. This is Temporal protecting you."
*   Ask the audience: *"How would you fix this?"*
*   Explain: `uuid.uuid4()` generates a random value. If the workflow replays, it would generate a different value, breaking determinism. Temporal provides `workflow.uuid4()` which is seeded from the event history -- same value on every replay.
*   **Do the fix live:** Replace `uuid.uuid4()` with `workflow.uuid4()`, and remove the `import uuid` line.
*   Save the file -- uvicorn auto-reloads, the worker picks up the change, and the workflow starts progressing.

### Bug 2: The Idempotency Bug

*   The workflow is progressing now. But look at the **Payment Ledger** panel in the Pizza UI.
*   The `charge_customer` activity randomly fails 75% of the time. On retries, it writes another charge with the same order ID.
*   "Look at the ledger -- the same order ID appears 3, 4, 5 times. The customer just got charged $75 for a $15 pizza. This is the #1 production bug in Temporal applications."
*   **Do the fix live:** Open `activities.py`. Add an idempotency check at the top of `charge_customer`: read `charges.txt`, check if the order ID is already there, return immediately if so.
*   The commented-out code in the file shows exactly what to uncomment.

*   **The Payoff:** Run `just fixed`. Place another order. Show the Payment Ledger -- exactly one charge per order, even though the activity still fails and retries. The idempotency check skips the duplicate writes.

**[🎬 SCREEN SWITCH: Switch screen share back to Presentation Slides]**

---

## 6. IPS Implementation Critique & Best Practices (10 mins)

*   **Tone:** "This is a blameless review. We are all learning. I looked across our DUNE applications to find common anti-patterns. But more importantly, **these are the exact anti-patterns AI will generate by default.** When you review AI-generated code, these are the mistakes you need to catch."

**Critique 1: SJC - Sequential Execution**
*   *Reference the Sequential vs Parallel Diagram:* Show how the sequential graph is a straight line, while parallel fans out.
*   "If you ask Cursor to process a 100-page document, it will write a sequential `for` loop like this. As the architect, you need to spot this and say 'No, rewrite this to fan-out using `asyncio.gather`.' Don't leave performance on the table."

**Critique 2: MOJ-SAK - Swallowing Exceptions**
*   "In SAK, a workflow wraps everything in a `try/except` and returns a 'Failed' string. This is standard defensive programming in normal Python, so AI loves doing it. But in Temporal, **never do this.** If you catch the exception, Temporal thinks the workflow succeeded. You lose all of Temporal's built-in retry and failure tracking. Let the errors bubble up!"

**Critique 3: MOEHE - Database Idempotency**
*   "Standard SQLAlchemy/Prisma code generated by AI usually lacks deduplication logic. Blind database inserts in activities will cause duplicates on retries. Always use `ON CONFLICT DO NOTHING` or check for existence first."

**Critique 4: MOEHE - Large Payloads**
*   "Passing massive JSON objects or full conversation histories into activities bloats the Temporal Event History. It slows down the system and can hit size limits. Pass an ID instead, and let the activity fetch the data."

**Critique 5: Council of Ministers - Redundant Waits**
*   "Setting a variable to True and immediately waiting for it to be True on the next line shows a misunderstanding of the async event loop. Keep your workflows clean."

---

## 7. FAQ & Common Questions (5 mins)

*   **Tone:** "Before we open the floor, here are two questions I get asked all the time."
*   **Child Workflows:** "Why use a child workflow? The biggest reason is Event History Limits. Temporal has a hard limit on how many events a single workflow can have. If you loop over 10,000 items and run an activity for each, your workflow will crash. Child workflows keep the main history clean. Also, it's great for reusability."
*   **Datetime:** "Can I use `datetime.now()`? No. Never. If the workflow crashes and replays tomorrow, `datetime.now()` will return tomorrow's date, breaking determinism. Always use `workflow.now()`. **Pro-tip: If you are reviewing a PR written by an LLM, this is the very first thing you should `Ctrl+F` for in the workflow file.**"

---

## 8. Q&A (5 mins)

*   "What questions do you have?"
*   Have the Temporal documentation link ready to share in the chat.