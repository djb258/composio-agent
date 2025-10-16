"""
Composio Agent Gateway - FastAPI Service
A proxy service for Composio API tool invocations
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Composio Agent Gateway",
    description="Proxy service for Composio API tool invocations with Render MCP integration",
    version="1.0.0"
)

# Import and include MCP router
try:
    from mcp_server import mcp_router
    app.include_router(mcp_router)
    logger.info("MCP server endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"MCP server not available: {e}")

# Environment variables
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
KILL_SWITCH = os.getenv("KILL_SWITCH", "false").lower() == "true"
COMPOSIO_API_BASE_URL = "https://api.composio.dev/api/v1"

# Validate API key on startup
if not COMPOSIO_API_KEY:
    logger.warning("COMPOSIO_API_KEY not set - /invoke endpoint will fail")


# Pydantic models
class InvokeRequest(BaseModel):
    """Request model for /invoke endpoint"""
    tool: str = Field(..., description="Tool name to invoke")
    data: Dict[str, Any] = Field(..., description="Tool parameters and data")


class InvokeResponse(BaseModel):
    """Response model for /invoke endpoint"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


# Load MCP endpoints configuration
def load_tool_definitions() -> Dict[str, Any]:
    """Load tool definitions from config/mcp_endpoints.json"""
    try:
        config_path = os.path.join("config", "mcp_endpoints.json")
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Tool definitions file not found at {config_path}")
        return {"tools": []}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing tool definitions: {e}")
        return {"tools": []}


@app.get("/health")
async def health():
    """
    Health check endpoint for Render
    Returns service health status
    """
    return {
        "status": "healthy",
        "service": "composio-agent",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """
    Detailed status endpoint
    Returns service status with additional info
    """
    logger.info("Status endpoint called")
    return {
        "status": "ok",
        "service": "composio-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "kill_switch": KILL_SWITCH,
        "api_key_configured": bool(COMPOSIO_API_KEY)
    }


@app.get("/schema")
async def get_schema():
    """
    Returns JSON listing all available tool definitions
    """
    logger.info("Schema endpoint called")
    tool_definitions = load_tool_definitions()
    return tool_definitions


@app.post("/invoke")
async def invoke_tool(request: InvokeRequest):
    """
    Executes a tool by proxying to Composio API

    Validates required fields:
    - agent_id
    - process_id
    - blueprint_id
    - timestamp_last_touched
    """
    start_time = datetime.utcnow()

    # Log invocation request
    logger.info(f"Invoke endpoint called - Tool: {request.tool}")
    logger.debug(f"Request data: {request.data}")

    # Check kill switch
    if KILL_SWITCH:
        logger.warning("Invoke request blocked - Kill switch is active")
        return JSONResponse(
            status_code=503,
            content={
                "error": "service disabled",
                "status": "kill_switch_active",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Validate API key
    if not COMPOSIO_API_KEY:
        logger.error("COMPOSIO_API_KEY not configured")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Service configuration error - API key not set",
                "status": "configuration_error",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Validate required fields
    required_fields = ["agent_id", "process_id", "blueprint_id", "timestamp_last_touched"]
    for field in required_fields:
        if field not in request.data:
            logger.error(f"Validation failed - Missing required field: {field}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": f"Missing required field: {field}",
                    "status": "validation_failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    try:
        # Prepare request to Composio API
        headers = {
            "X-API-Key": COMPOSIO_API_KEY,
            "Content-Type": "application/json"
        }

        # Build API endpoint URL
        # Assuming tool name maps to Composio endpoint
        # Adjust this based on actual Composio API structure
        api_url = f"{COMPOSIO_API_BASE_URL}/actions/{request.tool}/execute"

        # Prepare payload
        payload = request.data

        logger.info(f"Proxying request to Composio API: {api_url}")

        # Make request to Composio API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # Log successful invocation
        logger.info(f"Tool invocation successful - Tool: {request.tool}, Duration: {execution_time}s")
        logger.debug(f"Response: {result}")

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": execution_time
        }

    except httpx.HTTPStatusError as e:
        # HTTP error from Composio API
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_msg = f"Composio API error: {e.response.status_code} - {e.response.text}"
        logger.error(f"Tool invocation failed - {error_msg}, Duration: {execution_time}s")

        return JSONResponse(
            status_code=e.response.status_code,
            content={
                "success": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": execution_time
            }
        )

    except httpx.RequestError as e:
        # Network/connection error
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_msg = f"Request error: {str(e)}"
        logger.error(f"Tool invocation failed - {error_msg}, Duration: {execution_time}s")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": execution_time
            }
        )

    except Exception as e:
        # Unexpected error
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Tool invocation failed - {error_msg}, Duration: {execution_time}s", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat(),
                "execution_time": execution_time
            }
        )


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    """
    ChatGPT MCP discovery endpoint
    Returns plugin manifest for ChatGPT connector compatibility
    """
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Composio Agent Gateway",
        "name_for_model": "composio_agent",
        "description_for_human": "Unified MCP server for Composio, Render, and Firebase tools.",
        "description_for_model": "Provides read/write operations through the MCP protocol. Tools include firebase_write, render_get_logs, and more.",
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "https://composio-imo-creator-url.onrender.com/openapi.json"
        },
        "logo_url": "https://composio-imo-creator-url.onrender.com/logo.png",
        "contact_email": "support@yourdomain.com",
        "legal_info_url": "https://yourdomain.com/legal"
    })


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
