"""
Orchestrator node - Entry point of the workflow.

This node initializes the workflow and prepares for report identification.
"""

import asyncio
from typing import Dict, Any
from state import AppState


async def orchestrator(app_state: AppState) -> Dict[str, Any]:
    """
    Initialize workflow and prepare for report identification.

    Args:
        app_state: Current application state

    Returns:
        Updated state dict with UI status set to orchestrator step
    """
    # Check interrupt flag - if True, skip processing
    if app_state.get("Interrupt", False):
        return {"state": app_state["state"].copy(), "Interrupt": True}

    # Copy current state to avoid mutation issues
    current = app_state["state"].copy()

    # Simulate some processing time
    await asyncio.sleep(0.5)

    # Update UI state for this node
    current["ui"] = {
        "message": "🔍 Identifying relevant reports...",
        "current_node": "orchestrator",
        "status": "running",
        "progress": {"current": 1, "total": 4}
    }

    # Initialize data dict if not exists
    if "data" not in current:
        current["data"] = {}

    current["data"]["step"] = "orchestrator_complete"
    current["data"]["user_query"] = current.get("message", "")

    return {"state": current, "Interrupt": False}
