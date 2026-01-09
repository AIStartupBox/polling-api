"""
State definition for the chat application.

This module defines the single AppState TypedDict used throughout the workflow.
All data is stored in a single 'state' dictionary for simplicity and minimal checkpoints.
"""

from typing import TypedDict, Dict, Any


class AppState(TypedDict):
    """
    Single state object for the entire workflow.

    All data lives in the 'state' dict as key-value pairs:
    - state["message"]: Original user input
    - state["ui"]: UI-specific data (message, current_node, status, progress)
    - state["data"]: Business logic data (reports, insights, etc.)
    - state["Interrupt"]: Interrupt control flag
    """
    state: Dict[str, Any]
    Interrupt: bool
