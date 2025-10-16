"""
Composio Agent Gateway - FastAPI Service
Simplified, robust baseline with MCP integration
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifespan"""
    logger.info("Starting Composio Agent Gateway...")
    yield
    logger.info("Shutting down Composio Agent Gateway...")


# Initialize FastAPI app (single instance)
app = FastAPI(
    title="Composio Agent Gateway",
    description="MCP server for Composio, Render, and Firebase tools",
    version="1.0.0",
    lifespan=lifespan
)

# Add HTTPS redirect middleware
app.add_middleware(HTTPSRedirectMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include MCP router (with error handling)
MCP_AVAILABLE = False
try:
    from mcp_server import mcp_router
    app.include_router(mcp_router)
    MCP_AVAILABLE = True
    logger.info("MCP server endpoints loaded successfully")
except Exception as e:
    logger.warning(f"MCP server not available: {e}")
    logger.warning("Service will run without MCP endpoints")


@app.get("/")
@app.post("/")
async def root():
    """Root endpoint - Service info - accepts both GET and POST for MCP client compatibility"""
    return {
        "service": "Composio Agent Gateway",
        "version": "1.0.0",
        "status": "online",
        "mcp_enabled": True,
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "schema": "/schema",
            "invoke": "/invoke (POST)",
            "register": "/register (POST)",
            "mcp_tools": "/mcp/tools",
            "mcp_invoke": "/mcp/invoke (POST)",
            "discovery": "/.well-known/ai-plugin.json",
            "docs": "/docs"
        }
    }


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
    """Tool schema endpoint - Returns MCP-compliant tool list"""
    try:
        return {
            "tools": [
                {
                    "name": "firebase_write",
                    "description": "Write data to Firebase",
                    "parameters": {"type": "object"}
                },
                {
                    "name": "firebase_read",
                    "description": "Read data from Firebase",
                    "parameters": {"type": "object"}
                },
                {
                    "name": "render_get_logs",
                    "description": "Get Render service logs",
                    "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}
                },
                {
                    "name": "render_get_service_status",
                    "description": "Get Render service status",
                    "parameters": {"type": "object"}
                },
                {
                    "name": "render_get_latest_deploy",
                    "description": "Get latest Render deployment",
                    "parameters": {"type": "object"}
                },
                {
                    "name": "render_trigger_deploy",
                    "description": "Trigger Render deployment",
                    "parameters": {"type": "object", "properties": {"clear_cache": {"type": "boolean"}}}
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error in /schema: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/invoke")
async def invoke(data: dict):
    """Tool invocation endpoint - MCP-compliant with error handling"""
    try:
        tool_name = data.get("tool", "unknown")
        parameters = data.get("parameters", {})

        logger.info(f"Tool invoked: {tool_name}")

        return {
            "success": True,
            "tool": tool_name,
            "result": {
                "message": "Tool execution simulated",
                "parameters": parameters
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in /invoke: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


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
            "url": "https://composio-imo-creator-url.onrender.com/openapi.json",
            "is_user_authenticated": False
        },
        "logo_url": "https://raw.githubusercontent.com/djb258/composio-agent/main/assets/logo.png",
        "contact_email": "support@composio.dev",
        "legal_info_url": "https://composio.dev/legal"
    })


@app.get("/.well-known/openapi.json")
async def well_known_openapi():
    """Well-known OpenAPI endpoint for MCP discovery"""
    return JSONResponse(
        get_openapi(
            title="Composio Agent Gateway",
            version="1.0.0",
            description="MCP server for Composio, Render, and Firebase tools",
            routes=app.routes
        )
    )


@app.post("/register")
async def mcp_register(request: dict = {}):
    """MCP client registration endpoint"""
    import time
    client_id = request.get("client_id", "unknown") if isinstance(request, dict) else "unknown"
    logger.info(f"[MCP REGISTER] Client: {client_id}")

    return JSONResponse({
        "registered": True,
        "client_id": client_id,
        "server": "composio-agent",
        "version": "1.0.0",
        "capabilities": ["tools", "schema", "invoke"],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.get("/.well-known/oauth-authorization-server")
async def oauth_authorization_server():
    """OAuth discovery endpoint - returns no-auth configuration"""
    base_url = os.getenv("BASE_URL", "https://composio-imo-creator-url.onrender.com")
    return JSONResponse({
        "issuer": base_url,
        "authorization_endpoint": None,
        "token_endpoint": None,
        "grant_types_supported": [],
        "response_types_supported": [],
        "service_documentation": f"{base_url}/docs"
    })


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource():
    """OAuth resource discovery - indicates no authentication required"""
    base_url = os.getenv("BASE_URL", "https://composio-imo-creator-url.onrender.com")
    return JSONResponse({
        "resource": base_url,
        "authorization_servers": [],
        "bearer_methods_supported": [],
        "resource_documentation": f"{base_url}/docs"
    })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
