"""
LangGraph state machine assembly with MongoDB checkpointing.

This module creates the StateGraph, adds all nodes, defines edges,
and configures MongoDB persistence for checkpoint storage.
"""

import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

from state import AppState
from workflow.nodes import (
    orchestrator,
    report_identifier,
    report_runner,
    summary_agent
)

# Global MongoDB client for checkpoint cleanup
mongo_client = None
load_dotenv()


def create_graph():
    """
    Create and compile the LangGraph state machine.

    Returns:
        Compiled StateGraph with MongoDB checkpointing enabled
    """
    global mongo_client

    # Initialize MongoDB client and checkpointer
    # Connection string: mongodb://localhost:27017
    # Database: chat_checkpoints
    try:
        client = MongoClient(os.getenv("MONGO_DB_URI"), serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        mongo_client = client  # Store globally for cleanup
        checkpointer = MongoDBSaver(client, "chat_checkpoints")
    except Exception as e:
        print(f"Warning: MongoDB connection failed: {e}")
        print("Running without persistence. Install and start MongoDB for checkpoint support.")
        checkpointer = None

    # Create the StateGraph
    workflow = StateGraph(AppState)

    # Add all nodes
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("report_identifier", report_identifier)
    workflow.add_node("report_runner", report_runner)
    workflow.add_node("summary_agent", summary_agent)

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Define sequential edges
    workflow.add_edge("orchestrator", "report_identifier")
    workflow.add_edge("report_identifier", "report_runner")
    workflow.add_edge("report_runner", "summary_agent")
    workflow.add_edge("summary_agent", END)

    # Compile the graph with checkpointer and interrupt before report_identifier
    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["report_identifier"]
    )

    return compiled_graph


def cleanup_checkpoints(thread_id: str) -> bool:
    """
    Delete all MongoDB checkpoints for a specific thread_id.

    This removes all checkpoint data from both 'checkpoints' and 'checkpoint_writes'
    collections to prevent database bloat after workflow completion.

    Args:
        thread_id: The thread identifier whose checkpoints should be deleted

    Returns:
        True if cleanup was successful, False otherwise
    """
    global mongo_client

    if not mongo_client:
        print(f"Warning: Cannot cleanup checkpoints - MongoDB client not available")
        return False

    try:
        db = mongo_client["chat_checkpoints"]

        # Delete from checkpoints collection
        checkpoints_result = db["checkpoints"].delete_many({"thread_id": thread_id})
        checkpoints_deleted = checkpoints_result.deleted_count

        # Delete from checkpoint_writes collection
        writes_result = db["checkpoint_writes"].delete_many({"thread_id": thread_id})
        writes_deleted = writes_result.deleted_count

        print(f"✅ Cleanup complete for thread {thread_id}: "
              f"Deleted {checkpoints_deleted} checkpoints and {writes_deleted} writes")
        return True

    except Exception as e:
        print(f"❌ Error cleaning up checkpoints for thread {thread_id}: {e}")
        return False


# Create the graph instance at module level for import
graph = create_graph()
