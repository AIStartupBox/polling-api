"""
Debug script to inspect the LangGraph snapshot structure when interrupted.
"""

import asyncio
from workflow.graph import graph

async def test_interrupt():
    """Test the interrupt and inspect the snapshot."""
    # Configure thread
    thread_id = "debug-test"
    config = {"configurable": {"thread_id": thread_id}}

    # Initialize state
    initial_state = {
        "state": {
            "message": "test query",
            "ui": {
                "message": "Starting...",
                "current_node": "orchestrator",
                "status": "running",
                "progress": {"current": 0, "total": 4}
            },
            "data": {}
        }
    }

    print("Starting workflow...")
    # Run the graph until it hits the interrupt
    async for event in graph.astream(initial_state, config):
        print(f"Event: {event}")

    # Now check the snapshot when interrupted
    print("\n=== Checking snapshot after interrupt ===")
    snapshot = graph.get_state(config)

    print(f"snapshot.values: {snapshot.values}")
    print(f"snapshot.next: {snapshot.next}")
    print(f"has tasks attr: {hasattr(snapshot, 'tasks')}")
    if hasattr(snapshot, 'tasks'):
        print(f"snapshot.tasks: {snapshot.tasks}")
    print(f"has metadata attr: {hasattr(snapshot, 'metadata')}")
    if hasattr(snapshot, 'metadata'):
        print(f"snapshot.metadata: {snapshot.metadata}")

    print(f"\nAll snapshot attributes: {dir(snapshot)}")

if __name__ == "__main__":
    asyncio.run(test_interrupt())
