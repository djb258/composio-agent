"""
Composio Agent Gateway - FastAPI Service
Simplified, robust baseline with MCP integration
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app (single instance)
app = FastAPI(
    title="Composio Agent Gateway",
    description="MCP server for Composio, Render, and Firebase tools",
    version="1.0.0"
)

# Import and include MCP router
try:
    from mcp_server import mcp_router
    app.include_router(mcp_router)
    logger.info("MCP server endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"MCP server not available: {e}")


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "composio-agent",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """Service status endpoint"""
    return {
        "status": "ok",
        "service": "composio-agent",
        "timestamp": datetime.utcnow().isoformat(),
        "api_key_configured": bool(os.getenv("COMPOSIO_API_KEY"))
    }


@app.get("/schema")
async def get_schema():
    """Tool schema endpoint"""
    return {
        "tools": [
            "firebase_write",
            "firebase_read",
            "render_get_logs",
            "render_get_service_status",
            "render_get_latest_deploy",
            "render_trigger_deploy"
        ]
    }


@app.post("/invoke")
async def invoke(data: dict):
    """Tool invocation endpoint"""
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    """ChatGPT MCP discovery endpoint"""
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "Composio Agent Gateway",
        "name_for_model": "composio_agent",
        "description_for_human": "Unified MCP server for Composio, Render, and Firebase tools.",
        "description_for_model": "Provides read/write operations through the MCP protocol.",
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "https://composio-imo-creator-url.onrender.com/openapi.json"
        },
        "logo_url": "https://composio-imo-creator-url.onrender.com/logo.png",
        "contact_email": "support@yourdomain.com",
        "legal_info_url": "https://yourdomain.com/legal"
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
