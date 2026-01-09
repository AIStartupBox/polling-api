"""
Chat controller - Single POST /chat endpoint for new requests and polling.

Handles both initiating new workflows and polling existing ones.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from workflow.graph import graph, cleanup_checkpoints


# Pydantic models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: Optional[str] = None
    thread_id: Optional[str] = None
    approved: Optional[bool] = None  # For handling interrupt approval


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    thread_id: str
    status: Literal["running", "completed", "failed", "waiting_approval"]
    message: str
    current_node: str
    progress: Dict[str, int]
    data: Dict[str, Any]
    retry_after: Optional[int]
    requires_approval: Optional[bool] = False  # Indicates if workflow is waiting for approval


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
            },
            "Interrupt": False  # Initialize interrupt flag
        }

        # Configure thread
        config = {"configurable": {"thread_id": thread_id}}

        # Run the graph
        async for event in graph.astream(initial_state, config):
            # Events are streamed but we don't need to do anything here
            # The graph automatically saves checkpoints to MongoDB
            pass

        # Note: Cleanup happens when user polls and receives the completed status
        # This ensures the user sees the final state before it's deleted

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


async def resume_workflow(thread_id: str):
    """
    Resume an interrupted workflow.

    Args:
        thread_id: Unique thread identifier
    """
    try:
        # Configure thread
        config = {"configurable": {"thread_id": thread_id}}

        # Small delay to ensure the approval response is sent first
        await asyncio.sleep(0.1)

        # Resume the graph from where it was interrupted
        # Passing None as input resumes from the last checkpoint
        async for event in graph.astream(None, config):
            # Events are streamed as the graph processes
            # The graph automatically saves checkpoints to MongoDB
            pass

        # Note: Cleanup happens when user polls and receives the completed status
        # This ensures the user sees the final state before it's deleted

    except Exception as e:
        # If graph execution fails, save error state
        print(f"Error resuming workflow: {e}")
        import traceback
        traceback.print_exc()

        try:
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = graph.get_state(config)
            current_state = snapshot.values.get("state", {}) if snapshot and snapshot.values else {}

            error_state = {
                "state": {
                    **current_state,
                    "ui": {
                        "message": f"❌ Workflow failed after resume: {str(e)}",
                        "current_node": "error",
                        "status": "failed",
                        "progress": current_state.get("ui", {}).get("progress", {"current": 0, "total": 4})
                    },
                    "data": {**current_state.get("data", {}), "error": str(e)}
                }
            }
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

            # Check if workflow is interrupted and waiting for approval
            # When LangGraph interrupts:
            # - snapshot.next contains the next node(s) to execute
            # - snapshot.tasks contains pending tasks (with result=None)
            # - We check if report_identifier is in next and tasks have no results (pending)
            next_node = snapshot.next if hasattr(snapshot, 'next') else []
            tasks = snapshot.tasks if hasattr(snapshot, 'tasks') else []

            # Workflow is interrupted if next node is report_identifier and tasks are pending (no result)
            # Tasks with result=None are pending (interrupted), tasks with results are running/complete
            is_interrupted = (
                len(next_node) > 0 and
                "report_identifier" in next_node and
                len(tasks) > 0 and
                all(task.result is None for task in tasks)  # All tasks pending means interrupted
            )

            # Handle approval/rejection when workflow is interrupted
            if request.approved is not None and is_interrupted:
                if request.approved:
                    # User approved - update state to set Interrupt flag to False
                    approval_state = {
                        "state": snapshot.values.get("state", {}),
                        "Interrupt": False
                    }
                    graph.update_state(config, approval_state)

                    # Resume the workflow by running it in background
                    asyncio.create_task(resume_workflow(request.thread_id))

                    # Return response indicating workflow is resuming
                    return ChatResponse(
                        thread_id=request.thread_id,
                        status="running",
                        message="✅ Approved! Continuing with report identification...",
                        current_node="report_identifier",
                        progress={"current": 2, "total": 4},
                        data=snapshot.values.get("state", {}).get("data", {}),
                        retry_after=2,
                        requires_approval=False
                    )
                else:
                    # User rejected - stop the workflow
                    rejection_state = {
                        "state": {
                            **snapshot.values.get("state", {}),
                            "ui": {
                                "message": "❌ Workflow cancelled by user",
                                "current_node": "cancelled",
                                "status": "failed",
                                "progress": {"current": 1, "total": 4}
                            }
                        }
                    }
                    graph.update_state(config, rejection_state)

                    return ChatResponse(
                        thread_id=request.thread_id,
                        status="failed",
                        message="❌ Workflow cancelled by user",
                        current_node="cancelled",
                        progress={"current": 1, "total": 4},
                        data=snapshot.values.get("state", {}).get("data", {}),
                        retry_after=None,
                        requires_approval=False
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

            # If workflow is interrupted, show approval message and set Interrupt flag
            if is_interrupted:
                # Update state to set Interrupt flag to True
                interrupt_state = {
                    "state": snapshot.values.get("state", {}),
                    "Interrupt": True
                }
                graph.update_state(config, interrupt_state)

                status = "waiting_approval"
                message = "⚠️ Workflow paused. Approval required to proceed with report identification."
                retry_after = None  # Don't retry while waiting for approval
            else:
                status = ui.get("status", "running")
                message = ui.get("message", "Processing...")
                retry_after = None if status == "completed" or status == "failed" else 2

            # Prepare the response
            response = ChatResponse(
                thread_id=request.thread_id,
                status=status,
                message=message,
                current_node=ui.get("current_node", "unknown"),
                progress=ui.get("progress", {"current": 0, "total": 4}),
                data=data,
                retry_after=retry_after,
                requires_approval=is_interrupted
            )

            # Cleanup checkpoints AFTER preparing response if workflow is completed
            # This ensures the user receives the final state before deletion
            if status == "completed":
                # Schedule cleanup in background to not block response
                async def delayed_cleanup():
                    await asyncio.sleep(0.5)  # Wait for response to be sent
                    cleanup_checkpoints(request.thread_id)

                asyncio.create_task(delayed_cleanup())

            return response

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
