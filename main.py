"""
FastAPI application entry point.

This module initializes the FastAPI app and includes all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.chat_controller import router as chat_router
import uvicorn


# Create FastAPI app
app = FastAPI(
    title="Polling-Based LangGraph Chat API",
    description="Production-ready FastAPI application with LangGraph workflow and MongoDB checkpointing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Polling-Based LangGraph Chat API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat - POST endpoint for new workflows and polling",
            "docs": "/docs - Interactive API documentation",
            "health": "/health - Health check endpoint"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
