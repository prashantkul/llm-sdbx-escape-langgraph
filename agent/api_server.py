"""
LangGraph API Server for interactive agent usage.

This server exposes the security researcher agent via HTTP API,
allowing you to interact with it using:
- LangGraph Studio UI
- HTTP clients (curl, Postman)
- Custom web UIs

Usage:
    python api_server.py

Then connect LangGraph Studio to http://localhost:8123
"""

import sys
import os
from typing import Dict, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logging'))

from workflow import create_agent_graph, get_initial_state, initialize_mcp
from config import MCP_SERVER_URL, MAX_ATTEMPTS, GEMINI_MODEL
from logger import ResearchLogger

# Initialize global clients
logger = None

# Create the graph once at module level
agent_graph = None


def initialize():
    """Initialize MCP client, logger, and graph."""
    global logger, agent_graph

    # Initialize logger
    logger = ResearchLogger()
    print(f"Logging to: {logger.get_log_path()}")

    # Initialize MCP client and tools
    print(f"Connecting to MCP server at {MCP_SERVER_URL}")
    initialize_mcp()
    print("✓ Connected to MCP server")

    # Set globals in main module for nodes to access
    import __main__
    __main__.logger = logger
    __main__.llm = sys.modules['workflow'].llm
    __main__.mcp_tools = sys.modules['workflow'].mcp_tools

    # Create graph
    agent_graph = create_agent_graph()
    print("✓ Agent graph ready")


# Create FastAPI app
app = FastAPI(
    title="Security Researcher Agent API",
    description="LangGraph agent for security research and sandbox escape testing",
    version="1.0.0"
)

# Add CORS middleware for web UIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvokeRequest(BaseModel):
    """Request model for invoking the agent."""
    message: Optional[str] = None
    mode: Optional[str] = "interactive"  # "auto" or "interactive"
    config: Optional[Dict[str, Any]] = None


class InvokeResponse(BaseModel):
    """Response model for agent invocation."""
    success: bool
    attempt_count: int
    target_content: str
    error: str
    messages: list


@app.on_event("startup")
async def startup_event():
    """Initialize on server startup."""
    initialize()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Security Researcher Agent API",
        "version": "1.0.0",
        "model": GEMINI_MODEL,
        "max_attempts": MAX_ATTEMPTS,
        "endpoints": {
            "POST /invoke": "Run the agent with a custom message",
            "GET /health": "Health check",
            "GET /config": "Get current configuration"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "graph": "ready" if agent_graph else "not initialized"
    }


@app.get("/config")
async def get_config():
    """Get current configuration."""
    return {
        "model": GEMINI_MODEL,
        "mcp_server_url": MCP_SERVER_URL,
        "max_attempts": MAX_ATTEMPTS,
        "log_path": logger.get_log_path() if logger else None
    }


@app.post("/invoke", response_model=InvokeResponse)
async def invoke_agent(request: InvokeRequest):
    """
    Invoke the security researcher agent.

    Args:
        request: Contains optional custom message and config

    Returns:
        Agent execution results including success status and extracted content
    """
    if not agent_graph:
        raise HTTPException(status_code=503, detail="Agent graph not initialized")

    try:
        # Get initial state with custom or default message and mode
        initial_state = get_initial_state(
            user_message=request.message,
            mode=request.mode or "interactive"
        )

        # Default config
        config = request.config or {"recursion_limit": 50}

        # Run the agent
        final_state = agent_graph.invoke(initial_state, config=config)

        # Log result
        if final_state.get("success"):
            print(f"✓ Success after {final_state['attempt_count']} attempts")
        else:
            print(f"✗ Failed after {final_state['attempt_count']} attempts")
            logger.log_failure(final_state['attempt_count'])

        # Return results
        return InvokeResponse(
            success=final_state.get("success", False),
            attempt_count=final_state.get("attempt_count", 0),
            target_content=final_state.get("target_content", ""),
            error=final_state.get("error", ""),
            messages=[
                {
                    "type": msg.__class__.__name__,
                    "content": msg.content if hasattr(msg, 'content') else str(msg)
                }
                for msg in final_state.get("messages", [])
            ]
        )

    except Exception as e:
        logger.log_error(f"API invocation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stream")
async def stream_agent():
    """
    Stream agent execution (for future implementation).

    This would enable real-time streaming of agent thoughts and actions.
    """
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented. Use /invoke for now."
    )


if __name__ == "__main__":
    print("=" * 80)
    print("SECURITY RESEARCHER AGENT - API SERVER")
    print("=" * 80)
    print("\nStarting server on http://localhost:8123")
    print("\nConnect LangGraph Studio to: http://localhost:8123")
    print("Or use HTTP client: POST http://localhost:8123/invoke")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8123,
        log_level="info"
    )
