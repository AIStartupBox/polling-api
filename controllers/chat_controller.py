"""
Chat controller - Single POST /chat endpoint for new requests and polling.

Handles both initiating new workflows and polling existing ones.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from workflow.graph import graph


# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: Optional[str] = None
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    thread_id: str
    status: Literal["running", "completed", "failed"]
    message: str
    current_node: str
    progress: Dict[str, int]
    data: Dict[str, Any]
    retry_after: Optional[int]


# Create router
router = APIRouter(prefix="/chat", tags=["chat"])


async def run_background_graph(thread_id: str, user_message: str):
    """
    Execute the graph workflow in the background.

    Args:
        thread_id: Unique thread identifier
        user_message: User's input message
    """
    try:
        # Initialize state
        initial_state = {
            "state": {
                "message": user_message,
                "ui": {
                    "message": "Starting workflow...",
                    "current_node": "orchestrator",
                    "status": "running",
                    "progress": {"current": 0, "total": 4}
                },
                "data": {}
            }
        }

        # Configure thread
        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph
        async for event in graph.astream(initial_state, config):
            # Events are streamed but we don't need to do anything here
            # The graph automatically saves checkpoints to MongoDB
            pass

    except Exception as e:
        # If graph execution fails, save error state
        print(f"Error in background graph execution: {e}")
        try:
            error_state = {
                "state": {
                    "message": user_message,
                    "ui": {
                        "message": f"❌ Workflow failed: {str(e)}",
                        "current_node": "error",
                        "status": "failed",
                        "progress": {"current": 0, "total": 4}
                    },
                    "data": {"error": str(e)}
                }
            }
            config = {"configurable": {"thread_id": thread_id}}
            # Update state with error
            await graph.aupdate_state(config, error_state)
        except Exception as update_error:
            print(f"Failed to update error state: {update_error}")


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Single endpoint for both creating new workflows and polling existing ones.

    For new workflow:
        POST /chat {"message": "Analyze Q4 sales report"}

    For polling:
        POST /chat {"thread_id": "uuid-from-first-response"}

    Args:
        request: ChatRequest with either message (new) or thread_id (poll)

    Returns:
        ChatResponse with current workflow status and data

    Raises:
        HTTPException: 400 if neither message nor thread_id provided
        HTTPException: 404 if thread_id not found
    """
    # NEW workflow request
    if not request.thread_id and request.message:
        # Generate new thread ID
        thread_id = str(uuid.uuid4())

        # Start background execution
        asyncio.create_task(run_background_graph(thread_id, request.message))

        # Return initial response immediately
        return ChatResponse(
            thread_id=thread_id,
            status="running",
            message="🚀 Starting analysis...",
            current_node="initializing",
            progress={"current": 0, "total": 4},
            data={},
            retry_after=2
        )

    # POLL existing workflow
    elif request.thread_id:
        try:
            # Get current state snapshot
            config = {"configurable": {"thread_id": request.thread_id}}
            snapshot = graph.get_state(config)

            # Check if thread exists
            if not snapshot or not snapshot.values:
                raise HTTPException(
                    status_code=404,
                    detail=f"Thread {request.thread_id} not found"
                )

            # Extract state
            state = snapshot.values.get("state", {})
            ui = state.get("ui", {
                "message": "Processing...",
                "current_node": "unknown",
                "status": "running",
                "progress": {"current": 0, "total": 4}
            })
            data = state.get("data", {})

            # Determine retry_after based on status
            status = ui.get("status", "running")
            retry_after = None if status == "completed" or status == "failed" else 2

            return ChatResponse(
                thread_id=request.thread_id,
                status=status,
                message=ui.get("message", "Processing..."),
                current_node=ui.get("current_node", "unknown"),
                progress=ui.get("progress", {"current": 0, "total": 4}),
                data=data,
                retry_after=retry_after
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving workflow state: {str(e)}"
            )

    # Invalid request - neither message nor thread_id provided
    else:
        raise HTTPException(
            status_code=400,
            detail="Either 'message' (for new workflow) or 'thread_id' (for polling) must be provided"
        )
