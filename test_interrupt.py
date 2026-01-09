"""
Test script for interrupt and approval workflow.

This script demonstrates the complete flow:
1. Start a workflow
2. Poll until interrupt
3. Approve/reject the workflow
4. Continue polling until completion
"""

import requests
import time
import sys

API_URL = "http://localhost:8000/chat"


def test_interrupt_workflow(approve: bool = True):
    """
    Test the interrupt workflow with approval/rejection.

    Args:
        approve: True to approve, False to reject
    """
    print("=" * 60)
    print("Testing Interrupt Workflow")
    print(f"Action: {'APPROVE' if approve else 'REJECT'}")
    print("=" * 60)

    # Step 1: Start workflow
    print("\n[Step 1] Starting workflow...")
    response = requests.post(API_URL, json={"message": "Analyze Q4 sales report"})

    if response.status_code != 200:
        print(f"❌ Failed to start workflow: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    thread_id = data["thread_id"]
    print(f"✅ Workflow started: {thread_id}")
    print(f"   Status: {data['status']}")
    print(f"   Message: {data['message']}")

    # Step 2: Poll until we need approval
    print("\n[Step 2] Polling for status...")
    poll_count = 0
    max_polls = 20

    while poll_count < max_polls:
        time.sleep(2)
        poll_count += 1

        response = requests.post(API_URL, json={"thread_id": thread_id})

        if response.status_code != 200:
            print(f"❌ Polling failed: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        print(f"\n   Poll #{poll_count}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")
        print(f"   Current Node: {data['current_node']}")
        print(f"   Progress: {data['progress']['current']}/{data['progress']['total']}")
        print(f"   Requires Approval: {data.get('requires_approval', False)}")

        # Check if approval is required
        if data.get("requires_approval", False):
            print("\n⚠️  INTERRUPT DETECTED - Approval Required!")
            print(f"   Data: {data.get('data', {})}")
            break

        # Check if workflow is done (shouldn't happen before approval)
        if data["status"] in ["completed", "failed"]:
            print(f"\n⚠️  Workflow ended without interrupt: {data['status']}")
            return

    if poll_count >= max_polls:
        print("\n❌ Max polls reached without interrupt")
        return

    # Step 3: Send approval/rejection
    print(f"\n[Step 3] Sending {'approval' if approve else 'rejection'}...")
    response = requests.post(API_URL, json={
        "thread_id": thread_id,
        "approved": approve
    })

    if response.status_code != 200:
        print(f"❌ Failed to send approval: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    print(f"✅ Response received:")
    print(f"   Status: {data['status']}")
    print(f"   Message: {data['message']}")

    if not approve:
        print("\n✅ Workflow successfully cancelled!")
        return

    # Step 4: Continue polling until completion
    print("\n[Step 4] Continuing to poll until completion...")
    poll_count = 0

    while poll_count < max_polls:
        time.sleep(2)
        poll_count += 1

        response = requests.post(API_URL, json={"thread_id": thread_id})

        if response.status_code != 200:
            print(f"❌ Polling failed: {response.status_code}")
            return

        data = response.json()
        print(f"\n   Poll #{poll_count}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")
        print(f"   Current Node: {data['current_node']}")
        print(f"   Progress: {data['progress']['current']}/{data['progress']['total']}")

        # Check if workflow is done
        if data["status"] == "completed":
            print("\n✅ WORKFLOW COMPLETED SUCCESSFULLY!")
            print(f"\n   Final Data:")
            for key, value in data.get("data", {}).items():
                print(f"   - {key}: {value}")
            return
        elif data["status"] == "failed":
            print(f"\n❌ Workflow failed: {data['message']}")
            return

    print("\n❌ Max polls reached without completion")


if __name__ == "__main__":
    # Test with approval by default
    approve = True

    # Allow command line argument to test rejection
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ["reject", "false", "no"]:
            approve = False

    try:
        test_interrupt_workflow(approve)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   uvicorn main:app --reload")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
