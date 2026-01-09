"""
LangGraph state machine assembly with MongoDB checkpointing.

This module creates the StateGraph, adds all nodes, defines edges,
and configures MongoDB persistence for checkpoint storage.
"""

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


def create_graph():
    """
    Create and compile the LangGraph state machine.

    Returns:
        Compiled StateGraph with MongoDB checkpointing enabled
    """
    # Initialize MongoDB client and checkpointer
    # Connection string: mongodb://localhost:27017
    # Database: chat_checkpoints
    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
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

    # Compile the graph with checkpointer
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    return compiled_graph


# Create the graph instance at module level for import
graph = create_graph()
