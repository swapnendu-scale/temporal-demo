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
*   *Tone change: A bit of a warning.*
*   "We all love Cursor and Copilot. They are great at generating syntax. But Temporal has strict, unforgiving rules. If you ask an AI to 'write a workflow that charges a user and sends an email', it will generate code that looks 100% correct in standard Python."
*   "But if you don't understand Temporal's rules, that AI-generated code will fail catastrophically in production. It will charge the user 5 times because it didn't use an idempotency key. Today is about giving you the knowledge to supervise the AI."

---

## 2. Scope & Boundaries (5 mins)

**Slide 4: What we won't cover**
*   "I want to respect your time. We are not talking about Kubernetes, Cassandra, or how to deploy Temporal servers. We aren't looking at the Rust core."
*   "We are focusing entirely on the application layer: how you write code, how you debug it, and how to avoid footguns."

---

## 3. Introducing the Demo Scenario (5 mins)

**[🎬 SCREEN SWITCH: Switch screen share to IDE (Cursor/VSCode)]**

*   **Transition:** "Before we talk about the rules of Temporal, let's look at the code we will be using today."
*   **The Scenario:** "We have a relatable scenario: A Pizza Delivery App."
*   **The Code:** Show them `demo/workflows.py` and `demo/activities.py`.
    *   `PizzaOrderWorkflow`: The main orchestrator.
    *   `KitchenWorkflow`: A child workflow for preparing the food.
    *   `charge_customer`, `bake_pizza`, `deliver_order`: The activities.
*   "Don't worry about the bugs in here yet. Just understand the flow: Charge -> Kitchen -> Deliver."

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

*   **Transition:** "Enough slides. We've seen the rules, now let's see what happens when we break them."

**[🎬 SCREEN SWITCH: Switch screen share to IDE (Cursor/VSCode)]**

*   **The Bugs:**
    *   Open `demo/workflows.py`. Point out `uuid.uuid4()` in the workflow. Ask the audience: *"Why is this bad?"* (Answer: Non-deterministic).
    *   Open `demo/activities.py`. Point out the `charge_customer` activity that writes to a file and randomly fails. Ask: *"What happens when Temporal retries this?"* (Answer: Duplicate charges).

**[🎬 SCREEN SWITCH: Switch screen share to Terminal]**

*   **The Run:**
    *   `cd demo`
    *   Run `uv run worker.py` in one tab.
    *   Run `uv run starter.py` in another tab.

**[🎬 SCREEN SWITCH: Switch screen share to Temporal Web UI (localhost:8233)]**

*   **The Investigation:**
    *   Show them the `NonDeterministicWorkflowError` in the UI. Explain how to read the Event History.
    *   Show them the activity retrying and the `charges.txt` file filling up with duplicate charges.

**[🎬 SCREEN SWITCH: Switch screen share back to IDE]**

*   **The Fix:**
    *   Live-code the fix. Move the UUID generation to an activity (or use Temporal's deterministic UUID).
    *   Add a check in the activity to prevent duplicate writes.
    *   Show how Temporal immediately recovers and finishes the workflow.

**[🎬 SCREEN SWITCH: Switch screen share back to Presentation Slides]**

---

## 6. IPS Implementation Critique & Best Practices (10 mins)

*   **Tone:** "This is a blameless review. We are all learning. I looked across our DUNE applications to find common anti-patterns."

**Critique 1: SJC - Sequential Execution**
*   *Reference the Sequential vs Parallel Diagram:* Show how the sequential graph is a straight line, while parallel fans out.
*   "In SJC, we have a loop checking page boundaries one by one. For a 100-page document, that's 100 sequential waits. Temporal can handle thousands of parallel activities. We should be using `asyncio.gather` to fan these out. Don't leave performance on the table."

**Critique 2: MOJ-SAK - Swallowing Exceptions**
*   "In SAK, a workflow wraps everything in a `try/except` and returns a 'Failed' string. **Never do this.** If you catch the exception, Temporal thinks the workflow succeeded. You lose all of Temporal's built-in retry and failure tracking. Let the errors bubble up!"

**Critique 3: MOEHE - Database Idempotency**
*   "Similar to the example earlier. Blind database inserts in activities will cause duplicates on retries. Always use `ON CONFLICT DO NOTHING` or check for existence first."

**Critique 4: MOEHE - Large Payloads**
*   "Passing massive JSON objects or full conversation histories into activities bloats the Temporal Event History. It slows down the system and can hit size limits. Pass an ID instead, and let the activity fetch the data."

**Critique 5: Council of Ministers - Redundant Waits**
*   "Setting a variable to True and immediately waiting for it to be True on the next line shows a misunderstanding of the async event loop. Keep your workflows clean."

---

## 7. FAQ & Common Questions (5 mins)

*   **Tone:** "Before we open the floor, here are two questions I get asked all the time."
*   **Child Workflows:** "Why use a child workflow? The biggest reason is Event History Limits. Temporal has a hard limit on how many events a single workflow can have. If you loop over 10,000 items and run an activity for each, your workflow will crash. Child workflows keep the main history clean. Also, it's great for reusability."
*   **Datetime:** "Can I use `datetime.now()`? No. Never. If the workflow crashes and replays tomorrow, `datetime.now()` will return tomorrow's date, breaking determinism. Always use `workflow.now()`."

---

## 8. Q&A (5 mins)

*   "What questions do you have?"
*   Have the Temporal documentation link ready to share in the chat.