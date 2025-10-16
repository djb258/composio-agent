"""
MCP Server for Render Deployment Monitoring and Control
Provides tools for Claude to monitor and manage Render deployments
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router for MCP endpoints
mcp_router = APIRouter(prefix="/mcp", tags=["MCP"])

# Render API configuration
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_API_BASE = "https://api.render.com/v1"
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "rnd_GD2dsMkpLsLgpz18ux52aU1I24Yt")


class MCPToolRequest(BaseModel):
    """MCP tool invocation request"""
    tool: str
    parameters: Dict[str, Any] = {}


class RenderDeploymentInfo(BaseModel):
    """Render deployment information"""
    id: str
    status: str
    created_at: str
    finished_at: Optional[str] = None
    commit_id: Optional[str] = None
    commit_message: Optional[str] = None


async def call_render_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Call Render API with authentication"""
    if not RENDER_API_KEY:
        raise HTTPException(status_code=500, detail="RENDER_API_KEY not configured")

    url = f"{RENDER_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = await client.patch(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()


@mcp_router.get("/tools")
async def list_mcp_tools():
    """List all available MCP tools for Render management"""
    return {
        "tools": [
            {
                "name": "render_get_service_status",
                "description": "Get current status of Render service including deployment state",
                "parameters": {}
            },
            {
                "name": "render_get_latest_deploy",
                "description": "Get information about the latest deployment",
                "parameters": {}
            },
            {
                "name": "render_get_logs",
                "description": "Fetch recent logs from the Render service",
                "parameters": {
                    "limit": {"type": "integer", "default": 100, "description": "Number of log lines to fetch"}
                }
            },
            {
                "name": "render_list_deploys",
                "description": "List recent deployments",
                "parameters": {
                    "limit": {"type": "integer", "default": 10, "description": "Number of deployments to list"}
                }
            },
            {
                "name": "render_trigger_deploy",
                "description": "Trigger a new deployment with optional cache clear",
                "parameters": {
                    "clear_cache": {"type": "boolean", "default": False, "description": "Whether to clear build cache"}
                }
            },
            {
                "name": "render_get_env_vars",
                "description": "List all environment variables",
                "parameters": {}
            },
            {
                "name": "render_update_env_var",
                "description": "Update an environment variable",
                "parameters": {
                    "key": {"type": "string", "required": True, "description": "Environment variable key"},
                    "value": {"type": "string", "required": True, "description": "Environment variable value"}
                }
            },
            {
                "name": "render_get_metrics",
                "description": "Get service metrics (CPU, memory, bandwidth)",
                "parameters": {}
            }
        ]
    }


@mcp_router.post("/invoke")
async def invoke_mcp_tool(request: MCPToolRequest):
    """Execute an MCP tool"""
    tool_name = request.tool
    params = request.parameters

    logger.info(f"MCP tool invoked: {tool_name}")

    try:
        # Route to appropriate handler
        if tool_name == "render_get_service_status":
            result = await get_service_status()
        elif tool_name == "render_get_latest_deploy":
            result = await get_latest_deploy()
        elif tool_name == "render_get_logs":
            limit = params.get("limit", 100)
            result = await get_logs(limit)
        elif tool_name == "render_list_deploys":
            limit = params.get("limit", 10)
            result = await list_deploys(limit)
        elif tool_name == "render_trigger_deploy":
            clear_cache = params.get("clear_cache", False)
            result = await trigger_deploy(clear_cache)
        elif tool_name == "render_get_env_vars":
            result = await get_env_vars()
        elif tool_name == "render_update_env_var":
            key = params.get("key")
            value = params.get("value")
            if not key or not value:
                raise HTTPException(status_code=400, detail="key and value required")
            result = await update_env_var(key, value)
        elif tool_name == "render_get_metrics":
            result = await get_metrics()
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

        return {
            "success": True,
            "tool": tool_name,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"Render API error: {e.response.status_code} - {e.response.text}")
        return {
            "success": False,
            "error": f"Render API error: {e.response.status_code}",
            "details": e.response.text,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP tool execution failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Tool implementations
async def get_service_status() -> Dict:
    """Get current service status"""
    # Render API returns service data directly
    service = await call_render_api(f"/services/{RENDER_SERVICE_ID}")

    return {
        "id": service.get("id"),
        "name": service.get("name"),
        "type": service.get("type"),
        "state": service.get("suspended"),
        "created_at": service.get("createdAt"),
        "updated_at": service.get("updatedAt"),
        "url": service.get("serviceDetails", {}).get("url"),
        "branch": service.get("branch"),
        "auto_deploy": service.get("autoDeploy")
    }


async def get_latest_deploy() -> Dict:
    """Get latest deployment info"""
    # Render API returns array of [{deploy: {...}}]
    data = await call_render_api(f"/services/{RENDER_SERVICE_ID}/deploys?limit=1")

    if not data or not isinstance(data, list) or len(data) == 0:
        return {"message": "No deployments found"}

    deploy_obj = data[0].get("deploy", {})
    return {
        "id": deploy_obj.get("id"),
        "status": deploy_obj.get("status"),
        "created_at": deploy_obj.get("createdAt"),
        "finished_at": deploy_obj.get("finishedAt"),
        "commit_id": deploy_obj.get("commit", {}).get("id"),
        "commit_message": deploy_obj.get("commit", {}).get("message")
    }


async def get_logs(limit: int = 100) -> Dict:
    """Fetch recent logs"""
    data = await call_render_api(f"/services/{RENDER_SERVICE_ID}/logs?limit={limit}")
    logs = data.get("logs", [])

    return {
        "count": len(logs),
        "logs": [
            {
                "timestamp": log.get("timestamp"),
                "message": log.get("message"),
                "type": log.get("type")
            }
            for log in logs
        ]
    }


async def list_deploys(limit: int = 10) -> Dict:
    """List recent deployments"""
    # Render API returns array of [{deploy: {...}}]
    data = await call_render_api(f"/services/{RENDER_SERVICE_ID}/deploys?limit={limit}")

    if not data or not isinstance(data, list):
        return {"count": 0, "deploys": []}

    return {
        "count": len(data),
        "deploys": [
            {
                "id": item.get("deploy", {}).get("id"),
                "status": item.get("deploy", {}).get("status"),
                "created_at": item.get("deploy", {}).get("createdAt"),
                "finished_at": item.get("deploy", {}).get("finishedAt"),
                "commit_message": item.get("deploy", {}).get("commit", {}).get("message")
            }
            for item in data
        ]
    }


async def trigger_deploy(clear_cache: bool = False) -> Dict:
    """Trigger a new deployment"""
    payload = {}
    if clear_cache:
        payload["clearCache"] = "clear"

    data = await call_render_api(
        f"/services/{RENDER_SERVICE_ID}/deploys",
        method="POST",
        data=payload
    )

    deploy = data.get("deploy", {})
    return {
        "id": deploy.get("id"),
        "status": deploy.get("status"),
        "created_at": deploy.get("createdAt"),
        "message": "Deployment triggered successfully"
    }


async def get_env_vars() -> Dict:
    """List environment variables"""
    # Render API returns array of [{envVar: {...}}]
    data = await call_render_api(f"/services/{RENDER_SERVICE_ID}/env-vars")

    if not data or not isinstance(data, list):
        return {"count": 0, "variables": []}

    return {
        "count": len(data),
        "variables": [
            {
                "key": item.get("envVar", {}).get("key"),
                "value": item.get("envVar", {}).get("value") if not item.get("envVar", {}).get("isSecret") else "***REDACTED***"
            }
            for item in data
        ]
    }


async def update_env_var(key: str, value: str) -> Dict:
    """Update an environment variable"""
    data = await call_render_api(
        f"/services/{RENDER_SERVICE_ID}/env-vars/{key}",
        method="PATCH",
        data={"value": value}
    )

    return {
        "key": key,
        "updated": True,
        "message": "Environment variable updated successfully"
    }


async def get_metrics() -> Dict:
    """Get service metrics"""
    # Note: Render API metrics endpoint may require paid plan
    # This is a placeholder - adjust based on actual API availability
    try:
        data = await call_render_api(f"/services/{RENDER_SERVICE_ID}/metrics")
        return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 402:
            return {"message": "Metrics require paid Render plan"}
        raise
