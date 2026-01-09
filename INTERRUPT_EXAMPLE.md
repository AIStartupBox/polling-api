# Interrupt and Approval Workflow Example

This document demonstrates how to use the new interrupt and approval feature in the polling API.

## Overview

The workflow now pauses before the `report_identifier` node and waits for user approval. The client can either approve to continue or reject to cancel the workflow.

## API Flow

### Step 1: Start a New Workflow

**Request:**
```bash
POST /chat
Content-Type: application/json

{
  "message": "Analyze Q4 sales report"
}
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "🚀 Starting analysis...",
  "current_node": "initializing",
  "progress": {"current": 0, "total": 4},
  "data": {},
  "retry_after": 2,
  "requires_approval": false
}
```

### Step 2: Poll for Status (Workflow reaches interrupt point)

**Request:**
```bash
POST /chat
Content-Type: application/json

{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Waiting for Approval):**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "waiting_approval",
  "message": "🔍 Reports identified. Waiting for approval to proceed...",
  "current_node": "orchestrator",
  "progress": {"current": 1, "total": 4},
  "data": {
    "step": "orchestrator_complete",
    "user_query": "Analyze Q4 sales report"
  },
  "retry_after": 2,
  "requires_approval": true  ← Indicates workflow needs approval
}
```

### Step 3a: Approve and Continue

**Request (Approve):**
```bash
POST /chat
Content-Type: application/json

{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved": true
}
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "✅ Approved! Continuing with report identification...",
  "current_node": "report_identifier",
  "progress": {"current": 2, "total": 4},
  "data": {...},
  "retry_after": 2,
  "requires_approval": false
}
```

Now continue polling until `status` becomes `"completed"`.

### Step 3b: Reject and Cancel (Alternative)

**Request (Reject):**
```bash
POST /chat
Content-Type: application/json

{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "approved": false
}
```

**Response:**
```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "message": "❌ Workflow cancelled by user",
  "current_node": "cancelled",
  "progress": {"current": 1, "total": 4},
  "data": {...},
  "retry_after": null,
  "requires_approval": false
}
```

The workflow stops and no further processing happens.

## Client Implementation Example

### Python Example

```python
import requests
import time

API_URL = "http://localhost:8000/chat"

# Step 1: Start workflow
response = requests.post(API_URL, json={"message": "Analyze Q4 sales report"})
data = response.json()
thread_id = data["thread_id"]
print(f"Started workflow: {thread_id}")

# Step 2: Poll until we need approval
while True:
    time.sleep(2)
    response = requests.post(API_URL, json={"thread_id": thread_id})
    data = response.json()

    print(f"Status: {data['status']}, Message: {data['message']}")

    # Check if approval is required
    if data.get("requires_approval", False):
        print("\n⚠️  Workflow requires approval!")
        print(f"Current data: {data['data']}")

        # Prompt user for approval
        user_input = input("Do you want to proceed? (yes/no): ").strip().lower()

        if user_input == "yes":
            # Send approval
            response = requests.post(API_URL, json={
                "thread_id": thread_id,
                "approved": True
            })
            print("✅ Approved! Workflow continuing...")
        else:
            # Send rejection
            response = requests.post(API_URL, json={
                "thread_id": thread_id,
                "approved": False
            })
            print("❌ Workflow cancelled.")
            break

    # Check if workflow is done
    if data["status"] in ["completed", "failed"]:
        print(f"\nWorkflow finished: {data['status']}")
        print(f"Final data: {data['data']}")
        break
```

### JavaScript/TypeScript Example

```typescript
async function runWorkflowWithApproval() {
  const API_URL = "http://localhost:8000/chat";

  // Step 1: Start workflow
  let response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: "Analyze Q4 sales report" })
  });

  let data = await response.json();
  const threadId = data.thread_id;
  console.log(`Started workflow: ${threadId}`);

  // Step 2: Poll for status
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 2000));

    response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ thread_id: threadId })
    });

    data = await response.json();
    console.log(`Status: ${data.status}, Message: ${data.message}`);

    // Check if approval is required
    if (data.requires_approval) {
      console.log("⚠️  Workflow requires approval!");
      console.log(`Current data:`, data.data);

      // In a real app, show a UI dialog here
      const approved = confirm("Do you want to proceed with the workflow?");

      response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          approved: approved
        })
      });

      if (!approved) {
        console.log("❌ Workflow cancelled.");
        break;
      }

      console.log("✅ Approved! Workflow continuing...");
    }

    // Check if workflow is done
    if (data.status === "completed" || data.status === "failed") {
      console.log(`\nWorkflow finished: ${data.status}`);
      console.log("Final data:", data.data);
      break;
    }
  }
}

runWorkflowWithApproval();
```

## Key Points

1. **requires_approval field**: When `true`, the client should prompt the user for approval
2. **approved field**: Send `true` to continue, `false` to cancel
3. **status field**: Watch for `"waiting_approval"` status to detect interrupt state
4. **Workflow resumes automatically**: After approval, the graph continues from where it stopped
5. **Cancellation is final**: Once rejected, the workflow cannot be resumed

## Testing with cURL

```bash
# 1. Start workflow
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze Q4 sales report"}'

# Save the thread_id from response

# 2. Poll for status
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "YOUR_THREAD_ID"}'

# 3. When requires_approval is true, approve:
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "YOUR_THREAD_ID", "approved": true}'

# Or reject:
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "YOUR_THREAD_ID", "approved": false}'
```

## How It Works Internally

1. The `graph.py` compiles with `interrupt_before=["report_identifier"]`
2. When the workflow reaches the `report_identifier` node, LangGraph pauses execution
3. The state is checkpointed to MongoDB in an "interrupted" state
4. When polling, the `snapshot.next` field contains `["report_identifier"]`, indicating the interrupt
5. Sending `approved: true` calls `graph.update_state(config, None)` which resumes execution
6. Sending `approved: false` updates the state with a failed status and stops the workflow
